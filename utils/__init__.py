"""
Funciones auxiliares
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from database import get_connection


# ─── Mensajes estandarizados con delay ───────────────────────────
def msg_success(text="Datos Guardados Correctamente"):
    """Muestra mensaje de éxito y espera 3 segundos."""
    st.success(f"✅ {text}")
    time.sleep(3)


def msg_error(text="Hubo un problema al guardar"):
    """Muestra mensaje de error y espera 3 segundos."""
    st.error(f"❌ {text}")
    time.sleep(3)


def msg_warning(text="Revisar parámetros antes de continuar"):
    """Muestra mensaje de advertencia y espera 3 segundos."""
    st.warning(f"⚠️ {text}")
    time.sleep(3)


def get_catalog_values(tipo):
    """Obtiene los valores de un catálogo específico."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT valor FROM catalogos WHERE tipo = ? AND activo = 1 ORDER BY orden",
        (tipo,)
    ).fetchall()
    conn.close()
    return [r["valor"] for r in rows]


def get_users_by_role(rol=None):
    """Obtiene usuarios filtrados por rol."""
    conn = get_connection()
    if rol:
        rows = conn.execute(
            "SELECT * FROM usuarios WHERE rol_global = ? AND activo = 1 ORDER BY nombre_completo",
            (rol,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM usuarios WHERE activo = 1 ORDER BY nombre_completo"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_users():
    """Obtiene todos los usuarios activos."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM usuarios WHERE activo = 1 ORDER BY nombre_completo"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def format_date(date_str):
    """Formatea una fecha para mostrar."""
    if not date_str:
        return "—"
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str


def calculate_risk_level(probabilidad, impacto):
    """Calcula el nivel de riesgo basado en probabilidad e impacto."""
    promedio = (probabilidad + impacto) / 2
    if promedio <= 1.0:
        return "Muy Bajo"
    elif promedio <= 2.0:
        return "Bajo"
    elif promedio <= 3.0:
        return "Medio"
    elif promedio <= 4.0:
        return "Alto"
    else:
        return "Muy Alto"


def risk_badge(level):
    """Genera un badge HTML para el nivel de riesgo."""
    colors = {
        "Muy Bajo": ("#ECFDF5", "#059669"),
        "Bajo": ("#D1FAE5", "#047857"),
        "Medio": ("#FEF3C7", "#D97706"),
        "Alto": ("#FED7AA", "#EA580C"),
        "Muy Alto": ("#FEE2E2", "#DC2626"),
    }
    bg, fg = colors.get(level, ("#F1F5F9", "#475569"))
    return f'<span style="background:{bg}; color:{fg}; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;">{level}</span>'


def status_badge(estado):
    """Genera un badge HTML para el estado."""
    colors = {
        "Sin Iniciar": ("#F1F5F9", "#475569"),
        "En Proceso": ("#DBEAFE", "#2563EB"),
        "Completada": ("#ECFDF5", "#059669"),
        "Sin Asignar": ("#F1F5F9", "#475569"),
        "Asignado": ("#DBEAFE", "#2563EB"),
        "Vencida": ("#FEE2E2", "#DC2626"),
        "Respuesta Recibida": ("#FEF3C7", "#D97706"),
        "Aceptada": ("#ECFDF5", "#059669"),
        "Activo": ("#ECFDF5", "#059669"),
        "Cerrado": ("#F1F5F9", "#475569"),
    }
    bg, fg = colors.get(estado, ("#F1F5F9", "#475569"))
    return f'<span style="background:{bg}; color:{fg}; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:600;">{estado}</span>'


def metric_card(title, value, subtitle="", icon="📊", color="#0D68A5"):
    """Genera una tarjeta de métrica estilizada."""
    st.markdown(f"""
    <div style="background:white; border-radius:12px; padding:1.2rem; border-left:4px solid {color}; 
                box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <p style="color:#64748B; font-size:0.8rem; margin:0; text-transform:uppercase; letter-spacing:0.5px;">{title}</p>
                <p style="color:#1E293B; font-size:1.8rem; font-weight:700; margin:0.2rem 0;">{value}</p>
                <p style="color:#94A3B8; font-size:0.75rem; margin:0;">{subtitle}</p>
            </div>
            <div style="font-size:2rem;">{icon}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle="", icon=""):
    """Genera un encabezado de sección estilizado."""
    st.markdown(f"""
    <div style="margin-bottom:1.5rem; padding-bottom:0.8rem; border-bottom:2px solid #E2E8F0;">
        <h2 style="color:#233F84; margin:0; font-size:1.5rem;">
            {icon} {title}
        </h2>
        {f'<p style="color:#64748B; margin:0.3rem 0 0 0; font-size:0.9rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
