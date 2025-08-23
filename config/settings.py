# config/settings.py

# API para datos históricos y resultados
API_FOOTBALL_KEY ='978a55159c58e9703382e358fb55928a'

# API para cuotas
ODDS_API_KEY ='3af7924d9142e061f272ff5f448e31ad'

HISTORICAL_DATA_FILES = [
    #spain
    'data/SP1_2022_2023.csv',
    'data/SP1_2023_2024.csv',
    'data/SP1_2024_2025.csv',
    #england
    'data/E0_2022_2023.csv',
    'data/E0_2023_2024.csv',
    'data/E0_2024_2025.csv',
    #france
    'data/F1_2022_2023.csv',
    'data/F1_2023_2024.csv',
    'data/F1_2024_2025.csv',
    #italy
    'data/I1_2022_2023.csv',
    'data/I1_2023_2024.csv',
    'data/I1_2024_2025.csv',
    #Germany
    'data/D1_2022_2023.csv',
    'data/D1_2023_2024.csv',
    'data/D1_2024_2025.csv'
]

# --- Configuración de The Odds API ---
ODDS_API_LEAGUES = [
    'soccer_spain_la_liga',
    'soccer_epl',
    'soccer_germany_bundesliga',
    'soccer_italy_serie_a',
    'soccer_france_ligue_one'
]
REGIONS = 'eu'
MARKETS = 'h2h,totals'
HOURS_AHEAD = 72 # Ventana de tiempo para buscar partidos (en horas)
