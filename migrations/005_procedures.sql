-- 005_procedures.sql
-- Хранимая процедура для расчёта среднего чека
USE autoservice;

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

