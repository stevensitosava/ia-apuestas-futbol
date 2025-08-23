# 🤖 IA de Análisis de Apuestas de Fútbol

Este proyecto es un sistema de inteligencia artificial y automatización diseñado para analizar partidos de las principales ligas de fútbol europeas, identificar oportunidades de apuestas de valor y notificar los resultados de forma autónoma.

## ✨ Características Principales

-   **Modelo Predictivo Estadístico**: Utiliza un modelo basado en la **Distribución de Poisson** y la fuerza de ataque/defensa de cada equipo, entrenado con miles de partidos históricos.
-   **Análisis de Valor y Gestión de Riesgo**: No solo predice el resultado más probable, sino que identifica **apuestas de valor** (cuotas favorables) y sugiere el tamaño de la apuesta usando el **Criterio de Kelly**.
-   **Backtesting de Rendimiento**: Incluye un sistema de backtesting que evalúa la precisión histórica del modelo temporada a temporada, permitiendo visualizar su fiabilidad y evolución en una "Curva de Aprendizaje".
-   **Aprendizaje Continuo**: El sistema está diseñado para **aprender y mejorar con el tiempo**, actualizando su base de conocimiento con los resultados de los nuevos partidos cada semana.
-   **Interfaz Gráfica Interactiva**: Una aplicación construida con **Streamlit** permite realizar análisis manuales, visualizar el "diario de predicciones" de la IA y monitorizar su rendimiento.
-   **Automatización Total con n8n**: Un flujo de trabajo autónomo se ejecuta en un horario programado para realizar los análisis y enviar los resultados.
-   **Informes Personalizados con IA Generativa**: Utiliza **Google Gemini** para transformar los datos estadísticos en resúmenes de texto naturales y fáciles de entender, que son enviados a través de un bot de **Telegram**.

---
## 📈 Backtesting y Curva de Aprendizaje

Una de las características más potentes del sistema es su capacidad de autoevaluación. El módulo de backtesting simula el rendimiento del modelo en temporadas pasadas para medir su precisión predictiva.

El proceso funciona de forma secuencial:
1.  **Prueba 1**: Entrena el modelo con los datos de la temporada 2022/2023 y mide su precisión contra los resultados reales de la temporada 2023/2024.
2.  **Prueba 2**: Entrena el modelo con los datos de 2022/2023 y 2023/2024, y mide su precisión contra la temporada 2024/2025.
3.  **Registro**: Cada resultado se guarda en `performance_log.csv`.

Estos resultados se visualizan en la interfaz como una **"Curva de Aprendizaje"**, que muestra si la precisión del modelo mejora a medida que se alimenta con más datos.

---
## 🛠️ Tecnologías Utilizadas

-   **Lenguaje**: Python
-   **Análisis de Datos**: Pandas, SciPy
-   **Interfaz Gráfica**: Streamlit
-   **Automatización**: n8n
-   **IA Generativa**: Google Gemini API
-   **Notificaciones**: Telegram API
-   **Fuente de Datos Históricos**: Archivos CSV de [football-data.co.uk](http://football-data.co.uk/)
-   **Fuente de Cuotas en Vivo**: [The Odds API](https://the-odds-api.com/)

---
## 📂 Estructura del Proyecto

El proyecto sigue una estructura modular y profesional para separar las responsabilidades:

-   **`app.py`**: El front-end interactivo construido con Streamlit.
-   **`reporter.py`**: El script silencioso que genera los datos JSON para la automatización.
-   **`config/settings.py`**: Archivo central para claves de API y configuración.
-   **`data/`**: Carpeta que contiene los archivos CSV con los datos históricos.
-   **`src/`**: Módulos con la lógica principal del sistema.
    -   **`utils.py`**: Funciones de ayuda (carga de datos, normalización de nombres).
    -   **`data_analyzer.py`**: Lógica para calcular la fuerza de los equipos y estadísticas H2H.
    -   **`prediction_model.py`**: Contiene el modelo Poisson y la fórmula del Criterio de Kelly.
    -   **`data_fetcher.py`**: Se encarga de la comunicación con las APIs externas.
    -   **`core_logic.py`**: Orquesta las llamadas a los otros módulos para ejecutar las tareas principales.
    -   **`backtester.py`**: Mide la precisión histórica del modelo temporada a temporada.

---
## ⚙️ Cómo Funciona la Automatización (n8n)

El "piloto automático" del proyecto reside en un flujo de trabajo de n8n que sigue estos pasos:

1.  **⏰ Schedule (Programador)**: El flujo se activa automáticamente en un horario definido.
2.  **🐍 Execute Command (Ejecutor)**: Lanza el script `reporter.py`.
3.  **🤖 Google Gemini (Intérprete)**: Recibe el JSON del script y redacta un resumen en lenguaje natural.
4.  **📱 Telegram (Mensajero)**: Toma el texto de Gemini y lo envía al usuario.

---

## Disclaimer

Las predicciones generadas son el resultado de un modelo estadístico y no garantizan ningún tipo de ganancia. Las apuestas deportivas conllevan un riesgo financiero. Apuesta siempre con responsabilidad.