import os
import json
import time
import unicodedata
import requests
import scraper_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "team_logos.json")

logos = {}
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
            logos = old.get("logos", {})
    except Exception:
        pass

def norm_text(t):
    if not t:
        return ""
    return unicodedata.normalize("NFKD", str(t)).encode("ASCII", "ignore").decode("utf-8").lower().strip()

def fetch_league_teams(league_cfg):
    l_id = league_cfg.get("id")
    url = f"https://www.fotmob.com/api/data/leagues?id={l_id}&ccode3=GTM"
    try:
        r = requests.get(url, headers=scraper_engine.HEADERS, timeout=15)
        if r.status_code == 200:
            d = r.json()
            for m in d.get("fixtures", {}).get("allMatches", []):
                h = m.get("home")
                a = m.get("away")
                if h and h.get("name") and h.get("id"):
                    logos[h["name"]] = f"https://images.fotmob.com/image_resources/logo/teamlogo/{h['id']}.png"
                if a and a.get("name") and a.get("id"):
                    logos[a["name"]] = f"https://images.fotmob.com/image_resources/logo/teamlogo/{a['id']}.png"
            for tbl in d.get("table", []):
                for row in tbl.get("data", {}).get("table", {}).get("all", []):
                    if row.get("name") and row.get("id"):
                        logos[row["name"]] = f"https://images.fotmob.com/image_resources/logo/teamlogo/{row['id']}.png"
            print(f"[OK] Liga {league_cfg.get('name')} procesada ({len(logos)} acumulados)")
        else:
            print(f"[ERR] Liga {league_cfg.get('name')} status {r.status_code}")
    except Exception as e:
        print(f"[ERR] Error en liga {league_cfg.get('name')}: {e}")

def main():
    print(f"Iniciando con {len(logos)} equipos previos...")
    for idx, l in enumerate(scraper_engine.SUPPORTED_LEAGUES):
        fetch_league_teams(l)
        time.sleep(0.5)

    # 2. NBA Teams (30 franquicias)
    nba_teams = {
        "Atlanta Hawks": "atl", "Boston Celtics": "bos", "Brooklyn Nets": "bkn", "Charlotte Hornets": "cha",
        "Chicago Bulls": "chi", "Cleveland Cavaliers": "cle", "Dallas Mavericks": "dal", "Denver Nuggets": "den",
        "Detroit Pistons": "det", "Golden State Warriors": "gs", "Houston Rockets": "hou", "Indiana Pacers": "ind",
        "LA Clippers": "lac", "Los Angeles Clippers": "lac", "Los Angeles Lakers": "lal", "Memphis Grizzlies": "mem",
        "Miami Heat": "mia", "Milwaukee Bucks": "mil", "Minnesota Timberwolves": "min", "New Orleans Pelicans": "no",
        "New York Knicks": "ny", "Oklahoma City Thunder": "okc", "Orlando Magic": "orl", "Philadelphia 76ers": "phi",
        "Phoenix Suns": "phx", "Portland Trail Blazers": "por", "Sacramento Kings": "sac", "San Antonio Spurs": "sa",
        "Toronto Raptors": "tor", "Utah Jazz": "uta", "Washington Wizards": "wsh"
    }
    for name, code in nba_teams.items():
        logos[name] = f"https://a.espncdn.com/i/teamlogos/nba/500/{code}.png"

    # 3. Selecciones nacionales y clubes emblemáticos adicionales
    national_teams = {
        "Guatemala": "gt", "México": "mx", "Mexico": "mx", "Estados Unidos": "us", "Argentina": "ar",
        "Brasil": "br", "Brazil": "br", "Colombia": "co", "España": "es", "Spain": "es", "Inglaterra": "gb-eng",
        "England": "gb-eng", "Francia": "fr", "France": "fr", "Alemania": "de", "Germany": "de",
        "Italia": "it", "Italy": "it", "Portugal": "pt", "Países Bajos": "nl", "Holanda": "nl",
        "Uruguay": "uy", "Chile": "cl", "Ecuador": "ec", "Perú": "pe", "Peru": "pe", "Costa Rica": "cr",
        "Honduras": "hn", "El Salvador": "sv", "Panamá": "pa", "Panama": "pa", "Canadá": "ca", "Canada": "ca"
    }
    for name, code in national_teams.items():
        if name not in logos:
            logos[name] = f"https://flagcdn.com/w80/{code}.png"

    normalized_mapping = {}
    for name, url in logos.items():
        n = norm_text(name)
        if n and n not in normalized_mapping:
            normalized_mapping[n] = url

    full_payload = {
        "logos": logos,
        "normalized": normalized_mapping
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, indent=2, ensure_ascii=False)

    print(f"Base de datos de escudos guardada en {OUTPUT_FILE} con {len(logos)} equipos únicos.")

if __name__ == "__main__":
    main()
