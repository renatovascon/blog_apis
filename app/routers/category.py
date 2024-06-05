from fastapi import APIRouter, HTTPException
from app.database.operations import get_categories_from_db, get_categories_by_id, execute_query
from psycopg2 import sql
from app.models.category import Category
from typing import  List


router = APIRouter()

@router.get("/categories", response_model=List[Category])
def get_categories():
    try:
        categories = get_categories_from_db()
        categories_json = [{'category_id': category[0], 'name': category[1], 'slug': category[2]} for category in categories]
        return categories_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{post_id}", response_model=List[Category])
def get_categories_by_post_id(post_id: int):
    categories = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE post_id = {}").format(sql.Literal(post_id))
        categories_array = execute_query(query, fetch_all=True)
        for row in categories_array:
            categories_id = row[1]
            categories.append(get_categories_by_id(categories_id))
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))