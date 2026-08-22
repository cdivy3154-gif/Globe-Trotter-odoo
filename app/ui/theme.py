# ═══════════════════════════════════════════════════════════════════
#   GLOBETROTTER — M3 EXPRESSIVE DESIGN SYSTEM
#   Primary: Warm Amber-Orange (#D97706 / #8C4A01)
#   Surface: Deep Slate with warm tint
#   Typography: Segoe UI Variable → Segoe UI → fallback
# ═══════════════════════════════════════════════════════════════════

# ── Primary Brand Palette ────────────────────────────────────────
_ORANGE_50  = "#FFF8F0"
_ORANGE_100 = "#FFEDD5"
_ORANGE_200 = "#FED7AA"
_ORANGE_300 = "#FDBA74"
_ORANGE_400 = "#FB923C"
_ORANGE_500 = "#F97316"
_ORANGE_600 = "#EA580C"
_ORANGE_700 = "#C2410C"
_ORANGE_800 = "#9A3412"
_ORANGE_900 = "#7C2D12"

# ── Secondary (Amber, warm accent) ───────────────────────────────
_AMBER_400  = "#FBBF24"
_AMBER_500  = "#F59E0B"
_AMBER_600  = "#D97706"

# ── Surface Palette (Warm Slate) ──────────────────────────────────
_SLATE_50   = "#F8FAFC"
_SLATE_100  = "#F1F5F9"
_SLATE_200  = "#E2E8F0"
_SLATE_300  = "#CBD5E1"
_SLATE_400  = "#94A3B8"
_SLATE_500  = "#64748B"
_SLATE_600  = "#475569"
_SLATE_700  = "#334155"
_SLATE_800  = "#1E293B"
_SLATE_850  = "#172032"
_SLATE_900  = "#0F172A"
_SLATE_950  = "#090E1A"

# Warm tint over pure slate
_WARM_900   = "#120E08"   # near-black warm bg
_WARM_850   = "#1C160C"   # bg dark
_WARM_800   = "#241D0F"   # card bg
_WARM_750   = "#2E2510"   # card hover
_WARM_700   = "#3D3118"   # sidebar / input bg
_WARM_600   = "#574721"   # border
_WARM_500   = "#7A6430"   # border light / muted text area

# ── Semantic Status ───────────────────────────────────────────────
_GREEN_400  = "#34D399"
_GREEN_500  = "#10B981"
_GREEN_900  = "#064E3B"
_RED_400    = "#F87171"
_RED_500    = "#EF4444"
_RED_700    = "#B91C1C"
_RED_900    = "#7F1D1D"
_BLUE_400   = "#60A5FA"
_BLUE_500   = "#3B82F6"
_SKY_400    = "#38BDF8"
_TEAL_400   = "#2DD4BF"
_VIOLET_500 = "#8B5CF6"

# ══════════════════════════════════════════════════════════════════
#   THEME — the single source of truth imported everywhere
# ══════════════════════════════════════════════════════════════════
THEME = {
    # ── Brand ───────────────────────────────────────────────────
    "primary":           _ORANGE_600,       # #EA580C  Warm Orange
    "primary_hover":     _ORANGE_700,       # #C2410C  darker press
    "primary_dim":       _ORANGE_800,       # #9A3412  muted orange
    "primary_light":     _ORANGE_100,       # light tint
    "primary_container": "#2D1606",         # deep orange surface
    "on_primary":        "#FFFFFF",
    "on_primary_container": _ORANGE_200,

    # ── Amber / Gold Accent ──────────────────────────────────────
    "accent":            _AMBER_500,        # #F59E0B
    "accent_hover":      _AMBER_600,        # #D97706
    "on_accent":         "#1C1400",

    # ── Surfaces (warm slate hierarchy) ─────────────────────────
    "bg_dark":           _WARM_850,         # main app bg
    "bg_card":           _WARM_800,         # cards
    "bg_card_hover":     _WARM_750,         # card hover
    "bg_sidebar":        _WARM_900,         # sidebar
    "bg_input":          _WARM_700,         # input fields
    "bg_surface2":       "#1A1408",         # alternate deep surface

    # ── Borders & Dividers ───────────────────────────────────────
    "border":            _WARM_600,         # #574721
    "border_light":      _WARM_500,         # #7A6430
    "border_focus":      _ORANGE_600,       # orange on focus

    # ── Typography ───────────────────────────────────────────────
    "text_primary":      "#F8F4EE",         # warm white
    "text_secondary":    "#C4B99A",         # muted warm
    "text_muted":        "#8A7D62",         # very muted
    "text_on_primary":   "#FFFFFF",
    "text_on_accent":    "#1C1400",
    "text_link":         _ORANGE_400,

    # ── Status / Semantic ────────────────────────────────────────
    "success":           _GREEN_400,
    "success_bg":        _GREEN_900,
    "warning":           _AMBER_400,
    "warning_bg":        "#451A00",
    "danger":            _RED_400,
    "danger_hover":      _RED_500,
    "danger_bg":         _RED_900,
    "info":              _SKY_400,
    "info_bg":           "#0C2D44",

    # ── Chart / Data Vis Colors ──────────────────────────────────
    "chart_1":           _ORANGE_500,
    "chart_2":           _AMBER_400,
    "chart_3":           _GREEN_400,
    "chart_4":           _SKY_400,
    "chart_5":           _VIOLET_500,
    "chart_6":           _TEAL_400,

    # ── Trip Status Chips ────────────────────────────────────────
    "status_upcoming":   _BLUE_400,
    "status_ongoing":    _GREEN_400,
    "status_past":       _SLATE_400,
    "status_public":     _TEAL_400,
    "status_private":    _WARM_500,
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

    # Icon (Material Symbols not available natively — use emoji fallback)
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
#   MATPLOTLIB — chart style config (used by budget/admin screens)
# ══════════════════════════════════════════════════════════════════
MPL_STYLE = {
    "bg":           _WARM_800,
    "axes_bg":      _WARM_800,
    "text":         "#F8F4EE",
    "muted":        "#8A7D62",
    "grid":         "#2E2510",
    "colors":       [_ORANGE_500, _AMBER_400, _GREEN_400, _SKY_400, _VIOLET_500, _TEAL_400, _RED_400],
}
