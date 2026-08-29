# NovaCommerce Power BI — Report Pages

All pages connect to the same star schema. Slicers are cross-page using sync.

---

## Page 1 — Executive Overview

**Purpose:** C-suite one-glance health check.

**Visuals:**

| Visual | Type | Measures | Notes |
|---|---|---|---|
| Revenue KPI | Card | Net Revenue, YoY % | Conditional format: red if YoY < 0 |
| Profit KPI | Card | Gross Profit, Gross Margin % | |
| Orders KPI | Card | Order Count, MoM % | |
| AOV KPI | Card | AOV | |
| Revenue trend | Line | Net Revenue MTD vs same period PY | |
| Revenue by channel | Bar | Net Revenue | Sorted descending |
| Top 10 categories | Bar | Gross Profit | dim_product[category] |
| Refund rate | Gauge | Refund Rate | Target = 3% |

**Slicers:** Date range (dim_date[full_date]), Channel (dim_channel[channel_name])

---

## Page 2 — Sales & Profitability

**Purpose:** Deep-dive into revenue and margin drivers.

**Visuals:**

| Visual | Type | Measures | Notes |
|---|---|---|---|
| Revenue waterfall | Waterfall | Gross → Discounts → Refunds → Net | Shows leakage |
| Monthly trend | Line + column combo | Net Revenue (line), Gross Profit (column) | Dual axis |
| Category margin matrix | Matrix | dim_product[category] × dim_date[month_name] → Gross Margin % | Heatmap format |
| Channel decomposition | Stacked bar | Net Revenue by channel, stacked by category | |
| AOV trend | Line | AOV by month | |
| Top products table | Table | Product, Units Sold, Net Revenue, Gross Margin % | Top 20 |

**Slicers:** Date range, Channel, Category, Customer Segment

---

## Page 3 — Customers & Marketing

**Purpose:** Customer lifetime value, acquisition, and campaign effectiveness.

**Visuals:**

| Visual | Type | Measures | Notes |
|---|---|---|---|
| New vs Repeat customers | Donut | New Customers, Repeat Customers | |
| CAC trend | Line | CAC by month | |
| LTV distribution | Histogram | Avg LTV by segment | Buckets from dim_customer[value_tier] |
| ROAS by channel | Bar | ROAS | Conditional: green >3, yellow 1–3, red <1 |
| Campaign performance table | Table | Campaign, Spend, Revenue, ROAS, CTR, CVR | |
| Customer acquisition cohort | Matrix | signup_cohort × month → New Customers | |
| Marketing spend vs revenue | Scatter | x=Total Ad Spend, y=Attributed Revenue, size=ROAS | Channel as legend |

**Slicers:** Date range, Channel, Campaign (dim_channel[campaign_name])

---

## Page 4 — Inventory & Fulfillment

**Purpose:** Stock health and logistics performance.

**Visuals:**

| Visual | Type | Measures | Notes |
|---|---|---|---|
| Stock status KPIs | Cards | Out of Stock SKUs, Low Stock SKUs, Total Inventory Value | |
| On-time delivery rate | Gauge | On-Time Delivery Rate | Target = 95% |
| Stock status breakdown | Bar | SKU count by stock_status per category | |
| Inventory by warehouse | Matrix | dim_warehouse × dim_product[category] → Total Inventory Value | |
| Late shipments by carrier | Bar | Late Shipments per carrier | |
| Avg transit days trend | Line | Avg Transit Days by month | |
| At-risk SKU table | Table | Product, closing_qty, days_of_supply, stock_status | Filter: stock_status IN (low, out) |

**Slicers:** Date range, Warehouse, Category, Carrier

---

## Page 5 — Finance & Reconciliation

**Purpose:** Revenue → payments → refunds → fees → payouts reconciliation.

**Visuals:**

| Visual | Type | Measures | Notes |
|---|---|---|---|
| Reconciliation waterfall | Waterfall | Net Revenue → Payments → Refunds → Fees → Net Payout | |
| Exception count KPI | Card | Payment Exceptions | Conditional: red if > 0 |
| Warning count KPI | Card | Payment Warnings | |
| Payout variance KPI | Card | Total Payout Variance | |
| Exception trend | Line | Recon Exception Count by month | |
| Reconciliation status by platform | Stacked bar | Order count by MATCHED/WARNING/EXCEPTION per platform | |
| Payout reconciliation table | Table | Period, Platform, Gross Revenue, Net Payout, Payout Variance, Status | Conditional rows |
| Refund anomalies table | Table | Order ID, refund_amount, payment_amount, is_over_refund | Filter: over-refunds only |

**Slicers:** Date range, Platform (fct_payouts[platform]), Reconciliation Status

---

## Navigation & UX

- Use a left-side nav panel with icons for each page (collapsed on mobile).
- Bookmarks for "Current Month" vs "Last 12 Months" — tied to date slicer.
- All tables: enable drill-through to order-level detail (set fct_orders as drill-through target).
- Tooltip page: show order trend when hovering over a customer in Page 3.
