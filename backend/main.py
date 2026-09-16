from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from datetime import datetime
import hashlib
import random
import smtplib
from email.message import EmailMessage
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./scilog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    badge = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    doi = Column(String(100), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    author = relationship("User", back_populates="posts")

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# ESQUEMAS DE PYDANTIC
# ---------------------------------------------------------
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    badge: str | None = "Investigador"

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    badge: str | None
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class RecoverRequest(BaseModel):
    email: EmailStr

class PostCreate(BaseModel):
    title: str
    content: str
    category: str
    doi: str | None = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    doi: str | None
    created_at: datetime
    author: UserResponse
    class Config:
        from_attributes = True

# ---------------------------------------------------------
# INICIALIZACIÓN DE LA API
# ---------------------------------------------------------
app = FastAPI(title="SciLog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------------------------------
# RUTAS DE LA API
# ---------------------------------------------------------

@app.post("/users/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario o email ya está en uso.")
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        badge=user.badge
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/users/login", response_model=UserResponse)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter((User.username == user.username) | (User.email == user.username)).first()
    if not db_user or db_user.hashed_password != hash_password(user.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    return db_user

# =========================================================
# NUEVA RUTA PARA ENVIAR EMAILS DE RECUPERACIÓN REALES
# =========================================================
@app.post("/users/recover")
def recover_password(req: RecoverRequest, db: Session = Depends(get_db)):
    # 1. Buscar si el correo existe en la base de datos
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Correo no encontrado.")
    
    # 2. Generar nueva contraseña temporal (6 dígitos)
    new_pass = str(random.randint(100000, 999999))
    user.hashed_password = hash_password(new_pass)
    db.commit()

    # 3. Enviar el correo electrónico (Configuración SMTP)
    try:
        msg = EmailMessage()
        msg.set_content(f"Hola {user.full_name},\n\nAlguien solicitó recuperar tu cuenta en SciLog.\n\nTu nueva contraseña temporal es: {new_pass}\n\nPor favor, inicia sesión con esta clave y cámbiala lo antes posible.\n\nSaludos,\nEl equipo de SciLog.")
        msg['Subject'] = 'Recuperación de Contraseña - SciLog'
        
        # ⚠️ IMPORTANTE PARA PRODUCCIÓN ⚠️
        # Cambia esto por un correo de Gmail real y una "Contraseña de Aplicación"
        correo_origen = "TU_CORREO_DE_PRUEBA@gmail.com" 
        password_origen = "TU_CONTRASEÑA_DE_APLICACION" 
        
        msg['From'] = correo_origen
        msg['To'] = user.email

        # Conectar a los servidores de Google
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(correo_origen, password_origen)
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        # Si falla el envío de correo, avisamos al frontend
        print(f"Error enviando correo: {e}")
        raise HTTPException(status_code=500, detail="Error al intentar enviar el correo electrónico.")

    return {"message": "Correo enviado con éxito"}

@app.post("/posts/", response_model=PostResponse)
def create_post(post: PostCreate, author_id: int, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    new_post = Post(title=post.title, content=post.content, category=post.category, doi=post.doi, author_id=author_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/feed/", response_model=list[PostResponse])
def get_feed(skip: int = 0, limit: int = 20, category: str = None, db: Session = Depends(get_db)):
    query = db.query(Post)
    if category and category.lower() != "all":
        query = query.filter(Post.category == category)
    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor SciLog en http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)