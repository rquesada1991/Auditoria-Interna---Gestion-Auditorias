"""
Módulo de Hallazgos - Gestión de hallazgos de auditoría
"""
import streamlit as st
from datetime import datetime, date
from database import get_connection, log_action
from auth import get_current_user, require_role
from utils import (
    section_header, status_badge, risk_badge, format_date,
    get_catalog_values, get_all_users, calculate_risk_level,
    msg_success, msg_error, msg_warning
)
from config import ESTADOS_HALLAZGO


def render():
    """Renderiza el módulo de hallazgos."""
    user = get_current_user()

    if user["rol_global"] == "auditado":
        section_header("Mis Hallazgos", "Hallazgos asignados para respuesta", "📝")
        _show_auditado_findings(user)
        return

    require_role(["auditor", "supervisor", "auditor_campo"])
    section_header("Gestión de Hallazgos", "Registro y seguimiento de hallazgos", "🔍")

    tab1, tab2 = st.tabs(["📋 Listado de Hallazgos", "➕ Nuevo Hallazgo"])

    with tab1:
        _list_findings(user)

    with tab2:
        _create_finding(user)


def _list_findings(user):
    """Lista todos los hallazgos con filtros."""
    conn = get_connection()

    # Auto-actualizar vencidos
    today_str = date.today().strftime("%Y-%m-%d")
    conn.execute("""
        UPDATE hallazgos SET estado = 'Vencida'
        WHERE estado IN ('Asignado', 'Sin Asignar')
        AND fecha_compromiso IS NOT NULL
        AND fecha_compromiso < ? AND fecha_compromiso != ''
    """, (today_str,))
    conn.commit()

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        planes = conn.execute("SELECT id, nombre_plan, anio FROM planes ORDER BY anio DESC").fetchall()
        plan_options = {p["id"]: f"{p['nombre_plan']} ({p['anio']})" for p in planes}
        filtro_plan = st.selectbox("Plan", [None] + list(plan_options.keys()),
                                    format_func=lambda x: "Todos" if x is None else plan_options[x],
                                    key="fh_plan")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos"] + ESTADOS_HALLAZGO, key="fh_estado")
    with col_f3:
        filtro_riesgo = st.selectbox("Riesgo", ["Todos", "Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"], key="fh_riesgo")
    with col_f4:
        filtro_buscar = st.text_input("🔍 Buscar", key="fh_buscar", placeholder="Código...")

    query = """
        SELECT h.*, ps.nombre as subseccion_nombre, pp.nombre_auditoria,
            p.nombre_plan, u.nombre_completo as responsable_nombre
        FROM hallazgos h
        LEFT JOIN plan_subsecciones ps ON h.plan_subseccion_id = ps.id
        LEFT JOIN plan_proyectos pp ON h.plan_proyecto_id = pp.id
        LEFT JOIN planes p ON h.plan_id = p.id
        LEFT JOIN usuarios u ON h.responsable_id = u.id
        WHERE 1=1
    """
    params = []
    if filtro_plan:
        query += " AND h.plan_id = ?"
        params.append(filtro_plan)
    if filtro_estado != "Todos":
        query += " AND h.estado = ?"
        params.append(filtro_estado)
    if filtro_riesgo != "Todos":
        query += " AND h.nivel_riesgo = ?"
        params.append(filtro_riesgo)
    if filtro_buscar:
        query += " AND h.codigo_hallazgo LIKE ?"
        params.append(f"%{filtro_buscar}%")

    query += " ORDER BY h.fecha_creacion DESC"
    hallazgos = conn.execute(query, params).fetchall()
    conn.close()

    if not hallazgos:
        st.info("📭 No se encontraron hallazgos.")
        return

    total = len(hallazgos)
    vencidos = sum(1 for h in hallazgos if h["estado"] == "Vencida")
    sin_asignar = sum(1 for h in hallazgos if h["estado"] == "Sin Asignar")
    aceptados = sum(1 for h in hallazgos if h["estado"] == "Aceptada")

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Total", total)
    with mc2:
        st.metric("Sin Asignar", sin_asignar)
    with mc3:
        st.metric("Vencidos", vencidos)
    with mc4:
        st.metric("Aceptados", aceptados)

    st.divider()

    for h in hallazgos:
        h = dict(h)
        with st.expander(
            f"🔍 {h['codigo_hallazgo']} — {h.get('nombre_auditoria', '')} | "
            f"{h.get('nivel_riesgo', 'N/A')}",
            expanded=False
        ):
            _show_finding_detail(h, user)


def _show_finding_detail(h, user):
    """Muestra el detalle de un hallazgo."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Código:** {h['codigo_hallazgo']}")
        st.markdown(f"**Proyecto:** {h.get('nombre_auditoria', '—')}")
        st.markdown(f"**Subsección:** {h.get('subseccion_nombre', '—')}")
    with col2:
        st.markdown(f"**Estado:** {status_badge(h['estado'])}", unsafe_allow_html=True)
        st.markdown(f"**Riesgo:** {risk_badge(h.get('nivel_riesgo', 'N/A'))}", unsafe_allow_html=True)
        st.markdown(f"**Prob/Imp:** {h.get('probabilidad', '—')} / {h.get('impacto', '—')}")
    with col3:
        st.markdown(f"**Área:** {h.get('area', '—')}")
        st.markdown(f"**Responsable:** {h.get('responsable_nombre', '—')}")
        st.markdown(f"**Plan:** {h.get('nombre_plan', '—')}")

    st.divider()

    for label, value in [("Condición", h.get("condicion")), ("Causa", h.get("causa")),
                          ("Efecto", h.get("efecto")), ("Recomendación", h.get("recomendacion")),
                          ("Criterio", h.get("criterio"))]:
        if value:
            st.markdown(f"**{label}:** {value}")

    st.markdown(
        f"**Fechas:** Asignación: {format_date(h.get('fecha_asignacion'))} | "
        f"Compromiso: {format_date(h.get('fecha_compromiso'))} | "
        f"Respuesta: {format_date(h.get('fecha_respuesta'))}"
    )

    if h.get("respuesta_auditado"):
        st.markdown(f"**💬 Respuesta del Auditado:** {h['respuesta_auditado']}")

    conn = get_connection()
    adjuntos = conn.execute(
        "SELECT * FROM adjuntos_hallazgo WHERE hallazgo_id = ? ORDER BY tipo, fecha_subida DESC",
        (h["id"],)
    ).fetchall()
    conn.close()

    if adjuntos:
        st.markdown("**📎 Adjuntos:**")
        for adj in adjuntos:
            tipo_label = "📄 Hallazgo" if adj["tipo"] == "hallazgo" else "📩 Respuesta"
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"{tipo_label}: {adj['nombre_archivo']}")
            with col_b:
                st.download_button("⬇️", data=adj["datos"], file_name=adj["nombre_archivo"],
                                   key=f"dl_hadj_{adj['id']}")

    if user["rol_global"] in ["auditor", "auditor_campo"]:
        st.divider()
        _finding_actions(h, user)


def _finding_actions(h, user):
    """Acciones sobre un hallazgo."""
    col_a1, col_a2, col_a3, col_a4, col_a5 = st.columns(5)

    with col_a1:
        if h["estado"] == "Sin Asignar" and st.button("📤 Asignar", key=f"assign_{h['id']}"):
            st.session_state[f"assigning_{h['id']}"] = True
            st.rerun()

    with col_a2:
        if h["estado"] in ("Asignado", "Vencida") and st.button("👤 Reasignar", key=f"reassign_{h['id']}"):
            st.session_state[f"reassigning_{h['id']}"] = True
            st.rerun()

    with col_a3:
        if h["estado"] == "Respuesta Recibida":
            if st.button("✅ Aceptar", key=f"accept_{h['id']}"):
                _update_finding_status(h["id"], "Aceptada", user)

    with col_a4:
        if h["estado"] == "Respuesta Recibida":
            if st.button("↩️ Rechazar", key=f"reject_{h['id']}"):
                _update_finding_status(h["id"], "Asignado", user)

    with col_a5:
        if user["rol_global"] == "auditor":
            if st.button("🗑️ Eliminar", key=f"del_hall_{h['id']}", type="secondary"):
                try:
                    conn = get_connection()
                    conn.execute("DELETE FROM hallazgos WHERE id = ?", (h["id"],))
                    conn.commit()
                    conn.close()
                    log_action(user["id"], "Eliminar", "Hallazgos", f"Eliminado: {h['codigo_hallazgo']}")
                    msg_success()
                    st.rerun()
                except Exception:
                    msg_error()

    # Primera asignación
    if st.session_state.get(f"assigning_{h['id']}"):
        _assign_finding_form(h, user)

    # Reasignar (editar destinatario + fecha compromiso)
    if st.session_state.get(f"reassigning_{h['id']}"):
        _reassign_finding_form(h, user)

    # Editar hallazgo
    if st.button("✏️ Editar Hallazgo", key=f"edit_hall_{h['id']}"):
        st.session_state[f"editing_hall_{h['id']}"] = True
        st.rerun()

    if st.session_state.get(f"editing_hall_{h['id']}"):
        _edit_finding_form(h, user)

    # Upload
    uploader_key = f"upload_hall_{h['id']}"
    uploaded = st.file_uploader("📎 Adjuntar archivo", key=uploader_key,
                                type=["pdf", "docx", "xlsx", "png", "jpg"])
    if uploaded is not None:
        if st.button("📤 Confirmar subida", key=f"confirm_upload_{h['id']}", type="primary"):
            try:
                file_data = uploaded.read()
                conn = get_connection()
                conn.execute("""
                    INSERT INTO adjuntos_hallazgo (hallazgo_id, nombre_archivo, tipo_archivo, datos, tipo, subido_por)
                    VALUES (?, ?, ?, ?, 'hallazgo', ?)
                """, (h["id"], uploaded.name, uploaded.type, file_data, user["id"]))
                conn.commit()
                conn.close()
                log_action(user["id"], "Adjuntar", "Hallazgos", f"Archivo: {uploaded.name}")
                if uploader_key in st.session_state:
                    del st.session_state[uploader_key]
                msg_success()
                st.rerun()
            except Exception:
                msg_error()


def _assign_finding_form(h, user):
    """Formulario de primera asignación."""
    usuarios = get_all_users()
    user_options = {u["id"]: u["nombre_completo"] for u in usuarios}

    with st.form(f"assign_form_{h['id']}"):
        st.markdown("##### 📤 Asignar Hallazgo")
        responsable = st.selectbox("Asignar a", options=list(user_options.keys()),
                                    format_func=lambda x: user_options[x])
        fecha_comp = st.date_input("Fecha de Compromiso")

        if st.form_submit_button("📤 Asignar", type="primary"):
            try:
                conn = get_connection()
                conn.execute("""
                    UPDATE hallazgos SET estado='Asignado', responsable_id=?,
                        fecha_asignacion=?, fecha_compromiso=?
                    WHERE id=?
                """, (responsable, datetime.now().strftime("%Y-%m-%d"), str(fecha_comp), h["id"]))
                conn.commit()
                conn.close()
                log_action(user["id"], "Asignar", "Hallazgos",
                           f"Hallazgo {h['codigo_hallazgo']} asignado a {user_options[responsable]}")
                if f"assigning_{h['id']}" in st.session_state:
                    del st.session_state[f"assigning_{h['id']}"]
                msg_success()
                st.rerun()
            except Exception:
                msg_error()


def _reassign_finding_form(h, user):
    """Formulario para editar destinatario y fecha de compromiso."""
    usuarios = get_all_users()
    user_options = {u["id"]: u["nombre_completo"] for u in usuarios}
    user_keys = list(user_options.keys())

    current_idx = 0
    if h.get("responsable_id") and h["responsable_id"] in user_keys:
        current_idx = user_keys.index(h["responsable_id"])

    current_date = date.today()
    if h.get("fecha_compromiso"):
        try:
            current_date = datetime.strptime(h["fecha_compromiso"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

    with st.form(f"reassign_form_{h['id']}"):
        st.markdown("##### 👤 Editar Asignación")
        new_responsable = st.selectbox("Nuevo Destinatario", options=user_keys,
                                        format_func=lambda x: user_options[x], index=current_idx)
        new_fecha = st.date_input("Nueva Fecha de Compromiso", value=current_date)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            save = st.form_submit_button("💾 Guardar Cambios", type="primary")
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancelar")

        if save:
            try:
                new_estado = "Asignado" if str(new_fecha) >= date.today().strftime("%Y-%m-%d") else h["estado"]
                conn = get_connection()
                conn.execute("""
                    UPDATE hallazgos SET responsable_id=?, fecha_compromiso=?,
                        estado=?, fecha_modificacion=?
                    WHERE id=?
                """, (new_responsable, str(new_fecha), new_estado,
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"), h["id"]))
                conn.commit()
                conn.close()
                log_action(user["id"], "Reasignar", "Hallazgos",
                           f"{h['codigo_hallazgo']} → {user_options[new_responsable]}, {new_fecha}")
                if f"reassigning_{h['id']}" in st.session_state:
                    del st.session_state[f"reassigning_{h['id']}"]
                msg_success()
                st.rerun()
            except Exception:
                msg_error()

        if cancel:
            if f"reassigning_{h['id']}" in st.session_state:
                del st.session_state[f"reassigning_{h['id']}"]
            st.rerun()


def _update_finding_status(hallazgo_id, nuevo_estado, user):
    """Actualiza el estado de un hallazgo."""
    try:
        conn = get_connection()
        conn.execute("UPDATE hallazgos SET estado=?, fecha_modificacion=? WHERE id=?",
                     (nuevo_estado, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hallazgo_id))
        conn.commit()
        conn.close()
        log_action(user["id"], "Cambiar Estado", "Hallazgos",
                   f"Hallazgo {hallazgo_id} → {nuevo_estado}")
        msg_success()
        st.rerun()
    except Exception:
        msg_error()


def _edit_finding_form(h, user):
    """Formulario de edición de hallazgo."""
    areas = get_catalog_values("area")

    with st.form(f"edit_hall_form_{h['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            condicion = st.text_area("Condición", value=h.get("condicion", ""), height=80)
            causa = st.text_area("Causa", value=h.get("causa", ""), height=80)
            efecto = st.text_area("Efecto", value=h.get("efecto", ""), height=80)
        with col2:
            recomendacion = st.text_area("Recomendación", value=h.get("recomendacion", ""), height=80)
            criterio = st.text_area("Criterio", value=h.get("criterio", ""), height=80)
            probabilidad = st.slider("Probabilidad", 1, 5, h.get("probabilidad", 1))
            impacto = st.slider("Impacto", 1, 5, h.get("impacto", 1))

        area = st.selectbox("Área", areas,
                             index=areas.index(h["area"]) if h.get("area") in areas else 0)

        nivel_riesgo = calculate_risk_level(probabilidad, impacto)
        st.markdown(f"**Nivel de Riesgo Calculado:** {risk_badge(nivel_riesgo)}", unsafe_allow_html=True)

        if st.form_submit_button("💾 Guardar Cambios", type="primary"):
            try:
                conn = get_connection()
                conn.execute("""
                    UPDATE hallazgos SET condicion=?, causa=?, efecto=?, recomendacion=?,
                        criterio=?, probabilidad=?, impacto=?, nivel_riesgo=?, area=?,
                        fecha_modificacion=?
                    WHERE id=?
                """, (condicion, causa, efecto, recomendacion, criterio,
                      probabilidad, impacto, nivel_riesgo, area,
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"), h["id"]))
                conn.commit()
                conn.close()
                log_action(user["id"], "Editar", "Hallazgos", f"Editado: {h['codigo_hallazgo']}")
                del st.session_state[f"editing_hall_{h['id']}"]
                msg_success()
                st.rerun()
            except Exception:
                msg_error()


def _create_finding(user):
    """Formulario para crear un nuevo hallazgo."""
    require_role(["auditor", "auditor_campo"])
    st.markdown("##### Registrar Nuevo Hallazgo")

    conn = get_connection()
    planes = conn.execute("SELECT * FROM planes ORDER BY anio DESC").fetchall()
    if not planes:
        st.info("Primero debe crear un plan anual y agregar proyectos.")
        conn.close()
        return

    plan_options = {p["id"]: f"{p['nombre_plan']} ({p['anio']})" for p in planes}
    selected_plan = st.selectbox("Plan", list(plan_options.keys()),
                                  format_func=lambda x: plan_options[x], key="nc_plan")

    plan_projs = conn.execute(
        "SELECT * FROM plan_proyectos WHERE plan_id = ? AND estado = 'En Proceso' ORDER BY codigo_auditoria",
        (selected_plan,)
    ).fetchall()
    if not plan_projs:
        st.info("⚠️ Este plan no tiene proyectos en estado 'En Proceso'. Solo puede registrar hallazgos en proyectos activos.")
        conn.close()
        return

    proj_options = {p["id"]: f"{p['codigo_auditoria']} — {p['nombre_auditoria']}" for p in plan_projs}
    selected_proj = st.selectbox("Proyecto", list(proj_options.keys()),
                                  format_func=lambda x: proj_options[x], key="nc_proj")

    subsecciones = conn.execute("""
        SELECT ps.id, ps.codigo, ps.nombre, psc.codigo as sec_codigo
        FROM plan_subsecciones ps
        JOIN plan_secciones psc ON ps.plan_seccion_id = psc.id
        WHERE ps.plan_proyecto_id = ?
        ORDER BY psc.orden, ps.orden
    """, (selected_proj,)).fetchall()
    conn.close()

    if not subsecciones:
        st.info("Este proyecto no tiene subsecciones.")
        return

    sub_options = {s["id"]: f"{s['sec_codigo']}.{s['codigo']} — {s['nombre']}" for s in subsecciones}
    default_sub = st.session_state.get("selected_subseccion")
    sub_keys = list(sub_options.keys())
    default_idx = sub_keys.index(default_sub) if default_sub in sub_keys else 0
    selected_sub = st.selectbox("Subsección", sub_keys, format_func=lambda x: sub_options[x],
                                 index=default_idx, key="nc_sub")

    areas = get_catalog_values("area")
    form_version = st.session_state.get("hallazgo_form_version", 0)

    with st.form(f"form_new_finding_v{form_version}"):
        codigo = st.text_input("Código del Hallazgo *", placeholder="H-2026-001")
        col1, col2 = st.columns(2)
        with col1:
            condicion = st.text_area("Condición *", height=80, placeholder="¿Qué se encontró?")
            causa = st.text_area("Causa", height=80, placeholder="¿Por qué ocurrió?")
            efecto = st.text_area("Efecto", height=80, placeholder="¿Cuál es el impacto?")
        with col2:
            recomendacion = st.text_area("Recomendación", height=80, placeholder="¿Qué se recomienda?")
            criterio = st.text_area("Criterio", height=80, placeholder="¿Contra qué norma o política?")
            area = st.selectbox("Área", areas if areas else ["Sin definir"])

        col3, col4 = st.columns(2)
        with col3:
            probabilidad = st.slider("Probabilidad", 1, 5, 3)
        with col4:
            impacto = st.slider("Impacto", 1, 5, 3)

        nivel_riesgo = calculate_risk_level(probabilidad, impacto)
        st.markdown(f"**Nivel de Riesgo:** {risk_badge(nivel_riesgo)}", unsafe_allow_html=True)

        if st.form_submit_button("💾 Registrar Hallazgo", type="primary", use_container_width=True):
            if codigo.strip() and condicion.strip():
                try:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO hallazgos (codigo_hallazgo, plan_subseccion_id, plan_proyecto_id,
                            plan_id, condicion, causa, efecto, recomendacion, criterio,
                            probabilidad, impacto, nivel_riesgo, area, creado_por)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (codigo.strip(), selected_sub, selected_proj, selected_plan,
                          condicion, causa, efecto, recomendacion, criterio,
                          probabilidad, impacto, nivel_riesgo, area, user["id"]))
                    conn.commit()
                    conn.close()
                    log_action(user["id"], "Crear", "Hallazgos", f"Nuevo: {codigo}")
                    for key in ["selected_subseccion", "selected_plan_proyecto", "selected_plan"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state["hallazgo_form_version"] = form_version + 1
                    msg_success()
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e):
                        msg_error("El código del hallazgo ya existe")
                    else:
                        msg_error()
            else:
                msg_warning()


def _show_auditado_findings(user):
    """Muestra hallazgos asignados al auditado actual."""
    conn = get_connection()
    today_str = date.today().strftime("%Y-%m-%d")
    conn.execute("""
        UPDATE hallazgos SET estado = 'Vencida'
        WHERE estado IN ('Asignado', 'Sin Asignar')
        AND fecha_compromiso IS NOT NULL AND fecha_compromiso < ? AND fecha_compromiso != ''
    """, (today_str,))
    conn.commit()

    hallazgos = conn.execute("""
        SELECT h.*, ps.nombre as subseccion_nombre, pp.nombre_auditoria, p.nombre_plan
        FROM hallazgos h
        LEFT JOIN plan_subsecciones ps ON h.plan_subseccion_id = ps.id
        LEFT JOIN plan_proyectos pp ON h.plan_proyecto_id = pp.id
        LEFT JOIN planes p ON h.plan_id = p.id
        WHERE h.responsable_id = ? AND h.estado IN ('Asignado', 'Vencida')
        ORDER BY h.fecha_compromiso
    """, (user["id"],)).fetchall()
    conn.close()

    if not hallazgos:
        st.info("🎉 No tiene hallazgos pendientes de respuesta.")
        return

    st.markdown(f"**{len(hallazgos)} hallazgo(s) pendiente(s)**")

    for h in hallazgos:
        h = dict(h)
        with st.expander(f"🔍 {h['codigo_hallazgo']} — {h.get('nombre_auditoria', '')} | Compromiso: {format_date(h.get('fecha_compromiso'))}"):
            st.markdown(f"**Estado:** {status_badge(h['estado'])}", unsafe_allow_html=True)
            st.markdown(f"**Riesgo:** {risk_badge(h.get('nivel_riesgo', 'N/A'))}", unsafe_allow_html=True)
            st.markdown(f"**Proyecto:** {h.get('nombre_auditoria', '—')}")
            st.markdown(f"**Plan:** {h.get('nombre_plan', '—')}")
            st.markdown(f"**Área:** {h.get('area', '—')}")
            st.divider()

            for label, value in [("Condición", h.get("condicion")), ("Causa", h.get("causa")),
                                  ("Efecto", h.get("efecto")), ("Recomendación", h.get("recomendacion")),
                                  ("Criterio", h.get("criterio"))]:
                if value:
                    st.markdown(f"**{label}:** {value}")

            st.markdown(
                f"**Fechas:** Asignación: {format_date(h.get('fecha_asignacion'))} | "
                f"Compromiso: {format_date(h.get('fecha_compromiso'))}"
            )

            conn2 = get_connection()
            adjuntos = conn2.execute(
                "SELECT * FROM adjuntos_hallazgo WHERE hallazgo_id = ? ORDER BY tipo, fecha_subida DESC",
                (h["id"],)
            ).fetchall()
            conn2.close()

            if adjuntos:
                st.markdown("**📎 Adjuntos:**")
                for adj in adjuntos:
                    adj = dict(adj)
                    tipo_label = "📄 Hallazgo" if adj["tipo"] == "hallazgo" else "📩 Respuesta"
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"{tipo_label}: {adj['nombre_archivo']}")
                    with col_b:
                        st.download_button("⬇️", data=adj["datos"], file_name=adj["nombre_archivo"],
                                           key=f"dl_aud_{adj['id']}")

            st.divider()
            st.markdown("##### 📝 Responder al Hallazgo")

            with st.form(f"resp_form_{h['id']}"):
                respuesta = st.text_area("Su Respuesta", height=120,
                                          placeholder="Escriba su respuesta al hallazgo...")
                adjunto = st.file_uploader("Adjuntar evidencia",
                                            type=["pdf", "docx", "xlsx", "png", "jpg"],
                                            key=f"resp_file_{h['id']}")

                if st.form_submit_button("📤 Enviar Respuesta", type="primary"):
                    if respuesta.strip():
                        try:
                            conn = get_connection()
                            conn.execute("""
                                UPDATE hallazgos SET estado='Respuesta Recibida',
                                    respuesta_auditado=?, fecha_respuesta=?
                                WHERE id=?
                            """, (respuesta.strip(), datetime.now().strftime("%Y-%m-%d"), h["id"]))
                            if adjunto:
                                conn.execute("""
                                    INSERT INTO adjuntos_hallazgo (hallazgo_id, nombre_archivo, tipo_archivo,
                                        datos, tipo, subido_por)
                                    VALUES (?, ?, ?, ?, 'respuesta', ?)
                                """, (h["id"], adjunto.name, adjunto.type, adjunto.read(), user["id"]))
                            conn.commit()
                            conn.close()
                            log_action(user["id"], "Responder", "Hallazgos",
                                       f"Respuesta enviada: {h['codigo_hallazgo']}")
                            msg_success()
                            st.rerun()
                        except Exception:
                            msg_error()
                    else:
                        msg_warning()
