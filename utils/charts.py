"""
Módulo de Gráficos - Seaborn & Matplotlib
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from config import COLORS, CHART_PALETTE, RISK_LEVELS
from io import BytesIO


def setup_style():
    """Configura el estilo global de los gráficos."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.facecolor": "#F5F7FA",
        "axes.facecolor": "#FFFFFF",
        "axes.edgecolor": "#E2E8F0",
        "grid.color": "#F1F5F9",
        "text.color": "#1E293B",
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
    })


def risk_heatmap(data=None):
    """Genera un mapa de calor de riesgos (Matriz 5x5)."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 6))

    matrix = np.array([
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25],
    ])

    color_matrix = np.zeros((5, 5, 4))
    for i in range(5):
        for j in range(5):
            val = matrix[i][j]
            if val <= 4:
                color_matrix[i, j] = [0.063, 0.725, 0.506, 1.0]  # Verde
            elif val <= 9:
                color_matrix[i, j] = [0.961, 0.620, 0.043, 1.0]  # Amarillo
            elif val <= 15:
                color_matrix[i, j] = [0.976, 0.451, 0.086, 1.0]  # Naranja
            else:
                color_matrix[i, j] = [0.863, 0.149, 0.149, 1.0]  # Rojo

    ax.imshow(color_matrix, aspect='auto', origin='lower')

    # Counts
    count_matrix = np.zeros((5, 5), dtype=int)
    if data:
        for item in data:
            p = min(max(item.get("probabilidad", 1), 1), 5) - 1
            i = min(max(item.get("impacto", 1), 1), 5) - 1
            count_matrix[p][i] += 1

    labels_risk = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"]
    for i in range(5):
        for j in range(5):
            count = count_matrix[i][j]
            label = f"{count}" if count > 0 else ""
            ax.text(j, i, label, ha="center", va="center", fontsize=14,
                    fontweight="bold", color="white" if matrix[i][j] > 9 else "#1E293B")

    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(labels_risk, fontsize=9)
    ax.set_yticklabels(labels_risk, fontsize=9)
    ax.set_xlabel("Impacto", fontsize=11, fontweight="bold", color=COLORS["astronaut"])
    ax.set_ylabel("Probabilidad", fontsize=11, fontweight="bold", color=COLORS["astronaut"])
    ax.set_title("Matriz de Riesgos", fontsize=14, fontweight="bold", color=COLORS["astronaut"], pad=15)

    plt.tight_layout()
    return fig


def hallazgos_por_riesgo(data):
    """Gráfico de barras: hallazgos por nivel de riesgo."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    niveles = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"]
    colores = ["#10B981", "#6EE7B7", "#F59E0B", "#F97316", "#DC2626"]
    conteos = [data.get(n, 0) for n in niveles]

    bars = ax.bar(niveles, conteos, color=colores, edgecolor="white", linewidth=1.5, width=0.6)

    for bar, count in zip(bars, conteos):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                    str(count), ha="center", va="bottom", fontweight="bold", fontsize=11)

    ax.set_title("Hallazgos por Nivel de Riesgo", fontsize=14, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    ax.set_ylabel("Cantidad", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig


def hallazgos_por_area(data):
    """Gráfico de barras horizontales: hallazgos por área."""
    setup_style()
    if not data:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", fontsize=14, color="#94A3B8")
        ax.axis('off')
        return fig

    areas = list(data.keys())
    counts = list(data.values())

    fig, ax = plt.subplots(figsize=(7, max(3, len(areas) * 0.6)))
    colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(areas))]

    bars = ax.barh(areas, counts, color=colors, edgecolor="white", linewidth=1, height=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(count), ha="left", va="center", fontweight="bold", fontsize=10)

    ax.set_title("Hallazgos por Área", fontsize=14, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.invert_yaxis()
    plt.tight_layout()
    return fig


def tendencia_historica(data):
    """Gráfico de línea: tendencia de hallazgos en el tiempo."""
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if not data or len(data) == 0:
        ax.text(0.5, 0.5, "Sin datos históricos", ha="center", va="center", fontsize=14, color="#94A3B8")
        ax.axis('off')
        return fig

    periodos = list(data.keys())
    valores = list(data.values())

    ax.plot(periodos, valores, color=COLORS["allports"], linewidth=2.5, marker="o",
            markersize=8, markerfacecolor=COLORS["cerulean"], markeredgecolor="white",
            markeredgewidth=2, zorder=5)
    ax.fill_between(periodos, valores, alpha=0.1, color=COLORS["cerulean"])

    for i, (p, v) in enumerate(zip(periodos, valores)):
        ax.annotate(str(v), (p, v), textcoords="offset points", xytext=(0, 12),
                    ha="center", fontweight="bold", fontsize=10, color=COLORS["astronaut"])

    ax.set_title("Tendencia Histórica de Hallazgos", fontsize=14, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    ax.set_ylabel("Cantidad de Hallazgos", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def gantt_chart(proyectos):
    """Diagrama de Gantt: planificado vs real."""
    setup_style()

    if not proyectos:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5, "Sin proyectos para mostrar", ha="center", va="center",
                fontsize=14, color="#94A3B8")
        ax.axis('off')
        return fig

    fig, ax = plt.subplots(figsize=(12, max(4, len(proyectos) * 1.0)))

    from datetime import datetime

    y_pos = []
    y_labels = []
    has_planned = False
    has_real = False

    for idx, p in enumerate(proyectos):
        y = len(proyectos) - idx - 1
        y_pos.append(y)
        y_labels.append(p.get("nombre_auditoria", f"Proyecto {idx+1}")[:30])

        # Barras planificadas (azul)
        try:
            start_plan = datetime.strptime(p["fecha_inicial_planificada"], "%Y-%m-%d") if p.get("fecha_inicial_planificada") else None
            end_plan = datetime.strptime(p["fecha_final_planificada"], "%Y-%m-%d") if p.get("fecha_final_planificada") else None
            if start_plan and end_plan:
                duration = (end_plan - start_plan).days
                if duration > 0:
                    ax.barh(y + 0.18, duration, left=matplotlib.dates.date2num(start_plan),
                            height=0.3, color=COLORS["cerulean"], alpha=0.5,
                            label="📅 Planificado" if not has_planned else "",
                            edgecolor="white", linewidth=0.5)
                    has_planned = True
        except (ValueError, TypeError):
            pass

        # Barras reales (verde)
        try:
            start_real = datetime.strptime(p["fecha_inicio_real"], "%Y-%m-%d") if p.get("fecha_inicio_real") else None
            end_real = datetime.strptime(p["fecha_final_real"], "%Y-%m-%d") if p.get("fecha_final_real") else None

            # Si está En Proceso y sin fecha final real → extender a hoy
            if start_real and not end_real and p.get("estado") == "En Proceso":
                end_real = datetime.now()

            if start_real and end_real:
                duration = (end_real - start_real).days
                if duration > 0:
                    bar_color = COLORS["lochinvar"] if p.get("estado") == "Completada" else "#F59E0B"
                    ax.barh(y - 0.18, duration, left=matplotlib.dates.date2num(start_real),
                            height=0.3, color=bar_color, alpha=0.85,
                            label="✅ Real (Completado)" if not has_real and p.get("estado") == "Completada"
                            else ("🔄 Real (En Proceso)" if not has_real else ""),
                            edgecolor="white", linewidth=0.5)
                    has_real = True
        except (ValueError, TypeError):
            pass

        # Estado badge a la derecha
        estado = p.get("estado", "")
        estado_colors = {"Sin Iniciar": "#94A3B8", "En Proceso": "#2563EB", "Completada": "#059669"}
        ax.text(1.02, y, estado, transform=ax.get_yaxis_transform(),
                fontsize=7.5, va="center", fontweight="bold",
                color=estado_colors.get(estado, "#475569"),
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor=estado_colors.get(estado, "#CBD5E1"), alpha=0.9))

    # Línea de HOY
    today_num = matplotlib.dates.date2num(datetime.now())
    ax.axvline(x=today_num, color="#DC2626", linewidth=1.5, linestyle="--", alpha=0.7, zorder=10)
    ax.text(today_num, len(proyectos) - 0.3, " Hoy", fontsize=8, color="#DC2626",
            fontweight="bold", ha="left", va="bottom")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=9)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    plt.xticks(rotation=45, ha="right")
    ax.set_title("Diagrama de Gantt — Planificado vs Real", fontsize=14, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    return fig


def ejecucion_pie(ejecutado, total):
    """Gráfico de dona: porcentaje de ejecución del plan."""
    setup_style()
    fig, ax = plt.subplots(figsize=(4, 4))

    pct = (ejecutado / total * 100) if total > 0 else 0
    sizes = [pct, 100 - pct]
    colors_pie = [COLORS["lochinvar"], "#E2E8F0"]

    wedges, _ = ax.pie(sizes, colors=colors_pie, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))

    ax.text(0, 0, f"{pct:.0f}%", ha="center", va="center", fontsize=22,
            fontweight="bold", color=COLORS["astronaut"])
    ax.text(0, -0.15, "Ejecutado", ha="center", va="center", fontsize=9,
            color=COLORS["dark_gray"])

    ax.set_title("Ejecución del Plan", fontsize=13, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    plt.tight_layout()
    return fig


def hallazgos_estado_donut(data):
    """Gráfico de dona: hallazgos por estado."""
    setup_style()
    fig, ax = plt.subplots(figsize=(5, 5))

    if not data or sum(data.values()) == 0:
        ax.text(0.5, 0.5, "Sin hallazgos", ha="center", va="center", fontsize=14, color="#94A3B8")
        ax.axis('off')
        return fig

    labels = list(data.keys())
    sizes = list(data.values())
    colors_map = {
        "Sin Asignar": "#94A3B8",
        "Asignado": "#3B82F6",
        "Vencida": "#DC2626",
        "Respuesta Recibida": "#F59E0B",
        "Aceptada": "#10B981",
    }
    colors = [colors_map.get(l, CHART_PALETTE[i % len(CHART_PALETTE)]) for i, l in enumerate(labels)]

    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, startangle=90,
                                       autopct='%1.0f%%', pctdistance=0.78,
                                       wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2))

    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(8)

    centre_circle = plt.Circle((0, 0), 0.55, fc='white')
    ax.add_artist(centre_circle)

    total = sum(sizes)
    ax.text(0, 0.05, str(total), ha="center", va="center", fontsize=20,
            fontweight="bold", color=COLORS["astronaut"])
    ax.text(0, -0.12, "Total", ha="center", va="center", fontsize=9, color=COLORS["dark_gray"])

    ax.set_title("Estado de Hallazgos", fontsize=13, fontweight="bold",
                 color=COLORS["astronaut"], pad=15)
    plt.tight_layout()
    return fig
