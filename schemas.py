from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(default='', max_length=1200)
    price: float = Field(default=0, ge=0, le=100000000)
    image: str = Field(default='', max_length=500)
    stock: int = Field(default=0, ge=0, le=100000)
    active: bool = True
    contact_url: str = Field(default='', max_length=500)
    category_id: Optional[int] = None

class ArticleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=220)
    slug: str = Field(min_length=2, max_length=240)
    content: str = Field(min_length=1, max_length=20000)
    author: str = Field(default='ADV-Lab', max_length=140)
    cover: str = Field(default='', max_length=500)
    published: bool = True

class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(default='', max_length=1000)
    event_date: datetime

class PhotoLikeCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=180)

class NoteCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=180)
    body: str = Field(min_length=5, max_length=900)

class NoteLikeCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=180)

class ContactRequestCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(default='', max_length=180)
    full_name: str = Field(min_length=2, max_length=140)
    whatsapp: str = Field(min_length=6, max_length=60)
    email: str = Field(min_length=5, max_length=180)
    message: str = Field(min_length=5, max_length=1200)
