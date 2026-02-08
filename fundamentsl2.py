

from __future__ import annotations
import math
from typing import NamedTuple
# 1.  BASELINE PARAMETERS  (Table: "Model Parameters")
CATCHMENT_AREA_KM2      = 25          # km²  (50×50 grid, 100 m cells)
POPULATION              = 50_000
EXPOSED_ASSETS_EUR      = 2_500_000_000   # €2.5 billion
BASELINE_FLOOD_PROB     = 0.10        # 10 %  (1-in-10 year)
BASELINE_N_LOAD_KG      = 12_000      # kg N / year
BUDGET_EUR              = 10_000_000  # €10 million
DISCOUNT_RATE           = 0.03        # 3 %
HORIZON_YEARS           = 30

# ──────────────────────────────────────────────────────────────────────────────
# 2.  EXPECTED ANNUAL PRODUCTIVITY LOSS  (introductory illustration)
#     "For a mid-sized European city with €5 billion GDP in flood-prone
#      zones, 5 % annual flood probability, and 10 % average impact factor,
#      expected annual productivity losses reach €25 million."
# ──────────────────────────────────────────────────────────────────────────────
def annual_productivity_loss(gdp_flood_zone: float,
                             flood_prob: float,
                             impact_factor: float) -> float:
    """Simple expected-loss calculation from the Introduction."""
    return gdp_flood_zone * flood_prob * impact_factor


# ──────────────────────────────────────────────────────────────────────────────
# 3.  NPV HELPER  —  present value of a level annual cash-flow
# ──────────────────────────────────────────────────────────────────────────────
def npv_annuity(annual_value: float,
                rate: float = DISCOUNT_RATE,
                years: int = HORIZON_YEARS) -> float:
    """PV of 'annual_value' paid at end of each year for 'years' years."""
    if rate == 0:
        return annual_value * years
    return annual_value * (1 - (1 + rate) ** -years) / rate


def npv_lump(future_value: float, year: int,
             rate: float = DISCOUNT_RATE) -> float:
    """PV of a single future cash-flow occurring in 'year'."""
    return future_value / (1 + rate) ** year


# ──────────────────────────────────────────────────────────────────────────────
# 4.  NbS UNIT SPECIFICATIONS  (Table: "NbS Unit Specifications")
# ──────────────────────────────────────────────────────────────────────────────
class NbSType(NamedTuple):
    name:               str
    unit_size:          str       # descriptive
    storage_m3:         float     # m³ per unit
    n_removal_pct:      float     # % nitrogen removal
    impl_cost_eur:      float     # € per unit
    maint_cost_eur_yr:  float     # € / year per unit


WETLAND        = NbSType("Wetland",         "5 ha",        15_000, 50, 750_000, 15_000)
RIPARIAN       = NbSType("Riparian Buffer", "1 km × 15 m",  2_000, 60,  30_000,  2_000)
BIOSWALE       = NbSType("Bioswale",        "0.1 ha",         300, 65,  25_000,  1_500)
GREEN_CORRIDOR = NbSType("Green Corridor",  "2 ha",         4_000, 40, 200_000,  8_000)

NBS_TYPES = [WETLAND, RIPARIAN, BIOSWALE, GREEN_CORRIDOR]


def units_from_budget(nbs: NbSType, budget: float = BUDGET_EUR) -> int:
    """Maximum whole units purchasable with the given budget."""
    return int(budget // nbs.impl_cost_eur)


# ──────────────────────────────────────────────────────────────────────────────
# 5.  BASELINE  —  COST OF INACTION  (30-year totals)
#     Table: "Baseline Performance (30-year totals)"
# ──────────────────────────────────────────────────────────────────────────────
class BaselineResults(NamedTuple):
    expected_flood_events:       float   # major events over 30 yr
    direct_flood_damage_30yr:    float   # € undiscounted
    productivity_losses_30yr:    float   # € undiscounted
    restoration_costs_30yr:      float   # € undiscounted  (2.5× direct)
    annual_pollution_cost:       float   # € / year
    total_undiscounted_30yr:     float   # € sum
    npv_damages:                 float   # € at 3 % discount


def compute_baseline() -> BaselineResults:
    """
    Reproduce every number in the Baseline table.
    The restoration multiplier is 2.5× direct damage (stated in the report).
    """
    direct              = 47_320_000          # €47.32 M  (simulation output)
    productivity        = 31_800_000          # €31.8 M
    restoration_mult    = 2.5                 # "2-3×"; report uses 2.5×
    restoration         = direct * restoration_mult   # €118.3 M  (≈ 118.25 M)
    annual_pollution    = 42_000              # €42 k / year
    pollution_30yr      = annual_pollution * HORIZON_YEARS   # €1.26 M

    total_undiscounted  = direct + productivity + restoration + pollution_30yr
    # Reported NPV = €124.2 M  (from stochastic simulation; we also
    # derive it via the annuity helper for verification)
    # Annual equivalent implied by report: €4.1 M / yr
    annual_avg          = total_undiscounted / HORIZON_YEARS
    npv_derived         = npv_annuity(annual_avg)   # cross-check

    # Expected major events: 30 yr × 10 % / year ≈ 3 events;
    # report states 3.2 (stochastic average).
    expected_events     = 3.2

    return BaselineResults(
        expected_flood_events      = expected_events,
        direct_flood_damage_30yr   = direct,
        productivity_losses_30yr   = productivity,
        restoration_costs_30yr     = restoration,
        annual_pollution_cost      = annual_pollution,
        total_undiscounted_30yr    = total_undiscounted,
        npv_damages                = 124_200_000        # simulation-reported NPV
    )


def baseline_cost_breakdown(bl: BaselineResults) -> dict[str, float]:
    """Percentage shares of the 30-year undiscounted total."""
    total = bl.total_undiscounted_30yr
    pollution_30 = bl.annual_pollution_cost * HORIZON_YEARS
    return {
        "Infrastructure Restoration (%)": round(bl.restoration_costs_30yr / total * 100, 1),
        "Direct Flood Damage (%)":        round(bl.direct_flood_damage_30yr / total * 100, 1),
        "Productivity Losses (%)":        round(bl.productivity_losses_30yr / total * 100, 1),
        "Pollution Costs (%)":            round(pollution_30 / total * 100, 1),
    }


def structural_liability(bl: BaselineResults) -> float:
    """Annual loss as % of total exposed assets."""
    annual_equiv = bl.npv_damages / HORIZON_YEARS          # €4.1 M
    return annual_equiv / EXPOSED_ASSETS_EUR * 100         # 0.16 %


# ──────────────────────────────────────────────────────────────────────────────
# 6.  FLOOD DAMAGE FUNCTIONS  (Table: "Flood Damage Functions")
#     damage = flooded_area_m2 × asset_density × damage_percentage
# ──────────────────────────────────────────────────────────────────────────────
# asset_density  € / m²
# damage_pct at 0.5 m and 1.5 m inundation depth

DAMAGE_TABLE = {
    #  land_use      (asset_density, dmg_0.5m, dmg_1.5m)
    "Residential":    (800,   0.25, 0.60),
    "Commercial":     (1500,  0.35, 0.75),
    "Industrial":     (1200,  0.30, 0.70),
    "Infrastructure": (2000,  0.40, 0.80),
}


def flood_damage(land_use: str,
                 flooded_area_m2: float,
                 depth_m: float) -> float:
    """
    Linear interpolation between 0.5 m and 1.5 m benchmark damage rates.
    Below 0.5 m  → linear scale from 0 at depth = 0.
    Above 1.5 m  → capped at the 1.5 m rate (conservative).
    """
    density, pct_05, pct_15 = DAMAGE_TABLE[land_use]

    if depth_m <= 0.5:
        pct = pct_05 * (depth_m / 0.5)
    elif depth_m <= 1.5:
        pct = pct_05 + (pct_15 - pct_05) * ((depth_m - 0.5) / 1.0)
    else:
        pct = pct_15          # cap

    return flooded_area_m2 * density * pct


# ──────────────────────────────────────────────────────────────────────────────
# 7.  PRODUCTIVITY-LOSS FUNCTIONS  (Economic Impact Functions)
#     Tiers by flood depth
# ──────────────────────────────────────────────────────────────────────────────
# (max_depth_m, disruption_pct, duration_days)
PRODUCTIVITY_TIERS = [
    (0.5,  0.05,  30),   # Moderate  < 0.5 m
    (1.5,  0.15,  90),   # Severe    0.5-1.5 m
    (999,  0.25, 180),   # Extreme   > 1.5 m
]


def productivity_loss(gdp_in_zone: float, depth_m: float) -> float:
    """Annual productivity loss for one flood event of given depth."""
    for max_d, disrupt, days in PRODUCTIVITY_TIERS:
        if depth_m <= max_d:
            return gdp_in_zone * disrupt * (days / 365)
    # fallback – should not reach here
    return gdp_in_zone * 0.25 * (180 / 365)


# ──────────────────────────────────────────────────────────────────────────────
# 8.  FOUR STRATEGIC CONFIGURATIONS
#     All figures come directly from the report's results tables.
#     We verify BCR and NPV from the stated components.
# ──────────────────────────────────────────────────────────────────────────────
class NbSConfig(NamedTuple):
    name:                       str
    units_description:          str
    flood_peak_reduction_pct:   float
    inundation_area_red_pct:    float | None   # only bioswales reports this
    extreme_resilience_pct:     float | None   # 1-in-50 yr peak reduction
    pollution_reduction_pct:    float | None   # % nitrogen
    direct_damage_avoided_npv:  float
    productivity_avoided_npv:   float
    restoration_avoided_npv:    float
    treatment_savings_npv:      float          # water-treatment
    total_benefits_npv:         float
    implementation_cost:        float
    maintenance_cost_npv:       float
    net_present_value:          float          # reported
    benefit_cost_ratio:         float          # reported
    payback_years:              int


CONFIG_BIOSWALES = NbSConfig(
    name                       = "Distributed Bioswales",
    units_description          = "400 bioswales",
    flood_peak_reduction_pct   = 18,
    inundation_area_red_pct    = 23,
    extreme_resilience_pct     = 12,
    pollution_reduction_pct    = 22,
    direct_damage_avoided_npv  = 11_200_000,
    productivity_avoided_npv   =  8_100_000,
    restoration_avoided_npv    = 28_000_000,
    treatment_savings_npv      =  0,
    total_benefits_npv         = 47_300_000,
    implementation_cost        = 10_000_000,
    maintenance_cost_npv       =  9_300_000,
    net_present_value          = 28_000_000,
    benefit_cost_ratio         = 2.45,
    payback_years              = 12,
)

CONFIG_BUFFERS = NbSConfig(
    name                       = "Riparian Buffer Network",
    units_description          = "333 km of buffers",
    flood_peak_reduction_pct   = 21,
    inundation_area_red_pct    = None,
    extreme_resilience_pct     = 18,
    pollution_reduction_pct    = 48,
    direct_damage_avoided_npv  = 13_700_000,
    productivity_avoided_npv   =  9_400_000,
    restoration_avoided_npv    = 34_300_000,
    treatment_savings_npv      =  3_800_000,
    total_benefits_npv         = 61_200_000,
    implementation_cost        = 10_000_000,
    maintenance_cost_npv       = 10_400_000,
    net_present_value          = 40_800_000,
    benefit_cost_ratio         = 3.00,
    payback_years              =  9,
)

CONFIG_WETLANDS = NbSConfig(
    name                       = "Strategic Wetlands",
    units_description          = "13 wetlands (5 ha each)",
    flood_peak_reduction_pct   = 35,
    inundation_area_red_pct    = None,
    extreme_resilience_pct     = 45,
    pollution_reduction_pct    = 35,
    direct_damage_avoided_npv  = 19_800_000,
    productivity_avoided_npv   = 13_200_000,
    restoration_avoided_npv    = 49_500_000,
    treatment_savings_npv      =  0,
    total_benefits_npv         = 82_500_000,
    implementation_cost        = 10_000_000,
    maintenance_cost_npv       =  7_800_000,
    net_present_value          = 64_700_000,
    benefit_cost_ratio         = 4.63,
    payback_years              =  6,
)

CONFIG_HYBRID = NbSConfig(
    name                       = "Hybrid Approach",
    units_description          = "5 wetlands + 100 bioswales + 50 km buffers",
    flood_peak_reduction_pct   = 28,
    inundation_area_red_pct    = None,
    extreme_resilience_pct     = 32,
    pollution_reduction_pct    = 41,
    direct_damage_avoided_npv  = 16_400_000,
    productivity_avoided_npv   = 11_300_000,
    restoration_avoided_npv    = 41_000_000,
    treatment_savings_npv      =  2_600_000,
    total_benefits_npv         = 71_300_000,
    implementation_cost        = 10_000_000,
    maintenance_cost_npv       =  8_900_000,
    net_present_value          = 52_400_000,
    benefit_cost_ratio         = 3.77,
    payback_years              =  8,
)

ALL_CONFIGS = [CONFIG_BIOSWALES, CONFIG_BUFFERS, CONFIG_WETLANDS, CONFIG_HYBRID]


def verify_config_economics(cfg: NbSConfig) -> dict[str, float]:
    """
    Re-derive NPV and BCR from the stated benefit / cost components.
    """
    total_cost  = cfg.implementation_cost + cfg.maintenance_cost_npv
    derived_npv = cfg.total_benefits_npv - total_cost
    derived_bcr = cfg.total_benefits_npv / total_cost
    return {
        "total_cost_eur":   total_cost,
        "derived_npv_eur":  derived_npv,
        "reported_npv_eur": cfg.net_present_value,
        "npv_diff_eur":     derived_npv - cfg.net_present_value,
        "derived_bcr":      round(derived_bcr, 2),
        "reported_bcr":     cfg.benefit_cost_ratio,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 9.  HYBRID BUDGET BREAKDOWN
# ──────────────────────────────────────────────────────────────────────────────
def hybrid_budget_breakdown() -> dict[str, float]:
    """Itemised implementation cost of the Hybrid portfolio."""
    wetlands  = 5   * WETLAND.impl_cost_eur        # €3.75 M
    bioswales = 100 * BIOSWALE.impl_cost_eur       # €2.50 M
    buffers   = 50  * RIPARIAN.impl_cost_eur       # €1.50 M  (50 km)
    total     = wetlands + bioswales + buffers
    return {
        "Wetlands (5 × €750 k)":      wetlands,
        "Bioswales (100 × €25 k)":    bioswales,
        "Buffers (50 km × €30 k)":    buffers,
        "Total implementation cost":  total,
        "Remaining budget":           BUDGET_EUR - total,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 10. CLIMATE SCENARIO ESCALATION
#     Baseline NPV of damages under three climate futures
# ──────────────────────────────────────────────────────────────────────────────
CLIMATE_SCENARIOS = {
    "Current":  {
        "precip_intensity_factor": 1.00,
        "event_freq_factor":       1.00,   # 1-in-10 yr
        "baseline_npv_damages":    124_200_000,
    },
    "Moderate Change": {
        "precip_intensity_factor": 1.20,   # +20 %
        "event_freq_factor":       1.333,  # 1-in-10 → 1-in-7.5  (10/7.5)
        "baseline_npv_damages":    178_000_000,
    },
    "Severe Change": {
        "precip_intensity_factor": 1.40,   # +40 %
        "event_freq_factor":       2.00,   # 1-in-10 → 1-in-5    (10/5)
        "baseline_npv_damages":    265_000_000,
    },
}


def climate_escalation_multipliers() -> dict[str, float]:
    """Ratio of each scenario's baseline NPV to current-climate NPV."""
    current = CLIMATE_SCENARIOS["Current"]["baseline_npv_damages"]
    return {
        name: round(data["baseline_npv_damages"] / current, 2)
        for name, data in CLIMATE_SCENARIOS.items()
    }


# ──────────────────────────────────────────────────────────────────────────────
# 11. TERRITORIAL-COMPETITIVENESS INDICATORS
# ──────────────────────────────────────────────────────────────────────────────

# --- 11a  Business-Interruption Savings ---------------------------------
# Report states:
#   • Strategic wetlands avoid 85 business-interruption days / year
#   • Bioswales avoid 35 days / year
#   • "typical European SME with €50,000 daily revenue"
#   • "€42,000 avoided losses per firm per year"   ← see NOTE below
#   • 50 exposed firms  →  €2.1 M / year total

DAILY_REVENUE_PER_FIRM = 50_000   # € / day  (report text)
EXPOSED_FIRMS          = 50

INTERRUPTION_DAYS = {
    "Strategic Wetlands":      85,
    "Distributed Bioswales":   35,
}


def business_interruption_savings() -> dict[str, dict]:
    """
    Returns per-strategy breakdown.  Flags the internal inconsistency
    found in the report.
    """
    results = {}
    for strategy, days in INTERRUPTION_DAYS.items():
        raw_per_firm   = DAILY_REVENUE_PER_FIRM * days          # arithmetic
        raw_total      = raw_per_firm * EXPOSED_FIRMS
        results[strategy] = {
            "days_avoided_per_year":        days,
            "daily_revenue_per_firm_eur":   DAILY_REVENUE_PER_FIRM,
            # --- raw multiplication --------------------------------
            "computed_per_firm_eur":        raw_per_firm,
            "computed_total_eur":           raw_total,
            # --- report stated values ------------------------------
            "reported_per_firm_eur":        42000,
            "reported_total_annual_eur":    2100000,
        }
    return results


# --- 11b  Property-Value Protection -------------------------------------
# "flood risk capitalisation reduces property values by 0.5–1.0 %
#  per 1 % increase in annual flood probability"
# Wetlands: flood prob 10 %  →  6.5 %  (reduction = 3.5 pp)
# Protected value = exposed_assets × reduction_pp × capitalisation_rate

FLOOD_PROB_BASELINE_PCT       = 10.0
FLOOD_PROB_WETLANDS_PCT       =  6.5
CAPITALISATION_RATE_LOW       = 0.005   # 0.5 % per 1 pp
CAPITALISATION_RATE_HIGH      = 0.010   # 1.0 % per 1 pp


def property_value_protection() -> dict[str, float]:
    reduction_pp = FLOOD_PROB_BASELINE_PCT - FLOOD_PROB_WETLANDS_PCT   # 3.5
    low  = EXPOSED_ASSETS_EUR * reduction_pp * CAPITALISATION_RATE_LOW
    high = EXPOSED_ASSETS_EUR * reduction_pp * CAPITALISATION_RATE_HIGH
    return {
        "flood_prob_reduction_pp":          reduction_pp,
        "property_value_protected_low_eur": low,    # €43.75 M
        "property_value_protected_high_eur":high,   # €87.50 M
        "report_range":                     "€40–80 M (rounded in report)",
    }


# --- 11c  Insurance-Premium Savings -------------------------------------
# Flood-prob reduction 35 %  →  premium reduction 20–30 %
# Per household saving: €120–180 / yr
# 15 000 properties in catchment

PROPERTIES_IN_CATCHMENT  = 15_000
SAVING_PER_PROPERTY_LOW  =   120   # € / yr
SAVING_PER_PROPERTY_HIGH =   180


def insurance_premium_savings() -> dict[str, float]:
    low  = PROPERTIES_IN_CATCHMENT * SAVING_PER_PROPERTY_LOW
    high = PROPERTIES_IN_CATCHMENT * SAVING_PER_PROPERTY_HIGH
    return {
        "properties":               PROPERTIES_IN_CATCHMENT,
        "saving_per_property_low":  SAVING_PER_PROPERTY_LOW,
        "saving_per_property_high": SAVING_PER_PROPERTY_HIGH,
        "total_annual_low_eur":     low,     # €1.8 M
        "total_annual_high_eur":    high,    # €2.7 M
    }


# ──────────────────────────────────────────────────────────────────────────────
# 12. TERRITORIAL ATTRACTIVENESS INDEX  (composite, 0-100)
# ──────────────────────────────────────────────────────────────────────────────
ATTRACTIVENESS_INDEX = {
    "Baseline (no NbS)":        52,
    "Distributed Bioswales":    64,
    "Riparian Buffers":         67,
    "Strategic Wetlands":       71,
    "Hybrid Approach":          70,
}


# ──────────────────────────────────────────────────────────────────────────────
# 13. MASTER COMPARISON  —  all configs + baseline on one table
# ──────────────────────────────────────────────────────────────────────────────
def comparison_table() -> list[dict]:
    """
    Mirrors "Strategic Scenario Comparison" table in the report.
    """
    rows = []
    rows.append({
        "Configuration":      "Baseline (no NbS)",
        "NPV (€M)":           -124.2,
        "B/C Ratio":          None,
        "Flood Reduction (%)":  None,
        "Pollution Red. (%)":   None,
        "Resilience 1-in-50 (%)": None,
    })
    for cfg in ALL_CONFIGS:
        rows.append({
            "Configuration":          cfg.name,
            "NPV (€M)":               round(cfg.net_present_value / 1e6, 1),
            "B/C Ratio":              cfg.benefit_cost_ratio,
            "Flood Reduction (%)":    cfg.flood_peak_reduction_pct,
            "Pollution Red. (%)":     cfg.pollution_reduction_pct,
            "Resilience 1-in-50 (%)": cfg.extreme_resilience_pct,
        })
    return rows
def _fmt(val, prefix="€", suffix="", decimals=2):
    """Pretty-print a number with thousand-separators."""
    if val is None:
        return "  —  "
    txt = f"{val:,.{decimals}f}"
    return f"{prefix}{txt}{suffix}"


def main():
    divider = "=" * 72

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  1.  INTRODUCTORY EXPECTED ANNUAL PRODUCTIVITY LOSS")
    print(divider)
    loss = annual_productivity_loss(5_000_000_000, 0.05, 0.10)
    print(f"  GDP in flood zone        : {_fmt(5_000_000_000)}")
    print(f"  Annual flood probability : 5 %")
    print(f"  Average impact factor    : 10 %")
    print(f"  Expected annual loss     : {_fmt(loss)}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  2.  NbS UNIT COUNTS  (full €10 M budget)")
    print(divider)
    for t in NBS_TYPES:
        n = units_from_budget(t)
        print(f"  {t.name:<20s} : {n:>5d} units  "
              f"(cost {_fmt(t.impl_cost_eur)} each)")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  3.  BASELINE  —  COST OF INACTION")
    print(divider)
    bl = compute_baseline()
    print(f"  Expected flood events (30 yr)     : {bl.expected_flood_events}")
    print(f"  Cumulative direct flood damage    : {_fmt(bl.direct_flood_damage_30yr)}")
    print(f"  Cumulative productivity losses    : {_fmt(bl.productivity_losses_30yr)}")
    print(f"  Infrastructure restoration costs  : {_fmt(bl.restoration_costs_30yr)}  "
          f"(2.5× direct)")
    print(f"  Annual pollution treatment cost   : {_fmt(bl.annual_pollution_cost)} / yr")
    print(f"  Total economic impact (30 yr)     : {_fmt(bl.total_undiscounted_30yr)}  "
          f"(undiscounted)")
    print(f"  NPV of damages (3 % discount)     : {_fmt(bl.npv_damages)}")

    print("\n  Cost-of-Inaction Breakdown:")
    for label, pct in baseline_cost_breakdown(bl).items():
        print(f"    {label:<40s}: {pct:>5.1f} %")
    print(f"\n  Structural liability (annual / assets): "
          f"{structural_liability(bl):.2f} %")

    # cross-check NPV via annuity helper
    annual_avg   = bl.total_undiscounted_30yr / HORIZON_YEARS
    npv_check    = npv_annuity(annual_avg)
    print(f"\n  NPV cross-check (annuity on avg €{annual_avg/1e6:.2f} M / yr): "
          f"{_fmt(npv_check)}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  4.  FLOOD DAMAGE FUNCTION  —  example calculations")
    print(divider)
    examples = [
        ("Residential",    10_000, 0.3),
        ("Commercial",     5_000,  0.5),
        ("Industrial",     8_000,  1.0),
        ("Infrastructure", 3_000,  1.5),
    ]
    print(f"  {'Land Use':<15s} {'Area (m²)':>10s} {'Depth (m)':>10s} "
          f"{'Damage (€)':>14s}")
    print(f"  {'-'*15} {'-'*10} {'-'*10} {'-'*14}")
    for lu, area, depth in examples:
        dmg = flood_damage(lu, area, depth)
        print(f"  {lu:<15s} {area:>10,d} {depth:>10.1f} {_fmt(dmg):>14s}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  5.  PRODUCTIVITY-LOSS FUNCTION  —  example calculations")
    print(divider)
    gdp_zone = 500_000_000   # €500 M in flood zone (illustrative)
    for depth in [0.3, 0.8, 2.0]:
        pl = productivity_loss(gdp_zone, depth)
        print(f"  Depth {depth:.1f} m  →  productivity loss : {_fmt(pl)}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  6.  STRATEGIC CONFIGURATIONS  —  full economics")
    print(divider)
    for cfg in ALL_CONFIGS:
        v = verify_config_economics(cfg)
        print(f"\n  ── {cfg.name} ({cfg.units_description}) ──")
        print(f"    Flood-peak reduction        : {cfg.flood_peak_reduction_pct} %")
        if cfg.extreme_resilience_pct:
            print(f"    Extreme-event resilience    : {cfg.extreme_resilience_pct} % "
                  f"(1-in-50 yr peak)")
        if cfg.pollution_reduction_pct:
            print(f"    Pollution (N) reduction     : {cfg.pollution_reduction_pct} %")
        print(f"    Direct damage avoided (NPV) : {_fmt(cfg.direct_damage_avoided_npv)}")
        print(f"    Productivity avoided (NPV)  : {_fmt(cfg.productivity_avoided_npv)}")
        print(f"    Restoration avoided (NPV)   : {_fmt(cfg.restoration_avoided_npv)}")
        if cfg.treatment_savings_npv:
            print(f"    Treatment savings (NPV)     : {_fmt(cfg.treatment_savings_npv)}")
        print(f"    ── Totals ──")
        print(f"    Total benefits (NPV)        : {_fmt(cfg.total_benefits_npv)}")
        print(f"    Implementation cost         : {_fmt(cfg.implementation_cost)}")
        print(f"    Maintenance cost (NPV)      : {_fmt(cfg.maintenance_cost_npv)}")
        print(f"    Net present value           : {_fmt(cfg.net_present_value)}  "
              f"(reported)")
        print(f"    NPV derived from components : {_fmt(v['derived_npv_eur'])}  "
              f"(Δ = {_fmt(v['npv_diff_eur'])})")
        print(f"    Benefit-cost ratio          : {cfg.benefit_cost_ratio}  "
              f"(derived: {v['derived_bcr']})")
        print(f"    Payback period              : {cfg.payback_years} years")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  7.  HYBRID BUDGET BREAKDOWN")
    print(divider)
    for label, val in hybrid_budget_breakdown().items():
        print(f"    {label:<40s}: {_fmt(val)}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  8.  STRATEGIC SCENARIO COMPARISON TABLE")
    print(divider)
    hdr = (f"  {'Configuration':<25s} {'NPV (€M)':>10s} {'B/C':>6s} "
           f"{'Flood%':>7s} {'Poll%':>6s} {'Resil%':>7s}")
    print(hdr)
    print("  " + "-" * 68)
    for row in comparison_table():
        print(f"  {row['Configuration']:<25s} "
              f"{str(row['NPV (€M)']):>10s} "
              f"{str(row['B/C Ratio']) if row['B/C Ratio'] else '—':>6s} "
              f"{str(row['Flood Reduction (%)']) if row['Flood Reduction (%)'] else '—':>7s} "
              f"{str(row['Pollution Red. (%)']) if row['Pollution Red. (%)'] else '—':>6s} "
              f"{str(row['Resilience 1-in-50 (%)']) if row['Resilience 1-in-50 (%)'] else '—':>7s}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  9.  CLIMATE SCENARIO ESCALATION")
    print(divider)
    print(f"  {'Scenario':<22s} {'Precip ×':>9s} {'Freq ×':>8s} "
          f"{'Baseline NPV Damages':>22s} {'Multiplier':>11s}")
    print("  " + "-" * 75)
    mults = climate_escalation_multipliers()
    for name, data in CLIMATE_SCENARIOS.items():
        print(f"  {name:<22s} {data['precip_intensity_factor']:>9.2f} "
              f"{data['event_freq_factor']:>8.3f} "
              f"{_fmt(data['baseline_npv_damages']):>22s} "
              f"{mults[name]:>10.2f}×")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  10. TERRITORIAL COMPETITIVENESS")
    print(divider)

    print("\n  (a) Business-Interruption Savings")
    for strat, info in business_interruption_savings().items():
        print(f"\n    {strat}:")
        print(f"      Days avoided / year              : {info['days_avoided_per_year']}")
        print(f"      Computed per firm (raw arith.)   : {_fmt(info['computed_per_firm_eur'])}")
        print(f"      Reported per firm                : {_fmt(info['reported_per_firm_eur'])}")
        print(f"      Reported total annual            : {_fmt(info['reported_total_annual_eur'])}")
        

    print("\n  (b) Property-Value Protection  (Strategic Wetlands)")
    pvp = property_value_protection()
    print(f"      Flood-prob reduction                : {pvp['flood_prob_reduction_pp']} pp")
    print(f"      Protected value (low / high)        : "
          f"{_fmt(pvp['property_value_protected_low_eur'])} – "
          f"{_fmt(pvp['property_value_protected_high_eur'])}")
    print(f"      Report range                        : {pvp['report_range']}")

    print("\n  (c) Insurance-Premium Savings")
    ips = insurance_premium_savings()
    print(f"      Properties                          : {ips['properties']:,}")
    print(f"      Saving / property / yr (low–high)   : "
          f"{_fmt(ips['saving_per_property_low'])} – "
          f"{_fmt(ips['saving_per_property_high'])}")
    print(f"      Total annual savings (low–high)     : "
          f"{_fmt(ips['total_annual_low_eur'])} – "
          f"{_fmt(ips['total_annual_high_eur'])}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  11. TERRITORIAL ATTRACTIVENESS INDEX  (0-100)")
    print(divider)
    for label, score in ATTRACTIVENESS_INDEX.items():
        bar = "█" * score
        print(f"    {label:<28s} : {score:>3d}  {bar}")

    # ------------------------------------------------------------------
    print(f"\n{divider}")
    print("  12. RANKING BY NET PRESENT VALUE")
    print(divider)
    ranked = sorted(ALL_CONFIGS, key=lambda c: c.net_present_value, reverse=True)
    for rank, cfg in enumerate(ranked, 1):
        print(f"    {rank}.  {cfg.name:<30s} NPV = {_fmt(cfg.net_present_value)}   "
              f"BCR = {cfg.benefit_cost_ratio}")

    print(f"\n{divider}\n")


if __name__ == "__main__":
    main()