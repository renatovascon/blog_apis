from pathlib import Path, os
import psycopg2
from fastapi import  HTTPException
from dotenv import load_dotenv

load_dotenv()

db_connection_tokapi = {
    'user': str(os.getenv('USER_CONECTION_TOKAPI')),
    'password': str(os.getenv('PASSWORD_CONECTION_TOKAPI')),
    'host': str(os.getenv('HOST_CONECTION_TOKAPI')),
    'port': str(os.getenv('PORT_CONECTION_TOKAPI')),
    'database': str(os.getenv('DATABASE_CONECTION_TOKAPI'))
}
def get_connection():
    try:
        conn = psycopg2.connect(**db_connection_tokapi)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
