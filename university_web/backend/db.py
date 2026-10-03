"""
Central MySQL connection factory. Every module gets its database handle from here so
the connection settings live in one place (.env driven).
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Create a MySQL connection from the .env settings; pass database=False to connect to the server
# without selecting the residencehub schema.
def get_connection(database=True):
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "autocommit": False,
    }
    if database:
        config["database"] = os.getenv("DB_NAME", "residencehub")
    return mysql.connector.connect(**config)
