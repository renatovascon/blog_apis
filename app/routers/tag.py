from fastapi import APIRouter, HTTPException
from app.database.operations import get_tags_from_db, get_tags_by_id, execute_query
from psycopg2 import sql
from typing import  List
from app.models.tag import Tag

router = APIRouter()

@router.get("/tags", response_model=List[Tag])
def get_tags():
    try:
        tags = get_tags_from_db()
        tags_json = [{'tag_id': tag[0], 'name': tag[1], 'slug': tag[2]} for tag in tags]
        return tags_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tags/{post_id}")
def get_tags_by_post_id(post_id: int):
    tags = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts_tags_relation WHERE post_id = {}").format(sql.Literal(post_id))
        tags_array = execute_query(query, fetch_all=True)
        
        for row in tags_array:
            tags_id = row[1]
            tags.append(get_tags_by_id(tags_id))

        return tags
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
