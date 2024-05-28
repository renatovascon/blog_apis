from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import psycopg2
from psycopg2 import sql
import json
from dotenv import load_dotenv
from pathlib import Path, os

load_dotenv()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

db_connection_tokapi = {
    'user': str(os.getenv('USER_CONECTION_TOKAPI')),
    'password': str(os.getenv('PASSWORD_CONECTION_TOKAPI')),
    'host': str(os.getenv('HOST_CONECTION_TOKAPI')),
    'port': str(os.getenv('PORT_CONECTION_TOKAPI')),
    'database': str(os.getenv('DATABASE_CONECTION_TOKAPI'))
}

# class PostCreate(BaseModel):
#     title: str
#     url: str
#     slug: str
#     author_id: int
#     created: Optional[str]
#     published: Optional[str]
#     updated: Optional[str]
#     body: str
#     summary: str
#     seo_title: str
#     meta_description: str
#     status: str
#     featured_image: Optional[dict]
#     categories: List[dict]
#     tags: List[dict]

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
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_query_one_data(query, conn):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
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

def get_featured_image_from_db():
    query = "SELECT * FROM blog.featured_image"
    conn = get_connection()
    return execute_query(query, conn)

def get_categories_by_id(category_id: int):
    try:
        conn = get_connection()
        query = sql.SQL("SELECT * FROM blog.categories WHERE category_id = {}").format(sql.Literal(category_id))
        categories = execute_query_one_data(query, conn)
        categories_json = {'name': categories[1], 'slug': categories[2]}
        return categories_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_tags_by_id(tag_id: int):
    try:
        conn = get_connection()
        query = sql.SQL("SELECT * FROM blog.tags WHERE tag_id = {}").format(sql.Literal(tag_id))
        tags = execute_query_one_data(query, conn)
        tags_json = {'name': tags[1], 'slug': tags[2]}
        return tags_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_featured_image(featured_image_id  : int):
        try:
            conn = get_connection()
            query = sql.SQL("SELECT * FROM blog.featured_image WHERE featured_image = {}").format(sql.Literal(featured_image_id))
            
            featured_image = execute_query_one_data(query, conn)
            conn.close()

            if featured_image:
                featured_image_json = {
                        'id' : featured_image[0],
                        'data': featured_image[1], 
                        'last_modified': featured_image[2], 
                        'last_modified_date': featured_image[3], 
                        'name': featured_image[4], 
                        'size': featured_image[5], 
                        'type': featured_image[6], 
                        'webkit_relative_path': featured_image[7]
                    }
                return featured_image_json
            else:
            # Se não houver post encontrado, retorne uma resposta de erro
                print(featured_image)
                # raise HTTPException(status_code=404, detail="Imagem não encontrado")
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

def execute_insert_query_relational(query, values):
    try:
        with psycopg2.connect(**db_connection_tokapi) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_query_params(query, params, conn):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def post_categories(categories: list):
    conn = get_connection()
    select_query = "SELECT category_id FROM blog.categories WHERE name = %s"
    insert_query = "INSERT INTO blog.categories (name, slug) VALUES (%s, %s) RETURNING category_id"
    category_ids = []
    for category in categories:
        # Verificar se o nome da categoria já existe
        existing_category = execute_query_params(select_query, (category['name'],), conn)
        if existing_category:
            # Se a categoria já existe, obter o category_id
            category_id = existing_category[0][0]  # Acessa o primeiro elemento da tupla
        else:
            # Caso contrário, inserir a nova categoria e obter o category_id
            category_id = execute_insert_query(insert_query, (category['name'], category['slug']))
        
        category_ids.append(category_id)

    return category_ids

def post_tags(tags: list):
    conn = get_connection()
    select_query = "SELECT tag_id FROM blog.tags WHERE name = %s"
    insert_query = "INSERT INTO blog.tags (name, slug) VALUES (%s, %s) RETURNING tag_id"
    tag_ids = []
    for tag in tags:
        # Verificar se o nome da categoria já existe
        existing_tag = execute_query_params(select_query, (tag['name'],), conn)
        if existing_tag:
            # Se a categoria já existe, obter o category_id
            tag_id = existing_tag[0][0]
        else:
            # Caso contrário, inserir a nova categoria e obter o category_id
            tag_id = execute_insert_query(insert_query, (tag['name'], tag['slug']))
        
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
    select_query = "SELECT 1 FROM blog.posts_categories_relation WHERE post_id = %s AND category_id = %s"
    insert_query = "INSERT INTO blog.posts_categories_relation (post_id, category_id) VALUES (%s, %s)"
    
    for category_id in category_ids:
        cursor.execute(select_query, (post_id, category_id))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(insert_query, (post_id, category_id))

def insert_post_tag_relations(cursor, post_id: int, tag_ids: list):
    select_query = "SELECT 1 FROM blog.posts_tags_relation WHERE post_id = %s AND tag_id = %s"
    insert_query = "INSERT INTO blog.posts_tags_relation (post_id, tag_id) VALUES (%s, %s)"
    
    for tag_id in tag_ids:
        cursor.execute(select_query, (post_id, tag_id))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(insert_query, (post_id, tag_id))

def update_post_category_relations(cursor, post_id: int, category_ids: list):
    # Excluir todas as relações existentes para o post
    delete_query = "DELETE FROM blog.posts_categories_relation WHERE post_id = %s"
    execute_insert_query_relational(delete_query, (post_id,))

    # Inserir as novas relações
    insert_query = "INSERT INTO blog.posts_categories_relation (post_id, category_id) VALUES (%s, %s)"
    for category_id in category_ids:
        execute_insert_query_relational(insert_query, (post_id, category_id))

def update_post_tag_relations(cursor, post_id: int, tag_ids: list):
    # Excluir todas as relações existentes para o post
    delete_query = "DELETE FROM blog.posts_tags_relation WHERE post_id = %s"
    execute_insert_query_relational(delete_query, (post_id,))

    # Inserir as novas relações
    insert_query = "INSERT INTO blog.posts_tags_relation (post_id, tag_id) VALUES (%s, %s)"
    for tag_id in tag_ids:
        execute_insert_query_relational(insert_query, (post_id, tag_id))

@app.get("/search/{text}")
def search_posts_by_keyword(text: str):
    try:
        conn = get_connection()
        query = sql.SQL("SELECT * FROM blog.posts WHERE body ILIKE {}").format(sql.Literal(f"%{text}%"))
        
        posts = execute_query(query, conn)

        conn.close()

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
    
@app.get("/post")
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

@app.get("/post/{post_id}")
def get_post_by_id_from_db(post_id: int):
    posts_json = []
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
        conn = get_connection()
        cursor = conn.cursor()

        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE post_id = {}").format(sql.Literal(post_id))
        cursor.execute(query)
        
        for row in cursor.fetchall():
            categories_id = row[1]
            categories.append(get_categories_by_id(categories_id))

        return {'status': 'success', 'data': categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tags/{post_id}")
def get_tags_by_post_id(post_id: int):
    tags = []
    try:
        conn = get_connection()
        query = sql.SQL("SELECT * FROM blog.posts_tags_relation WHERE post_id = {}").format(sql.Literal(post_id))
        cursor = conn.cursor()

        cursor.execute(query)
        tags_array = execute_query(query, conn)
        
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
        conn = get_connection()
        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE category_id = {}").format(sql.Literal(category_id))
        
        posts_array = execute_query(query, conn)
        
        for row in posts_array:
            posts_id = row[0]
            posts.append(get_post_by_id_from_db(posts_id))

        return {'status': 'success', 'data': posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    finally:
        if conn:
            conn.close()
        
def patch_featured_image(featured_image: dict, featured_image_id: int):
    query = """
        UPDATE blog.featured_image SET
        data = %s, 
        last_modified = %s, 
        last_modified_date = %s, 
        name = %s, 
        size = %s, 
        type = %s, 
        webkit_relative_path = %s 
        WHERE featured_image = %s
    """
    values = (
        featured_image.get('data'),
        featured_image.get('last_modified'),
        featured_image.get('last_modified_date'),
        featured_image.get('name'),
        featured_image.get('size'),
        featured_image.get('type'),
        featured_image.get('webkit_relative_path'),
        featured_image_id
    )
    execute_insert_query_relational(query, values)
    return featured_image_id


@app.patch("/post/update/{post_id}")
async def update_post(request: Request, post_id: int):
    try:
        # Conecta-se ao banco de dados PostgreSQL
        conn = get_connection()
        cursor = conn.cursor()

        payload = await request.json()
        featured_image = payload.pop('featured_image', None)
        featured_image_id = featured_image.get('id') if featured_image else None
        print(featured_image_id)
        tags = payload.pop('tags', [])
        categories = payload.pop('categories', [])
        if categories:
            category_ids = post_categories(categories)
            print(category_ids)
            update_post_category_relations(cursor, post_id, category_ids)
        if tags:
            tag_ids = post_tags(tags)
            update_post_tag_relations(cursor, post_id, tag_ids)

        if featured_image_id:
            patch_featured_image(featured_image, featured_image_id)
        else:
            featured_image_id = post_featured_image(featured_image)

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
                featured_image = %s,
                featured_image_alt = %s
            WHERE post_id = %s
        """
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
            featured_image_id,
            payload.get('featured_image_alt'),
            post_id
        )

        # Executa o comando SQL para atualizar o post
        cursor.execute(update_query, post_values)

        # updated_post = cursor.fetchone()
        # print(update_post)
        
        conn.commit()

        return {'status': 'success', 'message': 'updated_post'}

    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# get_tags_by_post_id(97)
