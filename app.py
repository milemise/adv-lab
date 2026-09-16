import os
import uuid
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from PIL import Image

from database import Base, engine, get_db
from models import Photo, Photographer, Category
from config import *

try:
    from email_service import EmailService
except ImportError:
    EmailService = None

try:
    from ai_review import review_submission
except ImportError:
    review_submission = None

Base.metadata.create_all(bind=engine)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    if db.query(Category).count() == 0:
        categorias_completas = DEFAULT_CATEGORIES + ["Ilustraciones Digitales"]
        for cat in categorias_completas:
            if not db.query(Category).filter(Category.name == cat).first():
                db.add(Category(name=cat, icon=""))
        db.commit()
    yield

app = FastAPI(title="AstroLab API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
app.mount("/thumbs", StaticFiles(directory=THUMBNAIL_FOLDER), name="thumbs")

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"request": request}
    )

def get_illustration_category_id(db: Session):
    cat = db.query(Category).filter(Category.name == "Ilustraciones Digitales").first()
    if not cat:
        cat = Category(name="Ilustraciones Digitales", icon="")
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat.id

@app.get("/gallery")
def gallery(db: Session = Depends(get_db)):
    illus_id = get_illustration_category_id(db)
    return db.query(Photo).filter(
        Photo.status == "aprobada",
        Photo.category_id != illus_id
    ).order_by(Photo.created_at.desc()).all()

@app.get("/illustrations")
def get_illustrations(db: Session = Depends(get_db)):
    cat_id = get_illustration_category_id(db)
    return db.query(Photo).filter(
        Photo.category_id == cat_id,
        Photo.status == "aprobada"
    ).order_by(Photo.created_at.desc()).all()

@app.post("/admin/illustrations")
async def upload_illustration(
    password: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    admin_email = "admin@astrolab.com"
    photographer = db.query(Photographer).filter(Photographer.email == admin_email).first()
    if not photographer:
        photographer = Photographer(first_name="AstroLab", last_name="Mesa Editorial", email=admin_email)
        db.add(photographer)
        db.commit()
        db.refresh(photographer)

    extension = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    img = Image.open(filepath)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT))
    img.save(filepath, optimize=True, quality=IMAGE_QUALITY)

    thumb = os.path.join(THUMBNAIL_FOLDER, filename)
    mini = Image.open(filepath)
    if mini.mode in ("RGBA", "P"): mini = mini.convert("RGB")
    mini.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    mini.save(thumb, optimize=True, quality=THUMBNAIL_QUALITY)

    cat_id = get_illustration_category_id(db)
    photo = Photo(
        title=title,
        description=description,
        image=filename,
        thumbnail=f"thumbs/{filename}",
        token=str(uuid.uuid4()),
        status="aprobada",
        photographer_id=photographer.id,
        category_id=cat_id
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return {"success": True, "message": "Ilustración publicada con éxito"}

@app.get("/search")
def search(q: str, db: Session = Depends(get_db)):
    return db.query(Photo).filter(
        Photo.status == "aprobada"
    ).filter(
        Photo.title.contains(q) | Photo.description.contains(q)
    ).all()

@app.get("/category/{id}")
def category(id: int, db: Session = Depends(get_db)):
    return db.query(Photo).filter(
        Photo.category_id == id,
        Photo.status == "aprobada"
    ).all()

@app.post("/photos")
async def upload_photo(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    equipment: str = Form(""),
    telescope: str = Form(""),
    camera: str = Form(""),
    mount: str = Form(""),
    filter: str = Form(""),
    software: str = Form(""),
    exposure: str = Form(""),
    iso: str = Form(""),
    frames: str = Form(""),
    location: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    category_id: int = Form(0), 
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if review_submission:
        try:
            review = review_submission(
                title, description, equipment, location, image.filename
            )
            if not review.approved:
                raise HTTPException(status_code=400, detail=review.reason)
        except Exception as e:
            print(f"IA Review omitido o fallido: {e}")

    photographer = db.query(Photographer).filter(Photographer.email == email).first()
    if photographer is None:
        photographer = Photographer(first_name=first_name, last_name=last_name, email=email)
        db.add(photographer)
        db.commit()
        db.refresh(photographer)

    extension = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    img = Image.open(filepath)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT))
    img.save(filepath, optimize=True, quality=IMAGE_QUALITY)

    thumb = os.path.join(THUMBNAIL_FOLDER, filename)
    mini = Image.open(filepath)
    if mini.mode in ("RGBA", "P"): mini = mini.convert("RGB")
    mini.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    mini.save(thumb, optimize=True, quality=THUMBNAIL_QUALITY)

    token = str(uuid.uuid4())
    photo = Photo(
        title=title,
        description=description,
        image=filename,
        thumbnail=f"thumbs/{filename}",
        equipment=equipment,
        telescope=telescope,
        camera=camera,
        mount=mount,
        filter=filter,
        software=software,
        exposure=exposure,
        iso=iso,
        frames=frames,
        location=location,
        latitude=latitude,
        longitude=longitude,
        token=token,
        status="pendiente",
        photographer_id=photographer.id,
        category_id=category_id if category_id > 0 else None
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    if EmailService:
        try:
            EmailService.send_submission_email(photo)
        except Exception as e:
            print(f"Envío de correo omitido o fallido: {e}")

    return {
        "success": True,
        "message": "Fotografía enviada correctamente a revisión.",
        "token": token,
        "photo_id": photo.id
    }

@app.get("/edit/{token}")
def get_photo_by_token(token: str, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.token == token).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")
    return photo

@app.put("/edit/{token}")
def update_photo(token: str, data: dict = Body(...), db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.token == token).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")

    photo.title = data.get("title", photo.title)
    photo.description = data.get("description", photo.description)
    photo.equipment = data.get("equipment", photo.equipment)
    photo.telescope = data.get("telescope", photo.telescope)
    photo.camera = data.get("camera", photo.camera)
    photo.mount = data.get("mount", photo.mount)
    photo.filter = data.get("filter", photo.filter)
    photo.software = data.get("software", photo.software)
    photo.exposure = data.get("exposure", photo.exposure)
    photo.iso = data.get("iso", photo.iso)
    photo.frames = data.get("frames", photo.frames)
    photo.location = data.get("location", photo.location)
    photo.latitude = data.get("latitude", photo.latitude)
    photo.longitude = data.get("longitude", photo.longitude)
    
    photo.status = "pendiente"
    photo.reject_reason = None
    
    db.commit()
    db.refresh(photo)
    return photo

@app.put("/admin/approve/{photo_id}")
def approve_photo(photo_id: int, password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")

    photo.status = "aprobada"
    photo.reject_reason = None
    db.commit()
    db.refresh(photo)

    if EmailService:
        try: EmailService.send_approved_email(photo)
        except: pass

    return {"success": True}

@app.put("/admin/reject/{photo_id}")
def reject_photo(photo_id: int, password: str, reason: str = Body(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")

    photo.status = "rechazada"
    photo.reject_reason = reason
    db.commit()

    if EmailService:
        try: EmailService.send_rejected_email(photo)
        except: pass

    return {"success": True}

@app.put("/admin/request_changes/{photo_id}")
def request_changes(photo_id: int, password: str, reason: str = Body(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")

    photo.status = "pendiente"
    photo.reject_reason = reason
    db.commit()

    if EmailService:
        try: EmailService.send_changes_requested(photo)
        except: pass

    return {"success": True}

@app.delete("/admin/photo/{photo_id}")
def delete_photo(photo_id: int, password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")

    image_path = os.path.join(UPLOAD_FOLDER, photo.image)
    thumb_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(photo.thumbnail))

    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    if EmailService:
        try: EmailService.send_deleted_email(photo)
        except: pass

    db.delete(photo)
    db.commit()
    
    return {"success": True}

@app.get("/admin/stats")
def stats(password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    
    total = db.query(Photo).count()
    pending = db.query(Photo).filter(Photo.status == "pendiente").count()
    approved = db.query(Photo).filter(Photo.status == "aprobada").count()
    rejected = db.query(Photo).filter(Photo.status == "rechazada").count()
    photographers = db.query(Photographer).count()
    
    return {
        "photos": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "photographers": photographers
    }

@app.get("/admin/pending")
def pending(password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    return db.query(Photo).filter(Photo.status == "pendiente").order_by(Photo.created_at.desc()).all()

@app.get("/admin/approved")
def approved_list(password: str, db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    return db.query(Photo).filter(Photo.status == "aprobada").order_by(Photo.created_at.desc()).all()

@app.get("/featured")
def featured(db: Session = Depends(get_db)):
    return db.query(Photo).filter(
        Photo.featured == True,
        Photo.status == "aprobada"
    ).first()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )