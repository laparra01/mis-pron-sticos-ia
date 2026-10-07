# ==============================================================
# CONFIGURACIÓN FÁCIL - MIS PRONÓSTICOS AI
# ==============================================================
import os

# 1. MODO DE OPERACIÓN:
# False = Carga instantánea de prueba (sin esperas, funciona offline).
# True  = Conecta con las APIs deportivas en vivo para traer partidos reales de hoy.
USE_LIVE_API = os.environ.get("USE_LIVE_API", "True").lower() in ("true", "1")

# 2. CLAVES DE APIS DEPORTIVAS (Se configuran en Render de forma privada y segura):
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "420379031a164db5994782e7e51260fb")
NBA_API_KEY = os.environ.get("NBA_API_KEY", "1d3b81d6-ef83-4a40-947b-019f00a55e68")

# 3. INTELIGENCIA ARTIFICIAL (Gemini):
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
