import os
import requests
import json
try:
    import config
except ImportError:
    config = None

def get_gemini_key() -> str:
    """Obtiene la clave de Gemini desde config.py o variable de entorno."""
    return getattr(config, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")

_ai_cache = {}

def call_gemini_api(prompt: str) -> dict:
    """
    Envía el prompt a la API de Google Gemini (gemini-3.5-flash-lite con fallback a gemini-flash-latest)
    y retorna la estructura de análisis en formato diccionario.
    """
    api_key = get_gemini_key()
    if not api_key:
        return None

    # Cache en memoria para respuestas ultra-rápidas
    cache_key = abs(hash(prompt.strip()))
    if cache_key in _ai_cache:
        return _ai_cache[cache_key]

    models_to_try = ["gemini-3.5-flash-lite", "gemini-flash-latest"]
    
    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.35,
                    "maxOutputTokens": 600
                }
            }
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                    elif raw_text.startswith("```"):
                        raw_text = raw_text.split("```")[1].split("```")[0].strip()
                    parsed = json.loads(raw_text)
                    parsed["powered_by"] = f"Google Gemini AI ({model_name})"
                    parsed["is_gemini"] = True
                    _ai_cache[cache_key] = parsed
                    return parsed
        except Exception:
            continue

    return None


def generate_ai_analysis(match_data: dict, prediction: dict, force_gemini: bool = False) -> dict:
    """
    Análisis Pre-Match para Fútbol con Google Gemini AI.
    """
    if force_gemini:
        prompt = f"""
Actúa como analista deportivo experto para predicciones de fútbol (estilo 'Mis Pronósticos AI').
Analiza este partido con rigor táctico y actualidad de plantillas:
Partido: {match_data.get('home_team')} vs {match_data.get('away_team')} (Liga: {match_data.get('league')})
Goles esperados: Local {prediction.get('lambda_home')} - Visitante {prediction.get('mu_away')}
Probabilidades: Local {prediction.get('prob_home')}%, Empate {prediction.get('prob_draw')}%, Visitante {prediction.get('prob_away')}%
Over 2.5: {prediction.get('prob_over_25')}%, Ambos marcan: {prediction.get('prob_btts')}%
Pronóstico Principal: {prediction.get('recommended_pick')} ({prediction.get('confidence')}%)

Devuelve ÚNICAMENTE este formato JSON sin texto antes ni después:
{{
  "resumen": "Resumen ejecutivo táctico en 1 frase directa",
  "justificacion_estadistica": "Explicación del xG, ritmo de posesión y probabilidades",
  "factor_clave": "Duelo individual o clave táctica en la cancha",
  "advertencia_riesgo": "Escenario específico que complicaría el pronóstico",
  "marcador_sugerido": "{prediction.get('top_scores', [{}])[0].get('score', '2-1') if prediction.get('top_scores') else '2-1'}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            return ai_result

    # Fallback analítico avanzado
    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    pick = prediction.get('recommended_pick', 'Victoria Local')
    conf = prediction.get('confidence', 60.0)
    top_score = prediction.get('top_scores', [{}])[0].get('score', '2-1') if prediction.get('top_scores') else "2-1"

    if "Victoria Local" in pick or "Gana Local" in pick:
        resumen = f"Alta probabilidad para {home} aprovechando el factor localía y mayor producción ofensiva ({prediction.get('lambda_home', 2.1)} goles esperados)."
        justificacion = f"El modelo de Poisson refleja {prediction.get('prob_home', 55)}% a favor de {home}. Su solvencia defensiva reduce las opciones de {away}."
        factor = f"Efectividad en el primer tercio del partido y dominio de posesión de {home}."
        advertencia = f"Un bloque bajo de {away} buscando contragolpes directos."
    elif "Victoria Visitante" in pick or "Gana Visitante" in pick:
        resumen = f"{away} se posiciona como favorito sólido debido a su rendimiento de visita superior al promedio."
        justificacion = f"Con un {prediction.get('prob_away', 55)}% de probabilidad y {prediction.get('mu_away', 1.8)} goles esperados, {away} exhibe mayor pegada."
        factor = f"Superioridad técnica en transiciones rápidas del equipo visitante."
        advertencia = f"Desgaste físico por calendario apretado en {away}."
    elif "Más de 2.5" in pick or prediction.get('prob_over_25', 50) > 55:
        resumen = f"Duelo con perfil ofensivo abierto ({prediction.get('prob_over_25', 60)}% de probabilidad para más de 2.5 goles)."
        justificacion = f"Ambos combinan {round(prediction.get('lambda_home', 1.8) + prediction.get('mu_away', 1.4), 2)} goles esperados y {prediction.get('prob_btts', 55)}% de ambos marcan."
        factor = f"Defensas permisivas que conceden espacios en transiciones."
        advertencia = f"Falta de puntería en los primeros 45 minutos."
    else:
        resumen = f"Partido equilibrado con tendencia a marcador cerrado ({conf}% de confianza en {pick})."
        justificacion = f"Paridad técnica con probabilidad de empate de {prediction.get('prob_draw', 30)}%."
        factor = f"Estructuras tácticas conservadoras y prioridad por el orden en mediocampo."
        advertencia = f"Una tarjeta roja temprana que rompa el orden posicional."

    return {
        "resumen": resumen,
        "justificacion_estadistica": justificacion,
        "factor_clave": factor,
        "advertencia_riesgo": advertencia,
        "marcador_sugerido": top_score,
        "powered_by": "Motor Analítico Poisson Cuantitativo",
        "is_gemini": False
    }

def generate_live_ai_analysis(match_data: dict, live_pred: dict, live_stats: dict, force_gemini: bool = False) -> dict:
    """
    Análisis En Vivo para Fútbol con Google Gemini AI.
    """
    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    minute = live_pred.get('minute', 45)
    score = live_pred.get('current_score', '0-0')
    pick = live_pred.get('recommended_pick', 'Victoria Local')
    poss_h = live_stats.get('possession_home', 50)
    shots_h = live_stats.get('shots_on_target_home', 3)
    shots_a = live_stats.get('shots_on_target_away', 3)

    if force_gemini:
        prompt = f"""
Actúa como analista deportivo en vivo (estilo 'Mis Pronósticos AI').
Partido en juego: {home} vs {away} (Marcador {score}, Minuto {minute}')
Posesión: {home} {poss_h}% vs {away} {100-poss_h}%. Tiros a puerta: {shots_h} vs {shots_a}.
Pick en vivo: {pick} ({live_pred.get('confidence', 60)}%).

Devuelve ÚNICAMENTE este JSON:
{{
  "resumen": "Diagnóstico en 1 frase del minuto actual",
  "justificacion_estadistica": "Explicación del ritmo en juego y expectativa restante",
  "factor_clave": "Quién domina el momentum táctico y control del juego",
  "advertencia_riesgo": "Riesgo en el cierre del partido",
  "marcador_sugerido": "{score}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            return ai_result

    resumen = f"Minuto {minute}' ({score}): {pick} con {live_pred.get('confidence', 60)}% de probabilidad restante calculada."
    justificacion = (
        f"Con el marcador en {score} y {max(1, 90 - minute)} minutos por disputar, el modelo recalculó la expectativa de goles. "
        f"{home} registra {poss_h}% de posesión y {shots_h} remates a puerta (vs {shots_a} de {away}). "
        f"La probabilidad en vivo para victoria local es de {live_pred.get('prob_home', 50)}%, empate {live_pred.get('prob_draw', 25)}% y visitante {live_pred.get('prob_away', 25)}%."
    )
    factor = f"Momentum ofensivo: {home if poss_h >= 50 else away} domina el mediocampo y la presión alta."
    advertencia = f"En los últimos minutos aumenta el riesgo por desorden físico. Probabilidad de no más goles: {live_pred.get('prob_no_more_goals', 40)}%."

    return {
        "resumen": resumen,
        "justificacion_estadistica": justificacion,
        "factor_clave": factor,
        "advertencia_riesgo": advertencia,
        "marcador_sugerido": f"Actual {score}",
        "powered_by": "Motor Analítico Poisson Cuantitativo",
        "is_gemini": False
    }

def generate_nba_ai_analysis(match_data: dict, prediction: dict, force_gemini: bool = False) -> dict:
    """
    Análisis Pre-Match para NBA con Google Gemini AI.
    """
    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    pts_h = prediction.get('projected_pts_home', 115)
    pts_a = prediction.get('projected_pts_away', 112)
    total = prediction.get('total_points', 227)
    q_info = prediction.get("quarters_breakdown", {})
    q1_win = q_info.get("q1", {}).get("predicted_winner", "Local")

    if force_gemini:
        prompt = f"""
Actúa como analista de baloncesto NBA experto (estilo 'Mis Pronósticos AI').
Partido NBA: {home} vs {away}
Proyección de puntos: {home} {pts_h} - {pts_a} {away} (Total: {total} pts).
Línea Over/Under: {prediction.get('over_under_line', 226.5)} pts.
Pick Principal: {prediction.get('recommended_pick')} ({prediction.get('confidence', 60)}%).

Devuelve ÚNICAMENTE este formato JSON:
{{
  "resumen": "Resumen ejecutivo del matchup NBA en 1 frase",
  "justificacion_estadistica": "Explicación de ratings ofensivos/defensivos, pace y tiros de campo",
  "factor_clave": "Duelo clave (triples, pintura o rebotes)",
  "advertencia_riesgo": "Riesgo de rotación o faltas de estrellas",
  "marcador_sugerido": "{round(pts_h)} - {round(pts_a)}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            return ai_result

    resumen = (
        f"Proyección NBA: {home} {pts_h} - {pts_a} {away} ({total} pts totales). "
        f"Ganador 1Q: {q1_win} | Pick Principal: {prediction.get('recommended_pick')}."
    )
    justificacion = (
        f"El algoritmo evaluó el Offensive Rating de {home} frente a la defensa de {away}, "
        f"arrojando {prediction.get('prob_home', 55)}% para el local y {prediction.get('prob_away', 45)}% para el visitante. "
        f"Línea Over/Under: {prediction.get('over_under_line', 226.5)} puntos. "
        f"El Q1 y la 1ª Mitad se proyectan con titulares; los cuartos Q2, Q3 y Q4 se actualizarán en vivo con el flujo."
    )
    factor = f"Ritmo de posesiones (Pace), eficacia en triples y quinteto titular en el 1Q."
    advertencia = f"Gestión de minutos de estrellas y porcentaje de tiros libres en el cierre."

    return {
        "resumen": resumen,
        "justificacion_estadistica": justificacion,
        "factor_clave": factor,
        "advertencia_riesgo": advertencia,
        "marcador_sugerido": f"{round(pts_h)} - {round(pts_a)}",
        "powered_by": "Motor Analítico Poisson Cuantitativo",
        "is_gemini": False
    }

def generate_nba_live_ai_analysis(match_data: dict, live_pred: dict, live_stats: dict, force_gemini: bool = False) -> dict:
    """
    Análisis En Vivo para NBA con Cuartos y Mitades con Google Gemini AI.
    """
    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    q = live_pred.get('quarter', 'Q3')
    score = live_pred.get('current_score', '80-75')
    pick = live_pred.get('recommended_pick', 'Victoria Local')
    fg_h = live_stats.get('fg_pct_home', 45)
    fg_a = live_stats.get('fg_pct_away', 45)

    if force_gemini:
        prompt = f"""
Actúa como analista NBA en vivo durante el partido.
Juego en vivo: {home} vs {away} ({q}, Marcador {score}).
Proyección final: {live_pred.get('projected_final')} ({live_pred.get('projected_total')} pts).
Tiros de campo FG: {home} {fg_h}% vs {away} {fg_a}%.
Pick en vivo: {pick} ({live_pred.get('confidence', 60)}%).

Devuelve ÚNICAMENTE este formato JSON:
{{
  "resumen": "Lectura en 1 frase del momento actual en {q}",
  "justificacion_estadistica": "Explicación del ritmo de tiro y ganador de cuartos restantes",
  "factor_clave": "Control de rebotes y eficacia en triples",
  "advertencia_riesgo": "Rachas rápidas que alteren el clutch",
  "marcador_sugerido": "{live_pred.get('projected_final', score)}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            return ai_result

    q_break = live_pred.get("quarters_breakdown", {})
    q3_win = q_break.get("q3", {}).get("winner", "Local")
    q4_win = q_break.get("q4", {}).get("winner", "Local")
    h2_win = q_break.get("second_half", {}).get("winner", "Local")

    resumen = (
        f"{q} ({score}): Proyección final {live_pred.get('projected_final')} ({live_pred.get('projected_total')} pts). "
        f"Tendencia Q3: {q3_win} | Tendencia Q4: {q4_win} | Ganador 2ª Mitad: {h2_win}."
    )
    justificacion = (
        f"Con el marcador en {score} en el {q}, el modelo recalculó la expectativa de cada cuarto restante. "
        f"{home} tira al {fg_h}% de campo vs {fg_a}% de {away}. "
        f"Probabilidad de triunfo final: Local {live_pred.get('prob_home', 50)}% - Visitante {live_pred.get('prob_away', 50)}%."
    )
    factor = f"Efectividad en la pintura, control del rebote y rotación de banca."
    advertencia = f"Rachas rápidas de triples que cambian ventajas en segundos."

    return {
        "resumen": resumen,
        "justificacion_estadistica": justificacion,
        "factor_clave": factor,
        "advertencia_riesgo": advertencia,
        "marcador_sugerido": live_pred.get('projected_final', score),
        "powered_by": "Motor Analítico Poisson Cuantitativo",
        "is_gemini": False
    }
