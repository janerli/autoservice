"""Окно администратора/приёмщика"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QDateEdit,
                             QLabel, QDialog, QFormLayout, QLineEdit, QTextEdit, QMessageBox,
                             QGroupBox, QListWidget, QListWidgetItem, QSpinBox, QDateTimeEdit,
                             QTextBrowser, QDialogButtonBox, QFileDialog)
from PyQt6.QtCore import QDate, Qt, QDateTime
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument
from db import get_connection
from datetime import datetime, timedelta


class AdminWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle('Администратор - Автосервис')
        self.setGeometry(100, 100, 1200, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        tabs = QTabWidget()
        
        # Вкладка: Заказ-наряды
        self.orders_tab = self.create_orders_tab()
        tabs.addTab(self.orders_tab, 'Заказ-наряды')
        
        # Вкладка: Клиенты
        self.clients_tab = self.create_clients_tab()
        tabs.addTab(self.clients_tab, 'Клиенты')
        
        # Вкладка: Авто
        self.vehicles_tab = self.create_vehicles_tab()
        tabs.addTab(self.vehicles_tab, 'Автомобили')
        
        # Вкладка: Документы
        self.documents_tab = self.create_documents_tab()
        tabs.addTab(self.documents_tab, 'Документы')
        
        layout.addWidget(tabs)
        self.load_orders()
    
    def create_orders_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Фильтры
        filter_group = QGroupBox('Фильтры')
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel('Статус:'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Все', 'Ожидает', 'В работе', 'Ожидает запчасти',
                                    'Ожидает согласования', 'Выполнен', 'Выдан клиенту', 'Отменён'])
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel('Дата с:'))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel('Дата по:'))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filter_layout.addWidget(self.date_to)
        
        btn_filter = QPushButton('Фильтровать')
        btn_filter.clicked.connect(self.load_orders)
        filter_layout.addWidget(btn_filter)
        
        btn_show_all = QPushButton('Показать все')
        btn_show_all.clicked.connect(self.show_all_orders)
        filter_layout.addWidget(btn_show_all)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Таблица заказ-нарядов
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels(['№', 'Дата', 'Клиент', 'Авто', 'Статус', 'Механик', 'Сумма'])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.doubleClicked.connect(self.open_order)
        layout.addWidget(self.orders_table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_create = QPushButton('Создать заказ-наряд')
        btn_create.clicked.connect(self.create_order)
        btn_layout.addWidget(btn_create)
        
        btn_open = QPushButton('Открыть')
        btn_open.clicked.connect(self.open_order)
        btn_layout.addWidget(btn_open)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_clients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_create = QPushButton('Добавить клиента')
        btn_create.clicked.connect(self.create_client)
        layout.addWidget(btn_create)
        
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Телефон', 'Email'])
        layout.addWidget(self.clients_table)
        
        self.load_clients()
        return widget
    
    def create_vehicles_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.vehicles_table = QTableWidget()
        self.vehicles_table.setColumnCount(6)
        self.vehicles_table.setHorizontalHeaderLabels(['ID', 'Клиент', 'Марка', 'Модель', 'Год', 'VIN'])
        layout.addWidget(self.vehicles_table)
        
        self.load_vehicles()
        return widget
    
    def create_documents_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel('Выберите заказ-наряд на вкладке "Заказ-наряды" и нажмите "Открыть" для формирования документов')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        return widget
    
    def load_orders(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            status = self.status_filter.currentText()
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().toPyDate()
            
            query = """
                SELECT wo.work_order_id, wo.created_at, c.full_name, 
                       CONCAT(v.make, ' ', v.model) as vehicle,
                       wo.status, COALESCE(m.full_name, 'Не назначен') as mechanic,
                       (COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_services WHERE work_order_id = wo.work_order_id), 0) +
                        COALESCE((SELECT SUM(qty * price_at_time) FROM work_order_parts WHERE work_order_id = wo.work_order_id), 0)) as total
                FROM work_orders wo
                JOIN clients c ON wo.client_id = c.client_id
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                LEFT JOIN mechanics m ON wo.mechanic_id = m.mechanic_id
                WHERE 1=1
            """
            params = []
            
            if status != 'Все':
                query += " AND wo.status = %s"
                params.append(status)
            
            query += " AND DATE(wo.created_at) >= %s AND DATE(wo.created_at) <= %s"
            params.extend([date_from, date_to])
            
            query += " ORDER BY wo.created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.orders_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.orders_table.setItem(i, 0, QTableWidgetItem(str(row['work_order_id'])))
                self.orders_table.setItem(i, 1, QTableWidgetItem(str(row['created_at'])))
                self.orders_table.setItem(i, 2, QTableWidgetItem(row['full_name']))
                self.orders_table.setItem(i, 3, QTableWidgetItem(row['vehicle']))
                self.orders_table.setItem(i, 4, QTableWidgetItem(row['status']))
                self.orders_table.setItem(i, 5, QTableWidgetItem(row['mechanic']))
                self.orders_table.setItem(i, 6, QTableWidgetItem(f"{row['total']:.2f}"))
        finally:
            conn.close()
    
    def show_all_orders(self):
        self.status_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_to.setDate(QDate.currentDate().addDays(1))
        self.load_orders()
    
    def create_order(self):
        dialog = CreateOrderDialog(self)
        if dialog.exec():
            self.load_orders()
    
    def open_order(self):
        row = self.orders_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите заказ-наряд')
            return
        
        order_id = int(self.orders_table.item(row, 0).text())
        dialog = OrderDetailsDialog(order_id, self)
        if dialog.exec():
            self.load_orders()
    
    def load_clients(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT client_id, full_name, phone, email FROM clients ORDER BY full_name")
            rows = cursor.fetchall()
            
            self.clients_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.clients_table.setItem(i, 0, QTableWidgetItem(str(row['client_id'])))
                self.clients_table.setItem(i, 1, QTableWidgetItem(row['full_name']))
                self.clients_table.setItem(i, 2, QTableWidgetItem(row['phone']))
                self.clients_table.setItem(i, 3, QTableWidgetItem(row['email'] or ''))
        finally:
            conn.close()
    
    def create_client(self):
        dialog = CreateClientDialog(self)
        if dialog.exec():
            self.load_clients()
    
    def load_vehicles(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.vehicle_id, c.full_name, v.make, v.model, v.year, v.vin
                FROM vehicles v
                JOIN clients c ON v.client_id = c.client_id
                ORDER BY v.vehicle_id
            """)
            rows = cursor.fetchall()
            
            self.vehicles_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.vehicles_table.setItem(i, 0, QTableWidgetItem(str(row['vehicle_id'])))
                self.vehicles_table.setItem(i, 1, QTableWidgetItem(row['full_name']))
                self.vehicles_table.setItem(i, 2, QTableWidgetItem(row['make']))
                self.vehicles_table.setItem(i, 3, QTableWidgetItem(row['model']))
                self.vehicles_table.setItem(i, 4, QTableWidgetItem(str(row['year'])))
                self.vehicles_table.setItem(i, 5, QTableWidgetItem(row['vin']))
        finally:
            conn.close()


class CreateOrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Создать заказ-наряд')
        self.setMinimumSize(600, 500)
        self.client_id = None
        self.vehicle_id = None
        
        layout = QVBoxLayout()
        
        # Клиент
        client_group = QGroupBox('Клиент')
        client_layout = QVBoxLayout()
        
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText('Поиск по ФИО или телефону...')
        self.client_search.textChanged.connect(self.search_clients)
        client_layout.addWidget(self.client_search)
        
        self.clients_list = QListWidget()
        self.clients_list.itemDoubleClicked.connect(self.select_client)
        client_layout.addWidget(self.clients_list)
        
        btn_new_client = QPushButton('Новый клиент')
        btn_new_client.clicked.connect(self.create_new_client)
        client_layout.addWidget(btn_new_client)
        
        client_group.setLayout(client_layout)
        layout.addWidget(client_group)
        
        # Автомобиль
        vehicle_group = QGroupBox('Автомобиль')
        vehicle_layout = QVBoxLayout()
        
        self.vehicles_list = QListWidget()
        self.vehicles_list.itemDoubleClicked.connect(self.select_vehicle)
        vehicle_layout.addWidget(self.vehicles_list)
        
        btn_new_vehicle = QPushButton('Добавить авто')
        btn_new_vehicle.clicked.connect(self.create_new_vehicle)
        vehicle_layout.addWidget(btn_new_vehicle)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Работы
        services_group = QGroupBox('Работы')
        services_layout = QVBoxLayout()
        
        self.services_list = QListWidget()
        self.load_services()
        services_layout.addWidget(self.services_list)
        
        btn_add_service = QPushButton('Добавить услугу')
        btn_add_service.clicked.connect(self.add_service)
        services_layout.addWidget(btn_add_service)
        
        self.selected_services = QListWidget()
        services_layout.addWidget(QLabel('Выбранные услуги:'))
        services_layout.addWidget(self.selected_services)
        
        services_group.setLayout(services_layout)
        layout.addWidget(services_group)
        
        # Назначение
        assign_group = QGroupBox('Назначение')
        assign_layout = QFormLayout()
        
        self.mechanic_combo = QComboBox()
        self.load_mechanics()
        assign_layout.addRow('Механик:', self.mechanic_combo)
        
        self.ready_date = QDateTimeEdit()
        self.ready_date.setDateTime(QDateTime.currentDateTime().addDays(1))
        assign_layout.addRow('Ориентировочная дата готовности:', self.ready_date)
        
        self.complaint = QTextEdit()
        assign_layout.addRow('Жалоба/Описание:', self.complaint)
        
        assign_group.setLayout(assign_layout)
        layout.addWidget(assign_group)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_order)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.selected_services_data = []
    
    def search_clients(self):
        text = self.client_search.text().strip()
        conn = get_connection()
        try:
            cursor = conn.cursor()
            if text:
                cursor.execute("""
                    SELECT client_id, full_name, phone 
                    FROM clients 
                    WHERE full_name LIKE %s OR phone LIKE %s
                    LIMIT 20
                """, (f'%{text}%', f'%{text}%'))
            else:
                cursor.execute("SELECT client_id, full_name, phone FROM clients LIMIT 20")
            
            self.clients_list.clear()
            for row in cursor.fetchall():
                item = QListWidgetItem(f"{row['full_name']} ({row['phone']})")
                item.setData(Qt.ItemDataRole.UserRole, row['client_id'])
                self.clients_list.addItem(item)
        finally:
            conn.close()
    
    def select_client(self, item):
        self.client_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_vehicles()
    
    def load_vehicles(self):
        if not self.client_id:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vehicle_id, make, model, year, vin, plate_number
                FROM vehicles
                WHERE client_id = %s
            """, (self.client_id,))
            
            self.vehicles_list.clear()
            for row in cursor.fetchall():
                item = QListWidgetItem(f"{row['make']} {row['model']} ({row['year']}) - {row['vin']}")
                item.setData(Qt.ItemDataRole.UserRole, row['vehicle_id'])
                self.vehicles_list.addItem(item)
        finally:
            conn.close()
    
    def select_vehicle(self, item):
        self.vehicle_id = item.data(Qt.ItemDataRole.UserRole)
    
    def create_new_client(self):
        dialog = CreateClientDialog(self)
        if dialog.exec():
            self.search_clients()
    
    def create_new_vehicle(self):
        if not self.client_id:
            QMessageBox.warning(self, 'Ошибка', 'Сначала выберите клиента')
            return
        dialog = CreateVehicleDialog(self.client_id, self)
        if dialog.exec():
            self.load_vehicles()
    
    def load_services(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.service_id, sc.name as category, s.name, s.price
                FROM services s
                JOIN service_categories sc ON s.category_id = sc.category_id
                WHERE s.is_active = 1
                ORDER BY sc.name, s.name
            """)
            
            self.services_list.clear()
            for row in cursor.fetchall():
                item = QListWidgetItem(f"[{row['category']}] {row['name']} - {row['price']:.2f} руб.")
                item.setData(Qt.ItemDataRole.UserRole, row)
                self.services_list.addItem(item)
        finally:
            conn.close()
    
    def add_service(self):
        item = self.services_list.currentItem()
        if not item:
            return
        service_data = item.data(Qt.ItemDataRole.UserRole)
        
        # Проверяем, не добавлена ли уже
        for existing in self.selected_services_data:
            if existing['service_id'] == service_data['service_id']:
                QMessageBox.information(self, 'Информация', 'Услуга уже добавлена')
                return
        
        self.selected_services_data.append(service_data)
        list_item = QListWidgetItem(f"{service_data['name']} - {service_data['price']:.2f} руб.")
        self.selected_services.addItem(list_item)
    
    def load_mechanics(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT mechanic_id, full_name FROM mechanics WHERE is_active = 1")
            self.mechanic_combo.addItem('Не назначен', None)
            for row in cursor.fetchall():
                self.mechanic_combo.addItem(row['full_name'], row['mechanic_id'])
        finally:
            conn.close()
    
    def save_order(self):
        if not self.client_id or not self.vehicle_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите клиента и автомобиль')
            return
        
        if not self.selected_services_data:
            QMessageBox.warning(self, 'Ошибка', 'Добавьте хотя бы одну услугу')
            return
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            mechanic_id = self.mechanic_combo.currentData()
            ready_at = self.ready_date.dateTime().toPyDateTime()
            complaint = self.complaint.toPlainText()
            
            cursor.execute("""
                INSERT INTO work_orders (client_id, vehicle_id, mechanic_id, complaint, estimated_ready_at, status)
                VALUES (%s, %s, %s, %s, %s, 'Ожидает')
            """, (self.client_id, self.vehicle_id, mechanic_id, complaint, ready_at))
            
            order_id = cursor.lastrowid
            
            for service in self.selected_services_data:
                cursor.execute("""
                    INSERT INTO work_order_services (work_order_id, service_id, qty, price_at_time)
                    VALUES (%s, %s, 1, %s)
                """, (order_id, service['service_id'], service['price']))
            
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Заказ-наряд создан')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании: {e}')
        finally:
            conn.close()


class CreateClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Новый клиент')
        layout = QFormLayout()
        
        self.fio = QLineEdit()
        layout.addRow('ФИО:', self.fio)
        
        self.phone = QLineEdit()
        layout.addRow('Телефон:', self.phone)
        
        self.email = QLineEdit()
        layout.addRow('Email:', self.email)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_client)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def save_client(self):
        if not self.fio.text() or not self.phone.text():
            QMessageBox.warning(self, 'Ошибка', 'Заполните ФИО и телефон')
            return
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (full_name, phone, email)
                VALUES (%s, %s, %s)
            """, (self.fio.text(), self.phone.text(), self.email.text() or None))
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Клиент добавлен')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()


class CreateVehicleDialog(QDialog):
    def __init__(self, client_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle('Добавить автомобиль')
        layout = QFormLayout()
        
        self.make = QLineEdit()
        layout.addRow('Марка:', self.make)
        
        self.model = QLineEdit()
        layout.addRow('Модель:', self.model)
        
        self.year = QSpinBox()
        self.year.setRange(1900, 2100)
        self.year.setValue(2020)
        layout.addRow('Год:', self.year)
        
        self.vin = QLineEdit()
        layout.addRow('VIN:', self.vin)
        
        self.plate = QLineEdit()
        layout.addRow('Госномер:', self.plate)
        
        self.mileage = QSpinBox()
        self.mileage.setRange(0, 9999999)
        layout.addRow('Пробег (км):', self.mileage)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_vehicle)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def save_vehicle(self):
        if not all([self.make.text(), self.model.text(), self.vin.text(), self.plate.text()]):
            QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля')
            return
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicles (client_id, make, model, year, vin, plate_number, mileage_km)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.client_id, self.make.text(), self.model.text(), self.year.value(),
                  self.vin.text(), self.plate.text(), self.mileage.value()))
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Автомобиль добавлен')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()


class OrderDetailsDialog(QDialog):
    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle(f'Заказ-наряд №{order_id}')
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        # Основное
        main_tab = QWidget()
        main_layout = QFormLayout()
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Ожидает', 'В работе', 'Ожидает запчасти',
                                   'Ожидает согласования', 'Выполнен', 'Выдан клиенту', 'Отменён'])
        main_layout.addRow('Статус:', self.status_combo)
        
        self.mechanic_combo = QComboBox()
        main_layout.addRow('Механик:', self.mechanic_combo)
        
        self.complaint = QTextEdit()
        main_layout.addRow('Жалоба:', self.complaint)
        
        self.diagnostics = QTextEdit()
        main_layout.addRow('Результат диагностики:', self.diagnostics)
        
        self.total_label = QLabel('0.00')
        main_layout.addRow('Итоговая стоимость:', self.total_label)
        
        main_tab.setLayout(main_layout)
        tabs.addTab(main_tab, 'Основное')
        
        # Услуги
        services_tab = QWidget()
        services_layout = QVBoxLayout()
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(['Услуга', 'Кол-во', 'Цена', 'Сумма'])
        services_layout.addWidget(self.services_table)
        
        btn_add_service = QPushButton('Добавить услугу')
        btn_add_service.clicked.connect(self.add_service)
        services_layout.addWidget(btn_add_service)
        
        btn_remove_service = QPushButton('Удалить услугу')
        btn_remove_service.clicked.connect(self.remove_service)
        services_layout.addWidget(btn_remove_service)
        
        services_tab.setLayout(services_layout)
        tabs.addTab(services_tab, 'Услуги')
        
        # Запчасти
        parts_tab = QWidget()
        parts_layout = QVBoxLayout()
        
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(4)
        self.parts_table.setHorizontalHeaderLabels(['Запчасть', 'Кол-во', 'Цена', 'Сумма'])
        parts_layout.addWidget(self.parts_table)
        
        btn_add_part = QPushButton('Добавить запчасть')
        btn_add_part.clicked.connect(self.add_part)
        parts_layout.addWidget(btn_add_part)
        
        btn_remove_part = QPushButton('Удалить запчасть')
        btn_remove_part.clicked.connect(self.remove_part)
        parts_layout.addWidget(btn_remove_part)
        
        parts_tab.setLayout(parts_layout)
        tabs.addTab(parts_tab, 'Запчасти')
        
        layout.addWidget(tabs)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_save = QPushButton('Сохранить')
        btn_save.clicked.connect(self.save_order)
        btn_layout.addWidget(btn_save)
        
        btn_document = QPushButton('Сформировать заказ-наряд')
        btn_document.clicked.connect(self.generate_document)
        btn_layout.addWidget(btn_document)
        
        btn_act = QPushButton('Акт приёма-передачи')
        btn_act.clicked.connect(self.generate_act)
        btn_layout.addWidget(btn_act)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_order()
        self.load_mechanics()
    
    def load_order(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.*, c.full_name, CONCAT(v.make, ' ', v.model) as vehicle
                FROM work_orders wo
                JOIN clients c ON wo.client_id = c.client_id
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                WHERE wo.work_order_id = %s
            """, (self.order_id,))
            order = cursor.fetchone()
            
            if order:
                idx = self.status_combo.findText(order['status'])
                if idx >= 0:
                    self.status_combo.setCurrentIndex(idx)
                self.complaint.setPlainText(order['complaint'] or '')
                self.diagnostics.setPlainText(order['diagnostics_result'] or '')
            
            # Услуги
            cursor.execute("""
                SELECT wos.*, s.name
                FROM work_order_services wos
                JOIN services s ON wos.service_id = s.service_id
                WHERE wos.work_order_id = %s
            """, (self.order_id,))
            services = cursor.fetchall()
            
            self.services_table.setRowCount(len(services))
            for i, s in enumerate(services):
                self.services_table.setItem(i, 0, QTableWidgetItem(s['name']))
                self.services_table.setItem(i, 1, QTableWidgetItem(str(s['qty'])))
                self.services_table.setItem(i, 2, QTableWidgetItem(f"{s['price_at_time']:.2f}"))
                self.services_table.setItem(i, 3, QTableWidgetItem(f"{s['qty'] * s['price_at_time']:.2f}"))
                self.services_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, s['id'])
            
            # Запчасти
            cursor.execute("""
                SELECT wop.*, p.name
                FROM work_order_parts wop
                JOIN parts p ON wop.part_id = p.part_id
                WHERE wop.work_order_id = %s
            """, (self.order_id,))
            parts = cursor.fetchall()
            
            self.parts_table.setRowCount(len(parts))
            for i, p in enumerate(parts):
                self.parts_table.setItem(i, 0, QTableWidgetItem(p['name']))
                self.parts_table.setItem(i, 1, QTableWidgetItem(str(p['qty'])))
                self.parts_table.setItem(i, 2, QTableWidgetItem(f"{p['price_at_time']:.2f}"))
                self.parts_table.setItem(i, 3, QTableWidgetItem(f"{p['qty'] * p['price_at_time']:.2f}"))
                self.parts_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, p['id'])
            
            self.calculate_total()
        finally:
            conn.close()
    
    def load_mechanics(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT mechanic_id, full_name FROM mechanics WHERE is_active = 1")
            self.mechanic_combo.addItem('Не назначен', None)
            for row in cursor.fetchall():
                self.mechanic_combo.addItem(row['full_name'], row['mechanic_id'])
            
            # Устанавливаем текущего механика
            cursor.execute("SELECT mechanic_id FROM work_orders WHERE work_order_id = %s", (self.order_id,))
            result = cursor.fetchone()
            if result and result['mechanic_id']:
                for i in range(self.mechanic_combo.count()):
                    if self.mechanic_combo.itemData(i) == result['mechanic_id']:
                        self.mechanic_combo.setCurrentIndex(i)
                        break
        finally:
            conn.close()
    
    def calculate_total(self):
        total = 0.0
        for i in range(self.services_table.rowCount()):
            total += float(self.services_table.item(i, 3).text())
        for i in range(self.parts_table.rowCount()):
            total += float(self.parts_table.item(i, 3).text())
        self.total_label.setText(f"{total:.2f} руб.")
    
    def add_service(self):
        dialog = SelectServiceDialog(self)
        if dialog.exec():
            service_id, qty = dialog.get_selected()
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT service_id, name, price FROM services WHERE service_id = %s", (service_id,))
                service = cursor.fetchone()
                
                cursor.execute("""
                    INSERT INTO work_order_services (work_order_id, service_id, qty, price_at_time)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE qty = qty + %s
                """, (self.order_id, service_id, qty, service['price'], qty))
                conn.commit()
                self.load_order()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
            finally:
                conn.close()
    
    def remove_service(self):
        row = self.services_table.currentRow()
        if row < 0:
            return
        wos_id = self.services_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_order_services WHERE id = %s", (wos_id,))
            conn.commit()
            self.load_order()
        finally:
            conn.close()
    
    def add_part(self):
        dialog = SelectPartDialog(self)
        if dialog.exec():
            part_id, qty = dialog.get_selected()
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT part_id, name, price FROM parts WHERE part_id = %s", (part_id,))
                part = cursor.fetchone()
                
                cursor.execute("""
                    INSERT INTO work_order_parts (work_order_id, part_id, qty, price_at_time)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE qty = qty + %s
                """, (self.order_id, part_id, qty, part['price'], qty))
                conn.commit()
                self.load_order()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
            finally:
                conn.close()
    
    def remove_part(self):
        row = self.parts_table.currentRow()
        if row < 0:
            return
        wop_id = self.parts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_order_parts WHERE id = %s", (wop_id,))
            conn.commit()
            self.load_order()
        finally:
            conn.close()
    
    def save_order(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            mechanic_id = self.mechanic_combo.currentData()
            status = self.status_combo.currentText()
            
            if status in ['Выполнен', 'Выдан клиенту']:
                closed_at = datetime.now()
            else:
                closed_at = None
            
            cursor.execute("""
                UPDATE work_orders
                SET status = %s, mechanic_id = %s, complaint = %s, diagnostics_result = %s, closed_at = %s
                WHERE work_order_id = %s
            """, (status, mechanic_id, self.complaint.toPlainText(),
                  self.diagnostics.toPlainText(), closed_at, self.order_id))
            conn.commit()
            QMessageBox.information(self, 'Успех', 'Изменения сохранены')
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {e}')
        finally:
            conn.close()
    
    def generate_document(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.*, c.full_name, c.phone, c.email,
                       CONCAT(v.make, ' ', v.model, ' ', v.year) as vehicle, v.vin, v.plate_number
                FROM work_orders wo
                JOIN clients c ON wo.client_id = c.client_id
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
            <html>
            <head><meta charset="utf-8"></head>
            <body>
            <h1>ЗАКАЗ-НАРЯД №{order['work_order_id']}</h1>
            <p><b>Дата:</b> {order['created_at']}</p>
            <p><b>Клиент:</b> {order['full_name']}, тел. {order['phone']}</p>
            <p><b>Автомобиль:</b> {order['vehicle']}, VIN: {order['vin']}, Гос.номер: {order['plate_number']}</p>
            <p><b>Жалоба:</b> {order['complaint'] or ''}</p>
            <h2>Работы:</h2>
            <table border="1" cellpadding="5">
            <tr><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr>
            """
            total = 0
            for s in services:
                summa = s['qty'] * s['price_at_time']
                total += summa
                html += f"<tr><td>{s['name']}</td><td>{s['qty']}</td><td>{s['price_at_time']:.2f}</td><td>{summa:.2f}</td></tr>"
            
            html += "</table><h2>Запчасти:</h2><table border='1' cellpadding='5'><tr><th>Наименование</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr>"
            for p in parts:
                summa = p['qty'] * p['price_at_time']
                total += summa
                html += f"<tr><td>{p['name']}</td><td>{p['qty']}</td><td>{p['price_at_time']:.2f}</td><td>{summa:.2f}</td></tr>"
            
            html += f"</table><h2>ИТОГО: {total:.2f} руб.</h2></body></html>"
            
            dialog = DocumentViewDialog(html, self)
            dialog.exec()
        finally:
            conn.close()
    
    def generate_act(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wo.*, c.full_name, c.phone,
                       CONCAT(v.make, ' ', v.model, ' ', v.year) as vehicle, v.vin, v.plate_number
                FROM work_orders wo
                JOIN clients c ON wo.client_id = c.client_id
                JOIN vehicles v ON wo.vehicle_id = v.vehicle_id
                WHERE wo.work_order_id = %s
            """, (self.order_id,))
            order = cursor.fetchone()
            
            html = f"""
            <html>
            <head><meta charset="utf-8"></head>
            <body>
            <h1>АКТ ПРИЁМА-ПЕРЕДАЧИ</h1>
            <p>Дата: {order['created_at']}</p>
            <p>Клиент: {order['full_name']}, тел. {order['phone']}</p>
            <p>Автомобиль: {order['vehicle']}, VIN: {order['vin']}, Гос.номер: {order['plate_number']}</p>
            <p>Статус: {order['status']}</p>
            </body></html>
            """
            
            dialog = DocumentViewDialog(html, self)
            dialog.exec()
        finally:
            conn.close()


class SelectServiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Выбрать услугу')
        layout = QVBoxLayout()
        
        self.services_list = QListWidget()
        self.load_services()
        layout.addWidget(self.services_list)
        
        layout.addWidget(QLabel('Количество:'))
        self.qty = QSpinBox()
        self.qty.setRange(1, 100)
        self.qty.setValue(1)
        layout.addWidget(self.qty)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.selected_service_id = None
    
    def load_services(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.service_id, sc.name as category, s.name, s.price
                FROM services s
                JOIN service_categories sc ON s.category_id = sc.category_id
                WHERE s.is_active = 1
                ORDER BY sc.name, s.name
            """)
            
            for row in cursor.fetchall():
                item = QListWidgetItem(f"[{row['category']}] {row['name']} - {row['price']:.2f} руб.")
                item.setData(Qt.ItemDataRole.UserRole, row['service_id'])
                self.services_list.addItem(item)
        finally:
            conn.close()
    
    def get_selected(self):
        item = self.services_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole), self.qty.value()
        return None, 1


class SelectPartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Выбрать запчасть')
        layout = QVBoxLayout()
        
        self.parts_list = QListWidget()
        self.load_parts()
        layout.addWidget(self.parts_list)
        
        layout.addWidget(QLabel('Количество:'))
        self.qty = QSpinBox()
        self.qty.setRange(1, 100)
        self.qty.setValue(1)
        layout.addWidget(self.qty)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def load_parts(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT part_id, name, price, stock_qty FROM parts WHERE is_active = 1 ORDER BY name")
            
            for row in cursor.fetchall():
                item = QListWidgetItem(f"{row['name']} - {row['price']:.2f} руб. (остаток: {row['stock_qty']})")
                item.setData(Qt.ItemDataRole.UserRole, row['part_id'])
                self.parts_list.addItem(item)
        finally:
            conn.close()
    
    def get_selected(self):
        item = self.parts_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole), self.qty.value()
        return None, 1


class DocumentViewDialog(QDialog):
    def __init__(self, html, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Документ')
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout()
        
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        
        btn_save_pdf = QPushButton('Сохранить в PDF')
        btn_save_pdf.clicked.connect(lambda: self.save_to_pdf(html))
        layout.addWidget(btn_save_pdf)
        
        self.setLayout(layout)
        self.html_content = html
    
    def save_to_pdf(self, html):
        """Сохранить документ в PDF файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить документ в PDF',
            'document.pdf',
            'PDF Files (*.pdf)'
        )
        
        if filename:
            try:
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(filename)
                
                document = QTextDocument()
                document.setHtml(html)
                document.print(printer)
                
                QMessageBox.information(self, 'Успех', f'Документ сохранён в файл:\n{filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при сохранении PDF:\n{e}')

