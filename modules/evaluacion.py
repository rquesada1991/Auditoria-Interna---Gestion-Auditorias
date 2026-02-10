"""
Módulo de Evaluación del Universo Auditable
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection, log_action
from auth import get_current_user, require_role
from utils import section_header, risk_badge, msg_success


def render():
    """Renderiza el módulo de evaluación."""
    require_role(["auditor", "supervisor"])
    user = get_current_user()

    section_header("Evaluación del Universo Auditable",
                   "Priorización de auditorías por nivel de criticidad", "📊")

    # Sync data from plans
    if st.button("🔄 Sincronizar datos desde Planes", help="Actualiza datos automáticos desde los planes"):
        _sync_from_plans()
        msg_success()
        st.rerun()

    conn = get_connection()

    # Get all projects with evaluation data
    proyectos = conn.execute("""
        SELECT p.id, p.codigo_auditoria, p.nombre_auditoria,
            COALESCE(e.nivel_riesgo, 1) as nivel_riesgo,
            COALESCE(e.meses_ultima_auditoria, 0) as meses_ultima_auditoria,
            COALESCE(e.hallazgos_ult_auditoria, 0) as hallazgos_ult_auditoria,
            COALESCE(e.hallazgos_solucionados, 0) as hallazgos_solucionados,
            COALESCE(e.estado_auditoria, 'N/A') as estado_auditoria,
            e.fecha_auditoria,
            COALESCE(e.ciclo_rotacion, 12) as ciclo_rotacion,
            COALESCE(e.nivel_criticidad, 0) as nivel_criticidad
        FROM proyectos p
        LEFT JOIN evaluacion_universo e ON p.id = e.proyecto_id
        ORDER BY COALESCE(e.nivel_criticidad, 0) DESC
    """).fetchall()

    pesos = conn.execute("SELECT * FROM pesos_evaluacion ORDER BY id").fetchall()
    pesos_dict = {p["campo"]: p["peso"] for p in pesos}
    conn.close()

    if not proyectos:
        st.info("No hay proyectos en el universo auditable.")
        return

    # Show weights summary
    with st.expander("⚖️ Pesos actuales de evaluación"):
        for p in pesos:
            st.markdown(f"**{p['etiqueta']}:** {p['peso']:.0%}")

    st.divider()

    # Editable table
    st.markdown("##### Tabla de Evaluación")

    # Convert to dataframe for display
    data = []
    for p in proyectos:
        p = dict(p)
        data.append({
            "id": p["id"],
            "Cód. Auditoría": p["codigo_auditoria"],
            "Nombre Auditoría": p["nombre_auditoria"],
            "Nivel Riesgo (1-5)": p["nivel_riesgo"],
            "Meses Últ. Auditoría": p["meses_ultima_auditoria"],
            "Hallazgos Últ. Aud.": p["hallazgos_ult_auditoria"],
            "Hallazgos Solucionados": p["hallazgos_solucionados"],
            "Estado Auditoría": p["estado_auditoria"],
            "Fecha Auditoría": p["fecha_auditoria"] or "",
            "Ciclo Rotación (meses)": p["ciclo_rotacion"],
            "Nivel Criticidad": round(p["nivel_criticidad"], 2),
        })

    df = pd.DataFrame(data)

    # Display as styled dataframe
    st.dataframe(
        df.drop(columns=["id"]).style.background_gradient(
            subset=["Nivel Criticidad"], cmap="RdYlGn_r"
        ).format({"Nivel Criticidad": "{:.2f}"}),
        use_container_width=True,
        height=min(400, 60 + len(data) * 35)
    )

    st.divider()

    # Edit individual evaluations
    st.markdown("##### ✏️ Editar Evaluación")

    proj_options = {p["id"]: f"{p['codigo_auditoria']} — {p['nombre_auditoria']}" for p in proyectos}
    selected_proj = st.selectbox("Seleccione Proyecto",
                                  list(proj_options.keys()),
                                  format_func=lambda x: proj_options[x])

    current = next((dict(p) for p in proyectos if p["id"] == selected_proj), None)

    if current:
        with st.form(f"eval_form_{selected_proj}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nivel_riesgo = st.slider("Nivel de Riesgo", 1, 5, current["nivel_riesgo"])
                meses = st.number_input("Meses Últ. Auditoría", value=current["meses_ultima_auditoria"],
                                         min_value=0, step=1)
            with col2:
                hallazgos = st.number_input("Hallazgos Últ. Aud.", value=current["hallazgos_ult_auditoria"],
                                             min_value=0, step=1)
                solucionados = st.number_input("Hallazgos Solucionados", value=current["hallazgos_solucionados"],
                                                min_value=0, step=1)
            with col3:
                ciclo = st.number_input("Ciclo Rotación (meses)", value=current["ciclo_rotacion"],
                                         min_value=1, step=1)

            # Calculate criticality
            pct_solucionados = (solucionados / hallazgos * 5) if hallazgos > 0 else 0
            meses_norm = min(meses / 12 * 5, 5)
            ciclo_norm = min(ciclo / 24 * 5, 5)

            criticidad = (
                nivel_riesgo * pesos_dict.get("nivel_riesgo", 0.3) +
                meses_norm * pesos_dict.get("meses_ultima_auditoria", 0.2) +
                min(hallazgos, 5) * pesos_dict.get("hallazgos_ult_auditoria", 0.2) +
                (5 - pct_solucionados) * pesos_dict.get("hallazgos_solucionados", 0.15) +
                ciclo_norm * pesos_dict.get("ciclo_rotacion", 0.15)
            )

            criticidad_label = _criticidad_label(criticidad)
            st.markdown(f"**Nivel de Criticidad Calculado:** {criticidad:.2f} — {risk_badge(criticidad_label)}",
                        unsafe_allow_html=True)

            if st.form_submit_button("💾 Guardar Evaluación", type="primary"):
                conn = get_connection()
                conn.execute("""
                    INSERT INTO evaluacion_universo (proyecto_id, nivel_riesgo, meses_ultima_auditoria,
                        hallazgos_ult_auditoria, hallazgos_solucionados, estado_auditoria,
                        fecha_auditoria, ciclo_rotacion, nivel_criticidad, fecha_evaluacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(proyecto_id) DO UPDATE SET
                        nivel_riesgo=?, meses_ultima_auditoria=?, hallazgos_ult_auditoria=?,
                        hallazgos_solucionados=?, ciclo_rotacion=?, nivel_criticidad=?,
                        fecha_evaluacion=?
                """, (
                    selected_proj, nivel_riesgo, meses, hallazgos, solucionados,
                    current.get("estado_auditoria", "N/A"), current.get("fecha_auditoria", ""),
                    ciclo, criticidad, datetime.now().strftime("%Y-%m-%d"),
                    nivel_riesgo, meses, hallazgos, solucionados, ciclo, criticidad,
                    datetime.now().strftime("%Y-%m-%d")
                ))
                conn.commit()
                conn.close()
                log_action(user["id"], "Evaluar", "Evaluación",
                           f"Evaluación: {current['codigo_auditoria']} → Criticidad: {criticidad:.2f}")
                msg_success()
                st.rerun()


def _criticidad_label(value):
    """Determina la etiqueta de criticidad."""
    if value <= 1.0:
        return "Muy Bajo"
    elif value <= 2.0:
        return "Bajo"
    elif value <= 3.0:
        return "Medio"
    elif value <= 4.0:
        return "Alto"
    else:
        return "Muy Alto"


def _sync_from_plans():
    """Sincroniza datos de evaluación desde los planes."""
    conn = get_connection()
    proyectos = conn.execute("SELECT id FROM proyectos").fetchall()

    for proj in proyectos:
        pid = proj["id"]

        # Get latest plan project data
        latest = conn.execute("""
            SELECT pp.estado, pp.fecha_final_real, pp.id as plan_proyecto_id
            FROM plan_proyectos pp
            JOIN planes pl ON pp.plan_id = pl.id
            WHERE pp.proyecto_origen_id = ?
            ORDER BY pl.anio DESC LIMIT 1
        """, (pid,)).fetchone()

        if latest:
            estado_aud = latest["estado"] or "N/A"
            fecha_aud = latest["fecha_final_real"] or ""

            # Count hallazgos
            h_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM hallazgos WHERE plan_proyecto_id = ?",
                (latest["plan_proyecto_id"],)
            ).fetchone()["cnt"]

            h_solved = conn.execute(
                "SELECT COUNT(*) as cnt FROM hallazgos WHERE plan_proyecto_id = ? AND estado = 'Aceptada'",
                (latest["plan_proyecto_id"],)
            ).fetchone()["cnt"]

            # Calculate months since last audit
            meses = 0
            if fecha_aud:
                try:
                    fd = datetime.strptime(fecha_aud, "%Y-%m-%d")
                    meses = max(0, (datetime.now() - fd).days // 30)
                except (ValueError, TypeError):
                    pass

            conn.execute("""
                INSERT INTO evaluacion_universo (proyecto_id, meses_ultima_auditoria,
                    hallazgos_ult_auditoria, hallazgos_solucionados, estado_auditoria, fecha_auditoria)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(proyecto_id) DO UPDATE SET
                    meses_ultima_auditoria=?, hallazgos_ult_auditoria=?,
                    hallazgos_solucionados=?, estado_auditoria=?, fecha_auditoria=?
            """, (pid, meses, h_count, h_solved, estado_aud, fecha_aud,
                  meses, h_count, h_solved, estado_aud, fecha_aud))

    conn.commit()
    conn.close()
