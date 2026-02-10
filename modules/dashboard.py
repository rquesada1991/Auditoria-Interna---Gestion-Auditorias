"""
Módulo de Dashboard y Reportes
"""
import streamlit as st
from datetime import datetime, date
from database import get_connection
from auth import get_current_user, require_role
from utils import section_header, metric_card, risk_badge, status_badge
from utils.charts import (
    risk_heatmap, hallazgos_por_riesgo, hallazgos_por_area,
    tendencia_historica, gantt_chart, ejecucion_pie, hallazgos_estado_donut
)
from config import COLORS


def render():
    """Renderiza el dashboard principal."""
    require_role(["auditor", "supervisor", "auditor_campo"])
    user = get_current_user()

    section_header("Panel de control e informes", "Indicadores clave de gestión de auditoría", "📈")

    conn = get_connection()

    # ─── Auto-actualizar hallazgos vencidos ──────────────────────────
    # Marcar como "Vencida" los hallazgos con fecha_compromiso pasada
    today_str = date.today().strftime("%Y-%m-%d")
    conn.execute("""
        UPDATE hallazgos SET estado = 'Vencida'
        WHERE estado IN ('Asignado', 'Sin Asignar')
        AND fecha_compromiso IS NOT NULL
        AND fecha_compromiso < ?
        AND fecha_compromiso != ''
    """, (today_str,))
    conn.commit()

    # Filter by plan
    planes = conn.execute("SELECT id, nombre_plan, anio FROM planes ORDER BY anio DESC").fetchall()
    plan_options = {0: "Todos los planes"}
    plan_options.update({p["id"]: f"{p['nombre_plan']} ({p['anio']})" for p in planes})

    selected_plan = st.selectbox("📅 Filtrar por Plan", list(plan_options.keys()),
                                  format_func=lambda x: plan_options[x])

    st.divider()

    # ─── KPIs ────────────────────────────────────────────────────────
    plan_filter = "AND h.plan_id = ?" if selected_plan else ""
    plan_params = [selected_plan] if selected_plan else []

    proj_filter = "AND pp.plan_id = ?" if selected_plan else ""
    proj_params = [selected_plan] if selected_plan else []

    # Total hallazgos
    total_hallazgos = conn.execute(
        f"SELECT COUNT(*) as cnt FROM hallazgos h WHERE 1=1 {plan_filter}", plan_params
    ).fetchone()["cnt"]

    # Vencidos
    vencidos = conn.execute(
        f"SELECT COUNT(*) as cnt FROM hallazgos h WHERE h.estado = 'Vencida' {plan_filter}", plan_params
    ).fetchone()["cnt"]

    # Aceptados
    aceptados = conn.execute(
        f"SELECT COUNT(*) as cnt FROM hallazgos h WHERE h.estado = 'Aceptada' {plan_filter}", plan_params
    ).fetchone()["cnt"]

    # Pendientes
    pendientes = conn.execute(
        f"SELECT COUNT(*) as cnt FROM hallazgos h WHERE h.estado IN ('Sin Asignar', 'Asignado') {plan_filter}",
        plan_params
    ).fetchone()["cnt"]

    # Plan execution
    total_proyectos = conn.execute(
        f"SELECT COUNT(*) as cnt FROM plan_proyectos pp WHERE 1=1 {proj_filter}", proj_params
    ).fetchone()["cnt"]

    completados = conn.execute(
        f"SELECT COUNT(*) as cnt FROM plan_proyectos pp WHERE pp.estado = 'Completada' {proj_filter}",
        proj_params
    ).fetchone()["cnt"]

    en_proceso_proy = conn.execute(
        f"SELECT COUNT(*) as cnt FROM plan_proyectos pp WHERE pp.estado = 'En Proceso' {proj_filter}",
        proj_params
    ).fetchone()["cnt"]

    sin_iniciar_proy = conn.execute(
        f"SELECT COUNT(*) as cnt FROM plan_proyectos pp WHERE pp.estado = 'Sin Iniciar' {proj_filter}",
        proj_params
    ).fetchone()["cnt"]

    # KPI Cards - Hallazgos
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Total Hallazgos", total_hallazgos, "Registrados", "🔍", COLORS["allports"])
    with k2:
        metric_card("Vencidos", vencidos, "Requieren atención", "⏰", COLORS["danger"])
    with k3:
        metric_card("Aceptados", aceptados, "Resueltos", "✅", COLORS["success"])
    with k4:
        metric_card("Pendientes", pendientes, "En proceso", "⏳", COLORS["warning"])

    st.markdown("")

    # KPI Cards - Proyectos
    k5, k6, k7, k8 = st.columns(4)
    with k5:
        pct = f"{(completados / total_proyectos * 100):.0f}%" if total_proyectos > 0 else "0%"
        metric_card("Ejecución del Plan", pct, f"{completados}/{total_proyectos} proyectos",
                     "📊", COLORS["lochinvar"])
    with k6:
        metric_card("Sin Iniciar", sin_iniciar_proy, "Proyectos pendientes",
                     "🔘", "#94A3B8")
    with k7:
        metric_card("En Proceso", en_proceso_proy, "Proyectos activos",
                     "🔄", COLORS["allports"])
    with k8:
        metric_card("Completados", completados, "Proyectos finalizados",
                     "✅", COLORS["success"])

    st.divider()

    # ─── Charts Row 1 ───────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("##### 🎯 Ejecución del Plan")
        fig_exec = ejecucion_pie(completados, total_proyectos)
        st.pyplot(fig_exec, use_container_width=True)

    with chart_col2:
        st.markdown("##### 📊 Hallazgos por Nivel de Riesgo")
        riesgo_data = {}
        rows = conn.execute(
            f"SELECT nivel_riesgo, COUNT(*) as cnt FROM hallazgos h WHERE 1=1 {plan_filter} GROUP BY nivel_riesgo",
            plan_params
        ).fetchall()
        for r in rows:
            if r["nivel_riesgo"]:
                riesgo_data[r["nivel_riesgo"]] = r["cnt"]
        fig_riesgo = hallazgos_por_riesgo(riesgo_data)
        st.pyplot(fig_riesgo, use_container_width=True)

    st.divider()

    # ─── Charts Row 2 ───────────────────────────────────────────────
    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("##### 🏢 Hallazgos por Área")
        area_data = {}
        rows = conn.execute(
            f"SELECT area, COUNT(*) as cnt FROM hallazgos h WHERE area IS NOT NULL {plan_filter} GROUP BY area ORDER BY cnt DESC",
            plan_params
        ).fetchall()
        for r in rows:
            area_data[r["area"]] = r["cnt"]
        fig_area = hallazgos_por_area(area_data)
        st.pyplot(fig_area, use_container_width=True)

    with chart_col4:
        st.markdown("##### 📋 Estado de Hallazgos")
        estado_data = {}
        rows = conn.execute(
            f"SELECT estado, COUNT(*) as cnt FROM hallazgos h WHERE 1=1 {plan_filter} GROUP BY estado",
            plan_params
        ).fetchall()
        for r in rows:
            estado_data[r["estado"]] = r["cnt"]
        fig_estado = hallazgos_estado_donut(estado_data)
        st.pyplot(fig_estado, use_container_width=True)

    st.divider()

    # ─── Matriz de Riesgos ───────────────────────────────────────────
    st.markdown("##### 🔥 Mapa de Calor - Matriz de Riesgos")
    hallazgos_risk = conn.execute(
        f"SELECT probabilidad, impacto FROM hallazgos h WHERE 1=1 {plan_filter}",
        plan_params
    ).fetchall()
    risk_data = [{"probabilidad": h["probabilidad"], "impacto": h["impacto"]} for h in hallazgos_risk]
    fig_matrix = risk_heatmap(risk_data)
    st.pyplot(fig_matrix, use_container_width=True)

    st.divider()

    # ─── Tendencia Histórica ─────────────────────────────────────────
    st.markdown("##### 📈 Tendencia Histórica de Hallazgos")
    trend_data = {}
    rows = conn.execute("""
        SELECT p.nombre_plan || ' (' || p.anio || ')' as plan_label, COUNT(h.id) as cnt
        FROM planes p
        LEFT JOIN hallazgos h ON h.plan_id = p.id
        GROUP BY p.id
        ORDER BY p.anio
    """).fetchall()
    for r in rows:
        trend_data[r["plan_label"]] = r["cnt"]
    fig_trend = tendencia_historica(trend_data)
    st.pyplot(fig_trend, use_container_width=True)

    st.divider()

    # ─── Diagrama de Gantt ───────────────────────────────────────────
    st.markdown("##### 📅 Diagrama de Gantt — Planificado vs Real")
    gantt_projects = conn.execute(
        f"""SELECT pp.nombre_auditoria, pp.fecha_inicial_planificada, pp.fecha_final_planificada,
                pp.fecha_inicio_real, pp.fecha_final_real, pp.estado
            FROM plan_proyectos pp
            WHERE (pp.fecha_inicial_planificada IS NOT NULL OR pp.fecha_inicio_real IS NOT NULL)
                {proj_filter}
            ORDER BY pp.fecha_inicial_planificada""",
        proj_params
    ).fetchall()
    gantt_data = [dict(g) for g in gantt_projects]
    if gantt_data:
        fig_gantt = gantt_chart(gantt_data)
        st.pyplot(fig_gantt, use_container_width=True)
    else:
        st.info("No hay proyectos con fechas planificadas para mostrar en el Gantt.")

    st.divider()

    # ─── Hallazgos Vencidos Detalle ──────────────────────────────────
    st.markdown("##### ⏰ Hallazgos Vencidos")
    vencidos_detail = conn.execute(
        f"""SELECT h.codigo_hallazgo, h.condicion, h.nivel_riesgo, h.area,
                h.fecha_compromiso, pp.nombre_auditoria, u.nombre_completo as responsable
            FROM hallazgos h
            LEFT JOIN plan_proyectos pp ON h.plan_proyecto_id = pp.id
            LEFT JOIN usuarios u ON h.responsable_id = u.id
            WHERE h.estado = 'Vencida' {plan_filter}
            ORDER BY h.fecha_compromiso""",
        plan_params
    ).fetchall()

    if vencidos_detail:
        for v in vencidos_detail:
            col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
            with col1:
                st.markdown(f"**{v['codigo_hallazgo']}**")
            with col2:
                st.markdown(f"{v['condicion'][:60]}..." if v["condicion"] and len(v["condicion"]) > 60 else v.get("condicion", "—"))
            with col3:
                st.markdown(risk_badge(v.get("nivel_riesgo", "N/A")), unsafe_allow_html=True)
            with col4:
                st.markdown(f"📆 {v.get('fecha_compromiso', '—')}")
    else:
        st.success("🎉 No hay hallazgos vencidos")

    conn.close()
