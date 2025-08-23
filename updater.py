# updater.py
import requests
import pandas as pd
from config import settings
from datetime import datetime

def get_recent_scores_from_api(api_key: str, league: str, days_ago: int = 3):
    """Obtiene los resultados de partidos recientes desde The Odds API."""
    uri = f"https://api.the-odds-api.com/v4/sports/{league}/scores"
    params = {'apiKey': api_key, 'daysFrom': days_ago}
    try:
        response = requests.get(uri, params=params)
        response.raise_for_status()
        print(f"Peticiones restantes a The Odds API: {response.headers.get('x-requests-remaining')}")
        return response.json()
    except Exception as e:
        print(f"Error obteniendo resultados: {e}")
        return []

def main():
    """
    Actualiza los archivos CSV con los últimos resultados de los partidos.
    """
    print("--- 🧠 Iniciando Sistema de Aprendizaje (Actualizador de Datos) ---")

    # Mapeo de claves de API a nombres de archivo y columnas
    league_map = {
        'soccer_spain_la_liga': {'file': 'data/SP1_2025_2026.csv', 'name': 'La Liga'},
        'soccer_epl': {'file': 'data/E0_2025_2026.csv', 'name': 'Premier League'}
    }

    for league_key, info in league_map.items():
        print(f"\n🔄 Buscando nuevos resultados para {info['name']}...")
        scores = get_recent_scores_from_api(settings.ODDS_API_KEY, league_key)

        new_results = []
        for game in scores:
            if game.get('completed') and game.get('scores'):
                home_score = int(game['scores'][0]['score'])
                away_score = int(game['scores'][1]['score'])

                new_results.append({
                    'Date': datetime.fromisoformat(game['commence_time'].replace('Z', '')).strftime('%d/%m/%y'),
                    'HomeTeam': game['scores'][0]['name'],
                    'AwayTeam': game['scores'][1]['name'],
                    'FTHG': home_score,
                    'FTAG': away_score,
                    'B365H': None, 'B365D': None, 'B365A': None # No tenemos cuotas históricas
                })

        if not new_results:
            print("No se encontraron nuevos resultados finalizados.")
            continue

        try:
            # Intentamos leer el archivo existente, si no, creamos uno nuevo
            try:
                df = pd.read_csv(info['file'])
            except FileNotFoundError:
                df = pd.DataFrame()

            new_df = pd.DataFrame(new_results)
            # Usamos los IDs de los juegos para evitar duplicados
            updated_df = pd.concat([df, new_df]).drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'])
            updated_df.to_csv(info['file'], index=False)
            print(f"✅ ¡Hecho! Se han añadido {len(updated_df) - len(df)} nuevos partidos a {info['file']}.")

        except Exception as e:
            print(f"❌ Error al guardar los datos en el archivo CSV: {e}")

if __name__ == "__main__":
    main()