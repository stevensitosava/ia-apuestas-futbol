# app.py (Versión Final Estable)
    
import streamlit as st
import pandas as pd
import os
from src.core_logic import run_analysis, run_update, run_backtest_logic, run_review_predictions, run_financial_backtest_logic, run_flat_backtest_logic
    
# --- Configuración de la Página ---
st.set_page_config(page_title="IA de Apuestas de Fútbol", layout="wide")
st.title("🤖 Asistente de IA para Apuestas de Fútbol")
st.write("Esta aplicación utiliza un modelo estadístico entrenado con datos históricos para encontrar oportunidades de valor en los próximos partidos.")
    
# --- Barra Lateral con Acciones ---
st.sidebar.header("Acciones Principales")
    
if st.sidebar.button("💎 Buscar Apuestas de Valor"):
    with st.spinner('Entrenando modelo y buscando oportunidades...'):
        st.session_state.last_report = run_analysis()
        st.session_state.report_title = "Análisis de Próximos Partidos:"
        
st.sidebar.header("Mantenimiento y Aprendizaje")

if st.sidebar.button("📖 Revisar y Aprender de Predicciones"):
    with st.spinner('Consultando resultados y actualizando diario...'):
        st.session_state.last_report = run_review_predictions()
        st.session_state.report_title = "Informe de Revisión de Predicciones:"
    
if st.sidebar.button("🧠 Actualizar Base de Conocimiento"):
    with st.spinner('Añadiendo últimos resultados a la memoria a largo plazo...'):
        st.session_state.last_report = run_update()
        st.session_state.report_title = "Resultado de la Actualización:"
            
st.sidebar.header("Evaluación del Modelo")

if st.sidebar.button("📊 Evaluar Precisión Histórica"):
    with st.spinner('Ejecutando backtest de precisión...'):
        st.session_state.last_report = run_backtest_logic()
        st.session_state.report_title = "Resultado del Backtest de Precisión:"
        st.rerun()

if st.sidebar.button("📈 Simular Rentabilidad (Kelly)"):
    with st.spinner('Simulando temporada (Kelly)... Esto puede tardar un poco.'):
        st.session_state.last_report = run_financial_backtest_logic()
        st.session_state.report_title = "Resultado del Backtest Financiero (Kelly):"
        st.rerun()
        
if st.sidebar.button("⚖️ Comparar con Apuesta Fija (Flat)"):
    with st.spinner('Simulando temporada (Apuesta Fija)...'):
        st.session_state.last_report = run_flat_backtest_logic()
        st.session_state.report_title = "Resultado del Backtest (Apuesta Fija):"
        st.rerun()

# --- ÁREA PRINCIPAL DE RESULTADOS ---
st.header("📋 Informes de la IA")

if 'last_report' in st.session_state:
    st.subheader(st.session_state.get('report_title', 'Resultados:'))
    st.text(st.session_state.last_report)

# --- Visualización del Aprendizaje ---
st.header("🧠 Curva de Aprendizaje del Modelo (Precisión)")
# ... (código de la gráfica de precisión sin cambios)
performance_log_path = 'performance_log.csv'
if os.path.exists(performance_log_path):
    try:
        log_df = pd.read_csv(performance_log_path)
        if not log_df.empty:
            log_df.set_index('season_tested', inplace=True)
            chart_data = log_df[['accuracy', 'hc_accuracy']]
            chart_data.rename(columns={'accuracy': 'Precisión General', 'hc_accuracy': 'Precisión en Alta Confianza'}, inplace=True)
            st.line_chart(chart_data)
        else:
            st.info("El registro de rendimiento está vacío.")
    except Exception as e:
        st.error(f"No se pudo cargar la gráfica: {e}")
else:
    st.info("No se ha encontrado un historial. Presiona 'Evaluar Precisión Histórica'.")


# --- Visualización de Rentabilidad ---
st.header("📈 Evolución de la Rentabilidad (Simulación)")
financial_log_path = 'financial_log.csv'
if os.path.exists(financial_log_path):
    try:
        log_df = pd.read_csv(financial_log_path)
        if not log_df.empty:
            log_df.set_index('season_simulated', inplace=True)
            st.subheader("Beneficio / Pérdida por Temporada (en Unidades)")
            st.bar_chart(log_df['profit_loss'])
        else:
            st.info("El registro de rentabilidad está vacío.")
    except Exception as e:
        st.error(f"No se pudo cargar la gráfica de rentabilidad: {e}")
else:
    st.info("No se ha encontrado un historial. Presiona 'Simular Rentabilidad'.")


# --- Diario de Predicciones ---
st.header("📖 Diario de Predicciones de la IA")
# ... (código del diario sin cambios)
log_file = 'predictions_log.csv'
if os.path.exists(log_file):
    try:
        log_df = pd.read_csv(log_file)
        st.dataframe(log_df.tail(20))
    except Exception as e:
        st.error(f"No se pudo cargar el diario de predicciones: {e}")
else:
    st.info("Aún no se ha generado un diario. Presiona 'Buscar Apuestas de Valor'.")

