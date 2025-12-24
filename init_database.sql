-- Полный SQL скрипт для инициализации БД автосервиса
-- Выполните этот скрипт в MySQL для создания всех таблиц, данных и процедур

-- Создание БД
CREATE DATABASE IF NOT EXISTS autoservice
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE autoservice;

-- Таблица учёта миграций (необязательно, но оставлено для совместимости)
CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(50) PRIMARY KEY,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Пользователи (для авторизации)
CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  login VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('DIRECTOR','ADMIN','CLIENT') NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_role (role)
) ENGINE=InnoDB;

-- Клиенты
CREATE TABLE IF NOT EXISTS clients (
  client_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NULL UNIQUE,
  full_name VARCHAR(200) NOT NULL,
  phone VARCHAR(30) NOT NULL,
  email VARCHAR(120) NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_clients_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Механики
CREATE TABLE IF NOT EXISTS mechanics (
  mechanic_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(200) NOT NULL,
  phone VARCHAR(30) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Автомобили
CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  client_id BIGINT UNSIGNED NOT NULL,
  make VARCHAR(80) NOT NULL,
  model VARCHAR(80) NOT NULL,
  year SMALLINT UNSIGNED NOT NULL,
  vin VARCHAR(32) NOT NULL UNIQUE,
  plate_number VARCHAR(20) NOT NULL UNIQUE,
  mileage_km INT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_vehicles_client
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Категории услуг
CREATE TABLE IF NOT EXISTS service_categories (
  category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Услуги (прайс-лист)
CREATE TABLE IF NOT EXISTS services (
  service_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  category_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(160) NOT NULL,
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_services_category
    FOREIGN KEY (category_id) REFERENCES service_categories(category_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  INDEX idx_category (category_id),
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Запчасти (прайс-лист)
CREATE TABLE IF NOT EXISTS parts (
  part_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  unit VARCHAR(20) NOT NULL DEFAULT 'шт',
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  stock_qty INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- Записи клиентов на обслуживание
CREATE TABLE IF NOT EXISTS appointments (
  appointment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  client_id BIGINT UNSIGNED NOT NULL,
  vehicle_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  scheduled_at DATETIME NOT NULL,
  comment TEXT NULL,
  status ENUM('Запланирована','Отменена','Преобразована в заказ-наряд') NOT NULL DEFAULT 'Запланирована',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_appointments_client
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_appointments_vehicle
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_appointments_category
    FOREIGN KEY (category_id) REFERENCES service_categories(category_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  INDEX idx_scheduled (scheduled_at),
  INDEX idx_client (client_id),
  INDEX idx_status (status)
) ENGINE=InnoDB;

-- Заказ-наряды
CREATE TABLE IF NOT EXISTS work_orders (
  work_order_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  appointment_id BIGINT UNSIGNED NULL,
  client_id BIGINT UNSIGNED NOT NULL,
  vehicle_id BIGINT UNSIGNED NOT NULL,
  mechanic_id BIGINT UNSIGNED NULL,
  complaint TEXT NULL,
  diagnostics_result TEXT NULL,
  status ENUM(
    'Ожидает',
    'В работе',
    'Ожидает запчасти',
    'Ожидает согласования',
    'Выполнен',
    'Выдан клиенту',
    'Отменён'
  ) NOT NULL DEFAULT 'Ожидает',
  estimated_ready_at DATETIME NULL,
  closed_at DATETIME NULL,
  CONSTRAINT fk_work_orders_appointment
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_work_orders_client
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_work_orders_vehicle
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_work_orders_mechanic
    FOREIGN KEY (mechanic_id) REFERENCES mechanics(mechanic_id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  INDEX idx_status (status),
  INDEX idx_created (created_at),
  INDEX idx_client (client_id),
  INDEX idx_vehicle (vehicle_id)
) ENGINE=InnoDB;

-- Услуги в заказ-наряде
CREATE TABLE IF NOT EXISTS work_order_services (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  work_order_id BIGINT UNSIGNED NOT NULL,
  service_id BIGINT UNSIGNED NOT NULL,
  qty INT NOT NULL DEFAULT 1,
  price_at_time DECIMAL(10,2) NOT NULL CHECK (price_at_time >= 0),
  CONSTRAINT fk_wos_work_order
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_wos_service
    FOREIGN KEY (service_id) REFERENCES services(service_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  UNIQUE KEY uq_wos (work_order_id, service_id),
  INDEX idx_work_order (work_order_id)
) ENGINE=InnoDB;

-- Запчасти в заказ-наряде
CREATE TABLE IF NOT EXISTS work_order_parts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  work_order_id BIGINT UNSIGNED NOT NULL,
  part_id BIGINT UNSIGNED NOT NULL,
  qty INT NOT NULL DEFAULT 1,
  price_at_time DECIMAL(10,2) NOT NULL CHECK (price_at_time >= 0),
  CONSTRAINT fk_wop_work_order
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_wop_part
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  UNIQUE KEY uq_wop (work_order_id, part_id),
  INDEX idx_work_order (work_order_id)
) ENGINE=InnoDB;

-- ============================================
-- ТЕСТОВЫЕ ДАННЫЕ
-- ============================================

-- Категории услуг
INSERT INTO service_categories (name) VALUES
('ТО'),
('Диагностика'),
('Шиномонтаж'),
('Кузовной ремонт'),
('Электрика')
ON DUPLICATE KEY UPDATE name=name;

-- Пользователи (пароли: director123, admin123, client1, client2, client3)
INSERT INTO users (login, password_hash, role, is_active) VALUES
('director', SHA2('director123', 256), 'DIRECTOR', 1),
('admin', SHA2('admin123', 256), 'ADMIN', 1),
('client1', SHA2('client1', 256), 'CLIENT', 1),
('client2', SHA2('client2', 256), 'CLIENT', 1),
('client3', SHA2('client3', 256), 'CLIENT', 1)
ON DUPLICATE KEY UPDATE login=login;

-- Клиенты
INSERT INTO clients (user_id, full_name, phone, email) VALUES
((SELECT user_id FROM users WHERE login='client1'), 'Смирнова Анна Петровна', '+7 900 111 22 33', 'anna@mail.test'),
((SELECT user_id FROM users WHERE login='client2'), 'Ковалёв Олег Викторович', '+7 900 222 33 44', 'oleg@mail.test'),
((SELECT user_id FROM users WHERE login='client3'), 'Демидова Ирина Сергеевна', '+7 900 333 44 55', 'irina@mail.test')
ON DUPLICATE KEY UPDATE full_name=full_name;

-- Механики
INSERT INTO mechanics (full_name, phone, is_active) VALUES
('Иванов Иван Иванович', '+7 900 555 11 11', 1),
('Петров Пётр Петрович', '+7 900 555 22 22', 1),
('Сидоров Сергей Сергеевич', '+7 900 555 33 33', 1)
ON DUPLICATE KEY UPDATE full_name=full_name;

-- Автомобили
INSERT INTO vehicles (client_id, make, model, year, vin, plate_number, mileage_km) VALUES
((SELECT client_id FROM clients WHERE email='anna@mail.test'), 'Toyota', 'Corolla', 2012, 'JTDBR32E720123456', 'KR1AAA1', 180000),
((SELECT client_id FROM clients WHERE email='oleg@mail.test'), 'VW', 'Golf', 2016, 'WVWZZZ1KZGW123456', 'WA2BBB2', 98000),
((SELECT client_id FROM clients WHERE email='irina@mail.test'), 'BMW', 'X3', 2018, 'WBAWX31090P123456', 'GD3CCC3', 74000)
ON DUPLICATE KEY UPDATE vin=vin;

-- Услуги
INSERT INTO services (category_id, name, price, is_active) VALUES
((SELECT category_id FROM service_categories WHERE name='ТО'), 'Замена масла двигателя', 150.00, 1),
((SELECT category_id FROM service_categories WHERE name='ТО'), 'Замена фильтров', 200.00, 1),
((SELECT category_id FROM service_categories WHERE name='Диагностика'), 'Компьютерная диагностика', 120.00, 1),
((SELECT category_id FROM service_categories WHERE name='Диагностика'), 'Диагностика подвески', 150.00, 1),
((SELECT category_id FROM service_categories WHERE name='Шиномонтаж'), 'Сезонная смена шин', 200.00, 1),
((SELECT category_id FROM service_categories WHERE name='Электрика'), 'Замена аккумулятора', 80.00, 1),
((SELECT category_id FROM service_categories WHERE name='Кузовной ремонт'), 'Покраска бампера', 500.00, 1)
ON DUPLICATE KEY UPDATE name=name;

-- Запчасти
INSERT INTO parts (name, unit, price, stock_qty, is_active) VALUES
('Масляный фильтр', 'шт', 25.00, 10, 1),
('Моторное масло 5W-30', 'л', 30.00, 50, 1),
('Воздушный фильтр', 'шт', 35.00, 15, 1),
('Аккумулятор 60Ah', 'шт', 320.00, 5, 1),
('Комплект шиномонтажа', 'компл', 15.00, 30, 1),
('Тормозные колодки передние', 'компл', 120.00, 8, 1),
('Лампа H7', 'шт', 15.00, 20, 1)
ON DUPLICATE KEY UPDATE name=name;

-- Записи на обслуживание
INSERT INTO appointments (client_id, vehicle_id, category_id, scheduled_at, comment, status) VALUES
((SELECT client_id FROM clients WHERE email='anna@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='JTDBR32E720123456'),
 (SELECT category_id FROM service_categories WHERE name='ТО'),
 DATE_ADD(NOW(), INTERVAL 1 DAY),
 'Хочу заменить масло', 'Запланирована'),
((SELECT client_id FROM clients WHERE email='oleg@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='WVWZZZ1KZGW123456'),
 (SELECT category_id FROM service_categories WHERE name='Диагностика'),
 DATE_ADD(NOW(), INTERVAL 2 DAY),
 'Горит чек двигателя', 'Запланирована'),
((SELECT client_id FROM clients WHERE email='irina@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='WBAWX31090P123456'),
 (SELECT category_id FROM service_categories WHERE name='Шиномонтаж'),
 DATE_ADD(NOW(), INTERVAL 3 DAY),
 'Переобуть на зиму', 'Запланирована')
ON DUPLICATE KEY UPDATE scheduled_at=scheduled_at;

-- Заказ-наряды
INSERT INTO work_orders (appointment_id, client_id, vehicle_id, mechanic_id, complaint, status, estimated_ready_at, closed_at) VALUES
(NULL,
 (SELECT client_id FROM clients WHERE email='anna@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='JTDBR32E720123456'),
 (SELECT mechanic_id FROM mechanics WHERE full_name='Петров Пётр Петрович' LIMIT 1),
 'Замена масла и фильтров',
 'Выполнен',
 DATE_ADD(NOW(), INTERVAL -1 DAY),
 DATE_ADD(NOW(), INTERVAL -1 DAY)),
(NULL,
 (SELECT client_id FROM clients WHERE email='oleg@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='WVWZZZ1KZGW123456'),
 (SELECT mechanic_id FROM mechanics WHERE full_name='Иванов Иван Иванович' LIMIT 1),
 'Горит чек, нужна диагностика',
 'В работе',
 DATE_ADD(NOW(), INTERVAL 1 DAY),
 NULL),
(NULL,
 (SELECT client_id FROM clients WHERE email='irina@mail.test'),
 (SELECT vehicle_id FROM vehicles WHERE vin='WBAWX31090P123456'),
 NULL,
 'Шиномонтаж',
 'Ожидает',
 DATE_ADD(NOW(), INTERVAL 2 DAY),
 NULL)
ON DUPLICATE KEY UPDATE complaint=complaint;

-- Услуги в заказ-нарядах
INSERT INTO work_order_services (work_order_id, service_id, qty, price_at_time) VALUES
((SELECT work_order_id FROM work_orders WHERE complaint='Замена масла и фильтров' LIMIT 1),
 (SELECT service_id FROM services WHERE name='Замена масла двигателя' LIMIT 1),
 1, (SELECT price FROM services WHERE name='Замена масла двигателя' LIMIT 1)),
((SELECT work_order_id FROM work_orders WHERE complaint='Замена масла и фильтров' LIMIT 1),
 (SELECT service_id FROM services WHERE name='Замена фильтров' LIMIT 1),
 1, (SELECT price FROM services WHERE name='Замена фильтров' LIMIT 1)),
((SELECT work_order_id FROM work_orders WHERE complaint='Горит чек, нужна диагностика' LIMIT 1),
 (SELECT service_id FROM services WHERE name='Компьютерная диагностика' LIMIT 1),
 1, (SELECT price FROM services WHERE name='Компьютерная диагностика' LIMIT 1))
ON DUPLICATE KEY UPDATE qty=qty;

-- Запчасти в заказ-нарядах
INSERT INTO work_order_parts (work_order_id, part_id, qty, price_at_time) VALUES
((SELECT work_order_id FROM work_orders WHERE complaint='Замена масла и фильтров' LIMIT 1),
 (SELECT part_id FROM parts WHERE name='Масляный фильтр' LIMIT 1),
 1, (SELECT price FROM parts WHERE name='Масляный фильтр' LIMIT 1)),
((SELECT work_order_id FROM work_orders WHERE complaint='Замена масла и фильтров' LIMIT 1),
 (SELECT part_id FROM parts WHERE name='Моторное масло 5W-30' LIMIT 1),
 4, (SELECT price FROM parts WHERE name='Моторное масло 5W-30' LIMIT 1))
ON DUPLICATE KEY UPDATE qty=qty;

-- ============================================
-- ХРАНИМАЯ ПРОЦЕДУРА
-- ============================================

DROP PROCEDURE IF EXISTS sp_avg_check;

DELIMITER $$
CREATE PROCEDURE sp_avg_check(IN p_date_from DATE, IN p_date_to DATE)
BEGIN
  /*
    Средний чек = выручка / количество завершённых заказ-нарядов за период.
    Завершённые: статус 'Выполнен' или 'Выдан клиенту'
  */
  SELECT
    COUNT(*) AS orders_count,
    COALESCE(SUM(
      (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_services WHERE work_order_id = wo.work_order_id) +
      (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_parts WHERE work_order_id = wo.work_order_id)
    ), 0) AS total_revenue,
    CASE
      WHEN COUNT(*) = 0 THEN 0
      ELSE ROUND(
        SUM(
          (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_services WHERE work_order_id = wo.work_order_id) +
          (SELECT COALESCE(SUM(qty * price_at_time), 0) FROM work_order_parts WHERE work_order_id = wo.work_order_id)
        ) / COUNT(*),
        2
      )
    END AS avg_check
  FROM work_orders wo
  WHERE wo.status IN ('Выполнен', 'Выдан клиенту')
    AND wo.closed_at IS NOT NULL
    AND DATE(wo.closed_at) >= p_date_from
    AND DATE(wo.closed_at) <= p_date_to;
END$$
DELIMITER ;

