import os

# Identificador de Versión para Auditoría Institucional
CONFIG_VERSION = "10.0"
ENGINE_VERSION = "10.0 Quantitative Citadel"

# ==========================================
# GESTIÓN EXPLÍCITA DE RUTAS (PROJECT ROOT)
# ==========================================
# Si settings.py vive en quant_engine/config/settings.py:
# Subimos dos niveles para llegar a la raíz absoluta del proyecto.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# Directorios principales
CONFIG_DIR = os.path.join(PROJECT_ROOT, "quant_engine", "config")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
LOGS_POSTMORTEM_DIR = os.path.join(PROJECT_ROOT, "logs_postmortem")

# Archivos de persistencia y configuración unificados (Sin duplicados)
DB_PATH = os.path.join(PROJECT_ROOT, "bets.db")
LESSONS_MASTER_PATH = os.path.join(LOGS_POSTMORTEM_DIR, "lessons_master.json")
REGISTRY_FILE = os.path.join(CONFIG_DIR, "rule_registry.json")
PERFORMANCE_FILE = os.path.join(
    CONFIG_DIR, "rule_performance.json"
)  # Única definición oficial en CONFIG_DIR
CORRELATIONS_FILE = os.path.join(CONFIG_DIR, "rule_correlations.json")

# ==========================================
# PARÁMETROS CUANTITATIVOS Y DE RIESGO
# ==========================================
K_PRIOR_DEFAULT = 50.0
MONTE_CARLO_ITERATIONS = 25000

# Límites Institucionales de Riesgo de Portafolio (% bankroll)
MAX_ALLOWED_VAR_PCT = 5.0  # VaR máximo permitido al 95% de confianza (% bankroll)
MAX_ALLOWED_CVAR_PCT = 7.5  # CVaR (Expected Shortfall) máximo permitido (% bankroll)
STUDENT_T_DF = 4.0  # Grados de libertad para la Cópula Student-t

# Parámetros de Position Sizing y Kelly
KELLY_FRACTION = 0.25  # Fracción conservadora de Kelly (Quarter-Kelly)
CONFIDENCE_CAP_FACTOR = 0.95  # Factor tope de confianza sobre el score determinista
MAX_STAKE_PCT = 5.0  # Tope máximo absoluto de stake por apuesta (% bankroll)
RULE_MIN_SAMPLE_SIZE = 5  # Minimo de apuestas requeridas antes de permitir que una regla entre en MONITOR o DISABLED

# Configuración de Scraping y Selectores Playwright
SPORTSBOOK_URL = "https://www.playdoit.bn/sportsbook"
ODDS_CACHE_TTL_SECONDS = 120  # TTL de 2 minutos para el caché de cuotas en vivo
SEARCH_SELECTORS = [
    "input[type='search']",
    "input[placeholder*='Buscar']",
    "input[placeholder*='Search']",
]
ODDS_SELECTORS = [
    ".odds-button",
    ".outcome-price",
    "[data-qa='odds-value']",
    ".price",
    ".decimal-odds",
]

# Parámetros de Steam Move / FMS (Fast Market Sentinel)
STEAM_VELOCITY_THRESHOLD = 1.0  # % de cambio por minuto mínimo para considerar Steam
STEAM_TOTAL_MOVE_THRESHOLD = 5.0  # % de cambio total mínimo para considerar Steam

# Multiplicadores y Penalizaciones
PRIORITY_MULTIPLIERS = {0: 1.00, 1: 1.25, 2: 1.00, 3: 0.80}

SEVERITY_PENALTIES = {
    "LOW": 1.00,
    "MEDIUM": 0.85,
    "HIGH": 0.60,
    "CRITICAL_DATA": 0.90,
    "CRITICAL_EDGE": 0.50,
}

FUZZY_MATCH_THRESHOLD = 75
