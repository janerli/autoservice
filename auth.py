"""Модуль для авторизации пользователей"""
import hashlib
from db import get_connection


def hash_password(password):
    """Хэширование пароля (SHA256)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def authenticate(login, password):
    """Проверка логина и пароля, возвращает (user_id, role) или None"""
    print(f"[AUTH] Попытка авторизации: login={login}")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Явно выбираем БД
        cursor.execute("USE autoservice")
        password_hash = hash_password(password)
        print(f"[AUTH] Пароль захеширован, длина хэша: {len(password_hash)}")
        
        cursor.execute("""
            SELECT user_id, role 
            FROM users 
            WHERE login = %s AND password_hash = %s AND is_active = 1
        """, (login, password_hash))
        result = cursor.fetchone()
        
        if result:
            print(f"[AUTH] ✓ Авторизация успешна: user_id={result['user_id']}, role={result['role']}")
            return result['user_id'], result['role']
        else:
            print(f"[AUTH] ✗ Авторизация не удалась: пользователь не найден или неактивен")
            # Проверяем, существует ли пользователь вообще
            cursor.execute("SELECT user_id, role, is_active FROM users WHERE login = %s", (login,))
            user_check = cursor.fetchone()
            if user_check:
                print(f"[AUTH] Пользователь найден, но: is_active={user_check['is_active']}, роль={user_check['role']}")
            else:
                print(f"[AUTH] Пользователь с логином '{login}' не найден в БД")
            return None
    except Exception as e:
        print(f"[AUTH] ✗ Ошибка при авторизации: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()


def get_user_info(user_id):
    """Получить информацию о пользователе"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("USE autoservice")
        cursor.execute("""
            SELECT user_id, login, role 
            FROM users 
            WHERE user_id = %s
        """, (user_id,))
        return cursor.fetchone()
    finally:
        conn.close()


def get_client_id_by_user_id(user_id):
    """Получить client_id по user_id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("USE autoservice")
        cursor.execute("""
            SELECT client_id 
            FROM clients 
            WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        return result['client_id'] if result else None
    finally:
        conn.close()

