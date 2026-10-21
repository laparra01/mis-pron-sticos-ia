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
                    "maxOutputTokens": 1024
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
    proj_corners = float(prediction.get('projected_corners', 9.5) or 9.5)

    def calc_corner_tail_inline(lam, min_k):
        import math
        s = 0.0
        for k in range(min_k, 35):
            s += (math.exp(-lam) * (lam ** k)) / math.factorial(k)
        return round(min(0.99, max(0.01, s)) * 100, 1)

    # Cálculo dinámico exacto de Over 8.5 córners (k >= 9) y Over 9.5 córners (k >= 10)
    prob_corners = prediction.get('pct_corners_over')
    if prob_corners is None or prob_corners == 55.0:
        prob_corners = calc_corner_tail_inline(proj_corners, 9)
    else:
        prob_corners = float(prob_corners)

    prob_corners_95 = prediction.get('pct_corners_over_95')
    if prob_corners_95 is None:
        prob_corners_95 = calc_corner_tail_inline(proj_corners, 10)
    else:
        prob_corners_95 = float(prob_corners_95)

    proj_cards = prediction.get('projected_cards', 4.5)
    pick7 = next((p for p in prediction.get('seven_predictions', []) if p.get('id') == 7 or 'Tarjetas' in p.get('market', '')), {})
    friction_idx = pick7.get('friction_index', 'Fricción Moderada')

    h_c_stats = match_data.get('h2h', {}).get('home_corner_stats', {})
    a_c_stats = match_data.get('h2h', {}).get('away_corner_stats', {})
    h_y = h_c_stats.get('yellow_cards_avg_home') or h_c_stats.get('yellow_cards_avg') or 2.1
    a_y = a_c_stats.get('yellow_cards_avg_away') or a_c_stats.get('yellow_cards_avg') or 2.3
    h_f = h_c_stats.get('fouls_avg_home') or h_c_stats.get('fouls_avg') or 11.5
    a_f = a_c_stats.get('fouls_avg_away') or a_c_stats.get('fouls_avg') or 12.0

    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    pick = prediction.get('recommended_pick', 'Victoria Local')
    conf = prediction.get('confidence', 60.0)
    top_score = prediction.get('top_scores', [{}])[0].get('score', '2-1') if prediction.get('top_scores') else "2-1"

    if proj_corners >= 10.2:
        mercado_rec = "Más de 9.5 córners"
        prob_rec = prob_corners_95
    elif proj_corners >= 8.5:
        mercado_rec = "Más de 8.5 córners"
        prob_rec = prob_corners
    else:
        mercado_rec = "Menos de 9.5 córners"
        prob_rec = round(100.0 - prob_corners_95, 1)

    analisis_cr = f"El modelo proyecta una línea de {proj_corners} tiros de esquina totales ({prob_corners}% para Más de 8.5 córners, con mayor valor matemático en '{mercado_rec}' al {prob_rec}%), impulsado por la vocación ofensiva por bandas de {home} y las transiciones de {away}."

    tot_fouls = round(float(h_f) + float(a_f), 1)
    ref = match_data.get('referee')
    ref_desc = ""
    if ref and isinstance(ref, dict) and ref.get('name'):
        ref_desc = f" Árbitro oficial: {ref.get('name')} ({ref.get('country', '')}), perfil '{ref.get('rigor_level')}', promedia {ref.get('yellow_cards_per_match')} amarillas/partido y {ref.get('fouls_per_match')} faltas/partido."

    if proj_cards >= 5.2 or tot_fouls >= 27:
        analisis_tf = f"Duelo catalogado bajo el índice de '{friction_idx}' con {proj_cards} tarjetas y {tot_fouls} faltas combinadas proyectadas. La intensidad física en zonas de recuperación será elevada, con {home} promediando {h_y} amarillas de local frente a {a_y} de {away} de visita, lo que abre gran valor en líneas Over de amonestaciones (+4.5)."
    elif proj_cards >= 3.9:
        analisis_tf = f"Compromiso con índice de '{friction_idx}'. Se proyectan {proj_cards} amonestaciones totales y {tot_fouls} faltas combinadas. El duelo en la medular entre {home} ({h_y} tarjetas de local) y {away} ({a_y} de visita) sugiere un encuentro de fricción controlada con alta probabilidad para superar la línea de 3.5 tarjetas."
    else:
        analisis_tf = f"Encuentro calificado bajo el índice de '{friction_idx}' con una proyección moderada de {proj_cards} tarjetas y {tot_fouls} faltas. Ambos clubes se caracterizan por una presión limpia y pocas infracciones tácticas ({home} {h_y} tarjetas de local vs {a_y} de {away}), perfilando valor en líneas Under de tarjetas disciplinarias."

    if ref and isinstance(ref, dict) and ref.get('name'):
        analisis_tf += f" Designación arbitral: {ref.get('name')} ({ref.get('yellow_cards_per_match')} 🟨/partido - {ref.get('rigor_level')})."

    # Extracción de proyecciones multivariables Top 10 para Gemini AI
    mat = prediction.get('projections_matrix') or {}
    mat_sum = mat.get('summary') or {}
    top_ft = mat_sum.get('top_ft') or (prediction.get('top_scores') and f"{prediction['top_scores'][0]['score']} ({prediction['top_scores'][0]['prob']}%)") or f"{top_score} (12.0%)"
    top_ht = mat_sum.get('top_ht') or "0-0 (28.5%)"
    top_shots = mat_sum.get('top_shots') or "9-7 (2.1%)"
    top_sot = mat_sum.get('top_sot') or "4-3 (4.3%)"
    top_c = mat_sum.get('top_corners') or f"{round(proj_corners*0.55)}-{round(proj_corners*0.45)} (3.5%)"
    top_y = mat_sum.get('top_cards') or f"{round(proj_cards*0.5)}-{round(proj_cards*0.5)} (7.2%)"

    analisis_matriz_fallback = (
        f"Lectura Multivariable Algorítmica: La matriz proyecta como escenario central a tiempo completo el marcador {top_ft}, "
        f"precedido por una primera mitad de volumen táctico contenido con marcador más probable {top_ht}. "
        f"En la fase de finalización, se proyectan {top_shots} en disparos totales y {top_sot} a portería, confirmando una tasa de "
        f"conversión ofensiva enfocada. El asedio por las bandas proyecta {top_c} en saques de esquina, mientras que la fricción en la medular "
        f"refleja una disputa rigurosa con {top_y} en amonestaciones."
    )

    if force_gemini:
        prompt = f"""
Actúa como analista deportivo experto para predicciones de fútbol (estilo 'Mis Pronósticos AI').
Analiza este partido con rigor táctico y actualidad de plantillas:
Partido: {match_data.get('home_team')} vs {match_data.get('away_team')} (Liga: {match_data.get('league')})
Goles esperados: Local {prediction.get('lambda_home')} - Visitante {prediction.get('mu_away')}
Probabilidades: Local {prediction.get('prob_home')}%, Empate {prediction.get('prob_draw')}%, Visitante {prediction.get('prob_away')}%
Over 2.5: {prediction.get('prob_over_25')}%, Ambos marcan: {prediction.get('prob_btts')}%
Córners proyectados: {proj_corners} (Probabilidad Más de 8.5 Córners: {prob_corners}%)
Tarjetas proyectadas: {proj_cards} amonestaciones totales (Índice de Fricción: {friction_idx}). {match_data.get('home_team')} promedia {h_y} amarillas de local; {match_data.get('away_team')} promedia {a_y} de visita ({tot_fouls} faltas combinadas estimadas).{ref_desc}
Pronóstico Principal: {prediction.get('recommended_pick')} ({prediction.get('confidence')}%)

Matriz Multivariable Top 10 Proyecciones (Poisson Bivariado & Covarianza Dinámica):
• Marcador FT más probable (FTHG-FTAG): {top_ft}
• Marcador 1er Tiempo más probable (HTHG-HTAG): {top_ht}
• Disparos Totales más probables (HS-AS): {top_shots}
• Disparos al Arco más probables (HST-AST): {top_sot}
• Córners más probables (HC-AC): {top_c}
• Tarjetas Amarillas más probables (HY-AY): {top_y}

Devuelve ÚNICAMENTE este formato JSON sin texto antes ni después:
{{
  "resumen": "Resumen ejecutivo táctico en 1 frase directa",
  "justificacion_estadistica": "Explicación del xG, ritmo de posesión y probabilidades",
  "analisis_corners_remates": "Proyección y lectura táctica del mercado de córners ({proj_corners} córners esperados) y volumen de remates",
  "analisis_tarjetas_friccion": "Análisis táctico y lectura profunda del mercado disciplinario basada en las {proj_cards} tarjetas proyectadas, el índice de fricción ({friction_idx}), la rigurosidad en la disputa física ({tot_fouls} faltas combinadas estimadas) y la probabilidad de amonestaciones",
  "analisis_matriz_gemini": "Análisis táctico y cuantitativo de la matriz multivariable de proyecciones (FTHG-FTAG, HTHG-HTAG, HS-AS, HST-AST, HC-AC, HY-AY). Interpreta la relación entre disparos totales vs al arco (conversión), la correlación con córners y tarjetas, y el ritmo proyectado del primer tiempo frente al resultado final",
  "factor_clave": "Duelo individual o clave táctica en la cancha",
  "advertencia_riesgo": "Escenario específico que complicaría el pronóstico",
  "marcador_sugerido": "{top_score}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            if not ai_result.get("analisis_tarjetas_friccion"):
                ai_result["analisis_tarjetas_friccion"] = analisis_tf
            if not ai_result.get("analisis_corners_remates"):
                ai_result["analisis_corners_remates"] = analisis_cr
            if not ai_result.get("analisis_matriz_gemini"):
                ai_result["analisis_matriz_gemini"] = analisis_matriz_fallback
            return ai_result

    # Fallback analítico avanzado

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
        "analisis_corners_remates": analisis_cr,
        "analisis_tarjetas_friccion": analisis_tf,
        "analisis_matriz_gemini": analisis_matriz_fallback,
        "factor_clave": factor,
        "advertencia_riesgo": advertencia,
        "marcador_sugerido": top_score,
        "powered_by": "Motor Analítico Poisson Cuantitativo",
        "is_gemini": False
    }

def generate_live_ai_analysis(match_data: dict, live_pred: dict, live_stats: dict, force_gemini: bool = False) -> dict:
    """
    Análisis En Vivo para Fútbol con Google Gemini AI.
    Incluye diagnóstico en tiempo real de tiros a puerta, tiros totales y córners.
    """
    home = match_data.get('home_team', 'Local')
    away = match_data.get('away_team', 'Visitante')
    is_halftime = bool(match_data.get('is_halftime', False) or live_pred.get('is_halftime', False))
    minute = 45 if is_halftime else live_pred.get('minute', 45)
    time_label = "DESCANSO / MEDIO TIEMPO (HT)" if is_halftime else f"Minuto {minute}'"
    score = live_pred.get('current_score', '0-0')
    pick = live_pred.get('recommended_pick', 'Victoria Local')
    poss_h = live_stats.get('possession_home', 50)
    shots_h = live_stats.get('shots_on_target_home', 0)
    shots_a = live_stats.get('shots_on_target_away', 0)
    tot_shots_h = live_stats.get('total_shots_home', max(shots_h, 0))
    tot_shots_a = live_stats.get('total_shots_away', max(shots_a, 0))
    corners_h = live_stats.get('corners_home', 0)
    corners_a = live_stats.get('corners_away', 0)
    tot_corners = corners_h + corners_a
    yellow_h = live_stats.get('yellow_cards_home', 0)
    yellow_a = live_stats.get('yellow_cards_away', 0)
    red_h = live_stats.get('red_cards_home', 0)
    red_a = live_stats.get('red_cards_away', 0)
    tot_cards = yellow_h + yellow_a + (red_h + red_a) * 2

    eff_h = round((shots_h / max(tot_shots_h, 1)) * 100) if tot_shots_h > 0 else 0
    eff_a = round((shots_a / max(tot_shots_a, 1)) * 100) if tot_shots_a > 0 else 0

    if tot_corners == 0:
        corner_read = f"Trámite trabado en mediocampo sin profundidad por bandas (0 saques de esquina registrados hasta el momento)."
    elif corners_h > corners_a:
        corner_read = f"{home} vuelca su juego por las bandas sumando {corners_h} saque(s) de esquina (frente a {corners_a} de {away})."
    elif corners_a > corners_h:
        corner_read = f"{away} gana profundidad en tres cuartos de cancha sumando {corners_a} córner(s) a favor (frente a {corners_h} de {home})."
    else:
        corner_read = f"Juego disputado en el carril central con paridad en tiros de esquina ({corners_h} vs {corners_a})."

    rem_time = 45 if is_halftime else max(1, 90 - minute)
    proj_corners = round(tot_corners + max(0.5, (rem_time / 90.0) * max(1.0, tot_corners)), 1)

    time_context = "al descanso (primer tiempo)" if is_halftime else f"al minuto {minute}'"
    analisis_cr = (
        f"{corner_read} "
        f"En remates, {home} registra {shots_h}/{tot_shots_h} a puerta ({eff_h}% de puntería) frente a {shots_a}/{tot_shots_a} ({eff_a}%) de {away}. "
        f"Con {tot_corners} córners acumulados {time_context}, el modelo proyecta una línea final de {proj_corners} córners."
    )

    if tot_cards >= 4 or (red_h + red_a) > 0:
        analisis_live_cards = f"Clima de alta fricción disciplinaria: se acumulan {tot_cards} tarjetas en el encuentro ({yellow_h} amarillas y {red_h} rojas para {home}, frente a {yellow_a} amarillas y {red_a} rojas para {away}). Las disputas al límite y las reiteradas faltas tácticas incrementan fuertemente el riesgo de nuevas amonestaciones o expulsión en el cierre."
    elif tot_cards >= 2:
        analisis_live_cards = f"Fricción moderada en juego con {tot_cards} amonestaciones registradas ({yellow_h} para {home} y {yellow_a} para {away}). El árbitro mantiene el control del choque, aunque el desgaste físico hacia los últimos minutos propiciará infracciones para frenar contragolpes."
    else:
        analisis_live_cards = f"Trámite de juego limpio y baja tensión hasta el momento con apenas {tot_cards} tarjeta(s) mostrada(s) ({yellow_h} para {home} vs {yellow_a} para {away}). Encuentro fluido con escasa fricción y sin intervenciones rigurosas del juez principal."

    if force_gemini:
        prompt = f"""
Actúa como analista deportivo experto en apuestas y táctica en vivo (estilo 'Mis Pronósticos AI').
Partido en juego: {home} vs {away} (Marcador {score}, {time_label})
Estadísticas oficiales en tiempo real:
- Posesión de balón: {home} {poss_h}% vs {away} {100-poss_h}%
- Remates a puerta: {home} {shots_h} vs {away} {shots_a}
- Tiros totales: {home} {tot_shots_h} vs {away} {tot_shots_a}
- Saques de esquina (córners): {home} {corners_h} vs {away} {corners_a} (Total acumulado: {tot_corners} córners)
- Amonestaciones (tarjetas): {home} {yellow_h} amarillas/{red_h} rojas vs {away} {yellow_a} amarillas/{red_a} rojas (Total: {tot_cards} amonestaciones)
- Pick principal en vivo: {pick} ({live_pred.get('confidence', 60)}%)
{"- ESTADO ESPECIAL: El partido se encuentra en el DESCANSO / MEDIO TIEMPO (HT). Los equipos están en vestuarios y restan los 45 minutos del segundo tiempo." if is_halftime else ""}

REGLAS CRÍTICAS DE FIDELIDAD NUMÉRICA (OBLIGATORIAS):
1. Debes respetar RIGUROSAMENTE los datos numéricos reales provistos arriba.
2. Si un equipo tiene 0 tiros a puerta o 0 saques de esquina, indica textualmente y sin rodeos "0 tiros a puerta" o "0 saques de esquina". NO inventes que hubo más córners, remates a puerta o asedio ofensivo de los que realmente indican las estadísticas oficiales.
3. En 'analisis_corners_remates', cita exactamente las cifras provistas ({shots_h}/{tot_shots_h} vs {shots_a}/{tot_shots_a} remates, y {corners_h} vs {corners_a} córners) y analiza tácticamente lo que estos números exactos reflejan en el terreno de juego.
{"4. Si el partido está en descanso, habla del descanso / medio tiempo y de la segunda mitad que está por jugarse." if is_halftime else ""}

Devuelve ÚNICAMENTE este formato JSON sin texto antes ni después:
{{
  "resumen": "Diagnóstico en 1 frase directa y veraz del momento del partido",
  "justificacion_estadistica": "Explicación fiel basada en los {shots_h} vs {shots_a} remates a puerta y la posesión de balón",
  "analisis_corners_remates": "Lectura táctica precisa citando fielmente remates ({shots_h}/{tot_shots_h} vs {shots_a}/{tot_shots_a}) y córners ({corners_h} vs {corners_a} córners acumulados)",
  "analisis_tarjetas_friccion": "Lectura disciplinaria en vivo citando las {yellow_h} amarillas/{red_h} rojas de {home} y {yellow_a} amarillas/{red_a} rojas de {away} ({tot_cards} tarjetas acumuladas), el clima de tensión sobre el césped y la proyección disciplinaria para el tramo restante",
  "factor_clave": "Quién domina el ritmo del partido según las estadísticas reales",
  "advertencia_riesgo": "Riesgo táctico en el tramo final",
  "marcador_sugerido": "{score}"
}}
"""
        ai_result = call_gemini_api(prompt)
        if ai_result:
            if not ai_result.get("analisis_tarjetas_friccion"):
                ai_result["analisis_tarjetas_friccion"] = analisis_live_cards
            if not ai_result.get("analisis_corners_remates"):
                ai_result["analisis_corners_remates"] = analisis_cr
            return ai_result

    # Fallback analítico cuantitativo en vivo

    if is_halftime:
        resumen = f"Descanso / Medio Tiempo ({score}): {pick} con {live_pred.get('confidence', 60)}% de probabilidad proyectada para la 2ª mitad."
        justificacion = (
            f"Al medio tiempo con el marcador en {score} y 45 minutos por disputar en la 2ª mitad, el modelo cuantitativo recalculó la expectativa de goles. "
            f"{home} registra {poss_h}% de posesión y {shots_h} remates a puerta (vs {shots_a} de {away}). "
            f"La probabilidad en vivo para victoria local es de {live_pred.get('prob_home', 50)}%, empate {live_pred.get('prob_draw', 25)}% y visitante {live_pred.get('prob_away', 25)}%."
        )
    else:
        resumen = f"Minuto {minute}' ({score}): {pick} con {live_pred.get('confidence', 60)}% de probabilidad restante calculada."
        justificacion = (
            f"Con el marcador en {score} y {max(1, 90 - minute)} minutos por disputar, el modelo recalculó la expectativa de goles. "
            f"{home} registra {poss_h}% de posesión y {shots_h} remates a puerta (vs {shots_a} de {away}). "
            f"La probabilidad en vivo para victoria local es de {live_pred.get('prob_home', 50)}%, empate {live_pred.get('prob_draw', 25)}% y visitante {live_pred.get('prob_away', 25)}%."
        )
    factor = f"Momentum ofensivo: {home if poss_h >= 50 else away} domina la posesión ({poss_h}% vs {100-poss_h}%) con {shots_h} vs {shots_a} tiros a puerta."
    advertencia = f"En los últimos minutos aumenta el riesgo por desorden físico. Probabilidad de no más goles: {live_pred.get('prob_no_more_goals', 40)}%."

    return {
        "resumen": resumen,
        "justificacion_estadistica": justificacion,
        "analisis_corners_remates": analisis_cr,
        "analisis_tarjetas_friccion": analisis_live_cards,
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
