# src/database_manager.py

import sqlite3
from sqlite3 import Error

# ... (la función create_connection y create_table se quedan igual) ...
def create_connection(db_file: str):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn: sqlite3.Connection):
    sql_create_matches_table = """
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        league_code TEXT NOT NULL,
        matchday INTEGER,
        utc_date TEXT NOT NULL,
        status TEXT NOT NULL,
        home_team_name TEXT NOT NULL,
        away_team_name TEXT NOT NULL,
        home_team_score INTEGER,
        away_team_score INTEGER,
        home_win_odds REAL,
        draw_odds REAL,
        away_win_odds REAL
    );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_matches_table)
    except Error as e:
        print(e)

def insert_match(conn: sqlite3.Connection, match: dict, league_id: int):
    """
    Inserta un partido de API-Football en la tabla.
    """
    # La tabla se queda igual, así que solo adaptamos la extracción de datos
    sql = '''INSERT OR IGNORE INTO matches(id, league_code, matchday, utc_date, status, home_team_name, away_team_name, home_team_score, away_team_score)
             VALUES(?,?,?,?,?,?,?,?,?)'''

    cur = conn.cursor()

    fixture = match.get('fixture', {})
    teams = match.get('teams', {})
    goals = match.get('goals', {})

    # La tabla tiene columnas de cuotas, pero las dejaremos vacías (NULL)
    match_data = (
        fixture.get('id'),
        league_id, # Usamos el ID de la liga
        match.get('league', {}).get('round'),
        fixture.get('date'),
        fixture.get('status', {}).get('short'),
        teams.get('home', {}).get('name'),
        teams.get('away', {}).get('name'),
        goals.get('home'),
        goals.get('away')
    )

    cur.execute(sql, match_data)
    conn.commit()

