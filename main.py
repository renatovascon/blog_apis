from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from psycopg2 import sql
import json
from dotenv import load_dotenv
from app.database.connection import get_connection
from app.database.operations import(
    execute_query,
    get_featured_image,
    get_posts_from_db,
    get_categories_from_db,
    get_categories_by_id,
    get_tags_by_id,
    get_tags_from_db,
    post_categories,
    post_tags,
    post_featured_image,
    update_post_category_relations,
    update_post_tag_relations,
    insert_post_category_relations,
    insert_post_tag_relations,
    execute_insert_query,
    patch_featured_image
)

load_dotenv()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

@app.get("/search/{text}")
def search_posts_by_keyword(text: str):
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
    
@app.get("/posts")
def get_posts():
    posts_json = []
    posts = get_posts_from_db()
    try:
        for post in posts:
            post_dict = {'post_id': post[0], 'title': post[1], 'url': post[2], 'slug': post[3], 
                      'author_id': post[4], 'created': post[5], 'published': post[6], 'updated': post[7], 
                      'body': post[8], 'summary': post[9], 'seo_title': post[10], 'meta_description': post[11], 
                      'status': post[12], 'deleted': post[13], 'featured_image': post[14], 'featured_image_alt': post[15]
                      }
                      
        
            featured_image_data = get_featured_image(post[14])
            if featured_image_data:
                post_dict['featured_image'] = featured_image_data

            posts_json.append(post_dict)
                      
        return {'status': 'success', 'data': posts_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{post_id}")
def get_post_by_id_from_db(post_id: int):
    posts_json = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts WHERE post_id = {}").format(sql.Literal(post_id))
        post = execute_query(query, fetch_one=True)

        if post:
            # Mapear os resultados para um dicionário com a estrutura desejada
            post_dict = {
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
            featured_image_data = get_featured_image(post[14])
            if featured_image_data:
                post_dict['featured_image'] = featured_image_data

            posts_json.append(post_dict)
            
            return posts_json[0]
        else:

            raise HTTPException(status_code=404, detail="Post não encontrado")
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    try:
        categories = get_categories_from_db()
        categories_json = [{'category_id': category[0], 'name': category[1], 'slug': category[2]} for category in categories]
        return {'status': 'success', 'data': categories_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories/{post_id}")
def get_categories_by_post_id(post_id: int):
    categories = []
    try:

        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE post_id = {}").format(sql.Literal(post_id))
        categories_array = execute_query(query, fetch_all=True)
        
        for row in categories_array:
            categories_id = row[1]
            categories.append(get_categories_by_id(categories_id))

        return {'status': 'success', 'data': categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags/{post_id}")
def get_tags_by_post_id(post_id: int):
    tags = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts_tags_relation WHERE post_id = {}").format(sql.Literal(post_id))
        tags_array = execute_query(query, fetch_all=True)
        
        for row in tags_array:
            tags_id = row[1]
            tags.append(get_tags_by_id(tags_id))

        return {'status': 'success', 'data': tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags")
def get_tags():
    try:
        tags = get_tags_from_db()
        tags_json = [{'tag_id': tag[0], 'name': tag[1], 'slug': tag[2]} for tag in tags]
        return {'status': 'success', 'data': tags_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/category_id/{category_id}")
def get_posts_by_category_id(category_id: int):
    posts = []
    try:
        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE category_id = {}").format(sql.Literal(category_id))
        
        posts_array = execute_query(query, fetch_all=True)
        
        for row in posts_array:
            posts_id = row[0]
            posts.append(get_post_by_id_from_db(posts_id))

        return {'status': 'success', 'data': posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/create")
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
        
@app.patch("/posts/update/{post_id}")
async def update_post(request: Request, post_id: int):
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

