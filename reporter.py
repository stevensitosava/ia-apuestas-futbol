# reporter.py (Versión Final Completa - Agosto 2025)

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from scipy.stats import poisson
import json
import os
from config import settings

# --- MÓDULOS DE LÓGICA (Integrados para independencia) ---

def load_and_prepare_data(files: list) -> pd.DataFrame:
    """Versión silenciosa: Carga y unifica los datos desde los archivos CSV."""
    all_seasons_df = []
    for file_path in files:
        # Usamos os.path.exists para verificar antes de intentar leer
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, encoding='latin1')
                required_cols = {'Date': 'utc_date', 'HomeTeam': 'home_team_name', 'AwayTeam': 'away_team_name', 'FTHG': 'home_team_score', 'FTAG': 'away_team_score'}
                df = df[list(required_cols.keys())].rename(columns=required_cols)
                df['utc_date'] = pd.to_datetime(df['utc_date'], dayfirst=True)
                df.dropna(subset=['home_team_score', 'away_team_score'], inplace=True)
                all_seasons_df.append(df)
            except Exception:
                # Si hay un error al procesar, simplemente lo ignoramos en silencio
                pass
    return pd.concat(all_seasons_df, ignore_index=True) if all_seasons_df else pd.DataFrame()

def normalize_team_name(name: str) -> str:
    """Función definitiva que usa un diccionario para estandarizar cualquier nombre de equipo."""
    name_map = {
        'West Ham': 'West Ham', 'West Ham United': 'West Ham', 'Wolves': 'Wolves', 'Wolverhampton Wanderers': 'Wolves',
        'Nott\'m Forest': 'Nottingham Forest', 'Nottingham Forest': 'Nottingham Forest', 'Man United': 'Man United', 'Manchester United': 'Man United',
        'Newcastle': 'Newcastle', 'Newcastle United': 'Newcastle', 'Tottenham': 'Tottenham', 'Tottenham Hotspur': 'Tottenham',
        'Brighton': 'Brighton', 'Brighton & Hove Albion': 'Brighton', 'Leeds': 'Leeds', 'Leeds United': 'Leeds',
        'Leicester': 'Leicester', 'Leicester City': 'Leicester', 'Arsenal': 'Arsenal', 'Everton': 'Everton', 'Liverpool': 'Liverpool',
        'Chelsea': 'Chelsea', 'Crystal Palace': 'Crystal Palace', 'Brentford': 'Brentford', 'Aston Villa': 'Aston Villa', 'Bournemouth': 'Bournemouth', 'Fulham': 'Fulham',
        'Man City': 'Man City', 'Manchester City': 'Man City',
        'Athletic Bilbao': 'Athletic Bilbao', 'Athletic Club': 'Athletic Bilbao', 'Mallorca': 'Mallorca', 'RCD Mallorca': 'Mallorca',
        'Osasuna': 'Osasuna', 'CA Osasuna': 'Osasuna', 'Espanol': 'Espanyol', 'RCD Espanyol': 'Espanyol', 'RCD Espanyol Barcelona': 'Espanyol',
        'Cadiz': 'Cadiz', 'Cádiz CF': 'Cadiz', 'Atletico Madrid': 'Atletico Madrid', 'Atlético Madrid': 'Atletico Madrid',
        'Almeria': 'Almeria', 'UD Almería': 'Almeria', 'Celta Vigo': 'Celta Vigo', 'RC Celta': 'Celta Vigo',
        'Elche': 'Elche', 'Elche CF': 'Elche', 'Betis': 'Real Betis', 'Real Betis': 'Real Betis', 'Real Betis Balompié': 'Real Betis',
        'Real Madrid': 'Real Madrid', 'Sevilla': 'Sevilla', 'Valencia': 'Valencia', 'Girona': 'Girona', 'Getafe': 'Getafe', 'Real Sociedad': 'Real Sociedad',
        'Villarreal': 'Villarreal', 'Rayo Vallecano': 'Rayo Vallecano', 'Las Palmas': 'Las Palmas', 'Alaves': 'Alaves', 'Levante': 'Levante', 'Oviedo': 'Oviedo',
        'Bayern Munich': 'Bayern Munich', 'Bayer Leverkusen': 'Leverkusen', 'Leverkusen': 'Leverkusen',
        'Dortmund': 'Dortmund', 'Borussia Dortmund': 'Dortmund', 'Ein Frankfurt': 'Eintracht Frankfurt', 'Eintracht Frankfurt': 'Eintracht Frankfurt',
        'RB Leipzig': 'RB Leipzig', 'Leipzig': 'RB Leipzig', 'FC Koln': 'FC Koln', 'Koln': 'FC Koln',
        'Inter': 'Inter', 'Inter Milan': 'Inter', 'AC Milan': 'AC Milan', 'Milan': 'AC Milan',
        'Juventus': 'Juventus', 'Roma': 'Roma', 'Napoli': 'Napoli', 'Lazio': 'Lazio',
        'Atalanta': 'Atalanta', 'Fiorentina': 'Fiorentina',
        'Paris SG': 'Paris SG', 'Paris Saint-Germain': 'Paris SG',
        'Marseille': 'Marseille', 'Lyon': 'Lyon', 'Monaco': 'Monaco', 'Lille': 'Lille', 'Rennes': 'Rennes'
    }
    return name_map.get(name, name)

def calculate_team_strengths(df: pd.DataFrame):
    if df.empty: return None
    df['home_team_name'] = df['home_team_name'].apply(normalize_team_name)
    df['away_team_name'] = df['away_team_name'].apply(normalize_team_name)
    avg_home_goals = df['home_team_score'].mean()
    avg_away_goals = df['away_team_score'].mean()
    home_stats = df.groupby('home_team_name').agg(avg_scored=('home_team_score', 'mean'), avg_conceded=('away_team_score', 'mean')).rename_axis('team')
    away_stats = df.groupby('away_team_name').agg(avg_scored=('away_team_score', 'mean'), avg_conceded=('home_team_score', 'mean')).rename_axis('team')
    common_teams = home_stats.index.intersection(away_stats.index)
    team_strengths = pd.merge(home_stats.loc[common_teams], away_stats.loc[common_teams], on='team', suffixes=('_home', '_away'))
    if team_strengths.empty: return None
    team_strengths['attack_strength_home'] = team_strengths['avg_scored_home'] / avg_home_goals
    team_strengths['defense_strength_home'] = team_strengths['avg_conceded_home'] / avg_away_goals
    team_strengths['attack_strength_away'] = team_strengths['avg_scored_away'] / avg_away_goals
    team_strengths['defense_strength_away'] = team_strengths['avg_conceded_away'] / avg_home_goals
    return {'league_avg_home_goals': avg_home_goals, 'league_avg_away_goals': avg_away_goals, 'team_strengths': team_strengths.to_dict('index')}

def predict_outcome(avg_home_goals: float, avg_away_goals: float, max_goals: int = 5):
    home_win_prob, draw_prob, away_win_prob = 0, 0, 0
    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            prob = poisson.pmf(hg, avg_home_goals) * poisson.pmf(ag, avg_away_goals)
            if hg > ag: home_win_prob += prob
            elif hg == ag: draw_prob += prob
            else: away_win_prob += prob
    return {'home_win': home_win_prob, 'draw': draw_prob, 'away_win': away_win_prob}

def calculate_over_under_probs(avg_home_goals: float, avg_away_goals: float, max_goals: int = 6):
    over_2_5_prob = 0
    for home_g in range(max_goals + 1):
        for away_g in range(max_goals + 1):
            prob_scoreline = poisson.pmf(home_g, avg_home_goals) * poisson.pmf(away_g, avg_away_goals)
            if (home_g + away_g) > 2.5:
                over_2_5_prob += prob_scoreline
    return {'over_2.5': over_2_5_prob, 'under_2.5': 1 - over_2_5_prob}

def find_value_bets(prediction: dict, odds: dict) -> list:
    value_bets = []
    MAX_ODDS = 25.0
    home_odds, draw_odds, away_odds = odds.get('home_odds'), odds.get('draw_odds'), odds.get('away_odds')
    if home_odds and home_odds < MAX_ODDS and prediction['home_win'] * home_odds > 1.0: value_bets.append(f"Victoria Local @{home_odds:.2f} (Modelo: {prediction['home_win']:.2%})")
    if draw_odds and draw_odds < MAX_ODDS and prediction['draw'] * draw_odds > 1.0: value_bets.append(f"Empate @{draw_odds:.2f} (Modelo: {prediction['draw']:.2%})")
    if away_odds and away_odds < MAX_ODDS and prediction['away_win'] * away_odds > 1.0: value_bets.append(f"Victoria Visitante @{away_odds:.2f} (Modelo: {prediction['away_win']:.2%})")
    return value_bets

def calculate_kelly_criterion(model_prob: float, odds: float) -> float:
    if odds <= 1.0: return 0.0
    kelly_percentage = ((model_prob * odds) - 1) / (odds - 1)
    return max(0, kelly_percentage)

def get_future_odds_from_api(api_key: str, hours_ahead: int, league_key: str):
    time_now, time_future = datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(hours=hours_ahead)
    commence_time_from, commence_time_to = time_now.strftime('%Y-%m-%dT%H:%M:%SZ'), time_future.strftime('%Y-%m-%dT%H:%M:%SZ')
    uri = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
    params = {'apiKey': api_key, 'regions': settings.REGIONS, 'markets': settings.MARKETS, 'oddsFormat': 'decimal', 'commenceTimeFrom': commence_time_from, 'commenceTimeTo': commence_time_to}
    try:
        response = requests.get(uri, params=params)
        response.raise_for_status()
        return response.json()
    except:
        return []

def main():
    """Analiza TODOS los partidos y devuelve un JSON con la predicción principal y las oportunidades de valor si existen."""
    all_files = settings.HISTORICAL_DATA_FILES + [
        'data/SP1_2025_2026.csv', 'data/E0_2025_2026.csv',
        'data/D1_2025_2026.csv', 'data/I1_2025_2026.csv',
        'data/F1_2025_2026.csv'
    ]
    matches_df = load_and_prepare_data(all_files)
    if matches_df.empty:
        print(json.dumps([{"error": "No se pudieron cargar los datos históricos."}]))
        return
        
    stats = calculate_team_strengths(matches_df)
    if not stats:
        print(json.dumps([{"error": "No se pudieron calcular las fuerzas de los equipos."}]))
        return

    final_results = []
    for league_key in settings.ODDS_API_LEAGUES:
        upcoming_matches = get_future_odds_from_api(settings.ODDS_API_KEY, settings.HOURS_AHEAD, league_key)
        
        for match in upcoming_matches:
            home_team_original, away_team_original = match['home_team'], match['away_team']
            home_team_norm, away_team_norm = normalize_team_name(home_team_original), normalize_team_name(away_team_original)
            
            if home_team_norm in stats['team_strengths'] and away_team_norm in stats['team_strengths']:
                expected_home = stats['team_strengths'][home_team_norm]['attack_strength_home'] * stats['team_strengths'][away_team_norm]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = stats['team_strengths'][away_team_norm]['attack_strength_away'] * stats['team_strengths'][home_team_norm]['defense_strength_home'] * stats['league_avg_away_goals']
                
                prediction_1x2 = predict_outcome(expected_home, expected_away)
                prediction_ou = calculate_over_under_probs(expected_home, expected_away)
                
                # Siempre creamos un informe base para cada partido
                match_report = {
                    "partido": f"{home_team_original} vs {away_team_original}",
                    "prediccion_principal": max(prediction_1x2, key=prediction_1x2.get).replace('home_win', f'Victoria {home_team_original}').replace('away_win', f'Victoria {away_team_original}').replace('draw', 'Empate'),
                    "confianza_modelo": prediction_1x2[max(prediction_1x2, key=prediction_1x2.get)],
                    "oportunidades_valor": []
                }

                # Buscamos valor en mercado 1X2
                value_bets_h2h = []
                bookmaker_h2h = next((b for b in match['bookmakers'] if 'h2h' in [m['key'] for m in b['markets']]), None)
                if bookmaker_h2h:
                    market_h2h = next(m for m in bookmaker_h2h['markets'] if m['key'] == 'h2h')
                    home_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == home_team_original), None)
                    away_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == away_team_original), None)
                    draw_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == 'Draw'), None)
                    value_bets_h2h = find_value_bets(prediction_1x2, {'home_odds': home_odds, 'draw_odds': draw_odds, 'away_odds': away_odds})

                # Buscamos valor en mercado de goles
                value_bets_totals = []
                bookmaker_totals = next((b for b in match['bookmakers'] if 'totals' in [m['key'] for m in b['markets']]), None)
                if bookmaker_totals:
                    market_totals = next((m for m in bookmaker_totals['markets'] if m['key'] == 'totals'), None)
                    over_odds = next((p['price'] for p in market_totals['outcomes'] if p.get('name') == 'Over' and p.get('point') == 2.5), None)
                    under_odds = next((p['price'] for p in market_totals['outcomes'] if p.get('name') == 'Under' and p.get('point') == 2.5), None)
                    if over_odds and (prediction_ou['over_2.5'] * over_odds > 1.0):
                        value_bets_totals.append(f"Más de 2.5 Goles @{over_odds:.2f} (Modelo: {prediction_ou['over_2.5']:.2%})")
                    if under_odds and (prediction_ou['under_2.5'] * under_odds > 1.0):
                        value_bets_totals.append(f"Menos de 2.5 Goles @{under_odds:.2f} (Modelo: {prediction_ou['under_2.5']:.2%})")
                
                all_value_bets = value_bets_h2h + value_bets_totals
                
                if all_value_bets:
                    for bet in all_value_bets:
                        parts = bet.split(" @")
                        bet_type = parts[0]
                        odds_part = parts[1].split(" (Modelo: ")
                        odds = float(odds_part[0])
                        model_prob_str = odds_part[1].replace("%)", "")
                        model_prob = float(model_prob_str) / 100
                        kelly_stake = calculate_kelly_criterion(model_prob, odds)
                        match_report["oportunidades_valor"].append({
                            "tipo": bet_type,
                            "cuota": odds,
                            "probabilidad_modelo": model_prob,
                            "inversion_kelly_sugerida": kelly_stake * 100
                        })
                
                final_results.append(match_report)

    print(json.dumps(final_results, indent=2))

if __name__ == "__main__":
    main()