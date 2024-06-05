from pydantic import BaseModel
from typing import List, Optional

class Post_Response(BaseModel):
    post_id: int
    title: Optional[str] = None
    url: Optional[str] = None
    slug: Optional[str] = None
    author_id: Optional[int] = None
    created: Optional[str] = None
    published: Optional[str] = None
    updated: Optional[str] = None
    body: Optional[str] = None
    summary: Optional[str] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: Optional[str] = None
    deleted: Optional[bool] = None
    featured_image: Optional[dict] = None
    featured_image_alt: Optional[str] = None
    tags: Optional[List[dict]] = None
    categories: Optional[List[dict]] = None

class FeaturedImage(BaseModel):
    featured_image: int
    data: str

class Post(BaseModel):
    post_id: int
    title: str
    url: str
    slug: str
    author_id: int
    created: str
    published: str
    updated: str
    body: str
    summary: str
    seo_title: str
    meta_description: str
    status: str
    deleted: bool
    featured_image: FeaturedImage