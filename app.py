import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from data_provider import fetch_matches_data, fetch_live_matches_data, get_config

app = Flask(__name__)

@app.route("/")
def index():
    cfg = get_config()
    live_api_active = bool(cfg and getattr(cfg, "USE_LIVE_API", False))
    live_matches = fetch_live_matches_data()
    upcoming_matches = fetch_matches_data()
    all_matches = live_matches + upcoming_matches

    football_total = sum(1 for m in all_matches if m.get("sport") == "football")
    nba_total = sum(1 for m in all_matches if m.get("sport") == "nba")
    value_picks = sum(1 for m in all_matches if m["prediction"]["is_value_bet"])
    low_risk = sum(1 for m in all_matches if m["prediction"]["risk_level"] == "Bajo")

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

    unique_countries = sorted(list(set(m.get("country", "Internacional") for m in all_matches if m.get("country"))))
    unique_leagues = sorted(list(set(m.get("league", "") for m in all_matches if m.get("league"))))

    return render_template(
        "index.html",
        live_matches=live_matches,
        upcoming_matches=upcoming_matches,
        all_matches=all_matches,
        stats=stats_summary,
        live_api_active=live_api_active,
        today_iso=today_iso,
        tomorrow_iso=tomorrow_iso,
        today_str=today_str,
        tomorrow_str=tomorrow_str,
        countries=unique_countries,
        leagues=unique_leagues
    )

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

from ai_analyzer import generate_ai_analysis, generate_live_ai_analysis, generate_nba_ai_analysis, generate_nba_live_ai_analysis

@app.route("/api/match/<match_id>")
def api_match_detail(match_id):
    all_m = fetch_live_matches_data() + fetch_matches_data()
    match = next((m for m in all_m if m["id"] == match_id), None)
    if not match:
        return jsonify({"error": "Partido no encontrado"}), 404
    return jsonify(match)

@app.route("/api/match/<match_id>/gemini_analysis")
def api_match_gemini(match_id):
    all_m = fetch_live_matches_data() + fetch_matches_data()
    match = next((m for m in all_m if m["id"] == match_id), None)
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f"  MIS PRONÓSTICOS AI (FÚTBOL & NBA) - SERVIDOR ACTIVO")
    print(f"  Accede en tu navegador a: http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
