import os, requests, json
import config

api_key = config.GEMINI_API_KEY
prompt = """
Actúa como una base de datos deportiva oficial de fútbol y baloncesto.
Para el partido: West Ham United vs Queens Park Rangers (QPR)
Proporciona el historial de partidos:
1. 'home_last_5': los últimos 5 partidos jugados por West Ham United (fecha real o verosímil reciente de esta temporada, rival inglés real, condición Local o Visitante, marcador real y resultado W/D/L, torneo Premier League / FA Cup / EFL).
2. 'away_last_5': los últimos 5 partidos jugados por Queens Park Rangers (fecha reciente, rival inglés real, condición Local o Visitante, marcador real y resultado W/D/L, torneo Championship / EFL).
3. 'head_to_head': los últimos 5 enfrentamientos directos oficiales jugados entre West Ham United y Queens Park Rangers (fecha/año, torneo oficial, marcador real y ganador real).

Devuelve ÚNICAMENTE este formato JSON sin markdown:
{
  "home_last_5": [
    {"date": "28 Sep", "opponent": "Chelsea", "venue": "Local", "score": "0 - 3", "result": "L", "competition": "Premier League"}
  ],
  "away_last_5": [
    {"date": "28 Sep", "opponent": "Millwall", "venue": "Visitante", "score": "1 - 1", "result": "D", "competition": "Championship"}
  ],
  "head_to_head": [
    {"date": "25 Abr 2015", "competition": "Premier League", "score": "0 - 0", "winner": "Empate", "home_team": "QPR", "away_team": "West Ham"}
  ]
}
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.2,
        "maxOutputTokens": 2048
    }
}
resp = requests.post(url, json=payload, timeout=12)
print("STATUS:", resp.status_code)
if resp.status_code == 200:
    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw.startswith("```json"):
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif raw.startswith("```"):
        raw = raw.split("```")[1].split("```")[0].strip()
    data = json.loads(raw)
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("RESP BODY:", resp.text)

