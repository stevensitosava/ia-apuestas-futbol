from config import settings
from src.utils import load_and_prepare_data, normalize_team_name
from src.data_analyzer import calculate_team_strengths, get_h2h_stats
# Importamos la nueva función para calcular Over/Under
from src.prediction_model import predict_outcome, find_value_bets, calculate_kelly_criterion, calculate_over_under_probs
from src.data_fetcher import get_future_odds_from_api, get_recent_scores_from_api
from src.backtester import run_backtest_sequential, run_financial_backtest_by_league, run_flat_betting_backtest
from datetime import datetime
import pandas as pd
import os

def generar_informe_partido(match: dict, stats: dict, matches_df: pd.DataFrame, prediction: dict) -> str:
    """
    Genera un informe detallado, incluyendo ahora el análisis de goles.
    """
    informe = []
    home_team_original = match['home_team']
    away_team_original = match['away_team']
    match_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))

    informe.append("\n" + "="*50)
    informe.append(f"**{home_team_original} vs {away_team_original}**")
    informe.append(f"🗓️ {match_time.strftime('%A, %d de %B - %H:%M')}")
    informe.append("="*50)

    home_team_norm = normalize_team_name(home_team_original)
    away_team_norm = normalize_team_name(away_team_original)
    h2h = get_h2h_stats(matches_df, home_team_norm, away_team_norm)

    informe.append("\n" + "📊 **Cara a Cara (Historial Reciente):**")
    if h2h['total_matches'] > 0:
        informe.append(f"   - Partidos jugados: {h2h['total_matches']} | Victorias {home_team_original}: {h2h['team1_wins']} | Victorias {away_team_original}: {h2h['team2_wins']} | Empates: {h2h['draws']}")
    else:
        informe.append("   - No hay datos de enfrentamientos directos recientes.")

    team_strengths = stats['team_strengths']
    expected_home = team_strengths[home_team_norm]['attack_strength_home'] * team_strengths[away_team_norm]['defense_strength_away'] * stats['league_avg_home_goals']
    expected_away = team_strengths[away_team_norm]['attack_strength_away'] * team_strengths[home_team_norm]['defense_strength_home'] * stats['league_avg_away_goals']
    
    favorito_modelo = max(prediction, key=prediction.get)
    prob_favorito = prediction[favorito_modelo]
    if favorito_modelo == 'home_win': favorito_texto = f"Victoria de **{home_team_original}**"
    elif favorito_modelo == 'draw': favorito_texto = "**Empate**"
    else: favorito_texto = f"Victoria de **{away_team_original}**"

    informe.append("\n" + "🔮 **Predicción Principal del Modelo (Resultado):**")
    informe.append(f"   - El resultado más probable es **{favorito_texto}** con una probabilidad del **{prob_favorito:.1%}**.")
    informe.append(f"   - _Goles esperados: {expected_home:.2f} - {expected_away:.2f}_")
    
    # --- NUEVO: ANÁLISIS DE GOLES (OVER/UNDER 2.5) ---
    over_under_probs = calculate_over_under_probs(expected_home, expected_away)
    informe.append("\n" + "⚽ **Predicción de Goles (Más/Menos 2.5):**")
    informe.append(f"   - Probabilidad de Más de 2.5 goles: **{over_under_probs['over_2.5']:.1%}**")
    informe.append(f"   - Probabilidad de Menos de 2.5 goles: **{over_under_probs['under_2.5']:.1%}**")

    # --- OPORTUNIDADES DE VALOR (AMBOS MERCADOS) ---
    informe.append("\n" + "💎 **Oportunidades de Valor Detectadas:**")
    
    value_bets_h2h = []
    bookmaker_h2h = next((b for b in match['bookmakers'] if 'h2h' in [m['key'] for m in b['markets']]), None)
    if bookmaker_h2h:
        market_h2h = next(m for m in bookmaker_h2h['markets'] if m['key'] == 'h2h')
        home_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == home_team_original), None)
        away_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == away_team_original), None)
        draw_odds = next((p['price'] for p in market_h2h['outcomes'] if p['name'] == 'Draw'), None)
        value_bets_h2h = find_value_bets(prediction, {'home_odds': home_odds, 'draw_odds': draw_odds, 'away_odds': away_odds})

    value_bets_totals = []
    bookmaker_totals = next((b for b in match['bookmakers'] if 'totals' in [m['key'] for m in b['markets']]), None)
    if bookmaker_totals:
        market_totals = next((m for m in bookmaker_totals['markets'] if m['key'] == 'totals'), None)
        over_odds = next((p['price'] for p in market_totals['outcomes'] if p.get('name') == 'Over' and p.get('point') == 2.5), None)
        under_odds = next((p['price'] for p in market_totals['outcomes'] if p.get('name') == 'Under' and p.get('point') == 2.5), None)
        
        if over_odds and (over_under_probs['over_2.5'] * over_odds > 1.0):
            value_bets_totals.append(f"Más de 2.5 Goles @{over_odds:.2f} (Modelo: {over_under_probs['over_2.5']:.2%})")
        if under_odds and (over_under_probs['under_2.5'] * under_odds > 1.0):
            value_bets_totals.append(f"Menos de 2.5 Goles @{under_odds:.2f} (Modelo: {over_under_probs['under_2.5']:.2%})")

    all_value_bets = value_bets_h2h + value_bets_totals
    
    if not all_value_bets:
        informe.append("_No se ha encontrado una oportunidad clara de valor en los mercados principales._")
    else:
        informe.append("_Estas son apuestas donde el modelo cree que la cuota es desproporcionadamente alta para el riesgo que representa._")
        for bet_string in all_value_bets:
            parts = bet_string.split(" @")
            bet_type = parts[0]
            odds_part = parts[1].split(" (Modelo: ")
            odds = float(odds_part[0])
            model_prob = float(odds_part[1].replace("%)", "")) / 100
            kelly_stake = calculate_kelly_criterion(model_prob, odds)
            value_edge = (model_prob * odds) - 1
            if value_edge > 0.5: nivel = "⭐⭐⭐ (Muy Alta)"
            elif value_edge > 0.2: nivel = "⭐⭐ (Buena)"
            else: nivel = "⭐ (Pequeña Ventaja)"
            informe.append(f"\n- **{bet_type}:** Cuota **{odds:.2f}**. Nivel de Oportunidad: {nivel}")
            informe.append(f"  - **📈 Apuesta Sugerida (Kelly):** Invertir un **{kelly_stake:.2%}** de tu bankroll.")

    return "\n".join(informe)

def save_prediction(match: dict, prediction: dict):
    log_file = 'predictions_log.csv'
    match_id = f"{match['commence_time']}-{match['home_team']}-{match['away_team']}"
    favorito_modelo = max(prediction, key=prediction.get)
    if favorito_modelo == 'home_win': resultado_predicho = '1'
    elif favorito_modelo == 'draw': resultado_predicho = 'X'
    else: resultado_predicho = '2'
    log_entry = {'id': match_id, 'date': match['commence_time'], 'home_team': match['home_team'], 'away_team': match['away_team'], 'predicted_outcome': resultado_predicho, 'model_confidence': prediction[favorito_modelo], 'status': 'PENDIENTE', 'actual_outcome': None, 'is_correct': None}
    try:
        log_df = pd.read_csv(log_file) if os.path.exists(log_file) else pd.DataFrame(columns=log_entry.keys())
        if log_entry['id'] not in log_df['id'].values:
            new_log_df = pd.DataFrame([log_entry])
            updated_log = pd.concat([log_df, new_log_df], ignore_index=True)
            updated_log.to_csv(log_file, index=False)
    except Exception as e:
        print(f"Error al guardar predicción: {e}")

def run_analysis():
    all_files = settings.HISTORICAL_DATA_FILES + ['data/SP1_2025_2026.csv', 'data/E0_2025_2026.csv'] # Y otras ligas
    matches_df = load_and_prepare_data(all_files)
    if matches_df.empty: return "❌ No se encontraron datos históricos."
    informe_inicial = [f"✅ Modelo entrenado con {len(matches_df)} partidos históricos."]
    stats = calculate_team_strengths(matches_df)
    if not stats: return "❌ No se pudieron calcular las fuerzas de los equipos."
    informe_inicial.append(f"\n📡 Obteniendo cuotas para partidos en las próximas {settings.HOURS_AHEAD} horas...")
    informes = []
    partidos_encontrados = 0
    for league_key in settings.ODDS_API_LEAGUES:
        upcoming_matches = get_future_odds_from_api(settings.ODDS_API_KEY, league_key, settings.REGIONS, settings.MARKETS, settings.HOURS_AHEAD)
        for match in upcoming_matches:
            partidos_encontrados += 1
            home_team_norm, away_team_norm = normalize_team_name(match['home_team']), normalize_team_name(match['away_team'])
            if home_team_norm in stats['team_strengths'] and away_team_norm in stats['team_strengths']:
                expected_home = stats['team_strengths'][home_team_norm]['attack_strength_home'] * stats['team_strengths'][away_team_norm]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = stats['team_strengths'][away_team_norm]['attack_strength_away'] * stats['team_strengths'][home_team_norm]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                save_prediction(match, prediction)
                informe = generar_informe_partido(match, stats, matches_df, prediction)
                informes.append(informe)
    if partidos_encontrados == 0:
        informe_inicial.append("\nNo se han encontrado próximos partidos con cuotas en las APIs.")
    elif not informes:
        informe_inicial.append("\nSe encontraron partidos, pero nuestro modelo no tiene datos históricos para los equipos involucrados.")
    else:
        informe_inicial.append("\n\n" + "\n\n".join(informes))
    return "\n".join(informe_inicial)

def run_analysis():
    # ... (código sin cambios)
    all_files = settings.HISTORICAL_DATA_FILES + ['data/SP1_2025_2026.csv', 'data/E0_2025_2026.csv']
    matches_df = load_and_prepare_data(all_files)
    if matches_df.empty: return "❌ No se encontraron datos históricos."
    informe_inicial = [f"✅ Modelo entrenado con {len(matches_df)} partidos históricos."]
    stats = calculate_team_strengths(matches_df)
    if not stats: return "❌ No se pudieron calcular las fuerzas de los equipos."
    informe_inicial.append(f"\n📡 Obteniendo cuotas para partidos en las próximas {settings.HOURS_AHEAD} horas...")
    informes = []
    partidos_encontrados = 0
    for league_key in settings.ODDS_API_LEAGUES:
        upcoming_matches = get_future_odds_from_api(settings.ODDS_API_KEY, league_key, settings.REGIONS, settings.MARKETS, settings.HOURS_AHEAD)
        for match in upcoming_matches:
            partidos_encontrados += 1
            home_team_norm, away_team_norm = normalize_team_name(match['home_team']), normalize_team_name(match['away_team'])
            if home_team_norm in stats['team_strengths'] and away_team_norm in stats['team_strengths']:
                expected_home = stats['team_strengths'][home_team_norm]['attack_strength_home'] * stats['team_strengths'][away_team_norm]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = stats['team_strengths'][away_team_norm]['attack_strength_away'] * stats['team_strengths'][home_team_norm]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                save_prediction(match, prediction)
                informe = generar_informe_partido(match, stats, matches_df, prediction)
                informes.append(informe)
    if partidos_encontrados == 0:
        informe_inicial.append("\nNo se han encontrado próximos partidos con cuotas en las APIs.")
    elif not informes:
        informe_inicial.append("\nSe encontraron partidos, pero nuestro modelo no tiene datos históricos para los equipos involucrados.")
    else:
        informe_inicial.append("\n\n" + "\n\n".join(informes))
    return "\n".join(informe_inicial)

def run_review_predictions():
    # ... (código sin cambios)
    log_file = 'predictions_log.csv'
    output_log = ["--- 📖 Iniciando Revisión de Predicciones ---"]
    try: log_df = pd.read_csv(log_file)
    except FileNotFoundError: return "❌ No se encontró el diario de predicciones."
    pending_predictions = log_df[log_df['status'] == 'PENDIENTE']
    if pending_predictions.empty: return "✅ No hay predicciones nuevas que revisar."
    output_log.append(f"Revisando {len(pending_predictions)} predicciones pendientes...")
    all_scores = []
    for league in settings.ODDS_API_LEAGUES:
        all_scores.extend(get_recent_scores_from_api(settings.ODDS_API_KEY, league, days_ago=3))
    if not all_scores: return "No se pudieron obtener resultados recientes."
    aciertos, fallos = 0, 0
    for index, row in pending_predictions.iterrows():
        home_team_log_norm, away_team_log_norm = normalize_team_name(row['home_team']), normalize_team_name(row['away_team'])
        date_to_find = row['date'][:10]
        match_result = None
        for s in all_scores:
            if s.get('completed'):
                home_team_api_norm, away_team_api_norm = normalize_team_name(s.get('home_team', '')), normalize_team_name(s.get('away_team', ''))
                api_date = s['commence_time'][:10]
                if (home_team_api_norm == home_team_log_norm and away_team_api_norm == away_team_log_norm and api_date == date_to_find):
                    match_result = s
                    break
        if match_result and match_result.get('scores'):
            home_team_original_api, away_team_original_api = match_result['home_team'], match_result['away_team']
            home_score = next((int(s['score']) for s in match_result['scores'] if s['name'] == home_team_original_api), None)
            away_score = next((int(s['score']) for s in match_result['scores'] if s['name'] == away_team_original_api), None)
            if home_score is not None and away_score is not None:
                if home_score > away_score: actual_outcome = '1'
                elif home_score == away_score: actual_outcome = 'X'
                else: actual_outcome = '2'
                log_df.loc[index, 'status'] = 'REVISADO'
                log_df.loc[index, 'actual_outcome'] = actual_outcome
                if row['predicted_outcome'] == actual_outcome:
                    log_df.loc[index, 'is_correct'], aciertos = True, aciertos + 1
                else:
                    log_df.loc[index, 'is_correct'], fallos = False, fallos + 1
    log_df.to_csv(log_file, index=False)
    output_log.append(f"\n--- Resumen de la Revisión ---\nAciertos: {aciertos} | Fallos: {fallos}")
    if (aciertos + fallos) > 0:
        precision = (aciertos / (aciertos + fallos)) * 100
        output_log.append(f"Precisión en esta revisión: {precision:.2f}%")
    output_log.append("✅ Diario de predicciones actualizado.")
    return "\n".join(output_log)

def run_update():
    # ... (código sin cambios)
    output_log = ["--- 🧠 Iniciando Sistema de Aprendizaje (Actualizador de Datos) ---"]
    league_map = {'soccer_spain_la_liga': {'file': 'data/SP1_2025_2026.csv', 'name': 'La Liga'}, 'soccer_epl': {'file': 'data/E0_2025_2026.csv', 'name': 'Premier League'}}
    for league_key, info in league_map.items():
        output_log.append(f"\n🔄 Buscando nuevos resultados para {info['name']}...")
        scores = get_recent_scores_from_api(settings.ODDS_API_KEY, league_key)
        new_results = []
        for game in scores:
            if game.get('completed') and game.get('scores'):
                home_team, away_team = game['scores'][0]['name'], game['scores'][1]['name']
                if home_team and away_team:
                    new_results.append({'Date': datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d/%m/%Y'), 'HomeTeam': home_team, 'AwayTeam': away_team, 'FTHG': int(game['scores'][0]['score']), 'FTAG': int(game['scores'][1]['score']), 'B365H': None, 'B365D': None, 'B365A': None})
        if not new_results:
            output_log.append("No se encontraron nuevos resultados finalizados.")
            continue
        try:
            try: df = pd.read_csv(info['file'])
            except FileNotFoundError: df = pd.DataFrame()
            new_df = pd.DataFrame(new_results)
            updated_df = pd.concat([df, new_df]).drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last')
            updated_df.to_csv(info['file'], index=False)
            num_added = len(updated_df) - len(df)
            output_log.append(f"✅ ¡Hecho! Se han añadido {num_added} nuevos partidos a {info['file']}.")
        except Exception as e:
            output_log.append(f"❌ Error al guardar los datos en el archivo CSV: {e}")
    return "\n".join(output_log)

# --- FUNCIONES DE BACKTEST CORREGIDAS ---
def run_backtest_logic():
    """Ejecuta el backtest de PRECISIÓN."""
    full_df = load_and_prepare_data(settings.HISTORICAL_DATA_FILES)
    if full_df.empty: return "No se encontraron datos históricos para evaluar."
    season_start_years = sorted(full_df[full_df['utc_date'].dt.month > 7]['utc_date'].dt.year.unique())
    seasons_to_test = season_start_years[1:]
    if not seasons_to_test: return "Se necesita al menos dos temporadas de datos para realizar un backtest."
    report = run_backtest_sequential(files=settings.HISTORICAL_DATA_FILES, seasons_to_test=seasons_to_test)
    return report

def run_financial_backtest_logic():
    """Ejecuta el backtest FINANCIERO."""
    full_df = load_and_prepare_data(settings.HISTORICAL_DATA_FILES)
    if full_df.empty: return "No se encontraron datos históricos para evaluar."
    season_start_years = sorted(full_df[full_df['utc_date'].dt.month > 7]['utc_date'].dt.year.unique())
    seasons_to_test = season_start_years[1:]
    if not seasons_to_test: return "Se necesita al menos dos temporadas de datos para realizar un backtest."
    # --- LLAMADA CORREGIDA ---
    # Usamos la temporada más reciente para la simulación financiera
    latest_test_season = seasons_to_test[-1] if seasons_to_test else None
    if not latest_test_season:
        return "No hay una temporada reciente contra la que probar la rentabilidad."
    report = run_financial_backtest_by_league(files=settings.HISTORICAL_DATA_FILES, test_season_start_year=latest_test_season)
    return report

def run_flat_backtest_logic():
    """
    Ejecuta el backtest de Apuesta Fija.
    """
    report = run_flat_betting_backtest(
        files=settings.HISTORICAL_DATA_FILES,
        test_season_start_year=2024
    )
    return report