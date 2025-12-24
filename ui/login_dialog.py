"""Окно авторизации"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from auth import authenticate


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация')
        self.setFixedSize(300, 150)
        self.user_id = None
        self.role = None
        
        layout = QVBoxLayout()
        
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText('Логин')
        layout.addWidget(QLabel('Логин:'))
        layout.addWidget(self.login_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText('Пароль')
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel('Пароль:'))
        layout.addWidget(self.password_edit)
        
        btn_login = QPushButton('Войти')
        btn_login.clicked.connect(self.on_login)
        layout.addWidget(btn_login)
        
        self.setLayout(layout)
        
        # Enter для входа
        self.password_edit.returnPressed.connect(self.on_login)
    
    def on_login(self):
        print("[LOGIN] Кнопка 'Войти' нажата")
        login = self.login_edit.text().strip()
        password = self.password_edit.text()
        
        print(f"[LOGIN] Введённые данные: login='{login}', password_length={len(password)}")
        
        if not login or not password:
            print("[LOGIN] ✗ Пустые поля")
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return
        
        print("[LOGIN] Вызов authenticate()...")
        try:
            result = authenticate(login, password)
            print(f"[LOGIN] Результат authenticate(): {result}")
            
            if result:
                self.user_id, self.role = result
                print(f"[LOGIN] ✓ Данные сохранены: user_id={self.user_id}, role={self.role}")
                print("[LOGIN] Вызов accept()...")
                self.accept()
                print("[LOGIN] ✓ accept() выполнен")
            else:
                print("[LOGIN] ✗ Авторизация не удалась")
                QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')
        except Exception as e:
            print(f"[LOGIN] ✗ Исключение при авторизации: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при авторизации: {e}')

