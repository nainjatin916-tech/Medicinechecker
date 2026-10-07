"""
MediSafe - Dashboard Logic Module
Aggregates key metrics and generates interactive Plotly visualizations
for medicine status, adherence, manufacturer distribution, and expiry forecasts.
"""

from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import fetch_all, fetch_one
from medicine import get_all_medicines
from reminder import get_today_doses
from config import (
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
    DOSE_TAKEN,
    DOSE_SKIPPED,
    DOSE_PENDING,
    DEFAULT_EXPIRING_SOON_DAYS,
)


def get_dashboard_summary_metrics(threshold_days: int = DEFAULT_EXPIRING_SOON_DAYS) -> Dict[str, Any]:
    """
    Computes all 7 core KPI metrics for the MediSafe overview cards.
    """
    medicines = get_all_medicines(threshold_days=threshold_days)
    total_meds = len(medicines)
    expired_meds = sum(1 for m in medicines if m["expiry_status"] == STATUS_EXPIRED)
    expiring_meds = sum(1 for m in medicines if m["expiry_status"] == STATUS_EXPIRING_SOON)
    valid_meds = sum(1 for m in medicines if m["expiry_status"] == STATUS_VALID)

    today_doses = get_today_doses()
    today_reminders_count = len(today_doses)
    taken_today = sum(1 for d in today_doses if d["status"] == DOSE_TAKEN)
    skipped_today = sum(1 for d in today_doses if d["status"] == DOSE_SKIPPED)
    pending_today = sum(1 for d in today_doses if d["status"] == DOSE_PENDING)

    # All-time dose metrics
    all_doses = fetch_all("SELECT status, COUNT(*) as count FROM medication_history GROUP BY status;")
    all_time_stats = {DOSE_TAKEN: 0, DOSE_SKIPPED: 0, DOSE_PENDING: 0}
    for row in all_doses:
        st_name = row["status"]
        if st_name in all_time_stats:
            all_time_stats[st_name] = row["count"]

    return {
        "total_medicines": total_meds,
        "valid_medicines": valid_meds,
        "expiring_soon_medicines": expiring_meds,
        "expired_medicines": expired_meds,
        "today_reminders": today_reminders_count,
        "today_taken": taken_today,
        "today_skipped": skipped_today,
        "today_pending": pending_today,
        "all_time_taken": all_time_stats[DOSE_TAKEN],
        "all_time_skipped": all_time_stats[DOSE_SKIPPED],
        "all_time_pending": all_time_stats[DOSE_PENDING],
    }


def create_status_distribution_chart(medicines: List[Dict[str, Any]]) -> go.Figure:
    """
    Creates a donut chart representing medicine status distribution.
    Color coded: Valid (Emerald), Expiring Soon (Amber), Expired (Rose).
    """
    counts = {
        STATUS_VALID: sum(1 for m in medicines if m["expiry_status"] == STATUS_VALID),
        STATUS_EXPIRING_SOON: sum(1 for m in medicines if m["expiry_status"] == STATUS_EXPIRING_SOON),
        STATUS_EXPIRED: sum(1 for m in medicines if m["expiry_status"] == STATUS_EXPIRED),
    }

    labels = list(counts.keys())
    values = list(counts.values())

    color_map = {
        STATUS_VALID: "#10B981",         # Emerald
        STATUS_EXPIRING_SOON: "#F59E0B",   # Amber
        STATUS_EXPIRED: "#EF4444",         # Rose / Red
    }
    colors = [color_map[lbl] for lbl in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+value+percent",
                hoverinfo="label+value+percent",
            )
        ]
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Medicine Expiry Distribution</b>", font=dict(size=15, color="#0f172a")),
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
        height=330,
    )
    return fig


def create_dose_history_chart() -> go.Figure:
    """
    Creates a bar chart illustrating medication adherence history (Taken vs Skipped vs Pending).
    """
    rows = fetch_all(
        """
        SELECT DATE(scheduled_time) as dose_date, status, COUNT(*) as count
        FROM medication_history
        GROUP BY DATE(scheduled_time), status
        ORDER BY dose_date DESC
        LIMIT 21;
        """
    )

    if not rows:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            title=dict(text="<b>Dose History (No Data Yet)</b>", font=dict(size=15, color="#0f172a")),
            height=330,
            margin=dict(t=50, b=20, l=20, r=20),
        )
        return fig

    df = pd.DataFrame(rows)
    pivot_df = df.pivot_table(index="dose_date", columns="status", values="count", fill_value=0).reset_index()

    for col in [DOSE_TAKEN, DOSE_SKIPPED, DOSE_PENDING]:
        if col not in pivot_df.columns:
            pivot_df[col] = 0

    fig = go.Figure()
    fig.add_trace(go.Bar(x=pivot_df["dose_date"], y=pivot_df[DOSE_TAKEN], name="Taken", marker_color="#10B981"))
    fig.add_trace(go.Bar(x=pivot_df["dose_date"], y=pivot_df[DOSE_SKIPPED], name="Skipped", marker_color="#94A3B8"))
    fig.add_trace(go.Bar(x=pivot_df["dose_date"], y=pivot_df[DOSE_PENDING], name="Pending", marker_color="#F59E0B"))

    fig.update_layout(
        template="plotly_white",
        barmode="stack",
        title=dict(text="<b>Dose Adherence by Date</b>", font=dict(size=15, color="#0f172a")),
        xaxis_title="Date",
        yaxis_title="Doses",
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=330,
    )
    return fig


def create_manufacturer_chart(medicines: List[Dict[str, Any]]) -> go.Figure:
    """
    Creates a horizontal bar chart of medicines by manufacturer.
    """
    mfg_counts: Dict[str, int] = {}
    for m in medicines:
        mfg = m.get("manufacturer") or "Unknown"
        mfg_counts[mfg] = mfg_counts.get(mfg, 0) + 1

    sorted_mfgs = sorted(mfg_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [x[0] for x in sorted_mfgs]
    values = [x[1] for x in sorted_mfgs]

    fig = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker=dict(color="#0F766E", line=dict(color="#115E59", width=1)),
            )
        ]
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Medicines by Manufacturer</b>", font=dict(size=15, color="#0f172a")),
        xaxis_title="Count",
        yaxis=dict(autorange="reversed"),
        margin=dict(t=50, b=20, l=20, r=20),
        height=330,
    )
    return fig


def create_upcoming_expiry_timeline(medicines: List[Dict[str, Any]]) -> go.Figure:
    """
    Creates a sorted bar chart showing days remaining for valid and expiring-soon medicines.
    """
    non_expired = [m for m in medicines if m["expiry_status"] != STATUS_EXPIRED]
    non_expired.sort(key=lambda x: x["days_remaining"])
    subset = non_expired[:10]  # Next 10 expiring

    if not subset:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            title=dict(text="<b>Upcoming Expiry Timeline (No Active Medicines)</b>", font=dict(size=15, color="#0f172a")),
            height=330,
        )
        return fig

    names = [f"{m['medicine_name']} ({m['batch_number']})" for m in subset]
    days = [m["days_remaining"] for m in subset]
    colors = ["#F59E0B" if m["expiry_status"] == STATUS_EXPIRING_SOON else "#14B8A6" for m in subset]

    fig = go.Figure(
        data=[
            go.Bar(
                x=days,
                y=names,
                orientation="h",
                marker=dict(color=colors),
                text=[f"{d} days" for d in days],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>Nearest Upcoming Expiries (Days Remaining)</b>", font=dict(size=15, color="#0f172a")),
        xaxis_title="Days Until Expiry",
        yaxis=dict(autorange="reversed"),
        margin=dict(t=50, b=20, l=20, r=20),
        height=330,
    )
    return fig
