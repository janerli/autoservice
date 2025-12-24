"""Модуль для работы с подключением к БД"""
import pymysql
from pymysql.cursors import DictCursor
import os

# Параметры подключения (можно переопределить через переменные окружения)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'port': int(os.getenv('DB_PORT', '3309')),
    'database': os.getenv('DB_NAME', 'autoservice'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'autocommit': False
}


def get_connection(database=None):
    """Получить подключение к MySQL
    
    Args:
        database: имя БД (None для использования из конфига или подключения без БД)
    """
    config = DB_CONFIG.copy()
    db_name = database if database is not None else config.get('database')
    
    if db_name:
        # Подключаемся с указанием БД
        config['database'] = db_name
        conn = pymysql.connect(**config)
        # Явно выбираем БД после подключения (PyMySQL не всегда делает это автоматически)
        cursor = conn.cursor()
        cursor.execute(f"USE {db_name}")
        cursor.close()
    else:
        # Подключаемся без БД (для создания БД)
        config.pop('database', None)
        conn = pymysql.connect(**config)
    
    return conn

