# NovaCommerce — DAX Measure Library

All measures live in the **NovaCommerce Measures** display folder.
Business logic is in dbt (SQL); DAX is for time-intelligence and UI formatting only.

---

## 1. Revenue Measures

```dax
-- ── Core revenue ──────────────────────────────────────────────────────────────

Gross Revenue =
SUM(fct_order_items[revenue])

Total Discounts =
SUM(fct_order_items[discount])

Total Refunds =
SUMX(fct_refunds, fct_refunds[amount])

Net Revenue =
[Gross Revenue] - [Total Discounts] - [Total Refunds]

COGS =
SUM(fct_order_items[cost])

Gross Profit =
[Net Revenue] - [COGS]

Gross Margin % =
DIVIDE([Gross Profit], [Net Revenue])

-- ── Order metrics ─────────────────────────────────────────────────────────────

Order Count =
DISTINCTCOUNT(fct_orders[order_id])

AOV =
DIVIDE([Net Revenue], [Order Count])

Units Sold =
SUM(fct_order_items[quantity])
```

---

## 2. Customer Metrics

```dax
Total Customers =
DISTINCTCOUNT(dim_customer[customer_id])

New Customers =
CALCULATE(
    DISTINCTCOUNT(fct_orders[customer_id]),
    fct_orders[order_date] = MINX(
        FILTER(fct_orders, fct_orders[customer_id] = EARLIER(fct_orders[customer_id])),
        fct_orders[order_date]
    )
)

Repeat Customers =
CALCULATE(
    DISTINCTCOUNT(dim_customer[customer_id]),
    dim_customer[is_repeat_customer] = TRUE()
)

Avg LTV =
AVERAGEX(dim_customer, dim_customer[lifetime_revenue])
```

---

## 3. Marketing Metrics

```dax
Total Ad Spend =
SUM(fct_ad_spend[spend])

Attributed Revenue =
SUM(fct_ad_spend[attributed_revenue])

ROAS =
DIVIDE([Attributed Revenue], [Total Ad Spend])

Total Conversions =
SUM(fct_ad_spend[conversions])

CAC =
DIVIDE([Total Ad Spend], [New Customers])

CTR =
DIVIDE(SUM(fct_ad_spend[clicks]), SUM(fct_ad_spend[impressions]))

CVR =
DIVIDE(SUM(fct_ad_spend[conversions]), SUM(fct_ad_spend[clicks]))
```

---

## 4. Refund & Quality Metrics

```dax
Refund Rate =
DIVIDE([Total Refunds], [Gross Revenue])

Refund Count =
COUNTROWS(fct_refunds)

Over-Refund Count =
CALCULATE(COUNTROWS(fct_refunds), fct_refunds[is_over_refund] = TRUE())

Payment Exceptions =
CALCULATE(
    COUNTROWS(fct_payments),
    fct_payments[reconciliation_status] = "EXCEPTION"
)

Payment Warnings =
CALCULATE(
    COUNTROWS(fct_payments),
    fct_payments[reconciliation_status] = "WARNING"
)
```

---

## 5. Inventory Metrics

```dax
Total Inventory Value =
SUM(fct_inventory[inventory_value])

Out of Stock SKUs =
CALCULATE(
    DISTINCTCOUNT(fct_inventory[product_id]),
    fct_inventory[stock_status] = "out_of_stock"
)

Low Stock SKUs =
CALCULATE(
    DISTINCTCOUNT(fct_inventory[product_id]),
    fct_inventory[stock_status] = "low_stock"
)

Inventory Turnover =
DIVIDE([COGS], AVERAGEX(VALUES(dim_date[month_number]), [Total Inventory Value]))
```

---

## 6. Fulfillment Metrics

```dax
Shipment Count =
COUNTROWS(fct_shipments)

On-Time Delivery Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fct_shipments), fct_shipments[is_on_time] = TRUE()),
    [Shipment Count]
)

Avg Transit Days =
AVERAGEX(FILTER(fct_shipments, NOT ISBLANK(fct_shipments[transit_days])),
    fct_shipments[transit_days])

Late Shipments =
CALCULATE(COUNTROWS(fct_shipments), fct_shipments[days_late] > 0)
```

---

## 7. Time Intelligence

```dax
-- ── Month-to-date ─────────────────────────────────────────────────────────────
Net Revenue MTD =
CALCULATE([Net Revenue], DATESMTD(dim_date[full_date]))

Gross Profit MTD =
CALCULATE([Gross Profit], DATESMTD(dim_date[full_date]))

-- ── Quarter-to-date ───────────────────────────────────────────────────────────
Net Revenue QTD =
CALCULATE([Net Revenue], DATESQTD(dim_date[full_date]))

-- ── Year-to-date ──────────────────────────────────────────────────────────────
Net Revenue YTD =
CALCULATE([Net Revenue], DATESYTD(dim_date[full_date]))

Gross Profit YTD =
CALCULATE([Gross Profit], DATESYTD(dim_date[full_date]))

-- ── Previous period ───────────────────────────────────────────────────────────
Net Revenue PM =
CALCULATE([Net Revenue], PREVIOUSMONTH(dim_date[full_date]))

Net Revenue PY =
CALCULATE([Net Revenue], SAMEPERIODLASTYEAR(dim_date[full_date]))

-- ── Period-over-period % ──────────────────────────────────────────────────────
Revenue MoM % =
DIVIDE([Net Revenue] - [Net Revenue PM], [Net Revenue PM])

Revenue YoY % =
DIVIDE([Net Revenue] - [Net Revenue PY], [Net Revenue PY])

Gross Margin MoM pp =
[Gross Margin %] - CALCULATE([Gross Margin %], PREVIOUSMONTH(dim_date[full_date]))
```

---

## 8. Financial Reconciliation

```dax
Total Net Payout =
SUM(fct_payouts[net_payout])

Total Payout Variance =
SUM(fct_payouts[payout_variance])

Recon Exception Count =
CALCULATE(
    COUNTROWS(fct_payouts),
    fct_payouts[reconciliation_status] = "EXCEPTION"
)

Expected vs Actual Payout Δ =
[Net Revenue] - [Total Net Payout]
```

---

## Design Decisions

| Concern | Decision |
|---|---|
| Business logic | Defined in dbt SQL — not duplicated in DAX |
| Margin % | Computed in fct_order_items; DAX only aggregates |
| Time intelligence | All DAX time functions use `dim_date[full_date]` |
| Bi-directional | Avoided — all relationships single-direction |
| Row-level security | Apply via dim_customer[customer_segment] if needed |
