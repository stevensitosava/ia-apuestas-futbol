# src/explanation_generator.py

def generar_analisis_completo(prediction: dict, value_bets: list, h2h_stats: dict, home_team: str, away_team: str, expected_goals: dict) -> str:
    """
    Genera un informe completo y multilínea del análisis del partido.
    """
    informe = []
    
    # --- Sección 1: Análisis Cara a Cara (H2H) ---
    informe.append("\n" + "--- Análisis del Partido ---")
    informe.append("📊 Cara a Cara (Datos Históricos):")
    if h2h_stats['total_matches'] > 0:
        informe.append(f"   - Se han enfrentado {h2h_stats['total_matches']} veces.")
        informe.append(f"   - Victorias para {home_team}: {h2h_stats['team1_wins']}")
        informe.append(f"   - Victorias para {away_team}: {h2h_stats['team2_wins']}")
        informe.append(f"   - Empates: {h2h_stats['draws']}")
    else:
        informe.append("   - No hay datos de enfrentamientos directos recientes en nuestro historial.")

    # --- Sección 2: Predicción del Modelo ---
    favorito_modelo = max(prediction, key=prediction.get)
    if favorito_modelo == 'home_win': favorito_texto = f"una victoria de {home_team}"
    elif favorito_modelo == 'draw': favorito_texto = "un empate"
    else: favorito_texto = f"una victoria de {away_team}"

    informe.append("\n" + "🧠 Veredicto del Modelo:")
    informe.append(f"   - El modelo predice {favorito_texto} como el resultado más probable ({prediction[favorito_modelo]:.2%}).")
    
    # Añadimos contexto sobre los goles
    total_goles_esperados = expected_goals['home'] + expected_goals['away']
    if total_goles_esperados > 2.7:
        informe.append("   - Se espera un partido con varios goles.")
    elif total_goles_esperados < 2.3:
        informe.append("   - Se espera un partido con pocos goles.")

    # --- Sección 3: Interpretación del Valor ---
    valor_en_sorpresa = False
    for bet in value_bets:
        if (favorito_modelo == 'home_win' and ("Empate" in bet or "Visitante" in bet)) or \
           (favorito_modelo == 'away_win' and ("Empate" in bet or "Local" in bet)) or \
           (favorito_modelo == 'draw' and ("Local" in bet or "Visitante" in bet)):
            valor_en_sorpresa = True
            break
    
    informe.append("\n" + "💡 Interpretación de la Oportunidad de Valor:")
    if valor_en_sorpresa:
        informe.append("   - El valor se encuentra en la 'sorpresa'. Aunque el modelo tiene un favorito, "
                       "cree que las cuotas para los otros resultados son demasiado altas y ofrecen una ventaja matemática.")
    else:
        informe.append("   - El valor se alinea con la predicción. El modelo cree que el resultado más probable "
                       "tiene una cuota lo suficientemente atractiva como para ser una buena oportunidad.")
        
    return "\n".join(informe)