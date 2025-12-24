"""Модуль для применения миграций БД"""
import os
import re
from db import get_connection, DB_CONFIG


def get_migration_files():
    """Получить список файлов миграций в порядке применения"""
    migrations_dir = 'migrations'
    files = []
    for f in os.listdir(migrations_dir):
        if f.endswith('.sql'):
            # Извлекаем номер из имени файла (например, 001_...)
            match = re.match(r'(\d+)_', f)
            if match:
                num = int(match.group(1))
                files.append((num, f))
    files.sort(key=lambda x: x[0])
    return [filename for num, filename in files]


def get_applied_migrations(conn):
    """Получить список применённых миграций"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version FROM schema_migrations")
        return {row['version'] for row in cursor.fetchall()}
    except Exception:
        return set()
    finally:
        cursor.close()


def apply_migration(conn, filename):
    """Применить одну миграцию"""
    migrations_dir = 'migrations'
    filepath = os.path.join(migrations_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Обрабатываем DELIMITER (для процедур)
    # PyMySQL не поддерживает DELIMITER, поэтому обрабатываем вручную
    import re
    statements = []
    
    if 'DELIMITER' in sql.upper():
        # Убираем DELIMITER команды
        sql = re.sub(r'DELIMITER\s+\$\$', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'DELIMITER\s*;', '', sql, flags=re.IGNORECASE)
        
        # Ищем блоки CREATE PROCEDURE ... END$$
        # Паттерн: от CREATE PROCEDURE до END, затем возможные пробелы и $$
        # Используем жадный поиск до END, затем ищем $$
        proc_pattern = r'(CREATE\s+PROCEDURE.*?END)\s*\$\$'
        procedures = re.findall(proc_pattern, sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Убираем найденные процедуры из SQL (заменяем на пустую строку)
        sql_without_procs = re.sub(proc_pattern, '', sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Добавляем процедуры как отдельные запросы (без $$)
        for proc in procedures:
            proc = proc.strip()
            # Убираем лишние пробелы и переносы строк в конце
            proc = proc.rstrip()
            # Убираем многострочные комментарии /* */ из процедуры
            proc = re.sub(r'/\*.*?\*/', '', proc, flags=re.DOTALL)
            if proc:
                statements.append(proc)
        
        # Обрабатываем остальные запросы (DROP PROCEDURE и т.д.)
        for stmt in sql_without_procs.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                if not stmt.upper().startswith('USE '):
                    statements.append(stmt)
    else:
        # Обычная обработка - разбиваем по ;
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                if not stmt.upper().startswith('USE '):
                    statements.append(stmt)
    
    cursor = conn.cursor()
    try:
        # Убеждаемся, что БД выбрана (получаем имя БД из конфига)
        from db import DB_CONFIG
        db_name = DB_CONFIG.get('database', 'autoservice')
        try:
            cursor.execute(f"USE {db_name}")
        except Exception:
            # БД уже выбрана или не нужна для этого запроса
            pass
        
        # Выполняем все запросы
        for i, stmt in enumerate(statements):
            if stmt:
                try:
                    # Для процедур выводим больше информации
                    if 'CREATE PROCEDURE' in stmt.upper():
                        print(f"  Выполнение процедуры (длина: {len(stmt)} символов)...")
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"  Ошибка в запросе {i+1}/{len(statements)}: {stmt[:100]}...")
                    print(f"  Детали: {e}")
                    # Для процедур выводим больше контекста
                    if 'CREATE PROCEDURE' in stmt.upper():
                        lines = stmt.split('\n')
                        print(f"  Всего строк в процедуре: {len(lines)}")
                        if len(lines) > 20:
                            print(f"  Строки 20-25: {lines[19:25]}")
                    # Откатываем транзакцию при ошибке
                    conn.rollback()
                    raise
        
        # Записываем версию миграции только после успешного выполнения всех запросов
        try:
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (filename,)
            )
        except Exception as e:
            # Миграция уже записана - это нормально
            pass
        
        # Коммитим только если все запросы выполнились успешно
        conn.commit()
        print(f"✓ Применена миграция: {filename}")
    except Exception as e:
        conn.rollback()
        print(f"✗ Ошибка при применении {filename}: {e}")
        raise
    finally:
        cursor.close()


def run_migrations():
    """Запустить все неприменённые миграции"""
    # Сначала подключаемся без БД для создания её
    try:
        conn = get_connection(database=None)
    except Exception as e:
        print(f"Ошибка подключения к MySQL: {e}")
        print(f"Проверьте настройки подключения:")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  User: {DB_CONFIG['user']}")
        print(f"  Убедитесь, что MySQL запущен и доступен")
        raise
    
    try:
        files = get_migration_files()
        first_migration = files[0] if files else None
        
        # Применяем первую миграцию (создание БД) без проверки applied
        db_name = DB_CONFIG.get('database', 'autoservice')
        if first_migration == '001_schema_migrations.sql':
            try:
                # Сначала создаём БД
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_0900_ai_ci")
                conn.commit()
                cursor.close()
                print("✓ БД создана")
            except Exception as e:
                # Возможно БД уже создана, продолжаем
                print(f"Примечание при создании БД: {e}")
        
        conn.close()
        
        # Теперь подключаемся к созданной БД
        try:
            conn = get_connection()
            # Явно выбираем БД после подключения
            cursor = conn.cursor()
            cursor.execute(f"USE {db_name}")
            conn.commit()
            cursor.close()
            print(f"✓ Подключено к БД {db_name}")
        except Exception as e:
            print(f"Ошибка подключения к БД {db_name}: {e}")
            print("Убедитесь, что MySQL запущен и БД создана")
            raise
        
        # Проверяем, существует ли таблица schema_migrations, если нет - создаём
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM schema_migrations LIMIT 1")
        except Exception:
            # Таблицы нет, создаём её
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
            conn.commit()
            print("✓ Таблица schema_migrations создана")
        cursor.close()
        
        applied = get_applied_migrations(conn)
        
        # Применяем все миграции (проверяем applied для каждой)
        # Первую миграцию пропускаем, так как она уже применена выше
        for filename in files:
            if filename == first_migration:
                # Первая миграция уже применена, но проверим, записана ли она
                if filename not in applied:
                    # Записываем версию первой миграции
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            "INSERT INTO schema_migrations (version) VALUES (%s)",
                            (filename,)
                        )
                        conn.commit()
                    except Exception:
                        pass
                    finally:
                        cursor.close()
                continue
            
            if filename not in applied:
                print(f"Применение миграции: {filename}")
                try:
                    apply_migration(conn, filename)
                except Exception as e:
                    print(f"✗ Критическая ошибка при применении {filename}: {e}")
                    raise
            else:
                print(f"⊘ Пропущена (уже применена): {filename}")
        
        print(f"\nВсего миграций: {len(files)}, применено: {len(applied)}, новых: {len(files) - len(applied)}")
    finally:
        if 'conn' in locals():
            conn.close()

