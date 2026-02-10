# 🛡️ CoopeMédicos — Sistema de Gestión de Auditoría Interna

Sistema integral para la planificación, ejecución, seguimiento y control de auditorías internas, desarrollado con **Streamlit** y **Python**.

---

## 📋 Módulos del Sistema

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | Indicadores clave, gráficos de riesgo, Gantt, tendencias históricas |
| **Universo Auditable** | Gestión de proyectos con estructura Proyecto → Sección → Subsección |
| **Plan Anual** | Planes anuales con copia de proyectos del universo auditable |
| **Hallazgos** | Registro completo con flujo de estados, asignación y respuesta |
| **Evaluación** | Priorización por criticidad con pesos ajustables |
| **Catálogos** | Administración de listas preseleccionables y pesos |
| **Usuarios** | Gestión de perfiles, roles y bitácora de cambios |
| **Exportación** | Reportes en Excel, Word y PDF con logo institucional |

## 👥 Roles del Sistema

| Rol | Permisos |
|-----|----------|
| **Auditor** | Administrador global. Crea/edita/elimina todo. Gestiona catálogos y usuarios. |
| **Supervisor** | Revisa proyectos asignados. Acceso a evaluación y dashboard. |
| **Auditor de Campo** | Ejecuta proyectos asignados. Crea hallazgos. |
| **Auditado** | Solo ve hallazgos asignados y envía respuestas. |

---

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes)

### Pasos

```bash
# 1. Clonar o copiar la carpeta del proyecto
cd coopemedicos_audit

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

### Credenciales Demo
- **Admin:** usuario `admin` / contraseña `admin123`
- **Supervisor:** usuario `supervisor1` / contraseña `admin123`
- **Auditor Campo:** usuario `auditor1` / contraseña `admin123`
- **Auditado:** usuario `auditado1` / contraseña `admin123`

---

## 🗄️ Migración a SQL Server

La aplicación usa **SQLite** como prototipo. Para migrar a **SQL Server**:

### 1. Instalar el driver ODBC y pyodbc

```bash
pip install pyodbc
```

### 2. Editar `database.py`

Reemplazar la función `get_connection()`:

```python
import pyodbc

def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=TU_SERVIDOR;"
        "DATABASE=AuditDB;"
        "Trusted_Connection=yes;"  # Para Active Directory
    )
    conn = pyodbc.connect(conn_str)
    return conn
```

### 3. Crear las tablas en SQL Server

Ejecutar el script de creación adaptando la sintaxis SQLite a T-SQL:
- Cambiar `INTEGER PRIMARY KEY AUTOINCREMENT` → `INT IDENTITY(1,1) PRIMARY KEY`
- Cambiar `TEXT` → `NVARCHAR(MAX)` o `NVARCHAR(500)`
- Cambiar `BLOB` → `VARBINARY(MAX)`
- Cambiar `REAL` → `FLOAT`

### 4. Integración con Active Directory

Para autenticación con AD, reemplazar la función `authenticate()` en `auth.py`:

```python
import ldap3

def authenticate(username, password):
    server = ldap3.Server('ldap://tu-servidor-ad:389')
    conn = ldap3.Connection(server, f'DOMINIO\\{username}', password)
    if conn.bind():
        # Buscar usuario en BD local para obtener rol
        db_conn = get_connection()
        user = db_conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
            (username,)
        ).fetchone()
        db_conn.close()
        return dict(user) if user else None
    return None
```

---

## 🎨 Personalización

### Paleta de Colores
La paleta institucional CoopeMédicos está definida en `config.py`:

| Color | Hex | Uso |
|-------|-----|-----|
| Astronaut | #233F84 | Títulos, textos principales |
| Allports | #0D68A5 | Botones, acentos |
| Cerulean | #18A8E3 | Elementos interactivos |
| Tropical | #0B6957 | Acentos verdes |
| Dark Cyan | #008182 | Gradientes |
| Lochinvar | #24987F | Indicadores positivos |

### Catálogos
Los catálogos se administran desde el módulo **⚙️ Catálogos**:
- Tipos de Auditoría
- Procesos
- Áreas
- Pesos de Evaluación

---

## 📁 Estructura del Proyecto

```
coopemedicos_audit/
├── app.py                  # Aplicación principal
├── config.py               # Configuración y constantes
├── database.py             # Base de datos y esquema
├── auth.py                 # Autenticación
├── requirements.txt        # Dependencias
├── .streamlit/
│   └── config.toml         # Configuración de Streamlit
├── assets/
│   ├── logo.png            # Logo horizontal
│   ├── logo_blanco.png     # Logo blanco
│   └── logo_vertical.png   # Logo vertical
├── modules/
│   ├── catalogos.py        # Gestión de catálogos
│   ├── dashboard.py        # Dashboard y reportes
│   ├── evaluacion.py       # Evaluación del universo
│   ├── exportacion.py      # Exportación PDF/Word/Excel
│   ├── hallazgos.py        # Gestión de hallazgos
│   ├── perfiles.py         # Gestión de usuarios
│   ├── plan_anual.py       # Planes anuales
│   └── universo_auditable.py # Universo auditable
└── utils/
    ├── __init__.py          # Funciones auxiliares
    └── charts.py            # Gráficos (Matplotlib/Seaborn)
```

---

## ⚠️ Notas Importantes

1. **Base de datos**: El archivo `audit_database.db` (SQLite) se crea automáticamente al iniciar la aplicación.
2. **Adjuntos**: Los archivos adjuntos se almacenan como BLOB en la base de datos. Para producción con SQL Server, considere almacenar en red compartida.
3. **Correos automáticos**: La funcionalidad de envío de correos (al asignar/rechazar hallazgos) requiere configuración SMTP adicional.
4. **Respaldos**: Se recomienda respaldar la base de datos periódicamente.

---

**CoopeMédicos R.L. © 2026** — Departamento de Auditoría Interna
