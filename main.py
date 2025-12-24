"""Главный файл приложения"""
import sys
from PyQt6.QtWidgets import QApplication, QDialog
from ui.login_dialog import LoginDialog
from ui.admin_window import AdminWindow
from ui.director_window import DirectorWindow
from ui.client_window import ClientWindow


def main():
    # Проверка подключения к БД
    print("Проверка подключения к БД...")
    try:
        from db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("USE autoservice")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if not tables:
            print("⚠ ВНИМАНИЕ: БД пуста!")
            print("Выполните SQL скрипт init_database.sql в MySQL для создания таблиц и данных")
            sys.exit(1)
        print(f"✓ БД подключена, найдено таблиц: {len(tables)}")
        conn.close()
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        print("Убедитесь, что MySQL запущен и БД создана")
        print("Выполните SQL скрипт init_database.sql в MySQL")
        sys.exit(1)
    
    # Создание приложения
    app = QApplication(sys.argv)
    print("✓ Приложение PyQt6 инициализировано")
    
    # Окно логина
    login_dialog = LoginDialog()
    print("✓ Окно логина создано")
    
    # Используем сигналы вместо exec() для избежания проблем на Windows
    def on_dialog_accepted():
        user_id = login_dialog.user_id
        role = login_dialog.role
        
        if not user_id or not role:
            print("Ошибка: не получены данные пользователя")
            app.quit()
            return
        
        print(f"✓ Авторизация успешна: пользователь {user_id}, роль {role}")
        
        # Скрываем диалог (не закрываем, чтобы не завершить приложение)
        login_dialog.hide()
        
        # Открываем окно в зависимости от роли
        try:
            if role == 'ADMIN':
                window = AdminWindow(user_id)
            elif role == 'DIRECTOR':
                window = DirectorWindow(user_id)
            elif role == 'CLIENT':
                window = ClientWindow(user_id)
            else:
                print(f"Неизвестная роль: {role}")
                app.quit()
                return
            
            window.show()
            window.raise_()  # Поднимаем окно на передний план
            window.activateWindow()  # Активируем окно
            print("✓ Главное окно показано и активировано")
            
            # Сохраняем ссылку на окно, чтобы оно не удалялось
            app.main_window = window
        except Exception as e:
            print(f"Ошибка при создании главного окна: {e}")
            import traceback
            traceback.print_exc()
            app.quit()
    
    def on_dialog_rejected():
        print("Авторизация отменена")
        app.quit()
    
    login_dialog.accepted.connect(on_dialog_accepted)
    login_dialog.rejected.connect(on_dialog_rejected)
    login_dialog.finished.connect(lambda code: on_dialog_rejected() if code == QDialog.DialogCode.Rejected else None)
    
    # Показываем диалог
    login_dialog.show()
    print("✓ Диалог показан")
    
    # Запускаем event loop
    try:
        app.exec()
    except Exception as e:
        print(f"Ошибка в event loop: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
