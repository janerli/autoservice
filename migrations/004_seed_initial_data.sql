-- 004_seed_initial_data.sql
-- Тестовые данные (минимум 3 записи в каждую таблицу)
USE autoservice;

-- Категории услуг (минимум 4)
INSERT INTO service_categories (name) VALUES
('ТО'),
('Диагностика'),
('Шиномонтаж'),
('Кузовной ремонт'),
('Электрика')
ON DUPLICATE KEY UPDATE name=name;

-- Пользователи (3+)
-- Пароли: director123, admin123, client1, client2, client3
INSERT INTO users (login, password_hash, role, is_active) VALUES
('director', SHA2('director123', 256), 'DIRECTOR', 1),
('admin', SHA2('admin123', 256), 'ADMIN', 1),
('client1', SHA2('client1', 256), 'CLIENT', 1),
('client2', SHA2('client2', 256), 'CLIENT', 1),
('client3', SHA2('client3', 256), 'CLIENT', 1)
ON DUPLICATE KEY UPDATE login=login;

-- Клиенты (3+)
INSERT INTO clients (user_id, full_name, phone, email) VALUES
((SELECT user_id FROM users WHERE login='client1'), 'Смирнова Анна Петровна', '+7 900 111 22 33', 'anna@mail.test'),
((SELECT user_id FROM users WHERE login='client2'), 'Ковалёв Олег Викторович', '+7 900 222 33 44', 'oleg@mail.test'),
((SELECT user_id FROM users WHERE login='client3'), 'Демидова Ирина Сергеевна', '+7 900 333 44 55', 'irina@mail.test')
ON DUPLICATE KEY UPDATE full_name=full_name;

-- Механики (3+)
INSERT INTO mechanics (full_name, phone, is_active) VALUES
('Иванов Иван Иванович', '+7 900 555 11 11', 1),
('Петров Пётр Петрович', '+7 900 555 22 22', 1),
('Сидоров Сергей Сергеевич', '+7 900 555 33 33', 1)
ON DUPLICATE KEY UPDATE full_name=full_name;

-- Автомобили (3+)
INSERT INTO vehicles (client_id, make, model, year, vin, plate_number, mileage_km) VALUES
((SELECT client_id FROM clients WHERE email='anna@mail.test'), 'Toyota', 'Corolla', 2012, 'JTDBR32E720123456', 'KR1AAA1', 180000),
((SELECT client_id FROM clients WHERE email='oleg@mail.test'), 'VW', 'Golf', 2016, 'WVWZZZ1KZGW123456', 'WA2BBB2', 98000),
((SELECT client_id FROM clients WHERE email='irina@mail.test'), 'BMW', 'X3', 2018, 'WBAWX31090P123456', 'GD3CCC3', 74000)
ON DUPLICATE KEY UPDATE vin=vin;

-- Услуги (6+)
INSERT INTO services (category_id, name, price, is_active) VALUES
((SELECT category_id FROM service_categories WHERE name='ТО'), 'Замена масла двигателя', 150.00, 1),
((SELECT category_id FROM service_categories WHERE name='ТО'), 'Замена фильтров', 200.00, 1),
((SELECT category_id FROM service_categories WHERE name='Диагностика'), 'Компьютерная диагностика', 120.00, 1),
((SELECT category_id FROM service_categories WHERE name='Диагностика'), 'Диагностика подвески', 150.00, 1),
((SELECT category_id FROM service_categories WHERE name='Шиномонтаж'), 'Сезонная смена шин', 200.00, 1),
((SELECT category_id FROM service_categories WHERE name='Электрика'), 'Замена аккумулятора', 80.00, 1),
((SELECT category_id FROM service_categories WHERE name='Кузовной ремонт'), 'Покраска бампера', 500.00, 1)
ON DUPLICATE KEY UPDATE name=name;

-- Запчасти (6+)
INSERT INTO parts (name, unit, price, stock_qty, is_active) VALUES
('Масляный фильтр', 'шт', 25.00, 10, 1),
('Моторное масло 5W-30', 'л', 30.00, 50, 1),
('Воздушный фильтр', 'шт', 35.00, 15, 1),
('Аккумулятор 60Ah', 'шт', 320.00, 5, 1),
('Комплект шиномонтажа', 'компл', 15.00, 30, 1),
('Тормозные колодки передние', 'компл', 120.00, 8, 1),
('Лампа H7', 'шт', 15.00, 20, 1)
ON DUPLICATE KEY UPDATE name=name;

-- Записи на обслуживание (3+)
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

-- Заказ-наряды (3+)
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

