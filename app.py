"""
╔══════════════════════════════════════════════════════════════╗
║   CoopeMédicos - Sistema de Gestión de Auditoría Interna    ║
║   Versión 1.0.0                                             ║
╚══════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, APP_SUBTITLE, APP_ICON, COLORS, ASSETS_DIR, ROLES, VERSION
from database import init_database
from auth import login_page, logout, get_current_user

# ─── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title=f"CoopeMédicos | {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Initialize Database ────────────────────────────────────
init_database()


# ─── Minimal Safe CSS ────────────────────────────────────────
def load_css():
    """CSS seguro: SOLO cosméticos, CERO visibility/display hidden."""
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: #F0F4F8;
    }}

    /* Sidebar fondo oscuro */
    section[data-testid="stSidebar"] > div:first-child {{
        background: linear-gradient(180deg, {COLORS['astronaut']} 0%, #1a2d5a 100%);
    }}

    /* Textos sidebar en blanco */
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.15);
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,0.3) !important;
        background: rgba(255,255,255,0.08) !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(255,255,255,0.18) !important;
        border-color: rgba(255,255,255,0.5) !important;
    }}

    /* ── Navigation Radio Buttons ───────────────────────── */
    section[data-testid="stSidebar"] .stRadio > div {{
        gap: 4px;
    }}
    /* Texto nav en blanco */
    section[data-testid="stSidebar"] .stRadio > div > label > div p,
    section[data-testid="stSidebar"] .stRadio > div > label span {{
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }}
    /* Botón nav default */
    section[data-testid="stSidebar"] .stRadio > div > label {{
        background: rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 11px 16px !important;
        margin: 2px 0;
        cursor: pointer;
        border: 1px solid transparent;
        transition: all 0.15s ease;
    }}
    /* Hover */
    section[data-testid="stSidebar"] .stRadio > div > label:hover {{
        background: rgba(255,255,255,0.14);
        border-color: rgba(255,255,255,0.15);
    }}
    /* Seleccionado/Activo */
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background: linear-gradient(135deg, rgba(13,104,165,0.55), rgba(36,152,127,0.35)) !important;
        border-color: rgba(24,168,227,0.5) !important;
        border-left: 3px solid {COLORS['cerulean']} !important;
    }}
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] p,
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) p,
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) span {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}

    /* Cards y métricas */
    [data-testid="stExpander"] {{
        background: white;
        border-radius: 12px;
        border: 1px solid #E8ECF1;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    [data-testid="stMetric"] {{
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #E8ECF1;
    }}
    [data-testid="stMetricValue"] {{
        color: {COLORS['astronaut']} !important;
        font-weight: 700 !important;
    }}

    /* Botones primarios */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLORS['allports']}, {COLORS['dark_cyan']});
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}

    /* Forms */
    [data-testid="stForm"] {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #E8ECF1;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: white;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #E8ECF1;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {COLORS['allports']}, {COLORS['dark_cyan']});
        color: white !important;
        border-radius: 8px;
    }}

    /* Header y footer custom */
    .main-header {{
        background: white;
        border-radius: 14px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #E8ECF1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .user-badge {{
        background: linear-gradient(135deg, {COLORS['allports']}15, {COLORS['dark_cyan']}15);
        border: 1px solid {COLORS['allports']}30;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.82rem;
        color: {COLORS['astronaut']};
        font-weight: 500;
    }}
    .app-footer {{
        text-align: center;
        color: #94A3B8;
        font-size: 0.75rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid #E8ECF1;
        margin-top: 3rem;
    }}
    </style>
    """, unsafe_allow_html=True)


# ─── Sidebar Logo ────────────────────────────────────────────
def _render_sidebar_logo():
    """Renderiza el logo en el sidebar."""
    logo_path = os.path.join(ASSETS_DIR, "logo_blanco.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style="text-align:center; padding:1.2rem 0.5rem 0.5rem;">
                <img src="data:image/png;base64,{logo_b64}" style="max-width:200px; width:100%;" alt="CoopeMédicos">
            </div>
            <div style="text-align:center; padding:0 0 1rem;">
                <p style="color:rgba(255,255,255,0.6); font-size:0.75rem; margin:0; letter-spacing:1px;">
                    AUDIT + | Sistema de Gestión de Auditorías
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown("### 🛡️ CoopeMédicos")
        st.caption("Gestión de Auditoría")


# ─── Sidebar Completo (siempre se renderiza) ─────────────────
def render_sidebar():
    """
    Renderiza SIEMPRE el sidebar con contenido.
    Si no está autenticado: muestra logo + mensaje.
    Si está autenticado: muestra menú completo.
    Retorna el módulo seleccionado o None si no autenticado.
    """
    user = get_current_user()
    is_logged_in = st.session_state.get("authenticated", False) and user

    with st.sidebar:
        _render_sidebar_logo()
        st.divider()

        if not is_logged_in:
            # No autenticado — solo logo y mensaje
            st.markdown(
                """
                <div style="text-align:center; padding:1rem 0;">
                    <p style="color:rgba(255,255,255,0.5); font-size:0.85rem;">
                        🔒 Inicie sesión para acceder
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            return None

        # ─── Usuario autenticado ─────────────────────────────
        role_icons = {
            "auditor": "🛡️",
            "supervisor": "👁️",
            "auditor_campo": "📋",
            "auditado": "👤",
        }
        role_icon = role_icons.get(user["rol_global"], "👤")
        role_name = ROLES.get(user["rol_global"], user["rol_global"])

        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:12px; margin-bottom:1rem;">
                <p style="margin:0; font-size:0.85rem; font-weight:600; color:white;">
                    {role_icon} {user['nombre_completo']}
                </p>
                <p style="margin:0; font-size:0.72rem; color:rgba(255,255,255,0.55);">
                    {role_name}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Menú según rol
        if user["rol_global"] == "auditado":
            menu_items = ["📝 Mis Hallazgos"]
        elif user["rol_global"] == "auditor_campo":
            menu_items = [
                "📈 Dashboard",
                "🌐 Universo Auditable",
                "📅 Plan Anual",
                "🔍 Hallazgos",
                "📤 Exportación",
            ]
        elif user["rol_global"] == "supervisor":
            menu_items = [
                "📈 Dashboard",
                "🌐 Universo Auditable",
                "📅 Plan Anual",
                "🔍 Hallazgos",
                "📊 Evaluación",
                "📤 Exportación",
            ]
        else:  # auditor (admin)
            menu_items = [
                "📈 Dashboard",
                "🌐 Universo Auditable",
                "📅 Plan Anual",
                "🔍 Hallazgos",
                "📊 Evaluación",
                "📤 Exportación",
                "⚙️ Catálogos",
                "👥 Usuarios",
            ]

        st.markdown(
            '<p style="color:rgba(255,255,255,0.4); font-size:0.65rem; letter-spacing:1.5px; margin:0 0 4px 8px;">NAVEGACIÓN</p>',
            unsafe_allow_html=True
        )

        # Navegación por session state
        default_idx = 0
        if "nav" in st.session_state:
            nav_map = {
                "Dashboard": "📈 Dashboard",
                "Hallazgos": "🔍 Hallazgos",
                "Mis Hallazgos": "📝 Mis Hallazgos",
            }
            target = nav_map.get(st.session_state["nav"])
            if target in menu_items:
                default_idx = menu_items.index(target)
            del st.session_state["nav"]

        selected = st.radio(
            "Menú",
            menu_items,
            index=default_idx,
            label_visibility="collapsed"
        )

        st.divider()

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()

        st.markdown(
            f"""
            <div style="text-align:center; padding-top:2rem;">
                <p style="color:rgba(255,255,255,0.25); font-size:0.65rem; margin:0;">
                    v{VERSION} | CoopeMédicos © 2026
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    return selected


def render_header(user):
    """Renderiza el header principal."""
    role_name = ROLES.get(user["rol_global"], user["rol_global"])
    st.markdown(
        f"""
        <div class="main-header">
            <div>
                <span style="font-size:1.3rem; font-weight:700; color:{COLORS['astronaut']};">
                    {APP_ICON} {APP_TITLE}
                </span>
                <span style="font-size:0.85rem; color:{COLORS['dark_gray']}; margin-left:0.5rem;">
                    {APP_SUBTITLE}
                </span>
            </div>
            <div>
                <span class="user-badge">
                    👤 {user['nombre_completo']} &nbsp;|&nbsp; {role_name}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def route_module(selected):
    """Enruta al módulo seleccionado."""
    module_map = {
        "📈 Dashboard": "dashboard",
        "🌐 Universo Auditable": "universo_auditable",
        "📅 Plan Anual": "plan_anual",
        "🔍 Hallazgos": "hallazgos",
        "📝 Mis Hallazgos": "hallazgos",
        "📊 Evaluación": "evaluacion",
        "📤 Exportación": "exportacion",
        "⚙️ Catálogos": "catalogos",
        "👥 Usuarios": "perfiles",
    }

    module_name = module_map.get(selected, "dashboard")

    try:
        if module_name == "dashboard":
            from modules.dashboard import render
        elif module_name == "universo_auditable":
            from modules.universo_auditable import render
        elif module_name == "plan_anual":
            from modules.plan_anual import render
        elif module_name == "hallazgos":
            from modules.hallazgos import render
        elif module_name == "evaluacion":
            from modules.evaluacion import render
        elif module_name == "exportacion":
            from modules.exportacion import render
        elif module_name == "catalogos":
            from modules.catalogos import render
        elif module_name == "perfiles":
            from modules.perfiles import render
        else:
            from modules.dashboard import render
        render()
    except Exception as e:
        st.error(f"Error al cargar el módulo: {e}")
        import traceback
        st.code(traceback.format_exc())


def main():
    """Función principal."""
    load_css()

    # SIEMPRE renderizar el sidebar primero (con o sin login)
    selected = render_sidebar()

    # Si no autenticado, mostrar login en el área principal
    if selected is None:
        login_page()
        return

    # Autenticado — mostrar contenido
    user = get_current_user()
    render_header(user)
    route_module(selected)

    # Footer
    st.markdown(
        f"""
        <div class="app-footer">
            <p>CoopeMédicos — Sistema de Gestión de Auditoría Interna v{VERSION}</p>
            <p>© 2026 CoopeMédicos R.L. Todos los derechos reservados.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
