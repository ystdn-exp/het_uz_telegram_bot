from uuid import UUID
from typing import Any, Optional
from datetime import datetime
from httpx import AsyncClient

from src.services.het import het_service


def _get_account_link(telegram_user, account_id: UUID):
    """Helper to find account link for a user."""
    for link in telegram_user.users:
        if link.user.id == account_id:
            return link
    return None


async def _process_yearly_data(client: AsyncClient, access_token: str, year: int):
    """Fetch and process yearly consumption data (monthly aggregates)."""
    labels, values = [], []
    data, status = await het_service.get_monthly_consumption(client, access_token, year)

    if status == 200:
        raw_data = data.get("data")
        items = raw_data if isinstance(raw_data, list) else []

        # Aggregate values by month
        aggregated = {}
        for item in items:
            raw_label = item.get("period") or item.get("month") or item.get("date")
            label = _format_yearly_label(raw_label)
            if label:
                value = (
                    item.get("totalCalcKwh")
                    or item.get("consumption")
                    or item.get("calculateKwh")
                    or 0
                )
                # Convert Wh to kWh by dividing by 1000
                aggregated[label] = aggregated.get(label, 0) + (float(value) / 1000)

        # Define month order for sorting
        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        month_order = {m: i for i, m in enumerate(months)}

        # Sort by month order
        sorted_keys = sorted(aggregated.keys(), key=lambda x: month_order.get(x, 99))
        for k in sorted_keys:
            labels.append(k)
            values.append(aggregated[k])

    return labels, values


def _format_yearly_label(raw_label: Any) -> Optional[str]:
    """Format yearly/monthly data labels into readable month names."""
    if not raw_label:
        return None

    str_label = str(raw_label)
    if "-" in str_label:
        try:
            dt = datetime.strptime(str_label.split(" ")[0], "%Y-%m-%d")
            return dt.strftime("%b")
        except Exception:
            return str_label
    elif str_label.isdigit():
        try:
            month_idx = int(str_label)
            return datetime(2000, month_idx, 1).strftime("%b")
        except Exception:
            return str_label
    return str_label


async def _process_reading_based_data(
    client: AsyncClient, access_token: str, period: str
):
    """Fetch and process daily/weekly/monthly consumption data from readings."""
    labels, values = [], []
    # Fetch enough records for the period (Today: 2, Weekly: 8, Monthly: 32)
    size = 2 if period == "today" else (8 if period == "weekly" else 35)
    data, status = await het_service.get_reading_histories(
        client, access_token, size=size
    )

    if status == 200:
        # Based on HET API structure: {"content": [...]}
        items = data.get("content", [])
        if len(items) >= 2:
            for i in range(len(items) - 1):
                label, consumption = _calculate_consumption(items[i], items[i + 1])
                if label and consumption is not None:
                    labels.append(label)
                    values.append(consumption)

            limit = 1 if period == "today" else (7 if period == "weekly" else 30)
            labels = labels[:limit]
            values = values[:limit]
            labels.reverse()
            values.reverse()

    return labels, values


def _calculate_consumption(current_item: dict, prev_item: dict) -> tuple[str, float]:
    """Calculate consumption between two readings and format label."""
    try:
        current_val = current_item.get("readingAPlus")
        prev_val = prev_item.get("readingAPlus")
        date_str = current_item.get("readingDate")

        if current_val is None or prev_val is None:
            return None, None

        consumption = float(current_val) - float(prev_val)
        if consumption < 0:
            consumption = 0

        if date_str:
            try:
                dt = datetime.strptime(str(date_str).split(" ")[0], "%Y-%m-%d")
                label = dt.strftime("%d.%m")
            except Exception:
                label = str(date_str)
        else:
            label = "???"

        return label, consumption
    except (ValueError, TypeError):
        return None, None


async def process_chart_data(
    client: AsyncClient, period: str, access_token: str, _
) -> tuple[dict, str]:
    """
    Helper to fetch and format data for charts based on HET API response.
    """
    title = ""

    if period == "today":
        title = _("Today Consumption")
    elif period == "weekly":
        title = _("Weekly Consumption")
    elif period == "monthly":
        title = _("Monthly Consumption")

    if period == "yearly":
        # Fallback - main flow uses select_year_callback
        labels, values = await _process_yearly_data(
            client, access_token, datetime.now().year
        )
    elif period in ["today", "weekly", "monthly"]:
        labels, values = await _process_reading_based_data(client, access_token, period)
    else:
        labels, values = [], []

    # Fallback if no data found
    if not labels:
        data, status = await het_service.get_consumer_state(client, access_token)
        if status == 200:
            raw_data = data.get("data", {})
            usage = raw_data.get("currentMonthCalcKwh") or raw_data.get("usage")
            if usage is not None:
                labels = ["Current Mo"]
                values = [float(usage)]

    return {"labels": labels, "values": values}, title


def _format_payments_history(data: dict, _) -> str:
    """Helper to format payment history text."""
    payments_text = _("💳 <b>Payment History</b>\n\n")
    payments = data.get("content", [])

    if not payments:
        payments_text += _("<i>No payment records found for this account.</i>")
    else:
        for payment in payments:
            date = payment.get("paymentDate", "N/A")
            amount = payment.get("paymentAmount", 0)
            pay_type = payment.get("paymentType", {}).get("name") or "Unknown"
            purpose = payment.get("householdPaymentPurpose", {}).get("name") or _(
                "Electricity"
            )

            # Format with two decimal places and thousands separator
            display_amount = float(amount) / 100
            formatted_amount = "{:,.2f}".format(display_amount).replace(",", " ")

            payments_text += (
                f"📅 <b>{date}</b>\n"
                f"💰 {formatted_amount} UZS\n"
                f"🔌 {purpose} ({pay_type})\n"
                "-------------------\n"
            )
    return payments_text
