from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class PhotoStatus(str, Enum):
    pendiente = 'pendiente'
    aprobada = 'aprobada'
    rechazada = 'rechazada'

class Photographer(Base):
    __tablename__ = 'photographers'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(180), nullable=False, unique=True)
    biography = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    photos = relationship('Photo', back_populates='photographer')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    icon = Column(String(30), default='✦')
    products = relationship('Product', back_populates='category')

class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, default='')
    image = Column(String(500), nullable=False)
    telescope = Column(String(180), default='')
    camera = Column(String(180), default='')
    mount = Column(String(180), default='')
    exposure = Column(String(80), default='')
    iso = Column(String(50), default='')
    contributor_name = Column(String(100), default='')
    contributor_email = Column(String(180), default='')
    instagram = Column(String(120), default='')
    location = Column(String(180), default='')
    community_category = Column(String(100), default='')
    likes = Column(Integer, default=0)
    status = Column(SAEnum(PhotoStatus), default=PhotoStatus.pendiente, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    photographer_id = Column(Integer, ForeignKey('photographers.id'), nullable=True)
    photographer = relationship('Photographer', back_populates='photos')
    __table_args__ = (
        Index('ix_photos_status_created', 'status', 'created_at'),
        Index('ix_photos_category_created', 'community_category', 'created_at'),
    )

class PhotoLike(Base):
    __tablename__ = 'photo_likes'
    id = Column(Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'), nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(180), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('photo_id', 'email', name='uq_photo_like_email'),
        Index('ix_photo_likes_photo', 'photo_id'),
    )

class CommunityNote(Base):
    __tablename__ = 'community_notes'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    email = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    approved = Column(Boolean, default=True)
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('ix_notes_created', 'created_at'),
    )

class NoteLike(Base):
    __tablename__ = 'note_likes'
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey('community_notes.id', ondelete='CASCADE'), nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(180), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('note_id', 'email', name='uq_note_like_email'),
        Index('ix_note_likes_note', 'note_id'),
    )

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(220), nullable=False)
    slug = Column(String(240), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    author = Column(String(140), default='ADV-Lab')
    cover = Column(String(500), default='')
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AstronomicalEvent(Base):
    __tablename__ = 'astronomical_events'
    id = Column(Integer, primary_key=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, default='')
    event_date = Column(DateTime, nullable=False)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(180), nullable=False)
    description = Column(Text, default='')
    price = Column(Float, default=0)
    image = Column(String(500), default='')
    stock = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    contact_url = Column(String(500), default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='products')

class ContactRequest(Base):
    __tablename__ = 'contact_requests'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    product_name = Column(String(180), default='')
    full_name = Column(String(140), nullable=False)
    whatsapp = Column(String(60), nullable=False)
    email = Column(String(180), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(40), default='nuevo')
    __table_args__ = (
        Index('ix_contact_requests_created', 'created_at'),
    )
