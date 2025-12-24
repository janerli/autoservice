"""Окно директора"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QPushButton, QDateEdit, QLabel,
                             QDialog, QFormLayout, QLineEdit, QMessageBox, QGroupBox,
                             QDoubleSpinBox, QSpinBox, QComboBox, QDialogButtonBox)
from PyQt6.QtCore import QDate
from db import get_connection


class DirectorWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle('Директор - Автосервис')
        self.setGeometry(100, 100, 1200, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        tabs = QTabWidget()
        
        # Аналитика
        self.analytics_tab = self.create_analytics_tab()
        tabs.addTab(self.analytics_tab, 'Аналитика')
        
        # Прайс услуг
        self.services_tab = self.create_services_tab()
        tabs.addTab(self.services_tab, 'Прайс услуг')
        
        # Запчасти
        self.parts_tab = self.create_parts_tab()
        tabs.addTab(self.parts_tab, 'Запчасти')
        
        layout.addWidget(tabs)
    
    def create_analytics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Период
        period_group = QGroupBox('Период')
        period_layout = QHBoxLayout()
        
        period_layout.addWidget(QLabel('С:'))
        self.analytics_date_from = QDateEdit()
        self.analytics_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.analytics_date_from.setCalendarPopup(True)
        period_layout.addWidget(self.analytics_date_from)
        
        period_layout.addWidget(QLabel('По:'))
        self.analytics_date_to = QDateEdit()
        self.analytics_date_to.setDate(QDate.currentDate())
        self.analytics_date_to.setCalendarPopup(True)
        period_layout.addWidget(self.analytics_date_to)
        
        btn_calculate = QPushButton('Рассчитать')
        btn_calculate.clicked.connect(self.calculate_analytics)
        period_layout.addWidget(btn_calculate)
        
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # Показатели
        metrics_group = QGroupBox('Показатели')
        metrics_layout = QVBoxLayout()
        
        self.vehicles_count_label = QLabel('Количество обслуженных автомобилей: -')
        metrics_layout.addWidget(self.vehicles_count_label)
        
        self.revenue_label = QLabel('Выручка: -')
        metrics_layout.addWidget(self.revenue_label)
        
        self.avg_check_label = QLabel('Средний чек: -')
        metrics_layout.addWidget(self.avg_check_label)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Популярность услуг
        popular_group = QGroupBox('Популярность услуг')
        popular_layout = QVBoxLayout()
        
        self.popular_services_table = QTableWidget()
        self.popular_services_table.setColumnCount(3)
        self.popular_services_table.setHorizontalHeaderLabels(['Услуга', 'Количество', 'Сумма'])
        popular_layout.addWidget(self.popular_services_table)
        
        popular_group.setLayout(popular_layout)
        layout.addWidget(popular_group)
        
        return widget
    
    def create_services_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton('Добавить услугу')
        btn_add.clicked.connect(self.add_service)
        btn_layout.addWidget(btn_add)
        
        btn_edit = QPushButton('Редактировать')
        btn_edit.clicked.connect(self.edit_service)
        btn_layout.addWidget(btn_edit)
        
        layout.addLayout(btn_layout)
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(['ID', 'Категория', 'Название', 'Цена', 'Активна'])
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.services_table)
        
        self.load_services()
        return widget
    
    def create_parts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton('Добавить запчасть')
        btn_add.clicked.connect(self.add_part)
        btn_layout.addWidget(btn_add)
        
        btn_edit = QPushButton('Редактировать')
        btn_edit.clicked.connect(self.edit_part)
        btn_layout.addWidget(btn_edit)
        
        layout.addLayout(btn_layout)
        
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels(['ID', 'Название', 'Ед.изм.', 'Цена', 'Остаток', 'Активна'])
        self.parts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.parts_table)
        
        self.load_parts()
        return widget
    
    def calculate_analytics(self):
        date_from = self.analytics_date_from.date().toPyDate()
        date_to = self.analytics_date_to.date().toPyDate()
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Количество обслуженных автомобилей
            cursor.execute("""
                SELECT COUNT(DISTINCT vehicle_id) as cnt
                FROM work_orders
                WHERE status IN ('Выполнен', 'Выдан клиенту')
                  AND closed_at IS NOT NULL
                  AND DATE(closed_at) >= %s AND DATE(closed_at) <= %s
            """, (date_from, date_to))
            vehicles_count = cursor.fetchone()['cnt']
            self.vehicles_count_label.setText(f'Количество обслуженных автомобилей: {vehicles_count}')
            
            # Выручка
            cursor.execute("""
                SELECT COALESCE(SUM(
                  (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_services WHERE work_order_id = wo.work_order_id) +
                  (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_parts WHERE work_order_id = wo.work_order_id)
                ), 0) as revenue
                FROM work_orders wo
                WHERE wo.status IN ('Выполнен', 'Выдан клиенту')
                  AND wo.closed_at IS NOT NULL
                  AND DATE(wo.closed_at) >= %s AND DATE(wo.closed_at) <= %s
            """, (date_from, date_to))
            revenue = cursor.fetchone()['revenue']
            self.revenue_label.setText(f'Выручка: {revenue:.2f} руб.')
            
            # Средний чек (через процедуру)
            cursor.callproc('sp_avg_check', (date_from, date_to))
            result = cursor.fetchone()
            if result:
                avg_check = result['avg_check']
                self.avg_check_label.setText(f'Средний чек: {avg_check:.2f} руб.')
            
            # Популярность услуг
            cursor.execute("""
                SELECT s.name, SUM(wos.qty) as total_qty, SUM(wos.qty * wos.price_at_time) as total_sum
                FROM work_order_services wos
                JOIN services s ON wos.service_id = s.service_id
                JOIN work_orders wo ON wos.work_order_id = wo.work_order_id
                WHERE wo.status IN ('Выполнен', 'Выдан клиенту')
                  AND wo.closed_at IS NOT NULL
                  AND DATE(wo.closed_at) >= %s AND DATE(wo.closed_at) <= %s
                GROUP BY s.service_id, s.name
                ORDER BY total_qty DESC
                LIMIT 10
            """, (date_from, date_to))
            popular = cursor.fetchall()
            
            self.popular_services_table.setRowCount(len(popular))
            for i, row in enumerate(popular):
                self.popular_services_table.setItem(i, 0, QTableWidgetItem(row['name']))
                self.popular_services_table.setItem(i, 1, QTableWidgetItem(str(row['total_qty'])))
                self.popular_services_table.setItem(i, 2, QTableWidgetItem(f"{row['total_sum']:.2f}"))
        finally:
            conn.close()
    
    def load_services(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.service_id, sc.name as category, s.name, s.price, s.is_active
                FROM services s
                JOIN service_categories sc ON s.category_id = sc.category_id
                ORDER BY sc.name, s.name
            """)
            rows = cursor.fetchall()
            
            self.services_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.services_table.setItem(i, 0, QTableWidgetItem(str(row['service_id'])))
                self.services_table.setItem(i, 1, QTableWidgetItem(row['category']))
                self.services_table.setItem(i, 2, QTableWidgetItem(row['name']))
                self.services_table.setItem(i, 3, QTableWidgetItem(f"{row['price']:.2f}"))
                self.services_table.setItem(i, 4, QTableWidgetItem('Да' if row['is_active'] else 'Нет'))
        finally:
            conn.close()
    
    def add_service(self):
        dialog = ServiceDialog(self)
        if dialog.exec():
            self.load_services()
    
    def edit_service(self):
        row = self.services_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите услугу')
            return
        
        service_id = int(self.services_table.item(row, 0).text())
        dialog = ServiceDialog(self, service_id)
        if dialog.exec():
            self.load_services()
    
    def load_parts(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT part_id, name, unit, price, stock_qty, is_active FROM parts ORDER BY name")
            rows = cursor.fetchall()
            
            self.parts_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.parts_table.setItem(i, 0, QTableWidgetItem(str(row['part_id'])))
                self.parts_table.setItem(i, 1, QTableWidgetItem(row['name']))
                self.parts_table.setItem(i, 2, QTableWidgetItem(row['unit']))
                self.parts_table.setItem(i, 3, QTableWidgetItem(f"{row['price']:.2f}"))
                self.parts_table.setItem(i, 4, QTableWidgetItem(str(row['stock_qty'])))
                self.parts_table.setItem(i, 5, QTableWidgetItem('Да' if row['is_active'] else 'Нет'))
        finally:
            conn.close()
    
    def add_part(self):
        dialog = PartDialog(self)
        if dialog.exec():
            self.load_parts()
    
    def edit_part(self):
        row = self.parts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите запчасть')
            return
        
        part_id = int(self.parts_table.item(row, 0).text())
        dialog = PartDialog(self, part_id)
        if dialog.exec():
            self.load_parts()


class ServiceDialog(QDialog):
    def __init__(self, parent=None, service_id=None):
        super().__init__(parent)
        self.service_id = service_id
        self.setWindowTitle('Редактировать услугу' if service_id else 'Добавить услугу')
        layout = QFormLayout()
        
        self.category_combo = QComboBox()
        self.load_categories()
        layout.addRow('Категория:', self.category_combo)
        
        self.name = QLineEdit()
        layout.addRow('Название:', self.name)
        
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 999999.99)
        self.price.setDecimals(2)
        layout.addRow('Цена:', self.price)
        
        self.is_active = QComboBox()
        self.is_active.addItems(['Да', 'Нет'])
        layout.addRow('Активна:', self.is_active)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_service)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        if service_id:
            self.load_service()
    
    def load_categories(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT category_id, name FROM service_categories ORDER BY name")
            for row in cursor.fetchall():
                self.category_combo.addItem(row['name'], row['category_id'])
        finally:
            conn.close()
    
    def load_service(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT category_id, name, price, is_active FROM services WHERE service_id = %s", (self.service_id,))
            service = cursor.fetchone()
            
            if service:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == service['category_id']:
                        self.category_combo.setCurrentIndex(i)
                        break
                self.name.setText(service['name'])
                self.price.setValue(float(service['price']))
                self.is_active.setCurrentIndex(0 if service['is_active'] else 1)
        finally:
            conn.close()
    
    def save_service(self):
        if not self.name.text() or self.category_combo.currentIndex() < 0:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            category_id = self.category_combo.currentData()
            is_active = 1 if self.is_active.currentText() == 'Да' else 0
            
            if self.service_id:
                cursor.execute("""
                    UPDATE services
                    SET category_id = %s, name = %s, price = %s, is_active = %s
                    WHERE service_id = %s
                """, (category_id, self.name.text(), self.price.value(), is_active, self.service_id))
            else:
                cursor.execute("""
                    INSERT INTO services (category_id, name, price, is_active)
                    VALUES (%s, %s, %s, %s)
                """, (category_id, self.name.text(), self.price.value(), is_active))
            
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Услуга сохранена')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()


class PartDialog(QDialog):
    def __init__(self, parent=None, part_id=None):
        super().__init__(parent)
        self.part_id = part_id
        self.setWindowTitle('Редактировать запчасть' if part_id else 'Добавить запчасть')
        layout = QFormLayout()
        
        self.name = QLineEdit()
        layout.addRow('Название:', self.name)
        
        self.unit = QLineEdit()
        self.unit.setText('шт')
        layout.addRow('Единица измерения:', self.unit)
        
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 999999.99)
        self.price.setDecimals(2)
        layout.addRow('Цена:', self.price)
        
        self.stock_qty = QSpinBox()
        self.stock_qty.setRange(0, 999999)
        layout.addRow('Остаток:', self.stock_qty)
        
        self.is_active = QComboBox()
        self.is_active.addItems(['Да', 'Нет'])
        layout.addRow('Активна:', self.is_active)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_part)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        if part_id:
            self.load_part()
    
    def load_part(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, unit, price, stock_qty, is_active FROM parts WHERE part_id = %s", (self.part_id,))
            part = cursor.fetchone()
            
            if part:
                self.name.setText(part['name'])
                self.unit.setText(part['unit'])
                self.price.setValue(float(part['price']))
                self.stock_qty.setValue(part['stock_qty'])
                self.is_active.setCurrentIndex(0 if part['is_active'] else 1)
        finally:
            conn.close()
    
    def save_part(self):
        if not self.name.text():
            QMessageBox.warning(self, 'Ошибка', 'Заполните название')
            return
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            is_active = 1 if self.is_active.currentText() == 'Да' else 0
            
            if self.part_id:
                cursor.execute("""
                    UPDATE parts
                    SET name = %s, unit = %s, price = %s, stock_qty = %s, is_active = %s
                    WHERE part_id = %s
                """, (self.name.text(), self.unit.text(), self.price.value(),
                      self.stock_qty.value(), is_active, self.part_id))
            else:
                cursor.execute("""
                    INSERT INTO parts (name, unit, price, stock_qty, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                """, (self.name.text(), self.unit.text(), self.price.value(),
                      self.stock_qty.value(), is_active))
            
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Запчасть сохранена')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()

