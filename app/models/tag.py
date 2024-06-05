from pydantic import BaseModel

class Tag(BaseModel):
    tag_id: int
    name: str
    slug: str