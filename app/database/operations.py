from fastapi import HTTPException
from app.database.connection import get_connection
from psycopg2 import sql
from datetime import datetime

def execute_query(query, values=None, fetch_one=False, fetch_all=False):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
    except Exception as e:
        print('error execute_query', e)
        raise HTTPException(status_code=401, detail=str(e))

def execute_insert_query(query, values):
    result = execute_query(query, values, fetch_one=True)
    return result[0] if result else None

def fetch_all_records(table_name):
    schema, table = table_name.split('.')
    query = sql.SQL("SELECT * FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))
    return execute_query(query, fetch_all=True)

def fetch_record_by_id(table_name, column_name, record_id):
    schema, table = table_name.split('.')
    query = sql.SQL("SELECT * FROM {}.{} WHERE {} = %s").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.Identifier(column_name)
    )
    return execute_query(query, (record_id,), fetch_one=True)

def format_result(record, fields):
    return {field: record[i] for i, field in enumerate(fields)}


def upsert_records(table_name, records, id_field, fields):
    schema, table = table_name.split('.')
    
    select_query = sql.SQL("SELECT {} FROM {}.{} WHERE name = %s").format(
        sql.Identifier(id_field),
        sql.Identifier(schema),
        sql.Identifier(table)
    )
    
    insert_query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}) RETURNING {}").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(', ').join(map(sql.Identifier, fields)),
        sql.SQL(', ').join([sql.Placeholder()] * len(fields)),
        sql.Identifier(id_field)
    )
    
    ids = []
    for record in records:
        existing_record = execute_query(select_query, (record['name'],), fetch_one=True)
        if existing_record:
            record_id = existing_record[0]
        else:
            values = [record[field] for field in fields]
            record_id = execute_insert_query(insert_query, values)
        ids.append(record_id)
    return ids

def manage_relations(post_id, relation_ids, relation_table, relation_id_field):
    schema, table = relation_table.split('.')
    select_query = sql.SQL("SELECT 1 FROM {}.{} WHERE post_id = %s AND {} = %s").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.Identifier(relation_id_field)
    )
    insert_query = sql.SQL("INSERT INTO {}.{} (post_id, {}) VALUES (%s, %s)").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.Identifier(relation_id_field)
    )
    for relation_id in relation_ids:
        exists = execute_query(select_query, (post_id, relation_id), fetch_one=True)
        if not exists:
            execute_query(insert_query, (post_id, relation_id))

def map_post_to_json(post):
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
    featured_image_data = get_featured_image(post[14])
    if featured_image_data:
        post_json['featured_image'] = featured_image_data
    return post_json

def get_tags_by_post_id(post_id: int):
    try:
        query = sql.SQL("SELECT * FROM blog.posts_tags_relation WHERE post_id = {}").format(sql.Literal(post_id))
        tags_array = execute_query(query, fetch_all=True)
        tags = [get_tags_by_id(row[1]) for row in tags_array]
        return {'status': 'success', 'data': tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_categories_by_post_id(post_id: int):
    try:
        query = sql.SQL("SELECT * FROM blog.posts_categories_relation WHERE post_id = {}").format(sql.Literal(post_id))
        categories_relational = execute_query(query, fetch_all=True)
        categories = [get_categories_by_id(row[1]) for row in categories_relational]
        return {'status': 'success', 'data': categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_posts_from_db():
    return fetch_all_records("blog.posts")

def get_post_by_id_from_db(post_id: int):
    return fetch_record_by_id("blog.posts", "post_id", post_id)

def get_categories_from_db():
    return fetch_all_records("blog.categories")

def get_tags_from_db():
    return fetch_all_records("blog.tags")

def get_featured_image_from_db():
    return fetch_all_records("blog.featured_image")

def get_categories_by_id(category_id: int):
    category = fetch_record_by_id("blog.categories", "category_id", category_id)
    if category:
        return format_result(category, ['category_id', 'name', 'slug'])
    raise HTTPException(status_code=404, detail="Categoria não encontrada")

def get_tags_by_id(tag_id: int):
    tag = fetch_record_by_id("blog.tags", "tag_id", tag_id)
    if tag:
        return format_result(tag, ['tag_id', 'name', 'slug'])
    raise HTTPException(status_code=404, detail="Tag não encontrada")

def get_featured_image(featured_image_id: int):
    featured_image = fetch_record_by_id("blog.featured_image", "featured_image", featured_image_id)
    if featured_image:
        return format_result(featured_image, ['featured_image', 'data', 'last_modified', 'last_modified_date', 'name', 'size', 'type', 'webkit_relative_path'])
    else: print('sem imagem, featured_image: ', featured_image_id)
    # raise HTTPException(status_code=404, detail="Imagem não encontrada")

def post_categories(categories: list):
    return upsert_records("blog.categories", categories, "category_id", ['name', 'slug'])

def post_tags(tags: list):
    return upsert_records("blog.tags", tags, "tag_id", ['name', 'slug'])

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

def insert_post_category_relations(post_id: int, category_ids: list):
    manage_relations(post_id, category_ids, "blog.posts_categories_relation", "category_id")

def insert_post_tag_relations(post_id: int, tag_ids: list):
    manage_relations(post_id, tag_ids, "blog.posts_tags_relation", "tag_id")

def update_post_relations(post_id: int, relation_ids: list, relation_table: str, relation_id_field: str):
    schema, table = relation_table.split('.')
    
    delete_query = sql.SQL("DELETE FROM {}.{} WHERE post_id = %s").format(
        sql.Identifier(schema), 
        sql.Identifier(table)
    )
    
    insert_query = sql.SQL("INSERT INTO {}.{} (post_id, {}) VALUES (%s, %s)").format(
        sql.Identifier(schema), 
        sql.Identifier(table), 
        sql.Identifier(relation_id_field)
    )
    
    execute_query(delete_query, (post_id,))
    
    for relation_id in relation_ids:
        execute_query(insert_query, (post_id, relation_id))

def update_post_category_relations(post_id: int, category_ids: list):
    update_post_relations(post_id, category_ids, "blog.posts_categories_relation", "category_id")

def update_post_tag_relations(post_id: int, tag_ids: list):
    update_post_relations(post_id, tag_ids, "blog.posts_tags_relation", "tag_id")

def patch_featured_image(featured_image: dict, featured_image_id: int):
    query = """
        UPDATE blog.featured_image 
        SET data = %s, last_modified = %s, last_modified_date = %s, name = %s, size = %s, type = %s, webkit_relative_path = %s
        WHERE featured_image = %s RETURNING featured_image
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
    return execute_insert_query(query, values)
