from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request as UrlRequest, urlopen
try:
    from zoneinfo import ZoneInfo
    _ZoneInfoNotFoundError = Exception
except Exception:
    ZoneInfo = None
    _ZoneInfoNotFoundError = Exception
from xml.etree import ElementTree as ET
import hmac
import ipaddress
import json
import re
import time
import uuid

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, inspect, text
from sqlalchemy.orm import Session

from config import ADMIN_TOKEN, ALLOWED_HOSTS, INSTAGRAM_USERNAME, NASA_API_KEY
from database import Base, SessionLocal, engine, get_db
from models import Article, AstronomicalEvent, Category, CommunityNote, ContactRequest, NoteLike, Photo, PhotoLike, PhotoStatus, Product
from schemas import ArticleCreate, ContactRequestCreate, EventCreate, NoteCreate, NoteLikeCreate, PhotoLikeCreate, ProductCreate

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / 'static'
UPLOAD_DIR = STATIC_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title='ADV-Lab', version='7.1.0')
app.add_middleware(GZipMiddleware, minimum_size=1200)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

COMMUNITY_CATEGORIES = ['Luna', 'Planetas', 'Cielo profundo', 'Sol', 'Paisaje nocturno', 'Vía Láctea', 'Nebulosas', 'Galaxias', 'Estrellas', 'Espacio', 'Otros']
PRODUCT_CATEGORIES = ['Láminas', 'Papelería', 'Decoración', 'Accesorios', 'Regalos', 'Otros']
NASA_APOD_URL = f'https://api.nasa.gov/planetary/apod?api_key={quote(NASA_API_KEY)}'
NASA_NEWS_RSS = 'https://www.nasa.gov/rss/dyn/breaking_news.rss'
JPL_NEWS_RSS = 'https://cneos.jpl.nasa.gov/feed/news.xml'
INSTAGRAM_DM = f'https://ig.me/m/{INSTAGRAM_USERNAME}'
FALLBACK_UNIVERSE = 'https://science.nasa.gov/wp-content/uploads/2023/04/orion-nebula-xlarge_web-jpg.webp'
try:
    APP_TIMEZONE = ZoneInfo('America/Argentina/Buenos_Aires') if ZoneInfo else None
except Exception:
    APP_TIMEZONE = None
if APP_TIMEZONE is None:
    from datetime import timezone as _timezone
    APP_TIMEZONE = _timezone(timedelta(hours=-3))

DAILY_WORDS = [
    ('Espectro', 'Distribución de la energía o intensidad en función de una variable, como la longitud de onda.'),
    ('Paralaje', 'Cambio aparente de posición de un objeto cuando cambia el punto de observación.'),
    ('Magnitud', 'Escala logarítmica utilizada para expresar el brillo aparente de los objetos celestes.'),
    ('Nebulosa', 'Nube de gas y polvo interestelar donde pueden ocurrir procesos de formación estelar.'),
    ('Entropía', 'Magnitud física relacionada con el número de configuraciones microscópicas compatibles con un estado.'),
    ('Fotón', 'Cuanto de la radiación electromagnética y partícula mediadora de la interacción electromagnética.'),
    ('Gravedad', 'Interacción asociada a la curvatura del espacio-tiempo en relatividad general y a la atracción entre masas en la aproximación clásica.'),
    ('Exoplaneta', 'Planeta que orbita una estrella distinta del Sol.'),
    ('Púlsar', 'Estrella de neutrones que produce pulsos periódicos de radiación debido a su rotación y geometría magnética.'),
    ('Corrimiento al rojo', 'Desplazamiento de la luz hacia longitudes de onda más largas, que puede aportar información sobre movimiento y expansión cósmica.'),
    ('Apertura', 'Diámetro efectivo del sistema óptico que recoge luz en un telescopio.'),
    ('Resolución', 'Capacidad de distinguir detalles cercanos espacialmente o angularmente.'),
    ('Plasma', 'Estado de la materia con partículas cargadas libres en proporción suficiente para modificar su comportamiento colectivo.'),
    ('Cúmulo', 'Conjunto de estrellas o galaxias que puede estar ligado gravitacionalmente o formar una concentración aparente en el cielo.'),
    ('Cosmología', 'Rama de la física y la astronomía que estudia el universo a gran escala y su evolución.'),
    ('Órbita', 'Trayectoria determinada por la dinámica gravitatoria de un cuerpo alrededor de otro.'),
    ('Afelio', 'Punto de la órbita alrededor del Sol más alejado del Sol.'),
    ('Perihelio', 'Punto de la órbita alrededor del Sol más cercano al Sol.'),
    ('Supernova', 'Explosión estelar extremadamente energética asociada al final de determinadas estrellas.'),
    ('Espectroscopia', 'Técnica que estudia la interacción entre materia y radiación en función de la longitud de onda o frecuencia.'),
    ('Interferometría', 'Método que combina ondas para extraer información sobre fase, distancia, tamaño o estructura.'),
    ('Radiactividad', 'Emisión espontánea de partículas o radiación por núcleos atómicos inestables.'),
    ('Inercia', 'Propiedad de un cuerpo por la cual mantiene su estado de movimiento si no actúa una fuerza neta.'),
    ('Campo', 'Entidad física que asigna magnitudes a puntos del espacio y puede describir interacciones y transporte de energía.'),
    ('Radiación', 'Energía que se propaga mediante ondas electromagnéticas o partículas.'),
    ('Astrometría', 'Medición precisa de posiciones, movimientos y paralajes de objetos celestes.'),
    ('Heliosfera', 'Región espacial dominada por el viento solar y el campo magnético del Sol.'),
    ('Acreción', 'Proceso por el cual materia se acumula alrededor de un objeto bajo la acción de la gravedad y otras interacciones.'),
]

PLANETS = [
    {'name': 'Mercurio', 'year_days': 88.0, 'gravity': 3.7, 'accent': '☿', 'fact': 'El año más corto del sistema solar: cerca de 88 días terrestres.'},
    {'name': 'Venus', 'year_days': 224.7, 'gravity': 8.9, 'accent': '♀', 'fact': 'Su año dura unos 225 días terrestres y su atmósfera es extremadamente densa.'},
    {'name': 'Tierra', 'year_days': 365.2, 'gravity': 9.8, 'accent': '⊕', 'fact': 'Usamos la Tierra como referencia para edad y peso.'},
    {'name': 'Marte', 'year_days': 687.0, 'gravity': 3.7, 'accent': '♂', 'fact': 'Un año marciano dura casi 1,9 años terrestres.'},
    {'name': 'Júpiter', 'year_days': 4331, 'gravity': 23.1, 'accent': '♃', 'fact': 'Su órbita tarda alrededor de 11,9 años terrestres.'},
    {'name': 'Saturno', 'year_days': 10747, 'gravity': 9.0, 'accent': '♄', 'fact': 'Su año dura casi 29,5 años terrestres.'},
    {'name': 'Urano', 'year_days': 30589, 'gravity': 8.7, 'accent': '♅', 'fact': 'Necesita unos 84 años terrestres para completar una órbita.'},
    {'name': 'Neptuno', 'year_days': 59800, 'gravity': 11.0, 'accent': '♆', 'fact': 'Su año dura aproximadamente 165 años terrestres.'},
]

MOON_PHASES_2026 = [
    ('2026-01-03', 'Luna llena', '10:03 UTC', 'full'), ('2026-01-10', 'Cuarto menguante', '15:48 UTC', 'last'), ('2026-01-18', 'Luna nueva', '19:52 UTC', 'new'), ('2026-01-26', 'Cuarto creciente', '04:47 UTC', 'first'),
    ('2026-02-01', 'Luna llena', '22:09 UTC', 'full'), ('2026-02-09', 'Cuarto menguante', '12:43 UTC', 'last'), ('2026-02-17', 'Luna nueva', '12:01 UTC', 'new'), ('2026-02-24', 'Cuarto creciente', '12:27 UTC', 'first'),
    ('2026-03-03', 'Luna llena', '11:38 UTC', 'full'), ('2026-03-11', 'Cuarto menguante', '09:38 UTC', 'last'), ('2026-03-19', 'Luna nueva', '01:23 UTC', 'new'), ('2026-03-25', 'Cuarto creciente', '19:18 UTC', 'first'),
    ('2026-04-02', 'Luna llena', '02:12 UTC', 'full'), ('2026-04-10', 'Cuarto menguante', '04:51 UTC', 'last'), ('2026-04-17', 'Luna nueva', '11:52 UTC', 'new'), ('2026-04-24', 'Cuarto creciente', '02:32 UTC', 'first'),
    ('2026-05-01', 'Luna llena', '17:23 UTC', 'full'), ('2026-05-09', 'Cuarto menguante', '21:10 UTC', 'last'), ('2026-05-16', 'Luna nueva', '20:01 UTC', 'new'), ('2026-05-23', 'Cuarto creciente', '11:11 UTC', 'first'), ('2026-05-31', 'Luna llena', '08:45 UTC', 'full'),
    ('2026-06-08', 'Cuarto menguante', '10:00 UTC', 'last'), ('2026-06-15', 'Luna nueva', '02:54 UTC', 'new'), ('2026-06-21', 'Cuarto creciente', '21:55 UTC', 'first'), ('2026-06-29', 'Luna llena', '23:56 UTC', 'full'),
    ('2026-07-07', 'Cuarto menguante', '19:29 UTC', 'last'), ('2026-07-14', 'Luna nueva', '09:43 UTC', 'new'), ('2026-07-21', 'Cuarto creciente', '11:05 UTC', 'first'), ('2026-07-29', 'Luna llena', '14:36 UTC', 'full'),
    ('2026-08-06', 'Cuarto menguante', '02:21 UTC', 'last'), ('2026-08-12', 'Luna nueva', '17:37 UTC', 'new'), ('2026-08-20', 'Cuarto creciente', '02:46 UTC', 'first'), ('2026-08-28', 'Luna llena', '04:18 UTC', 'full'),
    ('2026-09-04', 'Cuarto menguante', '07:51 UTC', 'last'), ('2026-09-11', 'Luna nueva', '03:27 UTC', 'new'), ('2026-09-18', 'Cuarto creciente', '20:44 UTC', 'first'), ('2026-09-26', 'Luna llena', '16:49 UTC', 'full'),
    ('2026-10-03', 'Cuarto menguante', '13:25 UTC', 'last'), ('2026-10-10', 'Luna nueva', '15:50 UTC', 'new'), ('2026-10-18', 'Cuarto creciente', '16:12 UTC', 'first'), ('2026-10-26', 'Luna llena', '04:12 UTC', 'full'),
    ('2026-11-01', 'Cuarto menguante', '20:28 UTC', 'last'), ('2026-11-09', 'Luna nueva', '07:02 UTC', 'new'), ('2026-11-17', 'Cuarto creciente', '11:48 UTC', 'first'), ('2026-11-24', 'Luna llena', '14:53 UTC', 'full'),
    ('2026-12-01', 'Cuarto menguante', '06:08 UTC', 'last'), ('2026-12-09', 'Luna nueva', '00:52 UTC', 'new'), ('2026-12-17', 'Cuarto creciente', '05:42 UTC', 'first'), ('2026-12-24', 'Luna llena', '01:28 UTC', 'full'), ('2026-12-30', 'Cuarto menguante', '18:59 UTC', 'last')
]

ANNUAL_EVENTS_2026 = [
    ('2026-01-02', 'Lluvia de meteoros Cuadrántidas', 'Una de las principales lluvias anuales de meteoros.', 'meteor'),
    ('2026-01-10', 'Júpiter en oposición', 'Momento destacado para observar y fotografiar Júpiter.', 'planet'),
    ('2026-02-17', 'Eclipse solar anular', 'Visible principalmente desde regiones antárticas.', 'eclipse'),
    ('2026-03-20', 'Equinoccio de marzo', 'La astronomía de estaciones marca el cambio de estación en ambos hemisferios.', 'season'),
    ('2026-04-21', 'Líridas', 'Lluvia anual de meteoros asociada al cometa Thatcher.', 'meteor'),
    ('2026-05-05', 'Eta Acuáridas', 'Lluvia de meteoros asociada al cometa Halley.', 'meteor'),
    ('2026-06-21', 'Solsticio de junio', 'Solsticio que inicia el invierno astronómico en el hemisferio sur.', 'season'),
    ('2026-07-30', 'Delta Acuáridas del Sur', 'Lluvia de meteoros destacada del invierno austral.', 'meteor'),
    ('2026-08-12', 'Eclipse solar total', 'Visible en Groenlandia, Islandia y España según la guía anual de NASA.', 'eclipse'),
    ('2026-08-13', 'Perseidas', 'Una de las lluvias de meteoros más conocidas del año.', 'meteor'),
    ('2026-09-18', 'Venus en máxima brillantez vespertina', 'NASA señala esta fecha como el pico de brillo para su aparición de la tarde.', 'planet'),
    ('2026-09-19', 'International Observe the Moon Night', 'Noche internacional para observar la Luna y aprender sobre ciencia lunar.', 'moon'),
    ('2026-09-22', 'Equinoccio de septiembre', 'En el hemisferio sur comienza la primavera astronómica.', 'season'),
    ('2026-09-25', 'Neptuno en oposición', 'Ventana destacada para observar Neptuno con ayuda óptica.', 'planet'),
    ('2026-09-26', 'Luna de la cosecha cerca de Saturno y Neptuno', 'NASA destaca el encuentro aparente de la Luna con estos planetas.', 'moon'),
    ('2026-10-04', 'Saturno en oposición', 'Buen momento del año para observar y fotografiar Saturno.', 'planet'),
    ('2026-10-07', 'Dracónidas', 'Lluvia anual de meteoros de octubre.', 'meteor'),
    ('2026-10-21', 'Oriónidas', 'Lluvia de meteoros asociada al cometa Halley.', 'meteor'),
    ('2026-11-04', 'Táuridas', 'Lluvia de meteoros de actividad amplia y extendida.', 'meteor'),
    ('2026-11-17', 'Leónidas', 'Lluvia de meteoros asociada al cometa Tempel-Tuttle.', 'meteor'),
    ('2026-11-24', 'Superluna', 'NASA incluye esta fecha entre sus eventos destacados del año.', 'moon'),
    ('2026-11-25', 'Urano en oposición', 'Ventana favorable para observación telescópica.', 'planet'),
    ('2026-12-21', 'Solsticio de diciembre', 'En el hemisferio sur comienza el verano astronómico.', 'season'),
    ('2026-12-14', 'Géminidas', 'Una de las lluvias de meteoros más conocidas del año.', 'meteor'),
    ('2026-12-24', 'Superluna', 'NASA destaca una superluna para la víspera de Navidad.', 'moon'),
    ('2026-12-21', 'Úrsidas', 'Lluvia anual de meteoros de diciembre.', 'meteor')
]

HISTORY = [
    {
        'year': '1871–1877',
        'title': 'Córdoba y el comienzo de una astronomía sistemática',
        'lead': 'El Observatorio Astronómico Nacional nació en una Argentina que todavía estaba construyendo sus instituciones científicas.',
        'image': 'https://science.nasa.gov/wp-content/uploads/2023/04/orion-nebula-xlarge_web-jpg.webp',
        'body': [
            'El Observatorio Astronómico Nacional Argentino fue inaugurado en Córdoba el 24 de octubre de 1871. Su creación estuvo impulsada por Domingo Faustino Sarmiento y quedó estrechamente ligada al astrónomo estadounidense Benjamin A. Gould, que asumió como primer director. La institución no apareció solamente para mirar el cielo: nació para producir mediciones sistemáticas, catálogos y conocimiento útil para una nación que estaba organizando su infraestructura científica.',
            'Gould y su equipo trabajaron con instrumentos dedicados a medir posiciones estelares y a construir catálogos. Una de las obras más conocidas fue Uranometria Argentina, publicada en 1877, que reunió observaciones detalladas de estrellas visibles desde el hemisferio sur. Para la astronomía del siglo XIX, medir bien era una tarea central: una posición, una magnitud o una diferencia de tiempo podían convertirse en una pieza de evidencia sobre la estructura y el movimiento del cielo.',
            'La historia del observatorio también muestra algo interesante para quienes hoy aprenden programación. La ciencia moderna necesita tecnología, pero también necesita procedimientos repetibles, registros y bases de datos. Antes de hablar de software se hablaba de cuadernos, placas, tablas y catálogos; el principio era el mismo: transformar observaciones en información que otras personas pudieran revisar y utilizar.',
            'Desde Córdoba comenzó una tradición institucional que atravesaría generaciones de astrónomos, ingenieros, físicos, calculistas y técnicos. El observatorio produciría además trabajos relacionados con la hora oficial, meteorología, cartografía y observación sistemática, ampliando la idea de que observar el cielo podía tener consecuencias concretas en la vida científica y tecnológica del país.'
        ],
        'sources': [
            {'label': 'Observatorio Astronómico de Córdoba · Historia', 'url': 'https://oac.unc.edu.ar/institucional/historia/'},
            {'label': 'NASA · Universo', 'url': 'https://science.nasa.gov/universe/'}
        ],
        'tags': ['OAC', 'Benjamin Gould', 'Uranometria Argentina', '1871']
    },
    {
        'year': '1881–1911',
        'title': 'La Plata: astronomía, geofísica y formación científica',
        'lead': 'El Observatorio Astronómico de La Plata nació con una mirada que unía el cielo con la Tierra.',
        'image': 'https://images.unsplash.com/photo-1517976487492-5750f3195933?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'El proyecto científico de La Plata comenzó a desarrollarse a fines del siglo XIX y el observatorio quedó asociado desde temprano no solo con la astronomía, sino también con la geofísica. Esa combinación es importante porque recuerda que las ciencias del espacio no crecieron aisladas: medir estrellas, estudiar el campo magnético terrestre, registrar posiciones o trabajar con el tiempo formaban parte de una misma cultura de observación.',
            'La institución fue también un lugar de formación. El desarrollo de la astronomía argentina requirió personas capaces de operar instrumentos, hacer cálculos, comparar observaciones y construir series de datos. Con el paso de las décadas, estas tareas se transformaron profundamente, pero todavía podemos reconocer en ellas el origen de actividades que hoy hacemos con computadoras: limpiar datos, detectar patrones, convertir unidades y automatizar cálculos.',
            'La historia del observatorio muestra además la importancia de la colaboración entre disciplinas. Astronomía, geodesia, meteorología, geomagnetismo y física compartían instrumentos, procedimientos y problemas. Para quien se acerca hoy a la astrofísica, esa mezcla es una buena advertencia: muchas preguntas científicas interesantes aparecen justamente en las fronteras entre disciplinas.',
            'El legado de La Plata no se limita a su edificio. A lo largo del siglo XX, la institución ayudó a formar generaciones de científicos y sostuvo una tradición observacional que terminó conectándose con la astronomía moderna, la física y la exploración del ambiente terrestre y espacial.'
        ],
        'sources': [
            {'label': 'FCAGLP · Historia del Observatorio de La Plata', 'url': 'https://www.fcaglp.unlp.edu.ar/uploads/docs/perdomo__historia_obsevatorio.pdf'},
            {'label': 'UNLP · Facultad de Ciencias Astronómicas y Geofísicas', 'url': 'https://www.fcaglp.unlp.edu.ar/'}
        ],
        'tags': ['La Plata', 'geofísica', 'observación', 'formación']
    },
    {
        'year': '1930–1942',
        'title': 'Ramón Enrique Gaviola y la construcción de instrumentos',
        'lead': 'La física y la ingeniería óptica comenzaron a ser parte esencial de la astronomía argentina.',
        'image': 'https://images.unsplash.com/photo-1444703686981-a3abb4c4d4fe?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'Ramón Enrique Gaviola es una de las figuras más importantes de la historia científica argentina del siglo XX. Su trayectoria combinó física, instrumentación y astronomía, y está vinculada de manera decisiva con el desarrollo de grandes instrumentos ópticos en el país. Esta parte de la historia es especialmente valiosa porque muestra que una observación astronómica empieza mucho antes de la imagen final: comienza con materiales, óptica, mecánica, medición y diseño.',
            'El desarrollo del telescopio de Bosque Alegre representó una apuesta por construir infraestructura científica propia. El instrumento fue inaugurado en 1942 y se convirtió en una pieza central del trabajo astronómico del país. La construcción y puesta a punto de un telescopio de este tipo exige resolver problemas físicos y de ingeniería que anticipan muchas prácticas presentes hoy en la industria espacial.',
            'Gaviola también estuvo relacionado con la formación de personas y con la discusión sobre cómo desarrollar ciencia de alta calidad en la Argentina. Su historia ayuda a entender una idea que sigue siendo actual: para hacer astronomía no alcanza con comprar instrumentos. También hace falta saber diseñarlos, mantenerlos, calibrarlos y entender las limitaciones de las mediciones.',
            'Para alguien interesado en software, esta historia tiene otra lectura. Un instrumento científico puede imaginarse como una cadena de información: un fenómeno físico produce una señal, un sistema óptico o electrónico la registra, un instrumento la digitaliza y, finalmente, un algoritmo ayuda a convertirla en datos útiles. Esa cadena es hoy uno de los puentes más directos entre física y programación.'
        ],
        'sources': [
            {'label': 'Observatorio Astronómico de Córdoba · Historia', 'url': 'https://oac.unc.edu.ar/institucional/historia/'},
            {'label': 'Instituto Balseiro · Historia', 'url': 'https://www.ib.edu.ar/institucional/historia/'}
        ],
        'tags': ['Gaviola', 'Bosque Alegre', 'óptica', 'instrumentación']
    },
    {
        'year': '1955–1969',
        'title': 'El crecimiento de la física y la formación de nuevas generaciones',
        'lead': 'La astronomía argentina se apoyó cada vez más en una comunidad de físicos capaz de trabajar con problemas fundamentales.',
        'image': 'https://images.unsplash.com/photo-1517976547714-720226b864c1?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'La segunda mitad del siglo XX fue decisiva para la ciencia argentina. La creación del Instituto Balseiro en 1955 consolidó en Bariloche un espacio dedicado a la formación de físicos e ingenieros con una fuerte combinación de teoría, experimentación e instrumentación. Esa tradición no pertenece únicamente a la física nuclear: ayudó a ampliar la capacidad del país para abordar problemas científicos y tecnológicos complejos.',
            'La astrofísica se beneficia especialmente de este cruce. Para comprender una estrella no basta con reconocer su brillo. Se necesita física de plasmas, espectroscopia, radiación, mecánica, estadística y modelos matemáticos. La astronomía moderna es, en gran medida, una forma de física aplicada al universo.',
            'Este crecimiento institucional también cambió la relación entre ciencia y tecnología. Los observatorios dejaron de ser solamente lugares de observación y pasaron a depender cada vez más de laboratorios, detectores, electrónica, computación y técnicas de análisis. El dato astronómico comenzaba lentamente a parecerse a lo que hoy reconocemos como un flujo tecnológico completo.',
            'La lección para una comunidad aficionada es sencilla y poderosa: aprender astronomía puede llevar naturalmente a muchas otras disciplinas. Una persona puede empezar fotografiando la Luna y terminar interesándose por óptica, procesamiento de imágenes, electrónica, estadística o programación científica.'
        ],
        'sources': [
            {'label': 'Instituto Balseiro · Historia', 'url': 'https://www.ib.edu.ar/institucional/historia/'},
            {'label': 'IAFE · Historia', 'url': 'https://www.iafe.uba.ar/institucional/historia/'}
        ],
        'tags': ['física', 'Instituto Balseiro', 'formación', 'astrofísica']
    },
    {
        'year': '1962–actualidad',
        'title': 'Radioastronomía: aprender a escuchar el universo',
        'lead': 'Con el Instituto Argentino de Radioastronomía, el cielo argentino comenzó a estudiarse también en longitudes de onda de radio.',
        'image': 'https://images.unsplash.com/photo-1446776877081-d282a0f896e2?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'El Instituto Argentino de Radioastronomía (IAR) fue creado el 27 de abril de 1962 por un acuerdo entre la Universidad de Buenos Aires, CONICET y la Universidad Nacional de La Plata. Sus actividades científicas comenzaron en 1966 y ayudaron a consolidar en el país una forma distinta de estudiar el universo: en lugar de depender únicamente de la luz visible, la radioastronomía registra ondas de radio emitidas por procesos astrofísicos.',
            'Cambiar de longitud de onda cambia la pregunta que podemos hacer. Las ondas de radio permiten estudiar regiones que pueden ser difíciles de observar ópticamente, además de fenómenos como estructuras magnéticas, gas interestelar, fuentes compactas y emisiones producidas por partículas energéticas. La astronomía, así, se transforma en una disciplina que escucha y mide diferentes formas de radiación.',
            'Un radiotelescopio también es una gran lección de ingeniería. La señal que llega es extremadamente débil y necesita amplificación, filtrado, calibración y tratamiento matemático. El trabajo científico depende tanto del instrumento como de los algoritmos capaces de limpiar el ruido y recuperar información.',
            'En otras palabras, la radioastronomía representa uno de los puntos donde física, electrónica y computación dejan de ser áreas separadas. Para una comunidad interesada en software, es una demostración histórica de algo que sigue vigente: a veces la ciencia avanza porque inventamos una nueva manera de transformar una señal en datos.'
        ],
        'sources': [
            {'label': 'IAR · Historia institucional', 'url': 'https://www.iar.unlp.edu.ar/historia/'},
            {'label': 'CONICET', 'url': 'https://www.conicet.gov.ar/'}
        ],
        'tags': ['IAR', 'radioastronomía', 'señales', 'electrónica']
    },
    {
        'year': '1969',
        'title': 'IAFE: astronomía y física espacial como una misma conversación',
        'lead': 'La creación del IAFE conectó investigación astronómica, física y problemas ligados al espacio.',
        'image': 'https://images.unsplash.com/photo-1614728263952-84ea256f9679?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'El Instituto de Astronomía y Física del Espacio (IAFE) fue creado el 29 de diciembre de 1969, a partir de una estructura de investigación que ya vinculaba a CONICET y la Universidad de Buenos Aires. El instituto representa una evolución natural de la ciencia espacial argentina: estudiar el universo requiere comprender tanto los objetos astronómicos como los procesos físicos que ocurren en el espacio.',
            'Las líneas de investigación asociadas al IAFE abarcan problemas muy diversos: Sol, estrellas, medio interestelar, sistemas planetarios, galaxias, cosmología y plasmas. Esa amplitud muestra una característica central de la astrofísica: la misma teoría física puede ayudar a describir fenómenos que ocurren a escalas enormemente diferentes.',
            'El estudio de plasmas es especialmente ilustrativo. Un plasma no es simplemente un gas muy caliente; sus partículas cargadas interactúan con campos eléctricos y magnéticos y pueden producir comportamientos colectivos complejos. El Sol, el viento solar, ciertas regiones de estrellas y muchos entornos astrofísicos exigen pensar en términos de plasma.',
            'La existencia de instituciones como el IAFE también creó un contexto para formar investigadoras e investigadores que luego trabajarían con computación científica, simulaciones y análisis de observaciones. De nuevo aparece el puente con el software: muchas preguntas actuales de la astrofísica se responden con programas que modelan sistemas imposibles de recrear en un laboratorio terrestre.'
        ],
        'sources': [
            {'label': 'IAFE · Historia', 'url': 'https://www.iafe.uba.ar/institucional/historia/'},
            {'label': 'IAFE · Sitio institucional', 'url': 'https://www.iafe.uba.ar/'}
        ],
        'tags': ['IAFE', 'física espacial', 'plasma', 'cosmología']
    },
    {
        'year': '1991–1996',
        'title': 'CONAE y la construcción de una política espacial nacional',
        'lead': 'La creación de CONAE abrió una etapa en la que Argentina empezó a pensar el espacio también como sistema de observación y desarrollo tecnológico.',
        'image': 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'La Comisión Nacional de Actividades Espaciales, CONAE, fue creada en 1991. A comienzos de la década de 1990 comenzó a consolidarse una planificación espacial que incluía misiones satelitales y cooperación internacional. El Plan Espacial de 1994 estableció líneas de trabajo orientadas a utilizar tecnología espacial para producir información útil sobre la Tierra.',
            'La observación de la Tierra marcó una diferencia respecto de la astronomía tradicional. En este caso, el objetivo no era estudiar objetos muy lejanos sino usar sensores desde órbita para observar océanos, continentes, atmósfera, agricultura, emergencias y ambiente. Sin embargo, el corazón técnico era familiar: instrumentación, calibración, comunicaciones y procesamiento de imágenes.',
            'La cooperación con NASA y otras instituciones internacionales permitió que el país participara en proyectos de alcance global mientras desarrollaba capacidades propias. Una misión espacial exige una cadena larga de conocimientos: diseño del satélite, energía, control de actitud, comunicaciones, operación en tierra, tratamiento de datos y productos científicos.',
            'Esta etapa es especialmente interesante para quienes estudian software porque un satélite puede verse como un sistema distribuido extremo. Hay computación embarcada, enlaces de comunicación, sistemas en tierra y grandes procesos de datos. El software no es un accesorio: forma parte de la infraestructura de la misión.'
        ],
        'sources': [
            {'label': 'Argentina.gob.ar · Historia de CONAE', 'url': 'https://www.argentina.gob.ar/ciencia/conae'},
            {'label': 'Argentina.gob.ar · Decreto 995/1991', 'url': 'https://www.argentina.gob.ar/normativa/nacional/decreto-995-1991-51213'}
        ],
        'tags': ['CONAE', 'política espacial', 'satélites', 'observación de la Tierra']
    },
    {
        'year': '1996–2000',
        'title': 'SAC-B y SAC-C: aprender a hacer ciencia desde órbita',
        'lead': 'Los primeros satélites científicos argentinos de la era CONAE demostraron que la misión no termina con el lanzamiento.',
        'image': 'https://images.unsplash.com/photo-1517976547714-720226b864c1?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'El programa espacial argentino empezó a generar misiones concretas durante la década de 1990. SAC-B fue lanzado en 1996 y estuvo orientado a observar fenómenos energéticos del universo, mientras que SAC-C, lanzado en 2000, consolidó una nueva etapa de observación de la Tierra con instrumentos científicos de distintos socios internacionales.',
            'El valor de estos proyectos no puede reducirse a la imagen del cohete despegando. Una misión científica es una secuencia de decisiones: qué medir, con qué sensor, con qué resolución, cómo transmitir los datos, cómo calibrarlos y cómo convertirlos en información útil. Muchas veces el trabajo más importante empieza cuando el satélite ya está en órbita.',
            'La experiencia adquirida fue también un aprendizaje institucional. Cada misión obliga a documentar interfaces, validar componentes, planificar contingencias y coordinar equipos. En términos de ingeniería de software, esto se parece mucho a desarrollar sistemas críticos: los errores tienen consecuencias y la trazabilidad importa.',
            'Para quienes miran la astronomía desde la programación, los satélites muestran una idea fascinante: el universo no solo se observa a través de telescopios; también se convierte en conjuntos de datos que pueden procesarse, visualizarse y combinarse con modelos físicos en computadoras terrestres.'
        ],
        'sources': [
            {'label': 'Argentina.gob.ar · Misiones cumplidas de CONAE', 'url': 'https://www.argentina.gob.ar/ciencia/conae/misiones-espaciales/misiones-cumplidas'},
            {'label': 'Argentina.gob.ar · CONAE', 'url': 'https://www.argentina.gob.ar/ciencia/conae'}
        ],
        'tags': ['SAC-B', 'SAC-C', 'misiones', 'datos']
    },
    {
        'year': '2011',
        'title': 'SAC-D/Aquarius: cuando la ciencia argentina mira el planeta completo',
        'lead': 'Una misión internacional convirtió la observación espacial en una herramienta para estudiar océanos y clima.',
        'image': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'SAC-D/Aquarius fue lanzado el 10 de junio de 2011 y tuvo entre sus objetivos medir la salinidad de la superficie oceánica. La misión fue desarrollada con participación argentina y cooperación internacional, incluyendo a NASA y el Jet Propulsion Laboratory. La elección del océano como objeto de estudio recuerda que el espacio también puede utilizarse para investigar fenómenos muy cercanos a nuestra vida cotidiana.',
            'La salinidad ayuda a comprender procesos que afectan la circulación oceánica y el clima. Un sensor orbital puede reunir mediciones a escala planetaria que serían difíciles de obtener de manera homogénea solo desde barcos o estaciones. La observación espacial suma, entonces, cobertura y continuidad.',
            'Misiones como SAC-D también muestran que la frontera entre astronomía y ciencias de la Tierra es porosa. Los principios físicos siguen siendo los mismos: radiación, sensores, calibración, ruido, resolución espacial y análisis de datos. Cambia el objeto de estudio, no la necesidad de medir bien.',
            'Desde el punto de vista tecnológico, el proyecto es un ejemplo de colaboración compleja. Diferentes instituciones aportan instrumentos y conocimiento, pero el conjunto debe funcionar como un sistema único. Esa lógica es idéntica a la de muchos sistemas de software y hardware modernos: múltiples componentes, una misión común y una necesidad permanente de integración.'
        ],
        'sources': [
            {'label': 'Argentina.gob.ar · SAC-D/Aquarius', 'url': 'https://www.argentina.gob.ar/ciencia/conae/misiones-espaciales/sac-d'},
            {'label': 'NASA · Aquarius', 'url': 'https://www.nasa.gov/mission_pages/aquarius/main/index.html'}
        ],
        'tags': ['SAC-D', 'Aquarius', 'océanos', 'clima']
    },
    {
        'year': '2018–2020',
        'title': 'SAOCOM: radar, software y observación de la Tierra',
        'lead': 'Una constelación de satélites que une física electromagnética, antenas, ingeniería y procesamiento de imágenes.',
        'image': 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'SAOCOM 1A fue lanzado en 2018 y forma parte de una constelación de satélites de observación de la Tierra con radar de apertura sintética. El proyecto involucró a múltiples instituciones argentinas, entre ellas CONAE, CNEA, VENG, INVAP y otras organizaciones del sistema científico y tecnológico, además de cooperación internacional.',
            'El radar de apertura sintética permite observar la superficie terrestre utilizando microondas. A diferencia de una cámara óptica, el radar no depende de la iluminación solar para formar una imagen. Eso permite observar de día y de noche y estudiar regiones con condiciones que pueden dificultar la observación óptica.',
            'La parte más fascinante para una persona interesada en programación aparece después de la medición. Los datos deben procesarse para corregir geometría, reducir ruido, reconstruir información y generar productos interpretables. En ese camino aparecen transformadas, filtros, modelos físicos y enormes cantidades de operaciones numéricas.',
            'SAOCOM muestra con claridad por qué el espacio necesita perfiles híbridos. Física, electrónica, telecomunicaciones, control, software y ciencia de datos no compiten: se necesitan mutuamente para que una misión produzca información útil.'
        ],
        'sources': [
            {'label': 'Argentina.gob.ar · SAOCOM 1A', 'url': 'https://www.argentina.gob.ar/ciencia/conae/noche-espacial/satelite-saocom-1a'},
            {'label': 'Argentina.gob.ar · CONAE', 'url': 'https://www.argentina.gob.ar/ciencia/conae'}
        ],
        'tags': ['SAOCOM', 'radar', 'INVAP', 'procesamiento de imágenes']
    },
    {
        'year': '1998–actualidad',
        'title': 'Del calculista al algoritmo: la computación cambia la astronomía',
        'lead': 'La informática no reemplazó la observación: amplió la escala de lo que una persona puede medir, comparar y simular.',
        'image': 'https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'Durante décadas, gran parte del trabajo astronómico dependió de cálculos manuales, clasificación de placas fotográficas y series de medición mantenidas cuidadosamente. La incorporación de computadoras transformó esas tareas. Pero la idea básica no cambió: una observación tiene que convertirse en una representación que pueda analizarse, compararse y revisarse.',
            'Una imagen astronómica digital puede atravesar múltiples etapas antes de producir un resultado. Se puede calibrar, corregir por ruido, alinear, combinar, medir fuentes, detectar estructuras, estimar incertidumbres y clasificar objetos. Cada paso es un pequeño problema de computación científica.',
            'La astrofotografía de aficionados comparte parte de esta lógica. Apilar exposiciones, corregir gradientes, ajustar color o separar señal de ruido son procesos que transforman observaciones en información visual. La diferencia con el trabajo profesional está en la escala, los objetivos y el rigor instrumental, no en la idea fundamental de que un dato debe ser procesado con cuidado.',
            'Por eso programación y astronomía forman una combinación natural. Bases de datos, procesamiento de imágenes, visualización, simulación, aprendizaje automático y APIs pueden convertirse en instrumentos científicos. Aprender a programar no aleja del cielo: abre otra puerta para estudiarlo.'
        ],
        'sources': [
            {'label': 'FCAGLP · Historia del Observatorio de La Plata', 'url': 'https://www.fcaglp.unlp.edu.ar/uploads/docs/perdomo__historia_obsevatorio.pdf'},
            {'label': 'IAFE · Historia', 'url': 'https://www.iafe.uba.ar/institucional/historia/'}
        ],
        'tags': ['computación', 'datos', 'imágenes', 'software científico']
    },
    {
        'year': '2020–actualidad',
        'title': 'Astronomía de datos y una nueva forma de participar',
        'lead': 'Hoy la frontera entre observador, programador y divulgador puede ser mucho más permeable.',
        'image': 'https://images.unsplash.com/photo-1515705576963-95cad62945b6?auto=format&fit=crop&w=1600&q=90',
        'body': [
            'La astronomía contemporánea produce una cantidad de datos que sería imposible explorar manualmente. Los grandes relevamientos digitalizan enormes zonas del cielo y permiten volver sobre las mismas regiones para buscar cambios. La ciencia se convierte así en una combinación de observación, almacenamiento, clasificación y análisis.',
            'Esta transformación también cambia el papel de las personas fuera de los grandes observatorios. Una aficionada puede construir una estación de observación, registrar variables, automatizar una cámara, contribuir a una base de datos o desarrollar una herramienta educativa. El acceso a software libre, catálogos públicos y APIs reduce la distancia entre curiosidad y experimentación.',
            'La astrofotografía es un excelente punto de entrada porque obliga a pensar en el instrumento, el cielo, la adquisición y el procesamiento al mismo tiempo. Aprender a hacer una buena imagen puede llevar a investigar óptica, sensores, seguimiento, estadística, teoría del color y algoritmos.',
            'En ese contexto, una comunidad como ADV-Lab puede funcionar como un pequeño laboratorio abierto. Compartir una foto, una ubicación, un consejo o una técnica no sustituye la ciencia profesional, pero sí construye cultura científica y ayuda a que más personas aprendan a observar con criterio.'
        ],
        'sources': [
            {'label': 'NASA · Citizen Science', 'url': 'https://science.nasa.gov/citizen-science/'},
            {'label': 'NASA · Computing', 'url': 'https://www.nasa.gov/technology/computing/'}
        ],
        'tags': ['datos', 'ciencia ciudadana', 'astrofotografía', 'automatización']
    },
    {
        'year': 'Hoy',
        'title': 'Una historia que sigue abierta',
        'lead': 'La historia argentina del espacio no terminó en un observatorio ni en un satélite: sigue creciendo con nuevas preguntas.',
        'image': 'https://science.nasa.gov/wp-content/uploads/2023/04/orion-nebula-xlarge_web-jpg.webp',
        'body': [
            'Mirar en conjunto la historia argentina de la astronomía, la física y el espacio permite reconocer una continuidad. Primero fue necesario construir instituciones que supieran medir. Después hubo que formar personas, desarrollar instrumentos, crear laboratorios, aprender a trabajar con radioseñales y finalmente colocar sensores en órbita. Cada etapa amplió lo que la siguiente podía intentar.',
            'La parte interesante es que ninguna etapa vuelve inútil a la anterior. Los observatorios siguen siendo importantes. La física sigue siendo el lenguaje con el que interpretamos las señales. Los satélites agregan perspectiva. La computación permite integrar todo eso y encontrar patrones que serían imposibles de reconocer a simple vista.',
            'Para alguien que empieza desde la programación, esta historia ofrece un camino concreto: una aplicación puede terminar procesando una imagen, una simulación puede ayudar a enseñar dinámica orbital, una API puede acercar datos científicos al público y una herramienta de visualización puede convertir una tabla en una experiencia de aprendizaje.',
            'Y para quien empieza desde la astronomía ocurre lo contrario: aprender código puede convertirse en una forma de construir sus propios instrumentos digitales. El cielo sigue siendo el mismo desafío de siempre —entender algo inmenso a partir de señales pequeñas—, pero hoy tenemos muchas más herramientas para intentarlo.'
        ],
        'sources': [
            {'label': 'CONAE · Sitio oficial', 'url': 'https://www.argentina.gob.ar/ciencia/conae'},
            {'label': 'OAC · Historia', 'url': 'https://oac.unc.edu.ar/institucional/historia/'},
            {'label': 'IAFE · Historia', 'url': 'https://www.iafe.uba.ar/institucional/historia/'}
        ],
        'tags': ['presente', 'Argentina', 'espacio', 'futuro']
    }
]

CACHE = {'apod': None, 'apod_at': datetime.min, 'news': None, 'news_at': datetime.min}
RATE = {}
RATE_WINDOW = 60
RATE_LIMITS = {'notes': 8, 'contributions': 5, 'likes': 20, 'contacts': 8}


def local_now():
    return datetime.now(APP_TIMEZONE)


def admin_guard(x_admin_token: str = Header(default='')):
    if not hmac.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail='Token de administrador inválido')


def client_ip(request: Request):
    try:
        return str(ipaddress.ip_address(request.client.host if request.client else '0.0.0.0'))
    except ValueError:
        return '0.0.0.0'


def rate_limit(request: Request, action: str):
    now = time.monotonic()
    key = f'{action}:{client_ip(request)}'
    hits = RATE.setdefault(key, [])
    hits[:] = [stamp for stamp in hits if now - stamp < RATE_WINDOW]
    if len(hits) >= RATE_LIMITS[action]:
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes. Esperá un momento y volvé a intentar.')
    hits.append(now)


@app.middleware('http')
async def security_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.nasa.gov https://www.nasa.gov https://cneos.jpl.nasa.gov; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    if request.url.scheme == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    if request.url.path == '/admin' or request.url.path.startswith('/api/admin'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def clean_text(value):
    return ' '.join((value or '').replace('\n', ' ').replace('\r', ' ').split())


def valid_email(value):
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value or ''))


def normalize_http_url(value, fallback=''):
    value = (value or '').strip()
    if not value:
        return fallback
    try:
        parsed = urlparse(value)
        if parsed.scheme in {'https', 'http'} and parsed.netloc:
            return value[:500]
    except Exception:
        pass
    return fallback


def safe_basename(filename):
    return Path(filename or '').name.replace('..', '_')


def valid_image_bytes(data: bytes, suffix: str):
    if suffix in {'.jpg', '.jpeg'}:
        return data.startswith(b'\xff\xd8\xff')
    if suffix == '.png':
        return data.startswith(b'\x89PNG\r\n\x1a\n')
    if suffix == '.webp':
        return data[:4] == b'RIFF' and data[8:12] == b'WEBP'
    return False


def save_uploaded_image(file: UploadFile, max_mb: int):
    suffix = Path(safe_basename(file.filename)).suffix.lower()
    allowed = {'.jpg', '.jpeg', '.png', '.webp'}
    if suffix not in allowed:
        raise HTTPException(400, 'Formato no permitido. Usá JPG, PNG o WEBP.')
    content_type = (file.content_type or '').lower()
    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    if content_type not in allowed_types:
        raise HTTPException(400, 'Tipo de imagen no permitido.')
    data = file.file.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(400, f'La imagen supera {max_mb} MB')
    if not valid_image_bytes(data, suffix):
        raise HTTPException(400, 'El archivo no parece ser una imagen válida.')
    name = f'{uuid.uuid4().hex}{suffix}'
    (UPLOAD_DIR / name).write_bytes(data)
    return f'/static/uploads/{name}'


def serialize_photo(p: Photo):
    return {
        'id': p.id, 'title': p.title, 'description': p.description or '', 'image': p.image,
        'telescope': p.telescope or '', 'camera': p.camera or '', 'mount': p.mount or '',
        'exposure': p.exposure or '', 'iso': p.iso or '', 'status': p.status.value,
        'created_at': p.created_at.isoformat(), 'photographer': p.contributor_name or 'Comunidad',
        'email': p.contributor_email or '', 'instagram': p.instagram or '', 'location': p.location or '',
        'category': p.community_category or 'Otros', 'likes': p.likes or 0,
    }


def serialize_product(p: Product):
    return {
        'id': p.id, 'name': p.name, 'description': p.description or '', 'price': p.price,
        'image': p.image or '', 'stock': p.stock, 'active': p.active, 'contact_url': p.contact_url or INSTAGRAM_DM,
        'category': p.category.name if p.category else 'Otros', 'category_id': p.category_id,
        'created_at': p.created_at.isoformat(),
    }


def serialize_note(n: CommunityNote):
    return {'id': n.id, 'username': n.username, 'body': n.body, 'likes': n.likes or 0, 'created_at': n.created_at.isoformat()}


def serialize_article(a: Article):
    return {'id': a.id, 'title': a.title, 'slug': a.slug, 'content': a.content, 'author': a.author, 'cover': a.cover, 'published': a.published, 'created_at': a.created_at.isoformat()}


def seed_data():
    db = SessionLocal()
    try:
        product_categories = [('Láminas', '◌'), ('Papelería', '▧'), ('Decoración', '✧'), ('Accesorios', '◉'), ('Regalos', '✦'), ('Otros', '○')]
        existing_categories = {c.name for c in db.query(Category).all()}
        for name, icon in product_categories:
            if name not in existing_categories:
                db.add(Category(name=name, icon=icon))
        db.commit()
        if not db.query(Article).count():
            db.add_all([
                Article(title='Cómo preparar una noche de astrofotografía', slug='preparar-noche-astrofotografia', content='Una sesión de astrofotografía mejora cuando se planifica con calma: batería, memoria, enfoque, alineación, encuadre, exposición y una pequeña bitácora. Registrar lo que funcionó permite repetir resultados y aprender de cada noche.', author='ADV-Lab', cover='https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=1600&q=90'),
                Article(title='Qué observar y registrar en una primera sesión', slug='primera-sesion-de-observacion', content='No hace falta comenzar con el equipo perfecto. La práctica consiste en mirar el cielo, aprender a orientarse, registrar condiciones y construir un método personal de observación.', author='ADV-Lab', cover='https://images.unsplash.com/photo-1444703686981-a3abb4c4d4fe3?auto=format&fit=crop&w=1600&q=90')
            ])
            db.commit()
        if not db.query(Product).count():
            lam = db.query(Category).filter(Category.name == 'Láminas').first()
            pap = db.query(Category).filter(Category.name == 'Papelería').first()
            db.add_all([
                Product(name='Lámina Fases de la Luna', description='Diseño astronómico para pared o escritorio.', price=8500, stock=10, image='https://images.unsplash.com/photo-1534791547706-2d6b4b5b5b0a?auto=format&fit=crop&w=1200&q=90', contact_url=INSTAGRAM_DM, category_id=lam.id),
                Product(name='Mapa Estelar', description='Lámina decorativa inspirada en el cielo nocturno.', price=12000, stock=6, image='https://images.unsplash.com/photo-1444703686981-a3abb4c4d4fe3?auto=format&fit=crop&w=1200&q=90', contact_url=INSTAGRAM_DM, category_id=lam.id),
                Product(name='Bitácora Astronómica', description='Cuaderno para registrar observaciones y sesiones.', price=9800, stock=12, image='https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=1200&q=90', contact_url=INSTAGRAM_DM, category_id=pap.id)
            ])
            db.commit()
        if not db.query(AstronomicalEvent).count():
            now = datetime.utcnow()
            db.add_all([
                AstronomicalEvent(title='Noche de observación', description='Prepará una sesión y compartí tus resultados en Comunidad.', event_date=now + timedelta(days=4)),
                AstronomicalEvent(title='Noche de comunidad', description='Leé consejos, descubrí imágenes nuevas y dejá una nota.', event_date=now + timedelta(days=11)),
                AstronomicalEvent(title='Ventana de astrofotografía', description='Usá el calendario astronómico para planificar tu próxima captura.', event_date=now + timedelta(days=20)),
            ])
            db.commit()
    finally:
        db.close()


def migrate_database():
    inspector = inspect(engine)
    with engine.begin() as conn:
        if 'photos' in inspector.get_table_names():
            existing = {col['name'] for col in inspector.get_columns('photos')}
            additions = {
                'contributor_name': "ALTER TABLE photos ADD COLUMN contributor_name VARCHAR(100) DEFAULT ''",
                'contributor_email': "ALTER TABLE photos ADD COLUMN contributor_email VARCHAR(180) DEFAULT ''",
                'instagram': "ALTER TABLE photos ADD COLUMN instagram VARCHAR(120) DEFAULT ''",
                'location': "ALTER TABLE photos ADD COLUMN location VARCHAR(180) DEFAULT ''",
                'community_category': "ALTER TABLE photos ADD COLUMN community_category VARCHAR(100) DEFAULT ''",
                'likes': "ALTER TABLE photos ADD COLUMN likes INTEGER DEFAULT 0",
            }
            for column, statement in additions.items():
                if column not in existing:
                    conn.execute(text(statement))
    Base.metadata.create_all(bind=engine)


migrate_database()
seed_data()


@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='index.html', context={})


@app.get('/admin', response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name='admin.html', context={})


@app.get('/article/{slug}', response_class=HTMLResponse)
def article_page(request: Request, slug: str):
    return templates.TemplateResponse(request=request, name='article.html', context={'slug': slug})


@app.get('/profile', response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse(request=request, name='profile.html', context={})


@app.get('/edit', response_class=HTMLResponse)
def edit_page(request: Request):
    return templates.TemplateResponse(request=request, name='edit.html', context={})


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'ADV-Lab', 'version': '6.0.0'}


@app.get('/api/community/categories')
def community_categories():
    return COMMUNITY_CATEGORIES


@app.get('/api/categories')
def categories(db: Session = Depends(get_db)):
    return [{'id': c.id, 'name': c.name, 'icon': c.icon} for c in db.query(Category).order_by(Category.name).all()]


@app.get('/api/daily')
def daily():
    now = local_now()
    index = now.timetuple().tm_yday - 1
    word, definition = DAILY_WORDS[index % len(DAILY_WORDS)]
    return {'date': now.date().isoformat(), 'word': word, 'definition': definition, 'apod': fetch_apod()}


@app.get('/api/planets')
def planets():
    return PLANETS


@app.get('/api/calendar')
def calendar(year: int | None = None, month: int | None = None):
    now = local_now()
    year = year or now.year
    month = month or now.month
    if month < 1 or month > 12:
        raise HTTPException(400, 'Mes inválido')
    events = []
    for date_str, label, time_label, phase in MOON_PHASES_2026:
        dt = datetime.fromisoformat(date_str)
        if dt.year == year and dt.month == month:
            events.append({'date': date_str, 'title': label, 'description': f'Fase principal de la Luna. Horario de referencia: {time_label}.', 'type': 'moon_phase', 'phase': phase, 'time': time_label, 'source': 'USNO'})
    for date_str, title, description, kind in ANNUAL_EVENTS_2026:
        dt = datetime.fromisoformat(date_str)
        if dt.year == year and dt.month == month:
            events.append({'date': date_str, 'title': title, 'description': description, 'type': kind, 'phase': '', 'time': '', 'source': 'NASA'})
    if year != 2026:
        events.append({'date': f'{year}-{month:02d}-01', 'title': 'Agenda editorial', 'description': 'La edición detallada del calendario está curada para 2026. Las fases y eventos futuros requieren actualización astronómica anual.', 'type': 'info', 'phase': '', 'time': '', 'source': 'ADV-Lab'})
    events.sort(key=lambda item: item['date'])
    return {'year': year, 'month': month, 'month_name': datetime(year, month, 1).strftime('%B'), 'events': events, 'now': now.isoformat(), 'timezone': 'America/Argentina/Buenos_Aires'}


@app.get('/api/calendar/upcoming')
def upcoming_calendar(limit: int = 6):
    today = local_now().date().isoformat()
    items = []
    if local_now().year == 2026:
        for date_str, title, description, kind in ANNUAL_EVENTS_2026:
            if date_str >= today:
                items.append({'date': date_str, 'title': title, 'description': description, 'type': kind, 'source': 'NASA'})
        for date_str, label, time_label, phase in MOON_PHASES_2026:
            if date_str >= today:
                items.append({'date': date_str, 'title': label, 'description': f'Fase lunar principal · {time_label}.', 'type': 'moon_phase', 'source': 'USNO'})
    items.sort(key=lambda item: item['date'])
    return items[:max(1, min(limit, 20))]


@app.get('/api/contributions')
def contributions(request: Request, offset: int = 0, limit: int = 24, search: str = '', category: str = '', db: Session = Depends(get_db)):
    limit = max(1, min(limit, 48))
    offset = max(0, offset)
    query = db.query(Photo).filter(Photo.status == PhotoStatus.aprobada)
    if category and category in COMMUNITY_CATEGORIES:
        query = query.filter(Photo.community_category == category)
    if search.strip():
        term = f'%{search.strip()[:80]}%'
        query = query.filter((Photo.title.ilike(term)) | (Photo.location.ilike(term)) | (Photo.contributor_name.ilike(term)))
    total = query.count()
    items = query.order_by(desc(Photo.created_at)).offset(offset).limit(limit).all()
    return {'items': [serialize_photo(p) for p in items], 'total': total, 'offset': offset, 'limit': limit, 'has_more': offset + len(items) < total}


@app.post('/api/contributions')
async def create_contribution(request: Request, title: str = Form(...), image: UploadFile = File(...), description: str = Form(default=''), location: str = Form(default=''), instagram: str = Form(default=''), category: str = Form(default=''), contributor_name: str = Form(default=''), contributor_email: str = Form(default=''), telescope: str = Form(default=''), camera: str = Form(default=''), mount: str = Form(default=''), exposure: str = Form(default=''), iso: str = Form(default=''), website: str = Form(default=''), db: Session = Depends(get_db)):
    rate_limit(request, 'contributions')
    if website.strip():
        raise HTTPException(400, 'No se pudo validar el envío.')
    title = clean_text(title)[:180]
    if len(title) < 2:
        raise HTTPException(400, 'El título es obligatorio')
    if contributor_email and not valid_email(contributor_email):
        raise HTTPException(400, 'Correo electrónico inválido')
    image_url = save_uploaded_image(image, 10)
    photo = Photo(title=title, description=clean_text(description)[:500], image=image_url, location=clean_text(location)[:180], instagram=clean_text(instagram)[:120], community_category=category.strip() if category in COMMUNITY_CATEGORIES else '', contributor_name=clean_text(contributor_name)[:100], contributor_email=contributor_email.lower().strip()[:180], telescope=clean_text(telescope)[:180], camera=clean_text(camera)[:180], mount=clean_text(mount)[:180], exposure=clean_text(exposure)[:80], iso=clean_text(iso)[:50], status=PhotoStatus.pendiente, likes=0)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {'ok': True, 'photo': serialize_photo(photo)}


@app.post('/api/contributions/{photo_id}/like')
def like_photo(request: Request, photo_id: int, payload: PhotoLikeCreate, db: Session = Depends(get_db)):
    rate_limit(request, 'likes')
    photo = db.get(Photo, photo_id)
    if not photo or photo.status != PhotoStatus.aprobada:
        raise HTTPException(404, 'Imagen no encontrada')
    if not valid_email(payload.email):
        raise HTTPException(400, 'Correo electrónico inválido')
    email = payload.email.lower().strip()
    exists = db.query(PhotoLike).filter(PhotoLike.photo_id == photo_id, PhotoLike.email == email).first()
    if exists:
        return {'ok': True, 'likes': photo.likes or 0, 'already_liked': True}
    db.add(PhotoLike(photo_id=photo_id, username=clean_text(payload.username)[:100], email=email))
    photo.likes = (photo.likes or 0) + 1
    db.commit()
    return {'ok': True, 'likes': photo.likes, 'already_liked': False}


@app.get('/api/community/notes')
def notes(offset: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 40))
    offset = max(0, offset)
    base = db.query(CommunityNote).filter(CommunityNote.approved == True).order_by(desc(CommunityNote.created_at))
    total = base.count()
    items = base.offset(offset).limit(limit).all()
    return {'items': [serialize_note(n) for n in items], 'total': total, 'offset': offset, 'limit': limit, 'has_more': offset + len(items) < total}


@app.post('/api/community/notes')
def create_note(request: Request, payload: NoteCreate, db: Session = Depends(get_db)):
    rate_limit(request, 'notes')
    if not valid_email(payload.email):
        raise HTTPException(400, 'Correo electrónico inválido')
    if not payload.username.strip() or not payload.body.strip():
        raise HTTPException(400, 'Completá usuario y nota')
    note = CommunityNote(username=clean_text(payload.username)[:100], email=payload.email.lower().strip()[:180], body=clean_text(payload.body)[:900], approved=True)
    db.add(note)
    db.commit()
    db.refresh(note)
    return serialize_note(note)


@app.post('/api/community/notes/{note_id}/like')
def like_note(request: Request, note_id: int, payload: NoteLikeCreate, db: Session = Depends(get_db)):
    rate_limit(request, 'likes')
    if not valid_email(payload.email):
        raise HTTPException(400, 'Correo electrónico inválido')
    note = db.get(CommunityNote, note_id)
    if not note or not note.approved:
        raise HTTPException(404, 'Nota no encontrada')
    email = payload.email.lower().strip()
    if db.query(NoteLike).filter(NoteLike.note_id == note_id, NoteLike.email == email).first():
        return {'ok': True, 'likes': note.likes or 0, 'already_liked': True}
    db.add(NoteLike(note_id=note_id, username=clean_text(payload.username)[:100], email=email))
    note.likes = (note.likes or 0) + 1
    db.commit()
    return {'ok': True, 'likes': note.likes, 'already_liked': False}


@app.get('/api/admin/pending', dependencies=[Depends(admin_guard)])
def pending(db: Session = Depends(get_db)):
    return [serialize_photo(p) for p in db.query(Photo).filter(Photo.status == PhotoStatus.pendiente).order_by(desc(Photo.created_at)).all()]


@app.get('/api/admin/stats', dependencies=[Depends(admin_guard)])
def admin_stats(db: Session = Depends(get_db)):
    return {
        'pending': db.query(Photo).filter(Photo.status == PhotoStatus.pendiente).count(),
        'photos': db.query(Photo).count(),
        'products': db.query(Product).count(),
        'active_products': db.query(Product).filter(Product.active == True).count(),
        'requests': db.query(ContactRequest).count(),
        'notes': db.query(CommunityNote).count(),
    }


@app.post('/api/admin/approve/{photo_id}', dependencies=[Depends(admin_guard)])
def approve(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, 'Aporte no encontrado')
    photo.status = PhotoStatus.aprobada
    db.commit()
    return {'ok': True}


@app.delete('/api/admin/reject/{photo_id}', dependencies=[Depends(admin_guard)])
def reject(photo_id: int, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(404, 'Aporte no encontrado')
    photo.status = PhotoStatus.rechazada
    db.commit()
    return {'ok': True}


@app.get('/api/products')
def products(db: Session = Depends(get_db)):
    return [serialize_product(p) for p in db.query(Product).filter(Product.active == True).order_by(desc(Product.created_at)).all()]


@app.get('/api/products/{product_id}')
def product_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or not product.active:
        raise HTTPException(404, 'Producto no encontrado')
    return serialize_product(product)


@app.post('/api/shop/contact')
def shop_contact(request: Request, payload: ContactRequestCreate, db: Session = Depends(get_db)):
    rate_limit(request, 'contacts')
    if not valid_email(payload.email):
        raise HTTPException(400, 'Correo electrónico inválido')
    item = ContactRequest(product_id=payload.product_id, product_name=clean_text(payload.product_name)[:180], full_name=clean_text(payload.full_name)[:140], whatsapp=clean_text(payload.whatsapp)[:60], email=payload.email.lower().strip()[:180], message=clean_text(payload.message)[:1200])
    db.add(item)
    db.commit()
    return {'ok': True, 'message': 'Consulta recibida'}


@app.post('/api/admin/products', dependencies=[Depends(admin_guard)])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    payload_data = payload.model_dump()
    payload_data['contact_url'] = normalize_http_url(payload_data.get('contact_url'), INSTAGRAM_DM)
    payload_data['image'] = normalize_http_url(payload_data.get('image'), '')
    product = Product(**payload_data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@app.put('/api/admin/products/{product_id}', dependencies=[Depends(admin_guard)])
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, 'Producto no encontrado')
    data = payload.model_dump()
    data['contact_url'] = normalize_http_url(data.get('contact_url'), INSTAGRAM_DM)
    data['image'] = normalize_http_url(data.get('image'), '')
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@app.delete('/api/admin/products/{product_id}', dependencies=[Depends(admin_guard)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, 'Producto no encontrado')
    product.active = False
    db.commit()
    return {'ok': True}


@app.post('/api/admin/products/{product_id}/restore', dependencies=[Depends(admin_guard)])
def restore_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, 'Producto no encontrado')
    product.active = True
    db.commit()
    return {'ok': True}


@app.get('/api/admin/products', dependencies=[Depends(admin_guard)])
def admin_products(db: Session = Depends(get_db)):
    return [serialize_product(p) for p in db.query(Product).order_by(desc(Product.created_at)).all()]


@app.get('/api/admin/contact-requests', dependencies=[Depends(admin_guard)])
def admin_contact_requests(db: Session = Depends(get_db)):
    return [{'id': r.id, 'product_id': r.product_id, 'product_name': r.product_name, 'full_name': r.full_name, 'whatsapp': r.whatsapp, 'email': r.email, 'message': r.message, 'status': r.status, 'created_at': r.created_at.isoformat()} for r in db.query(ContactRequest).order_by(desc(ContactRequest.created_at)).all()]


@app.post('/api/admin/contact-requests/{request_id}/status', dependencies=[Depends(admin_guard)])
def admin_contact_status(request_id: int, status: str, db: Session = Depends(get_db)):
    item = db.get(ContactRequest, request_id)
    if not item:
        raise HTTPException(404, 'Consulta no encontrada')
    item.status = clean_text(status)[:40]
    db.commit()
    return {'ok': True}


@app.get('/api/articles')
def articles(db: Session = Depends(get_db)):
    return [serialize_article(a) for a in db.query(Article).filter(Article.published == True).order_by(desc(Article.created_at)).all()]


@app.get('/api/articles/{slug}')
def article_detail(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug, Article.published == True).first()
    if not article:
        raise HTTPException(404, 'Artículo no encontrado')
    return serialize_article(article)


@app.post('/api/admin/articles', dependencies=[Depends(admin_guard)])
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    article = Article(title=clean_text(payload.title)[:220], slug=clean_text(payload.slug).lower().replace(' ', '-')[:240], content=payload.content[:20000], author=clean_text(payload.author)[:140], cover=normalize_http_url(payload.cover, ''), published=payload.published)
    db.add(article)
    db.commit()
    db.refresh(article)
    return serialize_article(article)


@app.get('/api/events')
def events(db: Session = Depends(get_db)):
    return [{'id': e.id, 'title': e.title, 'description': e.description, 'event_date': e.event_date.isoformat()} for e in db.query(AstronomicalEvent).order_by(AstronomicalEvent.event_date).all()]


@app.post('/api/admin/events', dependencies=[Depends(admin_guard)])
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    item = AstronomicalEvent(title=clean_text(payload.title)[:180], description=clean_text(payload.description)[:1000], event_date=payload.event_date)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {'id': item.id}


@app.get('/api/history')
def history():
    return HISTORY


@app.get('/api/news')
def news():
    now = datetime.utcnow()
    if CACHE['news'] and now - CACHE['news_at'] < timedelta(minutes=30):
        return CACHE['news']
    items = []
    for feed_url, source in [(NASA_NEWS_RSS, 'NASA'), (JPL_NEWS_RSS, 'JPL/CNEOS')]:
        try:
            items.extend(fetch_rss(feed_url, source))
        except Exception:
            pass
    if items:
        items = sorted(items, key=lambda x: x.get('published_sort', ''), reverse=True)[:16]
        for item in items:
            item.pop('published_sort', None)
        CACHE['news'] = items
        CACHE['news_at'] = now
        return items
    fallback = [
        {'title': 'NASA Science', 'summary': 'Historias y recursos sobre ciencia, misiones, astronomía y exploración.', 'url': 'https://science.nasa.gov/', 'source': 'NASA'},
        {'title': 'NASA News', 'summary': 'Noticias y comunicados oficiales de NASA.', 'url': 'https://www.nasa.gov/news/', 'source': 'NASA'},
        {'title': 'CNEOS News', 'summary': 'Actualizaciones del Jet Propulsion Laboratory sobre objetos cercanos a la Tierra.', 'url': 'https://cneos.jpl.nasa.gov/news/', 'source': 'JPL/CNEOS'}
    ]
    CACHE['news'] = fallback
    CACHE['news_at'] = now
    return fallback


@app.post('/api/admin/upload', dependencies=[Depends(admin_guard)])
async def upload_asset(file: UploadFile = File(...)):
    return {'url': save_uploaded_image(file, 10), 'name': safe_basename(file.filename)}


def fetch_apod():
    now = datetime.utcnow()
    if CACHE['apod'] and now - CACHE['apod_at'] < timedelta(minutes=30):
        return CACHE['apod']
    try:
        request = UrlRequest(NASA_APOD_URL, headers={'User-Agent': 'ADV-Lab/7.0'})
        with urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
        apod = {'title': data.get('title', 'Imagen astronómica del día'), 'explanation': data.get('explanation', ''), 'date': data.get('date', ''), 'url': data.get('hdurl') or data.get('url', ''), 'media_type': data.get('media_type', 'image'), 'copyright': data.get('copyright', ''), 'source': 'NASA APOD'}
        CACHE['apod'] = apod
        CACHE['apod_at'] = now
        return apod
    except Exception:
        return {'title': 'Una ventana al universo', 'explanation': 'La imagen diaria proviene de NASA APOD cuando la conexión externa está disponible.', 'date': local_now().date().isoformat(), 'url': FALLBACK_UNIVERSE, 'media_type': 'image', 'copyright': '', 'source': 'ADV-Lab'}


def fetch_rss(feed_url, source):
    request = UrlRequest(feed_url, headers={'User-Agent': 'ADV-Lab/7.0'})
    with urlopen(request, timeout=7) as response:
        xml = response.read()
    root = ET.fromstring(xml)
    result = []
    for item in root.findall('.//item')[:10]:
        title = clean_text(item.findtext('title', default=''))
        link = clean_text(item.findtext('link', default=''))
        description = clean_text(item.findtext('description', default=''))
        pub = clean_text(item.findtext('pubDate', default=''))
        try:
            published_dt = parsedate_to_datetime(pub).isoformat() if pub else ''
        except Exception:
            published_dt = pub
        if title and link:
            result.append({'title': title, 'summary': description[:320], 'url': link, 'source': source, 'published': pub, 'published_sort': published_dt})
    return result
