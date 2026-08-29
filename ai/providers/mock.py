"""
Mock LLM provider — returns deterministic responses for development and testing.

No API key required. Responses are template-based and keyed on question intent,
so tests can assert on specific answer patterns without hitting a real LLM.
"""

from __future__ import annotations
import re
from typing import Any

from ai.providers.base import BaseLLMProvider, LLMResponse


class MockProvider(BaseLLMProvider):
    """Returns scripted responses based on detected question keywords."""

    provider_name = "mock"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})
        self.model = "mock-v1"

    def is_available(self) -> bool:
        return True

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> LLMResponse:
        content = self._generate(user_message, system_prompt)
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=len(system_prompt.split()) + len(user_message.split()),
            tokens_out=len(content.split()),
        )

    def _generate(self, question: str, system: str) -> str:
        q = question.lower()

        # ── SQL generation mode ────────────────────────────────────────────────
        if "write sql" in system.lower() or "generate sql" in system.lower():
            return self._sql_for(q)

        # ── Explanation mode ───────────────────────────────────────────────────
        if "revenue" in q and ("fall" in q or "decrease" in q or "drop" in q):
            return (
                "Based on the data for the requested period, net revenue declined "
                "primarily due to a reduction in paid-search channel performance "
                "(−18 % MoM) and a 12 % increase in the refund rate for the Electronics "
                "category. Order volume was broadly flat, suggesting the issue is "
                "average order value and product mix rather than traffic. "
                "Recommend investigating the Electronics refund spike and reviewing "
                "paid-search bid strategy."
            )

        if "margin" in q and "highest" in q:
            return (
                "The products with the highest gross margin are concentrated in the "
                "Beauty and Apparel categories, where realised margins average 58–62 %. "
                "The top individual SKUs are fragrance sets and premium skincare kits. "
                "Electronics has the lowest average margin at 22 %, dragged by "
                "competitive pricing on laptop and tablet lines."
            )

        if "roas" in q or ("marketing" in q and "channel" in q):
            return (
                "The best-performing channel by ROAS is Brand Search (Google Ads) at "
                "8.2x, followed by Display Retargeting at 5.1x. "
                "Meta Ads Retargeting - Cart delivers 6.0x but on a smaller spend base. "
                "Non-Brand Search and Prospecting campaigns have the lowest ROAS (2–3x) "
                "as expected for upper-funnel activity. "
                "Overall blended ROAS is 3.8x."
            )

        if "lifetime value" in q or "ltv" in q or ("customer" in q and "value" in q):
            return (
                "The top 10 % of customers by lifetime value account for 42 % of total "
                "net revenue. Champions segment customers average $1,840 LTV versus "
                "$210 for New customers. "
                "Loyal customers in the Apparel and Beauty categories show the strongest "
                "repeat purchase behaviour. Recommend targeted retention campaigns for "
                "At-Risk customers who have not ordered in 90+ days."
            )

        if "stock" in q or "inventory" in q or "out of stock" in q:
            return (
                "Currently 847 products are classified as low_stock (fewer than 10 units) "
                "and 312 are out_of_stock across all warehouses. "
                "The highest-risk category is Electronics, particularly Tablets and "
                "Headphones at WH-WEST. "
                "Based on current sell-through rates, 124 additional SKUs will reach "
                "zero stock within 14 days. Recommend expediting replenishment orders "
                "for the top 50 at-risk SKUs."
            )

        if "reconcil" in q or "payout" in q or "payment" in q:
            return (
                "The current reconciliation run shows 1,544 payment EXCEPTION records "
                "(variance > $100) totalling approximately $187,000 in unexplained "
                "discrepancies. An additional 978 WARNING records show $1–$100 variances. "
                "The root cause for most exceptions appears to be duplicate payment "
                "records (400 orphan payments detected). "
                "Finance should investigate the duplicate payment batch from the mock "
                "payments connector and reprocess those records."
            )

        if "refund" in q:
            return (
                "The refund rate has increased to 9.8 % of gross revenue, above the "
                "8 % historical baseline. The largest contributor is the Electronics "
                "category (damaged and defective reasons account for 61 % of refunds). "
                "A secondary driver is the 'wrong_item' reason in Apparel, suggesting "
                "a fulfilment accuracy issue at WH-EAST. "
                "408 refunds exceed the corresponding payment amount — these should be "
                "reviewed by finance immediately."
            )

        if "campaign" in q and "revenue" in q:
            return (
                "The highest revenue-generating campaigns are Brand Search ($2.1M "
                "attributed revenue, 8.2x ROAS) and Shopping - Electronics ($1.4M, "
                "4.5x ROAS). "
                "The Seasonal Sale campaign achieved 4.2x ROAS with strong Q4 "
                "performance. "
                "YouTube Awareness has the lowest ROAS (1.5x) as a brand-building "
                "investment — its value is in upper-funnel reach rather than direct "
                "conversion."
            )

        if "last month" in q or "compared" in q or "change" in q:
            return (
                "Compared to the prior month: net revenue is up 6.2 %, driven by "
                "strong Apparel performance (+14 %) and improved ROAS on Social Media "
                "campaigns. Orders grew 4.8 %. Gross margin improved by 1.1 pp to "
                "41.3 %. The main headwinds are Electronics refunds (+22 %) and "
                "higher shipping costs in Q4. Overall the business is trending positively."
            )

        if "warehouse" in q and ("delay" in q or "shipment" in q):
            return (
                "WH-EAST has the highest rate of late deliveries at 8.2 % of shipments, "
                "compared to a fleet average of 5.1 %. The primary carrier contributing "
                "to delays is USPS for short-haul routes. WH-CENTRAL shows the best "
                "on-time performance at 96.4 %. "
                "Recommend reviewing USPS contracts for the Eastern region and exploring "
                "UPS or FedEx as primary carriers for WH-EAST."
            )

        if "cannot" in system.lower() or "unknown" in system.lower():
            return (
                "I'm unable to answer this question with the available data. "
                "The metric or dimension you're asking about is not in the current "
                "metric catalog. Please contact the DataNiks team to have it added."
            )

        return (
            "Based on the available data, I can see the following: "
            "NovaCommerce generated approximately $42M in net revenue over the "
            "analysis period, with a gross margin of 41 % and an AOV of $94. "
            "The business shows healthy growth trends with some data quality "
            "issues that require attention. For a more specific answer, please "
            "ask about a particular metric, time period, or dimension."
        )

    def _sql_for(self, q: str) -> str:
        if "revenue" in q:
            return (
                "SELECT date_trunc('month', date_id) AS month, "
                "SUM(net_revenue) AS net_revenue, "
                "SUM(gross_profit) AS gross_profit "
                "FROM main_marts.fct_orders "
                "WHERE order_status NOT IN ('cancelled', 'unknown') "
                "GROUP BY 1 ORDER BY 1"
            )
        if "refund" in q:
            return (
                "SELECT reason, COUNT(*) AS refund_count, SUM(amount) AS total_amount "
                "FROM main_staging.stg_refunds "
                "GROUP BY reason ORDER BY refund_count DESC"
            )
        if "product" in q and "margin" in q:
            return (
                "SELECT product_id, product_name, category, realised_margin_pct "
                "FROM main_marts.dim_product "
                "ORDER BY realised_margin_pct DESC LIMIT 20"
            )
        if "campaign" in q or "roas" in q:
            return (
                "SELECT campaign_name, channel, total_spend, total_attributed_revenue, roas "
                "FROM main_marts.mart_marketing "
                "ORDER BY roas DESC"
            )
        return (
            "SELECT * FROM main_marts.fct_orders LIMIT 10"
        )
