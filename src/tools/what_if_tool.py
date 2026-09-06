from typing import Dict, Any, List

def run_what_if_simulation(
    base_price: float = 89999.0,
    price_change_percent: float = -10.0,
    unit_cost: float = 68000.0,
    base_volume: int = 12000
) -> Dict[str, Any]:
    """
    Simulates financial sensitivity and demand elasticity when price or cost parameters change.
    """
    new_price = base_price * (1 + price_change_percent / 100.0)
    
    # Price elasticity model (Elasticity coefficient = -1.5)
    elasticity = -1.5
    volume_change_percent = price_change_percent * elasticity
    new_volume = int(base_volume * (1 + volume_change_percent / 100.0))
    
    base_revenue = base_price * base_volume
    base_margin = (base_price - unit_cost) * base_volume
    base_margin_pct = ((base_price - unit_cost) / base_price) * 100.0 if base_price > 0 else 0

    new_revenue = new_price * new_volume
    new_margin = (new_price - unit_cost) * new_volume
    new_margin_pct = ((new_price - unit_cost) / new_price) * 100.0 if new_price > 0 else 0

    margin_impact_pct = ((new_margin - base_margin) / base_margin) * 100.0 if base_margin > 0 else 0

    if new_margin_pct < 10.0:
        recommendation_shift = "HIGH RISK: Gross margin drops below 10% threshold. Cost reduction required."
    elif margin_impact_pct > 15.0:
        recommendation_shift = "STRONG GROWTH: Volume surge offsets margin compression. Favorable scenario."
    elif price_change_percent < 0:
        recommendation_shift = "PILOT LAUNCH RECOMMENDED: Lower price boosts market penetration but requires tight cost control."
    else:
        recommendation_shift = "STABLE: Premium pricing strategy with controlled volume expectations."

    return {
        "scenario": f"{price_change_percent:+.1f}% Price Shift",
        "original_price": base_price,
        "new_price": round(new_price, 2),
        "original_unit_margin_pct": round(base_margin_pct, 1),
        "new_unit_margin_pct": round(new_margin_pct, 1),
        "volume_forecast_change_pct": round(volume_change_percent, 1),
        "original_expected_volume": base_volume,
        "new_expected_volume": new_volume,
        "projected_total_margin": round(new_margin, 2),
        "recommendation_impact": recommendation_shift
    }


def run_multi_scenario_comparison(
    base_price: float = 89999.0,
    unit_cost: float = 68000.0,
    base_volume: int = 12000,
    max_capacity: int = 15000,
    base_marketing_inr: float = 50000000.0
) -> Dict[str, Any]:
    """
    Compares 4 strategic scenarios side-by-side:
    1. Base Case Strategy
    2. -10% Price Discount Penetration
    3. +15% Marketing Spend Expansion
    4. Cost Reduction & Process Optimization (-8% BOM)
    """
    # 1. Base Case
    rev_1 = base_price * base_volume
    margin_1 = (base_price - unit_cost) * base_volume
    margin_pct_1 = ((base_price - unit_cost) / base_price) * 100
    utilization_1 = (base_volume / max_capacity) * 100

    # 2. -10% Price Discount (-10% price, +15% volume)
    price_2 = base_price * 0.90
    vol_2 = int(base_volume * 1.15)
    rev_2 = price_2 * vol_2
    margin_2 = (price_2 - unit_cost) * vol_2
    margin_pct_2 = ((price_2 - unit_cost) / price_2) * 100
    utilization_2 = (vol_2 / max_capacity) * 100

    # 3. +15% Marketing Spend (+15% marketing, +20% volume up to capacity ceiling)
    vol_3 = min(int(base_volume * 1.20), max_capacity)
    rev_3 = base_price * vol_3
    margin_3 = (base_price - unit_cost) * vol_3 - (base_marketing_inr * 0.15)
    margin_pct_3 = (margin_3 / rev_3) * 100 if rev_3 > 0 else 0
    utilization_3 = (vol_3 / max_capacity) * 100

    # 4. Cost Optimization (-8% unit cost, base volume)
    cost_4 = unit_cost * 0.92
    rev_4 = base_price * base_volume
    margin_4 = (base_price - cost_4) * base_volume
    margin_pct_4 = ((base_price - cost_4) / base_price) * 100
    utilization_4 = (base_volume / max_capacity) * 100

    scenarios = [
        {
            "id": "base_case",
            "name": "Scenario 1: Base Case Strategy",
            "unit_price": f"Rs. {base_price:,.2f}",
            "unit_cost": f"Rs. {unit_cost:,.2f}",
            "volume": f"{base_volume:,} units",
            "revenue": f"Rs. {rev_1 / 1e7:.2f} Cr",
            "unit_margin_pct": f"{margin_pct_1:.1f}%",
            "total_net_margin": f"Rs. {margin_1 / 1e7:.2f} Cr",
            "plant_capacity_utilization": f"{utilization_1:.1f}%",
            "risk_rating": "MODERATE",
            "feasibility_score": 8.5,
            "key_tradeoff": "Controlled growth within existing factory headroom (80% utilization)."
        },
        {
            "id": "price_discount",
            "name": "Scenario 2: -10% Price Discount",
            "unit_price": f"Rs. {price_2:,.2f}",
            "unit_cost": f"Rs. {unit_cost:,.2f}",
            "volume": f"{vol_2:,} units",
            "revenue": f"Rs. {rev_2 / 1e7:.2f} Cr",
            "unit_margin_pct": f"{margin_pct_2:.1f}%",
            "total_net_margin": f"Rs. {margin_2 / 1e7:.2f} Cr",
            "plant_capacity_utilization": f"{utilization_2:.1f}%",
            "risk_rating": "HIGH (Margin Compression)",
            "feasibility_score": 6.8,
            "key_tradeoff": "Volume surges 15%, but margin % drops significantly from 24% to 16%."
        },
        {
            "id": "marketing_push",
            "name": "Scenario 3: +15% Marketing Spend",
            "unit_price": f"Rs. {base_price:,.2f}",
            "unit_cost": f"Rs. {unit_cost:,.2f}",
            "volume": f"{vol_3:,} units",
            "revenue": f"Rs. {rev_3 / 1e7:.2f} Cr",
            "unit_margin_pct": f"{margin_pct_3:.1f}%",
            "total_net_margin": f"Rs. {margin_3 / 1e7:.2f} Cr",
            "plant_capacity_utilization": f"{utilization_3:.1f}% (Nearing 15k Ceiling)",
            "risk_rating": "HIGH (Capacity Bottleneck)",
            "feasibility_score": 8.2,
            "key_tradeoff": "Revenue reaches Rs. 133 Cr, but production hits plant max ceiling (15,000 limit)."
        },
        {
            "id": "cost_optimization",
            "name": "Scenario 4: Cost & Assembly Optimization",
            "unit_price": f"Rs. {base_price:,.2f}",
            "unit_cost": f"Rs. {cost_4:,.2f}",
            "volume": f"{base_volume:,} units",
            "revenue": f"Rs. {rev_4 / 1e7:.2f} Cr",
            "unit_margin_pct": f"{margin_pct_4:.1f}%",
            "total_net_margin": f"Rs. {margin_4 / 1e7:.2f} Cr",
            "plant_capacity_utilization": f"{utilization_4:.1f}%",
            "risk_rating": "LOW",
            "feasibility_score": 9.2,
            "key_tradeoff": "8% cost reduction boosts gross margin to 30.5% without exceeding plant capacity."
        }
    ]

    best_scenario = max(scenarios, key=lambda s: s["feasibility_score"])

    recommendation = (
        f"RECOMMENDED BEST SCENARIO: '{best_scenario['name']}'. "
        f"Provides highest feasibility score ({best_scenario['feasibility_score']}/10) and gross margin ({best_scenario['unit_margin_pct']}) "
        f"while maintaining production safely within the {max_capacity:,} unit manufacturing capacity ceiling."
    )

    return {
        "scenarios": scenarios,
        "best_scenario": best_scenario,
        "recommendation": recommendation
    }
