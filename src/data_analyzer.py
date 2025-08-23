# src/data_analyzer.py (Versión Corregida Final)
import pandas as pd
from src.utils import normalize_team_name # Asegúrate de que esta importación esté

def calculate_team_strengths(df: pd.DataFrame):
    """
    Calcula las fuerzas de ataque y defensa para cada equipo.
    """
    # La línea que filtraba por df['status'] == 'FT' se ha eliminado,
    # ya que los datos del CSV siempre son de partidos finalizados.
    # Ahora trabajamos directamente con el DataFrame 'df'.
    
    if df.empty:
        return None

    df['home_team_name'] = df['home_team_name'].apply(normalize_team_name)
    df['away_team_name'] = df['away_team_name'].apply(normalize_team_name)
    
    avg_home_goals = df['home_team_score'].mean()
    avg_away_goals = df['away_team_score'].mean()
    
    home_stats = df.groupby('home_team_name').agg(avg_scored=('home_team_score', 'mean'), avg_conceded=('away_team_score', 'mean')).rename_axis('team')
    away_stats = df.groupby('away_team_name').agg(avg_scored=('away_team_score', 'mean'), avg_conceded=('home_team_score', 'mean')).rename_axis('team')
    
    # Nos aseguramos de que ambos equipos tengan estadísticas de local y visitante para evitar errores
    common_teams = home_stats.index.intersection(away_stats.index)
    team_strengths = pd.merge(home_stats.loc[common_teams], away_stats.loc[common_teams], on='team', suffixes=('_home', '_away'))
    
    if team_strengths.empty:
        return None

    team_strengths['attack_strength_home'] = team_strengths['avg_scored_home'] / avg_home_goals
    team_strengths['defense_strength_home'] = team_strengths['avg_conceded_home'] / avg_away_goals
    team_strengths['attack_strength_away'] = team_strengths['avg_scored_away'] / avg_away_goals
    team_strengths['defense_strength_away'] = team_strengths['avg_conceded_away'] / avg_home_goals
    
    return {'league_avg_home_goals': avg_home_goals, 'league_avg_away_goals': avg_away_goals, 'team_strengths': team_strengths.to_dict('index')}

def get_h2h_stats(df, team1_norm: str, team2_norm: str) -> dict:
    """
    Calcula las estadísticas de enfrentamientos directos (H2H) entre dos equipos.
    """
    h2h_df = df[((df['home_team_name'] == team1_norm) & (df['away_team_name'] == team2_norm)) | 
                ((df['home_team_name'] == team2_norm) & (df['away_team_name'] == team1_norm))]

    if h2h_df.empty:
        return {'total_matches': 0}

    team1_wins = len(h2h_df[((h2h_df['home_team_name'] == team1_norm) & (h2h_df['home_team_score'] > h2h_df['away_team_score'])) |
                           ((h2h_df['away_team_name'] == team1_norm) & (h2h_df['away_team_score'] > h2h_df['home_team_score']))])
    
    team2_wins = len(h2h_df[((h2h_df['home_team_name'] == team2_norm) & (h2h_df['home_team_score'] > h2h_df['away_team_score'])) |
                           ((h2h_df['away_team_name'] == team2_norm) & (h2h_df['away_team_score'] > h2h_df['home_team_score']))])

    draws = len(h2h_df[h2h_df['home_team_score'] == h2h_df['away_team_score']])
    
    return {
        'total_matches': len(h2h_df),
        'team1_wins': team1_wins,
        'team2_wins': team2_wins,
        'draws': draws
    }



