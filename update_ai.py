with open("ai_analyzer.py", "r", encoding="utf-8") as f:
    content = f.read()

old_snippet = '''Pronóstico Principal: {prediction.get('recommended_pick')} ({prediction.get('confidence')}%)

Devuelve ÚNICAMENTE este formato JSON sin texto antes ni después:
{{
  "resumen": "Resumen ejecutivo táctico en 1 frase directa",
  "justificacion_estadistica": "Explicación del xG, ritmo de posesión y probabilidades",
  "analisis_corners_remates": "Proyección y lectura táctica del mercado de córners ({proj_corners} córners esperados) y volumen de remates",
  "analisis_tarjetas_friccion": "Análisis táctico y lectura profunda del mercado disciplinario basada en las {proj_cards} tarjetas proyectadas, el índice de fricción ({friction_idx}), la rigurosidad en la disputa física ({tot_fouls} faltas combinadas estimadas) y la probabilidad de amonestaciones",
  "factor_clave": "Duelo individual o clave táctica en la cancha",
  "advertencia_riesgo": "Escenario específico que complicaría el pronóstico",
  "marcador_sugerido": "{top_score}"
}}'''

new_snippet = '''Pronóstico Principal: {prediction.get('recommended_pick')} ({prediction.get('confidence')}%)

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
}}'''

if old_snippet in content:
    content = content.replace(old_snippet, new_snippet)
    print("SUCCESS: Updated prompt with matrix fields!")
else:
    print("ERROR: old_snippet not found.")

with open("ai_analyzer.py", "w", encoding="utf-8") as f:
    f.write(content)

