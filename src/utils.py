# src/utils.py (Versión Final Ampliada)
import pandas as pd
import os

def load_and_prepare_data(files: list) -> pd.DataFrame:
    all_seasons_df = []
    for file_path in files:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, encoding='latin1')
                # Extraemos el código de la liga del nombre del archivo (ej. 'SP1' de 'data/SP1_2022_2023.csv')
                league_code = os.path.basename(file_path).split('_')[0]
                df['league_code'] = league_code

                required_cols = {'Date': 'utc_date', 'HomeTeam': 'home_team_name', 'AwayTeam': 'away_team_name', 'FTHG': 'home_team_score', 'FTAG': 'away_team_score', 'B365H': 'home_win_odds', 'B365D': 'draw_odds', 'B365A': 'away_win_odds', 'league_code': 'league_code'}
                df = df[list(required_cols.keys())].rename(columns=required_cols)
                df['utc_date'] = pd.to_datetime(df['utc_date'], dayfirst=True)
                df.dropna(inplace=True)
                all_seasons_df.append(df)
            except Exception as e:
                print(f"Error procesando el archivo {file_path}: {e}")
    return pd.concat(all_seasons_df, ignore_index=True) if all_seasons_df else pd.DataFrame()

def normalize_team_name(name: str) -> str:
    """
    Función definitiva que usa un diccionario para estandarizar cualquier nombre de equipo.
    """
    # Clave: Cualquier variación posible. Valor: El nombre estándar que usaremos siempre.
    name_map = {
        # Premier League
        'West Ham': 'West Ham', 'West Ham United': 'West Ham',
        'Wolves': 'Wolves', 'Wolverhampton Wanderers': 'Wolves',
        'Nott\'m Forest': 'Nottingham Forest', 'Nottingham Forest': 'Nottingham Forest',
        'Man United': 'Man United', 'Manchester United': 'Man United',
        'Newcastle': 'Newcastle', 'Newcastle United': 'Newcastle',
        'Tottenham': 'Tottenham', 'Tottenham Hotspur': 'Tottenham',
        'Brighton': 'Brighton', 'Brighton & Hove Albion': 'Brighton',
        'Leeds': 'Leeds', 'Leeds United': 'Leeds',
        'Leicester': 'Leicester', 'Leicester City': 'Leicester',
        'Arsenal': 'Arsenal', 'Everton': 'Everton', 'Liverpool': 'Liverpool',
        'Chelsea': 'Chelsea', 'Crystal Palace': 'Crystal Palace', 'Brentford': 'Brentford',
        'Aston Villa': 'Aston Villa', 'Bournemouth': 'Bournemouth', 'Fulham': 'Fulham',
        'Man City': 'Man City', 'Manchester City': 'Man City',

        # La Liga
        'Athletic Bilbao': 'Athletic Bilbao', 'Athletic Club': 'Athletic Bilbao',
        'Mallorca': 'Mallorca', 'RCD Mallorca': 'Mallorca',
        'Osasuna': 'Osasuna', 'CA Osasuna': 'Osasuna',
        'Espanol': 'Espanyol', 'RCD Espanyol': 'Espanyol', 'RCD Espanyol Barcelona': 'Espanyol',
        'Cadiz': 'Cadiz', 'Cádiz CF': 'Cadiz',
        'Atletico Madrid': 'Atletico Madrid', 'Atlético Madrid': 'Atletico Madrid',
        'Almeria': 'Almeria', 'UD Almería': 'Almeria',
        'Celta Vigo': 'Celta Vigo', 'RC Celta': 'Celta Vigo',
        'Elche': 'Elche', 'Elche CF': 'Elche',
        'Betis': 'Real Betis', 'Real Betis': 'Real Betis', 'Real Betis Balompié': 'Real Betis',
        'Real Madrid': 'Real Madrid', 'Sevilla': 'Sevilla', 'Valencia': 'Valencia',
        'Girona': 'Girona', 'Getafe': 'Getafe', 'Real Sociedad': 'Real Sociedad',
        'Villarreal': 'Villarreal', 'Rayo Vallecano': 'Rayo Vallecano', 'Las Palmas': 'Las Palmas',
        'Alaves': 'Alaves', 'Levante': 'Levante', 'Oviedo': 'Oviedo',

        # --- NUEVOS EQUIPOS ---
        # Bundesliga (Alemania)
        'Bayern Munich': 'Bayern Munich',
        'Bayer Leverkusen': 'Leverkusen', 'Leverkusen': 'Leverkusen',
        'Dortmund': 'Dortmund', 'Borussia Dortmund': 'Dortmund',
        'Ein Frankfurt': 'Eintracht Frankfurt', 'Eintracht Frankfurt': 'Eintracht Frankfurt',
        'RB Leipzig': 'RB Leipzig', 'Leipzig': 'RB Leipzig',
        'FC Koln': 'FC Koln', 'Koln': 'FC Koln',

        # Serie A (Italia)
        'Inter': 'Inter', 'Inter Milan': 'Inter',
        'AC Milan': 'AC Milan', 'Milan': 'AC Milan',
        'Juventus': 'Juventus', 'Roma': 'Roma', 'Napoli': 'Napoli', 'Lazio': 'Lazio',
        'Atalanta': 'Atalanta', 'Fiorentina': 'Fiorentina',
        
        # Ligue 1 (Francia)
        'Paris SG': 'Paris SG', 'Paris Saint-Germain': 'Paris SG',
        'Marseille': 'Marseille', 'Lyon': 'Lyon', 'Monaco': 'Monaco', 'Lille': 'Lille', 'Rennes': 'Rennes'
    }
    
    # Si el nombre está en nuestro mapa, devolvemos el estándar. Si no, el original.
    return name_map.get(name, name)