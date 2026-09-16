import re

# ==========================================================
# PALABRAS PROHIBIDAS
# ==========================================================

BANNED_WORDS = [

    "porno",
    "porn",
    "xxx",
    "sexo",
    "desnudo",
    "desnuda",
    "nude",
    "onlyfans",

    "violencia",
    "asesinato",
    "matar",
    "arma",
    "pistola",
    "rifle",
    "terrorismo",

    "droga",
    "cocaina",
    "cocaína",
    "marihuana",
    "heroina",
    "heroína",

    "racismo",
    "nazi",
    "hitler",

    "spam",
    "casino",
    "apuestas",
    "bitcoin gratis",

    "hack",
    "cracker",
    "phishing"

]

# ==========================================================
# LONGITUDES
# ==========================================================

MIN_TITLE = 3
MAX_TITLE = 150

MIN_DESCRIPTION = 0
MAX_DESCRIPTION = 3000


# ==========================================================
# RESULTADO
# ==========================================================

class ReviewResult:

    def __init__(

        self,

        approved=True,

        reason=""

    ):

        self.approved = approved

        self.reason = reason


# ==========================================================
# UTILIDADES
# ==========================================================

def normalize(text: str):

    if text is None:

        return ""

    return text.strip().lower()


def contains_banned_words(text):

    text = normalize(text)

    for word in BANNED_WORDS:

        if word in text:

            return word

    return None


def contains_links(text):

    pattern = r"(http|https|www\.)"

    return re.search(pattern, text, re.IGNORECASE)


# ==========================================================
# VALIDAR TÍTULO
# ==========================================================

def validate_title(title):

    title = normalize(title)

    if len(title) < MIN_TITLE:

        return ReviewResult(

            False,

            "El título es demasiado corto."

        )

    if len(title) > MAX_TITLE:

        return ReviewResult(

            False,

            "El título es demasiado largo."

        )

    banned = contains_banned_words(title)

    if banned:

        return ReviewResult(

            False,

            f"El título contiene una palabra no permitida: {banned}"

        )

    return ReviewResult()


# ==========================================================
# VALIDAR DESCRIPCIÓN
# ==========================================================

def validate_description(description):

    description = normalize(description)

    if len(description) > MAX_DESCRIPTION:

        return ReviewResult(

            False,

            "La descripción supera el máximo permitido."

        )

    banned = contains_banned_words(description)

    if banned:

        return ReviewResult(

            False,

            f"La descripción contiene una palabra no permitida: {banned}"

        )

    if contains_links(description):

        return ReviewResult(

            False,

            "No se permiten enlaces en la descripción."

        )

    return ReviewResult()


# ==========================================================
# VALIDAR EQUIPO
# ==========================================================

def validate_equipment(text):

    if text is None:

        return ReviewResult()

    banned = contains_banned_words(text)

    if banned:

        return ReviewResult(

            False,

            "Información del equipo no válida."

        )

    return ReviewResult()


# ==========================================================
# VALIDAR UBICACIÓN
# ==========================================================

def validate_location(text):

    if text is None:

        return ReviewResult()

    banned = contains_banned_words(text)

    if banned:

        return ReviewResult(

            False,

            "Ubicación no válida."

        )

    return ReviewResult()


# ==========================================================
# VALIDAR IMAGEN
# ==========================================================

def validate_image(filename):

    allowed = [

        ".jpg",

        ".jpeg",

        ".png",

        ".webp"

    ]

    filename = filename.lower()

    valid = False

    for ext in allowed:

        if filename.endswith(ext):

            valid = True

            break

    if not valid:

        return ReviewResult(

            False,

            "Formato de imagen no permitido."

        )

    return ReviewResult()


# ==========================================================
# REVISIÓN GENERAL
# ==========================================================

def review_submission(

    title,

    description,

    equipment,

    location,

    filename

):

    review = validate_title(title)

    if not review.approved:

        return review

    review = validate_description(description)

    if not review.approved:

        return review

    review = validate_equipment(equipment)

    if not review.approved:

        return review

    review = validate_location(location)

    if not review.approved:

        return review

    review = validate_image(filename)

    if not review.approved:

        return review

    return ReviewResult(

        True,

        "Contenido válido."

    )


# ==========================================================
# PREPARADO PARA IA
# ==========================================================

def review_with_ai(image_path):

    """
    Esta función quedará preparada para usar
    la API de OpenAI en el futuro.

    Permitirá revisar automáticamente:

    - desnudez
    - violencia
    - spam
    - contenido ofensivo
    - calidad mínima
    - si realmente parece una astrofotografía

    Por ahora devuelve True.
    """

    return ReviewResult(

        True,

        "Sin revisión IA."

    )