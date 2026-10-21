with open("prediction_engine.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """    if current_a > 0:
        pct_away_score_live = 100.0
    else:
        pct_away_score_live = round(max(1.0, min(99.0, (1.0 - math.exp(-mu_rem)) * 100)), 1)

    return {"""

replacement = """    if current_a > 0:
        pct_away_score_live = 100.0
    else:
        pct_away_score_live = round(max(1.0, min(99.0, (1.0 - math.exp(-mu_rem)) * 100)), 1)

    projections_matrix = calculate_projections_matrix(
        home_stats=home_stats,
        away_stats=away_stats,
        lambda_home=round(float(home_stats.get("attack", 1.5) or 1.5), 2),
        mu_away=round(float(away_stats.get("attack", 1.2) or 1.2), 2)
    )

    return {"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open("prediction_engine.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Added projections_matrix to calculate_live_probabilities.")
else:
    print("ERROR: Target not found.")

