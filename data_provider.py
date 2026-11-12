import threading
import os
import json
import requests
import re
import time
import unicodedata
from datetime import datetime, timezone, timedelta
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

_TEAM_LOGOS = {}
_TEAM_LOGOS_NORM = {}

def load_team_logos():
    global _TEAM_LOGOS, _TEAM_LOGOS_NORM
    if _TEAM_LOGOS:
        return _TEAM_LOGOS, _TEAM_LOGOS_NORM
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(base_dir, "data", "team_logos.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                _TEAM_LOGOS = data.get("logos", {})
                _TEAM_LOGOS_NORM = data.get("normalized", {})
        except Exception:
            pass
    return _TEAM_LOGOS, _TEAM_LOGOS_NORM

_NHL_ABBR_LOGOS = {
    "anaheim ducks": "ana", "boston bruins": "bos", "buffalo sabres": "buf", "calgary flames": "cgy",
    "carolina hurricanes": "car", "chicago blackhawks": "chi", "colorado avalanche": "col",
    "columbus blue jackets": "cbj", "dallas stars": "dal", "detroit red wings": "det",
    "edmonton oilers": "edm", "florida panthers": "fla", "los angeles kings": "la",
    "minnesota wild": "min", "montreal canadiens": "mtl", "nashville predators": "nsh",
    "new jersey devils": "nj", "new york islanders": "nyi", "new york rangers": "nyr",
    "ottawa senators": "ott", "philadelphia flyers": "phi", "pittsburgh penguins": "pit",
    "san jose sharks": "sj", "seattle kraken": "sea", "st. louis blues": "stl",
    "tampa bay lightning": "tb", "toronto maple leafs": "tor", "utah mammoth": "utah",
    "utah hockey club": "utah", "vancouver canucks": "van", "vegas golden knights": "vgk",
    "washington capitals": "wsh", "winnipeg jets": "wpg",
}


def get_team_logo(team_name, sport="football", team_id=None):
    if team_id:
        return f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png"
    if not team_name:
        return ""
    norm = unicodedata.normalize("NFKD", str(team_name)).encode("ASCII", "ignore").decode("utf-8").lower().strip()
    if sport == "nhl" or any(k in norm or norm in k for k in _NHL_ABBR_LOGOS):
        for k, abbr in _NHL_ABBR_LOGOS.items():
            if k in norm or norm in k:
                return f"https://a.espncdn.com/i/teamlogos/nhl/500/{abbr}.png"
    logos, norm_logos = load_team_logos()
    if team_name in logos:
        return logos[team_name]
    if norm in norm_logos:
        return norm_logos[norm]
    # Búsqueda parcial o insensible
    for k, v in norm_logos.items():
        if k and (k in norm or norm in k):
            return v
    return ""

def enrich_h2h_with_logos(h2h_data, home_team=None, away_team=None, home_logo="", away_logo=""):
    if not isinstance(h2h_data, dict):
        return h2h_data
    
    for sub_match in h2h_data.get("home_last_5", []):
        m_home = sub_match.get("match_home")
        m_away = sub_match.get("match_away")
        if not m_home and sub_match.get("venue") == "Local":
            m_home = home_team
            m_away = sub_match.get("opponent")
        elif not m_home and sub_match.get("venue") == "Visitante":
            m_home = sub_match.get("opponent")
            m_away = home_team
        
        if not sub_match.get("home_logo"):
            sub_match["home_logo"] = home_logo if (m_home == home_team and home_logo) else get_team_logo(m_home)
        if not sub_match.get("away_logo"):
            sub_match["away_logo"] = away_logo if (m_away == away_team and away_logo) else get_team_logo(m_away)

    for sub_match in h2h_data.get("away_last_5", []):
        m_home = sub_match.get("match_home")
        m_away = sub_match.get("match_away")
        if not m_home and sub_match.get("venue") == "Local":
            m_home = away_team
            m_away = sub_match.get("opponent")
        elif not m_home and sub_match.get("venue") == "Visitante":
            m_home = sub_match.get("opponent")
            m_away = away_team

        if not sub_match.get("home_logo"):
            sub_match["home_logo"] = home_logo if (m_home == home_team and home_logo) else get_team_logo(m_home)
        if not sub_match.get("away_logo"):
            sub_match["away_logo"] = away_logo if (m_away == away_team and away_logo) else get_team_logo(m_away)

    for d in h2h_data.get("head_to_head", []):
        m_home = d.get("match_home") or d.get("home_team") or home_team
        m_away = d.get("match_away") or d.get("away_team") or away_team
        if not d.get("home_logo"):
            d["home_logo"] = home_logo if (m_home == home_team and home_logo) else get_team_logo(m_home)
        if not d.get("away_logo"):
            d["away_logo"] = away_logo if (m_away == away_team and away_logo) else get_team_logo(m_away)

    return h2h_data


from prediction_engine import (
    calculate_match_probabilities,
    calculate_live_probabilities,
    calculate_nba_probabilities,
    calculate_nba_live_probabilities,
    calculate_nhl_probabilities,
    calculate_nhl_live_probabilities,
    get_football_team_ratings,
    get_nba_team_ratings,
    get_nhl_team_ratings,
    generate_match_h2h,
    deterministic_hash,
    detect_league_and_country
)
from ai_analyzer import (
    generate_ai_analysis,
    generate_live_ai_analysis,
    generate_nba_ai_analysis,
    generate_nba_live_ai_analysis,
    generate_nhl_ai_analysis,
    generate_nhl_live_ai_analysis
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
ESPN_LEAGUES_BY_ID = {
    # España
    "740": ("LaLiga EA Sports", "España", "🇪🇸"),
    "741": ("LaLiga Hypermotion", "España", "🇪🇸"),
    "3928": ("LaLiga Hypermotion", "España", "🇪🇸"),
    "3951": ("Copa del Rey", "España", "🇪🇸"),
    # Inglaterra
    "382": ("Premier League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "3914": ("Championship", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "3917": ("National League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "3920": ("Carabao Cup (EFL Cup)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "3918": ("FA Cup", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    # Alemania
    "720": ("Bundesliga", "Alemania", "🇩🇪"),
    "3927": ("2. Bundesliga", "Alemania", "🇩🇪"),
    "3954": ("Copa de Alemania (DFB-Pokal)", "Alemania", "🇩🇪"),
    # Francia
    "710": ("Ligue 1", "Francia", "🇫🇷"),
    "3926": ("Ligue 2", "Francia", "🇫🇷"),
    # Italia
    "705": ("Serie A", "Italia", "🇮🇹"),
    "3931": ("Serie B", "Italia", "🇮🇹"),
    "3956": ("Copa de Italia (Coppa Italia)", "Italia", "🇮🇹"),
    # Países Bajos
    "725": ("Eredivisie", "Países Bajos", "🇳🇱"),
    "3933": ("Keuken Kampioen Divisie", "Países Bajos", "🇳🇱"),
    # Portugal
    "715": ("Primeira Liga", "Portugal", "🇵🇹"),
    # Bélgica
    "3901": ("Jupiler Pro League", "Bélgica", "🇧🇪"),
    # Suiza
    "3947": ("Super League Suiza", "Suiza", "🇨🇭"),
    # Turquía
    "3946": ("Süper Lig", "Turquía", "🇹🇷"),
    # Suecia
    "3945": ("Allsvenskan", "Suecia", "🇸🇪"),
    # Noruega
    "3960": ("Eliteserien", "Noruega", "🇳🇴"),
    # Dinamarca
    "3913": ("Superligaen", "Dinamarca", "🇩🇰"),
    # Rusia
    "3939": ("Russian Premier League", "Rusia", "🇷🇺"),
    # México
    "760": ("Liga MX", "México", "🇲🇽"),
    "3932": ("Liga de Expansión MX", "México", "🇲🇽"),
    "23541": ("Liga MX Femenil", "México", "🇲🇽"),
    # Centroamérica
    "3943": ("Primera División de El Salvador", "El Salvador", "🇸🇻"),
    "4005": ("Primera División de Costa Rica", "Costa Rica", "🇨🇷"),
    "3929": ("Liga Nacional de Honduras", "Honduras", "🇭🇳"),
    "3930": ("Liga Nacional de Guatemala", "Guatemala", "🇬🇹"),
    "3942": ("Liga Panameña de Fútbol (LPF)", "Panamá", "🇵🇦"),
    "3941": ("Liga Primera de Nicaragua", "Nicaragua", "🇳🇮"),
    # Sudamérica
    "650": ("Liga BetPlay Dimayor", "Colombia", "🇨🇴"),
    "670": ("Liga 1 Perú", "Perú", "🇵🇪"),
    "660": ("LigaPro Serie A", "Ecuador", "🇪🇨"),
    "620": ("División Profesional (Bolivia)", "Bolivia", "🇧🇴"),
    "745": ("Liga Profesional Argentina", "Argentina", "🇦🇷"),
    "3904": ("Primera B Metropolitana", "Argentina", "🇦🇷"),
    "680": ("Primera División de Uruguay", "Uruguay", "🇺🇾"),
    "630": ("Primera División de Chile", "Chile", "🇨🇱"),
    "640": ("Primera División de Paraguay", "Paraguay", "🇵🇾"),
    "690": ("Liga FUTVE", "Venezuela", "🇻🇪"),
    "268": ("Brasileirão Série A", "Brasil", "🇧🇷"),
    # Asia y Medio Oriente
    "750": ("J1 League", "Japón", "🇯🇵"),
    "8376": ("Chinese Super League", "China", "🇨🇳"),
    "21231": ("Saudi Pro League", "Arabia Saudita", "🇸🇦"),
    # Estados Unidos
    "4002": ("USL Championship", "Estados Unidos", "🇺🇸"),
    "5487": ("NCAA Soccer", "Estados Unidos", "🇺🇸"),
    # Torneos / Selecciones
    "20649": ("UEFA Nations League / Eliminatorias", "Europa", "🇪🇺"),
    "3923": ("Amistoso Internacional", "Internacional", "🌎"),
}

ESPN_SLUG_PREFIXES = [
    ("slv.", "Primera División de El Salvador", "El Salvador", "🇸🇻"),
    ("crc.", "Primera División de Costa Rica", "Costa Rica", "🇨🇷"),
    ("hon.", "Liga Nacional de Honduras", "Honduras", "🇭🇳"),
    ("gua.", "Liga Nacional de Guatemala", "Guatemala", "🇬🇹"),
    ("pan.", "Liga Panameña de Fútbol (LPF)", "Panamá", "🇵🇦"),
    ("nic.", "Liga Primera de Nicaragua", "Nicaragua", "🇳🇮"),
    ("ven.", "Liga FUTVE", "Venezuela", "🇻🇪"),
    ("col.", "Liga BetPlay Dimayor", "Colombia", "🇨🇴"),
    ("per.", "Liga 1 Perú", "Perú", "🇵🇪"),
    ("bol.", "División Profesional (Bolivia)", "Bolivia", "🇧🇴"),
    ("ecu.", "LigaPro Serie A", "Ecuador", "🇪🇨"),
    ("arg.", "Liga Profesional Argentina", "Argentina", "🇦🇷"),
    ("uru.", "Primera División de Uruguay", "Uruguay", "🇺🇾"),
    ("chi.", "Primera División de Chile", "Chile", "🇨🇱"),
    ("par.", "Primera División de Paraguay", "Paraguay", "🇵🇾"),
    ("bra.", "Brasileirão Série A", "Brasil", "🇧🇷"),
    ("mex.w.", "Liga MX Femenil", "México", "🇲🇽"),
    ("mex.", "Liga MX", "México", "🇲🇽"),
    ("esp.w.", "Liga F (Femenil)", "España", "🇪🇸"),
    ("esp.copa_del_rey", "Copa del Rey", "España", "🇪🇸"),
    ("esp.2", "LaLiga Hypermotion", "España", "🇪🇸"),
    ("esp.1", "LaLiga EA Sports", "España", "🇪🇸"),
    ("esp.", "LaLiga EA Sports", "España", "🇪🇸"),
    ("eng.w.league_cup", "English WSL Cup (Femenil)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.w.", "FA Women's Super League (WSL)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.fa", "FA Cup", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.league_cup", "Carabao Cup (EFL Cup)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.trophy", "EFL Trophy", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.1", "Premier League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.2", "Championship", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.3", "League One", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.4", "League Two", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.5", "National League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("eng.", "Premier League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    ("ger.dfb_pokal", "Copa de Alemania (DFB-Pokal)", "Alemania", "🇩🇪"),
    ("ger.cup", "Copa de Alemania (DFB-Pokal)", "Alemania", "🇩🇪"),
    ("ger.2", "2. Bundesliga", "Alemania", "🇩🇪"),
    ("ger.", "Bundesliga", "Alemania", "🇩🇪"),
    ("fra.2", "Ligue 2", "Francia", "🇫🇷"),
    ("fra.", "Ligue 1", "Francia", "🇫🇷"),
    ("ita.coppa_italia", "Copa de Italia (Coppa Italia)", "Italia", "🇮🇹"),
    ("ita.cup", "Copa de Italia (Coppa Italia)", "Italia", "🇮🇹"),
    ("ita.2", "Serie B", "Italia", "🇮🇹"),
    ("ita.", "Serie A", "Italia", "🇮🇹"),
    ("por.", "Primeira Liga", "Portugal", "🇵🇹"),
    ("ned.2", "Keuken Kampioen Divisie", "Países Bajos", "🇳🇱"),
    ("ned.", "Eredivisie", "Países Bajos", "🇳🇱"),
    ("bel.", "Jupiler Pro League", "Bélgica", "🇧🇪"),
    ("sui.", "Super League Suiza", "Suiza", "🇨🇭"),
    ("jpn.3", "J3 League", "Japón", "🇯🇵"),
    ("jpn.2", "J2 League", "Japón", "🇯🇵"),
    ("jpn.", "J1 League", "Japón", "🇯🇵"),
    ("tur.", "Süper Lig", "Turquía", "🇹🇷"),
    ("swe.", "Allsvenskan", "Suecia", "🇸🇪"),
    ("nor.", "Eliteserien", "Noruega", "🇳🇴"),
    ("den.", "Superligaen", "Dinamarca", "🇩🇰"),
    ("chn.", "Chinese Super League", "China", "🇨🇳"),
    ("ksa.", "Saudi Pro League", "Arabia Saudita", "🇸🇦"),
    ("uefa.nations", "UEFA Nations League", "Europa", "🇪🇺"),
    ("concacaf.nations", "Concacaf Nations League", "Concacaf", "🌎"),
    ("fifa.worldq.conmebol", "Eliminatorias CONMEBOL", "Sudamérica", "🌎"),
    ("fifa.worldq.concacaf", "Clasificatorias Concacaf", "Concacaf", "🌎"),
    ("fifa.worldq.uefa", "Clasificatorias UEFA", "Europa", "🇪🇺"),
    ("fifa.friendly", "Amistoso Internacional", "Internacional", "🌎"),
]

def get_league_and_country_info(comp_name, sport="football", home_team="", away_team="", espn_league_id=""):
    # 0. Si viene ESPN League ID directo
    if espn_league_id and str(espn_league_id) in ESPN_LEAGUES_BY_ID:
        t, c, f = ESPN_LEAGUES_BY_ID[str(espn_league_id)]
        return t, c, f

    comp_lower = (comp_name or "").lower().strip()

    # 1. Resolver por prefijo de slug de ESPN
    for pfx, t_name, c_name, flag in ESPN_SLUG_PREFIXES:
        if comp_lower.startswith(pfx) or f"/{pfx}" in comp_lower or f"_{pfx}" in comp_lower or f"-{pfx}" in comp_lower:
            return t_name, c_name, flag

    # 2. Casos directos por nombre explícito de país o liga
    # Copas Nacionales Principales
    if "copa del rey" in comp_lower or "copa-del-rey" in comp_lower or "copa rey" in comp_lower:
        return "Copa del Rey", "España", "🇪🇸"
    if "carabao" in comp_lower or "efl cup" in comp_lower or ("league cup" in comp_lower and "wsl" not in comp_lower and "women" not in comp_lower):
        return "Carabao Cup (EFL Cup)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "fa cup" in comp_lower or "the fa cup" in comp_lower or "facup" in comp_lower:
        return "FA Cup", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "coppa italia" in comp_lower or "copa italia" in comp_lower or "copa de italia" in comp_lower:
        return "Copa de Italia (Coppa Italia)", "Italia", "🇮🇹"
    if "dfb-pokal" in comp_lower or "dfb pokal" in comp_lower or "copa de alemania" in comp_lower or "copa alemana" in comp_lower or "german cup" in comp_lower:
        return "Copa de Alemania (DFB-Pokal)", "Alemania", "🇩🇪"
    if sport == "nba" or "nba" in comp_lower:
        return "NBA", "Estados Unidos", "🏀"
    if "salvador" in comp_lower or "slv.1" in comp_lower:
        return "Primera División de El Salvador", "El Salvador", "🇸🇻"
    if "costa rica" in comp_lower or "crc.1" in comp_lower or "promerica" in comp_lower:
        return "Primera División de Costa Rica", "Costa Rica", "🇨🇷"
    if "hondur" in comp_lower or "hon.1" in comp_lower or "betcris" in comp_lower:
        return "Liga Nacional de Honduras", "Honduras", "🇭🇳"
    if "guatemal" in comp_lower or "gua.1" in comp_lower or "banrural" in comp_lower or "liga guate" in comp_lower:
        return "Liga Nacional de Guatemala", "Guatemala", "🇬🇹"
    if "panam" in comp_lower or "pan.1" in comp_lower or "lpf" in comp_lower:
        return "Liga Panameña de Fútbol (LPF)", "Panamá", "🇵🇦"
    if "nicarag" in comp_lower or "nic.1" in comp_lower or "liga primera" in comp_lower:
        return "Liga Primera de Nicaragua", "Nicaragua", "🇳🇮"
    if "venezuel" in comp_lower or "ven.1" in comp_lower or "futve" in comp_lower:
        return "Liga FUTVE", "Venezuela", "🇻🇪"
    if "peru" in comp_lower or "perú" in comp_lower or "per.1" in comp_lower or "liga 1" in comp_lower or "liga1" in comp_lower:
        return "Liga 1 Perú", "Perú", "🇵🇪"
    if "boliv" in comp_lower or "bol.1" in comp_lower:
        return "División Profesional (Bolivia)", "Bolivia", "🇧🇴"
    if "suiz" in comp_lower or "switzer" in comp_lower or "swiss" in comp_lower or "sui.1" in comp_lower:
        return "Super League Suiza", "Suiza", "🇨🇭"
    if "bélgic" in comp_lower or "belgic" in comp_lower or "belgium" in comp_lower or "bel.1" in comp_lower or "jupiler" in comp_lower:
        return "Jupiler Pro League", "Bélgica", "🇧🇪"
    if "j3" in comp_lower or "j.league 3" in comp_lower or "j league 3" in comp_lower or "jpn.3" in comp_lower:
        return "J3 League", "Japón", "🇯🇵"
    if "j2" in comp_lower or "j.league 2" in comp_lower or "j league 2" in comp_lower or "jpn.2" in comp_lower:
        return "J2 League", "Japón", "🇯🇵"
    if "japón" in comp_lower or "japon" in comp_lower or "japan" in comp_lower or "jpn.1" in comp_lower or "j1" in comp_lower:
        return "J1 League", "Japón", "🇯🇵"
    if "mex.w" in comp_lower or ("femenil" in comp_lower and ("mex" in comp_lower or "liga mx" in comp_lower)):
        return "Liga MX Femenil", "México", "🇲🇽"
    if "wsl" in comp_lower or "players cup" in comp_lower or "w.league" in comp_lower:
        return "English WSL Cup (Femenil)", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "women" in comp_lower or "femenil" in comp_lower or "fem." in comp_lower:
        return "Competición Femenil", "Inglaterra" if ("eng" in comp_lower or "birmingham" in comp_lower) else "Internacional", "⚽"
    if "premier" in comp_lower:
        return "Premier League", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "championship" in comp_lower:
        return "Championship", "Inglaterra", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if "brasileir" in comp_lower or "brazil" in comp_lower or "bra.1" in comp_lower:
        return "Brasileirão Série A", "Brasil", "🇧🇷"
    if "serie a" in comp_lower and "brasil" not in comp_lower and "brazil" not in comp_lower:
        return "Serie A", "Italia", "🇮🇹"
    if "bundesliga" in comp_lower:
        return "Bundesliga", "Alemania", "🇩🇪"
    if "ligue 1" in comp_lower:
        return "Ligue 1", "Francia", "🇫🇷"
    if "ligue 2" in comp_lower or "ligue-2" in comp_lower:
        return "Ligue 2", "Francia", "🇫🇷"
    if "primeira liga" in comp_lower or "portugal" in comp_lower:
        return "Primeira Liga", "Portugal", "🇵🇹"
    if "eredivisie" in comp_lower or "netherlands" in comp_lower:
        return "Eredivisie", "Países Bajos", "🇳🇱"
    if "keuken" in comp_lower or "kampioen" in comp_lower:
        return "Keuken Kampioen Divisie", "Países Bajos", "🇳🇱"
    if "argentin" in comp_lower or "arg.1" in comp_lower:
        return "Liga Profesional Argentina", "Argentina", "🇦🇷"
    if "colomb" in comp_lower or "col.1" in comp_lower or "betplay" in comp_lower:
        return "Liga BetPlay Dimayor", "Colombia", "🇨🇴"
    if "chile" in comp_lower or "chi.1" in comp_lower:
        return "Primera División de Chile", "Chile", "🇨🇱"
    if "uruguay" in comp_lower or "uru.1" in comp_lower:
        return "Primera División de Uruguay", "Uruguay", "🇺🇾"
    if "paraguay" in comp_lower or "par.1" in comp_lower:
        return "Primera División de Paraguay", "Paraguay", "🇵🇾"
    if "ecuador" in comp_lower or "ecu.1" in comp_lower or "ligapro" in comp_lower:
        return "LigaPro Serie A", "Ecuador", "🇪🇨"
    if "mexic" in comp_lower or "méxic" in comp_lower or "liga mx" in comp_lower or "mex.1" in comp_lower:
        return "Liga MX", "México", "🇲🇽"
    if "mls" in comp_lower or "major league soccer" in comp_lower or "usl" in comp_lower or "ncaa" in comp_lower or "usa" in comp_lower:
        return "Major League Soccer (MLS)", "Estados Unidos", "🇺🇸"
    if "saudi" in comp_lower or "arab" in comp_lower or "ksa.1" in comp_lower:
        return "Saudi Pro League", "Arabia Saudita", "🇸🇦"
    if "super-lig" in comp_lower or "süper lig" in comp_lower or "turqu" in comp_lower:
        return "Süper Lig", "Turquía", "🇹🇷"
    if "allsvenskan" in comp_lower or "suecia" in comp_lower or "sweden" in comp_lower:
        return "Allsvenskan", "Suecia", "🇸🇪"
    if "eliteserien" in comp_lower or "noruega" in comp_lower or "norway" in comp_lower:
        return "Eliteserien", "Noruega", "🇳🇴"
    if "superliga" in comp_lower or "dinamarca" in comp_lower or "denmark" in comp_lower:
        return "Superligaen", "Dinamarca", "🇩🇰"
    if "chinese" in comp_lower or "china" in comp_lower or "csl" in comp_lower:
        return "Chinese Super League", "China", "🇨🇳"
    if "libertadores" in comp_lower:
        return "Copa CONMEBOL Libertadores", "Sudamérica", "🏆"
    if "sudamericana" in comp_lower:
        return "Copa CONMEBOL Sudamericana", "Sudamérica", "🏆"
    if "champions" in comp_lower:
        return "UEFA Champions League", "Europa", "🏆"
    if "concacaf" in comp_lower and "nations" in comp_lower:
        return "Concacaf Nations League", "Concacaf", "🌎"
    if "nations" in comp_lower or "uefa" in comp_lower:
        if "league d" in comp_lower or "nations_d" in comp_lower or "league_d" in comp_lower:
            t_uefa = "UEFA Nations League D"
        elif "league c" in comp_lower or "nations_c" in comp_lower or "league_c" in comp_lower:
            t_uefa = "UEFA Nations League C"
        elif "league b" in comp_lower or "nations_b" in comp_lower or "league_b" in comp_lower:
            t_uefa = "UEFA Nations League B"
        else:
            t_uefa = "UEFA Nations League"
        return t_uefa, "Europa", "🇪🇺"
    if "africa cup" in comp_lower or "afcon" in comp_lower or "copa africana" in comp_lower:
        return "Eliminatorias Copa Africana (Selecciones)", "África", "🌍"
    if "conmebol" in comp_lower or "sudameric" in comp_lower:
        return "Eliminatorias CONMEBOL", "Sudamérica", "🌎"
    if "selección" in comp_lower or "amistoso" in comp_lower or "fifa" in comp_lower or "friendly" in comp_lower or "friendlies" in comp_lower:
        return "Selecciones FIFA", "Internacional", "🌎"

    # España: ÚNICAMENTE si dice explícitamente LaLiga, España o EA Sports
    if "laliga" in comp_lower or "hypermotion" in comp_lower or (("la liga" in comp_lower or "primera division" in comp_lower) and any(k in comp_lower for k in ["españ", "spain", "ea sports", "santander"])):
        t_spain = "LaLiga Hypermotion" if ("hypermotion" in comp_lower or "segunda" in comp_lower) else "LaLiga EA Sports"
        return t_spain, "España", "🇪🇸"

    # 3. Detector experto si tenemos equipos o slug técnico
    t_clean, c_name, flag, _ = detect_league_and_country(home_team, away_team, sport, comp_name, "")
    if c_name and c_name != "Internacional" and t_clean != "Competición Oficial":
        return t_clean, c_name, flag

    # 4. Fallback limpio
    clean_title = comp_name if (comp_name and not comp_name.lower().startswith("202") and comp_name.lower() not in ("regular-season", "pre-season", "post-season", "oficial", "desconocida", "first-stage", "group-stage", "fall-season")) else "Competición Oficial"
    return clean_title, "Internacional", "⚽"

LEAGUE_TOTAL_ROUNDS = {
    "liga_mx": 17,
    "liga_mx_femenil": 17,
    "expansion_mx": 15,
    "guatemala": 22,
    "colombia": 20,
    "peru": 17,
    "argentina": 27,
    "brasileirao": 38,
    "suecia": 30,
    "eliteserien": 30,
    "j1_league": 38,
    "j2_league": 38,
    "j3_league": 38,
    "premier_league": 38,
    "laliga": 38,
    "serie_a": 38,
    "bundesliga": 34,
    "francia": 34,
    "holanda": 34,
    "liga_portugal": 34,
    "belgica": 30,
    "suiza": 38,
    "austria": 22,
    "superligaen": 22,
    "grecia": 26,
    "turquia": 38,
    "uefa_nations_league": 6,
    "uefa_nations_league_b": 6,
    "uefa_nations_league_c": 6,
    "uefa_nations_league_d": 6,
    "champions_league": 8,
    "europa_league": 8,
    "conference_league": 6,
}

def analyze_season_phase(league_slug: str, league_name: str, round_val: str, date_iso: str = "") -> dict:
    """
    Identifica si un torneo está en su recta final, últimas fechas o fase de playoffs/copa.
    Alerta sobre descompresión competitiva, rotación de plantillas y merma de rendimiento
    en clubes sin objetivos pendientes o ya campeones.
    """
    import re
    r_str = str(round_val or "").lower().strip()
    is_playoff = any(k in r_str for k in ["final", "semi", "cuartos", "playoff", "octavos", "1/8", "1/4", "repechaje", "play-in"])
    if is_playoff:
        rnd_title = str(round_val).title() if round_val else "Playoffs"
        return {
            "is_closing_phase": True,
            "phase_type": "playoff",
            "stage_label": f"Fase Final ({rnd_title})",
            "alert_title": "🏆 Eliminatoria Directa / Playoffs",
            "alert_message": "Duelo de eliminación directa o fase de copa. Suele primar el orden defensivo, mayor tensión táctica y menor margen de goles.",
            "badge_bg": "bg-purple-950/90 text-purple-300 border-purple-600/60"
        }

    num_match = re.search(r'\b(\d{1,2})\b', r_str)
    cur_round = int(num_match.group(1)) if num_match else None

    l_key = f"{(league_slug or '').lower()} {(league_name or '').lower()}"
    tot_rounds = None
    for k, v in LEAGUE_TOTAL_ROUNDS.items():
        if k in l_key or k.replace("_", " ") in l_key:
            tot_rounds = v
            break

    is_annual_closing_month = False
    if date_iso and len(date_iso) >= 7:
        month = date_iso[5:7]
        if month in ("11", "12"):
            annual_leagues = ["brasil", "brasileir", "suecia", "allsvenskan", "noruega", "eliteserien", "japon", "j1", "j2", "j3", "mls", "bolivia", "peru", "guatemala"]
            if any(al in l_key for al in annual_leagues):
                is_annual_closing_month = True
        elif month == "04" and "nhl" in l_key:
            is_annual_closing_month = True

    if cur_round and tot_rounds:
        pct = cur_round / float(tot_rounds)
        remaining = tot_rounds - cur_round
        if remaining <= 2 and remaining >= 0:
            return {
                "is_closing_phase": True,
                "phase_type": "critical_end",
                "stage_label": f"Últimas Fechas ({cur_round}/{tot_rounds})",
                "alert_title": "⚠️ Alerta Fin de Temporada & Descompresión",
                "alert_message": f"Faltan solo {remaining} fechas para concluir el torneo. Atención con la descompresión competitiva: clubes sin riesgo de descenso o con objetivos asegurados tienden a rotar titulares y bajar intensidad física.",
                "badge_bg": "bg-rose-950/90 text-rose-300 border-rose-600/60"
            }
        elif pct >= 0.76 or is_annual_closing_month:
            return {
                "is_closing_phase": True,
                "phase_type": "closing_stretch",
                "stage_label": f"Recta Final ({cur_round}/{tot_rounds})",
                "alert_title": "🏁 Recta Final de Temporada",
                "alert_message": f"Jornada {cur_round} de {tot_rounds}. Evalúa la motivación: clubes que pelean títulos o permanencia rinden al límite, mientras que equipos en zona media sin objetivos suelen registrar desempeños irregulares.",
                "badge_bg": "bg-amber-950/90 text-amber-300 border-amber-600/60"
            }

    if is_annual_closing_month:
        return {
            "is_closing_phase": True,
            "phase_type": "closing_stretch",
            "stage_label": "Tramo Final de Torneo",
            "alert_title": "🏁 Cierre de Año Calendario",
            "alert_message": "Torneo en sus semanas decisivas de fin de año. Revisa los objetivos puntuales de cada equipo antes de apostar a cuotas desbalanceadas.",
            "badge_bg": "bg-amber-950/90 text-amber-300 border-amber-600/60"
        }

    return {
        "is_closing_phase": False,
        "phase_type": "regular",
        "stage_label": f"Jornada {cur_round}" if cur_round else "",
        "alert_title": "",
        "alert_message": "",
        "badge_bg": ""
    }

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

_espn_event_cache = {}

def fetch_espn_event_real_stats(event_id: str, allow_network: bool = True) -> dict:
    """
    Consulta las estadísticas oficiales en vivo de ESPN (boxscore en tiempo real):
    tiros a puerta, tiros totales, córners reales, posesión exacta, faltas y tarjetas.
    Usa caché con TTL de 30s para máxima rapidez.
    """
    global _espn_event_cache
    now = time.time()
    if event_id in _espn_event_cache:
        cached = _espn_event_cache[event_id]
        if now - cached["timestamp"] < 45:
            return cached["data"]

    if not allow_network:
        return None

    if len(_espn_event_cache) > 40:
        oldest_k = next(iter(_espn_event_cache))
        _espn_event_cache.pop(oldest_k, None)

    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={event_id}"
    try:
        resp = requests.get(url, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            header = data.get("header", {})
            league_obj = header.get("league", {})
            season_obj = header.get("season", {})
            league_name = league_obj.get("name", "") or season_obj.get("name", "")
            league_id = str(league_obj.get("id", ""))
            league_slug = str(league_obj.get("slug", ""))

            boxscore = data.get("boxscore", {})
            teams = boxscore.get("teams", [])
            header_comps = header.get("competitions", [{}])[0].get("competitors", [])

            home_id = next((str(c.get("id")) for c in header_comps if c.get("homeAway") == "home"), None)
            away_id = next((str(c.get("id")) for c in header_comps if c.get("homeAway") == "away"), None)

            home_team_stats = None
            away_team_stats = None

            for t in teams:
                t_id = str(t.get("team", {}).get("id", ""))
                if home_id and t_id == home_id:
                    home_team_stats = t
                elif away_id and t_id == away_id:
                    away_team_stats = t

            if not home_team_stats and len(teams) >= 1:
                home_team_stats = teams[0]
            if not away_team_stats and len(teams) >= 2:
                away_team_stats = teams[1]

            def extract_team_stats(t_obj):
                if not t_obj:
                    return {}
                st = {}
                for s in t_obj.get("statistics", []):
                    st[s.get("name", "")] = s.get("displayValue", "")
                return st

            st_h = extract_team_stats(home_team_stats)
            st_a = extract_team_stats(away_team_stats)

            def parse_stat_int(val, default=0):
                try:
                    return int(str(val).split(".")[0].strip())
                except Exception:
                    return default

            def parse_stat_float(val, default=50.0):
                try:
                    return float(str(val).replace("%", "").strip())
                except Exception:
                    return default

            poss_h = round(parse_stat_float(st_h.get("possessionPct"), 50.0))
            poss_a = 100 - poss_h
            shots_h = parse_stat_int(st_h.get("shotsOnTarget"), 0)
            shots_a = parse_stat_int(st_a.get("shotsOnTarget"), 0)
            tot_h = parse_stat_int(st_h.get("totalShots"), shots_h)
            tot_a = parse_stat_int(st_a.get("totalShots"), shots_a)
            corn_h = parse_stat_int(st_h.get("wonCorners"), 0)
            corn_a = parse_stat_int(st_a.get("wonCorners"), 0)
            fouls_h = parse_stat_int(st_h.get("foulsCommitted"), 0)
            fouls_a = parse_stat_int(st_a.get("foulsCommitted"), 0)
            yc_h = parse_stat_int(st_h.get("yellowCards"), 0)
            yc_a = parse_stat_int(st_a.get("yellowCards"), 0)

            res = {
                "league_name": league_name,
                "league_id": league_id,
                "league_slug": league_slug,
                "stats": {
                    "possession_home": poss_h,
                    "possession_away": poss_a,
                    "shots_on_target_home": shots_h,
                    "shots_on_target_away": shots_a,
                    "total_shots_home": tot_h,
                    "total_shots_away": tot_a,
                    "corners_home": corn_h,
                    "corners_away": corn_a,
                    "fouls_home": fouls_h,
                    "fouls_away": fouls_a,
                    "yellow_cards_home": yc_h,
                    "yellow_cards_away": yc_a,
                    "dangerous_attacks_home": round(poss_h * 0.9),
                    "dangerous_attacks_away": round(poss_a * 0.9),
                    "is_real_live": True
                }
            }
            _espn_event_cache[event_id] = {"data": res, "timestamp": now}
            return res
    except Exception as ex:
        _espn_event_cache[event_id] = {"data": None, "timestamp": now}
        print(f"[ESPN] Error fetching event stats {event_id}: {ex}")
    return None

def find_scraped_h2h(home_name: str, away_name: str):
    """
    Busca si el partido en vivo ya existe en la base de datos oficial escrapeada (data/*.json).
    Si existe, devuelve su H2H verificado oficial de FotMob para que coincida exactamente 1:1
    entre la tarjeta pre-partido y la tarjeta en vivo.
    """
    def clean_team_key(name):
        return re.sub(r'[^a-z0-9]', '', (name or '').lower())

    h_norm = clean_team_key(home_name)
    a_norm = clean_team_key(away_name)
    if not h_norm or not a_norm:
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        return None

    for fname in os.listdir(data_dir):
        if fname.endswith("_real.json"):
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                matches = payload.get("upcoming_matches", [])
                for m in matches:
                    mh = clean_team_key(m.get("home_team", ""))
                    ma = clean_team_key(m.get("away_team", ""))
                    if ((h_norm in mh or mh in h_norm) and (a_norm in ma or ma in a_norm)) or \
                       ((h_norm in ma or ma in h_norm) and (a_norm in mh or mh in a_norm)):
                        h2h = m.get("h2h")
                        if h2h and (h2h.get("head_to_head") or h2h.get("home_last_5")):
                            return h2h
            except Exception:
                continue
    return None

def fetch_espn_live_soccer():
    """
    Obtiene partidos de fútbol en vivo transmitidos por ESPN (incluye selecciones como México, Concacaf, Conmebol, etc.).
    Soporta reconocimiento nativo de medio tiempo (descanso/HT) y vinculación con el H2H oficial pre-partido.
    """
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
        resp = requests.get(url, timeout=3.5)
        if resp.status_code == 200:
            events = resp.json().get("events", [])
            live_events = [e for e in events if e.get("status", {}).get("type", {}).get("state") == "in"]
            
            # Prefetch no-bloqueante de detalles y estadísticas para eventos en vivo
            event_ids = [str(e.get("id")) for e in live_events if e.get("id")]
            if event_ids:
                try:
                    from concurrent.futures import ThreadPoolExecutor, wait
                    executor = ThreadPoolExecutor(max_workers=4)
                    futures = [executor.submit(fetch_espn_event_real_stats, eid, True) for eid in event_ids[:6]]
                    wait(futures, timeout=2.0)
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass

            live_list = []
            for e in live_events:
                    comp = e.get("competitions", [{}])[0]
                    competitors = comp.get("competitors", [])
                    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
                    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})

                    home_name = home.get("team", {}).get("displayName", "Local")
                    away_name = away.get("team", {}).get("displayName", "Visitante")
                    score_h = int(home.get("score", 0) or 0)
                    score_a = int(away.get("score", 0) or 0)

                    # Detección precisa de Medio Tiempo / Descanso (Halftime)
                    status_type = e.get("status", {}).get("type", {})
                    state_name = str(status_type.get("name", "")).upper()
                    state_desc = str(status_type.get("description", "")).lower()
                    state_detail = str(status_type.get("detail", "")).upper()
                    state_short = str(status_type.get("shortDetail", "")).upper()
                    clock_raw = str(e.get("status", {}).get("displayClock", "")).strip()

                    is_halftime = (
                        state_name in ("STATUS_HALFTIME", "STATUS_END_OF_HALF", "STATUS_INTERMISSION")
                        or any(k in state_desc for k in ["halftime", "half time", "descanso", "medio tiempo", "entretiempo"])
                        or state_detail in ("HT", "HALFTIME")
                        or state_short in ("HT", "HALFTIME")
                        or "ht" in clock_raw.lower()
                    )

                    if is_halftime:
                        minute = 45
                        display_clock = "Descanso (HT)"
                        clock_label = "HT"
                    else:
                        clean_clock = clock_raw.replace("'", "").strip()
                        if "+" in clean_clock:
                            try:
                                minute = int(clean_clock.split("+")[0].strip())
                            except Exception:
                                minute = 45
                            display_clock = clock_raw
                        else:
                            digits = re.findall(r'\d+', clean_clock)
                            minute = int(digits[0]) if digits else 65
                            display_clock = f"{minute}'"
                        clock_label = display_clock

                    event_id = str(e.get('id', ''))
                    real_event_info = fetch_espn_event_real_stats(event_id, allow_network=False) if event_id else None

                    espn_lid = ""
                    uid = e.get("uid", "")
                    if "~l:" in uid:
                        try:
                            espn_lid = uid.split("~l:")[1].split("~")[0]
                        except Exception:
                            pass
                    if not espn_lid and real_event_info and real_event_info.get("league_id"):
                        espn_lid = real_event_info["league_id"]

                    raw_league = ""
                    if real_event_info and real_event_info.get("league_name") and real_event_info.get("league_name").lower() not in ("clausura", "apertura", "regular-season", "league-phase", "group-stage"):
                        raw_league = real_event_info["league_name"]
                    elif real_event_info and real_event_info.get("league_slug"):
                        raw_league = real_event_info["league_slug"]
                    elif real_event_info and real_event_info.get("league_name"):
                        raw_league = real_event_info["league_name"]
                    if not raw_league or raw_league.lower() in ("clausura", "apertura", "regular-season", "pre-season"):
                        raw_league = e.get("season", {}).get("slug", "") or comp.get("league", {}).get("description", "Amistoso Internacional")
                    if "mexico" in home_name.lower() or "chile" in away_name.lower() or "méxico" in home_name.lower():
                        raw_league = "Selecciones FIFA - Amistoso Internacional"

                    league_title, country_name, flag = get_league_and_country_info(raw_league, "football", home_name, away_name, espn_league_id=espn_lid)

                    # Garantizar que el H2H en vivo coincida 1:1 con el H2H de pre-partido si existe en el sistema
                    matched_h2h = find_scraped_h2h(home_name, away_name)
                    if matched_h2h and (matched_h2h.get("head_to_head") or matched_h2h.get("home_last_5")):
                        h2h_data = matched_h2h
                    else:
                        h2h_data = generate_match_h2h(home_name, away_name, "football", league_title, country=country_name)

                    h_ratings = get_football_team_ratings(home_name, league_title, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                    a_ratings = get_football_team_ratings(away_name, league_title, recent_matches=h2h_data.get("away_last_5"), venue_role="away")

                    if real_event_info and real_event_info.get("stats"):
                        live_stats = real_event_info["stats"]
                    else:
                        live_stats = generate_dynamic_live_stats(home_name, away_name, score_h, score_a, minute, h_ratings, a_ratings)

                    pred = calculate_live_probabilities(score_h, score_a, minute, h_ratings, a_ratings, live_stats, is_halftime=is_halftime)
                    ai_resp = generate_live_ai_analysis({
                        "home_team": home_name,
                        "away_team": away_name,
                        "league": league_title,
                        "is_halftime": is_halftime,
                        "display_clock": display_clock
                    }, pred, live_stats)

                    home_logo = home.get("team", {}).get("logo") or get_team_logo(home_name, "football")
                    away_logo = away.get("team", {}).get("logo") or get_team_logo(away_name, "football")
                    enrich_h2h_with_logos(h2h_data, home_team=home_name, away_team=away_name, home_logo=home_logo, away_logo=away_logo)

                    live_list.append({
                        "id": f"espn_soc_{e.get('id')}",
                        "sport": "football",
                        "league": league_title,
                        "country": country_name,
                        "league_flag": flag,
                        "country_flag": flag,
                        "home_team": home_name,
                        "away_team": away_name,
                        "home_logo": home_logo,
                        "away_logo": away_logo,
                        "minute": minute,
                        "display_clock": display_clock,
                        "clock_label": clock_label,
                        "is_halftime": is_halftime,
                        "score_home": score_h,
                        "score_away": score_a,
                        "home_stats": h_ratings,
                        "away_stats": a_ratings,
                        "live_stats": live_stats,
                        "prediction": pred,
                        "season_phase": analyze_season_phase(raw_league, league_title, "", str(e.get("date", ""))[:10]),
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

_NBA_STANDINGS_LOCK = threading.Lock()
_nba_standings_cache = {"data": {}, "timestamp": 0}
_NBA_TEAM_SCHEDULE_LOCK = threading.Lock()
_nba_team_schedule_cache = {}  # {team_id_season: {"events": [...], "timestamp": ts}}


def fetch_espn_nba_standings(force: bool = False) -> dict:
    """
    Obtiene estadísticas oficiales de temporada de todos los equipos NBA desde ESPN Standings
    (avgPointsFor, avgPointsAgainst, record overall/Home/Road, streak, diferencial). Caché de 1h.
    """
    global _nba_standings_cache
    now = time.time()
    if not force and _nba_standings_cache["data"] and (now - _nba_standings_cache["timestamp"] < 3600):
        return _nba_standings_cache["data"]

    with _NBA_STANDINGS_LOCK:
        now = time.time()
        if not force and _nba_standings_cache["data"] and (now - _nba_standings_cache["timestamp"] < 3600):
            return _nba_standings_cache["data"]
        try:
            url = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"
            resp = requests.get(url, timeout=7)
            if resp.status_code == 200:
                sd = resp.json()
                mapping = {}
                for ch in sd.get("children", []):
                    entries = ch.get("standings", {}).get("entries", [])
                    for entry in entries:
                        t_obj = entry.get("team", {}) or {}
                        tid = str(t_obj.get("id", "") or "")
                        dname = str(t_obj.get("displayName", "") or "")
                        sname = str(t_obj.get("shortDisplayName", "") or "")
                        abbr = str(t_obj.get("abbreviation", "") or "")
                        logo = t_obj.get("logo") or ((t_obj.get("logos") or [{}])[0].get("href", ""))

                        info = {
                            "team_id": tid,
                            "displayName": dname,
                            "shortDisplayName": sname,
                            "abbreviation": abbr,
                            "logo": logo,
                        }
                        for st in entry.get("stats", []):
                            name = st.get("name")
                            if not name:
                                continue
                            val = st.get("value")
                            disp = st.get("displayValue")
                            if name in ("avgPointsFor", "avgPointsAgainst", "differential", "winPercent", "wins", "losses", "playoffSeed"):
                                try:
                                    info[name] = float(val if val is not None else disp)
                                except Exception:
                                    pass
                            elif name in ("overall", "Home", "Road", "Last Ten Games", "streak"):
                                info[name] = disp or (str(val) if val is not None else "")

                        if tid:
                            mapping[f"id:{tid}"] = info
                        if dname:
                            mapping[dname.lower()] = info
                        if sname:
                            mapping[sname.lower()] = info
                        if abbr:
                            mapping[f"abbr:{abbr.lower()}"] = info

                if mapping:
                    _nba_standings_cache["data"] = mapping
                    _nba_standings_cache["timestamp"] = now
                    return mapping
        except Exception as ex:
            print(f"[ESPN NBA STANDINGS] Error al consultar clasificación NBA: {ex}")
        return _nba_standings_cache.get("data", {}) or {}


def get_nba_standing_for_team(standings_map: dict, team_name: str, team_id=None):
    if not standings_map:
        return None
    if team_id:
        res = standings_map.get(f"id:{str(team_id)}")
        if res:
            return res
    t_low = (team_name or "").lower().strip()
    if t_low in standings_map:
        return standings_map[t_low]
    for k, v in standings_map.items():
        if k.startswith("id:") or k.startswith("abbr:"):
            continue
        if k in t_low or t_low in k:
            return v
    # Último intento por apodo (última palabra)
    words = [w for w in t_low.split() if len(w) > 3]
    for w in words:
        if w in standings_map:
            return standings_map[w]
    return None


def _extract_espn_nba_stat(stats_list: list, candidate_names: list, default=0.0) -> float:
    if not stats_list:
        return float(default)
    cand_lower = [c.lower() for c in candidate_names]
    for c_name in cand_lower:
        for st in stats_list:
            nm = str(st.get("name", "")).lower()
            if nm == c_name:
                raw = st.get("displayValue") if st.get("displayValue") is not None else st.get("value")
                try:
                    return float(str(raw).replace("%", "").strip())
                except Exception:
                    pass
    return float(default)


def _extract_espn_record_summary(competitor: dict) -> str:
    for r in (competitor.get("records") or []):
        if str(r.get("name", "")).lower() in ("overall", "ytd") or str(r.get("type", "")).lower() in ("total", "ytd"):
            if r.get("summary"):
                return str(r["summary"])
    return ""


def fetch_espn_nba_team_schedule(team_id: str, season: int = None) -> list:
    """
    Obtiene partidos finalizados recientes reales desde el calendario oficial de ESPN para un equipo NBA.
    """
    if not team_id:
        return []
    cache_key = f"{team_id}_{season or 'cur'}"
    now = time.time()
    cached = _nba_team_schedule_cache.get(cache_key)
    if cached and (now - cached.get("timestamp", 0) < 1800):
        return cached.get("events", [])

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    if season:
        url += f"?season={season}"

    parsed = []
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for e in data.get("events", []):
                comp = (e.get("competitions") or [{}])[0]
                st_type = (comp.get("status") or {}).get("type") or {}
                if not st_type.get("completed"):
                    continue
                comps = comp.get("competitors") or []
                if len(comps) < 2:
                    continue
                h_c = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
                a_c = next((c for c in comps if c.get("homeAway") == "away"), comps[1])

                def _parse_sc(c):
                    sc = c.get("score")
                    if isinstance(sc, dict):
                        val = sc.get("value") if sc.get("value") is not None else sc.get("displayValue", 0)
                        return int(round(float(val or 0)))
                    try:
                        return int(round(float(sc or 0)))
                    except Exception:
                        return 0

                sc_h = _parse_sc(h_c)
                sc_a = _parse_sc(a_c)
                h_team_obj = h_c.get("team", {}) or {}
                a_team_obj = a_c.get("team", {}) or {}
                h_id = str(h_team_obj.get("id", h_c.get("id", "")) or "")
                a_id = str(a_team_obj.get("id", a_c.get("id", "")) or "")
                h_name = h_team_obj.get("displayName") or h_team_obj.get("shortDisplayName", "Local")
                a_name = a_team_obj.get("displayName") or a_team_obj.get("shortDisplayName", "Visitante")

                def _tlogo(t_obj):
                    if t_obj.get("logo"):
                        return t_obj["logo"]
                    logos = t_obj.get("logos") or []
                    if logos and isinstance(logos, list):
                        return logos[0].get("href", "")
                    return ""

                raw_date = e.get("date", "")
                date_ddmm = raw_date[:10]
                try:
                    dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    dt_gt = dt_utc.astimezone(timezone(timedelta(hours=-6)))
                    date_ddmm = dt_gt.strftime("%d/%m")
                except Exception:
                    pass

                parsed.append({
                    "id": str(e.get("id", "")),
                    "date": date_ddmm,
                    "raw_date": raw_date,
                    "home_id": h_id,
                    "away_id": a_id,
                    "home_team": h_name,
                    "away_team": a_name,
                    "home_score": sc_h,
                    "away_score": sc_a,
                    "home_logo": _tlogo(h_team_obj),
                    "away_logo": _tlogo(a_team_obj),
                    "winner": h_name if sc_h >= sc_a else a_name
                })
            # Más recientes primero
            parsed.sort(key=lambda x: x.get("raw_date", ""), reverse=True)
            with _NBA_TEAM_SCHEDULE_LOCK:
                _nba_team_schedule_cache[cache_key] = {"events": parsed, "timestamp": now}
    except Exception as ex:
        print(f"[ESPN NBA SCHEDULE] Error consultando equipo {team_id}: {ex}")
        if cached:
            return cached.get("events", [])
    return parsed


def fetch_espn_nba_team_h2h(home_id: str, away_id: str, home_name: str, away_name: str) -> dict:
    """
    Construye el historial real de últimos 5 partidos y duelos directos (Cara a Cara) NBA desde ESPN.
    """
    fallback = generate_match_h2h(home_name, away_name, "nba", "NBA", country="Estados Unidos")
    if not home_id or not away_id:
        return fallback

    home_sched = fetch_espn_nba_team_schedule(str(home_id))
    away_sched = fetch_espn_nba_team_schedule(str(away_id))

    def _to_last5(sched, tid, tname):
        out = []
        tname_l = (tname or "").lower()
        for ev in sched[:5]:
            is_h = (ev["home_id"] == str(tid)) or (ev["home_team"].lower() == tname_l)
            opp = ev["away_team"] if is_h else ev["home_team"]
            my_sc = ev["home_score"] if is_h else ev["away_score"]
            opp_sc = ev["away_score"] if is_h else ev["home_score"]
            out.append({
                "date": ev["date"],
                "opponent": opp,
                "venue": "Local" if is_h else "Visitante",
                "match_home": ev["home_team"],
                "match_away": ev["away_team"],
                "home_score": ev["home_score"],
                "away_score": ev["away_score"],
                "score": f"{ev['home_score']} - {ev['away_score']}",
                "result": "W" if my_sc >= opp_sc else "L",
                "home_logo": ev.get("home_logo", ""),
                "away_logo": ev.get("away_logo", ""),
                "competition": "NBA"
            })
        return out

    home_last_5 = _to_last5(home_sched, home_id, home_name)
    away_last_5 = _to_last5(away_sched, away_id, away_name)

    def _is_direct(ev, tid_a, tid_b):
        ids = {ev.get("home_id"), ev.get("away_id")}
        return str(tid_a) in ids and str(tid_b) in ids

    direct_evs = [ev for ev in home_sched if _is_direct(ev, home_id, away_id)]
    if len(direct_evs) < 3:
        # Complementar con temporada regular anterior en ESPN para tener hasta 5 duelos directos reales
        try:
            cur_year = datetime.now().year
            prev_season = cur_year if datetime.now().month >= 10 else cur_year - 1
            prev_sched = fetch_espn_nba_team_schedule(str(home_id), season=prev_season)
            seen_d = {ev["id"] for ev in direct_evs}
            for ev in prev_sched:
                if ev["id"] not in seen_d and _is_direct(ev, home_id, away_id):
                    direct_evs.append(ev)
                    seen_d.add(ev["id"])
        except Exception:
            pass

    direct_list = []
    for ev in direct_evs[:5]:
        direct_list.append({
            "date": ev["date"],
            "competition": "NBA",
            "tournament": "NBA",
            "match_home": ev["home_team"],
            "match_away": ev["away_team"],
            "home_score": ev["home_score"],
            "away_score": ev["away_score"],
            "score": f"{ev['home_score']} - {ev['away_score']}",
            "winner": ev["winner"],
            "home_team": ev["home_team"],
            "away_team": ev["away_team"],
            "home_logo": ev.get("home_logo", ""),
            "away_logo": ev.get("away_logo", "")
        })

    is_real_recent = bool(home_last_5 and away_last_5)
    final_home_5 = home_last_5 if home_last_5 else fallback["home_last_5"]
    final_away_5 = away_last_5 if away_last_5 else fallback["away_last_5"]
    final_direct = direct_list if direct_list else fallback["head_to_head"]

    w_h = sum(1 for m in final_direct if m["winner"] == home_name or (home_name.lower() in str(m.get("winner", "")).lower()))
    w_a = sum(1 for m in final_direct if m["winner"] == away_name or (away_name.lower() in str(m.get("winner", "")).lower()))
    avg_pts = round(sum(m["home_score"] + m["away_score"] for m in final_direct) / float(len(final_direct) or 1), 1)

    return {
        "home_last_5": final_home_5,
        "away_last_5": final_away_5,
        "head_to_head": final_direct,
        "is_real": bool(is_real_recent or direct_list),
        "is_real_recent": is_real_recent,
        "summary": {
            "home_wins": w_h,
            "draws": 0,
            "away_wins": w_a,
            "avg_goals": avg_pts,
            "text": f"{home_name} {w_h} victorias • {away_name} {w_a} victorias (últimos {len(final_direct)})"
        }
    }


def enrich_nba_match_with_real_h2h(match: dict) -> dict:
    """
    Enriquece bajo demanda un partido NBA (al abrir su modal /api/match/<id>) con H2H real de ESPN
    y recalibra ratings/predicción con sus últimos 5 partidos oficiales sin frenar la carga inicial.
    """
    if not match or match.get("sport") != "nba":
        return match
    if (match.get("h2h") or {}).get("is_real"):
        return match

    standings = fetch_espn_nba_standings()
    home_name = match.get("home_team", "")
    away_name = match.get("away_team", "")
    home_id = match.get("home_id")
    away_id = match.get("away_id")

    h_stand = get_nba_standing_for_team(standings, home_name, home_id)
    a_stand = get_nba_standing_for_team(standings, away_name, away_id)
    if not home_id and h_stand:
        home_id = h_stand.get("team_id")
    if not away_id and a_stand:
        away_id = a_stand.get("team_id")

    h2h_data = fetch_espn_nba_team_h2h(home_id, away_id, home_name, away_name)
    enrich_h2h_with_logos(
        h2h_data,
        home_team=home_name,
        away_team=away_name,
        home_logo=match.get("home_logo", ""),
        away_logo=match.get("away_logo", "")
    )
    match["h2h"] = h2h_data

    if h2h_data.get("is_real_recent") or h_stand or a_stand:
        h_ratings = get_nba_team_ratings(
            home_name,
            recent_matches=h2h_data.get("home_last_5"),
            venue_role="home",
            standing_info=h_stand,
            real_recent=bool(h2h_data.get("is_real_recent"))
        )
        a_ratings = get_nba_team_ratings(
            away_name,
            recent_matches=h2h_data.get("away_last_5"),
            venue_role="away",
            standing_info=a_stand,
            real_recent=bool(h2h_data.get("is_real_recent"))
        )
        match["home_stats"] = h_ratings
        match["away_stats"] = a_ratings
        if not match.get("is_live"):
            pred = calculate_nba_probabilities(h_ratings, a_ratings, home_team=home_name, away_team=away_name)
            match["prediction"] = pred
            if not (match.get("ai_analysis") or {}).get("is_gemini"):
                match["ai_analysis"] = generate_nba_ai_analysis(match, pred)

    return match


def _fetch_espn_scoreboard_events(sport_path: str, day_offsets=(0, 1, 2), include_default: bool = True, timeout: int = 8):
    """
    Consulta ESPN Scoreboard combinando el endpoint por defecto + fechas explícitas en hora de Guatemala (GMT-6),
    evitando que ESPN devuelva solo la jornada de ayer o se salte los partidos de hoy antes del mediodía.
    Retorna (events_dedup, fetch_ok).
    """
    from concurrent.futures import ThreadPoolExecutor

    gt_now = datetime.now(timezone(timedelta(hours=-6)))
    urls = []
    base = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    if include_default:
        urls.append(base)
    seen_dates = set()
    for off in (day_offsets or ()):
        d_str = (gt_now + timedelta(days=int(off))).strftime("%Y%m%d")
        if d_str not in seen_dates:
            seen_dates.add(d_str)
            urls.append(f"{base}?dates={d_str}")

    def _grab(u):
        try:
            r = requests.get(u, timeout=timeout)
            if r.status_code == 200:
                return True, (r.json().get("events", []) or [])
        except Exception:
            pass
        return False, []

    events = []
    seen_ids = set()
    fetch_ok = False
    with ThreadPoolExecutor(max_workers=max(1, min(4, len(urls)))) as ex:
        for ok, evs in ex.map(_grab, urls):
            if ok:
                fetch_ok = True
            for ev in evs:
                eid = str(ev.get("id") or "")
                if eid and eid not in seen_ids:
                    seen_ids.add(eid)
                    events.append(ev)
                elif not eid:
                    events.append(ev)

    return events, fetch_ok


def fetch_espn_live_nba():
    """
    Obtiene partidos de la NBA en vivo transmitidos por ESPN con estadísticas reales de tiro/rebotes/asistencias,
    reloj exacto por cuarto/HT/OT y ratings oficiales de temporada.
    """
    try:
        standings = fetch_espn_nba_standings()
        events, fetch_ok = _fetch_espn_scoreboard_events("basketball/nba", day_offsets=(0,), include_default=True, timeout=7)
        if fetch_ok or events:
            live_list = []
            for e in events:
                status_obj = e.get("status", {}) or {}
                status_type = status_obj.get("type", {}) or {}
                state = status_type.get("state")
                if state == "in":
                    comp = (e.get("competitions") or [{}])[0]
                    competitors = comp.get("competitors", [])
                    if len(competitors) < 2:
                        continue
                    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

                    home_team_obj = home.get("team", {}) or {}
                    away_team_obj = away.get("team", {}) or {}
                    home_id = str(home_team_obj.get("id", home.get("id", "")) or "")
                    away_id = str(away_team_obj.get("id", away.get("id", "")) or "")
                    home_name = home_team_obj.get("displayName", "Local")
                    away_name = away_team_obj.get("displayName", "Visitante")
                    score_h = int(float(home.get("score", 0) or 0))
                    score_a = int(float(away.get("score", 0) or 0))

                    period = int(status_obj.get("period", 1) or 1)
                    clock_secs = float(status_obj.get("clock", 0) or 0)
                    display_clock = str(status_obj.get("displayClock", "0:00") or "0:00")
                    st_name = str(status_type.get("name", "")).upper()
                    st_detail = str(status_type.get("shortDetail", "")).upper()
                    is_halftime = ("HALFTIME" in st_name) or ("HALFTIME" in st_detail) or ("HALF" in st_detail)

                    if is_halftime:
                        q_label = "HT (Descanso)"
                        q_param = "HT (Descanso)"
                        mins_rem = 24.0
                    elif period <= 4:
                        q_label = f"{period}Q {display_clock}"
                        q_param = f"Q{period}"
                        mins_rem = max(0.05, ((4 - period) * 12.0) + (clock_secs / 60.0))
                    else:
                        ot_n = period - 4
                        ot_tag = "OT" if ot_n == 1 else f"OT{ot_n}"
                        q_label = f"{ot_tag} {display_clock}"
                        q_param = ot_tag
                        mins_rem = max(0.05, clock_secs / 60.0)

                    home_lines = [int(round(float(l.get("value", 0) or 0))) for l in (home.get("linescores") or [])]
                    away_lines = [int(round(float(l.get("value", 0) or 0))) for l in (away.get("linescores") or [])]
                    q_scores = {}
                    for i in range(1, 5):
                        if i <= period and (i - 1 < len(home_lines) or i - 1 < len(away_lines)):
                            h_q = home_lines[i - 1] if i - 1 < len(home_lines) else 0
                            a_q = away_lines[i - 1] if i - 1 < len(away_lines) else 0
                            q_scores[f"{i}Q"] = f"{h_q}-{a_q}"
                        else:
                            q_scores[f"{i}Q"] = "-"
                    if period > 4 and len(home_lines) > 4 and len(away_lines) > 4:
                        for ot_idx in range(4, min(len(home_lines), len(away_lines))):
                            ot_lbl = "OT" if ot_idx == 4 else f"OT{ot_idx - 3}"
                            q_scores[ot_lbl] = f"{home_lines[ot_idx]}-{away_lines[ot_idx]}"

                    h_stand = get_nba_standing_for_team(standings, home_name, home_id)
                    a_stand = get_nba_standing_for_team(standings, away_name, away_id)
                    h2h_data = generate_match_h2h(home_name, away_name, "nba", "NBA", country="Estados Unidos")
                    h_ratings = get_nba_team_ratings(home_name, venue_role="home", standing_info=h_stand)
                    a_ratings = get_nba_team_ratings(away_name, venue_role="away", standing_info=a_stand)

                    home_record = _extract_espn_record_summary(home) or (h_stand or {}).get("overall", "")
                    away_record = _extract_espn_record_summary(away) or (a_stand or {}).get("overall", "")

                    h_st_list = home.get("statistics") or []
                    a_st_list = away.get("statistics") or []
                    fg_h = round(_extract_espn_nba_stat(h_st_list, ["fieldGoalPct"], 45.5), 1)
                    fg_a = round(_extract_espn_nba_stat(a_st_list, ["fieldGoalPct"], 44.5), 1)
                    three_h = round(_extract_espn_nba_stat(h_st_list, ["threePointPct", "threePointFieldGoalPct"], 34.5), 1)
                    three_a = round(_extract_espn_nba_stat(a_st_list, ["threePointPct", "threePointFieldGoalPct"], 33.5), 1)
                    reb_h = int(round(_extract_espn_nba_stat(h_st_list, ["rebounds", "avgRebounds"], 16 + period * 7)))
                    reb_a = int(round(_extract_espn_nba_stat(a_st_list, ["rebounds", "avgRebounds"], 15 + period * 7)))
                    ast_h = int(round(_extract_espn_nba_stat(h_st_list, ["assists", "avgAssists"], 9 + period * 5)))
                    ast_a = int(round(_extract_espn_nba_stat(a_st_list, ["assists", "avgAssists"], 8 + period * 5)))
                    tov_h = int(round(_extract_espn_nba_stat(h_st_list, ["turnovers"], 3 + period * 3)))
                    tov_a = int(round(_extract_espn_nba_stat(a_st_list, ["turnovers"], 3 + period * 3)))

                    live_stats = {
                        "q_scores": q_scores,
                        "is_halftime": is_halftime,
                        "fg_pct_home": fg_h,
                        "fg_pct_away": fg_a,
                        "three_pct_home": three_h,
                        "three_pct_away": three_a,
                        "field_goal_pct_home": fg_h,
                        "field_goal_pct_away": fg_a,
                        "three_point_pct_home": three_h,
                        "three_point_pct_away": three_a,
                        "rebounds_home": reb_h,
                        "rebounds_away": reb_a,
                        "assists_home": ast_h,
                        "assists_away": ast_a,
                        "turnovers_home": tov_h,
                        "turnovers_away": tov_a,
                        "current_run": f"{home_name if score_h >= score_a else away_name} +{abs(score_h - score_a)}"
                    }

                    pred = calculate_nba_live_probabilities(
                        current_h=score_h,
                        current_a=score_a,
                        quarter=q_param,
                        mins_remaining=mins_rem,
                        home_stats=h_ratings,
                        away_stats=a_ratings,
                        live_stats=live_stats
                    )
                    ai_resp = generate_nba_live_ai_analysis({
                        "home_team": home_name,
                        "away_team": away_name,
                        "home_stats": h_ratings,
                        "away_stats": a_ratings,
                        "home_record": home_record,
                        "away_record": away_record
                    }, pred, live_stats)

                    home_logo = home_team_obj.get("logo") or get_team_logo(home_name, "nba")
                    away_logo = away_team_obj.get("logo") or get_team_logo(away_name, "nba")
                    enrich_h2h_with_logos(h2h_data, home_team=home_name, away_team=away_name, home_logo=home_logo, away_logo=away_logo)

                    season_obj = e.get("season", {}) or {}
                    is_playoff = (season_obj.get("type") == 3) or ("playoff" in str(season_obj.get("slug", "")).lower())

                    live_list.append({
                        "id": f"espn_nba_{e.get('id')}",
                        "match_id": str(e.get("id")),
                        "sport": "nba",
                        "league": "NBA",
                        "country": "Estados Unidos",
                        "country_code": "us",
                        "league_flag": "🏀",
                        "country_flag": "🇺🇸",
                        "home_team": home_name,
                        "away_team": away_name,
                        "home_id": home_id,
                        "away_id": away_id,
                        "home_record": home_record,
                        "away_record": away_record,
                        "home_logo": home_logo,
                        "away_logo": away_logo,
                        "quarter": q_label,
                        "display_clock": q_label,
                        "is_halftime": is_halftime,
                        "score_home": score_h,
                        "score_away": score_a,
                        "home_stats": h_ratings,
                        "away_stats": a_ratings,
                        "live_stats": live_stats,
                        "prediction": pred,
                        "season_phase": analyze_season_phase("nba", "NBA", "Playoffs" if is_playoff else "", str(e.get("date", ""))[:10]),
                        "h2h": h2h_data,
                        "ai_analysis": ai_resp,
                        "is_live": True,
                        "is_external": True,
                        "source_api": "ESPN Live"
                    })
            if live_list:
                print(f"[ESPN REAL] Se cargaron {len(live_list)} partidos de la NBA en vivo con estadísticas reales.")
            return live_list
    except Exception as ex:
        print(f"[ESPN] Error al consultar NBA en vivo: {ex}")
    return []


_NHL_STANDINGS_LOCK = threading.Lock()
_nhl_standings_cache = {"data": {}, "timestamp": 0}
_NHL_TEAM_SCHEDULE_LOCK = threading.Lock()
_nhl_team_schedule_cache = {}
_NHL_BOX_CACHE = {}


def fetch_espn_nhl_standings(force: bool = False) -> dict:
    """
    Obtiene estadísticas oficiales de temporada de los 32 equipos NHL desde ESPN Standings
    (pointsFor, pointsAgainst, gamesPlayed, wins, losses, otLosses, points, overall, streak). Caché 1h.
    """
    global _nhl_standings_cache
    now = time.time()
    if not force and _nhl_standings_cache["data"] and (now - _nhl_standings_cache["timestamp"] < 3600):
        return _nhl_standings_cache["data"]

    with _NHL_STANDINGS_LOCK:
        now = time.time()
        if not force and _nhl_standings_cache["data"] and (now - _nhl_standings_cache["timestamp"] < 3600):
            return _nhl_standings_cache["data"]
        try:
            url = "https://site.api.espn.com/apis/v2/sports/hockey/nhl/standings"
            resp = requests.get(url, timeout=7)
            if resp.status_code == 200:
                sd = resp.json()
                mapping = {}
                for ch in sd.get("children", []):
                    entries = ch.get("standings", {}).get("entries", [])
                    for entry in entries:
                        t_obj = entry.get("team", {}) or {}
                        tid = str(t_obj.get("id", "") or "")
                        dname = str(t_obj.get("displayName", "") or "")
                        sname = str(t_obj.get("shortDisplayName", "") or "")
                        abbr = str(t_obj.get("abbreviation", "") or "")
                        logo = t_obj.get("logo") or ((t_obj.get("logos") or [{}])[0].get("href", ""))

                        info = {
                            "team_id": tid,
                            "displayName": dname,
                            "shortDisplayName": sname,
                            "abbreviation": abbr,
                            "logo": logo,
                        }
                        for st in entry.get("stats", []):
                            name = st.get("name")
                            if not name:
                                continue
                            val = st.get("value")
                            disp = st.get("displayValue")
                            if name in ("gamesPlayed", "pointsFor", "pointsAgainst", "differential", "wins", "losses", "otLosses", "points", "regWins"):
                                try:
                                    info[name] = float(val if val is not None else disp)
                                except Exception:
                                    pass
                            elif name in ("overall", "Home", "Road", "Last Ten Games", "streak"):
                                info[name] = disp or (str(val) if val is not None else "")

                        if info.get("overall") and "," in info["overall"]:
                            info["record_short"] = info["overall"].split(",")[0].strip()
                        else:
                            info["record_short"] = info.get("overall", "")

                        if tid:
                            mapping[f"id:{tid}"] = info
                        if dname:
                            mapping[dname.lower()] = info
                        if sname:
                            mapping[sname.lower()] = info
                        if abbr:
                            mapping[f"abbr:{abbr.lower()}"] = info

                if mapping:
                    _nhl_standings_cache["data"] = mapping
                    _nhl_standings_cache["timestamp"] = now
                    return mapping
        except Exception as ex:
            print(f"[ESPN NHL STANDINGS] Error al consultar clasificación NHL: {ex}")
        return _nhl_standings_cache.get("data", {}) or {}


def get_nhl_standing_for_team(standings_map: dict, team_name: str, team_id=None):
    return get_nba_standing_for_team(standings_map, team_name, team_id)


def fetch_espn_nhl_team_schedule(team_id: str, season: int = None) -> list:
    """
    Obtiene partidos finalizados recientes reales desde el calendario oficial de ESPN para un equipo NHL.
    """
    if not team_id:
        return []
    cache_key = f"{team_id}_{season or 'cur'}"
    now = time.time()
    cached = _nhl_team_schedule_cache.get(cache_key)
    if cached and (now - cached.get("timestamp", 0) < 1800):
        return cached.get("events", [])

    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/schedule"
    if season:
        url += f"?season={season}"

    parsed = []
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for e in data.get("events", []):
                comp = (e.get("competitions") or [{}])[0]
                st_type = (comp.get("status") or {}).get("type") or {}
                if not st_type.get("completed"):
                    continue
                comps = comp.get("competitors") or []
                if len(comps) < 2:
                    continue
                h_c = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
                a_c = next((c for c in comps if c.get("homeAway") == "away"), comps[1])

                def _parse_sc(c):
                    sc = c.get("score")
                    if isinstance(sc, dict):
                        val = sc.get("value") if sc.get("value") is not None else sc.get("displayValue", 0)
                        return int(round(float(val or 0)))
                    try:
                        return int(round(float(sc or 0)))
                    except Exception:
                        return 0

                sc_h = _parse_sc(h_c)
                sc_a = _parse_sc(a_c)
                h_team_obj = h_c.get("team", {}) or {}
                a_team_obj = a_c.get("team", {}) or {}
                h_id = str(h_team_obj.get("id", h_c.get("id", "")) or "")
                a_id = str(a_team_obj.get("id", a_c.get("id", "")) or "")
                h_name = h_team_obj.get("displayName") or h_team_obj.get("shortDisplayName", "Local")
                a_name = a_team_obj.get("displayName") or a_team_obj.get("shortDisplayName", "Visitante")

                def _tlogo(t_obj, tname):
                    if t_obj.get("logo"):
                        return t_obj["logo"]
                    logos = t_obj.get("logos") or []
                    if logos and isinstance(logos, list):
                        return logos[0].get("href", "")
                    return get_team_logo(tname, "nhl")

                raw_date = e.get("date", "")
                date_ddmm = raw_date[:10]
                try:
                    dt_utc = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    dt_gt = dt_utc.astimezone(timezone(timedelta(hours=-6)))
                    date_ddmm = dt_gt.strftime("%d/%m")
                except Exception:
                    pass

                sh_det = str(st_type.get("shortDetail", "") or "")
                ot_tag = " (SO)" if "SO" in sh_det else (" (OT)" if "OT" in sh_det else "")

                parsed.append({
                    "id": str(e.get("id", "")),
                    "date": date_ddmm,
                    "raw_date": raw_date,
                    "home_id": h_id,
                    "away_id": a_id,
                    "home_team": h_name,
                    "away_team": a_name,
                    "home_score": sc_h,
                    "away_score": sc_a,
                    "home_logo": _tlogo(h_team_obj, h_name),
                    "away_logo": _tlogo(a_team_obj, a_name),
                    "ot_tag": ot_tag,
                    "winner": h_name if sc_h >= sc_a else a_name
                })
            parsed.sort(key=lambda x: x.get("raw_date", ""), reverse=True)
            with _NHL_TEAM_SCHEDULE_LOCK:
                _nhl_team_schedule_cache[cache_key] = {"events": parsed, "timestamp": now}
    except Exception as ex:
        print(f"[ESPN NHL SCHEDULE] Error consultando equipo {team_id}: {ex}")
        if cached:
            return cached.get("events", [])
    return parsed


def fetch_espn_nhl_team_h2h(home_id: str, away_id: str, home_name: str, away_name: str) -> dict:
    """
    Construye el historial real de últimos 5 partidos y duelos directos (Cara a Cara) NHL desde ESPN.
    """
    fallback = generate_match_h2h(home_name, away_name, "nhl", "NHL", country="Norteamérica")
    if not home_id or not away_id:
        return fallback

    home_sched = fetch_espn_nhl_team_schedule(str(home_id))
    away_sched = fetch_espn_nhl_team_schedule(str(away_id))

    def _to_last5(sched, tid, tname):
        out = []
        tname_l = (tname or "").lower()
        for ev in sched[:5]:
            is_h = (ev["home_id"] == str(tid)) or (ev["home_team"].lower() == tname_l)
            opp = ev["away_team"] if is_h else ev["home_team"]
            my_sc = ev["home_score"] if is_h else ev["away_score"]
            opp_sc = ev["away_score"] if is_h else ev["home_score"]
            out.append({
                "date": ev["date"],
                "opponent": opp,
                "venue": "Local" if is_h else "Visitante",
                "match_home": ev["home_team"],
                "match_away": ev["away_team"],
                "home_score": ev["home_score"],
                "away_score": ev["away_score"],
                "score": f"{ev['home_score']} - {ev['away_score']}{ev.get('ot_tag', '')}",
                "result": "W" if my_sc >= opp_sc else "L",
                "home_logo": ev.get("home_logo", ""),
                "away_logo": ev.get("away_logo", ""),
                "competition": "NHL"
            })
        return out

    home_last_5 = _to_last5(home_sched, home_id, home_name)
    away_last_5 = _to_last5(away_sched, away_id, away_name)

    def _is_direct(ev, tid_a, tid_b):
        ids = {ev.get("home_id"), ev.get("away_id")}
        return str(tid_a) in ids and str(tid_b) in ids

    direct_evs = [ev for ev in home_sched if _is_direct(ev, home_id, away_id)]
    if len(direct_evs) < 3:
        try:
            cur_year = datetime.now().year
            prev_season = cur_year if datetime.now().month >= 10 else cur_year - 1
            prev_sched = fetch_espn_nhl_team_schedule(str(home_id), season=prev_season)
            seen_d = {ev["id"] for ev in direct_evs}
            for ev in prev_sched:
                if ev["id"] not in seen_d and _is_direct(ev, home_id, away_id):
                    direct_evs.append(ev)
                    seen_d.add(ev["id"])
        except Exception:
            pass

    direct_list = []
    for ev in direct_evs[:5]:
        direct_list.append({
            "date": ev["date"],
            "competition": "NHL",
            "tournament": "NHL",
            "match_home": ev["home_team"],
            "match_away": ev["away_team"],
            "home_score": ev["home_score"],
            "away_score": ev["away_score"],
            "score": f"{ev['home_score']} - {ev['away_score']}{ev.get('ot_tag', '')}",
            "winner": ev["winner"],
            "home_team": ev["home_team"],
            "away_team": ev["away_team"],
            "home_logo": ev.get("home_logo", ""),
            "away_logo": ev.get("away_logo", "")
        })

    is_real_recent = bool(home_last_5 and away_last_5)
    final_home_5 = home_last_5 if home_last_5 else fallback["home_last_5"]
    final_away_5 = away_last_5 if away_last_5 else fallback["away_last_5"]
    final_direct = direct_list if direct_list else fallback["head_to_head"]

    w_h = sum(1 for m in final_direct if m["winner"] == home_name or (home_name.lower() in str(m.get("winner", "")).lower()))
    w_a = sum(1 for m in final_direct if m["winner"] == away_name or (away_name.lower() in str(m.get("winner", "")).lower()))
    avg_goals = round(sum(m["home_score"] + m["away_score"] for m in final_direct) / float(len(final_direct) or 1), 1)

    return {
        "home_last_5": final_home_5,
        "away_last_5": final_away_5,
        "head_to_head": final_direct,
        "is_real": bool(is_real_recent or direct_list),
        "is_real_recent": is_real_recent,
        "summary": {
            "home_wins": w_h,
            "draws": 0,
            "away_wins": w_a,
            "avg_goals": avg_goals,
            "text": f"{home_name} {w_h} victorias • {away_name} {w_a} victorias (últimos {len(final_direct)})"
        }
    }


def enrich_nhl_match_with_real_h2h(match: dict) -> dict:
    """
    Enriquece bajo demanda un partido NHL (al abrir su modal /api/match/<id>) con H2H real de ESPN
    y recalibra ratings/predicción con sus últimos 5 partidos oficiales sin frenar la carga inicial.
    """
    if not match or match.get("sport") != "nhl":
        return match
    if (match.get("h2h") or {}).get("is_real"):
        return match

    standings = fetch_espn_nhl_standings()
    home_name = match.get("home_team", "")
    away_name = match.get("away_team", "")
    home_id = match.get("home_id")
    away_id = match.get("away_id")

    h_stand = get_nhl_standing_for_team(standings, home_name, home_id)
    a_stand = get_nhl_standing_for_team(standings, away_name, away_id)
    if not home_id and h_stand:
        home_id = h_stand.get("team_id")
    if not away_id and a_stand:
        away_id = a_stand.get("team_id")

    h2h_data = fetch_espn_nhl_team_h2h(home_id, away_id, home_name, away_name)
    enrich_h2h_with_logos(
        h2h_data,
        home_team=home_name,
        away_team=away_name,
        home_logo=match.get("home_logo", ""),
        away_logo=match.get("away_logo", "")
    )
    match["h2h"] = h2h_data

    if h2h_data.get("is_real_recent") or h_stand or a_stand:
        h_ratings = get_nhl_team_ratings(
            home_name,
            recent_matches=h2h_data.get("home_last_5"),
            venue_role="home",
            standing_info=h_stand,
            real_recent=bool(h2h_data.get("is_real_recent"))
        )
        a_ratings = get_nhl_team_ratings(
            away_name,
            recent_matches=h2h_data.get("away_last_5"),
            venue_role="away",
            standing_info=a_stand,
            real_recent=bool(h2h_data.get("is_real_recent"))
        )
        match["home_stats"] = h_ratings
        match["away_stats"] = a_ratings
        if not match.get("is_live"):
            pred = calculate_nhl_probabilities(h_ratings, a_ratings, home_team=home_name, away_team=away_name)
            match["prediction"] = pred
            if not (match.get("ai_analysis") or {}).get("is_gemini"):
                match["ai_analysis"] = generate_nhl_ai_analysis(match, pred)

    return match


def fetch_espn_nhl_boxscore(event_id: str, home_id: str = "", away_id: str = "") -> dict:
    """
    Obtiene el boxscore oficial en vivo de un partido NHL (shotsTotal SOG, hits, powerPlayPct,
    powerPlayGoals, powerPlayOpportunities, blockedShots, faceoffPercent, penaltyMinutes). Caché 25s.
    """
    if not event_id:
        return {}
    now = time.time()
    cached = _NHL_BOX_CACHE.get(event_id)
    if cached and (now - cached.get("timestamp", 0) < 25):
        return cached.get("data", {})

    out = {}
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={event_id}"
        resp = requests.get(url, timeout=4.5)
        if resp.status_code == 200:
            data = resp.json()
            teams = (data.get("boxscore") or {}).get("teams") or []
            for b in teams:
                tid = str((b.get("team") or {}).get("id", "") or "")
                side = "home" if (home_id and tid == str(home_id)) else ("away" if (away_id and tid == str(away_id)) else None)
                if side is None:
                    ha = b.get("homeAway")
                    side = ha if ha in ("home", "away") else ("away" if not out.get("away") else "home")
                st_map = {}
                for st in (b.get("statistics") or []):
                    nm = st.get("name")
                    if nm:
                        raw = st.get("displayValue") if st.get("displayValue") is not None else st.get("value")
                        try:
                            st_map[nm] = float(str(raw).replace("%", "").strip())
                        except Exception:
                            pass
                out[side] = st_map
            _NHL_BOX_CACHE[event_id] = {"data": out, "timestamp": now}
    except Exception:
        if cached:
            return cached.get("data", {})
    return out


def fetch_espn_live_nhl():
    """
    Obtiene partidos NHL en vivo transmitidos por ESPN Scoreboard + Boxscore en tiempo real
    (SOG, Atajadas SV%, Power Play%, Hits, Faceoffs, reloj por periodo 1P/2P/3P/OT/SO).
    """
    try:
        standings = fetch_espn_nhl_standings()
        events, fetch_ok = _fetch_espn_scoreboard_events("hockey/nhl", day_offsets=(0,), include_default=True, timeout=7)
        if fetch_ok or events:
            live_events = [e for e in events if ((e.get("status") or {}).get("type") or {}).get("state") == "in"]
            if not live_events:
                return []

            # Fetch boxscores en paralelo para velocidad optima
            box_map = {}
            try:
                from concurrent.futures import ThreadPoolExecutor
                def _grab_box(ev):
                    eid = str(ev.get("id", ""))
                    comp = (ev.get("competitions") or [{}])[0]
                    comps = comp.get("competitors") or []
                    hc = next((c for c in comps if c.get("homeAway") == "home"), comps[0] if comps else {})
                    ac = next((c for c in comps if c.get("homeAway") == "away"), comps[1] if len(comps) > 1 else {})
                    hid = str((hc.get("team") or {}).get("id", hc.get("id", "")) or "")
                    aid = str((ac.get("team") or {}).get("id", ac.get("id", "")) or "")
                    return eid, fetch_espn_nhl_boxscore(eid, hid, aid)
                with ThreadPoolExecutor(max_workers=min(6, len(live_events))) as ex:
                    for eid, bdata in ex.map(_grab_box, live_events):
                        box_map[eid] = bdata
            except Exception:
                pass

            live_list = []
            for e in live_events:
                eid = str(e.get("id", ""))
                comp = (e.get("competitions") or [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue
                home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

                home_team_obj = home.get("team", {}) or {}
                away_team_obj = away.get("team", {}) or {}
                home_id = str(home_team_obj.get("id", home.get("id", "")) or "")
                away_id = str(away_team_obj.get("id", away.get("id", "")) or "")
                home_name = home_team_obj.get("displayName", "Local")
                away_name = away_team_obj.get("displayName", "Visitante")
                score_h = int(float(home.get("score", 0) or 0))
                score_a = int(float(away.get("score", 0) or 0))

                status_obj = e.get("status", {}) or {}
                status_type = status_obj.get("type", {}) or {}
                period = int(status_obj.get("period", 1) or 1)
                clock_secs = float(status_obj.get("clock", 0) or 0)
                display_clock = str(status_obj.get("displayClock", "0:00") or "0:00")
                st_name = str(status_type.get("name", "")).upper()
                st_detail = str(status_type.get("shortDetail", "")).upper()
                is_int = ("END" in st_name) or ("END OF" in st_detail)
                is_so = ("SO" in st_detail and period >= 4) or ("SHOOTOUT" in st_detail) or (period >= 5)

                if is_so:
                    q_label = "SO (Penaltis)"
                    q_param = "SO"
                    mins_rem = 0.05
                elif is_int and period <= 3:
                    q_label = f"Fin {period}P"
                    q_param = f"Fin {period}P"
                    mins_rem = max(0.05, (3 - period) * 20.0) if period < 3 else 5.0
                elif period <= 3:
                    q_label = f"{period}P {display_clock}"
                    q_param = f"{period}P"
                    mins_rem = max(0.05, ((3 - period) * 20.0) + (clock_secs / 60.0))
                else:
                    q_label = f"OT {display_clock}"
                    q_param = "OT"
                    mins_rem = max(0.05, clock_secs / 60.0)

                home_lines = [int(round(float(l.get("value", 0) or 0))) for l in (home.get("linescores") or [])]
                away_lines = [int(round(float(l.get("value", 0) or 0))) for l in (away.get("linescores") or [])]
                q_scores = {}
                for i in range(1, 4):
                    if i <= period and (i - 1 < len(home_lines) or i - 1 < len(away_lines)):
                        hq = home_lines[i - 1] if i - 1 < len(home_lines) else 0
                        aq = away_lines[i - 1] if i - 1 < len(away_lines) else 0
                        q_scores[f"{i}P"] = f"{hq}-{aq}"
                    else:
                        q_scores[f"{i}P"] = "-"
                if period >= 4 and len(home_lines) >= 4 and len(away_lines) >= 4:
                    q_scores["OT"] = f"{home_lines[3]}-{away_lines[3]}"

                h_stand = get_nhl_standing_for_team(standings, home_name, home_id)
                a_stand = get_nhl_standing_for_team(standings, away_name, away_id)
                h2h_data = generate_match_h2h(home_name, away_name, "nhl", "NHL", country="Norteamérica")
                h_ratings = get_nhl_team_ratings(home_name, venue_role="home", standing_info=h_stand)
                a_ratings = get_nhl_team_ratings(away_name, venue_role="away", standing_info=a_stand)

                home_record = _extract_espn_record_summary(home) or (h_stand or {}).get("record_short", "")
                away_record = _extract_espn_record_summary(away) or (a_stand or {}).get("record_short", "")

                # Combinar boxscore oficial + saves del scoreboard
                bdata = box_map.get(eid) or fetch_espn_nhl_boxscore(eid, home_id, away_id)
                bh = bdata.get("home") or {}
                ba = bdata.get("away") or {}
                h_st_list = home.get("statistics") or []
                a_st_list = away.get("statistics") or []
                sb_sav_h = int(round(_extract_espn_nba_stat(h_st_list, ["saves"], 0)))
                sb_sav_a = int(round(_extract_espn_nba_stat(a_st_list, ["saves"], 0)))

                sog_h = int(round(bh.get("shotsTotal", sb_sav_a + score_h)))
                sog_a = int(round(ba.get("shotsTotal", sb_sav_h + score_a)))
                saves_h = max(0, sog_a - score_a) if sog_a >= score_a else sb_sav_h
                saves_a = max(0, sog_h - score_h) if sog_h >= score_h else sb_sav_a
                sv_pct_h = round((saves_h / float(sog_a)) * 100.0, 1) if sog_a > 0 else round(_extract_espn_nba_stat(h_st_list, ["savePct"], 90.5), 1)
                sv_pct_a = round((saves_a / float(sog_h)) * 100.0, 1) if sog_h > 0 else round(_extract_espn_nba_stat(a_st_list, ["savePct"], 90.5), 1)
                if sv_pct_h <= 1.0 and sv_pct_h > 0:
                    sv_pct_h = round(sv_pct_h * 100.0, 1)
                if sv_pct_a <= 1.0 and sv_pct_a > 0:
                    sv_pct_a = round(sv_pct_a * 100.0, 1)

                pp_pct_h = round(float(bh.get("powerPlayPct", h_ratings.get("pp_pct", 20.0))), 1)
                pp_pct_a = round(float(ba.get("powerPlayPct", a_ratings.get("pp_pct", 20.0))), 1)

                live_stats = {
                    "q_scores": q_scores,
                    "is_halftime": is_int,
                    "shots_home": sog_h,
                    "shots_away": sog_a,
                    "saves_home": saves_h,
                    "saves_away": saves_a,
                    "save_pct_home": sv_pct_h,
                    "save_pct_away": sv_pct_a,
                    "pp_goals_home": int(round(bh.get("powerPlayGoals", 0))),
                    "pp_goals_away": int(round(ba.get("powerPlayGoals", 0))),
                    "pp_opps_home": int(round(bh.get("powerPlayOpportunities", 0))),
                    "pp_opps_away": int(round(ba.get("powerPlayOpportunities", 0))),
                    "pp_pct_home": pp_pct_h,
                    "pp_pct_away": pp_pct_a,
                    "hits_home": int(round(bh.get("hits", 12))),
                    "hits_away": int(round(ba.get("hits", 12))),
                    "blocked_shots_home": int(round(bh.get("blockedShots", 6))),
                    "blocked_shots_away": int(round(ba.get("blockedShots", 6))),
                    "faceoff_pct_home": round(float(bh.get("faceoffPercent", 50.0)), 1),
                    "faceoff_pct_away": round(float(ba.get("faceoffPercent", 50.0)), 1),
                    "penalty_mins_home": int(round(bh.get("penaltyMinutes", 4))),
                    "penalty_mins_away": int(round(ba.get("penaltyMinutes", 4))),
                }

                pred = calculate_nhl_live_probabilities(
                    current_h=score_h,
                    current_a=score_a,
                    period_str=q_param,
                    mins_remaining=mins_rem,
                    home_stats=h_ratings,
                    away_stats=a_ratings,
                    live_stats=live_stats
                )
                ai_resp = generate_nhl_live_ai_analysis({
                    "home_team": home_name,
                    "away_team": away_name,
                    "home_stats": h_ratings,
                    "away_stats": a_ratings,
                    "home_record": home_record,
                    "away_record": away_record
                }, pred, live_stats)

                home_logo = home_team_obj.get("logo") or get_team_logo(home_name, "nhl")
                away_logo = away_team_obj.get("logo") or get_team_logo(away_name, "nhl")
                enrich_h2h_with_logos(h2h_data, home_team=home_name, away_team=away_name, home_logo=home_logo, away_logo=away_logo)

                season_obj = e.get("season", {}) or {}
                is_playoff = (season_obj.get("type") == 3) or ("playoff" in str(season_obj.get("slug", "")).lower())

                live_list.append({
                    "id": f"espn_nhl_{eid}",
                    "match_id": eid,
                    "sport": "nhl",
                    "league": "NHL",
                    "country": "Norteamérica",
                    "country_code": "",
                    "league_flag": "🏒",
                    "country_flag": "🏒",
                    "home_team": home_name,
                    "away_team": away_name,
                    "home_id": home_id,
                    "away_id": away_id,
                    "home_record": home_record,
                    "away_record": away_record,
                    "home_logo": home_logo,
                    "away_logo": away_logo,
                    "quarter": q_label,
                    "display_clock": q_label,
                    "is_halftime": is_int,
                    "score_home": score_h,
                    "score_away": score_a,
                    "home_stats": h_ratings,
                    "away_stats": a_ratings,
                    "live_stats": live_stats,
                    "prediction": pred,
                    "season_phase": analyze_season_phase("nhl", "NHL", "Playoffs" if is_playoff else "", str(e.get("date", ""))[:10]),
                    "h2h": h2h_data,
                    "ai_analysis": ai_resp,
                    "is_live": True,
                    "is_external": True,
                    "source_api": "ESPN NHL Live"
                })
            if live_list:
                print(f"[ESPN REAL] Se cargaron {len(live_list)} partidos NHL en vivo con boxscore real.")
            return live_list
    except Exception as ex:
        print(f"[ESPN] Error al consultar NHL en vivo: {ex}")
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

                                espn_lid = ""
                                uid = e.get("uid", "")
                                if "~l:" in uid:
                                    try:
                                        espn_lid = uid.split("~l:")[1].split("~")[0]
                                    except Exception:
                                        pass

                                raw_slug = e.get("season", {}).get("slug", "") or comp_info.get("league", {}).get("description", "Oficial")
                                l_clean, c_name, c_flag = get_league_and_country_info(raw_slug, "football", h_name, a_name, espn_league_id=espn_lid)

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

_live_cache = {"data": {}, "timestamp": 0, "updating": False, "updating_start": 0}
_LIVE_FETCH_LOCK = threading.Lock()
_LIVE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "live_cache_persist.json")

def _load_persisted_live_cache():
    global _live_cache
    if os.path.exists(_LIVE_CACHE_FILE):
        try:
            with open(_LIVE_CACHE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and saved.get("schema_v") == 3:
                    saved_ts = saved.get("timestamp", 0)
                    if (time.time() - saved_ts) < 300:
                        if "matches" in saved:
                            all_list = saved["matches"]
                            _live_cache["data"]["all"] = all_list
                            _live_cache["data"]["football"] = [m for m in all_list if m.get("sport") == "football"]
                            _live_cache["data"]["nba"] = [m for m in all_list if m.get("sport") == "nba"]
                            _live_cache["data"]["nhl"] = [m for m in all_list if m.get("sport") == "nhl"]
                        elif "data" in saved:
                            for k, v in saved.get("data", {}).items():
                                _live_cache["data"][k] = v
                        _live_cache["timestamp"] = saved_ts
                    else:
                        _live_cache["data"] = {}
                        _live_cache["timestamp"] = 0
                else:
                    _live_cache["data"] = {}
                    _live_cache["timestamp"] = 0
        except Exception:
            pass

def _save_persisted_live_cache():
    try:
        os.makedirs(os.path.dirname(_LIVE_CACHE_FILE), exist_ok=True)
        all_list = _live_cache.get("data", {}).get("all")
        if all_list is None:
            all_list = (
                (_live_cache.get("data", {}).get("football", []) or [])
                + (_live_cache.get("data", {}).get("nba", []) or [])
                + (_live_cache.get("data", {}).get("nhl", []) or [])
            )
        with open(_LIVE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "schema_v": 3,
                "matches": all_list,
                "timestamp": _live_cache.get("timestamp", 0)
            }, f, ensure_ascii=False)
    except Exception:
        pass

# Cargar cache persistente de disco de inmediato si existe
_load_persisted_live_cache()

def _refresh_live_cache_worker(sport_filter="all"):
    """
    Actualiza la cache de partidos en vivo con lock seguro y sincronizacion multi-deporte.
    """
    global _live_cache
    now = time.time()

    # Auto-desbloqueo: si lleva mas de 15s en 'updating', considerar hilo muerto
    if _live_cache.get("updating"):
        if (now - _live_cache.get("updating_start", 0)) < 15:
            return

    with _LIVE_FETCH_LOCK:
        now = time.time()
        _live_cache["updating"] = True
        _live_cache["updating_start"] = now
        try:
            live_results = []
            if sport_filter in ("all", "football"):
                live_results.extend(fetch_espn_live_soccer() or [])
            if sport_filter in ("all", "nba"):
                live_results.extend(fetch_espn_live_nba() or [])
            if sport_filter in ("all", "nhl"):
                live_results.extend(fetch_espn_live_nhl() or [])

            now = time.time()
            _live_cache["data"][sport_filter] = live_results

            # Sincronizar sub-filtros si se consulto all
            if sport_filter == "all":
                _live_cache["data"]["football"] = [m for m in live_results if m.get("sport") == "football"]
                _live_cache["data"]["nba"] = [m for m in live_results if m.get("sport") == "nba"]
                _live_cache["data"]["nhl"] = [m for m in live_results if m.get("sport") == "nhl"]

            _live_cache["timestamp"] = now
            _save_persisted_live_cache()
        except Exception as ex:
            print(f"[LIVE CACHE REFRESH ERROR]: {ex}")
        finally:
            _live_cache["updating"] = False

def fetch_live_matches_data(sport_filter="all", force_refresh=False):
    """
    Obtiene los partidos en vivo oficiales reales (ESPN Futbol & NBA).
    - Si force_refresh=True: actualiza sincrónicamente para entrega inmediata.
    - Si cache fresca (<35s): respuesta inmediata ultra-rapida.
    - Si arranque en frio mientras otro hilo actualiza: espera brevemente para evitar listas vacias / 404.
    """
    global _live_cache
    now = time.time()
    cfg = get_config()
    is_live_api = bool(cfg and getattr(cfg, "USE_LIVE_API", False))

    if is_live_api:
        # Auto-desbloqueo preventivo
        if _live_cache.get("updating") and (now - _live_cache.get("updating_start", 0) > 15):
            _live_cache["updating"] = False

        if force_refresh:
            # Si hay otro worker en curso, esperar brevemente antes o refrescar directamente
            deadline = time.time() + 8.0
            while _live_cache.get("updating") and time.time() < deadline:
                time.sleep(0.12)
            _refresh_live_cache_worker(sport_filter)
            return _live_cache.get("data", {}).get(sport_filter, [])

        cache_age = now - _live_cache.get("timestamp", 0)

        # 1. Si ya tenemos datos en memoria (Stale-While-Revalidate):
        if sport_filter in _live_cache.get("data", {}) and _live_cache["data"][sport_filter] is not None:
            if cache_age >= 35 and not _live_cache.get("updating"):
                threading.Thread(target=_refresh_live_cache_worker, args=(sport_filter,), daemon=True).start()
            return _live_cache["data"][sport_filter]

        # 2. Si memoria esta vacia, cargar cache persistida en disco
        _load_persisted_live_cache()
        if sport_filter in _live_cache.get("data", {}) and _live_cache["data"][sport_filter] is not None:
            if not _live_cache.get("updating"):
                threading.Thread(target=_refresh_live_cache_worker, args=(sport_filter,), daemon=True).start()
            return _live_cache["data"][sport_filter]

        # 3. Si otro hilo ya está actualizando en arranque en frío, esperar hasta que pueble
        if _live_cache.get("updating"):
            deadline = time.time() + 8.0
            while _live_cache.get("updating") and time.time() < deadline:
                if sport_filter in _live_cache.get("data", {}) and _live_cache["data"][sport_filter] is not None:
                    return _live_cache["data"][sport_filter]
                time.sleep(0.12)

        # 4. Arranque en frio absoluto sin cache previa: sincronizar
        _refresh_live_cache_worker(sport_filter)
        return _live_cache.get("data", {}).get(sport_filter, [])

    # Catalogo simulado (SOLO cuando USE_LIVE_API = False):
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
            h_logo = get_team_logo(item["home_team"], "football")
            a_logo = get_team_logo(item["away_team"], "football")
            enrich_h2h_with_logos(h2h_data, home_team=item["home_team"], away_team=item["away_team"], home_logo=h_logo, away_logo=a_logo)
            c_code_map = {"Brasil": "br", "España": "es", "Inglaterra": "gb-eng", "Italia": "it", "Alemania": "de", "Francia": "fr", "Estados Unidos": "us", "México": "mx", "Argentina": "ar", "Colombia": "co"}
            c_code = c_code_map.get(c_name, "")
            results.append({
                "id": item["id"],
                "sport": "football",
                "league": l_clean,
                "country": c_name,
                "country_code": c_code,
                "league_flag": c_flag,
                "country_flag": c_flag,
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "home_logo": h_logo,
                "away_logo": a_logo,
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
            h_logo = get_team_logo(item["home_team"], "nba")
            a_logo = get_team_logo(item["away_team"], "nba")
            enrich_h2h_with_logos(h2h_data, home_team=item["home_team"], away_team=item["away_team"], home_logo=h_logo, away_logo=a_logo)
            results.append({
                "id": item["id"],
                "sport": "nba",
                "league": "NBA",
                "country": "Estados Unidos",
                "country_code": "us",
                "league_flag": "🏀",
                "country_flag": "🇺🇸",
                "home_team": item["home_team"],
                "away_team": item["away_team"],
                "home_logo": h_logo,
                "away_logo": a_logo,
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

_last_auto_scrape_check = 0

def check_and_auto_update_scraped_matches(max_age_hours=6):
    """
    Verifica si los datos oficiales escrapeados tienen más de `max_age_hours` horas.
    Si están desactualizados o faltan, lanza los scrapers en un hilo en segundo plano,
    sin bloquear la carga de la página ni la experiencia del usuario.
    """
    # En la nube (Render con 512MB RAM), el scraping lo realiza GitHub Actions de forma aislada.
    # Evitamos ejecutar scrapers pesados en el proceso web para no exceder la memoria.
    if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_URL"):
        return

    global _last_auto_scrape_check
    import time
    now = time.time()
    if now - _last_auto_scrape_check < 300:  # Como máximo revisar cada 5 min
        return
    _last_auto_scrape_check = now

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    try:
        from scraper_engine import SUPPORTED_LEAGUES, scrape_single_league, load_match_cache, save_match_cache
        missing_leagues = []
        for l in SUPPORTED_LEAGUES:
            fpath = os.path.join(data_dir, f"{l['slug']}_real.json")
            if not os.path.exists(fpath):
                missing_leagues.append(l)
            else:
                try:
                    age_h = (now - os.path.getmtime(fpath)) / 3600.0
                    if age_h > max_age_hours:
                        missing_leagues.append(l)
                except Exception:
                    pass

        if missing_leagues:
            import threading
            def run_bg():
                cache = load_match_cache()
                for lg in missing_leagues:
                    try:
                        scrape_single_league(lg, cache)
                        save_match_cache(cache)
                        invalidate_scraped_matches_cache()
                    except Exception as err:
                        print(f"[AUTO-SCRAPER] Error en {lg['name']}: {err}")
            threading.Thread(target=run_bg, daemon=True).start()
            print(f"[AUTO-SCRAPER] Actualización en segundo plano iniciada para {len(missing_leagues)} ligas")
    except Exception as e:
        print(f"[AUTO-SCRAPER] Error comprobando ligas: {e}")

_SCRAPED_MATCHES_CACHE = None
_SCRAPED_MATCHES_CACHE_TIME = 0

def invalidate_scraped_matches_cache():
    global _SCRAPED_MATCHES_CACHE, _SCRAPED_MATCHES_CACHE_TIME
    _SCRAPED_MATCHES_CACHE = None
    _SCRAPED_MATCHES_CACHE_TIME = 0

def load_scraped_matches(force_reload=False):
    """
    Carga partidos oficiales reales obtenidos por web scraping especializado de FotMob
    (Brasileirão Série A, Liga BetPlay Dimayor y otras ligas clave).
    Prioriza estos partidos con estadísticas 100% verificadas, H2H oficial y córners reales.
    Usa caché en memoria de 60 segundos para respuestas instantáneas.
    """
    global _SCRAPED_MATCHES_CACHE, _SCRAPED_MATCHES_CACHE_TIME
    now = time.time()
    if not force_reload and _SCRAPED_MATCHES_CACHE is not None and (now - _SCRAPED_MATCHES_CACHE_TIME < 1800):
        return _SCRAPED_MATCHES_CACHE

    check_and_auto_update_scraped_matches(max_age_hours=6)

    scraped_list = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        return scraped_list

    for fname in os.listdir(data_dir):
        if fname.endswith("_real.json"):
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                upcoming = payload.get("upcoming_matches", [])
                for item in upcoming:
                    h_name = item.get("home_team")
                    a_name = item.get("away_team")
                    h2h_data = item.get("h2h", {})
                    league = item.get("league", "Brasileirão Série A")
                    country = item.get("country", "Brasil")
                    if not h2h_data.get("head_to_head"):
                        sim = generate_match_h2h(h_name, a_name, "football", league, country=country)
                        if sim and sim.get("head_to_head"):
                            h2h_data["head_to_head"] = sim["head_to_head"]
                        if not h2h_data.get("home_last_5") and sim.get("home_last_5"):
                            h2h_data["home_last_5"] = sim["home_last_5"]
                        if not h2h_data.get("away_last_5") and sim.get("away_last_5"):
                            h2h_data["away_last_5"] = sim["away_last_5"]

                    dir_matches = h2h_data.get("head_to_head", [])
                    if "summary" not in h2h_data or h2h_data["summary"].get("home_wins", 0) + h2h_data["summary"].get("draws", 0) + h2h_data["summary"].get("away_wins", 0) == 0:
                        w_h = sum(1 for m in dir_matches if m.get("winner") == h_name or (h_name.lower() in (m.get("winner") or "").lower()))
                        w_d = sum(1 for m in dir_matches if m.get("winner") == "Empate")
                        w_a = sum(1 for m in dir_matches if m.get("winner") == a_name or (a_name.lower() in (m.get("winner") or "").lower()))
                        total_g = sum(m.get("home_score", 0) + m.get("away_score", 0) for m in dir_matches)
                        count_dir = len(dir_matches) or 1
                        h2h_data["summary"] = {
                            "home_wins": w_h,
                            "draws": w_d,
                            "away_wins": w_a,
                            "avg_goals": round(total_g / float(count_dir), 1),
                            "text": f"{h_name} {w_h} victorias • {w_d} empates • {a_name} {w_a} victorias"
                        }

                    ref_info = item.get("referee")
                    home_stats = get_football_team_ratings(h_name, league, recent_matches=h2h_data.get("home_last_5"), venue_role="home")
                    away_stats = get_football_team_ratings(a_name, league, recent_matches=h2h_data.get("away_last_5"), venue_role="away")
                    pred = calculate_match_probabilities(home_stats, away_stats, home_team=h_name, away_team=a_name, referee=ref_info)
                    analysis = generate_ai_analysis(item, pred)

                    c_code = item.get("country_code") or ""
                    l_flag = item.get("league_flag") or "⚽"
                    c_flag = item.get("country_flag") or "⚽"
                    h_logo = item.get("home_logo") or get_team_logo(h_name, "football", item.get("home_id"))
                    a_logo = item.get("away_logo") or get_team_logo(a_name, "football", item.get("away_id"))
                    enrich_h2h_with_logos(h2h_data, home_team=h_name, away_team=a_name, home_logo=h_logo, away_logo=a_logo)
                    scraped_list.append({
                        "id": item.get("id"),
                        "match_id": item.get("match_id"),
                        "sport": "football",
                        "league": league,
                        "country": country,
                        "country_code": c_code,
                        "league_flag": l_flag,
                        "country_flag": c_flag,
                        "home_team": h_name,
                        "away_team": a_name,
                        "home_logo": h_logo,
                        "away_logo": a_logo,
                        "home_id": item.get("home_id"),
                        "away_id": item.get("away_id"),
                        "date": item.get("date"),
                        "date_iso": item.get("date_iso"),
                        "time": item.get("time"),
                        "timestamp": item.get("timestamp") or 0,
                        "timezone": item.get("timezone", "America/Guatemala"),
                        "round": item.get("round", ""),
                        "season_phase": analyze_season_phase(fname.replace("_real.json", ""), league, item.get("round", ""), item.get("date_iso", "")),
                        "home_stats": home_stats,
                        "away_stats": away_stats,
                        "prediction": pred,
                        "h2h": h2h_data,
                        "ai_analysis": analysis,
                        "referee": ref_info,
                        "is_live": False,
                        "is_external": True,
                        "source_api": "FotMob (Scraping Oficial)"
                    })
            except Exception as e:
                print(f"[SCRAPING DATA] Error procesando archivo {fname}: {e}")

    # Ordenar cronológicamente por hora/timestamp de Guatemala (los más próximos primero)
    scraped_list.sort(key=lambda m: (m.get("timestamp") or 0, m.get("date_iso") or "", m.get("time") or ""))
    _SCRAPED_MATCHES_CACHE = scraped_list
    _SCRAPED_MATCHES_CACHE_TIME = time.time()
    return scraped_list

_ESPN_UPCOMING_NBA_CACHE = {"data": None, "timestamp": 0}
_ESPN_UPCOMING_NBA_LOCK = threading.Lock()

def _parse_espn_nba_datetime(iso_str):
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(clean)
        gt_tz = timezone(timedelta(hours=-6))
        dt_gt = dt_utc.astimezone(gt_tz)
        days_es = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        day_name = days_es[dt_gt.weekday()]
        month_name = months_es[dt_gt.month - 1]
        date_formatted = f"{day_name} {dt_gt.day} {month_name}, {dt_gt.hour:02d}:{dt_gt.minute:02d}"
        date_iso = dt_gt.strftime("%Y-%m-%d")
        time_str = f"{dt_gt.hour:02d}:{dt_gt.minute:02d}"
        timestamp = int(dt_utc.timestamp())
        return date_formatted, date_iso, time_str, timestamp
    except Exception:
        now_dt = datetime.now()
        return "Hoy", now_dt.strftime("%Y-%m-%d"), "19:00", int(now_dt.timestamp())

def fetch_espn_upcoming_nba(force: bool = False):
    """
    Obtiene los partidos programados oficiales de la NBA directamente desde ESPN Scoreboard.
    Usa ESPN Standings reales para calibrar Offensive/Defensive Ratings y records oficiales.
    """
    global _ESPN_UPCOMING_NBA_CACHE
    now = time.time()
    if not force and _ESPN_UPCOMING_NBA_CACHE["data"] and (now - _ESPN_UPCOMING_NBA_CACHE["timestamp"] < 900):
        return _ESPN_UPCOMING_NBA_CACHE["data"]

    with _ESPN_UPCOMING_NBA_LOCK:
        now = time.time()
        if not force and _ESPN_UPCOMING_NBA_CACHE["data"] and (now - _ESPN_UPCOMING_NBA_CACHE["timestamp"] < 900):
            return _ESPN_UPCOMING_NBA_CACHE["data"]

        standings = fetch_espn_nba_standings()
        events = []
        fetch_ok = False
        try:
            events, fetch_ok = _fetch_espn_scoreboard_events("basketball/nba", day_offsets=(0, 1, 2), include_default=True, timeout=8)
        except Exception as ex:
            print(f"[ESPN NBA] Error al consultar scoreboard: {ex}")
            if not events and _ESPN_UPCOMING_NBA_CACHE["data"]:
                return _ESPN_UPCOMING_NBA_CACHE["data"]

        if not fetch_ok and not events and _ESPN_UPCOMING_NBA_CACHE["data"]:
            return _ESPN_UPCOMING_NBA_CACHE["data"]

        seen_ids = set()
        upcoming_list = []

        for e in events:
            eid = e.get("id")
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)

            state = e.get("status", {}).get("type", {}).get("state")
            if state != "pre":
                continue

            comp = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            home_team_data = home.get("team", {})
            away_team_data = away.get("team", {})
            home_id = str(home_team_data.get("id", home.get("id", "")) or "")
            away_id = str(away_team_data.get("id", away.get("id", "")) or "")
            home_name = home_team_data.get("displayName", "Local")
            away_name = away_team_data.get("displayName", "Visitante")

            home_logo = home_team_data.get("logo") or get_team_logo(home_name, "nba")
            away_logo = away_team_data.get("logo") or get_team_logo(away_name, "nba")

            raw_date = e.get("date", "")
            date_formatted, date_iso, time_str, timestamp = _parse_espn_nba_datetime(raw_date)

            h_stand = get_nba_standing_for_team(standings, home_name, home_id)
            a_stand = get_nba_standing_for_team(standings, away_name, away_id)
            home_record = _extract_espn_record_summary(home) or (h_stand or {}).get("overall", "")
            away_record = _extract_espn_record_summary(away) or (a_stand or {}).get("overall", "")

            h2h_data = generate_match_h2h(home_name, away_name, "nba", "NBA", country="Estados Unidos")
            h_ratings = get_nba_team_ratings(home_name, venue_role="home", standing_info=h_stand)
            a_ratings = get_nba_team_ratings(away_name, venue_role="away", standing_info=a_stand)
            pred = calculate_nba_probabilities(h_ratings, a_ratings, home_team=home_name, away_team=away_name)
            ai_resp = generate_nba_ai_analysis({
                "home_team": home_name,
                "away_team": away_name,
                "home_stats": h_ratings,
                "away_stats": a_ratings,
                "home_record": home_record,
                "away_record": away_record
            }, pred)
            enrich_h2h_with_logos(h2h_data, home_team=home_name, away_team=away_name, home_logo=home_logo, away_logo=away_logo)

            season_obj = e.get("season", {}) or {}
            is_playoff = (season_obj.get("type") == 3) or ("playoff" in str(season_obj.get("slug", "")).lower())

            upcoming_list.append({
                "id": f"espn_nba_{eid}",
                "match_id": str(eid),
                "sport": "nba",
                "league": "NBA",
                "country": "Estados Unidos",
                "country_code": "us",
                "league_flag": "🏀",
                "country_flag": "🇺🇸",
                "home_team": home_name,
                "away_team": away_name,
                "home_logo": home_logo,
                "away_logo": away_logo,
                "home_id": home_id,
                "away_id": away_id,
                "home_record": home_record,
                "away_record": away_record,
                "date": date_formatted,
                "date_iso": date_iso,
                "time": time_str,
                "timestamp": timestamp,
                "timezone": "America/Guatemala",
                "home_stats": h_ratings,
                "away_stats": a_ratings,
                "prediction": pred,
                "season_phase": analyze_season_phase("nba", "NBA", "Playoffs" if is_playoff else "", date_iso),
                "h2h": h2h_data,
                "ai_analysis": ai_resp,
                "referee": None,
                "is_live": False,
                "is_external": True,
                "source_api": "ESPN NBA (Oficial)"
            })

        upcoming_list.sort(key=lambda m: (m.get("timestamp") or 0, m.get("date_iso") or "", m.get("time") or ""))
        _ESPN_UPCOMING_NBA_CACHE["data"] = upcoming_list
        _ESPN_UPCOMING_NBA_CACHE["timestamp"] = time.time()
        if upcoming_list:
            print(f"[ESPN NBA] Se sincronizaron {len(upcoming_list)} partidos oficiales programados de la NBA.")
        return upcoming_list


_ESPN_UPCOMING_NHL_CACHE = {"data": None, "timestamp": 0}
_ESPN_UPCOMING_NHL_LOCK = threading.Lock()


def fetch_espn_upcoming_nhl(force: bool = False):
    """
    Obtiene los partidos programados oficiales de la NHL directamente desde ESPN Scoreboard.
    Usa ESPN NHL Standings reales para calibrar GF/GA, SOG, Power Play% y records W-L-OTL.
    """
    global _ESPN_UPCOMING_NHL_CACHE
    now = time.time()
    if not force and _ESPN_UPCOMING_NHL_CACHE["data"] and (now - _ESPN_UPCOMING_NHL_CACHE["timestamp"] < 900):
        return _ESPN_UPCOMING_NHL_CACHE["data"]

    with _ESPN_UPCOMING_NHL_LOCK:
        now = time.time()
        if not force and _ESPN_UPCOMING_NHL_CACHE["data"] and (now - _ESPN_UPCOMING_NHL_CACHE["timestamp"] < 900):
            return _ESPN_UPCOMING_NHL_CACHE["data"]

        standings = fetch_espn_nhl_standings()
        events = []
        fetch_ok = False
        try:
            events, fetch_ok = _fetch_espn_scoreboard_events("hockey/nhl", day_offsets=(0, 1, 2), include_default=True, timeout=8)
        except Exception as ex:
            print(f"[ESPN NHL] Error al consultar scoreboard: {ex}")
            if not events and _ESPN_UPCOMING_NHL_CACHE["data"]:
                return _ESPN_UPCOMING_NHL_CACHE["data"]

        if not fetch_ok and not events and _ESPN_UPCOMING_NHL_CACHE["data"]:
            return _ESPN_UPCOMING_NHL_CACHE["data"]

        seen_ids = set()
        upcoming_list = []

        for e in events:
            eid = e.get("id")
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)

            state = e.get("status", {}).get("type", {}).get("state")
            if state != "pre":
                continue

            comp = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            home_team_data = home.get("team", {})
            away_team_data = away.get("team", {})
            home_id = str(home_team_data.get("id", home.get("id", "")) or "")
            away_id = str(away_team_data.get("id", away.get("id", "")) or "")
            home_name = home_team_data.get("displayName", "Local")
            away_name = away_team_data.get("displayName", "Visitante")

            home_logo = home_team_data.get("logo") or get_team_logo(home_name, "nhl")
            away_logo = away_team_data.get("logo") or get_team_logo(away_name, "nhl")

            raw_date = e.get("date", "")
            date_formatted, date_iso, time_str, timestamp = _parse_espn_nba_datetime(raw_date)

            h_stand = get_nhl_standing_for_team(standings, home_name, home_id)
            a_stand = get_nhl_standing_for_team(standings, away_name, away_id)
            home_record = _extract_espn_record_summary(home) or (h_stand or {}).get("record_short", "")
            away_record = _extract_espn_record_summary(away) or (a_stand or {}).get("record_short", "")

            h2h_data = generate_match_h2h(home_name, away_name, "nhl", "NHL", country="Norteamérica")
            h_ratings = get_nhl_team_ratings(home_name, venue_role="home", standing_info=h_stand)
            a_ratings = get_nhl_team_ratings(away_name, venue_role="away", standing_info=a_stand)
            pred = calculate_nhl_probabilities(h_ratings, a_ratings, home_team=home_name, away_team=away_name)
            ai_resp = generate_nhl_ai_analysis({
                "home_team": home_name,
                "away_team": away_name,
                "home_stats": h_ratings,
                "away_stats": a_ratings,
                "home_record": home_record,
                "away_record": away_record
            }, pred)
            enrich_h2h_with_logos(h2h_data, home_team=home_name, away_team=away_name, home_logo=home_logo, away_logo=away_logo)

            season_obj = e.get("season", {}) or {}
            is_playoff = (season_obj.get("type") == 3) or ("playoff" in str(season_obj.get("slug", "")).lower())

            upcoming_list.append({
                "id": f"espn_nhl_{eid}",
                "match_id": str(eid),
                "sport": "nhl",
                "league": "NHL",
                "country": "Norteamérica",
                "country_code": "",
                "league_flag": "🏒",
                "country_flag": "🏒",
                "home_team": home_name,
                "away_team": away_name,
                "home_logo": home_logo,
                "away_logo": away_logo,
                "home_id": home_id,
                "away_id": away_id,
                "home_record": home_record,
                "away_record": away_record,
                "date": date_formatted,
                "date_iso": date_iso,
                "time": time_str,
                "timestamp": timestamp,
                "timezone": "America/Guatemala",
                "home_stats": h_ratings,
                "away_stats": a_ratings,
                "prediction": pred,
                "season_phase": analyze_season_phase("nhl", "NHL", "Playoffs" if is_playoff else "", date_iso),
                "h2h": h2h_data,
                "ai_analysis": ai_resp,
                "referee": None,
                "is_live": False,
                "is_external": True,
                "source_api": "ESPN NHL (Oficial)"
            })

        upcoming_list.sort(key=lambda m: (m.get("timestamp") or 0, m.get("date_iso") or "", m.get("time") or ""))
        _ESPN_UPCOMING_NHL_CACHE["data"] = upcoming_list
        _ESPN_UPCOMING_NHL_CACHE["timestamp"] = time.time()
        if upcoming_list:
            print(f"[ESPN NHL] Se sincronizaron {len(upcoming_list)} partidos oficiales programados de la NHL.")
        return upcoming_list


def fetch_matches_data(sport_filter="all"):
    """
    Obtiene los partidos programados (pre-match).
    - Fútbol: Partidos analizados mediante extracción oficial de FotMob con estadísticas 100% reales.
    - NBA: Partidos oficiales programados vía ESPN Oficial Scoreboard + Standings.
    - NHL: Partidos oficiales programados vía ESPN NHL Scoreboard + Standings.
    """
    results = []

    # 1. Fútbol oficial escrapeado de FotMob
    if sport_filter in ("all", "football"):
        results.extend(load_scraped_matches())

    # 2. NBA oficial vía ESPN Scoreboard
    if sport_filter in ("all", "nba"):
        results.extend(fetch_espn_upcoming_nba())

    # 3. NHL oficial vía ESPN Scoreboard
    if sport_filter in ("all", "nhl"):
        results.extend(fetch_espn_upcoming_nhl())

    # Ordenar cronológicamente si hay partidos combinados
    if sport_filter == "all":
        results.sort(key=lambda m: (m.get("timestamp") or 0, m.get("date_iso") or "", m.get("time") or ""))

    return results


def get_match_by_id(match_id):
    """
    Búsqueda ultra-rápida en memoria O(1) para detalles de partido,
    con fallback inteligente si un partido NBA/NHL cambió entre programado y en vivo.
    """
    if not match_id:
        return None
    str_id = str(match_id).strip()

    # 1. En caché de partidos en vivo
    for sp in list(_live_cache.get("data", {}).keys()):
        for m in (_live_cache["data"].get(sp) or []):
            if m.get("id") == str_id or str(m.get("match_id")) == str_id:
                return m

    # 2. En caché de partidos escrapeados
    if _SCRAPED_MATCHES_CACHE is not None:
        for m in _SCRAPED_MATCHES_CACHE:
            if m.get("id") == str_id or str(m.get("match_id")) == str_id:
                return m

    # 3. En caché de NBA / NHL
    if _ESPN_UPCOMING_NBA_CACHE.get("data"):
        for m in _ESPN_UPCOMING_NBA_CACHE["data"]:
            if m.get("id") == str_id or str(m.get("match_id")) == str_id:
                return m

    if _ESPN_UPCOMING_NHL_CACHE.get("data"):
        for m in _ESPN_UPCOMING_NHL_CACHE["data"]:
            if m.get("id") == str_id or str(m.get("match_id")) == str_id:
                return m

    # 4. Fallback si la caché estaba vacía o en transición live <-> pre
    if str_id.startswith("espn_nba_"):
        live_nba = fetch_live_matches_data("nba", force_refresh=True) or []
        found = next((m for m in live_nba if m.get("id") == str_id or str(m.get("match_id")) == str_id), None)
        if found:
            return found
        up_nba = fetch_espn_upcoming_nba(force=True) or []
        found = next((m for m in up_nba if m.get("id") == str_id or str(m.get("match_id")) == str_id), None)
        if found:
            return found

    if str_id.startswith("espn_nhl_"):
        live_nhl = fetch_live_matches_data("nhl", force_refresh=True) or []
        found = next((m for m in live_nhl if m.get("id") == str_id or str(m.get("match_id")) == str_id), None)
        if found:
            return found
        up_nhl = fetch_espn_upcoming_nhl(force=True) or []
        found = next((m for m in up_nhl if m.get("id") == str_id or str(m.get("match_id")) == str_id), None)
        if found:
            return found

    all_m = (fetch_live_matches_data() or []) + (fetch_matches_data() or [])
    return next((m for m in all_m if m.get("id") == str_id or str(m.get("match_id")) == str_id), None)


def get_match_referee(match_id):
    """
    Obtiene la información oficial del árbitro en tiempo real o caché para un partido específico.
    """
    if not match_id:
        return None
    try:
        from scraper_engine import fetch_referee_from_fotmob
        return fetch_referee_from_fotmob(match_id)
    except Exception as e:
        print(f"[REFEREE ERROR]: {e}")
        return None

