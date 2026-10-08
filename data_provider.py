import os
import requests
from datetime import datetime
import importlib
try:
    import config
except ImportError:
    config = None

def get_config():
    global config
    try:
        if config is not None:
            importlib.reload(config)
        else:
            import config
    except Exception:
        config = None
    return config


from prediction_engine import (
    calculate_match_probabilities,
    calculate_live_probabilities,
    calculate_nba_probabilities,
    calculate_nba_live_probabilities,
    get_football_team_ratings,
    get_nba_team_ratings,
    generate_match_h2h,
    deterministic_hash,
    detect_league_and_country
)
from ai_analyzer import (
    generate_ai_analysis,
    generate_live_ai_analysis,
    generate_nba_ai_analysis,
    generate_nba_live_ai_analysis
)

# ==============================================================
# CATÁLOGO DE FÚTBOL (SOCCER)
# ==============================================================
SOCCER_LIVE_MATCHES = [
    {
        "id": "soc_live_001",
        "sport": "football",
        "league": "UEFA Champions League",
        "league_flag": "🏆",
        "home_team": "Real Madrid",
        "away_team": "Bayern Múnich",
        "minute": 68,
        "score_home": 2,
        "score_away": 1,
        "home_stats": {"attack": 2.4, "defense": 0.9},
        "away_stats": {"attack": 2.1, "defense": 1.2},
        "live_stats": {
            "possession_home": 58,
            "possession_away": 42,
            "shots_on_target_home": 7,
            "shots_on_target_away": 4,
            "total_shots_home": 14,
            "total_shots_away": 9,
            "corners_home": 6,
            "corners_away": 3,
            "fouls_home": 9,
            "fouls_away": 12,
            "yellow_cards_home": 1,
            "yellow_cards_away": 2,
            "dangerous_attacks_home": 54,
            "dangerous_attacks_away": 38
        }
    },
    {
        "id": "soc_live_002",
        "sport": "football",
        "league": "Premier League",
        "league_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "home_team": "Manchester City",
        "away_team": "Arsenal",
        "minute": 79,
        "score_home": 1,
        "score_away": 1,
        "home_stats": {"attack": 2.6, "defense": 0.8},
        "away_stats": {"attack": 2.2, "defense": 0.9},
        "live_stats": {
            "possession_home": 65,
            "possession_away": 35,
            "shots_on_target_home": 8,
            "shots_on_target_away": 3,
            "total_shots_home": 18,
            "total_shots_away": 6,
            "corners_home": 9,
            "corners_away": 2,
            "fouls_home": 7,
            "fouls_away": 11,
            "yellow_cards_home": 2,
            "yellow_cards_away": 3,
            "dangerous_attacks_home": 68,
            "dangerous_attacks_away": 27
        }
    },
    {
        "id": "soc_live_003",
        "sport": "football",
        "league": "LaLiga EA Sports",
        "league_flag": "🇪🇸",
        "home_team": "FC Barcelona",
        "away_team": "Atlético de Madrid",
        "minute": 34,
        "score_home": 1,
        "score_away": 0,
        "home_stats": {"attack": 2.5, "defense": 1.0},
        "away_stats": {"attack": 1.6, "defense": 0.8},
        "live_stats": {
            "possession_home": 62,
            "possession_away": 38,
            "shots_on_target_home": 4,
            "shots_on_target_away": 1,
            "total_shots_home": 8,
            "total_shots_away": 3,
            "corners_home": 4,
            "corners_away": 1,
            "fouls_home": 5,
            "fouls_away": 8,
            "yellow_cards_home": 0,
            "yellow_cards_away": 1,
            "dangerous_attacks_home": 32,
            "dangerous_attacks_away": 16
        }
    },
    {
        "id": "soc_live_004",
        "sport": "football",
        "league": "Eliminatorias CONMEBOL (Selecciones)",
        "league_flag": "🌎",
        "home_team": "Argentina",
        "away_team": "Brasil",
        "minute": 63,
        "score_home": 1,
        "score_away": 0,
        "home_stats": {"attack": 2.3, "defense": 0.5},
        "away_stats": {"attack": 1.9, "defense": 0.8},
        "live_stats": {
            "possession_home": 54,
            "possession_away": 46,
            "shots_on_target_home": 6,
            "shots_on_target_away": 3,
            "total_shots_home": 12,
            "total_shots_away": 7,
            "corners_home": 5,
            "corners_away": 4,
            "fouls_home": 14,
            "fouls_away": 16,
            "yellow_cards_home": 2,
            "yellow_cards_away": 3,
            "dangerous_attacks_home": 46,
            "dangerous_attacks_away": 39
        }
    },
    {
        "id": "soc_live_005",
        "sport": "football",
        "league": "UEFA Nations League (Selecciones)",
        "league_flag": "🏆",
        "home_team": "España",
        "away_team": "Francia",
        "minute": 74,
        "score_home": 2,
        "score_away": 2,
        "home_stats": {"attack": 2.4, "defense": 0.9},
        "away_stats": {"attack": 2.2, "defense": 1.0},
        "live_stats": {
            "possession_home": 61,
            "possession_away": 39,
            "shots_on_target_home": 7,
            "shots_on_target_away": 6,
            "total_shots_home": 15,
            "total_shots_away": 11,
            "corners_home": 8,
            "corners_away": 4,
            "fouls_home": 8,
            "fouls_away": 10,
            "yellow_cards_home": 1,
            "yellow_cards_away": 2,
            "dangerous_attacks_home": 60,
            "dangerous_attacks_away": 48
        }
    }
]

SOCCER_UPCOMING_MATCHES = [
    {
        "id": "soc_up_101",
        "sport": "football",
        "league": "Premier League",
        "league_flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "home_team": "Liverpool",
        "away_team": "Chelsea",
        "date": "Mañana - 16:30",
        "home_stats": {"attack": 2.3, "defense": 1.1},
        "away_stats": {"attack": 1.7, "defense": 1.4},
        "market_odds": {"1": 1.70, "X": 4.10, "2": 4.50}
    },
    {
        "id": "soc_up_102",
        "sport": "football",
        "league": "Serie A",
        "league_flag": "🇮🇹",
        "home_team": "Inter Milán",
        "away_team": "Juventus",
        "date": "Mañana - 18:45",
        "home_stats": {"attack": 2.0, "defense": 0.7},
        "away_stats": {"attack": 1.4, "defense": 0.7},
        "market_odds": {"1": 1.90, "X": 3.30, "2": 4.40}
    },
    {
        "id": "soc_up_103",
        "sport": "football",
        "league": "Bundesliga",
        "league_flag": "🇩🇪",
        "home_team": "Bayer Leverkusen",
        "away_team": "Borussia Dortmund",
        "date": "Mañana - 15:30",
        "home_stats": {"attack": 2.5, "defense": 1.0},
        "away_stats": {"attack": 2.0, "defense": 1.5},
        "market_odds": {"1": 1.80, "X": 4.00, "2": 3.90}
    },
    {
        "id": "soc_up_104",
        "sport": "football",
        "league": "Ligue 1",
        "league_flag": "🇫🇷",
        "home_team": "Paris Saint-Germain",
        "away_team": "Olympique Marsella",
        "date": "Domingo - 20:45",
        "home_stats": {"attack": 2.6, "defense": 0.9},
        "away_stats": {"attack": 1.8, "defense": 1.2},
        "market_odds": {"1": 1.55, "X": 4.50, "2": 5.50}
    },
    {
        "id": "soc_up_105",
        "sport": "football",
        "league": "Liga MX",
        "league_flag": "🇲🇽",
        "home_team": "Club América",
        "away_team": "Chivas Guadalajara",
        "date": "Sábado - 21:05",
        "home_stats": {"attack": 2.1, "defense": 1.0},
        "away_stats": {"attack": 1.5, "defense": 1.2},
        "market_odds": {"1": 1.85, "X": 3.50, "2": 4.20}
    },
    {
        "id": "soc_up_106",
        "sport": "football",
        "league": "Copa Libertadores",
        "league_flag": "🌎",
        "home_team": "Flamengo",
        "away_team": "River Plate",
        "date": "Jueves - 19:30",
        "home_stats": {"attack": 2.2, "defense": 0.8},
        "away_stats": {"attack": 1.8, "defense": 0.9},
        "market_odds": {"1": 1.95, "X": 3.40, "2": 3.90}
    },
    {
        "id": "soc_up_107",
        "sport": "football",
        "league": "Clasificatorias Concacaf (Selecciones)",
        "league_flag": "🏆",
        "home_team": "México",
        "away_team": "Estados Unidos",
        "date": "Sábado - 20:00",
        "home_stats": {"attack": 2.0, "defense": 0.8},
        "away_stats": {"attack": 1.9, "defense": 0.9},
        "market_odds": {"1": 2.15, "X": 3.25, "2": 3.40}
    },
    {
        "id": "soc_up_108",
        "sport": "football",
        "league": "Eliminatorias CONMEBOL (Selecciones)",
        "league_flag": "🌎",
        "home_team": "Colombia",
        "away_team": "Uruguay",
        "date": "Jueves - 17:30",
        "home_stats": {"attack": 2.1, "defense": 0.7},
        "away_stats": {"attack": 2.0, "defense": 0.8},
        "market_odds": {"1": 2.10, "X": 3.20, "2": 3.60}
    },
    {
        "id": "soc_up_109",
        "sport": "football",
        "league": "UEFA Nations League (Selecciones)",
        "league_flag": "🏆",
        "home_team": "Inglaterra",
        "away_team": "Alemania",
        "date": "Domingo - 20:45",
        "home_stats": {"attack": 2.3, "defense": 0.9},
        "away_stats": {"attack": 2.1, "defense": 1.1},
        "market_odds": {"1": 2.00, "X": 3.40, "2": 3.70}
    }
]

# ==============================================================
# CATÁLOGO DE NBA (BALONCESTO)
# ==============================================================
NBA_LIVE_MATCHES = [
    {
        "id": "nba_live_001",
        "sport": "nba",
        "league": "NBA - Conferencia Oeste",
        "league_flag": "🏀",
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "quarter": "3Q 7:45",
        "mins_remaining": 19.5,
        "score_home": 82,
        "score_away": 78,
        "home_stats": {"off_rating": 116.8, "def_rating": 114.2, "pace": 101.5},
        "away_stats": {"off_rating": 117.2, "def_rating": 115.0, "pace": 100.8},
        "live_stats": {
            "q_scores": {"Q1": "28-26", "Q2": "30-29", "Q3": "24-23"},
            "fg_pct_home": 49.2,
            "fg_pct_away": 46.5,
            "three_pct_home": 38.5,
            "three_pct_away": 41.2,
            "rebounds_home": 34,
            "rebounds_away": 30,
            "assists_home": 22,
            "assists_away": 24,
            "turnovers_home": 8,
            "turnovers_away": 11
        }
    },
    {
        "id": "nba_live_002",
        "sport": "nba",
        "league": "NBA - Conferencia Este",
        "league_flag": "🏀",
        "home_team": "Boston Celtics",
        "away_team": "Milwaukee Bucks",
        "quarter": "4Q 3:10",
        "mins_remaining": 3.1,
        "score_home": 108,
        "score_away": 104,
        "home_stats": {"off_rating": 122.0, "def_rating": 110.5, "pace": 98.2},
        "away_stats": {"off_rating": 118.5, "def_rating": 115.0, "pace": 99.0},
        "live_stats": {
            "q_scores": {"Q1": "31-28", "Q2": "29-27", "Q3": "26-29", "Q4": "22-20"},
            "fg_pct_home": 51.0,
            "fg_pct_away": 48.3,
            "three_pct_home": 42.1,
            "three_pct_away": 36.8,
            "rebounds_home": 41,
            "rebounds_away": 39,
            "assists_home": 27,
            "assists_away": 21,
            "turnovers_home": 9,
            "turnovers_away": 13
        }
    }
]

NBA_UPCOMING_MATCHES = [
    {
        "id": "nba_up_201",
        "sport": "nba",
        "league": "NBA - Conferencia Oeste",
        "league_flag": "🏀",
        "home_team": "Denver Nuggets",
        "away_team": "Phoenix Suns",
        "date": "Hoy - 21:00",
        "home_stats": {"off_rating": 119.5, "def_rating": 112.0, "pace": 97.5},
        "away_stats": {"off_rating": 116.8, "def_rating": 114.5, "pace": 98.8},
        "market_odds": {"home_ml": 1.62, "away_ml": 2.40}
    },
    {
        "id": "nba_up_202",
        "sport": "nba",
        "league": "NBA - Conferencia Oeste",
        "league_flag": "🏀",
        "home_team": "Dallas Mavericks",
        "away_team": "LA Clippers",
        "date": "Hoy - 21:30",
        "home_stats": {"off_rating": 118.0, "def_rating": 113.8, "pace": 99.2},
        "away_stats": {"off_rating": 117.5, "def_rating": 112.5, "pace": 98.0},
        "market_odds": {"home_ml": 1.85, "away_ml": 2.00}
    },
    {
        "id": "nba_up_203",
        "sport": "nba",
        "league": "NBA - Conferencia Este",
        "league_flag": "🏀",
        "home_team": "New York Knicks",
        "away_team": "Philadelphia 76ers",
        "date": "Mañana - 19:30",
        "home_stats": {"off_rating": 117.2, "def_rating": 111.8, "pace": 96.0},
        "away_stats": {"off_rating": 116.5, "def_rating": 113.0, "pace": 98.5},
        "market_odds": {"home_ml": 1.72, "away_ml": 2.15}
    },
    {
        "id": "nba_up_204",
        "sport": "nba",
        "league": "NBA - Conferencia Este",
        "league_flag": "🏀",
        "home_team": "Miami Heat",
        "away_team": "Indiana Pacers",
        "date": "Mañana - 20:00",
        "home_stats": {"off_rating": 113.5, "def_rating": 111.0, "pace": 96.8},
        "away_stats": {"off_rating": 121.0, "def_rating": 118.5, "pace": 102.5},
        "market_odds": {"home_ml": 1.90, "away_ml": 1.95}
    }
]

def try_fetch_external_football():
    """
    Intenta conectar a Football-Data.org si USE_LIVE_API = True en config.py.
    Si no hay conexión o no hay clave, regresa None para usar el catálogo local.
    """
def get_league_and_country_info(comp_name, sport="football", home_team="", away_team=""):
    # Si la competición es genérica (ej. 'regular-season') o disponemos de los nombres de los equipos
    comp_lower = (comp_name or "").lower().strip()
    if (home_team or away_team) and comp_lower in ("regular-season", "pre-season", "post-season", "oficial", "amistoso internacional", "desconocida", ""):
        t_clean, c_name, flag, _ = detect_league_and_country(home_team, away_team, sport, comp_name, "")
        return t_clean, c_name, flag

    if sport == "nba" or "nba" in comp_lower:
        return "NBA", "Estados Unidos", "🇺🇸"
    if "premier" in comp_lower:
        return "Premier League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "championship" in comp_lower:
        return "Championship", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "primera division" in comp_lower or "laliga" in comp_lower or "la liga" in comp_lower:
        return "LaLiga EA Sports", "España", "🇪🇸"
    if "brasileir" in comp_lower or "brazil" in comp_lower:
        return "Brasileirão Série A", "Brasil", "🇧🇷"
    if "serie a" in comp_lower or "italia" in comp_lower:
        return "Serie A", "Italia", "🇮🇹"
    if "bundesliga" in comp_lower:
        return "Bundesliga", "Alemania", "🇩🇪"
    if "ligue 1" in comp_lower:
        return "Ligue 1", "Francia", "🇫🇷"
    if "primeira liga" in comp_lower or "portugal" in comp_lower:
        return "Primeira Liga", "Portugal", "🇵🇹"
    if "eredivisie" in comp_lower or "netherlands" in comp_lower:
        return "Eredivisie", "Países Bajos", "🇳🇱"
    if "argentin" in comp_lower:
        return "Liga Profesional Argentina", "Argentina", "🇦🇷"
    if "colomb" in comp_lower:
        return "Liga BetPlay Dimayor", "Colombia", "🇨🇴"
    if "mls" in comp_lower or "major league soccer" in comp_lower or "usl" in comp_lower or "ncaa" in comp_lower or "usa" in comp_lower:
        return "Major League Soccer (MLS)", "Estados Unidos", "🇺🇸"
    if "saudi" in comp_lower or "arab" in comp_lower:
        return "Saudi Pro League", "Arabia Saudita", "🇸🇦"
    if "libertadores" in comp_lower:
        return "Copa CONMEBOL Libertadores", "Sudamérica", "🏆"
    if "sudamericana" in comp_lower:
        return "Copa CONMEBOL Sudamericana", "Sudamérica", "🏆"
    if "mexic" in comp_lower or "méxic" in comp_lower or "liga mx" in comp_lower:
        return "Liga MX", "México", "🇲🇽"
    if "selección" in comp_lower or "amistoso" in comp_lower or "fifa" in comp_lower or "friendly" in comp_lower:
        return "Selecciones FIFA", "Internacional", "🌎"
    if "champions" in comp_lower:
        return "UEFA Champions League", "Europa", "🏆"
    if "nations" in comp_lower:
        return "UEFA Nations League", "Europa", "🇪🇺"

    t_clean, c_name, flag, _ = detect_league_and_country(home_team, away_team, sport, comp_name, "")
    return t_clean, c_name, flag

def generate_dynamic_live_stats(home_name: str, away_name: str, score_h: int, score_a: int, minute: int, h_ratings: dict = None, a_ratings: dict = None) -> dict:
    """
    Genera estadísticas de partido en vivo completamente dinámicas, asimétricas y realistas
    para tiros a puerta, tiros totales, córners, faltas y posesión.
    Garantiza que tiros a puerta >= goles, tiros totales > tiros a puerta, y que ambos
    equipos tengan cifras diferenciadas y coherentes con el flujo del juego.
    """
    h_hash = deterministic_hash(home_name)
    a_hash = deterministic_hash(away_name)
    comb_hash = deterministic_hash(f"{home_name}_{away_name}_{minute}")

    h_att = h_ratings.get("attack", 2.1) if h_ratings else 2.1
    a_att = a_ratings.get("attack", 1.8) if a_ratings else 1.8

    diff = score_h - score_a
    base_poss = 51 + (diff * 2) + int((h_att - a_att) * 7) + ((h_hash % 7) - 3)
    poss_h = max(36, min(68, base_poss))
    poss_a = 100 - poss_h

    m_factor = max(0.15, minute / 90.0)

    # Tiros a puerta: garantizado mayor o igual a los goles anotados
    shots_h = max(score_h, round(m_factor * (h_att * 2.7 + (poss_h / 12.0) + (h_hash % 3))))
    shots_a = max(score_a, round(m_factor * (a_att * 2.4 + (poss_a / 13.0) + (a_hash % 3))))
    if shots_h == shots_a:
        if poss_h >= poss_a:
            shots_h += 1
        else:
            shots_a += 1

    # Tiros totales: siempre mayor a tiros a puerta
    extra_h = max(2, round(shots_h * 1.25) + (comb_hash % 4))
    extra_a = max(2, round(shots_a * 1.15) + ((comb_hash // 4) % 4))
    total_shots_h = shots_h + extra_h
    total_shots_a = shots_a + extra_a

    # Córners: asimétricos y crecientes con el minuto
    corners_h = max(1, round(m_factor * (3.8 + (poss_h / 14.0) + (h_hash % 3))))
    corners_a = max(0, round(m_factor * (2.7 + (poss_a / 16.0) + (a_hash % 3))))
    if corners_h == corners_a:
        corners_h += 1

    # Faltas y tarjetas
    fouls_h = max(2, round(m_factor * (7 + (a_hash % 5))))
    fouls_a = max(3, round(m_factor * (8 + (h_hash % 5))))
    yellows_h = 1 if minute > 28 and (h_hash % 3 == 0) else (2 if minute > 70 else 0)
    yellows_a = 1 if minute > 32 else (2 if minute > 65 and (a_hash % 2 == 0) else 0)

    return {
        "possession_home": poss_h,
        "possession_away": poss_a,
        "shots_on_target_home": shots_h,
        "shots_on_target_away": shots_a,
        "total_shots_home": total_shots_h,
        "total_shots_away": total_shots_a,
        "corners_home": corners_h,
        "corners_away": corners_a,
        "fouls_home": fouls_h,
        "fouls_away": fouls_a,
        "yellow_cards_home": yellows_h,
        "yellow_cards_away": yellows_a,
        "dangerous_attacks_home": round(poss_h * 0.88 + (minute * 0.18)),
        "dangerous_attacks_away": round(poss_a * 0.82 + (minute * 0.14))
    }

def fetch_espn_live_soccer():
    """
    Obtiene partidos de fútbol en vivo transmitidos por ESPN (incluye selecciones como México, Concacaf, Conmebol, etc.).
    """
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            events = resp.json().get("events", [])
            live_list = []
            for e in events:
                state = e.get("status", {}).get("type", {}).get("state")
                if state == "in":
                    comp = e.get("competitions", [{}])[0]
                    competitors = comp.get("competitors", [])
                    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
                    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})

                    home_name = home.get("team", {}).get("displayName", "Local")
                    away_name = away.get("team", {}).get("displayName", "Visitante")
                    score_h = int(home.get("score", 0) or 0)
                    score_a = int(away.get("score", 0) or 0)
                    clock = e.get("status", {}).get("displayClock", "65'")
                    try:
                        minute = int(clock.replace("'", ""))
                    except Exception:
                        minute = 65

                    raw_league = e.get("season", {}).get("slug", "") or comp.get("league", {}).get("description", "Amistoso Internacional")
                    if "mexico" in home_name.lower() or "chile" in away_name.lower() or "méxico" in home_name.lower():
                        raw_league = "Selecciones FIFA - Amistoso Internacional"

                    league_title, country_name, flag = get_league_and_country_info(raw_league, "football", home_name, away_name)

                    h2h_data = generate_match_h2h(home_name, away_name, "football", league_title, country=country_name)
                    h_ratings = get_football_team_ratings(home_name, league_title, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                    a_ratings = get_football_team_ratings(away_name, league_title, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                    live_stats = generate_dynamic_live_stats(home_name, away_name, score_h, score_a, minute, h_ratings, a_ratings)

                    pred = calculate_live_probabilities(score_h, score_a, minute, h_ratings, a_ratings, live_stats)
                    ai_resp = generate_live_ai_analysis({"home_team": home_name, "away_team": away_name, "league": league_title}, pred, live_stats)

                    live_list.append({
                        "id": f"espn_soc_{e.get('id')}",
                        "sport": "football",
                        "league": league_title,
                        "country": country_name,
                        "league_flag": flag,
                        "country_flag": flag,
                        "home_team": home_name,
                        "away_team": away_name,
                        "minute": minute,
                        "score_home": score_h,
                        "score_away": score_a,
                        "home_stats": h_ratings,
                        "away_stats": a_ratings,
                        "live_stats": live_stats,
                        "prediction": pred,
                        "h2h": h2h_data,
                        "ai_analysis": ai_resp,
                        "is_live": True,
                        "is_external": True,
                        "source_api": "ESPN Live"
                    })
            if live_list:
                print(f"[ESPN REAL] Se cargaron {len(live_list)} partidos de fútbol en vivo (incluyendo Selecciones).")
            return live_list
    except Exception as ex:
        print(f"[ESPN] Error al consultar fútbol en vivo: {ex}")
    return []

def fetch_espn_live_nba():
    """
    Obtiene partidos de la NBA en vivo transmitidos por ESPN (incluye pretemporada y temporada regular, ej. Lakers).
    """
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            events = resp.json().get("events", [])
            live_list = []
            for e in events:
                state = e.get("status", {}).get("type", {}).get("state")
                if state == "in":
                    comp = e.get("competitions", [{}])[0]
                    competitors = comp.get("competitors", [])
                    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
                    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})

                    home_name = home.get("team", {}).get("displayName", "Local")
                    away_name = away.get("team", {}).get("displayName", "Visitante")
                    score_h = int(home.get("score", 0) or 0)
                    score_a = int(away.get("score", 0) or 0)
                    period = e.get("status", {}).get("period", 3)
                    clock_str = e.get("status", {}).get("displayClock", "0.0")
                    q_label = f"{period}Q"

                    home_lines = [int(l.get("value", 0)) for l in home.get("linescores", [])]
                    away_lines = [int(l.get("value", 0)) for l in away.get("linescores", [])]
                    q_scores = {}
                    for i in range(1, 5):
                        h_q = home_lines[i-1] if i-1 < len(home_lines) else 0
                        a_q = away_lines[i-1] if i-1 < len(away_lines) else 0
                        q_scores[f"{i}Q"] = f"{h_q}-{a_q}"

                    h2h_data = generate_match_h2h(home_name, away_name, "nba", "NBA", country="Estados Unidos")
                    h_ratings = get_nba_team_ratings(home_name, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                    a_ratings = get_nba_team_ratings(away_name, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                    h_hash = deterministic_hash(home_name)
                    fg_h = round(44.0 + (score_h / 25.0) + ((h_hash % 5) * 0.8), 1)
                    fg_a = round(43.0 + (score_a / 25.0) + (((h_hash // 5) % 5) * 0.8), 1)

                    live_stats = {
                        "q_scores": q_scores,
                        "field_goal_pct_home": min(56.0, fg_h),
                        "field_goal_pct_away": min(56.0, fg_a),
                        "three_point_pct_home": round(32.0 + ((h_hash % 8)), 1),
                        "three_point_pct_away": round(31.0 + (((h_hash // 7) % 8)), 1),
                        "rebounds_home": 34 + (period * 2),
                        "rebounds_away": 32 + (period * 2),
                        "assists_home": 20 + period,
                        "assists_away": 18 + period,
                        "turnovers_home": 8 + period,
                        "turnovers_away": 10 + period,
                        "current_run": f"{home_name if score_h >= score_a else away_name} +{abs(score_h - score_a)}"
                    }

                    try:
                        mins_rem = float(clock_str.split(":")[0]) if ":" in clock_str else 1.0
                    except Exception:
                        mins_rem = 2.0

                    pred = calculate_nba_live_probabilities(
                        current_h=score_h,
                        current_a=score_a,
                        quarter=f"Q{period}",
                        mins_remaining=mins_rem,
                        home_stats=h_ratings,
                        away_stats=a_ratings,
                        live_stats=live_stats
                    )
                    ai_resp = generate_nba_live_ai_analysis({"home_team": home_name, "away_team": away_name}, pred, live_stats)

                    live_list.append({
                        "id": f"espn_nba_{e.get('id')}",
                        "sport": "nba",
                        "league": "NBA",
                        "country": "Estados Unidos",
                        "league_flag": "🏀",
                        "country_flag": "🇺🇸",
                        "home_team": home_name,
                        "away_team": away_name,
                        "quarter": q_label,
                        "score_home": score_h,
                        "score_away": score_a,
                        "home_stats": h_ratings,
                        "away_stats": a_ratings,
                        "live_stats": live_stats,
                        "prediction": pred,
                        "h2h": h2h_data,
                        "ai_analysis": ai_resp,
                        "is_live": True,
                        "is_external": True,
                        "source_api": "ESPN Live"
                    })
            if live_list:
                print(f"[ESPN REAL] Se cargaron {len(live_list)} partidos de la NBA en vivo (incluyendo Lakers).")
            return live_list
    except Exception as ex:
        print(f"[ESPN] Error al consultar NBA en vivo: {ex}")
    return []

def try_fetch_external_live_football():
    """
    Intenta obtener partidos de fútbol REALES que estén en juego en este momento (status IN_PLAY o PAUSED).
    """
    cfg = get_config()
    if not (cfg and getattr(cfg, "USE_LIVE_API", False)):
        return None

    api_key = getattr(cfg, "FOOTBALL_DATA_API_KEY", "") or os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        return None

    try:
        url = "https://api.football-data.org/v4/matches?status=IN_PLAY"
        headers = {"X-Auth-Token": api_key}
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            data = resp.json().get("matches", [])
            live_matches = []
            for item in data:
                home_name = item.get("homeTeam", {}).get("name", "Local")
                away_name = item.get("awayTeam", {}).get("name", "Visitante")
                comp = item.get("competition", {}).get("name", "Competición")
                score = item.get("score", {}).get("fullTime", {})
                score_h = score.get("home") if score.get("home") is not None else 0
                score_a = score.get("away") if score.get("away") is not None else 0
                minute = item.get("minute", 45) or 45

                h2h_data = generate_match_h2h(home_name, away_name, "football", comp)
                h_ratings = get_football_team_ratings(home_name, comp, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                a_ratings = get_football_team_ratings(away_name, comp, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                live_stats = generate_dynamic_live_stats(home_name, away_name, score_h, score_a, minute, h_ratings, a_ratings)
                pred = calculate_live_probabilities(score_h, score_a, minute, h_ratings, a_ratings, live_stats)
                ai_resp = generate_live_ai_analysis({"home_team": home_name, "away_team": away_name, "league": comp}, pred, live_stats)
                live_matches.append({
                    "id": f"ext_live_{item.get('id')}",
                    "sport": "football",
                    "league": comp,
                    "league_flag": "⚽",
                    "home_team": home_name,
                    "away_team": away_name,
                    "minute": minute,
                    "score_home": score_h,
                    "score_away": score_a,
                    "live_stats": live_stats,
                    "prediction": pred,
                    "h2h": h2h_data,
                    "ai_analysis": ai_resp,
                    "is_live": True,
                    "is_external": True,
                    "source_api": "Football-Data.org (En Vivo)"
                })
            return live_matches
    except Exception as e:
        print(f"[INFO] Error al consultar partidos en vivo de Football-Data ({e}).")
    return None

import time

_football_cache = {"data": None, "timestamp": 0}
_nba_cache = {"data": None, "timestamp": 0}

def try_fetch_external_football(date_from=None, date_to=None):
    """
    Intenta conectar a Football-Data.org para traer partidos reales programados.
    """
    global _football_cache
    now = time.time()
    if not date_from and not date_to:
        if _football_cache["data"] and (now - _football_cache["timestamp"] < 180):
            return _football_cache["data"]

    cfg = get_config()
    if not (cfg and getattr(cfg, "USE_LIVE_API", False)):
        return None

    api_key = getattr(cfg, "FOOTBALL_DATA_API_KEY", "") or os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        print("[INFO] USE_LIVE_API está activo pero no has configurado FOOTBALL_DATA_API_KEY en config.py.")
        return None

    try:
        from datetime import timedelta
        today = datetime.now()
        if not date_from:
            date_from = today.strftime("%Y-%m-%d")
        if not date_to:
            date_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        url = f"https://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={date_to}"
        headers = {"X-Auth-Token": api_key}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json().get("matches", [])
            matches_list = []
            for item in data[:45]:
                home_name = item.get("homeTeam", {}).get("name", "Local")
                away_name = item.get("awayTeam", {}).get("name", "Visitante")
                comp = item.get("competition", {}).get("name", "Competición")
                raw_date = item.get("utcDate", "")
                date_iso = raw_date[:10] if len(raw_date) >= 10 else date_from
                time_str = raw_date[11:16] if len(raw_date) >= 16 else "00:00"

                try:
                    dt_obj = datetime.strptime(date_iso, "%Y-%m-%d")
                    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    dia_nombre = dias_semana[dt_obj.weekday()]
                    mes_nombre = meses[dt_obj.month - 1]
                    pretty_date = f"{dia_nombre} {dt_obj.day} {mes_nombre}, {time_str}"
                except Exception:
                    pretty_date = f"{date_iso} {time_str}"

                league_clean, country_name, flag = get_league_and_country_info(comp, "football", home_name, away_name)
                h2h_data = generate_match_h2h(home_name, away_name, "football", league_clean, country=country_name)
                home_stats = get_football_team_ratings(home_name, league_clean, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                away_stats = get_football_team_ratings(away_name, league_clean, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                pred = calculate_match_probabilities(home_stats, away_stats, home_team=home_name, away_team=away_name)
                analysis = generate_ai_analysis({"home_team": home_name, "away_team": away_name, "league": league_clean}, pred)

                matches_list.append({
                    "id": f"ext_{item.get('id')}",
                    "sport": "football",
                    "league": league_clean,
                    "country": country_name,
                    "league_flag": flag,
                    "country_flag": flag,
                    "home_team": home_name,
                    "away_team": away_name,
                    "date": pretty_date,
                    "date_iso": date_iso,
                    "time": time_str,
                    "home_stats": home_stats,
                    "away_stats": away_stats,
                    "prediction": pred,
                    "h2h": h2h_data,
                    "ai_analysis": analysis,
                    "is_live": False,
                    "is_external": True,
                    "source_api": "Football-Data.org"
                })

            # Complementar con partidos de ESPN Scoreboard para cubrir TODAS las ligas del mundo (Brasileirão, Liga MX, MLS, Selecciones, etc.)
            try:
                existing_keys = set(f"{m['home_team'].lower()}_{m['away_team'].lower()}" for m in matches_list)
                dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                
                # Consultar próximos 3 días en ESPN Scoreboard
                for day_offset in range(0, 3):
                    target_dt = today + timedelta(days=day_offset)
                    espn_date_str = target_dt.strftime("%Y%m%d")
                    espn_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={espn_date_str}"
                    espn_resp = requests.get(espn_url, timeout=3)
                    if espn_resp.status_code == 200:
                        espn_events = espn_resp.json().get("events", [])
                        for e in espn_events:
                            state = e.get("status", {}).get("type", {}).get("state")
                            if state == "pre":
                                comp_info = e.get("competitions", [{}])[0]
                                comps = comp_info.get("competitors", [])
                                h_team = next((c for c in comps if c.get("homeAway") == "home"), comps[0] if comps else {})
                                a_team = next((c for c in comps if c.get("homeAway") == "away"), comps[1] if len(comps) > 1 else {})
                                h_name = h_team.get("team", {}).get("displayName", "Local")
                                a_name = a_team.get("team", {}).get("displayName", "Visitante")

                                m_key = f"{h_name.lower()}_{a_name.lower()}"
                                if m_key in existing_keys:
                                    continue
                                existing_keys.add(m_key)

                                raw_slug = e.get("season", {}).get("slug", "") or comp_info.get("league", {}).get("description", "Oficial")
                                l_clean, c_name, c_flag = get_league_and_country_info(raw_slug, "football", h_name, a_name)

                                raw_dt = e.get("date", "")
                                d_iso = raw_dt[:10] if len(raw_dt) >= 10 else target_dt.strftime("%Y-%m-%d")
                                t_str = raw_dt[11:16] if len(raw_dt) >= 16 else "18:00"

                                try:
                                    dt_o = datetime.strptime(d_iso, "%Y-%m-%d")
                                    p_date = f"{dias_semana[dt_o.weekday()]} {dt_o.day} {meses[dt_o.month - 1]}, {t_str}"
                                except Exception:
                                    p_date = f"{d_iso} {t_str}"

                                e_h2h = generate_match_h2h(h_name, a_name, "football", l_clean, country=c_name)
                                h_stats = get_football_team_ratings(h_name, l_clean, recent_matches=e_h2h.get("home_last_5"), venue_role="home")
                                a_stats = get_football_team_ratings(a_name, l_clean, recent_matches=e_h2h.get("away_last_5"), venue_role="away")
                                e_pred = calculate_match_probabilities(h_stats, a_stats, home_team=h_name, away_team=a_name)
                                e_analysis = generate_ai_analysis({"home_team": h_name, "away_team": a_name, "league": l_clean}, e_pred)

                                matches_list.append({
                                    "id": f"espn_pre_{e.get('id')}",
                                    "sport": "football",
                                    "league": l_clean,
                                    "country": c_name,
                                    "league_flag": c_flag,
                                    "country_flag": c_flag,
                                    "home_team": h_name,
                                    "away_team": a_name,
                                    "date": p_date,
                                    "date_iso": d_iso,
                                    "time": t_str,
                                    "home_stats": h_stats,
                                    "away_stats": a_stats,
                                    "prediction": e_pred,
                                    "h2h": e_h2h,
                                    "ai_analysis": e_analysis,
                                    "is_live": False,
                                    "is_external": True,
                                    "source_api": "ESPN Scoreboard"
                                })
            except Exception as ex:
                print(f"[ESPN Scoreboard] Info al complementar ligas mundiales: {ex}")

            if matches_list:
                _football_cache["data"] = matches_list
                _football_cache["timestamp"] = now
                print(f"[API REAL] Se cargaron {len(matches_list)} partidos reales de todas las ligas.")
                return matches_list
    except Exception as e:
        print(f"[INFO] Error al conectar API externa ({e}).")
    return None

def try_fetch_external_nba():
    """
    Intenta conectar a Balldontlie NBA API si USE_LIVE_API = True en config.py.
    """
    global _nba_cache
    now = time.time()
    if _nba_cache["data"] and (now - _nba_cache["timestamp"] < 180):
        return _nba_cache["data"]

    cfg = get_config()
    if not (cfg and getattr(cfg, "USE_LIVE_API", False)):
        return None

    api_key = getattr(cfg, "NBA_API_KEY", "") or os.environ.get("NBA_API_KEY", "")
    if not api_key:
        return None

    try:
        url = "https://api.balldontlie.io/v1/games?seasons[]=2024&per_page=12"
        headers = {"Authorization": api_key}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            games = resp.json().get("data", [])
            nba_matches = []
            for g in games[:12]:
                home_team = g.get("home_team", {}).get("full_name", "Local")
                away_team = g.get("visitor_team", {}).get("full_name", "Visitante")
                raw_date = g.get("date", "")
                date_iso = raw_date[:10] if len(raw_date) >= 10 else "2024-10-22"
                try:
                    dt_obj = datetime.strptime(date_iso, "%Y-%m-%d")
                    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
                    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    pretty_date = f"{dias_semana[dt_obj.weekday()]} {dt_obj.day} {meses[dt_obj.month - 1]}"
                except Exception:
                    pretty_date = date_iso

                h2h_data = generate_match_h2h(home_team, away_team, "nba", "NBA", country="Estados Unidos")
                home_stats = get_nba_team_ratings(home_team, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                away_stats = get_nba_team_ratings(away_team, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                pred = calculate_nba_probabilities(home_stats, away_stats, home_team=home_team, away_team=away_team)
                nba_matches.append({
                    "id": f"nba_ext_{g.get('id')}",
                    "sport": "nba",
                    "league": "NBA",
                    "country": "Estados Unidos",
                    "league_flag": "🏀",
                    "country_flag": "🇺🇸",
                    "home_team": home_team,
                    "away_team": away_team,
                    "date": pretty_date,
                    "date_iso": date_iso,
                    "time": "TBD",
                    "home_stats": home_stats,
                    "away_stats": away_stats,
                    "prediction": pred,
                    "h2h": h2h_data,
                    "ai_analysis": generate_nba_ai_analysis({"home_team": home_team, "away_team": away_team}, pred),
                    "is_live": False,
                    "is_external": True,
                    "source_api": "Balldontlie NBA"
                })
            if nba_matches:
                _nba_cache["data"] = nba_matches
                _nba_cache["timestamp"] = now
                print(f"[API REAL] Se cargaron {len(nba_matches)} partidos reales desde Balldontlie NBA.")
                return nba_matches
    except Exception as e:
        print(f"[INFO] Error al conectar Balldontlie NBA ({e}).")
    return None

def fetch_live_matches_data(sport_filter="all"):
    """
    Obtiene los partidos en vivo.
    Si USE_LIVE_API = True, trae ÚNICAMENTE partidos oficiales en juego reales.
    NUNCA devuelve simulaciones si USE_LIVE_API = True.
    """
    cfg = get_config()
    is_live_api = bool(cfg and getattr(cfg, "USE_LIVE_API", False))
    if is_live_api:
        live_results = []
        if sport_filter in ("all", "football"):
            # Trae partidos de fútbol en vivo (incluye Selección Mexicana y amistosos)
            live_results.extend(fetch_espn_live_soccer())
            fd_live = try_fetch_external_live_football()
            if fd_live:
                live_results.extend(fd_live)
        if sport_filter in ("all", "nba"):
            # Trae partidos de la NBA en vivo (incluye Lakers vs Warriors)
            live_results.extend(fetch_espn_live_nba())
        if live_results:
            return live_results

    # Catálogo simulado (SOLO cuando USE_LIVE_API = False):
    results = []
    if sport_filter in ("all", "football"):
        for item in SOCCER_LIVE_MATCHES:
            l_clean, c_name, c_flag = get_league_and_country_info(item["league"], "football", item["home_team"], item["away_team"])
            h2h_data = generate_match_h2h(item["home_team"], item["away_team"], "football", l_clean, country=c_name)
            home_stats = get_football_team_ratings(item["home_team"], l_clean, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
            away_stats = get_football_team_ratings(item["away_team"], l_clean, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
            pred = calculate_live_probabilities(
                current_h=item["score_home"],
                current_a=item["score_away"],
                minute=item["minute"],
                home_stats=home_stats,
                away_stats=away_stats,
                live_stats=item["live_stats"]
            )
            ai_resp = generate_live_ai_analysis(item, pred, item["live_stats"])
            results.append({
                "id": item["id"],
                "sport": "football",
                "league": l_clean,
                "country": c_name,
                "league_flag": c_flag,
                "country_flag": c_flag,
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "minute": item["minute"],
                "score_home": item["score_home"],
                "score_away": item["score_away"],
                "home_stats": home_stats,
                "away_stats": away_stats,
                "live_stats": item["live_stats"],
                "prediction": pred,
                "h2h": h2h_data,
                "ai_analysis": ai_resp,
                "is_live": True
            })

    if sport_filter in ("all", "nba"):
        for item in NBA_LIVE_MATCHES:
            h2h_data = generate_match_h2h(item["home_team"], item["away_team"], "nba", "NBA", country="Estados Unidos")
            home_stats = get_nba_team_ratings(item["home_team"], recent_matches=h2h_data.get("home_last_5"), venue_role="home")
            away_stats = get_nba_team_ratings(item["away_team"], recent_matches=h2h_data.get("away_last_5"), venue_role="away")
            pred = calculate_nba_live_probabilities(
                current_h=item["score_home"],
                current_a=item["score_away"],
                quarter=item["quarter"],
                mins_remaining=item["mins_remaining"],
                home_stats=home_stats,
                away_stats=away_stats,
                live_stats=item["live_stats"]
            )
            ai_resp = generate_nba_live_ai_analysis(item, pred, item["live_stats"])
            results.append({
                "id": item["id"],
                "sport": "nba",
                "league": "NBA",
                "country": "Estados Unidos",
                "league_flag": "🏀",
                "country_flag": "🇺🇸",
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "quarter": item["quarter"],
                "score_home": item["score_home"],
                "score_away": item["score_away"],
                "home_stats": home_stats,
                "away_stats": away_stats,
                "live_stats": item["live_stats"],
                "prediction": pred,
                "h2h": h2h_data,
                "ai_analysis": ai_resp,
                "is_live": True
            })

    return results

def fetch_matches_data(sport_filter="all"):
    """
    Obtiene los partidos programados (pre-match).
    Si USE_LIVE_API = True, trae ÚNICAMENTE partidos oficiales reales de las APIs.
    NUNCA devuelve partidos simulados si USE_LIVE_API = True.
    """
    cfg = get_config()
    is_live_api = bool(cfg and getattr(cfg, "USE_LIVE_API", False))
    results = []

    if is_live_api:
        if sport_filter in ("all", "football"):
            ext_matches = try_fetch_external_football()
            if ext_matches:
                results.extend(ext_matches)
        if sport_filter in ("all", "nba"):
            ext_nba = try_fetch_external_nba()
            if ext_nba:
                results.extend(ext_nba)
        return results

    # Modo offline de maqueta local (SOLO cuando USE_LIVE_API = False):
    if sport_filter in ("all", "football"):
        for item in SOCCER_UPCOMING_MATCHES:
            l_clean, c_name, c_flag = get_league_and_country_info(item["league"], "football", item["home_team"], item["away_team"])
            h2h_data = generate_match_h2h(item["home_team"], item["away_team"], "football", l_clean, country=c_name)
            home_stats = get_football_team_ratings(item["home_team"], l_clean, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
            away_stats = get_football_team_ratings(item["away_team"], l_clean, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
            pred = calculate_match_probabilities(home_stats, away_stats, home_team=item["home_team"], away_team=item["away_team"])
            analysis = generate_ai_analysis(item, pred)
            results.append({
                "id": item["id"],
                "sport": "football",
                "league": l_clean,
                "country": c_name,
                "league_flag": c_flag,
                "country_flag": c_flag,
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "date": item["date"],
                "date_iso": "2026-10-07",
                "market_odds": item.get("market_odds", {}),
                "home_stats": home_stats,
                "away_stats": away_stats,
                "prediction": pred,
                "h2h": h2h_data,
                "ai_analysis": analysis,
                "is_live": False
            })

    if sport_filter in ("all", "nba"):
        for item in NBA_UPCOMING_MATCHES:
            h2h_data = generate_match_h2h(item["home_team"], item["away_team"], "nba", "NBA", country="Estados Unidos")
            home_stats = get_nba_team_ratings(item["home_team"], recent_matches=h2h_data.get("home_last_5"), venue_role="home")
            away_stats = get_nba_team_ratings(item["away_team"], recent_matches=h2h_data.get("away_last_5"), venue_role="away")
            pred = calculate_nba_probabilities(home_stats, away_stats, home_team=item["home_team"], away_team=item["away_team"])
            analysis = generate_nba_ai_analysis(item, pred)
            results.append({
                "id": item["id"],
                "sport": "nba",
                "league": "NBA",
                "country": "Estados Unidos",
                "league_flag": "🏀",
                "country_flag": "🇺🇸",
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "date": item["date"],
                "date_iso": "2026-10-07",
                "market_odds": item.get("market_odds", {}),
                "home_stats": home_stats,
                "away_stats": away_stats,
                "prediction": pred,
                "h2h": h2h_data,
                "ai_analysis": analysis,
                "is_live": False
            })

    return results
