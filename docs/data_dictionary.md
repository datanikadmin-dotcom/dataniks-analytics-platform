# Data Dictionary

All tables are in the `main_marts` schema of the DuckDB warehouse (or BigQuery dataset `novacommerce_marts` in production).

---

## Dimension Tables

### dim_date
| Column | Type | Description |
|---|---|---|
| date_id | DATE | Primary key |
| full_date | DATE | Same as date_id (for DAX time intelligence) |
| year | INT | Calendar year |
| quarter | INT | Quarter (1-4) |
| month_number | INT | Month (1-12) |
| month_name | VARCHAR | e.g. "January" |
| week_of_year | INT | ISO week number |
| day_of_week | INT | 1=Monday … 7=Sunday |
| day_name | VARCHAR | e.g. "Monday" |
| is_weekend | BOOL | True for Saturday/Sunday |
| is_holiday | BOOL | True for US federal holidays |

### dim_customer
| Column | Type | Description |
|---|---|---|
| customer_id | VARCHAR | Primary key |
| email | VARCHAR | Customer email |
| full_name | VARCHAR | First + last name |
| signup_date | DATE | Registration date |
| signup_cohort | VARCHAR | YYYY-MM of signup (for cohort analysis) |
| segment | VARCHAR | enterprise / mid_market / smb / consumer |
| city | VARCHAR | |
| state | VARCHAR | |
| country | VARCHAR | |
| lifetime_revenue | DECIMAL | Sum of all net revenue |
| order_count | INT | Total orders placed |
| first_order_date | DATE | |
| last_order_date | DATE | |
| is_repeat_customer | BOOL | order_count > 1 |
| active_days | INT | Days since first order |
| value_tier | VARCHAR | high / mid / low (based on LTV quartiles) |

### dim_product
| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | Primary key |
| sku | VARCHAR | Stock-keeping unit |
| name | VARCHAR | Product name |
| category | VARCHAR | Top-level category (8 categories) |
| subcategory | VARCHAR | |
| category_path | VARCHAR | category / subcategory |
| base_price | DECIMAL | List price |
| base_cost | DECIMAL | Unit cost |
| weight_kg | DECIMAL | Shipping weight |
| units_sold | INT | Lifetime units sold (from int_product_sales) |
| gross_revenue | DECIMAL | Lifetime revenue |
| gross_margin_pct | DECIMAL | (revenue - cost) / revenue |

### dim_channel
| Column | Type | Description |
|---|---|---|
| channel_id | VARCHAR | Primary key |
| channel_name | VARCHAR | organic / email / paid_search / paid_social / affiliate / referral / direct |
| channel_type | VARCHAR | organic / paid / direct |

### dim_warehouse
| Column | Type | Description |
|---|---|---|
| warehouse_id | VARCHAR | Primary key |
| name | VARCHAR | e.g. "West Coast Hub" |
| region | VARCHAR | west / east / central / south / north |
| city | VARCHAR | |
| state | VARCHAR | |

---

## Fact Tables

### fct_orders
Grain: one row per order.

| Column | Type | Description |
|---|---|---|
| order_id | VARCHAR | Primary key |
| customer_id | VARCHAR | FK → dim_customer |
| channel_id | VARCHAR | FK → dim_channel |
| date_id | DATE | FK → dim_date |
| order_date | TIMESTAMP | Full order timestamp |
| status | VARCHAR | placed / fulfilled / cancelled / returned / unknown |
| gross_revenue | DECIMAL | Sum of item revenues |
| total_discount | DECIMAL | Sum of item discounts |
| total_refunds | DECIMAL | Sum of refund amounts |
| net_revenue | DECIMAL | gross - discounts - refunds |
| total_cost | DECIMAL | Sum of item costs |
| gross_profit | DECIMAL | net_revenue - total_cost |
| item_count | INT | Distinct SKUs in order |
| unit_count | INT | Total quantity |
| refund_count | INT | Number of refunds |
| has_refund | BOOL | refund_count > 0 |
| has_multiple_refunds | BOOL | refund_count > 1 |

### fct_order_items
Grain: one row per order × product.

| Column | Type | Description |
|---|---|---|
| item_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → fct_orders |
| product_id | VARCHAR | FK → dim_product |
| date_id | DATE | FK → dim_date |
| quantity | INT | |
| unit_price | DECIMAL | Actual sold price |
| discount | DECIMAL | Item discount |
| revenue | DECIMAL | quantity × unit_price |
| cost | DECIMAL | quantity × base_cost |
| item_margin_pct | DECIMAL | (revenue - cost) / revenue |
| effective_unit_price | DECIMAL | (revenue - discount) / quantity |

### fct_payments
Grain: one row per payment.

| Column | Type | Description |
|---|---|---|
| payment_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → fct_orders |
| date_id | DATE | FK → dim_date |
| amount | DECIMAL | |
| method | VARCHAR | credit_card / paypal / buy_now_pay_later / bank_transfer / crypto |
| status | VARCHAR | completed / failed / refunded |
| reconciliation_status | VARCHAR | MATCHED / WARNING / EXCEPTION |

### fct_refunds
Grain: one row per refund.

| Column | Type | Description |
|---|---|---|
| refund_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → fct_orders |
| payment_id | VARCHAR | FK → fct_payments |
| customer_id | VARCHAR | FK → dim_customer |
| date_id | DATE | FK → dim_date |
| amount | DECIMAL | |
| reason | VARCHAR | |
| is_over_refund | BOOL | refund > original payment |

### fct_inventory
Grain: product × warehouse × month snapshot.

| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | FK → dim_product |
| warehouse_id | VARCHAR | FK → dim_warehouse |
| date_id | DATE | FK → dim_date |
| opening_qty | INT | Start of period |
| closing_qty | INT | End of period (clamped ≥ 0) |
| reorder_point | INT | |
| inventory_value | DECIMAL | closing_qty × base_cost |
| stock_status | VARCHAR | out_of_stock / low_stock / healthy / overstocked |
| days_of_supply | DECIMAL | closing_qty / avg daily demand |

### fct_shipments
Grain: one row per shipment.

| Column | Type | Description |
|---|---|---|
| shipment_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → fct_orders |
| warehouse_id | VARCHAR | FK → dim_warehouse |
| date_id | DATE | FK → dim_date (ship date) |
| carrier | VARCHAR | UPS / FedEx / USPS / DHL / Amazon |
| shipped_at | TIMESTAMP | |
| estimated_delivery | DATE | |
| actual_delivery | DATE | |
| is_on_time | BOOL | actual ≤ estimated |
| transit_days | INT | actual - shipped (days) |
| days_late | INT | max(0, actual - estimated) |

### fct_ad_spend
Grain: campaign × date.

| Column | Type | Description |
|---|---|---|
| ad_id | VARCHAR | Primary key |
| channel_id | VARCHAR | FK → dim_channel |
| date_id | DATE | FK → dim_date |
| platform | VARCHAR | google / meta |
| campaign_name | VARCHAR | |
| spend | DECIMAL | |
| impressions | INT | |
| clicks | INT | |
| conversions | INT | |
| attributed_revenue | DECIMAL | |
| roas | DECIMAL | attributed_revenue / spend |
| ctr | DECIMAL | clicks / impressions |

### fct_payouts
Grain: one row per payout from marketplace/platform.

| Column | Type | Description |
|---|---|---|
| payout_id | VARCHAR | Primary key |
| date_id | DATE | FK → dim_date |
| platform | VARCHAR | shopify / amazon / etsy |
| period_start | DATE | |
| period_end | DATE | |
| gross_revenue | DECIMAL | Platform's reported revenue |
| platform_fees | DECIMAL | |
| refunds | DECIMAL | |
| net_payout | DECIMAL | gross - fees - refunds |
| our_net_revenue | DECIMAL | From fct_orders for same period |
| payout_variance | DECIMAL | net_payout - our_net_revenue |
| reconciliation_status | VARCHAR | MATCHED / WARNING / EXCEPTION |

---

## Mart Tables

### mart_sales
Grain: month × channel.

| Column | Type | Description |
|---|---|---|
| month | DATE | First day of month |
| channel_id | VARCHAR | FK → dim_channel |
| gross_revenue | DECIMAL | |
| net_revenue | DECIMAL | |
| gross_profit | DECIMAL | |
| gross_margin_pct | DECIMAL | |
| order_count | INT | |
| aov | DECIMAL | |
| units_sold | INT | |

### mart_customer
Grain: one row per customer.

All dim_customer columns plus:

| Column | Type | Description |
|---|---|---|
| signup_cohort | VARCHAR | YYYY-MM |
| recency_status | VARCHAR | Active (≤30d) / Lapsing (31-90d) / Churned (>90d) |

### mart_marketing
Grain: campaign × month.

| Column | Type | Description |
|---|---|---|
| month | DATE | |
| channel_id | VARCHAR | |
| platform | VARCHAR | |
| campaign_name | VARCHAR | |
| spend | DECIMAL | |
| attributed_revenue | DECIMAL | |
| roas | DECIMAL | |
| avg_ctr | DECIMAL | |
| avg_cvr | DECIMAL | |
| cost_per_conversion | DECIMAL | |

### mart_inventory
Grain: product × warehouse (latest snapshot).

| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | |
| warehouse_id | VARCHAR | |
| closing_qty | INT | |
| inventory_value | DECIMAL | |
| stock_status | VARCHAR | |
| days_of_supply | DECIMAL | |

### mart_finance
Grain: month × platform.

| Column | Type | Description |
|---|---|---|
| month | DATE | |
| platform | VARCHAR | |
| gross_revenue | DECIMAL | |
| total_payments | DECIMAL | |
| total_refunds | DECIMAL | |
| net_payout | DECIMAL | |
| payout_variance | DECIMAL | |
| reconciliation_status | VARCHAR | |
