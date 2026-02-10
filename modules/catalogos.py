"""
Módulo de Catálogos - Administración de listas preseleccionables
"""
import streamlit as st
from database import get_connection, log_action
from auth import get_current_user, require_role
from utils import section_header, msg_success, msg_error, msg_warning


def render():
    """Renderiza el módulo de catálogos."""
    require_role(["auditor"])
    user = get_current_user()

    section_header("Gestión de Catálogos", "Administre las listas de valores preseleccionables", "⚙️")

    tab1, tab2, tab3 = st.tabs(["📋 Catálogos", "⚖️ Pesos de Evaluación", "➕ Nuevo Valor"])

    with tab1:
        _show_catalogs()

    with tab2:
        _show_weights()

    with tab3:
        _add_catalog_value(user)


def _show_catalogs():
    """Muestra y permite editar los catálogos existentes."""
    conn = get_connection()

    tipos = conn.execute(
        "SELECT DISTINCT tipo FROM catalogos ORDER BY tipo"
    ).fetchall()

    tipo_labels = {
        "tipo_auditoria": "🔍 Tipos de Auditoría",
        "proceso": "⚙️ Procesos",
        "area": "🏢 Áreas",
    }

    for tipo_row in tipos:
        tipo = tipo_row["tipo"]
        label = tipo_labels.get(tipo, f"📁 {tipo.replace('_', ' ').title()}")

        with st.expander(label, expanded=False):
            valores = conn.execute(
                "SELECT * FROM catalogos WHERE tipo = ? ORDER BY orden, valor",
                (tipo,)
            ).fetchall()

            if valores:
                for val in valores:
                    col1, col2, col3, col4 = st.columns([3, 4, 1, 1])
                    with col1:
                        st.text(val["valor"])
                    with col2:
                        st.text(val["descripcion"] or "—")
                    with col3:
                        st.text("✅" if val["activo"] else "❌")
                    with col4:
                        if st.button("🗑️", key=f"del_cat_{val['id']}", help="Desactivar"):
                            conn2 = get_connection()
                            conn2.execute(
                                "UPDATE catalogos SET activo = 0 WHERE id = ?", (val["id"],)
                            )
                            conn2.commit()
                            conn2.close()
                            log_action(st.session_state["user"]["id"], "Desactivar",
                                       "Catálogos", f"Desactivado: {val['valor']} en {tipo}")
                            st.rerun()
            else:
                st.info("No hay valores en este catálogo.")

    conn.close()


def _show_weights():
    """Muestra y permite editar los pesos de evaluación."""
    conn = get_connection()
    pesos = conn.execute("SELECT * FROM pesos_evaluacion ORDER BY id").fetchall()
    conn.close()

    st.markdown("##### Configuración de Pesos para Nivel de Criticidad")
    st.caption("Los pesos determinan la importancia relativa de cada factor en el cálculo de criticidad.")

    total_peso = 0
    with st.form("form_pesos"):
        new_pesos = {}
        for peso in pesos:
            col1, col2, col3 = st.columns([3, 2, 5])
            with col1:
                st.markdown(f"**{peso['etiqueta']}**")
            with col2:
                new_val = st.number_input(
                    "Peso", value=float(peso["peso"]), min_value=0.0, max_value=1.0,
                    step=0.05, key=f"peso_{peso['id']}", label_visibility="collapsed"
                )
                new_pesos[peso["id"]] = new_val
                total_peso += new_val
            with col3:
                st.caption(peso["descripcion"] or "")

        st.markdown(f"**Total de pesos: {total_peso:.2f}** {'✅' if abs(total_peso - 1.0) < 0.01 else '⚠️ Debe sumar 1.0'}")

        if st.form_submit_button("💾 Guardar Pesos", type="primary"):
            if abs(total_peso - 1.0) < 0.01:
                conn = get_connection()
                for pid, pval in new_pesos.items():
                    conn.execute("UPDATE pesos_evaluacion SET peso = ? WHERE id = ?", (pval, pid))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["id"], "Actualizar", "Pesos", "Pesos actualizados")
                msg_success()
                st.rerun()
            else:
                msg_warning("Los pesos deben sumar 1.0")


def _add_catalog_value(user):
    """Formulario para agregar un nuevo valor al catálogo."""
    st.markdown("##### Agregar Nuevo Valor")

    # Form version counter to clear after saving
    form_version = st.session_state.get("catalog_form_version", 0)

    with st.form(f"form_new_catalog_v{form_version}"):
        tipo = st.selectbox("Tipo de Catálogo", [
            "tipo_auditoria", "proceso", "area"
        ], format_func=lambda x: {
            "tipo_auditoria": "Tipo de Auditoría",
            "proceso": "Proceso",
            "area": "Área"
        }.get(x, x))

        valor = st.text_input("Valor *", placeholder="Nombre del valor")
        descripcion = st.text_input("Descripción", placeholder="Descripción opcional")
        orden = st.number_input("Orden", value=0, min_value=0, step=1)

        if st.form_submit_button("➕ Agregar", type="primary"):
            if valor.strip():
                try:
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO catalogos (tipo, valor, descripcion, orden) VALUES (?, ?, ?, ?)",
                        (tipo, valor.strip(), descripcion.strip(), orden)
                    )
                    conn.commit()
                    conn.close()
                    log_action(user["id"], "Crear", "Catálogos", f"Nuevo: {valor} en {tipo}")
                    msg_success()
                    st.session_state["catalog_form_version"] = form_version + 1
                    st.rerun()
                except Exception:
                    msg_error()
            else:
                msg_warning()
