# src/backtester.py (Versión Final Corregida)

import pandas as pd
from datetime import datetime
import os
from src.utils import load_and_prepare_data, normalize_team_name
from src.data_analyzer import calculate_team_strengths
from src.prediction_model import predict_outcome, find_value_bets, calculate_kelly_criterion

def run_backtest_sequential(files: list, seasons_to_test: list) -> str:
    # ... (esta función ya estaba correcta y no cambia)
    report_log = ["="*50, "🔬 INICIANDO BACKTEST DE PRECISIÓN 🔬", "="*50]
    full_df = load_and_prepare_data(files)
    if full_df.empty: return "❌ No se pudieron cargar los datos."
    season_results = []
    for test_season_start_year in seasons_to_test:
        report_log.append(f"\n--- EXAMEN DE LA TEMPORADA {test_season_start_year}/{test_season_start_year+1} ---")
        train_df = full_df[full_df['utc_date'] < f'{test_season_start_year}-08-01']
        test_start_date, test_end_date = f'{test_season_start_year}-08-01', f'{test_season_start_year+1}-07-31'
        test_df = full_df[(full_df['utc_date'] >= test_start_date) & (full_df['utc_date'] <= test_end_date)]
        if train_df.empty or test_df.empty:
            report_log.append("  - No hay suficientes datos para esta combinación.")
            continue
        stats = calculate_team_strengths(train_df.copy())
        if not stats: continue
        report_log.append(f"  - Materia de Estudio: {len(train_df)} partidos.")
        team_strengths = stats['team_strengths']
        correct_predictions, hc_correct, hc_total, total_tested = 0, 0, 0, 0
        for index, match in test_df.iterrows():
            home_team, away_team = normalize_team_name(match['home_team_name']), normalize_team_name(match['away_team_name'])
            if home_team in team_strengths and away_team in team_strengths:
                total_tested += 1
                expected_home = team_strengths[home_team]['attack_strength_home'] * team_strengths[away_team]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = team_strengths[away_team]['attack_strength_away'] * team_strengths[home_team]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                predicted_outcome = max(prediction, key=prediction.get)
                actual_home, actual_away = match['home_team_score'], match['away_team_score']
                actual_outcome = 'home_win' if actual_home > actual_away else 'draw' if actual_home == actual_away else 'away_win'
                if predicted_outcome == actual_outcome: correct_predictions += 1
                if prediction[predicted_outcome] > 0.55:
                    hc_total += 1
                    if predicted_outcome == actual_outcome: hc_correct += 1
        if total_tested == 0: continue
        accuracy = (correct_predictions / total_tested) * 100
        hc_accuracy = (hc_correct / hc_total) * 100 if hc_total > 0 else 0
        report_log.append(f"  - 🎯 Nota de Precisión General: {accuracy:.2f}%")
        season_results.append({'season': f"{test_season_start_year}/{test_season_start_year+1}", 'accuracy': accuracy})
        try:
            log_entry = pd.DataFrame([{'timestamp': datetime.now(), 'season_tested': f"{test_season_start_year}/{test_season_start_year+1}", 'accuracy': accuracy,'hc_accuracy': hc_accuracy}])
            log_df = pd.read_csv('performance_log.csv') if os.path.exists('performance_log.csv') else pd.DataFrame()
            updated_log = pd.concat([log_df, log_entry]).drop_duplicates(subset=['season_tested'], keep='last')
            updated_log.to_csv('performance_log.csv', index=False)
        except: pass
    if len(season_results) > 1:
        last_result, previous_result = season_results[-1], season_results[-2]
        report_log.append("\n" + "="*50)
        report_log.append("💡 CONCLUSIÓN DE LA EVOLUCIÓN:")
        if last_result['accuracy'] > previous_result['accuracy'] + 1:
            conclusion = f"El modelo MEJORÓ su rendimiento en la temporada {last_result['season']} en comparación con la anterior."
        elif last_result['accuracy'] < previous_result['accuracy'] - 1:
            conclusion = f"El modelo fue MENOS preciso en la temporada {last_result['season']} que en la anterior."
        else:
            conclusion = "El modelo mantuvo un rendimiento ESTABLE y consistente."
        report_log.append(conclusion)
        report_log.append("="*50)
    return "\n".join(report_log)


def run_financial_backtest_by_league(
    files: list, 
    test_season_start_year: int, 
    initial_bankroll: float = 100.0, 
    kelly_fraction: float = 0.5,
    min_edge: float = 0.05
) -> str:
    """
    Backtester FINANCIERO. Simula la estrategia Kelly por ligas.
    """
    report_log = ["="*50, "📈 INICIANDO BACKTEST FINANCIERO AVANZADO 📈", "="*50]
    full_df = load_and_prepare_data(files)
    if full_df.empty: return "❌ No se pudieron cargar los datos."
    train_df = full_df[full_df['utc_date'] < f'{test_season_start_year}-08-01']
    test_start_date, test_end_date = f'{test_season_start_year}-08-01', f'{test_season_start_year+1}-07-31'
    test_df = full_df[(full_df['utc_date'] >= test_start_date) & (full_df['utc_date'] <= test_end_date)].copy()
    if train_df.empty or test_df.empty: return "❌ No hay suficientes datos para separar en temporadas."
    stats = calculate_team_strengths(train_df)
    if not stats: return "❌ No se pudieron calcular las fuerzas de los equipos."
    report_log.append(f"🧠 Modelo entrenado con {len(train_df)} partidos.")
    report_log.append(f"🏦 Bankroll Inicial por Liga: {initial_bankroll:.2f} | Fracción Kelly: {kelly_fraction}x | Edge Mínimo: {min_edge:.1%}")
    league_name_map = {'SP1': 'La Liga', 'E0': 'Premier League', 'D1': 'Bundesliga', 'I1': 'Serie A', 'F1': 'Ligue 1'}
    leagues_to_test = test_df['league_code'].unique()
    for league_code in leagues_to_test:
        league_name = league_name_map.get(league_code, f"Liga Desconocida ({league_code})")
        league_test_df = test_df[test_df['league_code'] == league_code]
        report_log.append(f"\n--- {league_name} | Temporada {test_season_start_year}/{test_season_start_year+1} ---")
        bankroll, bets_placed, total_staked = initial_bankroll, 0, 0.0
        for index, match in league_test_df.sort_values(by='utc_date').iterrows():
            home_team, away_team = normalize_team_name(match['home_team_name']), normalize_team_name(match['away_team_name'])
            if home_team in stats['team_strengths'] and away_team in stats['team_strengths']:
                expected_home = stats['team_strengths'][home_team]['attack_strength_home'] * stats['team_strengths'][away_team]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = stats['team_strengths'][away_team]['attack_strength_away'] * stats['team_strengths'][home_team]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                odds = {'home_win_odds': match['home_win_odds'], 'draw_odds': match['draw_odds'], 'away_win_odds': match['away_win_odds']}
                value_bets = find_value_bets(prediction, odds)
                if value_bets:
                    bet_string = value_bets[0]
                    
                    # --- LÍNEA CORREGIDA ---
                    parts = bet_string.split(" @")
                    bet_type = parts[0]
                    # ------------------------

                    odds_part = parts[1].split(" (Modelo: ")
                    bet_odds = float(odds_part[0])
                    
                    model_prob = float(odds_part[1].replace("%)", "")) / 100
                    edge = (model_prob * bet_odds) - 1
                    if edge >= min_edge:
                        kelly_stake_percent = calculate_kelly_criterion(model_prob, bet_odds)
                        stake = bankroll * (kelly_stake_percent * kelly_fraction)
                        if stake > 0:
                            bets_placed += 1
                            total_staked += stake
                            bankroll -= stake
                            actual_home, actual_away = match['home_team_score'], match['away_team_score']
                            if (bet_type == "Victoria Local" and actual_home > actual_away) or \
                               (bet_type == "Empate" and actual_home == actual_away) or \
                               (bet_type == "Victoria Visitante" and actual_home < actual_away):
                                winnings = stake * bet_odds
                                bankroll += winnings
        profit_loss = bankroll - initial_bankroll
        roi = (profit_loss / total_staked) * 100 if total_staked > 0 else 0
        report_log.append(f"  - Resultado: Bankroll Final: {bankroll:.2f} | P/L: {profit_loss:+.2f} | ROI: {roi:+.2f}%")
        
        # Guardamos el resultado en el log financiero
        try:
            log_entry = pd.DataFrame([{'season_simulated': f"{test_season_start_year}/{test_season_start_year+1}", 'league': league_name, 'final_bankroll': bankroll, 'profit_loss': profit_loss, 'roi_percent': roi}])
            log_file = 'financial_log.csv'
            log_df = pd.read_csv(log_file) if os.path.exists(log_file) else pd.DataFrame()
            updated_log = pd.concat([log_df, log_entry]).drop_duplicates(subset=['season_simulated', 'league'], keep='last')
            updated_log.to_csv(log_file, index=False)
        except Exception as e:
            report_log.append(f"  - ❌ No se pudo guardar el log: {e}")

    report_log.append("\n💾 Rentabilidad guardada. La gráfica se actualizará.")
    return "\n".join(report_log)

def run_flat_betting_backtest(
    files: list, 
    test_season_start_year: int, 
    initial_bankroll: float = 100.0,
    stake_per_bet: float = 1.0, # Apostamos 1 unidad fija
    min_edge: float = 0.05
) -> str:
    """
    Simula una estrategia de Apuesta Fija (Flat Betting) y calcula la rentabilidad.
    """
    report_log = ["="*50, "⚖️ INICIANDO BACKTEST DE APUESTA FIJA (FLAT) ⚖️", "="*50]
    full_df = load_and_prepare_data(files)
    if full_df.empty: return "❌ No se pudieron cargar los datos."
    
    train_df = full_df[full_df['utc_date'] < f'{test_season_start_year}-08-01']
    test_start_date, test_end_date = f'{test_season_start_year}-08-01', f'{test_season_start_year+1}-07-31'
    test_df = full_df[(full_df['utc_date'] >= test_start_date) & (full_df['utc_date'] <= test_end_date)].copy()
    
    if train_df.empty or test_df.empty: return "❌ No hay suficientes datos para separar en temporadas."
    stats = calculate_team_strengths(train_df)
    if not stats: return "❌ No se pudieron calcular las fuerzas de los equipos."

    report_log.append(f"🧠 Modelo entrenado con {len(train_df)} partidos.")
    report_log.append(f"🏦 Bankroll Inicial por Liga: {initial_bankroll:.2f} | Apuesta Fija: {stake_per_bet:.2f} ud. | Edge Mínimo: {min_edge:.1%}")
    
    league_name_map = {'SP1': 'La Liga', 'E0': 'Premier League', 'D1': 'Bundesliga', 'I1': 'Serie A', 'F1': 'Ligue 1'}
    leagues_to_test = test_df['league_code'].unique()

    for league_code in leagues_to_test:
        league_name = league_name_map.get(league_code, f"Liga Desconocida ({league_code})")
        league_test_df = test_df[test_df['league_code'] == league_code]
        
        report_log.append(f"\n--- {league_name} | Temporada {test_season_start_year}/{test_season_start_year+1} ---")
        
        bankroll, bets_placed, total_staked = initial_bankroll, 0, 0.0
        
        for index, match in league_test_df.sort_values(by='utc_date').iterrows():
            home_team, away_team = normalize_team_name(match['home_team_name']), normalize_team_name(match['away_team_name'])
            
            if home_team in stats['team_strengths'] and away_team in stats['team_strengths']:
                expected_home = stats['team_strengths'][home_team]['attack_strength_home'] * stats['team_strengths'][away_team]['defense_strength_away'] * stats['league_avg_home_goals']
                expected_away = stats['team_strengths'][away_team]['attack_strength_away'] * stats['team_strengths'][home_team]['defense_strength_home'] * stats['league_avg_away_goals']
                prediction = predict_outcome(expected_home, expected_away)
                odds = {'home_win_odds': match['home_win_odds'], 'draw_odds': match['draw_odds'], 'away_win_odds': match['away_win_odds']}
                value_bets = find_value_bets(prediction, odds)

                if value_bets:
                    bet_string = value_bets[0]

                    parts = bet_string.split(" @")
                    bet_type = parts[0]
                    
                    # --- LÍNEA CORREGIDA ---
                    odds_part = parts[1].split(" (Modelo: ")
                    bet_odds = float(odds_part[0])
                    # ------------------------

                    model_prob = float(odds_part[1].replace("%)", "")) / 100
                    
                    edge = (model_prob * bet_odds) - 1
                    if edge >= min_edge:
                        stake = stake_per_bet
                        bets_placed += 1
                        total_staked += stake
                        bankroll -= stake
                        actual_home, actual_away = match['home_team_score'], match['away_team_score']
                        if (bet_type == "Victoria Local" and actual_home > actual_away) or \
                           (bet_type == "Empate" and actual_home == actual_away) or \
                           (bet_type == "Victoria Visitante" and actual_home < actual_away):
                            winnings = stake * bet_odds
                            bankroll += winnings

        profit_loss = bankroll - initial_bankroll
        roi = (profit_loss / total_staked) * 100 if total_staked > 0 else 0
        
        report_log.append(f"  - Resultado: Bankroll Final: {bankroll:.2f} | P/L: {profit_loss:+.2f} | ROI: {roi:+.2f}%")

    return "\n".join(report_log)
    