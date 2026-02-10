"""
Módulo de Perfiles de Usuario
"""
import streamlit as st
from database import get_connection, log_action
from auth import get_current_user, require_role, hash_password
from utils import section_header, msg_success, msg_error, msg_warning
from config import ROLES


def render():
    """Renderiza el módulo de perfiles de usuario."""
    require_role(["auditor"])
    user = get_current_user()

    section_header("Gestión de Usuarios", "Administración de perfiles y roles", "👥")

    tab1, tab2, tab3 = st.tabs(["👥 Usuarios", "➕ Nuevo Usuario", "📜 Bitácora"])

    with tab1:
        _list_users(user)

    with tab2:
        _create_user(user)

    with tab3:
        _show_log()


def _list_users(current_user):
    """Lista todos los usuarios."""
    conn = get_connection()
    usuarios = conn.execute(
        "SELECT * FROM usuarios ORDER BY rol_global, nombre_completo"
    ).fetchall()
    conn.close()

    role_icons = {
        "auditor": "🛡️",
        "supervisor": "👁️",
        "auditor_campo": "📋",
        "auditado": "👤",
    }

    for u in usuarios:
        u = dict(u)
        icon = role_icons.get(u["rol_global"], "👤")
        status = "✅ Activo" if u["activo"] else "❌ Inactivo"

        with st.expander(f"{icon} {u['nombre_completo']} — {ROLES.get(u['rol_global'], u['rol_global'])} {status}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Usuario:** {u['username']}")
                st.markdown(f"**Email:** {u.get('email', '—') or '—'}")
                st.markdown(f"**Rol:** {ROLES.get(u['rol_global'], u['rol_global'])}")
            with col2:
                st.markdown(f"**Estado:** {'Activo' if u['activo'] else 'Inactivo'}")
                st.markdown(f"**Creado:** {u.get('fecha_creacion', '—') or '—'}")

            if u["id"] != current_user["id"]:
                st.divider()
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    new_role = st.selectbox(
                        "Cambiar Rol", list(ROLES.keys()),
                        format_func=lambda x: ROLES[x],
                        index=list(ROLES.keys()).index(u["rol_global"]) if u["rol_global"] in ROLES else 0,
                        key=f"role_{u['id']}"
                    )
                    if new_role != u["rol_global"]:
                        if st.button("💾 Guardar Rol", key=f"save_role_{u['id']}"):
                            conn = get_connection()
                            conn.execute("UPDATE usuarios SET rol_global = ? WHERE id = ?",
                                         (new_role, u["id"]))
                            conn.commit()
                            conn.close()
                            log_action(current_user["id"], "Cambiar Rol", "Usuarios",
                                       f"{u['nombre_completo']} → {ROLES[new_role]}")
                            st.rerun()

                with col_b:
                    if u["activo"]:
                        if st.button("🚫 Desactivar", key=f"deact_{u['id']}"):
                            conn = get_connection()
                            conn.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (u["id"],))
                            conn.commit()
                            conn.close()
                            log_action(current_user["id"], "Desactivar", "Usuarios", u["nombre_completo"])
                            st.rerun()
                    else:
                        if st.button("✅ Activar", key=f"act_{u['id']}"):
                            conn = get_connection()
                            conn.execute("UPDATE usuarios SET activo = 1 WHERE id = ?", (u["id"],))
                            conn.commit()
                            conn.close()
                            log_action(current_user["id"], "Activar", "Usuarios", u["nombre_completo"])
                            st.rerun()

                with col_c:
                    if st.button("🔑 Reset Pass", key=f"reset_{u['id']}", help="Resetear a 'admin123'"):
                        conn = get_connection()
                        conn.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?",
                                     (hash_password("admin123"), u["id"]))
                        conn.commit()
                        conn.close()
                        log_action(current_user["id"], "Reset Password", "Usuarios", u["nombre_completo"])
                        msg_success(f"Contraseña de {u['nombre_completo']} reseteada a 'admin123'")


def _create_user(current_user):
    """Formulario para crear un nuevo usuario."""
    st.markdown("##### Crear Nuevo Usuario")

    # Form version counter to clear after creation
    form_version = st.session_state.get("user_form_version", 0)

    with st.form(f"form_new_user_v{form_version}"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Usuario *", placeholder="jperez")
            nombre = st.text_input("Nombre Completo *", placeholder="Juan Pérez")
            email = st.text_input("Email", placeholder="jperez@coopemedicos.com")
        with col2:
            password = st.text_input("Contraseña *", type="password", value="admin123")
            rol = st.selectbox("Rol", list(ROLES.keys()),
                                format_func=lambda x: ROLES[x])

        if st.form_submit_button("💾 Crear Usuario", type="primary", use_container_width=True):
            if username.strip() and nombre.strip() and password:
                try:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol_global)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username.strip(), hash_password(password), nombre.strip(), email, rol))
                    conn.commit()
                    conn.close()
                    log_action(current_user["id"], "Crear", "Usuarios", f"Nuevo: {nombre}")
                    st.session_state["user_form_version"] = form_version + 1
                    msg_success()
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e):
                        msg_error("El nombre de usuario ya existe")
                    else:
                        msg_error()
            else:
                msg_warning()


def _show_log():
    """Muestra la bitácora de cambios."""
    conn = get_connection()
    logs = conn.execute("""
        SELECT b.*, u.nombre_completo
        FROM bitacora b
        LEFT JOIN usuarios u ON b.usuario_id = u.id
        ORDER BY b.fecha DESC
        LIMIT 100
    """).fetchall()
    conn.close()

    if not logs:
        st.info("No hay registros en la bitácora.")
        return

    for log_entry in logs:
        log_entry = dict(log_entry)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
        with col1:
            st.caption(log_entry["fecha"][:19] if log_entry.get("fecha") else "—")
        with col2:
            st.caption(log_entry.get("nombre_completo") or "Sistema")
        with col3:
            st.caption(f"{log_entry['accion']} | {log_entry['modulo']}")
        with col4:
            st.caption(log_entry.get("detalle") or "")
