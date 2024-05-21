from fastapi import FastAPI, HTTPException, Request
import psycopg2
import json
from psycopg2 import sql
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

db_connection_tokapi = {
    'user': 'temporario',
    'password': '010a8de4cc1875d2b12d',
    'host': '0.0.0.0',
    'port': '1234',
    'database': 'tokapi'
}


def get_connection():
    try:
        conn = psycopg2.connect(**db_connection_tokapi)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_query(query, conn):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_posts_from_db():
    query = "SELECT * FROM blog.posts"
    conn = get_connection()
    return execute_query(query, conn)

def get_post_by_id_from_db(post_id: int):
    query = sql.SQL("SELECT * FROM blog.posts WHERE post_id = %s")
    conn = get_connection()
    return execute_query(query, conn)

def get_categories_from_db():
    query = "SELECT * FROM blog.categories"
    conn = get_connection()
    return execute_query(query, conn)

def get_tags_from_db():
    query = "SELECT * FROM blog.tags"
    conn = get_connection()
    return execute_query(query, conn)

@app.get("/post")
def get_posts():
    try:
        posts = get_posts_from_db()
        posts_json = [{'post_id': post[0], 'title': post[1], 'url': post[2], 'slug': post[3], 
                      'author_id': post[4], 'created': post[5], 'published': post[6], 'updated': post[7], 
                      'body': post[8], 'summary': post[9], 'seo_title': post[10], 'meta_description': post[11], 
                      'status': post[12], 'deleted': post[13], 'featured_image': post[14], 'featured_image_alt': post[15]}
                      for post in posts]
        return {'status': 'success', 'data': posts_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/post/{post_id}")
def get_post_by_id_from_db(post_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = sql.SQL("SELECT * FROM blog.posts WHERE post_id = {}").format(sql.Literal(post_id))
        cursor.execute(query)
        post = cursor.fetchone()

        cursor.close()
        conn.close()

        if post:
            # Mapear os resultados para um dicionário com a estrutura desejada
            post_json = {
                'status': 'success',
                'data': {
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
            }
            return post_json
        else:
            # Se não houver post encontrado, retorne uma resposta de erro
            raise HTTPException(status_code=404, detail="Post não encontrado")
    except Exception as e:
        # Em caso de erro, retorne uma resposta de erro com status 500
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    try:
        categories = get_categories_from_db()
        categories_json = [{'name': category[1], 'slug': category[2]} for category in categories]
        return {'status': 'success', 'data': categories_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags")
def get_tags():
    try:
        tags = get_tags_from_db()
        tags_json = [{'name': tag[1], 'slug': tag[2]} for tag in tags]
        return {'status': 'success', 'data': tags_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_insert_query(query, values):
    try:
        with psycopg2.connect(**db_connection_tokapi) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
                return cursor.fetchone()[0] 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def post_categories(categories: list):
    query = "INSERT INTO blog.categories (name, slug) VALUES (%s, %s) RETURNING category_id"
    category_ids = []
    for category in categories:
        category_id = execute_insert_query(query, (category['name'], category['slug']))
        category_ids.append(category_id)
    return category_ids

def post_tags(tags: list):
    query = "INSERT INTO blog.tags (name, slug) VALUES (%s, %s) RETURNING tag_id"
    tag_ids = []
    for tag in tags:
        tag_id = execute_insert_query(query, (tag['name'], tag['slug']))
        tag_ids.append(tag_id)
    return tag_ids

def post_featured_image(featured_image: dict):
    query = """
        INSERT INTO blog.featured_image 
        (data, last_modified, last_modified_date, name, size, type, webkit_relative_path) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING featured_image
    """
    values = (
        featured_image.get('data'),
        featured_image.get('last_modified'),
        featured_image.get('last_modified_date'),
        featured_image.get('name'),
        featured_image.get('size'),
        featured_image.get('type'),
        featured_image.get('webkit_relative_path')
    )
    return execute_insert_query(query, values)

def insert_post_category_relations(cursor, post_id: int, category_ids: list):
    query = "INSERT INTO blog.posts_categories_relation (post_id, category_id) VALUES (%s, %s)"
    for category_id in category_ids:
        cursor.execute(query, (post_id, category_id))

def insert_post_tag_relations(cursor, post_id: int, tag_ids: list):
    query = "INSERT INTO blog.posts_tags_relation (post_id, tag_id) VALUES (%s, %s)"
    for tag_id in tag_ids:
        cursor.execute(query, (post_id, tag_id))

@app.post("/post/create")
async def post_create(request: Request):
    body = await request.body()
    payload = json.loads(body)
    tags = payload.pop('tags', [])
    categories = payload.pop('categories', [])
    featured_image = payload.pop('featured_image', None)
    category_ids = []
    tag_ids = []

    try:
      with psycopg2.connect(**db_connection_tokapi) as conn:
          with conn.cursor() as cursor:
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

              cursor.execute(insert_query, tuple(payload.values()))
              new_post_id = cursor.fetchone()[0]
              new_article = cursor.fetchone()

              insert_post_category_relations(cursor, new_post_id, category_ids)
              insert_post_tag_relations(cursor, new_post_id, tag_ids)

              conn.commit()

      return {'status': 'success', 'message': 'Artigo criado com sucesso!', 'article': new_article}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

@app.patch("/post/update/{post_id}")
async def update_post(request: Request, post_id: int):
    try:
        payload = await request.json()
        
        # Conecta-se ao banco de dados PostgreSQL
        conn = psycopg2.connect(**db_connection_tokapi)
        cursor = conn.cursor()

        # Comando SQL para atualizar o post na tabela
        update_query = """
            UPDATE blog.posts 
            SET 
                title = %s,
                url = %s,
                slug = %s,
                author_id = %s,
                created = %s,
                published = %s,
                updated = %s,
                body = %s,
                summary = %s,
                seo_title = %s,
                meta_description = %s,
                status = %s,
                deleted = %s,
                featured_image_alt = %s
            WHERE post_id = %s
        """
        
        # Extrai os valores do payload
        post_values = (
            payload.get('title'),
            payload.get('url'),
            payload.get('slug'),
            payload.get('author_id'),
            payload.get('created'),
            payload.get('published'),
            payload.get('updated'),
            payload.get('body'),
            payload.get('summary'),
            payload.get('seo_title'),
            payload.get('meta_description'),
            payload.get('status'),
            payload.get('deleted'),
            payload.get('featured_image_alt'),
            post_id
        )

        # Executa o comando SQL para atualizar o post
        cursor.execute(update_query, post_values)
        conn.commit()

        cursor.close()
        conn.close()

        return {'status': 'success', 'message': 'Post atualizado com sucesso!'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{text}")
def search_posts_by_keyword(text: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = sql.SQL("SELECT * FROM blog.posts WHERE body ILIKE {}").format(sql.Literal(f"%{text}%"))
        cursor.execute(query)
        posts = cursor.fetchall()

        cursor.close()
        conn.close()

        if posts:
            # Mapear os resultados para uma lista de dicionários com a estrutura desejada
            posts_json = []
            for post in posts:
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
                posts_json.append(post_json)
            
            return {'status': 'success', 'data': posts_json}
        else:
            # Se não houver posts encontrados, retorne uma resposta de erro
            raise HTTPException(status_code=404, detail="Nenhum post encontrado com a palavra-chave fornecida")
    except Exception as e:
        # Em caso de erro, retorne uma resposta de erro com status 500
        raise HTTPException(status_code=500, detail=str(e))
    


# search_posts_by_keyword("asdasdaI")