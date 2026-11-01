"""
generate_dashboard.py - Renders the GitHub Profile Dashboard as a pixel-perfect, GitHub README-compatible SVG.
Includes horizontal stacked language bar, 12-week heatmap, stat cards, circular progress, and recent activities.
"""

import json
import xml.sax.saxutils as saxutils
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_PATH = BASE_DIR / "config" / "profile.json"


def escape(text):
    return saxutils.escape(str(text)) if text is not None else ""


# Inline SVG icons
ICONS = {
    "commit": '<path fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z" fill="#8b949e"/>',
    "pull_request": '<path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.128a2.251 2.251 0 11-1.5 0V6.5a2.5 2.5 0 00-2.5-2.5h-1V2.5z" fill="#8b949e"/>',
    "repo": '<path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1h-8a1 1 0 00-1 1v6.708A2.486 2.486 0 014.5 9h8V1.5zM5 12.25a.25.25 0 01.25-.25H12v1.5H5.25a.25.25 0 01-.25-.25z" fill="#8b949e"/>',
    "branch": '<path fill-rule="evenodd" d="M11.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122V6A2.5 2.5 0 0110 8.5H6a1 1 0 00-1 1v1.128a2.251 2.251 0 11-1.5 0V5.372a2.25 2.25 0 111.5 0v1.836A2.492 2.492 0 016 7h4a1 1 0 001-1v-.628A2.25 2.25 0 019.5 3.25z" fill="#8b949e"/>',
    "linkedin": '<path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" fill="#8b949e"/>',
    "email": '<path d="M1.75 2A1.75 1.75 0 000 3.75v.736l9 5.25 9-5.25v-.736A1.75 1.75 0 0016.25 2H1.75zM18 6.014l-9 5.25-9-5.25V14.25c0 .966.784 1.75 1.75 1.75h14.5A1.75 1.75 0 0018 14.25V6.014z" fill="#8b949e"/>',
    "instagram": '<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" fill="#8b949e"/>',
    "github": '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" fill="#8b949e"/>'
}


def generate_svg(stats=None):
    if not stats:
        processed_path = DATA_DIR / "processed_stats.json"
        if not processed_path.exists():
            raise FileNotFoundError(f"Processed stats file {processed_path} not found.")
        with open(processed_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

    labels = stats.get("labels", {})
    profile = stats.get("profile", {})
    card1 = stats.get("card1_last_active", {})
    card2 = stats.get("card2_month_contributions", {})
    card3 = stats.get("card3_year_contributions", {})
    card4 = stats.get("card4_recent_repo", {})
    languages = stats.get("languages", [])
    heatmap = stats.get("heatmap", {})
    recent_activities = stats.get("recent_activities", [])
    social_links = profile.get("social_links", {})

    # Circular donut calculations for Card 3
    # Radius = 24, Circumference = 2 * pi * 24 = 150.796
    circumference = 150.8
    pct = min(100, max(0, card3.get("percentage", 0)))
    dashoffset = circumference * (1.0 - (pct / 100.0))

    # SVG layout dimensions
    width = 940
    height = 824

    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">')

    # CSS Styles
    svg_parts.append("""
  <style>
    .font-main { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif; }
    .bg-canvas { fill: #0d1117; }
    .card-bg { fill: #161b22; stroke: #30363d; stroke-width: 1px; }
    .text-title { fill: #f0f6fc; font-weight: 700; }
    .text-subtitle { fill: #8b949e; font-weight: 400; }
    .text-label { fill: #8b949e; font-size: 13px; font-weight: 400; }
    .text-stat { fill: #f0f6fc; font-weight: 700; }
    .badge-pill { fill: #161b22; stroke: #30363d; stroke-width: 1px; }
    .badge-text { fill: #c9d1d9; font-size: 12px; font-weight: 500; }
    .collab-pill { fill: #13231b; stroke: #238636; stroke-width: 1px; }
    .collab-text { fill: #3fb950; font-size: 12px; font-weight: 600; }
    .divider { stroke: #21262d; stroke-width: 1px; }
    .legend-item { font-size: 13px; fill: #c9d1d9; font-weight: 500; }
    .legend-pct { font-size: 13px; fill: #8b949e; font-weight: 600; }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.4; }
      100% { opacity: 1; }
    }
    .pulse-dot { animation: pulse 2.5s infinite ease-in-out; }
  </style>
""")

    # Layout definitions
    mid_y = 244
    mid_h = 352
    col_w = (width - 24 * 2 - 16) // 2  # 438px each
    col1_x = 24
    col2_x = col1_x + col_w + 16

    bar_x = col1_x + 24
    bar_y = mid_y + 60
    bar_total_w = col_w - 48  # 390px
    bar_h = 16

    # Defs
    svg_parts.append("  <defs>")
    # Avatar clip path
    svg_parts.append('    <clipPath id="avatar-clip"><circle cx="52" cy="56" r="26"/></clipPath>')
    # Stacked language bar clip path (smooth rounded outer corners)
    svg_parts.append(f'    <clipPath id="lang-bar-clip"><rect x="{bar_x}" y="{bar_y}" width="{bar_total_w}" height="{bar_h}" rx="8"/></clipPath>')
    svg_parts.append("  </defs>")

    # Canvas Background
    svg_parts.append(f'  <rect width="{width}" height="{height}" rx="16" class="bg-canvas" stroke="#30363d" stroke-width="1"/>')

    # =========================================================================
    # SECTION A: PROFILE HEADER
    # =========================================================================
    avatar_b64 = profile.get("avatar_base64")
    if avatar_b64:
        svg_parts.append(f'  <image href="{avatar_b64}" x="26" y="30" width="52" height="52" clip-path="url(#avatar-clip)"/>')
    else:
        # Fallback circle avatar with initials ZA
        svg_parts.append('  <circle cx="52" cy="56" r="26" fill="#09325c" stroke="#1f6feb" stroke-width="1"/>')
        svg_parts.append('  <text x="52" y="63" text-anchor="middle" fill="#58a6ff" font-size="16" font-weight="700" class="font-main">ZA</text>')

    # Display Name & Username
    name_str = escape(profile.get("display_name") or profile.get("username", "Zakkyaulia"))
    subtitle_str = escape(profile.get("subtitle", ""))
    svg_parts.append(f'  <text x="92" y="50" font-size="20" class="font-main text-title">{name_str}</text>')
    svg_parts.append(f'  <text x="92" y="70" font-size="13" class="font-main text-subtitle">{subtitle_str}</text>')

    # Collaboration Availability Badge
    if profile.get("collaboration_available", True):
        status_text = escape(profile.get("collaboration_status", "Terbuka untuk kolaborasi"))
        # Pill width dynamically estimated
        badge_w = max(170, len(status_text) * 8 + 42)
        badge_x = width - 24 - badge_w - 36
        svg_parts.append(f'  <rect x="{badge_x}" y="40" width="{badge_w}" height="32" rx="16" class="collab-pill"/>')
        svg_parts.append(f'  <circle cx="{badge_x + 18}" cy="56" r="4.5" fill="#3fb950" class="pulse-dot"/>')
        svg_parts.append(f'  <text x="{badge_x + 30}" y="61" class="font-main collab-text">{status_text}</text>')

    # Top right 3-dot decoration
    dots_x = width - 42
    svg_parts.append(f'  <circle cx="{dots_x}" cy="56" r="2" fill="#8b949e"/>')
    svg_parts.append(f'  <circle cx="{dots_x + 7}" cy="56" r="2" fill="#8b949e"/>')
    svg_parts.append(f'  <circle cx="{dots_x + 14}" cy="56" r="2" fill="#8b949e"/>')

    # =========================================================================
    # SECTION B: FOUR STATISTIC CARDS
    # =========================================================================
    # Desktop 4-card row
    card_y = 104
    card_h = 124
    card_w = 212
    card_gap = 14
    start_x = 24

    # Card 1: Last Active
    c1_x = start_x
    c1_title = escape(labels.get("last_active_title", "Terakhir aktif"))
    c1_val = escape(card1.get("value", "—"))
    c1_sub = escape(card1.get("subtitle", "aktivitas publik terbaru"))
    svg_parts.append(f'  <!-- Card 1: Last Active -->')
    svg_parts.append(f'  <rect x="{c1_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="12" class="card-bg"/>')
    svg_parts.append(f'  <text x="{c1_x + 18}" y="{card_y + 30}" class="font-main text-label">{c1_title}</text>')
    svg_parts.append(f'  <text x="{c1_x + 18}" y="{card_y + 68}" font-size="24" class="font-main text-stat">{c1_val}</text>')
    svg_parts.append(f'  <text x="{c1_x + 18}" y="{card_y + 98}" font-size="12" class="font-main text-subtitle">{c1_sub}</text>')

    # Card 2: Contributions This Month
    c2_x = c1_x + card_w + card_gap
    c2_title = escape(labels.get("month_contributions_title", "Kontribusi bulan ini"))
    c2_val = escape(card2.get("value", "0"))
    c2_sub = escape(card2.get("subtitle", "total sejak awal bulan"))
    svg_parts.append(f'  <!-- Card 2: Contributions This Month -->')
    svg_parts.append(f'  <rect x="{c2_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="12" class="card-bg"/>')
    svg_parts.append(f'  <text x="{c2_x + 18}" y="{card_y + 30}" class="font-main text-label">{c2_title}</text>')
    svg_parts.append(f'  <text x="{c2_x + 18}" y="{card_y + 68}" font-size="28" class="font-main text-stat">{c2_val}</text>')
    svg_parts.append(f'  <text x="{c2_x + 18}" y="{card_y + 98}" font-size="12" class="font-main text-subtitle">{c2_sub}</text>')

    # Card 3: Contributions This Year (with circular donut progress)
    c3_x = c2_x + card_w + card_gap
    c3_title = escape(labels.get("year_contributions_title", "Kontribusi tahun ini"))
    c3_donut_cx = c3_x + 46
    c3_donut_cy = card_y + 70
    raw_sub = labels.get("year_contributions_sub", "dari seluruh\nkontribusi")
    c3_sub_lines = raw_sub.replace("\\n", "\n").split("\n")
    svg_parts.append(f'  <!-- Card 3: Contributions This Year -->')
    svg_parts.append(f'  <rect x="{c3_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="12" class="card-bg"/>')
    svg_parts.append(f'  <text x="{c3_x + 18}" y="{card_y + 30}" class="font-main text-label">{c3_title}</text>')
    # Donut Background track
    svg_parts.append(f'  <circle cx="{c3_donut_cx}" cy="{c3_donut_cy}" r="24" stroke="#21262d" stroke-width="5" fill="none"/>')
    # Donut Progress arc
    svg_parts.append(f'  <circle cx="{c3_donut_cx}" cy="{c3_donut_cy}" r="24" stroke="#388bfd" stroke-width="5" stroke-linecap="round" fill="none" stroke-dasharray="{circumference}" stroke-dashoffset="{dashoffset:.2f}" transform="rotate(-90 {c3_donut_cx} {c3_donut_cy})"/>')
    # Percentage text in center
    svg_parts.append(f'  <text x="{c3_donut_cx}" y="{c3_donut_cy + 5}" text-anchor="middle" font-size="13" font-weight="700" class="font-main text-stat">{pct}%</text>')
    # Subtitle beside donut
    sub_y = card_y + 66
    for line in c3_sub_lines:
        svg_parts.append(f'  <text x="{c3_x + 86}" y="{sub_y}" font-size="12" class="font-main text-subtitle">{escape(line)}</text>')
        sub_y += 16

    # Card 4: Recently Updated Repository
    c4_x = c3_x + card_w + card_gap
    c4_title = escape(labels.get("recent_repo_title", "Repo terakhir diperbarui"))
    c4_repo = escape(card4.get("name", "—"))
    c4_lang = escape(card4.get("language", "None"))
    c4_color = escape(card4.get("language_color", "#8b949e"))
    c4_time = escape(card4.get("relative_time", "—"))
    svg_parts.append(f'  <!-- Card 4: Recently Updated Repository -->')
    svg_parts.append(f'  <rect x="{c4_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="12" class="card-bg"/>')
    svg_parts.append(f'  <text x="{c4_x + 18}" y="{card_y + 30}" class="font-main text-label">{c4_title}</text>')
    svg_parts.append(f'  <text x="{c4_x + 18}" y="{card_y + 66}" font-size="18" class="font-main text-stat">{c4_repo}</text>')
    # Language dot + info
    svg_parts.append(f'  <circle cx="{c4_x + 22}" cy="{card_y + 94}" r="4.5" fill="{c4_color}"/>')
    svg_parts.append(f'  <text x="{c4_x + 32}" y="{card_y + 98}" font-size="12" class="font-main text-subtitle">{c4_lang} · {c4_time}</text>')

    # =========================================================================
    # SECTION C & D: PROGRAMMING LANGUAGES & 12-WEEK HEATMAP
    # =========================================================================

    # --- SECTION C: PROGRAMMING LANGUAGES (LAST 3 MONTHS) ---
    svg_parts.append(f'  <!-- SECTION C: Programming Languages Stacked Bar -->')
    svg_parts.append(f'  <rect x="{col1_x}" y="{mid_y}" width="{col_w}" height="{mid_h}" rx="12" class="card-bg"/>')
    lang_title = escape(labels.get("languages_title", "Bahasa yang dipakai, 3 bulan terakhir"))
    svg_parts.append(f'  <text x="{col1_x + 24}" y="{mid_y + 36}" font-size="15" font-weight="600" class="font-main text-title">{lang_title}</text>')

    # Render segments inside clip-path
    svg_parts.append(f'  <g clip-path="url(#lang-bar-clip)">')
    # Background full bar in case of 0%
    svg_parts.append(f'    <rect x="{bar_x}" y="{bar_y}" width="{bar_total_w}" height="{bar_h}" fill="#21262d"/>')
    current_seg_x = bar_x
    for lang in languages:
        seg_pct = lang.get("percentage", 0)
        if seg_pct > 0:
            seg_w = (seg_pct / 100.0) * bar_total_w
            seg_color = lang.get("color", "#8b949e")
            svg_parts.append(f'    <rect x="{current_seg_x:.2f}" y="{bar_y}" width="{seg_w:.2f}" height="{bar_h}" fill="{seg_color}"/>')
            current_seg_x += seg_w
    svg_parts.append(f'  </g>')

    # Stacked Bar Outer Stroke
    svg_parts.append(f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_total_w}" height="{bar_h}" rx="7" fill="none" stroke="#30363d" stroke-width="1"/>')

    # Legend Below the Bar
    # Elegantly structured with colored dot, language name, and percentage
    legend_start_y = bar_y + 44
    for i, lang in enumerate(languages):
        item_y = legend_start_y + (i * 44)
        lang_name = escape(lang.get("name", ""))
        lang_color = escape(lang.get("color", "#8b949e"))
        lang_pct = lang.get("percentage", 0)
        lang_lines = lang.get("count", 0)

        # Colored circular indicator
        svg_parts.append(f'  <circle cx="{bar_x + 8}" cy="{item_y - 4}" r="5" fill="{lang_color}"/>')
        # Language Name
        svg_parts.append(f'  <text x="{bar_x + 24}" y="{item_y}" class="font-main legend-item">{lang_name}</text>')
        # Right aligned percentage & lines
        svg_parts.append(f'  <text x="{bar_x + bar_total_w}" y="{item_y}" text-anchor="end" class="font-main legend-pct">{lang_pct}%</text>')
        # Subtle horizontal divider between legend items (except last)
        if i < len(languages) - 1:
            svg_parts.append(f'  <line x1="{bar_x}" y1="{item_y + 16}" x2="{bar_x + bar_total_w}" y2="{item_y + 16}" class="divider"/>')

    # --- SECTION D: CONTRIBUTION HEATMAP (LAST 12 WEEKS) ---
    svg_parts.append(f'  <!-- SECTION D: 12-Week Contribution Heatmap -->')
    svg_parts.append(f'  <rect x="{col2_x}" y="{mid_y}" width="{col_w}" height="{mid_h}" rx="12" class="card-bg"/>')
    heat_title = escape(labels.get("activity_title", "Aktivitas 12 minggu"))
    svg_parts.append(f'  <text x="{col2_x + 24}" y="{mid_y + 36}" font-size="15" font-weight="600" class="font-main text-title">{heat_title}</text>')

    # Heatmap Grid: 12 columns x 7 rows
    sq_size = 23
    sq_gap = 7
    weeks_list = heatmap.get("weeks", [])
    month_cols = heatmap.get("month_columns", {})
    grid_total_w = 12 * sq_size + 11 * sq_gap  # 276 + 77 = 353px
    grid_start_x = col2_x + 24 + (col_w - 48 - grid_total_w) // 2
    grid_start_y = mid_y + 84

    # Month Labels Row
    # Place month labels above the columns
    for col_str, m_name in month_cols.items():
        try:
            col_idx = int(col_str)
            if col_idx < 12:
                m_x = grid_start_x + col_idx * (sq_size + sq_gap)
                svg_parts.append(f'  <text x="{m_x}" y="{grid_start_y - 12}" font-size="12" class="font-main text-subtitle">{escape(m_name)}</text>')
        except ValueError:
            pass

    # Heatmap Color Palette
    HEAT_COLORS = {
        0: "#21262d",
        1: "#0e4429",
        2: "#006d32",
        3: "#26a641",
        4: "#39d353"
    }

    # Draw Squares
    for c_idx, week in enumerate(weeks_list[:12]):
        col_x = grid_start_x + c_idx * (sq_size + sq_gap)
        for r_idx, day_info in enumerate(week[:7]):
            row_y = grid_start_y + r_idx * (sq_size + sq_gap)
            lvl = day_info.get("level", 0)
            sq_fill = HEAT_COLORS.get(lvl, "#21262d")
            # If future day, show subtle dotted/empty
            if day_info.get("is_future"):
                sq_fill = "#161b22"
            svg_parts.append(f'  <rect x="{col_x}" y="{row_y}" width="{sq_size}" height="{sq_size}" rx="4" fill="{sq_fill}"/>')

    # Heatmap Bottom Summary & Legend
    bottom_y = grid_start_y + 7 * (sq_size + sq_gap) + 18
    active_weeks_txt = escape(heatmap.get("active_weeks_text", "Aktif 6 dari 12 minggu"))
    svg_parts.append(f'  <text x="{grid_start_x}" y="{bottom_y + 10}" font-size="12" class="font-main text-subtitle">{active_weeks_txt}</text>')

    # Legend on right side: Sedikit [■ ■ ■ ■ ■] Banyak
    legend_right_x = grid_start_x + grid_total_w
    less_txt = escape(labels.get("less", "Sedikit"))
    more_txt = escape(labels.get("more", "Banyak"))

    # Compute positions from right to left
    more_w = len(more_txt) * 7
    less_w = len(less_txt) * 7
    squares_w = 5 * 11 + 4 * 4  # 55 + 16 = 71px

    leg_start_x = legend_right_x - (more_w + squares_w + less_w + 16)
    svg_parts.append(f'  <text x="{leg_start_x}" y="{bottom_y + 10}" font-size="12" class="font-main text-subtitle">{less_txt}</text>')

    cur_lsq_x = leg_start_x + less_w + 6
    for lvl in range(5):
        svg_parts.append(f'  <rect x="{cur_lsq_x}" y="{bottom_y}" width="11" height="11" rx="2" fill="{HEAT_COLORS[lvl]}"/>')
        cur_lsq_x += 15

    svg_parts.append(f'  <text x="{cur_lsq_x + 4}" y="{bottom_y + 10}" font-size="12" class="font-main text-subtitle">{more_txt}</text>')

    # =========================================================================
    # SECTION E: RECENT ACTIVITIES
    # =========================================================================
    act_y = 612
    act_h = 138
    act_w = width - 48
    act_x = 24

    svg_parts.append(f'  <!-- SECTION E: Recent Activities -->')
    svg_parts.append(f'  <rect x="{act_x}" y="{act_y}" width="{act_w}" height="{act_h}" rx="12" class="card-bg"/>')
    act_title = escape(labels.get("recent_activities_title", "Aktivitas terbaru"))
    svg_parts.append(f'  <text x="{act_x + 20}" y="{act_y + 26}" font-size="14" font-weight="600" class="font-main text-title">{act_title}</text>')

    for i, act in enumerate(recent_activities[:3]):
        row_y = act_y + 42 + (i * 30)
        action_desc = escape(act.get("action", ""))
        repo_name = escape(act.get("repo", ""))
        rel_time = escape(act.get("relative_time", ""))
        icon_name = act.get("icon", "commit")
        icon_svg = ICONS.get(icon_name, ICONS["commit"])

        # Icon wrapper
        svg_parts.append(f'  <g transform="translate({act_x + 20}, {row_y}) scale(0.9)">{icon_svg}</g>')
        # Action Description + Repo Name
        if repo_name and repo_name != "—":
            svg_parts.append(f'  <text x="{act_x + 44}" y="{row_y + 12}" font-size="13" class="font-main text-title">{action_desc} <tspan font-weight="400" fill="#8b949e">· {repo_name}</tspan></text>')
        else:
            svg_parts.append(f'  <text x="{act_x + 44}" y="{row_y + 12}" font-size="13" class="font-main text-title">{action_desc}</text>')
        # Relative time (right-aligned)
        svg_parts.append(f'  <text x="{act_x + act_w - 20}" y="{row_y + 12}" text-anchor="end" font-size="12" class="font-main text-subtitle">{rel_time}</text>')
        # Divider between rows
        if i < 2:
            svg_parts.append(f'  <line x1="{act_x + 20}" y1="{row_y + 22}" x2="{act_x + act_w - 20}" y2="{row_y + 22}" class="divider"/>')

    # =========================================================================
    # SECTION F: SOCIAL LINKS PILL BADGES
    # =========================================================================
    soc_y = 766
    soc_h = 32
    soc_items = [
        {"name": "LinkedIn", "icon": "linkedin", "w": 96, "url": social_links.get("linkedin", "")},
        {"name": "Email", "icon": "email", "w": 78, "url": social_links.get("email", "")},
        {"name": "Instagram", "icon": "instagram", "w": 104, "url": social_links.get("instagram", "")},
        {"name": profile.get("username", "Zakkyaulia"), "icon": "github", "w": 118, "url": social_links.get("github", "")}
    ]

    cur_soc_x = 24
    svg_parts.append(f'  <!-- SECTION F: Social Badges -->')
    for item in soc_items:
        sw = item["w"]
        s_icon = ICONS.get(item["icon"], ICONS["github"])
        svg_parts.append(f'  <g transform="translate({cur_soc_x}, {soc_y})">')
        svg_parts.append(f'    <rect width="{sw}" height="{soc_h}" rx="8" class="badge-pill"/>')
        svg_parts.append(f'    <g transform="translate(10, 8) scale(0.9)">{s_icon}</g>')
        svg_parts.append(f'    <text x="32" y="20" class="font-main badge-text">{escape(item["name"])}</text>')
        svg_parts.append(f'  </g>')
        cur_soc_x += sw + 12

    svg_parts.append("</svg>")

    full_svg_content = "\n".join(svg_parts)

    # Save to assets/github-dashboard.svg
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = ASSETS_DIR / "github-dashboard.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(full_svg_content)

    print(f"SVG Dashboard successfully generated and saved to {svg_path} ({len(full_svg_content)} bytes)")
    return str(svg_path)


if __name__ == "__main__":
    generate_svg()
