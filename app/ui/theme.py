# ═══════════════════════════════════════════════════════════════════
#   GLOBETROTTER — SUNRISE DESIGN SYSTEM
#   Mode:    Light (warm cream / ivory surfaces)
#   Primary: Saffron Orange  #E8811A / #D4700F
#   Accent:  Golden Yellow   #F5A623 / #D4861B
#   Surface: Warm Ivory + Linen hierarchy
#   Status:  Standard semantic greens/reds on light bg
# ═══════════════════════════════════════════════════════════════════

# ── Saffron-Orange Brand ─────────────────────────────────────────
_SAF_50  = "#FFF8EE"
_SAF_100 = "#FEECD3"
_SAF_200 = "#FDD4A0"
_SAF_300 = "#FBB469"
_SAF_400 = "#F99336"
_SAF_500 = "#E8811A"       # primary
_SAF_600 = "#D4700F"       # primary hover
_SAF_700 = "#B05A09"       # dim / muted brand
_SAF_800 = "#8C4407"
_SAF_900 = "#6B3106"

# ── Golden Accent ────────────────────────────────────────────────
_GOLD_300 = "#FCCF6B"
_GOLD_400 = "#F5A623"      # accent
_GOLD_500 = "#D4861B"      # accent hover
_GOLD_600 = "#B36E14"

# ── Warm Cream / Linen Surface Hierarchy ─────────────────────────
_CREAM_50  = "#FFFDF9"     # purest white
_CREAM_100 = "#FDF9F2"     # app background
_CREAM_200 = "#F8F1E4"     # card background
_CREAM_300 = "#F0E6D2"     # card hover / sidebar
_CREAM_400 = "#E5D5B8"     # input background
_CREAM_500 = "#D4BE96"     # border light
_CREAM_600 = "#B89E70"     # border
_CREAM_700 = "#8C7448"     # muted text / border strong

# ── Neutral Grey for text ────────────────────────────────────────
_GREY_900  = "#1A1208"     # primary text (warm near-black)
_GREY_700  = "#3D2E0F"     # secondary text
_GREY_600  = "#5E4A25"     # muted text
_GREY_400  = "#8C7448"     # placeholder / very muted

# ── Semantic Colours ─────────────────────────────────────────────
_GREEN_500  = "#16A34A"
_GREEN_100  = "#DCFCE7"
_GREEN_700  = "#15803D"
_RED_500    = "#DC2626"
_RED_100    = "#FEE2E2"
_RED_700    = "#B91C1C"
_BLUE_500   = "#2563EB"
_BLUE_100   = "#DBEAFE"
_TEAL_500   = "#0D9488"
_TEAL_100   = "#CCFBF1"
_VIOLET_500 = "#7C3AED"
_SKY_500    = "#0284C7"

# ══════════════════════════════════════════════════════════════════
#   THEME — single source of truth imported everywhere
# ══════════════════════════════════════════════════════════════════
THEME = {
    # ── Brand ────────────────────────────────────────────────────
    "primary":              _SAF_500,           # #E8811A  saffron orange
    "primary_hover":        _SAF_600,           # #D4700F  darker press
    "primary_dim":          _SAF_700,           # muted brand
    "primary_light":        _SAF_100,           # very light tint
    "primary_container":    _SAF_100,           # container tint (orange chip bg)
    "on_primary":           "#FFFFFF",
    "on_primary_container": _SAF_700,

    # ── Golden Accent ─────────────────────────────────────────────
    "accent":               _GOLD_400,          # #F5A623
    "accent_hover":         _GOLD_500,          # #D4861B
    "on_accent":            "#2D1A00",

    # ── Surfaces (light warm cream hierarchy) ─────────────────────
    "bg_dark":              _CREAM_100,         # app root bg  (warm off-white)
    "bg_card":              _CREAM_50,          # cards / panels (pure ivory)
    "bg_card_hover":        _CREAM_200,         # card hover
    "bg_sidebar":           _CREAM_300,         # sidebar (linen)
    "bg_input":             _CREAM_200,         # input fields
    "bg_surface2":          _CREAM_400,         # deeper panels

    # ── Borders & Dividers ────────────────────────────────────────
    "border":               _CREAM_500,         # #D4BE96
    "border_light":         _CREAM_400,         # subtle
    "border_focus":         _SAF_500,           # orange ring on focus

    # ── Typography ────────────────────────────────────────────────
    "text_primary":         _GREY_900,          # warm near-black
    "text_secondary":       _GREY_700,          # #3D2E0F
    "text_muted":           _GREY_600,          # #5E4A25
    "text_on_primary":      "#FFFFFF",
    "text_on_accent":       "#2D1A00",
    "text_link":            _SAF_600,

    # ── Status / Semantic ─────────────────────────────────────────
    "success":              _GREEN_700,
    "success_bg":           _GREEN_100,
    "warning":              _GOLD_500,
    "warning_bg":           _SAF_100,
    "danger":               _RED_500,
    "danger_hover":         _RED_700,
    "danger_bg":            _RED_100,
    "info":                 _BLUE_500,
    "info_bg":              _BLUE_100,

    # ── Chart / Data Vis ──────────────────────────────────────────
    "chart_1":              _SAF_500,
    "chart_2":              _GOLD_400,
    "chart_3":              _GREEN_500,
    "chart_4":              _SKY_500,
    "chart_5":              _VIOLET_500,
    "chart_6":              _TEAL_500,

    # ── Trip Status Chips ─────────────────────────────────────────
    "status_upcoming":      _BLUE_500,
    "status_ongoing":       _GREEN_500,
    "status_past":          _GREY_600,
    "status_public":        _TEAL_500,
    "status_private":       _GREY_400,
}

# ══════════════════════════════════════════════════════════════════
#   FONTS — semantic scale
# ══════════════════════════════════════════════════════════════════
_BASE = "Segoe UI Variable"   # Win11 variable font
_FALL = "Segoe UI"            # Win10 fallback

FONTS = {
    # Display headings
    "display":      (_BASE, 32, "bold"),
    "title_xl":     (_BASE, 26, "bold"),
    "title_lg":     (_BASE, 20, "bold"),
    "title_md":     (_BASE, 16, "bold"),
    "title_sm":     (_BASE, 14, "bold"),

    # Body
    "body_lg":      (_BASE, 14, "bold"),
    "body":         (_BASE, 13),
    "body_sm":      (_BASE, 11),

    # Utility
    "badge":        (_BASE, 10, "bold"),
    "caption":      (_BASE, 10),
    "code":         ("Consolas", 12),
    "mono":         ("Consolas", 11),

    # Icon
    "icon_lg":      (_BASE, 20),
    "icon_md":      (_BASE, 16),
}

# ══════════════════════════════════════════════════════════════════
#   SHAPE — corner radii constants (M3-style)
# ══════════════════════════════════════════════════════════════════
SHAPE = {
    "none":         0,
    "extra_small":  4,
    "small":        8,
    "medium":       12,
    "large":        16,
    "extra_large":  24,
    "full":         9999,
}

# ══════════════════════════════════════════════════════════════════
#   LAYOUT — spacing, sizing constants
# ══════════════════════════════════════════════════════════════════
LAYOUT = {
    "sidebar_width":     240,
    "topbar_height":     56,
    "card_radius":       SHAPE["medium"],
    "btn_height":        40,
    "btn_height_sm":     32,
    "btn_height_lg":     48,
    "input_height":      38,
    "pad_xs":            4,
    "pad_sm":            8,
    "pad_md":            16,
    "pad_lg":            24,
    "pad_xl":            32,
}

# ══════════════════════════════════════════════════════════════════
#   MATPLOTLIB — chart style config (light mode)
# ══════════════════════════════════════════════════════════════════
MPL_STYLE = {
    "bg":       _CREAM_50,
    "axes_bg":  _CREAM_50,
    "text":     _GREY_900,
    "muted":    _GREY_600,
    "grid":     _CREAM_400,
    "colors":   [_SAF_500, _GOLD_400, _GREEN_500, _SKY_500, _VIOLET_500, _TEAL_500, _RED_500],
}
