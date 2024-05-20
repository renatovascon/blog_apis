from fastapi import FastAPI, HTTPException, Request
import psycopg2
import json
from psycopg2 import sql
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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

def insert_post_into_db(payload):
    try:
        query = sql.SQL("INSERT INTO blog.posts ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, [
                'title', 'url', 'slug', 'author_id', 'created', 'published',
                'updated', 'body', 'summary', 'seo_title', 'meta_description',
                'status', 'deleted', 'featured_image', 'featured_image_alt'
            ])),
            sql.SQL(', ').join(sql.Placeholder() * len(payload))
        )
        
        conn = get_connection()
        cursor = conn.cursor()

        # Extrai os valores do payload
        values = [payload[key] for key in [
            'title', 'url', 'slug', 'author_id', 'created', 'published',
            'updated', 'body', 'summary', 'seo_title', 'meta_description',
            'status', 'deleted', 'featured_image', 'featured_image_alt'
        ]]

        cursor.execute(query, tuple(values))
        conn.commit()

        cursor.close()
        conn.close()

        # Após a inserção, você pode retornar o ID do post inserido ou os dados do post
        # Aqui, estou retornando o ID do último post inserido
        return cursor.lastrowid

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

@app.post("/post/create")
async def post_create(request: Request):
    body = await request.body()
    print(body)
    try:
        # Conecta-se ao banco de dados PostgreSQL
        conn = psycopg2.connect(**db_connection_tokapi)
        cursor = conn.cursor()

        # Decodifica o payload JSON da solicitação
        body = await request.body()
        payload = json.loads(body)

        tags = payload.pop('tags', [])
        categories = payload.pop('categories', [])

        # Comando SQL para inserir um novo artigo na tabela
        insert_query = sql.SQL("INSERT INTO blog.posts ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, ['title', 'url', 'slug', 'author_id', 'created', 'published', 'updated', 'body', 'summary', 'seo_title', 'meta_description', 'status', 'deleted', 'featured_image', 'featured_image_alt'])),
            sql.SQL(', ').join(sql.Placeholder() * len(payload)))

        # Executa o comando SQL para inserir o novo artigo
        cursor.execute(insert_query, (
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
            payload.get('featured_image'),
            payload.get('featured_image_alt'),
        ))

        for tag in tags:
            cursor.execute("INSERT INTO blog.tags (name, slug) VALUES (%s, %s)", (tag['name'], tag['slug']))

        # Por exemplo, atualizar a tabela 'categories'
        for category in categories:
            cursor.execute("INSERT INTO blog.categories (name, slug) VALUES (%s, %s)", (category['name'], category['slug']))

        # Obtém o ID do artigo recém-inserido
        conn.commit()

        cursor.execute("SELECT * FROM blog.posts WHERE post_id = LASTVAL()")

        new_article = cursor.fetchone()

        cursor.close()
        conn.close()
        # Retorna uma resposta de sucesso
        return {'status': 'success', 'message': 'Artigo criado com sucesso!', 'article': new_article}

    except Exception as e:
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
