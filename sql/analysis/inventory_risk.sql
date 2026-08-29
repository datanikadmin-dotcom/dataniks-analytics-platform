-- Products at risk: out of stock or low stock
SELECT
    p.category,
    p.subcategory,
    p.name                              AS product_name,
    p.sku,
    w.name                              AS warehouse,
    i.closing_qty,
    i.reorder_point,
    i.stock_status,
    ROUND(i.days_of_supply, 1)          AS days_of_supply,
    ROUND(i.inventory_value, 2)         AS inventory_value
FROM main_marts.fct_inventory i
JOIN main_marts.dim_product p ON i.product_id = p.product_id
JOIN main_marts.dim_warehouse w ON i.warehouse_id = w.warehouse_id
WHERE i.stock_status IN ('out_of_stock', 'low_stock')
ORDER BY i.stock_status, i.days_of_supply;
