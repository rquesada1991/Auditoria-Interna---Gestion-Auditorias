"""
Módulo de Base de Datos - SQLite (prototipo) / SQL Server (producción)
"""
import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def dict_factory(cursor, row):
    """Row factory que retorna diccionarios en vez de sqlite3.Row."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_connection():
    """Obtiene conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Para migrar a SQL Server, reemplazar get_connection con: ───────
# import pyodbc
# def get_connection():
#     conn_str = (
#         f"DRIVER={SQL_SERVER_CONFIG['driver']};"
#         f"SERVER={SQL_SERVER_CONFIG['server']};"
#         f"DATABASE={SQL_SERVER_CONFIG['database']};"
#         f"Trusted_Connection={SQL_SERVER_CONFIG['trusted_connection']};"
#     )
#     return pyodbc.connect(conn_str)


def init_database():
    """Inicializa todas las tablas de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()

    # ─── Tabla de Usuarios ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            email TEXT,
            rol_global TEXT NOT NULL DEFAULT 'auditado',
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ─── Catálogos ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL,
            descripcion TEXT,
            activo INTEGER DEFAULT 1,
            orden INTEGER DEFAULT 0,
            UNIQUE(tipo, valor)
        )
    """)

    # ─── Pesos de Evaluación ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pesos_evaluacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campo TEXT UNIQUE NOT NULL,
            etiqueta TEXT NOT NULL,
            peso REAL NOT NULL DEFAULT 1.0,
            descripcion TEXT
        )
    """)

    # ─── Universo Auditable - Proyectos ─────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_auditoria TEXT UNIQUE NOT NULL,
            nombre_auditoria TEXT NOT NULL,
            objetivo TEXT,
            tipo_auditoria TEXT,
            proceso TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            fecha_inicial_planificada TEXT,
            fecha_final_planificada TEXT,
            fecha_inicio_real TEXT,
            fecha_final_real TEXT,
            supervisor_id INTEGER,
            auditor_campo_id INTEGER,
            creado_por INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supervisor_id) REFERENCES usuarios(id),
            FOREIGN KEY (auditor_campo_id) REFERENCES usuarios(id),
            FOREIGN KEY (creado_por) REFERENCES usuarios(id)
        )
    """)

    # ─── Adjuntos de Proyectos (Papeles de Trabajo) ─────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adjuntos_proyecto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            nombre_archivo TEXT NOT NULL,
            tipo_archivo TEXT,
            datos BLOB,
            fecha_subida TEXT DEFAULT CURRENT_TIMESTAMP,
            subido_por INTEGER,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
            FOREIGN KEY (subido_por) REFERENCES usuarios(id)
        )
    """)

    # ─── Secciones ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            orden INTEGER DEFAULT 0,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)

    # ─── Subsecciones ────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subsecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seccion_id INTEGER NOT NULL,
            proyecto_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            orden INTEGER DEFAULT 0,
            FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE CASCADE,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)

    # ─── Planes Anuales ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_plan TEXT UNIQUE NOT NULL,
            nombre_plan TEXT NOT NULL,
            objetivo TEXT,
            anio INTEGER NOT NULL,
            estado TEXT DEFAULT 'Activo',
            creado_por INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creado_por) REFERENCES usuarios(id)
        )
    """)

    # ─── Proyectos dentro de un Plan (copia) ─────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            proyecto_origen_id INTEGER NOT NULL,
            codigo_auditoria TEXT NOT NULL,
            nombre_auditoria TEXT NOT NULL,
            objetivo TEXT,
            tipo_auditoria TEXT,
            proceso TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            fecha_inicial_planificada TEXT,
            fecha_final_planificada TEXT,
            fecha_inicio_real TEXT,
            fecha_final_real TEXT,
            supervisor_id INTEGER,
            auditor_campo_id INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES planes(id) ON DELETE CASCADE,
            FOREIGN KEY (proyecto_origen_id) REFERENCES proyectos(id),
            FOREIGN KEY (supervisor_id) REFERENCES usuarios(id),
            FOREIGN KEY (auditor_campo_id) REFERENCES usuarios(id)
        )
    """)

    # ─── Secciones del Plan ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_secciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_proyecto_id INTEGER NOT NULL,
            seccion_origen_id INTEGER,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            orden INTEGER DEFAULT 0,
            FOREIGN KEY (plan_proyecto_id) REFERENCES plan_proyectos(id) ON DELETE CASCADE
        )
    """)

    # ─── Subsecciones del Plan ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_subsecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_seccion_id INTEGER NOT NULL,
            plan_proyecto_id INTEGER NOT NULL,
            subseccion_origen_id INTEGER,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            estado TEXT DEFAULT 'Sin Iniciar',
            orden INTEGER DEFAULT 0,
            FOREIGN KEY (plan_seccion_id) REFERENCES plan_secciones(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_proyecto_id) REFERENCES plan_proyectos(id) ON DELETE CASCADE
        )
    """)

    # ─── Hallazgos ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hallazgos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_hallazgo TEXT UNIQUE NOT NULL,
            plan_subseccion_id INTEGER NOT NULL,
            plan_proyecto_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            condicion TEXT,
            causa TEXT,
            efecto TEXT,
            recomendacion TEXT,
            criterio TEXT,
            probabilidad INTEGER DEFAULT 1,
            impacto INTEGER DEFAULT 1,
            nivel_riesgo TEXT,
            area TEXT,
            responsable_id INTEGER,
            estado TEXT DEFAULT 'Sin Asignar',
            fecha_asignacion TEXT,
            fecha_compromiso TEXT,
            fecha_respuesta TEXT,
            respuesta_auditado TEXT,
            creado_por INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_subseccion_id) REFERENCES plan_subsecciones(id),
            FOREIGN KEY (plan_proyecto_id) REFERENCES plan_proyectos(id),
            FOREIGN KEY (plan_id) REFERENCES planes(id),
            FOREIGN KEY (responsable_id) REFERENCES usuarios(id),
            FOREIGN KEY (creado_por) REFERENCES usuarios(id)
        )
    """)

    # ─── Adjuntos de Hallazgos ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adjuntos_hallazgo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hallazgo_id INTEGER NOT NULL,
            nombre_archivo TEXT NOT NULL,
            tipo_archivo TEXT,
            datos BLOB,
            tipo TEXT DEFAULT 'hallazgo',
            fecha_subida TEXT DEFAULT CURRENT_TIMESTAMP,
            subido_por INTEGER,
            FOREIGN KEY (hallazgo_id) REFERENCES hallazgos(id) ON DELETE CASCADE,
            FOREIGN KEY (subido_por) REFERENCES usuarios(id)
        )
    """)

    # ─── Evaluación del Universo Auditable ───────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluacion_universo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            nivel_riesgo INTEGER DEFAULT 1,
            meses_ultima_auditoria INTEGER DEFAULT 0,
            hallazgos_ult_auditoria INTEGER DEFAULT 0,
            hallazgos_solucionados INTEGER DEFAULT 0,
            estado_auditoria TEXT,
            fecha_auditoria TEXT,
            ciclo_rotacion INTEGER DEFAULT 12,
            nivel_criticidad REAL DEFAULT 0,
            fecha_evaluacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
            UNIQUE(proyecto_id)
        )
    """)

    # ─── Bitácora de Cambios ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            accion TEXT NOT NULL,
            modulo TEXT NOT NULL,
            detalle TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # ─── Asignaciones de Roles por Proyecto ──────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones_proyecto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_proyecto_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            rol TEXT NOT NULL,
            fecha_asignacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_proyecto_id) REFERENCES plan_proyectos(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()

    # ─── Insertar datos iniciales ────────────────────────────────────
    _insert_initial_data(conn)
    conn.close()


def _insert_initial_data(conn):
    """Inserta datos iniciales (catálogos, usuario admin, pesos)."""
    cursor = conn.cursor()

    # Usuario admin por defecto
    cursor.execute("SELECT COUNT(*) as cnt FROM usuarios")
    if cursor.fetchone()["cnt"] == 0:
        import hashlib
        pwd = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol_global)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", pwd, "Administrador del Sistema", "admin@coopemedicos.com", "auditor"))

        # Usuarios demo
        usuarios_demo = [
            ("supervisor1", pwd, "María González", "maria@coopemedicos.com", "supervisor"),
            ("auditor1", pwd, "Carlos Ramírez", "carlos@coopemedicos.com", "auditor_campo"),
            ("auditado1", pwd, "Ana Pérez", "ana@coopemedicos.com", "auditado"),
        ]
        for u in usuarios_demo:
            cursor.execute("""
                INSERT OR IGNORE INTO usuarios (username, password_hash, nombre_completo, email, rol_global)
                VALUES (?, ?, ?, ?, ?)
            """, u)

    # Catálogos iniciales
    catalogos_iniciales = [
        # Tipos de Auditoría
        ("tipo_auditoria", "Auditoría Financiera", "Revisión de estados financieros", 1),
        ("tipo_auditoria", "Auditoría Operativa", "Revisión de procesos operativos", 2),
        ("tipo_auditoria", "Auditoría de Cumplimiento", "Verificación de cumplimiento normativo", 3),
        ("tipo_auditoria", "Auditoría de TI", "Revisión de tecnología de información", 4),
        ("tipo_auditoria", "Auditoría Especial", "Investigaciones especiales", 5),
        ("tipo_auditoria", "Seguimiento", "Seguimiento de hallazgos previos", 6),
        # Procesos
        ("proceso", "Crédito", "Proceso de crédito", 1),
        ("proceso", "Captación", "Proceso de captación", 2),
        ("proceso", "Tesorería", "Proceso de tesorería", 3),
        ("proceso", "Contabilidad", "Proceso contable", 4),
        ("proceso", "Recursos Humanos", "Proceso de RRHH", 5),
        ("proceso", "Tecnología", "Proceso de TI", 6),
        ("proceso", "Cumplimiento", "Proceso de cumplimiento", 7),
        ("proceso", "Operaciones", "Proceso de operaciones", 8),
        # Áreas
        ("area", "Gerencia General", "", 1),
        ("area", "Dirección Financiera", "", 2),
        ("area", "Dirección de Crédito", "", 3),
        ("area", "Dirección de TI", "", 4),
        ("area", "Dirección de RRHH", "", 5),
        ("area", "Dirección de Operaciones", "", 6),
        ("area", "Cumplimiento", "", 7),
        ("area", "Tesorería", "", 8),
    ]

    for cat in catalogos_iniciales:
        cursor.execute("""
            INSERT OR IGNORE INTO catalogos (tipo, valor, descripcion, orden)
            VALUES (?, ?, ?, ?)
        """, cat)

    # Pesos de evaluación iniciales
    pesos_iniciales = [
        ("nivel_riesgo", "Nivel de Riesgo", 0.30, "Riesgo inherente del proceso (1-5)"),
        ("meses_ultima_auditoria", "Meses Última Auditoría", 0.20, "Meses desde la última auditoría"),
        ("hallazgos_ult_auditoria", "Hallazgos Últ. Auditoría", 0.20, "Cantidad de hallazgos encontrados"),
        ("hallazgos_solucionados", "Hallazgos Solucionados", 0.15, "Porcentaje de hallazgos resueltos"),
        ("ciclo_rotacion", "Ciclo de Rotación", 0.15, "Frecuencia de auditoría en meses"),
    ]

    for peso in pesos_iniciales:
        cursor.execute("""
            INSERT OR IGNORE INTO pesos_evaluacion (campo, etiqueta, peso, descripcion)
            VALUES (?, ?, ?, ?)
        """, peso)

    conn.commit()


def log_action(usuario_id, accion, modulo, detalle=""):
    """Registra una acción en la bitácora."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO bitacora (usuario_id, accion, modulo, detalle) VALUES (?, ?, ?, ?)",
        (usuario_id, accion, modulo, detalle)
    )
    conn.commit()
    conn.close()
