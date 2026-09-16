import os
from dotenv import load_dotenv

# ==========================================================
# CARGAR VARIABLES DE ENTORNO
# ==========================================================

load_dotenv()

# ==========================================================
# BASE DE DATOS
# ==========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./database.db"
)

# ==========================================================
# DIRECTORIOS
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

THUMBNAIL_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "thumbs"
)

# Crear carpetas automáticamente

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    THUMBNAIL_FOLDER,
    exist_ok=True
)

# ==========================================================
# IMÁGENES
# ==========================================================

MAX_IMAGE_SIZE = 25 * 1024 * 1024

MAX_IMAGE_WIDTH = 4000

MAX_IMAGE_HEIGHT = 4000

THUMBNAIL_WIDTH = 500

THUMBNAIL_HEIGHT = 500

IMAGE_QUALITY = 90

THUMBNAIL_QUALITY = 80

ALLOWED_EXTENSIONS = {

    "jpg",

    "jpeg",

    "png",

    "webp"

}

# ==========================================================
# CORREO
# ==========================================================

SMTP_SERVER = os.getenv(
    "SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        465
    )
)

EMAIL = os.getenv("EMAIL")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ==========================================================
# SITIO WEB
# ==========================================================

SITE_NAME = "AstroLab"

SITE_URL = os.getenv(

    "SITE_URL",

    "http://127.0.0.1:8000"

)

FRONTEND_URL = os.getenv(

    "FRONTEND_URL",

    "http://127.0.0.1:5500"

)

# ==========================================================
# ADMINISTRADOR
# ==========================================================

ADMIN_PASSWORD = "mile1211"  # Escribe la contraseña que tú quieras aquí
UPLOAD_FOLDER = "uploads"
THUMBNAIL_FOLDER = "thumbs"

# ==========================================================
# OPENAI
# ==========================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

# ==========================================================
# CATEGORÍAS
# ==========================================================

DEFAULT_CATEGORIES = [

    "Luna",

    "Sol",

    "Planetas",

    "Galaxias",

    "Nebulosas",

    "Cúmulos",

    "Cometas",

    "Vía Láctea",

    "Deep Sky",

    "Paisaje Nocturno",

    "Satélites",

    "Otros"

]

# ==========================================================
# ESTADOS
# ==========================================================

PHOTO_STATUS = [

    "pendiente",

    "aprobada",

    "rechazada"

]