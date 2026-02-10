"""
Configuración global de la aplicación CoopeMédicos - Sistema de Auditoría
"""
import os

# ─── Rutas ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DB_PATH = os.path.join(BASE_DIR, "audit_database.db")

# ─── Paleta de Colores CoopeMédicos ─────────────────────────────────
COLORS = {
    "astronaut": "#233F84",       # Azul oscuro principal
    "allports": "#0D68A5",        # Azul medio
    "cerulean": "#18A8E3",        # Azul claro
    "tropical": "#0B6957",        # Verde oscuro
    "dark_cyan": "#008182",       # Verde azulado
    "lochinvar": "#24987F",       # Verde medio
    "white": "#FFFFFF",
    "light_gray": "#F5F7FA",
    "medium_gray": "#E2E8F0",
    "dark_gray": "#64748B",
    "text_dark": "#1E293B",
    "text_light": "#475569",
    "danger": "#DC2626",
    "warning": "#F59E0B",
    "success": "#10B981",
}

# ─── Colores para gráficos (Seaborn/Matplotlib) ────────────────────
CHART_PALETTE = [
    COLORS["astronaut"],
    COLORS["allports"],
    COLORS["cerulean"],
    COLORS["tropical"],
    COLORS["dark_cyan"],
    COLORS["lochinvar"],
]

# ─── Escalas de Riesgo ──────────────────────────────────────────────
RISK_LEVELS = {
    1: {"label": "Muy Bajo", "color": "#10B981"},
    2: {"label": "Bajo", "color": "#6EE7B7"},
    3: {"label": "Medio", "color": "#F59E0B"},
    4: {"label": "Alto", "color": "#F97316"},
    5: {"label": "Muy Alto", "color": "#DC2626"},
}

RISK_MATRIX_COLORS = {
    (1, 1): "#10B981", (1, 2): "#10B981", (1, 3): "#6EE7B7", (1, 4): "#F59E0B", (1, 5): "#F97316",
    (2, 1): "#10B981", (2, 2): "#6EE7B7", (2, 3): "#F59E0B", (2, 4): "#F97316", (2, 5): "#DC2626",
    (3, 1): "#6EE7B7", (3, 2): "#F59E0B", (3, 3): "#F59E0B", (3, 4): "#F97316", (3, 5): "#DC2626",
    (4, 1): "#F59E0B", (4, 2): "#F97316", (4, 3): "#F97316", (4, 4): "#DC2626", (4, 5): "#DC2626",
    (5, 1): "#F97316", (5, 2): "#DC2626", (5, 3): "#DC2626", (5, 4): "#DC2626", (5, 5): "#DC2626",
}

# ─── Estados ─────────────────────────────────────────────────────────
ESTADOS_PROYECTO = ["Sin Iniciar", "En Proceso", "Completada"]
ESTADOS_HALLAZGO = ["Sin Asignar", "Asignado", "Vencida", "Respuesta Recibida", "Aceptada"]

# ─── Roles ───────────────────────────────────────────────────────────
ROLES = {
    "auditor": "Auditor (Administrador)",
    "supervisor": "Supervisor",
    "auditor_campo": "Auditor de Campo",
    "auditado": "Auditado",
}

# ─── Configuración SQL Server (para producción) ─────────────────────
# Descomenta y configura para SQL Server:
# SQL_SERVER_CONFIG = {
#     "server": "TU_SERVIDOR",
#     "database": "AuditDB",
#     "driver": "{ODBC Driver 17 for SQL Server}",
#     "trusted_connection": "yes",  # Para AD
# }

APP_TITLE = "AUDIT +"
APP_SUBTITLE = "Sistema de Gestión de Auditorías"
APP_ICON = "🛡️"
VERSION = "1.0.0"
