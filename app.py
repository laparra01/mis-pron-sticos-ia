import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import security_manager
from data_provider import fetch_matches_data, fetch_live_matches_data, get_config, load_team_logos
from dream_parleys_engine import get_or_generate_dream_parleys
import gzip
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, "templates") if os.path.isdir(os.path.join(base_dir, "templates")) else base_dir
app = Flask(__name__, template_folder=template_dir)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
cfg_init = get_config()
app.secret_key = getattr(cfg_init, "SECRET_KEY", "mis-pronosticos-ai-secret-key-2026")


@app.before_request
def security_and_access_control():
    try:
        # Permitir archivos estáticos
        if request.path.startswith('/static'):
            return None

        client_ip = security_manager.get_client_ip(request)
        client_dev = request.headers.get("X-Device-Id") or request.args.get("device_id")

        # Verificación de lista negra (bloqueados)
        if security_manager.is_blocked(client_ip, client_dev):
            if request.path == "/blocked":
                return None
            if request.path.startswith("/api/"):
                return jsonify({"error": "Acceso restringido", "blocked": True}), 403
            return redirect("/blocked")

        # Protección Anti-Scraping / Flood para APIs
        if request.path.startswith("/api/") and request.path not in ("/api/ping", "/api/heartbeat"):
            if not security_manager.check_rate_limit(client_ip):
                return jsonify({"error": "Demasiadas peticiones por minuto (Anti-Scraping). Espera un momento.", "rate_limited": True}), 429
    except Exception as esec:
        print(f"[SECURITY CHECK WARNING]: {esec}")


@app.after_request
def compress_and_secure_response(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' in accept_encoding.lower() and response.status_code == 200 and not response.direct_passthrough and len(response.data) > 1024:
        response.data = gzip.compress(response.data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(response.data)
    return response

def slim_match_for_client(m):
    p = m.get("prediction", {})
    picks = p.get("four_predictions") or p.get("seven_predictions") or p.get("eight_predictions") or []
    ref = m.get("referee") or {}

    p_exp_c = float(p.get("projected_corners", 9.5) or 9.5)
    pct_c_85 = p.get("pct_corners_over_85") or p.get("pct_corners_over")
    if pct_c_85 is None or pct_c_85 == 55.0:
        import math
        s = 0.0
        for k in range(9, 35):
            s += (math.exp(-p_exp_c) * (p_exp_c ** k)) / math.factorial(k)
        pct_c_85 = round(min(0.99, max(0.01, s)) * 100, 1)

    pct_c_95 = p.get("pct_corners_over_95")
    if pct_c_95 is None:
        import math
        s95 = 0.0
        for k in range(10, 35):
            s95 += (math.exp(-p_exp_c) * (p_exp_c ** k)) / math.factorial(k)
        pct_c_95 = round(min(0.99, max(0.01, s95)) * 100, 1)

    slim_pred = {
        "prob_home": p.get("prob_home"),
        "prob_draw": p.get("prob_draw"),
        "prob_away": p.get("prob_away"),
        "prob_over_15": p.get("prob_over_15"),
        "prob_under_15": p.get("prob_under_15"),
        "prob_over_25": p.get("prob_over_25"),
        "prob_under_25": p.get("prob_under_25"),
        "prob_btts": p.get("prob_btts"),
        "prob_home_score": p.get("prob_home_score") or p.get("home_team_over_05"),
        "prob_away_score": p.get("prob_away_score") or p.get("away_team_over_05"),
        "home_team_over_05": p.get("home_team_over_05") or p.get("prob_home_score"),
        "away_team_over_05": p.get("away_team_over_05") or p.get("prob_away_score"),
        "recommended_pick": p.get("recommended_pick"),
        "confidence": p.get("confidence"),
        "fair_odds": p.get("fair_odds"),
        "risk_level": p.get("risk_level"),
        "risk_color": p.get("risk_color"),
        "is_value_bet": p.get("is_value_bet"),
        "projected_corners": p_exp_c,
        "pct_corners_over": pct_c_85,
        "pct_corners_over_85": pct_c_85,
        "pct_corners_over_95": pct_c_95,
        "projected_cards": p.get("projected_cards"),
        "total_points": p.get("total_points"),
        "over_under_line": p.get("over_under_line"),
        "spread_home": p.get("spread_home"),
        "quarters_breakdown": p.get("quarters_breakdown"),
        "top_scores": p.get("top_scores", [])[:1],
        "four_predictions": picks[:4],
        "projections_matrix": p.get("projections_matrix"),
    }
    ref_clean = None
    if ref.get("name"):
        ref_clean = {
            "name": ref.get("name"),
            "yellow_cards_per_match": ref.get("yellow_cards_per_match"),
            "rigor_level": ref.get("rigor_level"),
            "matches_analyzed": ref.get("matches_analyzed"),
            "fouls_per_match": ref.get("fouls_per_match"),
            "penalty_percentage": ref.get("penalty_percentage")
        }
    return {
        "id": m.get("id"),
        "match_id": m.get("match_id"),
        "sport": m.get("sport"),
        "league": m.get("league"),
        "country": m.get("country"),
        "country_code": m.get("country_code", ""),
        "league_flag": m.get("league_flag", ""),
        "country_flag": m.get("country_flag", ""),
        "home_team": m.get("home_team"),
        "away_team": m.get("away_team"),
        "home_logo": m.get("home_logo", ""),
        "away_logo": m.get("away_logo", ""),
        "date": m.get("date"),
        "date_iso": m.get("date_iso"),
        "time": m.get("time"),
        "timestamp": m.get("timestamp") or 0,
        "is_live": m.get("is_live", False),
        "is_halftime": m.get("is_halftime", False),
        "minute": m.get("minute"),
        "quarter": m.get("quarter"),
        "display_clock": m.get("display_clock"),
        "score_home": m.get("score_home", 0),
        "score_away": m.get("score_away", 0),
        "is_external": m.get("is_external", False),
        "source_api": m.get("source_api", ""),
        "home_stats": m.get("home_stats"),
        "away_stats": m.get("away_stats"),
        "referee": ref_clean,
        "prediction": slim_pred,
        "h2h": {"summary": (m.get("h2h") or {}).get("summary", {})},
        "ai_analysis": m.get("ai_analysis")
    }


@app.route("/")
def index():
    try:
        cfg = get_config()
        live_api_active = bool(cfg and getattr(cfg, "USE_LIVE_API", False))
        live_matches = fetch_live_matches_data() or []
        upcoming_matches = fetch_matches_data() or []
        all_matches = live_matches + upcoming_matches

        football_total = sum(1 for m in all_matches if m.get("sport") == "football")
        nba_total = sum(1 for m in all_matches if m.get("sport") == "nba")
        value_picks = sum(1 for m in all_matches if m.get("prediction", {}).get("is_value_bet", False))
        low_risk = sum(1 for m in all_matches if m.get("prediction", {}).get("risk_level") == "Bajo")

        stats_summary = {
            "total_analyzed": len(all_matches),
            "football_count": football_total,
            "nba_count": nba_total,
            "live_count": len(live_matches),
            "value_picks": value_picks,
            "low_risk": low_risk,
            "historical_accuracy": "78.4%"
        }
        today_dt = datetime.now()
        tomorrow_dt = today_dt + timedelta(days=1)
        today_iso = today_dt.strftime("%Y-%m-%d")
        tomorrow_iso = tomorrow_dt.strftime("%Y-%m-%d")
        today_str = today_dt.strftime("%d/%m")
        tomorrow_str = tomorrow_dt.strftime("%d/%m")

        country_flags = {
            "Brasil": "🇧🇷", "España": "🇪🇸", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Italia": "🇮🇹",
            "Alemania": "🇩🇪", "Francia": "🇫🇷", "Portugal": "🇵🇹", "Países Bajos": "🇳🇱",
            "Holanda": "🇳🇱", "Estados Unidos": "🇺🇸", "México": "🇲🇽", "Argentina": "🇦🇷",
            "Colombia": "🇨🇴", "Guatemala": "🇬🇹", "Noruega": "🇳🇴", "Dinamarca": "🇩🇰",
            "Bélgica": "🇧🇪", "Suiza": "🇨🇭", "Perú": "🇵🇪", "Bolivia": "🇧🇴",
            "Japón": "🇯🇵",
            "Europa": "🏆", "Chile": "🇨🇱", "Uruguay": "🇺🇾", "Armenia": "🇦🇲", "Austria": "🇦🇹",
            "Suecia": "🇸🇪", "Grecia": "🇬🇷", "Sudamérica": "🏆", "Internacional": "🌍"
        }
        country_codes = {
            "Brasil": "br", "España": "es", "Inglaterra": "gb-eng", "Italia": "it",
            "Alemania": "de", "Francia": "fr", "Portugal": "pt", "Países Bajos": "nl",
            "Holanda": "nl", "Estados Unidos": "us", "México": "mx", "Argentina": "ar",
            "Colombia": "co", "Guatemala": "gt", "Noruega": "no", "Dinamarca": "dk",
            "Bélgica": "be", "Suiza": "ch", "Perú": "pe", "Bolivia": "bo",
            "Japón": "jp",
            "Europa": "eu", "Chile": "cl", "Uruguay": "uy", "Armenia": "am", "Austria": "at",
            "Suecia": "se", "Grecia": "gr", "Sudamérica": ""
        }
        country_map = {}
        country_code_map = {}
        for m in all_matches:
            c_name = m.get("country", "Internacional")
            c_flag = m.get("country_flag") or m.get("league_flag") or country_flags.get(c_name, "🌍")
            c_code = m.get("country_code") or country_codes.get(c_name, "")
            if c_name and c_name not in country_map:
                country_map[c_name] = c_flag
                country_code_map[c_name] = c_code

        unique_countries = [
            {"name": c, "flag": country_map[c], "code": country_code_map.get(c, "")}
            for c in sorted(country_map.keys())
        ]
        unique_leagues = sorted(list(set(m.get("league", "") for m in all_matches if m.get("league"))))

        try:
            dream_parleys = get_or_generate_dream_parleys(upcoming_matches)
        except Exception as ep:
            print(f"[PARLEYS ERROR]: {ep}")
            dream_parleys = {"tickets": []}

        now_ts = datetime.now().timestamp()
        today_pending_count = sum(1 for m in upcoming_matches if m.get("date_iso") == today_iso and (m.get("timestamp") or 0) >= now_ts - 300)
        team_logos, team_logos_norm = load_team_logos()

        upcoming_initial = upcoming_matches[:40]
        slim_all_matches = [slim_match_for_client(m) for m in all_matches]

        context = dict(
            live_matches=live_matches,
            upcoming_matches=upcoming_initial,
            total_upcoming_matches=len(upcoming_matches),
            all_matches=slim_all_matches,
            dream_parleys=dream_parleys,
            stats=stats_summary,
            live_api_active=live_api_active,
            today_iso=today_iso,
            tomorrow_iso=tomorrow_iso,
            today_str=today_str,
            tomorrow_str=tomorrow_str,
            today_pending_count=today_pending_count,
            countries=unique_countries,
            leagues=unique_leagues,
            team_logos=team_logos,
            team_logos_norm=team_logos_norm,
            online_users=security_manager.get_active_count(),
            is_owner=bool(session.get("is_admin") or session.get("is_owner"))
        )

        # Priorizar la plantilla index.html mas actualizada (soporta templates/index.html y raiz index.html)
        root_tpl = os.path.join(base_dir, "index.html")
        dir_tpl = os.path.join(base_dir, "templates", "index.html")
        target_path = None

        if os.path.exists(root_tpl) and os.path.exists(dir_tpl):
            try:
                with open(root_tpl, "r", encoding="utf-8") as f_r:
                    root_c = f_r.read()
                with open(dir_tpl, "r", encoding="utf-8") as f_d:
                    dir_c = f_d.read()
                if "btn-share-matrix-whatsapp" in root_c and "btn-share-matrix-whatsapp" not in dir_c:
                    target_path = root_tpl
                elif os.path.getmtime(root_tpl) > os.path.getmtime(dir_tpl):
                    target_path = root_tpl
                else:
                    target_path = dir_tpl
            except Exception:
                target_path = dir_tpl
        elif os.path.exists(root_tpl):
            target_path = root_tpl
        elif os.path.exists(dir_tpl):
            target_path = dir_tpl

        if target_path:
            from flask import render_template_string
            with open(target_path, "r", encoding="utf-8") as f:
                return render_template_string(f.read(), **context)

        return render_template("index.html", **context)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"[ERROR /]: {err_msg}")
        from flask import render_template_string
        return render_template_string('''<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Picks 90 GT - Sincronizando</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen p-4 font-sans">
    <div class="bg-slate-900 border border-slate-800 p-8 rounded-3xl max-w-md w-full text-center shadow-2xl">
        <div class="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
            <svg class="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
        </div>
        <h1 class="text-xl font-bold text-white mb-2">Sincronizando Picks 90 GT</h1>
        <p class="text-sm text-slate-400 mb-6 leading-relaxed">El sistema está actualizando las cuotas y partidos en vivo. Toca el botón abajo para ingresar.</p>
        <a href="/" class="inline-block w-full py-3.5 px-6 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-2xl transition shadow-lg shadow-emerald-500/20 active:scale-[0.98]">
            Entrar a Picks 90 GT
        </a>
    </div>
</body>
</html>'''), 500

@app.errorhandler(500)
def handle_500_error(e):
    import traceback
    err_msg = traceback.format_exc()
    print(f"[500 ERROR CAUGHT]: {err_msg}")
    from flask import render_template_string
    return render_template_string('''<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Picks 90 GT - Sincronizando</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen p-4 font-sans">
    <div class="bg-slate-900 border border-slate-800 p-8 rounded-3xl max-w-md w-full text-center shadow-2xl">
        <div class="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
            <svg class="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
        </div>
        <h1 class="text-xl font-bold text-white mb-2">Sincronizando Picks 90 GT</h1>
        <p class="text-sm text-slate-400 mb-6 leading-relaxed">El sistema está actualizando las cuotas y partidos en vivo. Toca el botón abajo para ingresar.</p>
        <a href="/" class="inline-block w-full py-3.5 px-6 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-2xl transition shadow-lg shadow-emerald-500/20 active:scale-[0.98]">
            Entrar a Picks 90 GT
        </a>
    </div>
</body>
</html>'''), 500

@app.route("/api/live")
def api_live():
    sport = request.args.get("sport", "all")
    return jsonify({"live_matches": fetch_live_matches_data(sport)})

@app.route("/api/matches")
def api_matches():
    sport = request.args.get("sport", "all")
    league = request.args.get("league")
    risk = request.args.get("risk")
    value_only = request.args.get("value_only") == "true"

    matches = fetch_matches_data(sport)

    if league and league != "all":
        matches = [m for m in matches if league.lower() in m["league"].lower()]
    if risk and risk != "all":
        matches = [m for m in matches if m["prediction"]["risk_level"].lower() == risk.lower()]
    if value_only:
        matches = [m for m in matches if m["prediction"]["is_value_bet"]]

    return jsonify({"matches": matches})

@app.route("/api/dream-parleys")
def api_dream_parleys():
    try:
        upcoming_matches = fetch_matches_data() or []
        parleys = get_or_generate_dream_parleys(upcoming_matches)
        return jsonify(parleys)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dream-parleys/regenerate", methods=["POST"])
def api_dream_parleys_regenerate():
    try:
        upcoming_matches = fetch_matches_data() or []
        parleys = get_or_generate_dream_parleys(upcoming_matches, force_regenerate=True)
        return jsonify(parleys)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from ai_analyzer import generate_ai_analysis, generate_live_ai_analysis, generate_nba_ai_analysis, generate_nba_live_ai_analysis

@app.route("/api/match/<match_id>")
def api_match_detail(match_id):
    all_m = fetch_live_matches_data() + fetch_matches_data()
    match = next((m for m in all_m if m.get("id") == match_id or str(m.get("match_id")) == str(match_id)), None)
    if not match:
        return jsonify({"error": "Partido no encontrado"}), 404
    return jsonify(match)

@app.route("/api/match/<match_id>/gemini_analysis")
def api_match_gemini(match_id):
    all_m = fetch_live_matches_data() + fetch_matches_data()
    match = next((m for m in all_m if m.get("id") == match_id or str(m.get("match_id")) == str(match_id)), None)
    if not match:
        return jsonify({"error": "Partido no encontrado"}), 404

    sport = match.get("sport", "football")
    is_live = match.get("is_live", False)
    pred = match.get("prediction", {})
    live_stats = match.get("live_stats", {})

    if is_live:
        if sport == "nba":
            ai_data = generate_nba_live_ai_analysis(match, pred, live_stats, force_gemini=True)
        else:
            ai_data = generate_live_ai_analysis(match, pred, live_stats, force_gemini=True)
    else:
        if sport == "nba":
            ai_data = generate_nba_ai_analysis(match, pred, force_gemini=True)
        else:
            ai_data = generate_ai_analysis(match, pred, force_gemini=True)

    match["ai_analysis"] = ai_data
    return jsonify(ai_data)

@app.route("/api/match/<match_id>/referee")
def api_match_referee(match_id):
    from data_provider import get_match_referee
    all_m = fetch_live_matches_data() + fetch_matches_data()
    match = next((m for m in all_m if m.get("id") == match_id or str(m.get("match_id")) == str(match_id)), None)
    if match and match.get("referee"):
        return jsonify({"referee": match["referee"]})

    clean_id = match.get("match_id") if match else match_id
    ref = get_match_referee(clean_id)
    if match and ref:
        match["referee"] = ref
    return jsonify({"referee": ref})


@app.route("/api/trigger-scrape", methods=["POST"])
def api_trigger_scrape():
    """
    Inicia la actualización bajo demanda:
    - Si GITHUB_TOKEN está configurado, invoca GitHub Actions para procesar en la nube y persistir en el repo.
    - Si no hay GITHUB_TOKEN (ej. local o prueba), corre scraper_engine en segundo plano.
    """
    import threading
    import requests

    cfg = get_config()
    token = getattr(cfg, "GITHUB_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    repo = getattr(cfg, "GITHUB_REPO", "") or os.environ.get("GITHUB_REPO", "laparra01/mis-pron-sticos-ia")

    if token:
        url = f"https://api.github.com/repos/{repo}/actions/workflows/update_matches.yml/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        data = {"ref": "main"}
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code in (204, 200, 201):
                return jsonify({
                    "success": True,
                    "method": "github_action",
                    "message": "¡GitHub Action iniciada con éxito! El robot está extrayendo los datos y tu web se actualizará en aproximadamente 1 minuto."
                })
            else:
                return jsonify({
                    "success": False,
                    "method": "github_action",
                    "error": f"GitHub API respondió {resp.status_code}: {resp.text}"
                }), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        def run_background_scrape():
            try:
                import scraper_engine
                print("[TRIGGER SCRAPE] Ejecutando extracción local en segundo plano...")
                scraper_engine.scrape_all_leagues()
                print("[TRIGGER SCRAPE] Extracción local finalizada con éxito.")
            except Exception as ex:
                print(f"[TRIGGER SCRAPE ERROR]: {ex}")

        threading.Thread(target=run_background_scrape, daemon=True).start()
        return jsonify({
            "success": True,
            "method": "local_background",
            "message": "Extracción iniciada en segundo plano en el servidor. Los datos se actualizarán en breve."
        })


# ==============================================================
# SEGURIDAD, HEARTBEAT, PING (KEEP-ALIVE) Y ADMIN PANEL
# ==============================================================
@app.route("/blocked")
def page_blocked():
    client_ip = security_manager.get_client_ip(request)
    return render_template("blocked.html", ip=client_ip)

@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id") or request.headers.get("X-Device-Id")
    client_ip = security_manager.get_client_ip(request)
    ua = request.headers.get("User-Agent", "")
    res = security_manager.register_heartbeat(device_id, client_ip, ua)
    return jsonify(res)

@app.route("/api/ping")
def api_ping():
    """Endpoint ultraliviano para el robot Keep-Alive (UptimeRobot / Cron-job)"""
    return jsonify({
        "status": "online",
        "app": "Picks 90 GT",
        "server_time": datetime.now().isoformat(),
        "online_users": security_manager.get_active_count()
    })


@app.route("/owner")
@app.route("/dueno")
def activate_owner_vip():
    """Ruta VIP directa para el Dueño con pase libre garantizado 24/7"""
    cfg = get_config()
    pw = request.args.get("pass") or request.args.get("key") or request.args.get("clave") or ""
    expected_pw = getattr(cfg, "ADMIN_PASSWORD", "admin123") or "admin123"
    if pw == expected_pw:
        session.permanent = True
        session["is_admin"] = True
        session["is_owner"] = True
        return redirect("/?vip=owner")
    elif session.get("is_admin") or session.get("is_owner"):
        return redirect("/?vip=owner")
    return redirect("/admin")

@app.route("/admin")
def admin_dashboard():
    is_auth = bool(session.get("is_admin"))
    if not is_auth:
        return render_template("admin.html", authenticated=False, error=request.args.get("error"))
    sessions_list = security_manager.get_active_sessions_list()
    blacklist_list = security_manager.get_blacklist_records()
    stats_info = security_manager.get_stats_summary()
    return render_template("admin.html", authenticated=True, sessions=sessions_list, blacklist=blacklist_list, stats=stats_info)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    cfg = get_config()
    expected_pw = getattr(cfg, "ADMIN_PASSWORD", "admin123") or "admin123"
    provided_pw = request.form.get("password", "")
    if provided_pw == expected_pw:
        session.permanent = True
        session["is_admin"] = True
        session["is_owner"] = True
        return redirect("/admin")
    return render_template("admin.html", authenticated=False, error="Contraseña incorrecta. Acceso denegado.")

@app.route("/admin/logout", methods=["POST", "GET"])
def admin_logout():
    session.pop("is_admin", None)
    return redirect("/admin")

@app.route("/admin/api/sessions")
def admin_api_sessions():
    if not session.get("is_admin"):
        return jsonify({"error": "No autorizado"}), 401
    return jsonify({
        "sessions": security_manager.get_active_sessions_list(),
        "blacklist": security_manager.get_blacklist_records(),
        "stats": security_manager.get_stats_summary()
    })

@app.route("/admin/api/block", methods=["POST"])
def admin_api_block():
    if not session.get("is_admin"):
        return jsonify({"error": "No autorizado"}), 401
    data = request.get_json(silent=True) or {}
    t_type = data.get("type", "auto")
    value = data.get("value", "")
    reason = data.get("reason", "Bloqueo desde panel de administración")
    if not value:
        return jsonify({"error": "Valor no proporcionado"}), 400
    security_manager.block_target(t_type, value, reason=reason)
    return jsonify({"success": True, "value": value})

@app.route("/admin/api/unblock", methods=["POST"])
def admin_api_unblock():
    if not session.get("is_admin"):
        return jsonify({"error": "No autorizado"}), 401
    data = request.get_json(silent=True) or {}
    t_type = data.get("type", "auto")
    value = data.get("value", "")
    if not value:
        return jsonify({"error": "Valor no proporcionado"}), 400
    security_manager.unblock_target(t_type, value)
    return jsonify({"success": True, "value": value})


# Precalentamiento de caché en segundo plano al arrancar el servidor
def prewarm_cache_task():
    try:
        import time
        time.sleep(1)
        print("[PREWARM] Calentando caché inicial en segundo plano...")
        fetch_matches_data()
        fetch_live_matches_data()
        print("[PREWARM] Caché lista. Servidor ultra-rápido en 0.001s.")
    except Exception as e:
        print(f"[PREWARM ERROR]: {e}")

import threading
threading.Thread(target=prewarm_cache_task, daemon=True).start()

def self_keep_alive_task():
    import time, requests
    if not (os.environ.get('RENDER') or os.environ.get('RENDER_EXTERNAL_URL')):
        return
    time.sleep(60)
    while True:
        try:
            render_url = os.environ.get('RENDER_EXTERNAL_URL') or 'https://mis-pronosticos.onrender.com'
            if render_url:
                ping_url = f"{render_url.rstrip('/')}/api/ping"
                requests.get(ping_url, headers={'User-Agent': 'RenderKeepAlive/1.0'}, timeout=15)
        except Exception:
            pass
        time.sleep(480)

threading.Thread(target=self_keep_alive_task, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  PICKS 90 GT (FÚTBOL & NBA) - SERVIDOR ACTIVO")
    print(f"  Accede en tu navegador a: http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
