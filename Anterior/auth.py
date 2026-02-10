"""
Módulo de Autenticación
"""
import hashlib
import streamlit as st
from database import get_connection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    """Autentica un usuario contra la base de datos."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password_hash = ? AND activo = 1",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    if user:
        return dict(user)
    return None


def get_current_user():
    """Retorna el usuario actual de la sesión."""
    return st.session_state.get("user", None)


def is_auditor():
    user = get_current_user()
    return user and user["rol_global"] == "auditor"


def is_supervisor():
    user = get_current_user()
    return user and user["rol_global"] in ["auditor", "supervisor"]


def is_auditor_campo():
    user = get_current_user()
    return user and user["rol_global"] in ["auditor", "supervisor", "auditor_campo"]


def is_auditado():
    user = get_current_user()
    return user and user["rol_global"] == "auditado"


def require_role(roles):
    """Verifica que el usuario tenga uno de los roles requeridos."""
    user = get_current_user()
    if not user or user["rol_global"] not in roles:
        st.error("⛔ No tiene permisos para acceder a esta sección.")
        st.stop()


def login_page():
    """Muestra la página de login."""
    import base64
    import os
    from config import ASSETS_DIR, COLORS

    st.markdown(f"""
    <style>
    .login-card {{
        max-width: 480px;
        margin: 2rem auto;
        background: white;
        border-radius: 20px;
        padding: 2.5rem 2rem;
        box-shadow: 0 8px 32px rgba(35,63,132,0.12);
        border: 1px solid #E8ECF1;
    }}
    .login-logo-area {{
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    .login-logo-area img {{
        max-width: 320px;
        width: 90%;
        margin-bottom: 1.2rem;
    }}
    .login-app-name {{
        color: {COLORS['astronaut']};
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin: 0.5rem 0 0.2rem;
        text-align: center;
        line-height: 1;
    }}
    .login-app-name span {{
        background: linear-gradient(135deg, {COLORS['allports']}, {COLORS['lochinvar']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .login-tagline {{
        color: {COLORS['dark_gray']};
        font-size: 1rem;
        text-align: center;
        margin: 0.3rem 0 1.5rem;
        letter-spacing: 0.5px;
    }}
    .login-divider {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, {COLORS['cerulean']}40, transparent);
        margin: 1rem 0;
    }}
    .login-footer {{
        text-align: center;
        margin-top: 1.2rem;
        color: #94A3B8;
        font-size: 0.78rem;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        # Logo grande
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f"""
                <div class="login-logo-area">
                    <img src="data:image/png;base64,{logo_b64}" alt="CoopeMédicos">
                </div>
                """,
                unsafe_allow_html=True
            )

        # Nombre de la app grande
        st.markdown('<div class="login-app-name"><span>AUDIT +</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="login-tagline">Sistema de Gestión de Auditorías</p>', unsafe_allow_html=True)

        st.markdown('<hr class="login-divider">', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingrese su contraseña")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True, type="primary")

            if submitted:
                if username and password:
                    user = authenticate(username, password)
                    if user:
                        st.session_state["user"] = user
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.warning("⚠️ Complete todos los campos")

        st.markdown("""
        <div class="login-footer">
            <p>Demo: admin / admin123</p>
        </div>
        """, unsafe_allow_html=True)


def logout():
    """Cierra la sesión del usuario."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
