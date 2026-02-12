"""
BKD Configuration - Tarif dan Pengaturan PAD
Data dummy untuk development - akan diganti dengan data real dari BKD
"""

# ==========================================
# TARIF RETRIBUSI PARKIR (Dummy)
# ==========================================
PARKING_TARIFF = {
    'motor': {
        'hourly': 2000,      # Rp per jam
        'daily': 10000,      # Rp per hari
        'monthly': 50000     # Rp per bulan
    },
    'mobil': {
        'hourly': 5000,
        'daily': 25000,
        'monthly': 150000
    },
    'bus': {
        'hourly': 10000,
        'daily': 50000,
        'monthly': 300000
    }
}

# Estimasi utilisasi parkir (%)
PARKING_UTILIZATION = {
    'mall': 0.7,           # 70% occupancy
    'pasar': 0.8,          # 80% occupancy
    'perkantoran': 0.6,    # 60% occupancy
    'hotel': 0.5,          # 50% occupancy
    'umum': 0.4            # 40% occupancy
}

# Estimasi jam operasional per hari
PARKING_HOURS = {
    'mall': 12,
    'pasar': 10,
    'perkantoran': 9,
    'hotel': 24,
    'umum': 12
}

# ==========================================
# TARIF PBB (Dummy - % dari NJOP)
# ==========================================
PBB_RATE = {
    'residential': 0.1,      # 0.1% dari NJOP
    'commercial': 0.2,       # 0.2% dari NJOP
    'industrial': 0.3,       # 0.3% dari NJOP
    'mixed_use': 0.15        # 0.15% dari NJOP
}

# NJOP Dummy per zona (Rp per m²)
NJOP_ZONE = {
    'pusat_kota': 3000000,   # Rp 3 juta per m²
    'semi_pusat': 2000000,   # Rp 2 juta per m²
    'pinggiran': 1000000,    # Rp 1 juta per m²
    'rural': 500000          # Rp 500 ribu per m²
}

# ==========================================
# PRIORITAS ALIH FUNGSI LAHAN
# ==========================================
LAND_CHANGE_PRIORITY = {
    # Format: (from_class, to_class): priority_level
    ('vegetation', 'built'): 'HIGH',        # Tanah lapang → Bangunan
    ('crops', 'built'): 'HIGH',             # Sawah → Bangunan
    ('bare', 'built'): 'MEDIUM',            # Lahan kosong → Bangunan
    ('vegetation', 'crops'): 'LOW',         # Hutan → Sawah
    ('water', 'built'): 'CRITICAL',         # Air → Bangunan (illegal?)
}

# Estimasi potensi pajak per jenis perubahan (multiplier)
LAND_CHANGE_TAX_POTENTIAL = {
    'vegetation_to_commercial': 5.0,   # 5x lipat potensi pajak
    'vegetation_to_residential': 3.0,  # 3x lipat
    'bare_to_commercial': 4.0,
    'bare_to_residential': 2.5,
    'crops_to_built': 3.5
}

# ==========================================
# KOORDINAT KECAMATAN KOTA MATARAM
# ==========================================
MATARAM_DISTRICTS = {
    'Ampenan': {
        'lat': -8.5707,
        'lon': 116.0840,
        'radius': 3500,
        'zone': 'semi_pusat',
        'kdkec': '010',
        'nmkec': 'AMPENAN'
    },
    'Cakranegara': {
        'lat': -8.5841,
        'lon': 116.1310,
        'radius': 3500,
        'zone': 'pusat_kota',
        'kdkec': '020',
        'nmkec': 'CAKRANEGARA'
    },
    'Mataram': {
        'lat': -8.6010,
        'lon': 116.1099,
        'radius': 3500,
        'zone': 'pusat_kota',
        'kdkec': '030',
        'nmkec': 'MATARAM'
    },
    'Selaparang': {
        'lat': -8.5721,
        'lon': 116.1068,
        'radius': 3500,
        'zone': 'semi_pusat',
        'kdkec': '040',
        'nmkec': 'SELAPARANG'
    },
    'Sekarbela': {
        'lat': -8.6080,
        'lon': 116.0869,
        'radius': 3500,
        'zone': 'pinggiran',
        'kdkec': '050',
        'nmkec': 'SEKARBELA'
    },
    'Sandubaya': {
        'lat': -8.5979,
        'lon': 116.1449,
        'radius': 3500,
        'zone': 'pinggiran',
        'kdkec': '060',
        'nmkec': 'SANDUBAYA'
    }
}

# ==========================================
# THRESHOLDS & PARAMETERS
# ==========================================
# Parking detection
PARKING_MIN_AREA = 50         # m² - minimum area (Indomaret/Retail scale)
PARKING_MAX_AREA = 10000      # m² - maximum area (filter outliers)
PARKING_ASPECT_RATIO = 0.15    # Min aspect ratio (Allow narrow retail parking)
PARKING_ACTIVITY_MIN = 100    # Threshold untuk deteksi pergerakan kendaraan
ROAD_BUFFER_M = 25            # Jarak maksimum dari jalan raya (meter)

# Building detection
BUILDING_MIN_AREA = 20        # m² - minimum building area
BUILDING_HEIGHT_THRESHOLD = 0.5  # meter - minimum height to be considered building

# Land use change
CHANGE_MIN_AREA = 50          # m² - minimum area untuk change detection
CHANGE_CONFIDENCE = 0.7       # 70% confidence threshold

# ==========================================
# VISUALIZATION COLORS
# ==========================================
COLORS = {
    'parking': '#FFD700',      # Gold
    'building': '#FF4444',     # Red
    'vegetation': '#22c55e',   # Green
    'water': '#3b82f6',        # Blue
    'bare': '#d4a574',         # Brown
    'crops': '#84cc16',        # Lime
    'change_high': '#ef4444',  # Red (high priority change)
    'change_medium': '#f97316', # Orange
    'change_low': '#eab308'    # Yellow
}

# ==========================================
# TARGET PAD (Dummy - untuk benchmarking)
# ==========================================
TARGET_PAD_ANNUAL = {
    'parking': 5_000_000_000,      # Rp 5 miliar
    'pbb': 50_000_000_000,         # Rp 50 miliar
    'land_change': 2_000_000_000   # Rp 2 miliar (dari objek pajak baru)
}

# ==========================================
# EXPORT SETTINGS
# ==========================================
EXPORT_FORMATS = ['csv', 'excel', 'geojson', 'pdf']
REPORT_TEMPLATE = 'templates/bkd_report.html'  # Jinja2 template

# ==========================================
# BOUNDARY VISUALIZATION
# ==========================================
BOUNDARY_COLORS = {
    'kecamatan': '#FF6B6B',
    'kelurahan': '#4ECDC4',
    'sls': '#95E1D3'
}

BOUNDARY_STYLES = {
    'default': {
        'color': '#FF6B6B',
        'weight': 2,
        'fillOpacity': 0,
        'opacity': 0.6
    },
    'highlight': {
        'color': '#FFD93D',
        'weight': 3,
        'fillOpacity': 0.1,
        'opacity': 0.9
    }
}

# Path to GeoJSON boundary data
BOUNDARY_GEOJSON_PATH = 'd:/bps/5271sls.geojson'

