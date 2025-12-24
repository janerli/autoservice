"""Окно клиента"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel, QDialog,
                             QFormLayout, QComboBox, QDateTimeEdit, QTextEdit, QMessageBox,
                             QGroupBox, QDialogButtonBox)
from PyQt6.QtCore import QDateTime
from db import get_connection
from auth import get_client_id_by_user_id


class ClientWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.client_id = get_client_id_by_user_id(user_id)
        self.setWindowTitle('Клиент - Автосервис')
        self.setGeometry(100, 100, 1000, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        tabs = QTabWidget()
        
        # Запись
        self.appointment_tab = self.create_appointment_tab()
        tabs.addTab(self.appointment_tab, 'Запись на обслуживание')
        
        # Мои заказы
        self.orders_tab = self.create_orders_tab()
        tabs.addTab(self.orders_tab, 'Мои заказы')
        
        # История
        self.history_tab = self.create_history_tab()
        tabs.addTab(self.history_tab, 'История обслуживания')
        
        layout.addWidget(tabs)
        
        if not self.client_id:
            QMessageBox.warning(self, 'Ошибка', 'Клиент не найден')
    
    def create_appointment_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_group = QGroupBox('Новая запись')
        form_layout = QFormLayout()
        
        self.vehicle_combo = QComboBox()
        self.load_vehicles()
        form_layout.addRow('Автомобиль:', self.vehicle_combo)
        
        self.scheduled_datetime = QDateTimeEdit()
        self.scheduled_datetime.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.scheduled_datetime.setCalendarPopup(True)
        form_layout.addRow('Дата и время:', self.scheduled_datetime)
        
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow('Категория работ:', self.category_combo)
        
        self.comment = QTextEdit()
        form_layout.addRow('Комментарий:', self.comment)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        btn_create = QPushButton('Создать запись')
        btn_create.clicked.connect(self.create_appointment)
        layout.addWidget(btn_create)
        
        layout.addStretch()
        return widget
    
    def create_orders_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel('Список ваших заказ-нарядов:')
        layout.addWidget(info)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(['№', 'Дата', 'Автомобиль', 'Статус', 'Сумма'])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.orders_table)
        
        btn_refresh = QPushButton('Обновить')
        btn_refresh.clicked.connect(self.load_orders)
        layout.addWidget(btn_refresh)
        
        self.load_orders()
        return widget
    
    def create_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel('История завершённых заказ-нарядов:')
        layout.addWidget(info)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(['№', 'Дата', 'Автомобиль', 'Статус', 'Сумма'])
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.doubleClicked.connect(self.show_history_details)
        layout.addWidget(self.history_table)
        
        btn_refresh = QPushButton('Обновить')
        btn_refresh.clicked.connect(self.load_history)
        layout.addWidget(btn_refresh)
        
        self.load_history()
        return widget
    
    def load_vehicles(self):
        if not self.client_id:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vehicle_id, make, model, year, vin
                FROM vehicles
                WHERE client_id = %s
            """, (self.client_id,))
            
            self.vehicle_combo.clear()
            for row in cursor.fetchall():
                text = f"{row['make']} {row['model']} ({row['year']}) - {row['vin']}"
                self.vehicle_combo.addItem(text, row['vehicle_id'])
        finally:
            conn.close()
    
    def load_categories(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT category_id, name FROM service_categories ORDER BY name")
            for row in cursor.fetchall():
                self.category_combo.addItem(row['name'], row['category_id'])
        finally:
            conn.close()
    
    def create_appointment(self):
        if not self.client_id:
            QMessageBox.warning(self, 'Ошибка', 'Клиент не найден')
            return
        
        if self.vehicle_combo.currentIndex() < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите автомобиль')
            return
        
        vehicle_id = self.vehicle_combo.currentData()
        category_id = self.category_combo.currentData()
        scheduled_at = self.scheduled_datetime.dateTime().toPyDateTime()
        comment = self.comment.toPlainText()
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointments (client_id, vehicle_id, category_id, scheduled_at, comment, status)
                VALUES (%s, %s, %s, %s, %s, 'Запланирована')
            """, (self.client_id, vehicle_id, category_id, scheduled_at, comment))
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Запись создана')
            self.comment.clear()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()
    
    def load_orders(self):
        if not self.client_id:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.work_order_id, wo.created_at, CONCAT(v.make, ' ', v.model) as vehicle,
                       wo.status,
                       (COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_services WHERE work_order_id = wo.work_order_id), 0) +
                        COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_parts WHERE work_order_id = wo.work_order_id), 0)) as total
                FROM work_orders wo
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                WHERE wo.client_id = %s
                ORDER BY wo.created_at DESC
            """, (self.client_id,))
            rows = cursor.fetchall()
            
            self.orders_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.orders_table.setItem(i, 0, QTableWidgetItem(str(row['work_order_id'])))
                self.orders_table.setItem(i, 1, QTableWidgetItem(str(row['created_at'])))
                self.orders_table.setItem(i, 2, QTableWidgetItem(row['vehicle']))
                self.orders_table.setItem(i, 3, QTableWidgetItem(row['status']))
                self.orders_table.setItem(i, 4, QTableWidgetItem(f"{row['total']:.2f}"))
        finally:
            conn.close()
    
    def load_history(self):
        if not self.client_id:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.work_order_id, wo.created_at, CONCAT(v.make, ' ', v.model) as vehicle,
                       wo.status,
                       (COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_services WHERE work_order_id = wo.work_order_id), 0) +
                        COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_parts WHERE work_order_id = wo.work_order_id), 0)) as total
                FROM work_orders wo
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                WHERE wo.client_id = %s
                  AND wo.status IN ('Выполнен', 'Выдан клиенту')
                ORDER BY wo.closed_at DESC
            """, (self.client_id,))
            rows = cursor.fetchall()
            
            self.history_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.history_table.setItem(i, 0, QTableWidgetItem(str(row['work_order_id'])))
                self.history_table.setItem(i, 1, QTableWidgetItem(str(row['created_at'])))
                self.history_table.setItem(i, 2, QTableWidgetItem(row['vehicle']))
                self.history_table.setItem(i, 3, QTableWidgetItem(row['status']))
                self.history_table.setItem(i, 4, QTableWidgetItem(f"{row['total']:.2f}"))
        finally:
            conn.close()
    
    def show_history_details(self):
        row = self.history_table.currentRow()
        if row < 0:
            return
        
        order_id = int(self.history_table.item(row, 0).text())
        dialog = HistoryDetailsDialog(order_id, self)
        dialog.exec()


class HistoryDetailsDialog(QDialog):
    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle(f'Заказ-наряд №{order_id}')
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout()
        
        from PyQt6.QtWidgets import QTextBrowser
        
        browser = QTextBrowser()
        html = self.generate_html()
        browser.setHtml(html)
        layout.addWidget(browser)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def generate_html(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.*, CONCAT(v.make, ' ', v.model, ' ', v.year) as vehicle
                FROM work_orders wo
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                WHERE wo.work_order_id = %s
            """, (self.order_id,))
            order = cursor.fetchone()
            
            cursor.execute("""
                SELECT s.name, wos.qty, wos.price_at_time
                FROM work_order_services wos
                JOIN services s ON wos.service_id = s.service_id
                WHERE wos.work_order_id = %s
            """, (self.order_id,))
            services = cursor.fetchall()
            
            cursor.execute("""
                SELECT p.name, wop.qty, wop.price_at_time
                FROM work_order_parts wop
                JOIN parts p ON wop.part_id = p.part_id
                WHERE wop.work_order_id = %s
            """, (self.order_id,))
            parts = cursor.fetchall()
            
            html = f"""
            <html><head><meta charset="utf-8"></head><body>
            <h2>Заказ-наряд №{order['work_order_id']}</h2>
            <p><b>Дата:</b> {order['created_at']}</p>
            <p><b>Автомобиль:</b> {order['vehicle']}</p>
            <p><b>Статус:</b> {order['status']}</p>
            <h3>Работы:</h3>
            <table border="1" cellpadding="5">
            <tr><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr>
            """
            total = 0
            for s in services:
                summa = s['qty'] * s['price_at_time']
                total += summa
                html += f"<tr><td>{s['name']}</td><td>{s['qty']}</td><td>{s['price_at_time']:.2f}</td><td>{summa:.2f}</td></tr>"
            
            html += "</table><h3>Запчасти:</h3><table border='1' cellpadding='5'><tr><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr>"
            for p in parts:
                summa = p['qty'] * p['price_at_time']
                total += summa
                html += f"<tr><td>{p['name']}</td><td>{p['qty']}</td><td>{p['price_at_time']:.2f}</td><td>{summa:.2f}</td></tr>"
            
            html += f"</table><h3>ИТОГО: {total:.2f} руб.</h3></body></html>"
            return html
        finally:
            conn.close()

