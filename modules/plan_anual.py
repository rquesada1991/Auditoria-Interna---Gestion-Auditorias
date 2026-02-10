"""
Módulo Plan Anual de Auditoría - Gestión de planes anuales
"""
import streamlit as st
from datetime import datetime
from database import get_connection, log_action
from auth import get_current_user, require_role
from utils import section_header, status_badge, format_date, get_all_users, msg_success, msg_error, msg_warning
from config import ESTADOS_PROYECTO


def render():
    """Renderiza el módulo de Plan Anual."""
    require_role(["auditor", "supervisor", "auditor_campo"])
    user = get_current_user()

    section_header("Plan Anual de Auditoría", "Planificación y seguimiento de planes anuales", "📅")

    tab1, tab2 = st.tabs(["📋 Planes", "➕ Nuevo Plan"])

    with tab1:
        _list_plans(user)

    with tab2:
        if user["rol_global"] == "auditor":
            _create_plan(user)
        else:
            st.info("Solo el Auditor puede crear planes anuales.")


def _list_plans(user):
    """Lista todos los planes anuales."""
    conn = get_connection()
    planes = conn.execute(
        "SELECT * FROM planes ORDER BY anio DESC, fecha_creacion DESC"
    ).fetchall()
    conn.close()

    if not planes:
        st.info("📭 No hay planes creados. Cree uno en la pestaña 'Nuevo Plan'.")
        return

    for plan in planes:
        plan = dict(plan)
        with st.expander(f"📅 {plan['codigo_plan']} — {plan['nombre_plan']} ({plan['anio']})", expanded=False):
            _show_plan_detail(plan, user)


def _show_plan_detail(plan, user):
    """Muestra el detalle de un plan con 3 columnas por estado."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Código:** {plan['codigo_plan']}")
    with col2:
        st.markdown(f"**Año:** {plan['anio']}")
    with col3:
        st.markdown(f"**Estado:** {status_badge(plan.get('estado', 'Activo'))}", unsafe_allow_html=True)

    if plan.get("objetivo"):
        st.markdown(f"**Objetivo:** {plan['objetivo']}")

    st.divider()

    # Obtener proyectos del plan
    conn = get_connection()
    plan_proyectos = conn.execute("""
        SELECT pp.*, u1.nombre_completo as supervisor_nombre, u2.nombre_completo as auditor_campo_nombre
        FROM plan_proyectos pp
        LEFT JOIN usuarios u1 ON pp.supervisor_id = u1.id
        LEFT JOIN usuarios u2 ON pp.auditor_campo_id = u2.id
        WHERE pp.plan_id = ?
        ORDER BY pp.codigo_auditoria
    """, (plan["id"],)).fetchall()

    # Clasificar por estado
    sin_iniciar = []
    en_proceso = []
    completados = []
    for pp in plan_proyectos:
        pp = dict(pp)
        if pp["estado"] == "Completada":
            completados.append(pp)
        elif pp["estado"] == "En Proceso":
            en_proceso.append(pp)
        else:
            sin_iniciar.append(pp)

    # ─── 3 Columnas por Estado ─────────────────────────────
    col_sin, col_proc, col_comp = st.columns(3)

    with col_sin:
        st.markdown(f"#### 🔘 Sin Iniciar ({len(sin_iniciar)})")
        if sin_iniciar:
            for pp in sin_iniciar:
                _render_project_card(pp, plan, user, conn, "sin_iniciar")
        else:
            st.caption("Sin proyectos")

    with col_proc:
        st.markdown(f"#### 🔄 En Proceso ({len(en_proceso)})")
        if en_proceso:
            for pp in en_proceso:
                _render_project_card(pp, plan, user, conn, "en_proceso")
        else:
            st.caption("Sin proyectos")

    with col_comp:
        st.markdown(f"#### ✅ Completados ({len(completados)})")
        if completados:
            for pp in completados:
                _render_project_card(pp, plan, user, conn, "completado")
        else:
            st.caption("Sin proyectos")

    conn.close()

    # Agregar proyectos del universo
    if user["rol_global"] == "auditor":
        st.divider()
        _add_project_to_plan(plan, user)

        st.divider()
        col_a, col_b = st.columns([5, 1])
        with col_b:
            if st.button("🗑️ Eliminar Plan", key=f"del_plan_{plan['id']}", type="secondary"):
                conn = get_connection()
                conn.execute("DELETE FROM planes WHERE id = ?", (plan["id"],))
                conn.commit()
                conn.close()
                log_action(user["id"], "Eliminar", "Plan Anual", f"Eliminado: {plan['codigo_plan']}")
                st.rerun()


def _render_project_card(pp, plan, user, conn, column_type):
    """Renderiza una tarjeta de proyecto dentro de una columna de estado."""
    # Contar hallazgos
    h_stats = conn.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN estado = 'Aceptada' THEN 1 ELSE 0 END) as aceptados
        FROM hallazgos WHERE plan_proyecto_id = ?
    """, (pp["id"],)).fetchone()
    total_h = h_stats["total"] or 0
    aceptados_h = h_stats["aceptados"] or 0

    sup = pp.get('supervisor_nombre') or 'Sin asignar'
    aud = pp.get('auditor_campo_nombre') or 'Sin asignar'

    st.markdown(f"**📋 {pp['codigo_auditoria']}** — {pp['nombre_auditoria']}")
    st.caption(
        f"📆 Plan: {format_date(pp.get('fecha_inicial_planificada'))} → {format_date(pp.get('fecha_final_planificada'))}"
    )
    if pp.get('fecha_inicio_real'):
        st.caption(
            f"🕐 Real: {format_date(pp.get('fecha_inicio_real'))} → {format_date(pp.get('fecha_final_real'))}"
        )
    st.caption(f"👤 {sup} · 🔍 {aud}")
    if total_h > 0:
        st.caption(f"📊 Hallazgos: {aceptados_h}/{total_h} aceptados")
    st.markdown("---")

    # Botones de acción
    if user["rol_global"] in ["auditor", "supervisor"]:
        _project_actions(pp, plan, user, conn, column_type, total_h, aceptados_h)


def _project_actions(pp, plan, user, conn, column_type, total_h, aceptados_h):
    """Botones de acción para un proyecto según su estado."""
    if column_type == "sin_iniciar":
        # Editar datos del proyecto + botón "Iniciar"
        btn_cols = st.columns(2)
        with btn_cols[0]:
            with st.popover("✏️ Editar", use_container_width=True):
                _edit_plan_project_form(pp, user, allow_state_change=False)
        with btn_cols[1]:
            if st.button("▶️ Iniciar", key=f"start_{pp['id']}", use_container_width=True, type="primary"):
                # Validar campos requeridos
                errors = []
                if not pp.get("fecha_inicial_planificada"):
                    errors.append("Fecha inicio planificada")
                if not pp.get("fecha_final_planificada"):
                    errors.append("Fecha fin planificada")
                if not pp.get("supervisor_id"):
                    errors.append("Supervisor")
                if not pp.get("auditor_campo_id"):
                    errors.append("Auditor de Campo")

                if errors:
                    msg_warning(f"Complete antes: {', '.join(errors)}")
                else:
                    try:
                        conn2 = get_connection()
                        conn2.execute("""
                            UPDATE plan_proyectos SET estado = 'En Proceso',
                                fecha_inicio_real = ?
                            WHERE id = ?
                        """, (datetime.now().strftime("%Y-%m-%d"), pp["id"]))
                        conn2.commit()
                        conn2.close()
                        log_action(user["id"], "Iniciar", "Plan Anual",
                                   f"Proyecto iniciado: {pp['codigo_auditoria']}")
                        msg_success()
                        st.rerun()
                    except Exception:
                        msg_error()

    elif column_type == "en_proceso":
        btn_cols = st.columns(2)
        with btn_cols[0]:
            with st.popover("✏️ Editar", use_container_width=True):
                _edit_plan_project_form(pp, user, allow_state_change=False)
        with btn_cols[1]:
            # Solo completar si todos los hallazgos están aceptados
            if total_h > 0 and aceptados_h == total_h:
                if st.button("✅ Completar", key=f"complete_{pp['id']}", use_container_width=True, type="primary"):
                    try:
                        conn2 = get_connection()
                        conn2.execute("""
                            UPDATE plan_proyectos SET estado = 'Completada',
                                fecha_final_real = ?
                            WHERE id = ?
                        """, (datetime.now().strftime("%Y-%m-%d"), pp["id"]))
                        conn2.commit()
                        conn2.close()
                        log_action(user["id"], "Completar", "Plan Anual",
                                   f"Proyecto completado: {pp['codigo_auditoria']}")
                        msg_success()
                        st.rerun()
                    except Exception:
                        msg_error()
            elif total_h > 0:
                st.caption(f"⏳ {total_h - aceptados_h} hallazgo(s) pendiente(s)")
            else:
                st.caption("Sin hallazgos registrados")

    elif column_type == "completado":
        if user["rol_global"] == "auditor":
            if st.button("🔓 Reabrir", key=f"reopen_{pp['id']}", use_container_width=True):
                try:
                    conn2 = get_connection()
                    conn2.execute("""
                        UPDATE plan_proyectos SET estado = 'En Proceso',
                            fecha_final_real = NULL
                        WHERE id = ?
                    """, (pp["id"],))
                    conn2.commit()
                    conn2.close()
                    log_action(user["id"], "Reabrir", "Plan Anual",
                               f"Proyecto reabierto: {pp['codigo_auditoria']}")
                    msg_success()
                    st.rerun()
                except Exception:
                    msg_error()

    # Mostrar estructura expandible (secciones/subsecciones)
    with st.expander(f"📂 Estructura", expanded=False):
        _show_project_structure(pp, plan, user, conn)


def _show_project_structure(pp, plan, user, conn):
    """Muestra secciones y subsecciones de un proyecto."""
    secciones = conn.execute(
        "SELECT * FROM plan_secciones WHERE plan_proyecto_id = ? ORDER BY orden, codigo",
        (pp["id"],)
    ).fetchall()

    if not secciones:
        st.caption("Sin estructura definida")
        return

    for sec in secciones:
        sec = dict(sec)
        st.markdown(f"📑 **{sec['codigo']}** — {sec['nombre']}")

        subsecciones = conn.execute(
            "SELECT * FROM plan_subsecciones WHERE plan_seccion_id = ? ORDER BY orden, codigo",
            (sec["id"],)
        ).fetchall()

        for sub in subsecciones:
            sub = dict(sub)
            h_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM hallazgos WHERE plan_subseccion_id = ?",
                (sub["id"],)
            ).fetchone()["cnt"]

            badge = f" 🔴 {h_count}" if h_count > 0 else ""
            st.markdown(f"&nbsp;&nbsp;&nbsp;↳ **{sub['codigo']}** — {sub['nombre']}{badge}")

            # Botón hallazgos solo si proyecto En Proceso
            if pp["estado"] == "En Proceso" and user["rol_global"] in ["auditor", "auditor_campo"]:
                if st.button(f"🔍 Hallazgos ({h_count})", key=f"hall_sub_{sub['id']}",
                             help="Ver o crear hallazgos"):
                    st.session_state["selected_subseccion"] = sub["id"]
                    st.session_state["selected_plan_proyecto"] = pp["id"]
                    st.session_state["selected_plan"] = plan["id"]
                    st.session_state["nav"] = "Hallazgos"
                    st.rerun()


def _edit_plan_project_form(pp, user, allow_state_change=False):
    """Formulario para editar datos de planificación de un proyecto."""
    usuarios = get_all_users()
    user_options = {u["id"]: u["nombre_completo"] for u in usuarios}
    user_keys = list(user_options.keys())

    # Preseleccionar supervisor actual
    sup_options = [None] + user_keys
    sup_idx = 0
    if pp.get("supervisor_id") and pp["supervisor_id"] in user_keys:
        sup_idx = sup_options.index(pp["supervisor_id"])

    # Preseleccionar auditor campo actual
    aud_idx = 0
    if pp.get("auditor_campo_id") and pp["auditor_campo_id"] in user_keys:
        aud_idx = sup_options.index(pp["auditor_campo_id"])

    with st.form(f"edit_pp_{pp['id']}"):
        fecha_ini = st.date_input("Fecha Inicio Planificada",
                                   value=datetime.strptime(pp["fecha_inicial_planificada"], "%Y-%m-%d").date()
                                   if pp.get("fecha_inicial_planificada") else None)
        fecha_fin = st.date_input("Fecha Fin Planificada",
                                   value=datetime.strptime(pp["fecha_final_planificada"], "%Y-%m-%d").date()
                                   if pp.get("fecha_final_planificada") else None)
        supervisor = st.selectbox("Supervisor",
                                   options=sup_options,
                                   format_func=lambda x: "— Seleccionar —" if x is None else user_options[x],
                                   index=sup_idx)
        auditor_campo = st.selectbox("Auditor de Campo",
                                      options=sup_options,
                                      format_func=lambda x: "— Seleccionar —" if x is None else user_options[x],
                                      index=aud_idx)

        if st.form_submit_button("💾 Guardar"):
            try:
                conn = get_connection()
                conn.execute("""
                    UPDATE plan_proyectos SET fecha_inicial_planificada=?,
                        fecha_final_planificada=?, supervisor_id=?, auditor_campo_id=?
                    WHERE id=?
                """, (str(fecha_ini) if fecha_ini else None,
                      str(fecha_fin) if fecha_fin else None,
                      supervisor, auditor_campo, pp["id"]))
                conn.commit()
                conn.close()
                log_action(user["id"], "Editar", "Plan Anual",
                           f"Proyecto editado: {pp['codigo_auditoria']}")
                msg_success()
                st.rerun()
            except Exception:
                msg_error()


def _add_project_to_plan(plan, user):
    """Agrega proyectos del universo auditable al plan (copia)."""
    st.markdown("##### ➕ Agregar Proyecto del Universo Auditable")

    conn = get_connection()
    existing = conn.execute(
        "SELECT proyecto_origen_id FROM plan_proyectos WHERE plan_id = ?",
        (plan["id"],)
    ).fetchall()
    existing_ids = [e["proyecto_origen_id"] for e in existing]

    proyectos = conn.execute(
        "SELECT * FROM proyectos ORDER BY codigo_auditoria"
    ).fetchall()
    conn.close()

    available = [dict(p) for p in proyectos]
    if not available:
        st.caption("No hay proyectos en el universo auditable.")
        return

    options = {p["id"]: f"{p['codigo_auditoria']} — {p['nombre_auditoria']}" +
               (" ✅ (ya en plan)" if p["id"] in existing_ids else "")
               for p in available}

    selected = st.multiselect(
        "Seleccione proyectos",
        options=[p["id"] for p in available if p["id"] not in existing_ids],
        format_func=lambda x: options.get(x, str(x)),
        key=f"add_proj_plan_{plan['id']}"
    )

    if st.button("📥 Copiar al Plan", key=f"copy_to_plan_{plan['id']}", type="primary"):
        if selected:
            conn = get_connection()
            for proj_id in selected:
                proj = conn.execute("SELECT * FROM proyectos WHERE id = ?", (proj_id,)).fetchone()
                if proj:
                    proj = dict(proj)
                    cursor = conn.execute("""
                        INSERT INTO plan_proyectos (plan_id, proyecto_origen_id, codigo_auditoria,
                            nombre_auditoria, objetivo, tipo_auditoria, proceso,
                            fecha_inicial_planificada, fecha_final_planificada)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (plan["id"], proj["id"], proj["codigo_auditoria"],
                          proj["nombre_auditoria"], proj.get("objetivo"),
                          proj.get("tipo_auditoria"), proj.get("proceso"),
                          proj.get("fecha_inicial_planificada"), proj.get("fecha_final_planificada")))

                    plan_proyecto_id = cursor.lastrowid

                    secciones = conn.execute(
                        "SELECT * FROM secciones WHERE proyecto_id = ? ORDER BY orden",
                        (proj["id"],)
                    ).fetchall()

                    for sec in secciones:
                        sec = dict(sec)
                        cursor_sec = conn.execute("""
                            INSERT INTO plan_secciones (plan_proyecto_id, seccion_origen_id,
                                codigo, nombre, descripcion, orden)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (plan_proyecto_id, sec["id"], sec["codigo"], sec["nombre"],
                              sec.get("descripcion"), sec.get("orden", 0)))

                        plan_seccion_id = cursor_sec.lastrowid

                        subsecciones = conn.execute(
                            "SELECT * FROM subsecciones WHERE seccion_id = ? ORDER BY orden",
                            (sec["id"],)
                        ).fetchall()

                        for sub in subsecciones:
                            sub = dict(sub)
                            conn.execute("""
                                INSERT INTO plan_subsecciones (plan_seccion_id, plan_proyecto_id,
                                    subseccion_origen_id, codigo, nombre, descripcion, orden)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (plan_seccion_id, plan_proyecto_id, sub["id"],
                                  sub["codigo"], sub["nombre"], sub.get("descripcion"),
                                  sub.get("orden", 0)))

            conn.commit()
            conn.close()
            log_action(user["id"], "Copiar", "Plan Anual",
                       f"Copiados {len(selected)} proyecto(s) al plan {plan['codigo_plan']}")
            msg_success()
            st.rerun()
        else:
            msg_warning("Seleccione al menos un proyecto")


def _create_plan(user):
    """Formulario para crear un nuevo plan anual."""
    st.markdown("##### Crear Nuevo Plan Anual")

    form_version = st.session_state.get("plan_form_version", 0)

    with st.form(f"form_new_plan_v{form_version}"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código del Plan *", placeholder="PLAN-2026")
            nombre = st.text_input("Nombre del Plan *", placeholder="Plan Anual de Auditoría 2026")
        with col2:
            anio = st.number_input("Año", value=datetime.now().year, min_value=2020, max_value=2040)

        objetivo = st.text_area("Objetivo del Plan", height=100)

        if st.form_submit_button("💾 Crear Plan", type="primary", use_container_width=True):
            if codigo.strip() and nombre.strip():
                try:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO planes (codigo_plan, nombre_plan, objetivo, anio, creado_por)
                        VALUES (?, ?, ?, ?, ?)
                    """, (codigo.strip(), nombre.strip(), objetivo, anio, user["id"]))
                    conn.commit()
                    conn.close()
                    log_action(user["id"], "Crear", "Plan Anual", f"Plan: {codigo}")
                    st.session_state["plan_form_version"] = form_version + 1
                    msg_success()
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e):
                        msg_error("El código del plan ya existe")
                    else:
                        msg_error()
            else:
                msg_warning()
