from pydantic import BaseModel, EmailStr
from datetime import datetime


# ==========================================================
# CATEGORÍAS
# ==========================================================

class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: str | None = None

    class Config:
        from_attributes = True


# ==========================================================
# FOTÓGRAFOS
# ==========================================================

class PhotographerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    biography: str | None = None
    country: str | None = None
    city: str | None = None
    instagram: str | None = None
    facebook: str | None = None
    website: str | None = None


class PhotographerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    biography: str | None
    country: str | None
    city: str | None
    instagram: str | None
    facebook: str | None
    website: str | None
    avatar: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================================
# FOTOGRAFÍAS
# ==========================================================

class PhotoCreate(BaseModel):

    title: str
    description: str | None = None

    equipment: str | None = None

    telescope: str | None = None
    camera: str | None = None
    mount: str | None = None
    filter: str | None = None

    software: str | None = None

    exposure: str | None = None

    iso: str | None = None

    frames: str | None = None

    location: str | None = None

    latitude: str | None = None

    longitude: str | None = None

    photographer_id: int

    category_id: int


class PhotoUpdate(BaseModel):

    title: str

    description: str | None = None

    equipment: str | None = None

    telescope: str | None = None

    camera: str | None = None

    mount: str | None = None

    filter: str | None = None

    software: str | None = None

    exposure: str | None = None

    iso: str | None = None

    frames: str | None = None

    location: str | None = None

    latitude: str | None = None

    longitude: str | None = None


class PhotoResponse(BaseModel):

    id: int

    title: str

    description: str | None

    image: str

    thumbnail: str | None

    equipment: str | None

    telescope: str | None

    camera: str | None

    mount: str | None

    filter: str | None

    software: str | None

    exposure: str | None

    iso: str | None

    frames: str | None

    location: str | None

    latitude: str | None

    longitude: str | None

    token: str

    status: str

    reject_reason: str | None

    featured: bool

    likes: int

    views: int

    created_at: datetime

    photographer: PhotographerResponse

    category: CategoryResponse

    class Config:
        from_attributes = True


# ==========================================================
# ARTÍCULOS
# ==========================================================

class ArticleCreate(BaseModel):

    title: str

    excerpt: str

    content: str

    author: str


class ArticleResponse(BaseModel):

    id: int

    title: str

    slug: str | None

    excerpt: str | None

    content: str

    cover: str | None

    author: str

    published: bool

    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================================
# EVENTOS
# ==========================================================

class EventCreate(BaseModel):

    title: str

    description: str

    type: str

    event_date: datetime


class EventResponse(BaseModel):

    id: int

    title: str

    description: str

    type: str

    event_date: datetime

    image: str | None

    class Config:
        from_attributes = True


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

class SettingsResponse(BaseModel):

    hero_title: str | None

    hero_text: str | None

    featured_photo_id: int | None

    featured_article_id: int | None

    editor_pick: int | None

    class Config:
        from_attributes = True