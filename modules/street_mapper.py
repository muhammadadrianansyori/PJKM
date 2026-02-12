import requests
import geopandas as gpd
from shapely.geometry import Point, LineString
from typing import List, Dict, Optional
import pandas as pd


class StreetMapper:
    """
    Maps street data from OpenStreetMap to administrative boundaries.
    """
    
    def __init__(self, geojson_path: str):
        """
        Initialize with path to SLS boundary GeoJSON file.
        
        Args:
            geojson_path: Path to 5271sls.geojson file
        """
        self.sls_gdf = gpd.read_file(geojson_path)
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        
    def get_kecamatan_list(self) -> List[str]:
        """Get unique list of Kecamatan names from SLS data."""
        return sorted(self.sls_gdf['nmkec'].unique().tolist())
    
    def fetch_streets_osm(self, kecamatan: str) -> gpd.GeoDataFrame:
        """
        Fetch street data from OSM for a specific Kecamatan.
        
        Args:
            kecamatan: Kecamatan name to filter
            
        Returns:
            GeoDataFrame with street LineStrings and names
        """
        # Filter SLS data by kecamatan
        kec_data = self.sls_gdf[self.sls_gdf['nmkec'] == kecamatan.upper()]
        
        if kec_data.empty:
            return gpd.GeoDataFrame()
        
        # Get bounding box
        bounds = kec_data.total_bounds  # [minx, miny, maxx, maxy]
        min_lat, min_lon = bounds[1], bounds[0]
        max_lat, max_lon = bounds[3], bounds[2]
        
        # Overpass query for roads/streets
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"~"primary|secondary|tertiary|residential|service|unclassified|living_street|pedestrian|footway|path"]["name"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out geom;
        """
        
        try:
            response = requests.get(self.overpass_url, params={'data': query}, timeout=90)
            data = response.json()
            
            streets = []
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    # Extract coordinates
                    coords = [(node['lon'], node['lat']) for node in element['geometry']]
                    if len(coords) >= 2:
                        line = LineString(coords)
                        name = element.get('tags', {}).get('name', 'Jalan Tanpa Nama')
                        highway_type = element.get('tags', {}).get('highway', 'unknown')
                        osm_id = element.get('id', 0)
                        
                        streets.append({
                            'osm_id': osm_id,
                            'name': name,
                            'highway_type': highway_type,
                            'geometry': line,
                            'coords_list': coords  # Keep for easy map rendering
                        })
            
            if streets:
                return gpd.GeoDataFrame(streets, crs='EPSG:4326')
            else:
                return gpd.GeoDataFrame()
                
        except Exception as e:
            print(f"Error fetching OSM data: {e}")
            return gpd.GeoDataFrame()
    
    def map_streets_to_admin(self, kecamatan: str) -> pd.DataFrame:
        """
        Map streets to administrative boundaries (RT, Lingkungan, Kelurahan).
        Uses point-in-polygon with street centroid for accurate boundary detection.
        
        Args:
            kecamatan: Kecamatan name
            
        Returns:
            DataFrame with columns: Nama Jalan dan Gang, SLS, Lingkungan, Kelurahan, 
                                   Latitude, Longitude, Google Maps Link, MatchaPro Link
        """
        from shapely.geometry import Point
        
        # Fetch streets
        streets_gdf = self.fetch_streets_osm(kecamatan)
        
        if streets_gdf.empty:
            return pd.DataFrame(columns=[
                'Nama Jalan dan Gang', 'SLS', 'Lingkungan', 'Kelurahan', 'Coverage',
                'Latitude', 'Longitude', 'Google Maps Link', 'MatchaPro Link'
            ])
        
        results = []
        
        # Identify valid kelurahans for the selected kecamatan
        valid_kelurahans = self.sls_gdf[self.sls_gdf['nmkec'] == kecamatan.upper()]['nmdesa'].unique().tolist()
        
        # We use the full sls_gdf instead of just the selected kecamatan 
        # to handle streets that are on the border or slightly outside
        search_gdf = self.sls_gdf.copy()
        
        # Ensure same CRS
        if streets_gdf.crs != search_gdf.crs:
            streets_gdf = streets_gdf.to_crs(search_gdf.crs)
        
        # Group by name to treat fragmented ways as single streets
        # This is more accurate for coverage calculation
        if not streets_gdf.empty:
            # First, extract some metadata before dissolve
            # We filter out 'Jalan Tanpa Nama' to keep things clean
            named_streets = streets_gdf[streets_gdf['name'] != 'Jalan Tanpa Nama'].copy()
            if not named_streets.empty:
                # Dissolve geometries by street name
                dissolved_streets = named_streets.dissolve(by='name').reset_index()
            else:
                dissolved_streets = named_streets
        else:
            dissolved_streets = streets_gdf

        for idx, street_row in dissolved_streets.iterrows():
            street_geom = street_row['geometry']
            street_name = street_row['name']
            street_length = street_geom.length
            
            # Get centroid for coordinate reference
            centroid = street_geom.centroid
            lat = round(centroid.y, 6)
            lon = round(centroid.x, 6)
            
            # Find all SLS features that intersect with this street
            intersections = []
            
            # Efficient spatial search
            possible_matches_index = search_gdf.sindex.query(street_geom, predicate='intersects')
            possible_matches = search_gdf.iloc[possible_matches_index]
            
            for _, boundary in possible_matches.iterrows():
                try:
                    intersection = boundary['geometry'].intersection(street_geom)
                    if hasattr(intersection, 'length') and intersection.length > 0:
                        coverage_pct = (intersection.length / street_length) * 100
                        
                # Baris 162 - 175
                # Extract Lingkungan from nmsls
                nmsls_val = boundary['nmsls']
                
                # FORMATTING FIX: Mengubah 3-digit RT (misal: RT 001) menjadi 2-digit RT (misal: RT 01)
                # Ini mengikuti permintaan user agar di Excel/UI hanya muncul 2 digit
                import re
                nmsls_val = re.sub(r'RT\s+0+(\d{2})', r'RT \1', nmsls_val)
                
                if 'LINGKUNGAN' in nmsls_val:
                    parts = nmsls_val.split('LINGKUNGAN', 1)
                    lingk_name = parts[1].strip() if len(parts) > 1 else nmsls_val
                else:
                    lingk_name = nmsls_val
                            
                        intersections.append({
                            'nmsls': nmsls_val,
                            'lingkungan': lingk_name,
                            'kelurahan': boundary['nmdesa'],
                            'coverage': coverage_pct
                        })
                except:
                    continue
            
            # Administrative Assignment Logic (Hierarchical & Strict)
            # Thresholds: RT >= 95%, Lingkungan >= 95%
            RT_THRESHOLD = 95.0
            LINGKUNGAN_THRESHOLD = 95.0
            
            assigned_sls = "-"
            assigned_lingk = "-"
            assigned_kel = "-"
            final_coverage_info = "No match"
            
            if intersections:
                # 1. Check for Kelurahan Best Match (Fallback baseline)
                kel_stats = {}
                for inter in intersections:
                    kl = inter['kelurahan']
                    if kl not in kel_stats:
                        kel_stats[kl] = 0
                    kel_stats[kl] += inter['coverage']
                
                best_kel_name = max(kel_stats, key=kel_stats.get)
                assigned_kel = best_kel_name
                final_coverage_info = f"Kelurahan Only ({kel_stats[best_kel_name]:.1f}%)"
                
                # 2. Check for Lingkungan within the best Kelurahan
                lingk_stats = {}
                for inter in intersections:
                    if inter['kelurahan'] == best_kel_name:
                        lk = inter['lingkungan']
                        if lk not in lingk_stats:
                            lingk_stats[lk] = 0
                        lingk_stats[lk] += inter['coverage']
                
                if lingk_stats:
                    best_lingk_name = max(lingk_stats, key=lingk_stats.get)
                    best_lingk_coverage = lingk_stats[best_lingk_name]
                    
                    # Apply Lingkungan threshold (90%)
                    if best_lingk_coverage >= LINGKUNGAN_THRESHOLD:
                        assigned_lingk = best_lingk_name
                        final_coverage_info = f"{best_lingk_coverage:.1f}% (Lingk)"
                        
                        # 3. Check for specific RT (SLS) within the best Lingkungan
                        rt_stats = {}
                        for inter in intersections:
                            if inter['kelurahan'] == best_kel_name and inter['lingkungan'] == best_lingk_name:
                                rt = inter['nmsls']
                                if rt not in rt_stats:
                                    rt_stats[rt] = 0
                                rt_stats[rt] += inter['coverage']
                        
                        if rt_stats:
                            best_rt_name = max(rt_stats, key=rt_stats.get)
                            best_rt_coverage = rt_stats[best_rt_name]
                            
                            # Apply RT threshold (95%)
                            if best_rt_coverage >= RT_THRESHOLD:
                                assigned_sls = best_rt_name
                                final_coverage_info = f"{best_rt_coverage:.1f}% (RT)"
                    else:
                        # Best Lingkungan is < Lingkungan Threshold
                        pass

            # Create validation links
            google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            matchapro_link = f"https://cek-posisi-v2.streamlit.app/?coords=@{lat},{lon}"
            
            results.append({
                'Nama Jalan dan Gang': street_name,
                'SLS': assigned_sls,
                'Lingkungan': assigned_lingk,
                'Kelurahan': assigned_kel,
                'Coverage': final_coverage_info,
                'Latitude': lat,
                'Longitude': lon,
                'Google Maps Link': google_maps_link,
                'MatchaPro Link': matchapro_link
            })
        
        # Create DataFrame
        df = pd.DataFrame(results)
        if not df.empty:
            # FILTER: Only keep streets that fall into the selected Kecamatan's kelurahans
            # This prevents bounding box spillover from other districts from affecting metrics
            df = df[df['Kelurahan'].isin(valid_kelurahans)]
            
            df = df.drop_duplicates(subset=['Nama Jalan dan Gang', 'SLS'])
            df = df.sort_values(['Kelurahan', 'Lingkungan', 'Nama Jalan dan Gang'])
            df = df.reset_index(drop=True)
        
        return df
    
    def export_to_excel(self, df: pd.DataFrame, output_path: str):
        """
        Export street mapping data to Excel.
        
        Args:
            df: DataFrame with street mapping data
            output_path: Path to save Excel file
        """
        df.to_excel(output_path, index=False, sheet_name='Data Jalan')

