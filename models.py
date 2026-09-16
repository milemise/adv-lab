from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Boolean
)

from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# ==========================================================
# FOTÓGRAFOS
# ==========================================================

class Photographer(Base):
    __tablename__ = "photographers"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(100), nullable=False)

    last_name = Column(String(100), nullable=False)

    email = Column(String(150), unique=True, nullable=False)

    biography = Column(Text)

    country = Column(String(100))

    city = Column(String(100))

    instagram = Column(String(200))

    facebook = Column(String(200))

    website = Column(String(200))

    avatar = Column(String(255))

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    photos = relationship(
        "Photo",
        back_populates="photographer",
        cascade="all, delete"
    )


# ==========================================================
# CATEGORÍAS
# ==========================================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    name = Column(
        String(80),
        unique=True,
        nullable=False
    )

    icon = Column(String(100))

    photos = relationship(
        "Photo",
        back_populates="category"
    )


# ==========================================================
# FOTOGRAFÍAS
# ==========================================================

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(Text)

    image = Column(
        String(255),
        nullable=False
    )

    thumbnail = Column(String(255))

    equipment = Column(String(250))

    telescope = Column(String(150))

    camera = Column(String(150))

    mount = Column(String(150))

    filter = Column(String(150))

    software = Column(String(150))

    exposure = Column(String(80))

    iso = Column(String(50))

    frames = Column(String(50))

    location = Column(String(200))

    latitude = Column(String(50))

    longitude = Column(String(50))

    token = Column(
        String(255),
        unique=True
    )

    status = Column(
        Enum(
            "pendiente",
            "aprobada",
            "rechazada",
            name="photo_status"
        ),
        default="pendiente"
    )

    reject_reason = Column(Text)

    featured = Column(
        Boolean,
        default=False
    )

    views = Column(
        Integer,
        default=0
    )

    likes = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    photographer_id = Column(
        Integer,
        ForeignKey("photographers.id")
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id")
    )

    photographer = relationship(
        "Photographer",
        back_populates="photos"
    )

    category = relationship(
        "Category",
        back_populates="photos"
    )


# ==========================================================
# ARTÍCULOS
# ==========================================================

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)

    title = Column(
        String(250),
        nullable=False
    )

    slug = Column(
        String(250),
        unique=True
    )

    excerpt = Column(Text)

    content = Column(Text)

    cover = Column(String(255))

    author = Column(String(150))

    published = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# EVENTOS ASTRONÓMICOS
# ==========================================================

class AstronomicalEvent(Base):
    __tablename__ = "astronomical_events"

    id = Column(Integer, primary_key=True)

    title = Column(String(200))

    description = Column(Text)

    type = Column(String(100))

    event_date = Column(DateTime)

    image = Column(String(255))


# ==========================================================
# CONFIGURACIÓN DEL SITIO
# ==========================================================

class SiteSettings(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True)

    hero_title = Column(String(255))

    hero_text = Column(Text)

    featured_photo_id = Column(Integer)

    featured_article_id = Column(Integer)

    editor_pick = Column(Integer)