import os
import json
import time
import math
from datetime import datetime
import importlib

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dream_parleys_cache.json")

def calculate_parley_odds(legs):
    total_odds = 1.0
    for leg in legs:
        odds = float(leg.get("fair_odds", 1.80) or 1.80)
        total_odds *= odds
    return round(total_odds, 2)

def calculate_parley_probability(legs):
    combined_prob = 1.0
    for leg in legs:
        prob = float(leg.get("probability", 55.0) or 55.0) / 100.0
        combined_prob *= prob
    return round(combined_prob * 100.0, 1)

def select_ticket_1_tactical(matches):
    """
    Ticket 1: 🛡️ La Soñadora Táctica (Cuota ~4.50 - 7.50)
    3 selecciones de alta solidez y convicción (prob ~52-65%, cuotas individuales ~1.65 - 2.05)
    """
    candidates = []
    for m in matches:
        pred = m.get("prediction", {})
        sevens = pred.get("seven_predictions", [])
        
        today_iso = datetime.now().strftime("%Y-%m-%d")
        d_display = "Hoy" if m.get("date_iso") == today_iso else m.get("date", "Hoy")
        for p in sevens:
            prob = p.get("probability", 0)
            odds = p.get("fair_odds", 0)
            mkt = p.get("market", "")
            if 50.0 <= prob <= 75.0 and 1.55 <= odds <= 2.20:
                priority = 3 if ("1X2" in mkt or "Doble" in mkt) else (2 if "Goles" in mkt else 1)
                candidates.append({
                    "match_id": m.get("id"),
                    "home_team": m.get("home_team"),
                    "away_team": m.get("away_team"),
                    "league": m.get("league"),
                    "country": m.get("country"),
                    "country_code": m.get("country_code", ""),
                    "league_flag": m.get("league_flag") or m.get("country_flag") or "⚽",
                    "date": d_display,
                    "date_iso": m.get("date_iso", ""),
                    "time": m.get("time", ""),
                    "timestamp": m.get("timestamp") or 0,
                    "market": p.get("market"),
                    "pick": p.get("name"),
                    "probability": prob,
                    "fair_odds": odds,
                    "explanation": p.get("explanation", ""),
                    "priority": priority
                })

    candidates.sort(key=lambda x: (x["priority"], x["probability"]), reverse=True)
    selected = []
    used_teams = set()
    for c in candidates:
        team_key = f"{c['home_team']}_{c['away_team']}"
        if team_key not in used_teams:
            selected.append(c)
            used_teams.add(team_key)
            if len(selected) == 3:
                # Comprobar si alcanzamos la cuota deseada (~4.5 - 7.5)
                cur_odds = calculate_parley_odds(selected)
                if cur_odds >= 4.5:
                    break
            elif len(selected) == 4:
                break

    return selected

def select_ticket_2_goals_corners_cards(matches):
    """
    Ticket 2: ⚡ La Soñadora de Goles, Córners & Fricción (Cuota ~10.00 - 18.00)
    3 a 4 selecciones combinando mercados especiales:
    1 de córners (+9.5 o +8.5), 1 de tarjetas (+4.5 o alta fricción), 1 o 2 de goles (Over 2.5, BTTS SI, etc.)
    """
    corners_candidates = []
    cards_candidates = []
    goals_candidates = []

    for m in matches:
        pred = m.get("prediction", {})
        sevens = pred.get("seven_predictions", [])
        
        today_iso = datetime.now().strftime("%Y-%m-%d")
        d_display = "Hoy" if m.get("date_iso") == today_iso else m.get("date", "Hoy")
        base_info = {
            "match_id": m.get("id"),
            "home_team": m.get("home_team"),
            "away_team": m.get("away_team"),
            "league": m.get("league"),
            "country": m.get("country"),
            "country_code": m.get("country_code", ""),
            "league_flag": m.get("league_flag") or m.get("country_flag") or "⚽",
            "date": d_display,
            "date_iso": m.get("date_iso", ""),
            "time": m.get("time", ""),
            "timestamp": m.get("timestamp") or 0,
        }

        for p in sevens:
            mkt = p.get("market", "")
            odds = float(p.get("fair_odds", 1.80) or 1.80)
            prob = float(p.get("probability", 50.0) or 50.0)

            if "Córners" in mkt and 1.50 <= odds <= 2.50 and prob >= 35.0:
                item = dict(base_info)
                item.update({
                    "market": "Tiros de Esquina",
                    "pick": p.get("name"),
                    "probability": prob,
                    "fair_odds": odds,
                    "explanation": p.get("explanation", "")
                })
                corners_candidates.append(item)
            elif "Tarjetas" in mkt and 1.50 <= odds <= 2.50 and prob >= 35.0:
                item = dict(base_info)
                item.update({
                    "market": "Fricción & Tarjetas",
                    "pick": p.get("name"),
                    "probability": prob,
                    "fair_odds": odds,
                    "explanation": p.get("explanation", "")
                })
                cards_candidates.append(item)
            elif ("2.5" in mkt or "1.5" in mkt or "Ambos" in mkt) and 1.50 <= odds <= 2.50 and prob >= 35.0:
                item = dict(base_info)
                item.update({
                    "market": "Mercado de Goles",
                    "pick": p.get("name"),
                    "probability": prob,
                    "fair_odds": odds,
                    "explanation": p.get("explanation", "")
                })
                goals_candidates.append(item)

    corners_candidates.sort(key=lambda x: x["fair_odds"], reverse=True)
    cards_candidates.sort(key=lambda x: x["fair_odds"], reverse=True)
    goals_candidates.sort(key=lambda x: x["fair_odds"], reverse=True)

    selected = []
    used_teams = set()

    # 1. El mejor de córners
    for c in corners_candidates:
        tk = f"{c['home_team']}_{c['away_team']}"
        if tk not in used_teams:
            selected.append(c)
            used_teams.add(tk)
            break

    # 2. El mejor de tarjetas
    for c in cards_candidates:
        tk = f"{c['home_team']}_{c['away_team']}"
        if tk not in used_teams:
            selected.append(c)
            used_teams.add(tk)
            break

    # 3. Uno o dos de goles para alcanzar ~10.0x - 18.0x
    for c in goals_candidates:
        tk = f"{c['home_team']}_{c['away_team']}"
        if tk not in used_teams:
            selected.append(c)
            used_teams.add(tk)
            cur_odds = calculate_parley_odds(selected)
            if len(selected) >= 3 and cur_odds >= 9.8:
                break
            if len(selected) >= 4:
                break

    # Si aún no alcanza 9.5, buscar patas adicionales en el conjunto combinado
    cur_odds = calculate_parley_odds(selected)
    if cur_odds < 9.5 and len(selected) < 5:
        combined_pool = sorted(goals_candidates + corners_candidates + cards_candidates, key=lambda x: x["fair_odds"], reverse=True)
        for c in combined_pool:
            tk = f"{c['home_team']}_{c['away_team']}"
            if tk not in used_teams:
                selected.append(c)
                used_teams.add(tk)
                cur_odds = calculate_parley_odds(selected)
                if cur_odds >= 9.5 or len(selected) >= 5:
                    break

    return selected[:5]

def select_ticket_3_rompebancas_ultra(matches):
    """
    Ticket 3: 🚀 La Rompe-Bancas Ultra (Cuota ~25.00 - 45.00+)
    3 a 4 selecciones con cuota atractiva y valor matemático:
    - Empates tácticos con paridad esperada (p_draw >= 32.0%)
    - Victorias visitantes o de valor
    - Mercados cuantitativos de alto rendimiento (cuotas >= 1.70 - 2.80)
    """
    candidates = []
    for m in matches:
        pred = m.get("prediction", {})
        h_name = m.get("home_team")
        a_name = m.get("away_team")
        today_iso = datetime.now().strftime("%Y-%m-%d")
        d_display = "Hoy" if m.get("date_iso") == today_iso else m.get("date", "Hoy")
        base_info = {
            "match_id": m.get("id"),
            "home_team": h_name,
            "away_team": a_name,
            "league": m.get("league"),
            "country": m.get("country"),
            "country_code": m.get("country_code", ""),
            "league_flag": m.get("league_flag") or m.get("country_flag") or "⚽",
            "date": d_display,
            "date_iso": m.get("date_iso", ""),
            "time": m.get("time", ""),
            "timestamp": m.get("timestamp") or 0,
        }

        p_draw = pred.get("prob_draw", 28.0)
        p_away = pred.get("prob_away", 30.0)

        # 1. Candidato Empate si hay paridad táctica proyectada
        if 32.0 <= p_draw <= 48.0:
            item = dict(base_info)
            odds = round(100.0 / p_draw, 2)
            item.update({
                "market": "1X2 (Resultado Final)",
                "pick": f"Empate ({h_name} vs {a_name})",
                "probability": p_draw,
                "fair_odds": odds,
                "explanation": f"Alta paridad táctica con {p_draw}% de probabilidad de empate y marcadores proyectados cerrados."
            })
            candidates.append(item)

        # 2. Candidato Victoria Visitante con valor
        if 36.0 <= p_away <= 60.0 and (pred.get("mu_away", 1.0) >= 1.2 or p_away >= 45.0):
            item = dict(base_info)
            odds = round(100.0 / p_away, 2)
            item.update({
                "market": "1X2 (Resultado Final)",
                "pick": f"Victoria Visitante ({a_name})",
                "probability": p_away,
                "fair_odds": odds,
                "explanation": f"Valor subestimado: {a_name} exhibe solvencia ofensiva visitante."
            })
            candidates.append(item)

        # 3. Candidatos de las 7 predicciones cuantitativas con cuota alta (>= 1.70)
        for p in pred.get("seven_predictions", []):
            p_odds = float(p.get("fair_odds", 0) or 0)
            p_prob = float(p.get("probability", 0) or 0)
            if 1.70 <= p_odds <= 2.80 and p_prob >= 35.0:
                item = dict(base_info)
                item.update({
                    "market": p.get("market"),
                    "pick": p.get("name"),
                    "probability": p_prob,
                    "fair_odds": p_odds,
                    "explanation": p.get("explanation", "")
                })
                candidates.append(item)

    # Ordenar buscando cuotas altas
    candidates.sort(key=lambda x: x["fair_odds"], reverse=True)
    selected = []
    used_teams = set()

    # Priorizar hasta 2 empates si existen
    for c in candidates:
        if "Empate" in c["pick"]:
            tk = f"{c['home_team']}_{c['away_team']}"
            if tk not in used_teams:
                selected.append(c)
                used_teams.add(tk)
                if len(selected) == 2:
                    break

    # Rellenar con selecciones de valor hasta alcanzar cuota deseada (~25x - 45x)
    for c in candidates:
        tk = f"{c['home_team']}_{c['away_team']}"
        if tk not in used_teams:
            selected.append(c)
            used_teams.add(tk)
            cur_odds = calculate_parley_odds(selected)
            if len(selected) >= 3 and cur_odds >= 25.0:
                break
            if len(selected) == 4:
                break

    return selected[:4]

def enrich_parleys_with_gemini(ticket_1_legs, ticket_2_legs, ticket_3_legs):
    """
    Consulta a Google Gemini AI para redactar los títulos, lemas y veredictos tácticos.
    """
    try:
        from ai_analyzer import call_gemini_api
        t1_summary = "; ".join([f"{l['home_team']} vs {l['away_team']}: {l['pick']} (Cuota {l['fair_odds']})" for l in ticket_1_legs])
        t2_summary = "; ".join([f"{l['home_team']} vs {l['away_team']}: {l['pick']} ({l['market']}, Cuota {l['fair_odds']})" for l in ticket_2_legs])
        t3_summary = "; ".join([f"{l['home_team']} vs {l['away_team']}: {l['pick']} (Cuota {l['fair_odds']})" for l in ticket_3_legs])

        prompt = f"""
Actúa como analista deportivo de élite y experto en combinadas (parleys) deportivas de 'Mis Pronósticos AI'.
Hemos seleccionado estadísticamente 3 parleys soñadores para el día de hoy:

TICKET 1 - SOÑADORA TÁCTICA (Cuota media ~5x-7x, alta solidez):
{t1_summary}

TICKET 2 - SOÑADORA DE GOLES, CÓRNERS & FRICCIÓN (Cuota ~10x-18x, mercados especiales):
{t2_summary}

TICKET 3 - LA ROMPE-BANCAS ULTRA (Cuota alta ~25x-50x+, gran premio):
{t3_summary}

Devuelve ÚNICAMENTE este formato JSON sin texto antes ni después:
{{
  "ticket_1": {{
    "titulo": "Título llamativo para la Soñadora Táctica (ej. Tridente de Alta Convicción)",
    "lema": "Frase de enganche táctico corta",
    "veredicto_gemini": "Explicación de 2-3 frases de por qué este ticket combina solidez y valor matemático con los datos de hoy"
  }},
  "ticket_2": {{
    "titulo": "Título para la Soñadora de Mercados Especiales (ej. Sinfonía de Córners y Fricción)",
    "lema": "Frase de enganche corta",
    "veredicto_gemini": "Explicación de 2-3 frases de por qué la combinación de bandas, tarjetas e intensidad física sustenta esta cuota"
  }},
  "ticket_3": {{
    "titulo": "Título para La Rompe-Bancas Ultra (ej. El Asalto Maestro de Cuota Gigante)",
    "lema": "Frase de enganche corta",
    "veredicto_gemini": "Explicación de 2-3 frases de por qué, a pesar de ser una cuota enorme, cada una de las patas tiene respaldo de xG y valor positivo"
  }}
}}
"""
        res = call_gemini_api(prompt)
        if res and isinstance(res, dict) and "ticket_1" in res and "ticket_2" in res and "ticket_3" in res:
            return res
    except Exception as e:
        print(f"[PARLEYS GEMINI WARNING]: {e}")
    return None

def build_dream_parleys_package(matches, force_gemini=False):
    """
    Construye el paquete completo con los 3 parleys soñadores diarios.
    Filtra rigurosamente para incluir ÚNICAMENTE partidos de HOY que NO hayan comenzado aún.
    """
    today_iso = datetime.now().strftime("%Y-%m-%d")
    now_ts = time.time()
    
    # 1. Priorizar rigurosamente los partidos de HOY que aún NO hayan comenzado
    today_pending = [
        m for m in matches 
        if m.get("date_iso") == today_iso and ((m.get("timestamp") or 0) >= now_ts - 300 or not m.get("timestamp"))
    ]
    
    if len(today_pending) >= 3:
        source_matches = today_pending
    else:
        # Fallback si hoy ya no quedan suficientes partidos por jugar (ej. madrugada o final del día)
        pending_matches = [
            m for m in matches 
            if (m.get("timestamp") or 0) >= now_ts - 300 or not m.get("timestamp")
        ]
        pending_matches.sort(key=lambda x: (x.get("timestamp") or 9999999999))
        source_matches = pending_matches[:30] if len(pending_matches) >= 3 else matches

    t1_legs = select_ticket_1_tactical(source_matches)
    t2_legs = select_ticket_2_goals_corners_cards(source_matches)
    t3_legs = select_ticket_3_rompebancas_ultra(source_matches)

    t1_odds = calculate_parley_odds(t1_legs)
    t1_prob = calculate_parley_probability(t1_legs)

    t2_odds = calculate_parley_odds(t2_legs)
    t2_prob = calculate_parley_probability(t2_legs)

    t3_odds = calculate_parley_odds(t3_legs)
    t3_prob = calculate_parley_probability(t3_legs)

    # Enriquecer con Gemini AI si está disponible
    ai_enrichment = enrich_parleys_with_gemini(t1_legs, t2_legs, t3_legs)

    # Fallback descriptivo analítico
    t1_ai = (ai_enrichment or {}).get("ticket_1", {
        "titulo": "Tridente de Convicción Táctica",
        "lema": "Solidez Matemática y Control de Posesión",
        "veredicto_gemini": f"Combinada estructurada con {len(t1_legs)} selecciones respaldadas por modelos de Poisson con expectativa de goles favorable. Diseñada para multiplicar x{t1_odds} con un balance óptimo entre cuota atractiva y probabilidad estadística."
    })
    t2_ai = (ai_enrichment or {}).get("ticket_2", {
        "titulo": "Fórmula Especial: Córners, Tarjetas & Goles",
        "lema": "Intensidad por Bandas y Tensión Disciplinaria",
        "veredicto_gemini": f"Este parley explota el valor oculto de las bandas y la fricción física ({len(t2_legs)} selecciones combinadas). Las proyecciones de tiros de esquina y amonestaciones permiten elevar la cuota a x{t2_odds} sin depender exclusivamente de quién gane el partido."
    })
    t3_ai = (ai_enrichment or {}).get("ticket_3", {
        "titulo": "La Rompe-Bancas Ultra",
        "lema": "El Gran Premio: Cuota Gigante con Sustento de Valor",
        "veredicto_gemini": f"La auténtica soñadora del día: cuota acumulada de x{t3_odds} combinando {len(t3_legs)} eventos con discrepancia estadística positiva frente al mercado. Un boleto ambicioso donde una inversión moderada genera un retorno masivo respaldado por métricas avanzadas de xG."
    })

    now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
    today_date_str = datetime.now().strftime("%Y-%m-%d")

    tickets = [
        {
            "id": "parley_1_tactical",
            "tier": 1,
            "badge": "Soñadora Táctica",
            "icon": "shield-check",
            "theme_color": "emerald",
            "accent_gradient": "from-emerald-500/20 via-teal-500/10 to-transparent",
            "border_color": "border-emerald-500/50",
            "glow_color": "shadow-emerald-950/50",
            "target_odds_label": "Nivel 1 • Cuota ~5.00x",
            "total_odds": t1_odds,
            "combined_prob": t1_prob,
            "stake_example": 100,
            "payout_example": round(100 * t1_odds),
            "titulo": t1_ai.get("titulo"),
            "lema": t1_ai.get("lema"),
            "veredicto_gemini": t1_ai.get("veredicto_gemini"),
            "legs_count": len(t1_legs),
            "legs": t1_legs
        },
        {
            "id": "parley_2_special_markets",
            "tier": 2,
            "badge": "Goles, Córners & Tarjetas",
            "icon": "zap",
            "theme_color": "cyan",
            "accent_gradient": "from-cyan-500/20 via-blue-500/10 to-transparent",
            "border_color": "border-cyan-500/50",
            "glow_color": "shadow-cyan-950/50",
            "target_odds_label": "Nivel 2 • Cuota ~12.00x",
            "total_odds": t2_odds,
            "combined_prob": t2_prob,
            "stake_example": 100,
            "payout_example": round(100 * t2_odds),
            "titulo": t2_ai.get("titulo"),
            "lema": t2_ai.get("lema"),
            "veredicto_gemini": t2_ai.get("veredicto_gemini"),
            "legs_count": len(t2_legs),
            "legs": t2_legs
        },
        {
            "id": "parley_3_rompebancas",
            "tier": 3,
            "badge": "La Rompe-Bancas Ultra",
            "icon": "sparkles",
            "theme_color": "amber",
            "accent_gradient": "from-amber-500/25 via-orange-500/15 to-transparent",
            "border_color": "border-amber-500/60",
            "glow_color": "shadow-amber-950/60",
            "target_odds_label": "Nivel 3 • Cuota ~30.00x+",
            "total_odds": t3_odds,
            "combined_prob": t3_prob,
            "stake_example": 100,
            "payout_example": round(100 * t3_odds),
            "titulo": t3_ai.get("titulo"),
            "lema": t3_ai.get("lema"),
            "veredicto_gemini": t3_ai.get("veredicto_gemini"),
            "legs_count": len(t3_legs),
            "legs": t3_legs
        }
    ]

    package = {
        "date_iso": today_date_str,
        "generated_at": now_str,
        "is_ai_powered": bool(ai_enrichment),
        "powered_by": "Google Gemini AI & Modelos Poisson Cuantitativos",
        "tickets": tickets
    }

    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(package, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE ERROR]: {e}")

    return package

def get_or_generate_dream_parleys(matches, force_regenerate=False):
    """
    Retorna el paquete de parleys desde caché o lo genera si no existe,
    ha expirado, contiene partidos de días anteriores, o contiene partidos que ya iniciaron.
    """
    today_iso = datetime.now().strftime("%Y-%m-%d")
    now_ts = time.time()

    if not force_regenerate and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 1. Comprobar fecha del paquete y existencia de 3 tickets
            cache_valid = (data.get("date_iso") == today_iso and len(data.get("tickets", [])) == 3)
            
            if cache_valid:
                # Comprobar cuántos partidos de hoy están disponibles
                today_pending_matches = [
                    m for m in matches 
                    if m.get("date_iso") == today_iso and ((m.get("timestamp") or 0) >= now_ts - 300 or not m.get("timestamp"))
                ]
                
                # Validar cada pierna (leg) de cada ticket
                for t in data.get("tickets", []):
                    legs = t.get("legs", [])
                    if not legs:
                        cache_valid = False
                        break
                    for leg in legs:
                        # Si hay al menos 3 partidos hoy, exigir que las selecciones sean estrictamente de hoy
                        if len(today_pending_matches) >= 3:
                            if leg.get("date_iso") != today_iso:
                                cache_valid = False
                                break
                        # Si el partido ya arrancó hace más de 10 minutos, invalidar caché
                        leg_ts = leg.get("timestamp") or 0
                        if leg_ts and leg_ts < now_ts - 600:
                            cache_valid = False
                            break
                    if not cache_valid:
                        break

            if cache_valid:
                return data
        except Exception as e:
            print(f"[CACHE VALIDATION WARNING]: {e}")
            pass

    return build_dream_parleys_package(matches, force_gemini=force_regenerate)
