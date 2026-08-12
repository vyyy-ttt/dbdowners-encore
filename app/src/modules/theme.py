# Shared presentation helpers for the desktop layout.
#
# The palette itself lives in .streamlit/config.toml. This module only adds the
# things Streamlit's theme options cannot express: card surfaces, the KPI tile
# grid, tag chips, and the page header bar from the wireframes.
#
# Call apply_theme() once, right after SideBarLinks(), on any page that wants
# this look. Pages that do not call it are unaffected.

import streamlit as st

VIOLET = "#7C4DFF"
VIOLET_DARK = "#5B2BD9"
INK = "#191A2C"
MUTED = "#6B6C85"
BORDER = "#E7E7F2"

_CSS = f"""
<style>
  /* Wider, breathing-room content column. This is a desktop layout. */
  .block-container {{
      padding-top: 2.2rem;
      padding-bottom: 4rem;
      max-width: 1500px;
  }}

  /* ---- Page header bar ---- */
  .enc-header {{
      display: flex;
      align-items: baseline;
      gap: 0.85rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid {BORDER};
      margin-bottom: 0.4rem;
  }}
  .enc-brand {{
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: {VIOLET};
  }}
  .enc-divider {{
      color: {BORDER};
      font-size: 1.5rem;
      font-weight: 300;
  }}
  .enc-title {{
      font-size: 1.35rem;
      font-weight: 700;
      color: {INK};
  }}
  .enc-welcome {{
      color: {MUTED};
      font-size: 0.95rem;
      margin: 0 0 1.6rem 0;
  }}

  /* ---- Section labels ---- */
  .enc-section {{
      font-size: 1.05rem;
      font-weight: 700;
      color: {INK};
      margin: 0.4rem 0 0.9rem 0;
  }}

  /* ---- KPI tiles ---- */
  .enc-tile {{
      background: #FFFFFF;
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 1.05rem 1.15rem;
      height: 100%;
      box-shadow: 0 1px 2px rgba(25, 26, 44, 0.04);
  }}
  .enc-tile-label {{
      font-size: 0.8rem;
      font-weight: 600;
      color: {MUTED};
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 0.35rem;
  }}
  .enc-tile-value {{
      font-size: 2.1rem;
      font-weight: 800;
      line-height: 1.1;
      color: {VIOLET};
      letter-spacing: -0.02em;
  }}
  .enc-tile-value.enc-empty {{ color: #C7C8D8; }}
  /* Text values (a category name) need a smaller size than a bare number. */
  .enc-tile-value.enc-text {{
      font-size: 1.32rem;
      line-height: 1.25;
      padding-top: 0.3rem;
  }}
  .enc-tile-sub {{
      font-size: 0.8rem;
      color: {MUTED};
      margin-top: 0.3rem;
  }}

  /* ---- Meter rows (ratings by category) ---- */
  .enc-meter-row {{
      display: grid;
      grid-template-columns: 150px 1fr 46px;
      align-items: center;
      gap: 0.85rem;
      margin-bottom: 0.7rem;
  }}
  .enc-meter-name {{ font-size: 0.9rem; color: {INK}; font-weight: 500; }}
  .enc-meter-track {{
      background: #EFEFF6;
      border-radius: 999px;
      height: 10px;
      overflow: hidden;
  }}
  .enc-meter-fill {{
      background: linear-gradient(90deg, {VIOLET} 0%, {VIOLET_DARK} 100%);
      height: 100%;
      border-radius: 999px;
  }}
  .enc-meter-value {{
      font-size: 0.9rem;
      font-weight: 700;
      color: {VIOLET};
      text-align: right;
  }}
  .enc-meter-value.enc-empty {{ color: #C7C8D8; font-weight: 500; }}

  /* ---- Cards (reviews) ---- */
  .enc-card {{
      background: #FFFFFF;
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 1.1rem 1.25rem 0.4rem 1.25rem;
      margin-bottom: 0.5rem;
      box-shadow: 0 1px 2px rgba(25, 26, 44, 0.04);
  }}
  .enc-card-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.5rem;
  }}
  .enc-stars {{ color: {VIOLET}; font-size: 1.05rem; letter-spacing: 0.08em; }}
  .enc-rating {{ color: {MUTED}; font-size: 0.85rem; margin-left: 0.4rem; }}
  .enc-meta {{ color: {MUTED}; font-size: 0.85rem; }}
  .enc-quote {{
      color: {INK};
      font-size: 0.97rem;
      line-height: 1.55;
      margin: 0.1rem 0 0.6rem 0;
  }}

  /* ---- Chips ---- */
  .enc-chip {{
      display: inline-block;
      background: #F0EBFF;
      color: {VIOLET_DARK};
      border-radius: 999px;
      padding: 0.18rem 0.7rem;
      font-size: 0.78rem;
      font-weight: 600;
      margin-right: 0.35rem;
  }}
  .enc-chip-grey {{ background: #F1F1F6; color: {MUTED}; }}

  /* ---- Replies ---- */
  .enc-reply {{
      border-left: 3px solid {VIOLET};
      background: #FAF8FF;
      border-radius: 0 10px 10px 0;
      padding: 0.6rem 0.9rem;
      margin: 0.2rem 0 0.7rem 0;
      font-size: 0.9rem;
      color: {INK};
  }}
  .enc-reply-vm {{ border-left-color: #9FA1BC; background: #F7F7FB; }}
  .enc-reply-label {{
      font-weight: 700;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: {MUTED};
      display: block;
      margin-bottom: 0.15rem;
  }}

  /* Tighten Streamlit's default gaps so cards sit closer together. */
  div[data-testid="stVerticalBlock"] > div:has(> .enc-card) {{ gap: 0; }}

  /* Sidebar: centre the logo and give the nav more air. */
  section[data-testid="stSidebar"] div[data-testid="stImage"] {{
      display: flex;
      justify-content: center;
      margin: 0.4rem 0 0.1rem 0;
  }}
  section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"],
  section[data-testid="stSidebar"] .stPageLink a {{
      border-radius: 10px;
  }}
</style>
"""


def apply_theme():
    """Inject the shared CSS. Safe to call once per page render."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title, welcome=None):
    """The 'Encore | <title>' bar from the wireframes."""
    st.markdown(
        f"""
        <div class="enc-header">
          <span class="enc-brand">Encore</span>
          <span class="enc-divider">|</span>
          <span class="enc-title">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if welcome:
        st.markdown(f'<p class="enc-welcome">{welcome}</p>', unsafe_allow_html=True)


def tile(label, value, sub=None, empty=False, text_value=False):
    """A KPI tile.

    empty=True greys the value out for a 'no data yet' state. text_value=True
    drops the font size, for values that are words rather than a number.
    """
    classes = "enc-tile-value"
    if empty:
        classes += " enc-empty"
    if text_value:
        classes += " enc-text"
    sub_html = f'<div class="enc-tile-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="enc-tile">
          <div class="enc-tile-label">{label}</div>
          <div class="{classes}">{value}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def meter(name, value, out_of=5.0):
    """A labelled 0 to 5 bar, as in the wireframes' 'Ratings by Category'."""
    if value is None:
        st.markdown(
            f"""
            <div class="enc-meter-row">
              <div class="enc-meter-name">{name}</div>
              <div class="enc-meter-track"></div>
              <div class="enc-meter-value enc-empty">n/a</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    pct = max(0.0, min(100.0, (value / out_of) * 100.0))
    st.markdown(
        f"""
        <div class="enc-meter-row">
          <div class="enc-meter-name">{name}</div>
          <div class="enc-meter-track">
            <div class="enc-meter-fill" style="width: {pct:.1f}%"></div>
          </div>
          <div class="enc-meter-value">{value:.1f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stars(rating):
    """Filled/empty star string for a 1 to 5 rating."""
    if rating is None:
        return '<span class="enc-meta">unrated</span>'
    filled = max(0, min(5, int(rating)))
    return (
        f'<span class="enc-stars">{"★" * filled}{"☆" * (5 - filled)}</span>'
        f'<span class="enc-rating">{filled}/5</span>'
    )


def chip(text, grey=False):
    css = "enc-chip enc-chip-grey" if grey else "enc-chip"
    return f'<span class="{css}">{text}</span>'


def section(text):
    st.markdown(f'<div class="enc-section">{text}</div>', unsafe_allow_html=True)
