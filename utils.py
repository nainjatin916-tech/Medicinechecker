"""
MediSafe - Utilities Module
UI design helpers, custom CSS, branding elements, logo generator,
empty states, Viva demonstration notes, and academic prototype disclaimers.
"""

from pathlib import Path
from typing import Optional, Any, List
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    ACADEMIC_DISCLAIMER,
    LOGO_PATH,
    STATUS_EXPIRED,
    STATUS_EXPIRING_SOON,
    STATUS_VALID,
    VERIFIED_FOUND,
    NOT_FOUND,
    VERIFICATION_REQUIRED,
    DOSE_TAKEN,
    DOSE_SKIPPED,
    DOSE_PENDING,
)


def ensure_logo() -> Path:
    """
    Generates a professional MediSafe logo PNG image if it doesn't already exist.
    """
    if LOGO_PATH.exists():
        return LOGO_PATH

    LOGO_PATH.parent.mkdir(parents=True, exist_ok=True)
    width, height = 400, 100
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Rounded emblem background (Teal-800)
    draw.rounded_rectangle([(10, 10), (90, 90)], radius=22, fill="#0F766E")

    # Medical cross inside emblem
    draw.rounded_rectangle([(44, 25), (56, 75)], radius=5, fill="#FFFFFF")
    draw.rounded_rectangle([(25, 44), (75, 56)], radius=5, fill="#FFFFFF")

    # Pulse dot
    draw.ellipse([(47, 47), (53, 53)], fill="#14B8A6")

    try:
        font_large = ImageFont.truetype("arialbd.ttf", 38)
        font_sub = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((108, 16), "MEDISAFE", fill="#0F172A", font=font_large)
    draw.text((110, 58), "Smart Medicine Safety & Reminders", fill="#0D9488", font=font_sub)

    img.save(str(LOGO_PATH), "PNG")
    return LOGO_PATH


def apply_custom_css() -> None:
    """
    Injects custom CSS for a modern, state-of-the-art medical dashboard aesthetic.
    Features Google Font Inter, rounded elevation cards, high-contrast badges,
    and responsive tables.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Top Banner & Header */
        .medisafe-header-container {
            background: linear-gradient(135deg, #0f172a 0%, #134e4a 60%, #0f766e 100%);
            padding: 24px 30px;
            border-radius: 16px;
            color: #ffffff;
            margin-bottom: 22px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
            border-left: 6px solid #14b8a6;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .medisafe-header-title {
            font-size: 2.1rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin: 0;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .medisafe-header-subtitle {
            font-size: 1.05rem;
            color: #ccfbf1;
            font-weight: 500;
            margin: 0;
        }
        .medisafe-header-tagline {
            font-size: 0.86rem;
            color: #99f6e4;
            font-style: italic;
            opacity: 0.95;
            margin-top: 2px;
        }

        /* Metric Cards */
        .metric-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 16px 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }
        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
            color: #64748b;
        }
        .metric-icon {
            font-size: 1.25rem;
            opacity: 0.85;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            margin: 4px 0 2px 0;
            line-height: 1.2;
        }
        .metric-desc {
            font-size: 0.8rem;
            color: #94a3b8;
            font-weight: 500;
        }

        /* Status Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            font-size: 0.78rem;
            font-weight: 700;
            border-radius: 9999px;
            letter-spacing: 0.02em;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        .badge-expired {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #f87171;
        }
        .badge-expiring {
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fcd34d;
        }
        .badge-valid {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
        }
        .badge-verified {
            background-color: #dbeafe;
            color: #1e40af;
            border: 1px solid #93c5fd;
        }
        .badge-notfound {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }
        .badge-taken {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #34d399;
        }
        .badge-skipped {
            background-color: #f1f5f9;
            color: #475569;
            border: 1px solid #cbd5e1;
        }
        .badge-pending {
            background-color: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
        }

        /* Academic Disclaimer Banner */
        .disclaimer-banner {
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 14px 18px;
            border-radius: 10px;
            font-size: 0.83rem;
            color: #78350f;
            margin-top: 28px;
            margin-bottom: 16px;
            line-height: 1.5;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
        }
        .disclaimer-title {
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
            font-size: 0.88rem;
        }

        /* Viva Demonstration Note */
        .viva-box {
            background-color: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-left: 4px solid #16a34a;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 0.82rem;
            color: #14532d;
            margin: 12px 0;
        }
        .viva-title {
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }

        /* Empty State Container */
        .empty-state-box {
            text-align: center;
            padding: 36px 20px;
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 14px;
            margin: 16px 0;
        }
        .empty-state-icon {
            font-size: 2.4rem;
            margin-bottom: 8px;
        }
        .empty-state-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #334155;
            margin-bottom: 4px;
        }
        .empty-state-desc {
            font-size: 0.85rem;
            color: #64748b;
            max-width: 480px;
            margin: 0 auto;
        }

        /* Safety Alert Cards */
        .safety-alert-critical {
            background: #fff1f2;
            border: 1px solid #fecdd3;
            border-left: 5px solid #e11d48;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .safety-alert-warning {
            background: #fffbeb;
            border: 1px solid #fef3c7;
            border-left: 5px solid #f59e0b;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 10px;
        }

        /* Dose Item Card */
        .dose-item-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            transition: border-color 0.15s ease;
        }
        .dose-item-card:hover {
            border-color: #cbd5e1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: Optional[str] = None, subtitle: Optional[str] = None) -> None:
    """
    Renders the unified MediSafe top banner.
    """
    apply_custom_css()
    display_title = title or APP_NAME
    display_subtitle = subtitle or APP_SUBTITLE

    st.markdown(
        f"""
        <div class="medisafe-header-container">
            <div class="medisafe-header-title">
                🛡️ {display_title}
            </div>
            <div class="medisafe-header-subtitle">{display_subtitle}</div>
            <div class="medisafe-header-tagline">"{APP_TAGLINE}"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_academic_disclaimer() -> None:
    """
    Renders the prominent academic prototype safety disclaimer.
    """
    st.markdown(
        f"""
        <div class="disclaimer-banner">
            <div class="disclaimer-title">⚠️ ACADEMIC PROTOTYPE NOTICE & MEDICAL DISCLAIMER</div>
            <div>{ACADEMIC_DISCLAIMER}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_viva_note(title: str, explanation: str) -> None:
    """
    Renders an academic explanation note for student Viva / Examiner reference.
    """
    st.markdown(
        f"""
        <div class="viva-box">
            <div class="viva-title">🎓 Student Viva Note: {title}</div>
            <div>{explanation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, description: str, icon: str = "🔍") -> None:
    """
    Renders an aesthetically pleasing empty state when lists or tables have no records.
    """
    st.markdown(
        f"""
        <div class="empty-state-box">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_status_badge_html(status: str, extra_text: str = "") -> str:
    """
    Returns an HTML badge snippet for a given status.
    """
    text = f"{status} - {extra_text}" if extra_text else status
    status_upper = status.upper()

    if status_upper == STATUS_EXPIRED:
        cls = "badge-expired"
        icon = "⛔ "
    elif status_upper == STATUS_EXPIRING_SOON:
        cls = "badge-expiring"
        icon = "⏳ "
    elif status_upper == STATUS_VALID:
        cls = "badge-valid"
        icon = "✅ "
    elif "VERIFIED" in status_upper:
        cls = "badge-verified"
        icon = "🛡️ "
    elif "NOT FOUND" in status_upper:
        cls = "badge-notfound"
        icon = "❓ "
    elif status_upper == DOSE_TAKEN:
        cls = "badge-taken"
        icon = "✔️ "
    elif status_upper == DOSE_SKIPPED:
        cls = "badge-skipped"
        icon = "⏭️ "
    elif status_upper == DOSE_PENDING:
        cls = "badge-pending"
        icon = "🕒 "
    else:
        cls = "badge-skipped"
        icon = ""

    return f'<span class="badge {cls}">{icon}{text}</span>'


def render_metric_card(label: str, value: Any, desc: str = "", border_color: str = "#0d9488", icon: str = "📊") -> str:
    """
    Returns an HTML string for a custom metric card with an icon and top border accent.
    """
    return f"""
    <div class="metric-card" style="border-top: 3px solid {border_color};">
        <div class="metric-header">
            <span class="metric-label">{label}</span>
            <span class="metric-icon">{icon}</span>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-desc">{desc}</div>
    </div>
    """
