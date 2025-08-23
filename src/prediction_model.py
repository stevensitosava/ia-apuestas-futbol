# src/prediction_model.py

"""
Módulo para el modelo de predicción de partidos usando la distribución de Poisson.
"""

from scipy.stats import poisson

def predict_outcome(avg_home_goals: float, avg_away_goals: float, max_goals: int = 5) -> dict:
    """
    Calcula la probabilidad de victoria local, empate y victoria visitante.

    Args:
        avg_home_goals (float): La media de goles del equipo que juega en casa.
        avg_away_goals (float): La media de goles del equipo que juega fuera.
        max_goals (int): El número máximo de goles a simular para cada equipo.

    Returns:
        dict: Un diccionario con las probabilidades de 'home_win', 'draw', 'away_win'.
    """
    home_win_prob = 0
    draw_prob = 0
    away_win_prob = 0

    # Itera sobre todos los posibles goles del equipo local (de 0 a max_goals)
    for home_goals in range(max_goals + 1):
        # Itera sobre todos los posibles goles del equipo visitante
        for away_goals in range(max_goals + 1):
            # Calcula la probabilidad de que se dé exactamente ese número de goles
            prob_home = poisson.pmf(home_goals, avg_home_goals)
            prob_away = poisson.pmf(away_goals, avg_away_goals)
            
            # La probabilidad del resultado (ej. 2-1) es la multiplicación de ambas
            prob_scoreline = prob_home * prob_away
            
            # Acumula la probabilidad en la categoría correspondiente
            if home_goals > away_goals:
                home_win_prob += prob_scoreline
            elif home_goals == away_goals:
                draw_prob += prob_scoreline
            else:
                away_win_prob += prob_scoreline
                
    return {
        'home_win': home_win_prob,
        'draw': draw_prob,
        'away_win': away_win_prob
    }

# Añade esta función al final de tu archivo src/prediction_model.py

def find_value_bets(prediction: dict, odds: dict) -> list:
    """
    Compara las probabilidades del modelo con las cuotas para encontrar apuestas de valor.

    Args:
        prediction (dict): Probabilidades del modelo {'home_win', 'draw', 'away_win'}.
        odds (dict): Cuotas del partido {'home_odds', 'draw_odds', 'away_odds'}.

    Returns:
        list: Una lista de strings describiendo las apuestas de valor encontradas.
    """
    value_bets = []

    # Comprobar valor en la victoria local
    if odds.get('home_odds') and prediction['home_win'] * odds['home_odds'] > 1.0:
        value_bets.append(
            f"Victoria Local @{odds['home_odds']:.2f} (Modelo: {prediction['home_win']:.2%})"
        )

    # Comprobar valor en el empate
    if odds.get('draw_odds') and prediction['draw'] * odds['draw_odds'] > 1.0:
        value_bets.append(
            f"Empate @{odds['draw_odds']:.2f} (Modelo: {prediction['draw']:.2%})"
        )

    # Comprobar valor en la victoria visitante
    if odds.get('away_odds') and prediction['away_win'] * odds['away_odds'] > 1.0:
        value_bets.append(
            f"Victoria Visitante @{odds['away_odds']:.2f} (Modelo: {prediction['away_win']:.2%})"
        )

    return value_bets

def calculate_kelly_criterion(model_prob: float, odds: float) -> float:
    """
    Calcula el porcentaje del bankroll a apostar según el Criterio de Kelly.
    """
    if odds <= 1.0:
        return 0.0
    
    # Fórmula de Kelly: (probabilidad_de_ganar * cuota - 1) / (cuota - 1)
    kelly_percentage = ((model_prob * odds) - 1) / (odds - 1)
    
    # Solo devolvemos valores positivos (si no, no hay valor)
    return max(0, kelly_percentage)

def calculate_over_under_probs(avg_home_goals: float, avg_away_goals: float, max_goals: int = 6):
    """
    Calcula la probabilidad de que haya más o menos de 2.5 goles.
    """
    over_2_5_prob = 0
    # Iteramos sobre todos los posibles marcadores
    for home_g in range(max_goals + 1):
        for away_g in range(max_goals + 1):
            prob_scoreline = poisson.pmf(home_g, avg_home_goals) * poisson.pmf(away_g, avg_away_goals)
            # Si la suma de goles es 3 o más, la añadimos a la probabilidad de "Más de 2.5"
            if (home_g + away_g) > 2.5:
                over_2_5_prob += prob_scoreline

    return {
        'over_2.5': over_2_5_prob,
        'under_2.5': 1 - over_2_5_prob
    }