# ⚽🏀 Mis Pronósticos AI (Fútbol Mundial & NBA)

Plataforma analítica y cuantitativa de predicciones deportivas asistida por Inteligencia Artificial, inspirada en la arquitectura de **Mis Pronósticos AI**.

---

## ⚡ Cómo Probar en tu PC Personal (Inicio Rápido)

1. En tu PC personal, abre esta carpeta sincronizada de OneDrive.
2. Haz doble clic en el archivo:
   ```text
   iniciar_web.bat
   ```
3. Se abrirá automáticamente tu navegador en:
   ```text
   http://localhost:5000
   ```
*(La carga es **instantánea (0 esperas)** gracias a que el modo de prueba viene activo por defecto).*

---

## 🔌 ¿Cómo conectar partidos reales en vivo cuando quieras?

Dejamos un archivo de configuración súper sencillo llamado [**`config.py`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/config.py). 

Para pasar de la maqueta rápida a partidos 100% reales en vivo:

1. Abre [**`config.py`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/config.py) con el bloc de notas o cualquier editor.
2. Cambia la primera línea:
   ```python
   USE_LIVE_API = True
   ```
3. Pega tu clave gratuita (por ejemplo de [Football-Data.org](https://www.football-data.org/)):
   ```python
   FOOTBALL_DATA_API_KEY = "tu_clave_aqui"
   ```
4. Guarda el archivo y listo. La aplicación intentará traer los partidos oficiales de hoy, y si en algún momento no tienes internet o la API falla, **automáticamente usa el catálogo local como respaldo sin trabarse ni dar error**.

---

## 🌟 Cobertura y Funcionalidades

### 🏀 1. NBA (Baloncesto)
* **Desglose de Cuartos & Mitades:**
  - $1Q$: Proyección inicial de quinteto titular.
  - $2Q, 3Q, 4Q$: **Analizados dinámicamente en vivo** según el ritmo de tiro ($FG\%$), rebotes y momentum.
  - $1ª \text{ Mitad}$ ($Q1+Q2$) y $2ª \text{ Mitad}$ ($Q3+Q4$).
  - **Juego Completo:** Moneyline y proyección final de puntos totales.
* **Estadísticas en Tiempo Real:** Reloj por cuartos, $\% FG$, $\% 3PT$, Rebotes, Asistencias y Pérdidas.

### ⚽ 2. Fútbol (Clubes & Selecciones Nacionales)
* **Clubes:** Champions League, Premier League, LaLiga, Serie A, Bundesliga, Ligue 1, Liga MX, Copa Libertadores.
* **Selecciones Nacionales:** Eliminatorias CONMEBOL (Argentina vs Brasil, Colombia vs Uruguay), UEFA Nations League (España vs Francia, Inglaterra vs Alemania), Concacaf (México vs USA).
* **Métricas In-Play:** Posesión $(\%)$, tiros a puerta, tiros totales, córners, faltas, tarjetas y recálculo Poisson ($1X2$).

---

## 📁 Archivos Clave
* [**`config.py`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/config.py): Interruptor central (`USE_LIVE_API = True/False`) y claves de conexión.
* [**`iniciar_web.bat`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/iniciar_web.bat): Lanzador con 1 solo clic en Windows.
* [**`prediction_engine.py`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/prediction_engine.py): Distribución de Poisson (fútbol) y modelo gaussiano de cuartos y pace (NBA).
* [**`data_provider.py`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/data_provider.py): Conector de datos locales y APIs remotas.
* [**`templates/index.html`**](file:///c:/Users/usr042518/OneDrive%20-%20Banco%20de%20Desarrollo%20Rural,%20S.A/iA/templates/index.html): Interfaz web oscura, responsive y filtros rápidos.
