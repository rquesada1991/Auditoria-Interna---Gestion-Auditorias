"""
Módulo Universo Auditable - Gestión de Proyectos, Secciones y Subsecciones
Solo información general (machotes) que luego se jalan al Plan Anual.
NO incluye fechas, estado, supervisor ni auditor de campo.
"""
import streamlit as st
from datetime import datetime
from database import get_connection, log_action
from auth import get_current_user, require_role
from utils import (
    get_catalog_values, section_header, format_date,
    msg_success, msg_error, msg_warning
)


def render():
    """Renderiza el módulo de Universo Auditable."""
    require_role(["auditor", "supervisor", "auditor_campo"])
    user = get_current_user()

    section_header("Universo Auditable",
                   "Plantillas de proyectos de auditoría (se copian al Plan Anual)", "🌐")

    tab1, tab2 = st.tabs(["📁 Proyectos", "➕ Nuevo Proyecto"])

    with tab1:
        _list_projects(user)

    with tab2:
        if user["rol_global"] == "auditor":
            _create_project(user)
        else:
            st.info("Solo el Auditor puede crear proyectos en el universo auditable.")


def _list_projects(user):
    """Lista todos los proyectos del universo auditable."""
    conn = get_connection()

    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipos = ["Todos"] + get_catalog_values("tipo_auditoria")
        filtro_tipo = st.selectbox("Tipo", tipos, key="filtro_ua_tipo")
    with col_f2:
        filtro_buscar = st.text_input("🔍 Buscar", placeholder="Código o nombre...", key="filtro_ua_buscar")

    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []

    if filtro_tipo != "Todos":
        query += " AND tipo_auditoria = ?"
        params.append(filtro_tipo)
    if filtro_buscar:
        query += " AND (codigo_auditoria LIKE ? OR nombre_auditoria LIKE ?)"
        params.extend([f"%{filtro_buscar}%", f"%{filtro_buscar}%"])

    query += " ORDER BY fecha_creacion DESC"
    proyectos = conn.execute(query, params).fetchall()
    conn.close()

    if not proyectos:
        st.info("📭 No se encontraron proyectos. Cree uno en la pestaña 'Nuevo Proyecto'.")
        return

    st.markdown(f"**{len(proyectos)} proyecto(s) encontrado(s)**")

    for p in proyectos:
        p = dict(p)
        with st.expander(
            f"📋 {p['codigo_auditoria']} — {p['nombre_auditoria']}",
            expanded=False
        ):
            _show_project_detail(p, user)


def _show_project_detail(p, user):
    """Muestra el detalle de un proyecto (solo info general)."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Código:** {p['codigo_auditoria']}")
        st.markdown(f"**Tipo de Auditoría:** {p.get('tipo_auditoria', '—')}")
        st.markdown(f"**Proceso:** {p.get('proceso', '—')}")
    with col2:
        if p.get("objetivo"):
            st.markdown(f"**Objetivo:** {p['objetivo']}")

    st.divider()

    # Secciones y Subsecciones
    _show_sections(p["id"], user)

    # Adjuntos (Papeles de Trabajo)
    st.divider()
    _show_attachments(p["id"], user)

    # Editar / Eliminar
    if user["rol_global"] == "auditor":
        st.divider()
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            if st.button("✏️ Editar Proyecto", key=f"edit_proj_{p['id']}"):
                st.session_state["editing_project"] = p["id"]
                st.rerun()
        with col_c:
            if st.button("🗑️ Eliminar", key=f"del_proj_{p['id']}", type="secondary"):
                conn = get_connection()
                conn.execute("DELETE FROM proyectos WHERE id = ?", (p["id"],))
                conn.commit()
                conn.close()
                log_action(user["id"], "Eliminar", "Universo Auditable",
                           f"Eliminado: {p['codigo_auditoria']}")
                msg_success()
                st.rerun()

    # Modal de edición
    if st.session_state.get("editing_project") == p["id"]:
        _edit_project_form(p, user)


def _show_sections(proyecto_id, user):
    """Muestra las secciones y subsecciones de un proyecto."""
    conn = get_connection()
    secciones = conn.execute(
        "SELECT * FROM secciones WHERE proyecto_id = ? ORDER BY orden, codigo",
        (proyecto_id,)
    ).fetchall()

    st.markdown("**📑 Estructura del Proyecto**")

    if not secciones:
        st.caption("No hay secciones definidas.")
    else:
        for sec in secciones:
            sec = dict(sec)
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"**{sec['codigo']}** — {sec['nombre']}")
                if sec.get("descripcion"):
                    st.caption(sec["descripcion"])
            with col2:
                if user["rol_global"] == "auditor":
                    if st.button("🗑️", key=f"del_sec_{sec['id']}", help="Eliminar sección"):
                        conn2 = get_connection()
                        conn2.execute("DELETE FROM secciones WHERE id = ?", (sec["id"],))
                        conn2.commit()
                        conn2.close()
                        st.rerun()

            # Subsecciones
            subsecciones = conn.execute(
                "SELECT * FROM subsecciones WHERE seccion_id = ? ORDER BY orden, codigo",
                (sec["id"],)
            ).fetchall()

            for sub in subsecciones:
                sub = dict(sub)
                sc1, sc2 = st.columns([6, 1])
                with sc1:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ **{sub['codigo']}** — {sub['nombre']}")
                    if sub.get("descripcion"):
                        st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{sub['descripcion']}")
                with sc2:
                    if user["rol_global"] == "auditor":
                        if st.button("🗑️", key=f"del_sub_{sub['id']}", help="Eliminar subsección"):
                            conn3 = get_connection()
                            conn3.execute("DELETE FROM subsecciones WHERE id = ?", (sub["id"],))
                            conn3.commit()
                            conn3.close()
                            st.rerun()

            # Agregar subsección
            if user["rol_global"] == "auditor":
                with st.popover(f"➕ Subsección en {sec['codigo']}", use_container_width=False):
                    with st.form(f"form_new_sub_{sec['id']}"):
                        sub_codigo = st.text_input("Código", key=f"nsub_cod_{sec['id']}")
                        sub_nombre = st.text_input("Nombre", key=f"nsub_nom_{sec['id']}")
                        sub_desc = st.text_area("Descripción", key=f"nsub_desc_{sec['id']}", height=68)
                        if st.form_submit_button("Guardar"):
                            if sub_codigo and sub_nombre:
                                conn4 = get_connection()
                                conn4.execute(
                                    """INSERT INTO subsecciones (seccion_id, proyecto_id, codigo, nombre, descripcion)
                                    VALUES (?, ?, ?, ?, ?)""",
                                    (sec["id"], proyecto_id, sub_codigo, sub_nombre, sub_desc)
                                )
                                conn4.commit()
                                conn4.close()
                                st.rerun()

    conn.close()

    # Agregar sección
    if user["rol_global"] == "auditor":
        with st.popover("➕ Nueva Sección", use_container_width=False):
            with st.form(f"form_new_sec_{proyecto_id}"):
                sec_codigo = st.text_input("Código", key=f"nsec_cod_{proyecto_id}")
                sec_nombre = st.text_input("Nombre", key=f"nsec_nom_{proyecto_id}")
                sec_desc = st.text_area("Descripción", key=f"nsec_desc_{proyecto_id}", height=68)
                if st.form_submit_button("Guardar"):
                    if sec_codigo and sec_nombre:
                        conn5 = get_connection()
                        conn5.execute(
                            """INSERT INTO secciones (proyecto_id, codigo, nombre, descripcion)
                            VALUES (?, ?, ?, ?)""",
                            (proyecto_id, sec_codigo, sec_nombre, sec_desc)
                        )
                        conn5.commit()
                        conn5.close()
                        st.rerun()


def _show_attachments(proyecto_id, user):
    """Muestra y gestiona adjuntos del proyecto. Usa botón de confirmación para evitar ciclo infinito."""
    conn = get_connection()
    adjuntos = conn.execute(
        "SELECT * FROM adjuntos_proyecto WHERE proyecto_id = ? ORDER BY fecha_subida DESC",
        (proyecto_id,)
    ).fetchall()
    conn.close()

    st.markdown("**📎 Papeles de Trabajo**")

    if adjuntos:
        for adj in adjuntos:
            col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
            with col1:
                st.markdown(f"📄 {adj['nombre_archivo']}")
            with col2:
                st.caption(format_date(adj["fecha_subida"][:10] if adj["fecha_subida"] else ""))
            with col3:
                st.download_button(
                    "⬇️", data=adj["datos"], file_name=adj["nombre_archivo"],
                    key=f"dl_adj_{adj['id']}", help="Descargar"
                )
            with col4:
                if user["rol_global"] in ["auditor", "auditor_campo"]:
                    if st.button("🗑️", key=f"del_adj_{adj['id']}", help="Eliminar adjunto"):
                        conn2 = get_connection()
                        conn2.execute("DELETE FROM adjuntos_proyecto WHERE id = ?", (adj["id"],))
                        conn2.commit()
                        conn2.close()
                        log_action(user["id"], "Eliminar", "Adjuntos",
                                   f"Eliminado adjunto: {adj['nombre_archivo']}")
                        st.rerun()
    else:
        st.caption("No hay archivos adjuntos.")

    # Subir adjunto — botón de confirmación para evitar ciclo infinito
    if user["rol_global"] in ["auditor", "auditor_campo"]:
        uploader_key = f"upload_proj_{proyecto_id}"
        uploaded = st.file_uploader(
            "Subir archivo", key=uploader_key,
            type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        if uploaded is not None:
            if st.button("📤 Confirmar subida", key=f"confirm_upload_{proyecto_id}", type="primary"):
                file_data = uploaded.read()
                file_name = uploaded.name
                file_type = uploaded.type
                conn = get_connection()
                conn.execute(
                    """INSERT INTO adjuntos_proyecto (proyecto_id, nombre_archivo, tipo_archivo, datos, subido_por)
                    VALUES (?, ?, ?, ?, ?)""",
                    (proyecto_id, file_name, file_type, file_data, user["id"])
                )
                conn.commit()
                conn.close()
                log_action(user["id"], "Subir", "Adjuntos",
                           f"Subido: {file_name} al proyecto {proyecto_id}")
                msg_success()
                # Limpiar el uploader
                del st.session_state[uploader_key]
                st.rerun()


def _create_project(user):
    """Formulario para crear un nuevo proyecto (solo info general)."""
    st.markdown("##### Crear Nuevo Proyecto de Auditoría")
    st.caption("Este es un machote. Las fechas, estados y responsables se asignan al incluir el proyecto en un Plan Anual.")

    tipos = get_catalog_values("tipo_auditoria")
    procesos = get_catalog_values("proceso")

    # Counter para generar claves únicas → limpia el form tras crear exitosamente
    form_version = st.session_state.get("ua_form_version", 0)

    with st.form(f"form_new_project_v{form_version}"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código de Auditoría *", placeholder="AUD-2026-001")
            nombre = st.text_input("Nombre de Auditoría *", placeholder="Nombre del proyecto")
        with col2:
            tipo = st.selectbox("Tipo de Auditoría", tipos if tipos else ["Sin definir"])
            proceso = st.selectbox("Proceso", procesos if procesos else ["Sin definir"])

        objetivo = st.text_area("Objetivo", height=100, placeholder="Objetivo general del proyecto de auditoría")

        submitted = st.form_submit_button("💾 Crear Proyecto", type="primary", use_container_width=True)

        if submitted:
            if codigo.strip() and nombre.strip():
                try:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO proyectos (codigo_auditoria, nombre_auditoria, objetivo,
                            tipo_auditoria, proceso, creado_por)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        codigo.strip(), nombre.strip(), objetivo, tipo, proceso, user["id"]
                    ))
                    conn.commit()
                    conn.close()
                    log_action(user["id"], "Crear", "Universo Auditable", f"Proyecto: {codigo}")
                    st.session_state["ua_form_version"] = form_version + 1
                    msg_success()
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e):
                        msg_error("El código de auditoría ya existe")
                    else:
                        msg_error()
            else:
                msg_warning()


def _edit_project_form(p, user):
    """Formulario de edición de proyecto (solo campos generales)."""
    st.markdown("---")
    st.markdown("##### ✏️ Editar Proyecto")

    tipos = get_catalog_values("tipo_auditoria")
    procesos = get_catalog_values("proceso")

    with st.form(f"form_edit_project_{p['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre", value=p["nombre_auditoria"])
            tipo_idx = tipos.index(p["tipo_auditoria"]) if p.get("tipo_auditoria") in tipos else 0
            tipo = st.selectbox("Tipo", tipos, index=tipo_idx)
        with col2:
            proc_idx = procesos.index(p["proceso"]) if p.get("proceso") in procesos else 0
            proceso = st.selectbox("Proceso", procesos, index=proc_idx)

        objetivo = st.text_area("Objetivo", value=p.get("objetivo", ""), height=80)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True):
                conn = get_connection()
                conn.execute("""
                    UPDATE proyectos SET nombre_auditoria=?, objetivo=?, tipo_auditoria=?,
                        proceso=?, fecha_modificacion=?
                    WHERE id=?
                """, (
                    nombre, objetivo, tipo, proceso,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p["id"]
                ))
                conn.commit()
                conn.close()
                log_action(user["id"], "Editar", "Universo Auditable",
                           f"Editado: {p['codigo_auditoria']}")
                del st.session_state["editing_project"]
                msg_success()
                st.rerun()
        with col_s2:
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                del st.session_state["editing_project"]
                st.rerun()
