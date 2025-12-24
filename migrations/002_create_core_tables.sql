-- 002_create_core_tables.sql
USE autoservice;

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

