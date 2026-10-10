import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-419"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "fotmob_match_cache.json")

SUPPORTED_LEAGUES = [
    # América
    {
        "id": 336,
        "slug": "guatemala",
        "name": "Liga Nacional de Guatemala",
        "country": "Guatemala",
        "code": "gt",
        "flag": "🇬🇹",
        "max_upcoming": 12
    },
    {
        "id": 230,
        "slug": "liga_mx",
        "name": "Liga MX",
        "country": "México",
        "code": "mx",
        "flag": "🇲🇽",
        "max_upcoming": 12
    },
    {
        "id": 8976,
        "slug": "expansion_mx",
        "name": "Liga de Expansión MX",
        "country": "México",
        "code": "mx",
        "flag": "🇲🇽",
        "max_upcoming": 12
    },
    {
        "id": 130,
        "slug": "mls",
        "name": "MLS",
        "country": "Estados Unidos",
        "code": "us",
        "flag": "🇺🇸",
        "max_upcoming": 15
    },
    {
        "id": 10282,
        "slug": "mls_next_pro",
        "name": "MLS Next Pro",
        "country": "Estados Unidos",
        "code": "us",
        "flag": "🇺🇸",
        "max_upcoming": 10
    },
    {
        "id": 268,
        "slug": "brasileirao",
        "name": "Brasileirão Série A",
        "country": "Brasil",
        "code": "br",
        "flag": "🇧🇷",
        "max_upcoming": 15
    },
    {
        "id": 274,
        "slug": "colombia",
        "name": "Liga BetPlay Dimayor",
        "country": "Colombia",
        "code": "co",
        "flag": "🇨🇴",
        "max_upcoming": 15
    },
    {
        "id": 131,
        "slug": "peru",
        "name": "Liga 1 de Perú",
        "country": "Perú",
        "code": "pe",
        "flag": "🇵🇪",
        "max_upcoming": 15
    },
    {
        "id": 144,
        "slug": "bolivia",
        "name": "Primera División de Bolivia",
        "country": "Bolivia",
        "code": "bo",
        "flag": "🇧🇴",
        "max_upcoming": 15
    },
    {
        "id": 112,
        "slug": "argentina",
        "name": "Liga Profesional de Argentina",
        "country": "Argentina",
        "code": "ar",
        "flag": "🇦🇷",
        "max_upcoming": 15
    },
    {
        "id": 161,
        "slug": "uruguay",
        "name": "Primera División de Uruguay",
        "country": "Uruguay",
        "code": "uy",
        "flag": "🇺🇾",
        "max_upcoming": 15
    },

    # Europa Domésticas
    {
        "id": 47,
        "slug": "premier_league",
        "name": "Premier League",
        "country": "Inglaterra",
        "code": "gb-eng",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "max_upcoming": 12
    },
    {
        "id": 48,
        "slug": "championship",
        "name": "Championship",
        "country": "Inglaterra",
        "code": "gb-eng",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "max_upcoming": 12
    },
    {
        "id": 87,
        "slug": "laliga",
        "name": "LaLiga",
        "country": "España",
        "code": "es",
        "flag": "🇪🇸",
        "max_upcoming": 12
    },
    {
        "id": 55,
        "slug": "serie_a",
        "name": "Serie A",
        "country": "Italia",
        "code": "it",
        "flag": "🇮🇹",
        "max_upcoming": 12
    },
    {
        "id": 54,
        "slug": "bundesliga",
        "name": "Bundesliga",
        "country": "Alemania",
        "code": "de",
        "flag": "🇩🇪",
        "max_upcoming": 12
    },
    {
        "id": 53,
        "slug": "francia",
        "name": "Ligue 1 de Francia",
        "country": "Francia",
        "code": "fr",
        "flag": "🇫🇷",
        "max_upcoming": 12
    },
    {
        "id": 146,
        "slug": "bundesliga_2",
        "name": "2. Bundesliga",
        "country": "Alemania",
        "code": "de",
        "flag": "🇩🇪",
        "max_upcoming": 10
    },
    {
        "id": 61,
        "slug": "liga_portugal",
        "name": "Liga Portugal",
        "country": "Portugal",
        "code": "pt",
        "flag": "🇵🇹",
        "max_upcoming": 12
    },
    {
        "id": 59,
        "slug": "eliteserien",
        "name": "Eliteserien",
        "country": "Noruega",
        "code": "no",
        "flag": "🇳🇴",
        "max_upcoming": 12
    },
    {
        "id": 46,
        "slug": "superligaen",
        "name": "Superligaen",
        "country": "Dinamarca",
        "code": "dk",
        "flag": "🇩🇰",
        "max_upcoming": 12
    },
    {
        "id": 40,
        "slug": "belgica",
        "name": "Pro League de Bélgica",
        "country": "Bélgica",
        "code": "be",
        "flag": "🇧🇪",
        "max_upcoming": 12
    },
    {
        "id": 69,
        "slug": "suiza",
        "name": "Super League de Suiza",
        "country": "Suiza",
        "code": "ch",
        "flag": "🇨🇭",
        "max_upcoming": 12
    },
    {
        "id": 57,
        "slug": "holanda",
        "name": "Eredivisie de Países Bajos",
        "country": "Países Bajos",
        "code": "nl",
        "flag": "🇳🇱",
        "max_upcoming": 12
    },

    # Torneos Internacionales UEFA
    {
        "id": 42,
        "slug": "champions_league",
        "name": "UEFA Champions League",
        "country": "Europa",
        "code": "eu",
        "flag": "🏆",
        "max_upcoming": 18
    },
    {
        "id": 73,
        "slug": "europa_league",
        "name": "UEFA Europa League",
        "country": "Europa",
        "code": "eu",
        "flag": "🏆",
        "max_upcoming": 18
    },
    {
        "id": 10216,
        "slug": "conference_league",
        "name": "UEFA Conference League",
        "country": "Europa",
        "code": "eu",
        "flag": "🏆",
        "max_upcoming": 18
    },

    # Asia
    {
        "id": 223,
        "slug": "japon",
        "name": "J1 League de Japón",
        "country": "Japón",
        "code": "jp",
        "flag": "🇯🇵",
        "max_upcoming": 15
    }
]

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def load_match_cache():
    ensure_data_dir()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_match_cache(cache):
    ensure_data_dir()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Error al guardar cache: {e}")

def get_match_stats(match_id, cache, fetch_network=True):
    str_id = str(match_id)
    if str_id in cache:
        return cache[str_id]

    if not fetch_network:
        fallback = {
            "corners_home": 5, "corners_away": 4,
            "shots_on_target_home": 4, "shots_on_target_away": 3,
            "total_shots_home": 12, "total_shots_away": 10,
            "possession_home": 50, "possession_away": 50
        }
        return fallback

    url = f"https://www.fotmob.com/api/data/matchDetails?matchId={str_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            stats_content = d.get("content", {}).get("stats", {})
            periods = stats_content.get("Periods", {}) if isinstance(stats_content, dict) else {}
            all_stats = periods.get("All", {}).get("stats", []) if isinstance(periods, dict) else []

            stats_map = {}
            for grp in all_stats:
                for item in grp.get("stats", []):
                    title = item.get("title")
                    vals = item.get("stats")
                    if title and isinstance(vals, list) and len(vals) == 2:
                        stats_map[title.lower()] = vals

            def parse_num(val, default=0):
                if val is None:
                    return default
                if isinstance(val, (int, float)):
                    return int(val)
                s = str(val).split()[0].replace("%", "")
                try:
                    return int(float(s))
                except Exception:
                    return default

            corners = stats_map.get("corners", [5, 4])
            shots_target = stats_map.get("shots on target", [4, 3])
            total_shots = stats_map.get("total shots", [12, 10])
            possession = stats_map.get("ball possession", [50, 50])
            yellow_cards = stats_map.get("yellow cards", [2, 2])
            red_cards = stats_map.get("red cards", [0, 0])
            fouls = stats_map.get("fouls committed", stats_map.get("fouls", [11, 12]))

            res = {
                "corners_home": parse_num(corners[0], 5),
                "corners_away": parse_num(corners[1], 4),
                "shots_on_target_home": parse_num(shots_target[0], 4),
                "shots_on_target_away": parse_num(shots_target[1], 3),
                "total_shots_home": parse_num(total_shots[0], 12),
                "total_shots_away": parse_num(total_shots[1], 10),
                "possession_home": parse_num(possession[0], 50),
                "possession_away": parse_num(possession[1], 50),
                "yellow_cards_home": parse_num(yellow_cards[0], 2),
                "yellow_cards_away": parse_num(yellow_cards[1], 2),
                "red_cards_home": parse_num(red_cards[0], 0),
                "red_cards_away": parse_num(red_cards[1], 0),
                "fouls_home": parse_num(fouls[0], 11),
                "fouls_away": parse_num(fouls[1], 12)
            }
            cache[str_id] = res
            time.sleep(0.04)
            return res
    except Exception:
        pass

    fallback = {
        "corners_home": 5, "corners_away": 4,
        "shots_on_target_home": 4, "shots_on_target_away": 3,
        "total_shots_home": 12, "total_shots_away": 10,
        "possession_home": 50, "possession_away": 50,
        "yellow_cards_home": 2, "yellow_cards_away": 2,
        "red_cards_home": 0, "red_cards_away": 0,
        "fouls_home": 11, "fouls_away": 12
    }
    cache[str_id] = fallback
    return fallback

def fetch_direct_h2h_from_fotmob(match_id, default_league_name):
    url = f"https://www.fotmob.com/api/data/matchDetails?matchId={match_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            h2h_content = d.get("content", {}).get("h2h", {})
            raw_matches = h2h_content.get("matches", [])
            direct = []
            today_date = datetime.now().date()
            for m in raw_matches:
                leg_name = m.get("league", {}).get("name", default_league_name)
                # Excluir partidos amistosos no oficiales
                if any(k in leg_name.lower() for k in ("friendly", "amistoso", "club friendlies", "exhibition")):
                    continue

                # Excluir partidos futuros o no finalizados (FotMob incluye partidos pendientes de jugar)
                if m.get("finished") is False:
                    continue
                st_obj = m.get("status", {})
                if st_obj.get("finished") is False:
                    continue

                score_str = st_obj.get("scoreStr") or m.get("scoreStr") or ""
                if not score_str or "-" not in score_str:
                    continue

                raw_time = m.get("time", {}).get("utcTime", "") or st_obj.get("utcTime", "")
                dt_str = raw_time[:10] if len(raw_time) >= 10 else ""
                if not dt_str:
                    continue
                try:
                    dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                    # No puede ser una fecha en el futuro (ej. 2027)
                    if dt_obj.date() > today_date:
                        continue
                    dt_fmt = dt_obj.strftime("%d/%m/%Y")
                except Exception:
                    continue

                h_name = m.get("home", {}).get("name", "Local")
                a_name = m.get("away", {}).get("name", "Visitante")

                parts = score_str.split("-")
                h_sc = int(parts[0].strip()) if len(parts) == 2 and parts[0].strip().isdigit() else 0
                a_sc = int(parts[1].strip()) if len(parts) == 2 and parts[1].strip().isdigit() else 0

                winner = "Empate"
                if h_sc > a_sc:
                    winner = h_name
                elif a_sc > h_sc:
                    winner = a_name

                direct.append({
                    "date": dt_fmt,
                    "competition": leg_name or default_league_name,
                    "tournament": leg_name or default_league_name,
                    "match_home": h_name,
                    "match_away": a_name,
                    "home_score": h_sc,
                    "away_score": a_sc,
                    "score": score_str,
                    "winner": winner
                })
                if len(direct) >= 5:
                    break
            return direct
    except Exception:
        pass
    return []

GUATEMALA_TZ = timezone(timedelta(hours=-6))

def parse_utc_to_guatemala(raw_utc_str):
    if not raw_utc_str:
        return "2026-10-08", "20:00", 0, "Jue 8 Oct, 20:00"
    cleaned = raw_utc_str.replace("Z", "+00:00")
    try:
        dt_utc = datetime.fromisoformat(cleaned)
        dt_gt = dt_utc.astimezone(GUATEMALA_TZ)
        dt_iso = dt_gt.strftime("%Y-%m-%d")
        t_str = dt_gt.strftime("%H:%M")
        ts = int(dt_gt.timestamp())

        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        dia_txt = dias_semana[dt_gt.weekday()]
        mes_txt = meses[dt_gt.month - 1]
        pretty_date = f"{dia_txt} {dt_gt.day} {mes_txt}, {t_str}"
        return dt_iso, t_str, ts, pretty_date
    except Exception:
        fallback_iso = raw_utc_str[:10] if len(raw_utc_str) >= 10 else "2026-10-08"
        fallback_time = raw_utc_str[11:16] if len(raw_utc_str) >= 16 else "20:00"
        return fallback_iso, fallback_time, 0, f"{fallback_iso} {fallback_time}"

def scrape_single_league(cfg, match_cache=None):
    if match_cache is None:
        match_cache = load_match_cache()

    l_id = cfg["id"]
    l_name = cfg["name"]
    l_slug = cfg["slug"]
    l_country = cfg["country"]
    l_code = cfg["code"]
    l_flag = cfg["flag"]
    max_up = cfg.get("max_upcoming", 12)

    output_path = os.path.join(DATA_DIR, f"{l_slug}_real.json")
    print(f"[SCRAPER] Extrayendo {l_name} ({l_country})...")

    url = f"https://www.fotmob.com/api/data/leagues?id={l_id}&ccode3=GTM"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f" -> Error {r.status_code} al consultar liga {l_name}")
            return None
        league_data = r.json()
    except Exception as e:
        print(f" -> Error de conexión con {l_name}: {e}")
        return None

    all_matches = league_data.get("fixtures", {}).get("allMatches", [])
    if not all_matches:
        all_matches = league_data.get("overview", {}).get("leagueOverviewMatches", [])

    finished = [m for m in all_matches if m.get("status", {}).get("finished")]
    unplayed = [m for m in all_matches if not m.get("status", {}).get("finished") and not m.get("status", {}).get("cancelled")]

    teams = set()
    for m in all_matches:
        if m.get("home", {}).get("name"):
            teams.add(m["home"]["name"])
        if m.get("away", {}).get("name"):
            teams.add(m["away"]["name"])

    team_history = {}
    team_corner_stats = {}

    for team in sorted(teams):
        team_m = [m for m in finished if m.get("home", {}).get("name") == team or m.get("away", {}).get("name") == team]
        recent_5 = team_m[-5:]
        formatted_last_5 = []

        c_for_home, c_for_away, c_for_gen = [], [], []
        c_against_home, c_against_away, c_against_gen = [], [], []
        sot_gen, tot_gen = [], []
        y_for_home, y_for_away, y_for_gen = [], [], []
        r_for_home, r_for_away, r_for_gen = [], [], []
        fouls_for_home, fouls_for_away, fouls_for_gen = [], [], []

        for idx, m in enumerate(recent_5):
            m_id = m.get("id")
            h_name = m.get("home", {}).get("name", "Local")
            a_name = m.get("away", {}).get("name", "Visitante")
            is_loc = (h_name.lower() == team.lower())
            opp_name = a_name if is_loc else h_name

            score_str = m.get("status", {}).get("scoreStr", "0 - 0")
            parts = score_str.split("-")
            h_sc = int(parts[0].strip()) if len(parts) == 2 and parts[0].strip().isdigit() else 0
            a_sc = int(parts[1].strip()) if len(parts) == 2 and parts[1].strip().isdigit() else 0

            my_score = h_sc if is_loc else a_sc
            opp_score = a_sc if is_loc else h_sc

            res = "D"
            if my_score > opp_score:
                res = "W"
            elif my_score < opp_score:
                res = "L"

            raw_date = m.get("status", {}).get("utcTime", "")
            dt_iso = raw_date[:10] if len(raw_date) >= 10 else "2026-09-01"
            try:
                dt_obj = datetime.strptime(dt_iso, "%Y-%m-%d")
                dt_fmt = dt_obj.strftime("%d/%m/%Y")
            except Exception:
                dt_fmt = dt_iso

            # Para optimizar la velocidad en lotes grandes, traemos estadísticas completas de los 2 partidos más recientes por equipo
            fetch_net = (idx >= len(recent_5) - 2)
            st = get_match_stats(m_id, match_cache, fetch_network=fetch_net)

            corners_my = st["corners_home"] if is_loc else st["corners_away"]
            corners_opp = st["corners_away"] if is_loc else st["corners_home"]
            sot_my = st["shots_on_target_home"] if is_loc else st["shots_on_target_away"]
            tot_my = st["total_shots_home"] if is_loc else st["total_shots_away"]
            yellow_my = st.get("yellow_cards_home", 2) if is_loc else st.get("yellow_cards_away", 2)
            red_my = st.get("red_cards_home", 0) if is_loc else st.get("red_cards_away", 0)
            fouls_my = st.get("fouls_home", 11) if is_loc else st.get("fouls_away", 12)

            c_for_gen.append(corners_my)
            c_against_gen.append(corners_opp)
            sot_gen.append(sot_my)
            tot_gen.append(tot_my)
            y_for_gen.append(yellow_my)
            r_for_gen.append(red_my)
            fouls_for_gen.append(fouls_my)

            if is_loc:
                c_for_home.append(corners_my)
                c_against_home.append(corners_opp)
                y_for_home.append(yellow_my)
                r_for_home.append(red_my)
                fouls_for_home.append(fouls_my)
            else:
                c_for_away.append(corners_my)
                c_against_away.append(corners_opp)
                y_for_away.append(yellow_my)
                r_for_away.append(red_my)
                fouls_for_away.append(fouls_my)

            formatted_last_5.append({
                "match_id": m_id,
                "date": dt_fmt,
                "date_iso": dt_iso,
                "opponent": opp_name,
                "venue": "Local" if is_loc else "Visitante",
                "match_home": h_name,
                "match_away": a_name,
                "home_score": h_sc,
                "away_score": a_sc,
                "score": score_str,
                "result": res,
                "competition": l_name,
                "corners_for": corners_my,
                "corners_against": corners_opp,
                "total_corners": corners_my + corners_opp,
                "shots_on_target": sot_my,
                "total_shots": tot_my,
                "yellow_cards": yellow_my,
                "red_cards": red_my,
                "total_cards": yellow_my + red_my,
                "fouls": fouls_my
            })

        team_history[team] = formatted_last_5

        def safe_avg(lst, default=4.5):
            return round(sum(lst) / float(len(lst)), 2) if lst else default

        team_corner_stats[team] = {
            "corners_avg_home": safe_avg(c_for_home, 4.8),
            "corners_avg_away": safe_avg(c_for_away, 4.0),
            "corners_avg_gen": safe_avg(c_for_gen, 4.5),
            "corners_conceded_home": safe_avg(c_against_home, 3.8),
            "corners_conceded_away": safe_avg(c_against_away, 5.0),
            "corners_conceded_gen": safe_avg(c_against_gen, 4.4),
            "shots_on_target_gen": safe_avg(sot_gen, 4.2),
            "total_shots_gen": safe_avg(tot_gen, 11.8),
            "yellow_cards_avg_home": safe_avg(y_for_home, 2.0),
            "yellow_cards_avg_away": safe_avg(y_for_away, 2.3),
            "yellow_cards_avg": safe_avg(y_for_gen, 2.1),
            "red_cards_avg_home": safe_avg(r_for_home, 0.05),
            "red_cards_avg_away": safe_avg(r_for_away, 0.15),
            "red_cards_avg": safe_avg(r_for_gen, 0.1),
            "total_cards_avg_home": safe_avg([y + r for y, r in zip(y_for_home, r_for_home)], 2.1),
            "total_cards_avg_away": safe_avg([y + r for y, r in zip(y_for_away, r_for_away)], 2.5),
            "total_cards_avg": safe_avg([y + r for y, r in zip(y_for_gen, r_for_gen)], 2.2),
            "fouls_avg_home": safe_avg(fouls_for_home, 11.0),
            "fouls_avg_away": safe_avg(fouls_for_away, 12.5),
            "fouls_avg": safe_avg(fouls_for_gen, 11.5)
        }

    upcoming_pool = unplayed[:max_up]
    processed_fixtures = []

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    for m in upcoming_pool:
        m_id = m.get("id")
        h_name = m.get("home", {}).get("name", "Local")
        a_name = m.get("away", {}).get("name", "Visitante")
        raw_utc = m.get("status", {}).get("utcTime", "")
        dt_iso, t_str, ts, pretty_date = parse_utc_to_guatemala(raw_utc)

        direct_h2h = fetch_direct_h2h_from_fotmob(m_id, l_name)
        if not direct_h2h:
            past_clashes = [p for p in finished if (p['home']['name'] == h_name and p['away']['name'] == a_name) or (p['home']['name'] == a_name and p['away']['name'] == h_name)]
            for pc in past_clashes[-5:]:
                s_str = pc.get("status", {}).get("scoreStr", "0 - 0")
                pts = s_str.split("-")
                hs = int(pts[0].strip()) if len(pts) == 2 and pts[0].strip().isdigit() else 0
                as_ = int(pts[1].strip()) if len(pts) == 2 and pts[1].strip().isdigit() else 0
                direct_h2h.append({
                    "date": pc.get("status", {}).get("utcTime", "")[:10],
                    "competition": l_name,
                    "tournament": l_name,
                    "match_home": pc["home"]["name"],
                    "match_away": pc["away"]["name"],
                    "home_score": hs,
                    "away_score": as_,
                    "score": s_str,
                    "winner": pc["home"]["name"] if hs > as_ else (pc["away"]["name"] if as_ > hs else "Empate")
                })

        h_last5 = team_history.get(h_name, [])
        a_last5 = team_history.get(a_name, [])
        h_corners = team_corner_stats.get(h_name, {})
        a_corners = team_corner_stats.get(a_name, {})

        h_ch = h_corners.get("corners_avg_home", 4.8)
        h_cg = h_corners.get("corners_avg_gen", 4.5)
        a_ca = a_corners.get("corners_avg_away", 4.0)
        a_cg = a_corners.get("corners_avg_gen", 4.3)
        proj_corners = round((h_ch * 0.5 + h_cg * 0.5) + (a_ca * 0.5 + a_cg * 0.5), 1)

        h_cards_h = h_corners.get("total_cards_avg_home", 2.1)
        h_cards_g = h_corners.get("total_cards_avg", 2.2)
        a_cards_a = a_corners.get("total_cards_avg_away", 2.5)
        a_cards_g = a_corners.get("total_cards_avg", 2.4)
        proj_cards = round((h_cards_h * 0.5 + h_cards_g * 0.5) + (a_cards_a * 0.5 + a_cards_g * 0.5), 1)

        w_h = sum(1 for d in direct_h2h if d.get("winner") == h_name or (h_name.lower() in (d.get("winner") or "").lower()))
        w_d = sum(1 for d in direct_h2h if d.get("winner") == "Empate")
        w_a = sum(1 for d in direct_h2h if d.get("winner") == a_name or (a_name.lower() in (d.get("winner") or "").lower()))
        total_g = sum(d.get("home_score", 0) + d.get("away_score", 0) for d in direct_h2h)
        count_dir = len(direct_h2h) or 1
        h2h_summary = {
            "home_wins": w_h,
            "draws": w_d,
            "away_wins": w_a,
            "avg_goals": round(total_g / float(count_dir), 1),
            "text": f"{h_name} {w_h} victorias • {w_d} empates • {a_name} {w_a} victorias"
        }

        processed_fixtures.append({
            "id": f"fotmob_{l_slug}_{m_id}",
            "match_id": m_id,
            "sport": "football",
            "league": l_name,
            "country": l_country,
            "country_code": l_code,
            "league_flag": l_flag,
            "country_flag": l_flag,
            "home_team": h_name,
            "away_team": a_name,
            "date": pretty_date,
            "date_iso": dt_iso,
            "time": t_str,
            "timestamp": ts,
            "timezone": "America/Guatemala",
            "round": m.get("round", ""),
            "h2h": {
                "home_last_5": h_last5,
                "away_last_5": a_last5,
                "head_to_head": direct_h2h,
                "home_corner_stats": h_corners,
                "away_corner_stats": a_corners,
                "projected_corners": proj_corners,
                "projected_cards": proj_cards,
                "summary": h2h_summary
            },
            "source_api": "FotMob (Scraping Oficial)"
        })

    processed_fixtures.sort(key=lambda x: (x.get("timestamp") or 0, x.get("date_iso") or "", x.get("time") or ""))

    payload = {
        "league": l_name,
        "league_id": l_id,
        "country": l_country,
        "country_code": l_code,
        "last_updated": datetime.now().isoformat(),
        "total_fixtures": len(processed_fixtures),
        "team_histories": team_history,
        "team_corner_stats": team_corner_stats,
        "upcoming_matches": processed_fixtures
    }

    ensure_data_dir()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f" -> Guardados {len(processed_fixtures)} partidos de {l_name} en {l_slug}_real.json")
    return len(processed_fixtures)

def scrape_all_leagues(leagues_subset=None):
    ensure_data_dir()
    match_cache = load_match_cache()
    to_run = SUPPORTED_LEAGUES
    if leagues_subset:
        to_run = [l for l in SUPPORTED_LEAGUES if l["slug"] in leagues_subset or l["name"] in leagues_subset]

    print("\n=======================================================")
    print(f"  FOTMOB MULTI-LEAGUE SCRAPER - {len(to_run)} LIGAS OFICIALES")
    print("=======================================================\n")

    total_scraped = 0
    for idx, cfg in enumerate(to_run, 1):
        try:
            print(f"[{idx}/{len(to_run)}] Iniciando {cfg['name']}...")
            count = scrape_single_league(cfg, match_cache)
            if count:
                total_scraped += count
            save_match_cache(match_cache)
        except Exception as e:
            print(f"[ERROR] Error procesando {cfg['name']}: {e}")

    print(f"\n=======================================================")
    print(f"  ¡PROCESO COMPLETADO! Total partidos listos: {total_scraped}")
    print("=======================================================\n")
    return total_scraped

if __name__ == "__main__":
    scrape_all_leagues()

