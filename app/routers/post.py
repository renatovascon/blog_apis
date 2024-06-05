# app/routers/posts.py
from fastapi import APIRouter, HTTPException, Request
from typing import  List
from psycopg2 import sql
from app.models.post import Post, Post_Response
import json


from app.database.operations import (
    get_posts_from_db,
    get_post_by_id_from_db,
    post_categories,
    post_tags,
    post_featured_image,
    execute_insert_query,
    insert_post_category_relations,
    insert_post_tag_relations,
    update_post_category_relations,
    update_post_tag_relations,
    patch_featured_image,
    execute_query,
    map_post_to_json,
    get_featured_image
)

router = APIRouter()


@router.get("/posts", response_model=List[Post_Response])
def get_posts():
    try:
        posts = get_posts_from_db()
        posts_json = [map_post_to_json(post) for post in posts]
        return posts_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/{post_id}", response_model=Post_Response)
def get_post_by_id(post_id: int):
    post = get_post_by_id_from_db(post_id)
    if post:
        posts_json = map_post_to_json(post)
        return posts_json
    raise HTTPException(status_code=404, detail="Post não encontrado")


@router.get("/posts/category_id/{category_id}", response_model=List[Post_Response])
def get_posts_by_category_id(category_id: int):
    posts = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE category_id = {}").format(sql.Literal(category_id))
        
        posts_array = execute_query(query, fetch_all=True)
        for row in posts_array:
            posts_id = row[0]
            post_data = get_post_by_id_from_db(posts_id)
            if post_data:
                post_json = map_post_to_json(post_data)
                posts.append(post_json)

        return  posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{text}", response_model=List[Post_Response])
def search_posts_by_keyword(text: str):
    try:
        query = sql.SQL("SELECT * FROM blog.posts WHERE body ILIKE {}").format(sql.Literal(f"%{text}%"))
        posts = execute_query(query, fetch_all=True)
        if posts:
            posts_json = [map_post_to_json(post) for post in posts]
            return {'status': 'success', 'data': posts_json}
        else:
            raise HTTPException(status_code=404, detail="Nenhum post encontrado com a palavra-chave fornecida")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/posts/create")
async def post_create(request: Request):
    body = await request.body()
    payload = json.loads(body)
    tags = payload.pop('tags', [])
    categories = payload.pop('categories', [])
    featured_image = payload.pop('featured_image', None)
    category_ids = []
    tag_ids = []

    try:
        if categories:
            category_ids = post_categories(categories)
        if tags:
            tag_ids = post_tags(tags)
        if featured_image:
            featured_image_id = post_featured_image(featured_image)
        if featured_image_id:
            payload['featured_image'] = featured_image_id

        insert_query = sql.SQL("INSERT INTO blog.posts ({}) VALUES ({}) RETURNING *").format(
            sql.SQL(', ').join(map(sql.Identifier, payload.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(payload))
        )

        new_post_id = execute_insert_query(insert_query, tuple(payload.values()))
        insert_post_category_relations(new_post_id, category_ids)
        insert_post_tag_relations(new_post_id, tag_ids)


        return {'status': 'success', 'message': 'Artigo criado com sucesso!', 'article_id': new_post_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@router.patch("/posts/update/{post_id}")
async def update_post(post_id: int, request: Request):
# async def update_post(request: Request, post_id: int):
    try:
        payload = await request.json()
        featured_image = payload.pop('featured_image', None)
        featured_image_id = featured_image.get('featured_image') if featured_image else None
        tags = payload.pop('tags', [])
        categories = payload.pop('categories', [])
        if categories:
            category_ids = post_categories(categories)
            update_post_category_relations(post_id, category_ids)
        if tags:
            tag_ids = post_tags(tags)
            update_post_tag_relations(post_id, tag_ids)

        if featured_image:
            if featured_image_id:
                patch_featured_image(featured_image, featured_image_id)
            else:
                featured_image_id = post_featured_image(featured_image)
            payload['featured_image'] = featured_image_id

        set_clauses = []
        values = []
        
        for key, value in payload.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        set_clause = ", ".join(set_clauses)
        values.append(post_id)
        
        update_query = f"UPDATE blog.posts SET {set_clause} WHERE post_id = %s"
        
        execute_query(update_query, tuple(values))
        
        return {'status': 'success', 'message': 'updated_post'}

    except Exception as e:
        print('error-patch:', str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/posts/search/{text}")
async def search_posts_by_keyword(text: str):
    try:
        query = sql.SQL("SELECT * FROM blog.posts WHERE body ILIKE {}").format(sql.Literal(f"%{text}%"))
        posts = execute_query(query, fetch_all=True)

        if posts:
            # Mapear os resultados para uma lista de dicionários com a estrutura desejada
            posts_json = []
            for post in posts:
                featured_image_data = get_featured_image(post[14])

                post_json = {
                    'post_id': post[0],
                    'title': post[1],
                    'url': post[2],
                    'slug': post[3],
                    'author_id': post[4],
                    'created': post[5].isoformat() if post[5] else None,
                    'published': post[6].isoformat() if post[6] else None,
                    'updated': post[7].isoformat() if post[7] else None,
                    'body': post[8],
                    'summary': post[9],
                    'seo_title': post[10],
                    'meta_description': post[11],
                    'status': post[12],
                    'deleted': post[13],
                    'featured_image': post[14],
                    'featured_image_alt': post[15]
                }
                if featured_image_data:
                    post_json['featured_image'] = featured_image_data

                posts_json.append(post_json)
            
            return {'status': 'success', 'data': posts_json}
        else:
            # Se não houver posts encontrados, retorne uma resposta de erro
            raise HTTPException(status_code=404, detail="Nenhum post encontrado com a palavra-chave fornecida")
    except Exception as e:
        # Em caso de erro, retorne uma resposta de erro com status 500
        raise HTTPException(status_code=500, detail=str(e))
    