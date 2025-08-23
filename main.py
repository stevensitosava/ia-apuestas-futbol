# main.py (Versión Final con Informes Detallados)
from config import settings
from datetime import datetime
# Importamos las nuevas funciones
from src.utils import load_and_prepare_data, normalize_team_name
from src.data_analyzer import calculate_team_strengths, get_h2h_stats
from src.prediction_model import predict_outcome, find_value_bets
from src.data_fetcher import get_future_odds_from_api
from src.explanation_generator import generar_analisis_completo

def main():
    print("--- Iniciando IA de Apuestas v6.0 (con Informes Detallados) ---")

    matches_df = load_and_prepare_data(settings.HISTORICAL_DATA_FILES)
    if matches_df.empty: return

    print(f"✅ Modelo entrenado con {len(matches_df)} partidos históricos.")
    stats = calculate_team_strengths(matches_df)
    if not stats: return

    print(f"\n📡 Obteniendo cuotas para partidos en las próximas {settings.HOURS_AHEAD} horas...")
    for league_key in settings.ODDS_API_LEAGUES:
        upcoming_matches = get_future_odds_from_api(settings.ODDS_API_KEY, league_key, settings.REGIONS, settings.MARKETS, settings.HOURS_AHEAD)
        league_name = league_key.replace('_', ' ').replace('soccer', '').replace('epl', 'Premier League').title()
        if not upcoming_matches:
            print(f"\nNo se encontraron próximos partidos con cuotas para {league_name}.")
            continue

        print(f"\n--- 🔍 Analizando Apuestas para: {league_name} ---")
        for match in sorted(upcoming_matches, key=lambda x: x['commence_time']):
            home_team_original = match['home_team']
            away_team_original = match['away_team']
            home_team_norm = normalize_team_name(home_team_original)
            away_team_norm = normalize_team_name(away_team_original)

            team_strengths = stats['team_strengths']
            if home_team_norm in team_strengths and away_team_norm in team_strengths:
                bookmaker, market = match['bookmakers'][0], match['bookmakers'][0]['markets'][0]
                home_odds = next((p['price'] for p in market['outcomes'] if p['name'] == home_team_original), None)
                away_odds = next((p['price'] for p in market['outcomes'] if p['name'] == away_team_original), None)
                draw_odds = next((p['price'] for p in market['outcomes'] if p['name'] == 'Draw'), None)
                if not all((home_odds, away_odds, draw_odds)): continue

                expected_home = team_strengths[home_team_norm]['attack_strength_home'] * team_strengths[away_team_norm]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = team_strengths[away_team_norm]['attack_strength_away'] * team_strengths[home_team_norm]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                value_bets = find_value_bets(prediction, {'home_odds': home_odds, 'draw_odds': draw_odds, 'away_odds': away_odds})

                if value_bets:
                    match_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
                    print(f"\n{'='*50}")
                    print(f"💎 ¡Valor encontrado para {home_team_original} vs {away_team_original}!")
                    print(f"   🗓️  {match_time.strftime('%A, %d de %B - %H:%M')}")

                    # Obtenemos las estadísticas H2H y generamos el informe
                    h2h = get_h2h_stats(matches_df, home_team_norm, away_team_norm)
                    expected_goals = {'home': expected_home, 'away': expected_away}
                    informe = generar_analisis_completo(prediction, value_bets, h2h, home_team_original, away_team_original, expected_goals)

                    print(informe) # Imprimimos el informe completo

                    print("\n" + "🎯 Oportunidades de Valor Identificadas:")
                    for bet in value_bets: print(f"  -> {bet}")
                    print(f"{'='*50}")

if __name__ == "__main__":
    main()

