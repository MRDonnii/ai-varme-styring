"""Heat economy model for AI Varme Styring."""

from __future__ import annotations

from math import isfinite
from typing import Any


GAS_KWH_PER_M3_DEFAULT = 10.55
GAS_BOILER_EFFICIENCY_DEFAULT = 0.94
DEFAULT_HEAT_PUMP_COP = 4.5


def _num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if isfinite(out) else None


def _round(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None else None


def _price_row(source: str, price: float | None, valid: bool, reason: str) -> dict[str, Any]:
    return {
        "source": source,
        "price_dkk_per_heat_kwh": _round(price, 4),
        "valid": bool(valid and price is not None),
        "reason": reason,
    }


def _heat_pump_price(el_price: Any, cop: Any = DEFAULT_HEAT_PUMP_COP) -> dict[str, Any]:
    el = _num(el_price)
    cop_f = _num(cop)
    if el is None:
        return _price_row("heat_pump", None, False, "missing electricity price")
    if cop_f is None or cop_f <= 1.0:
        return _price_row("heat_pump", None, False, "invalid COP")
    return _price_row("heat_pump", el / cop_f, True, f"el/COP {cop_f:.2f}")


def _gas_price(
    *,
    gas_price_dkk_per_m3: Any = None,
    gas_price_dkk_per_kwh_input: Any = None,
    efficiency: Any = GAS_BOILER_EFFICIENCY_DEFAULT,
    kwh_per_m3: Any = GAS_KWH_PER_M3_DEFAULT,
) -> dict[str, Any]:
    eff = _num(efficiency)
    if eff is None or eff <= 0.0 or eff > 1.2:
        return _price_row("gas", None, False, "invalid boiler efficiency")
    direct = _num(gas_price_dkk_per_kwh_input)
    if direct is not None:
        return _price_row("gas", direct / eff, True, f"gas kWh/eff {eff:.2f}")
    price_m3 = _num(gas_price_dkk_per_m3)
    kwh_m3 = _num(kwh_per_m3)
    if price_m3 is None or kwh_m3 is None or kwh_m3 <= 0:
        return _price_row("gas", None, False, "missing gas price")
    return _price_row("gas", price_m3 / (kwh_m3 * eff), True, f"m3/(kWh*m3*eff {eff:.2f})")


def _district_price(price: Any) -> dict[str, Any]:
    price_f = _num(price)
    if price_f is None:
        return _price_row("district_heat", None, False, "missing district heat price")
    return _price_row("district_heat", price_f, True, "direct tariff")


def build_heat_economy(
    *,
    rooms: list[dict[str, Any]],
    el_price_dkk_per_kwh: Any,
    heat_pump_price_dkk_per_heat_kwh: Any = None,
    heat_pump_cop: Any = DEFAULT_HEAT_PUMP_COP,
    heat_pump_el_kwh: Any = None,
    gas_price_dkk_per_m3: Any = None,
    gas_price_dkk_per_heat_kwh: Any = None,
    gas_price_dkk_per_kwh_input: Any = None,
    gas_m3: Any = None,
    gas_emitted_total_kwh: Any = None,
    gas_emitted_space_heat_kwh: Any = None,
    gas_emitted_dhw_kwh: Any = None,
    legionella_kwh: Any = None,
    district_price_dkk_per_kwh: Any = None,
    district_heat_kwh: Any = None,
    price_margin: float = 0.0,
) -> dict[str, Any]:
    """Build a measured-first economy payload for control and reporting."""
    validation_warnings: list[str] = []
    strategy_warnings: list[str] = []

    hp_price_direct = _num(heat_pump_price_dkk_per_heat_kwh)
    hp_price = (
        _price_row("heat_pump", hp_price_direct, True, "measured template")
        if hp_price_direct is not None
        else _heat_pump_price(el_price_dkk_per_kwh, heat_pump_cop)
    )
    gas_heat_price_direct = _num(gas_price_dkk_per_heat_kwh)
    prices = {
        "heat_pump": hp_price,
        "gas": (
            _price_row("gas", gas_heat_price_direct, True, "measured heat tariff")
            if gas_heat_price_direct is not None
            else _gas_price(
                gas_price_dkk_per_m3=gas_price_dkk_per_m3,
                gas_price_dkk_per_kwh_input=gas_price_dkk_per_kwh_input,
            )
        ),
        "district_heat": _district_price(district_price_dkk_per_kwh),
    }
    valid_prices = [
        row
        for row in prices.values()
        if row.get("valid") and row.get("price_dkk_per_heat_kwh") is not None
    ]
    cheapest = min(valid_prices, key=lambda x: x["price_dkk_per_heat_kwh"]) if valid_prices else None
    alt_rows = [p for p in valid_prices if p is not cheapest]
    next_best = min(alt_rows, key=lambda x: x["price_dkk_per_heat_kwh"]) if alt_rows else None
    savings_per_kwh = None
    if cheapest and next_best:
        savings_per_kwh = max(
            0.0,
            float(next_best["price_dkk_per_heat_kwh"]) - float(cheapest["price_dkk_per_heat_kwh"]),
        )

    gas_m3_f = _num(gas_m3)
    gas_input_kwh = gas_m3_f * GAS_KWH_PER_M3_DEFAULT if gas_m3_f is not None else None
    gas_total = _num(gas_emitted_total_kwh)
    gas_space = _num(gas_emitted_space_heat_kwh)
    gas_dhw = _num(gas_emitted_dhw_kwh)
    legionella = _num(legionella_kwh)
    if gas_input_kwh is not None and gas_total is not None and gas_input_kwh > 0:
        apparent_eff = gas_total / gas_input_kwh
        if apparent_eff > 1.10:
            validation_warnings.append(f"gas heat vs m3 is not physically consistent ({apparent_eff:.2f})")
    if gas_space is None and gas_input_kwh is not None:
        gas_space = max(
            0.0,
            gas_input_kwh * GAS_BOILER_EFFICIENCY_DEFAULT - (gas_dhw or 0.0) - (legionella or 0.0),
        )

    hp_el = _num(heat_pump_el_kwh)
    cop = _num(heat_pump_cop) or DEFAULT_HEAT_PUMP_COP
    hp_heat = hp_el * cop if hp_el is not None else None
    district_kwh = _num(district_heat_kwh)

    cold_rooms = [r for r in rooms if float(_num(r.get("deficit")) or 0.0) > 0.05]
    hp_cold = [r for r in cold_rooms if r.get("heat_pump")]
    radiator_cold = [r for r in cold_rooms if r.get("radiators") and not r.get("heat_pump")]
    hp_cheapest = bool(
        prices["heat_pump"].get("valid")
        and cheapest
        and cheapest.get("source") == "heat_pump"
        and (
            next_best is None
            or float(next_best["price_dkk_per_heat_kwh"]) - float(prices["heat_pump"]["price_dkk_per_heat_kwh"])
            >= price_margin
        )
    )
    radiator_price_rows = [p for p in (prices["district_heat"], prices["gas"]) if p.get("valid")]
    cheapest_radiator = min(
        radiator_price_rows,
        key=lambda x: x["price_dkk_per_heat_kwh"],
    ) if radiator_price_rows else None

    if not cold_rooms:
        strategy = "Klar"
        strategy_reason = "ingen rum med tydeligt varmeunderskud"
    elif hp_cheapest and hp_cold and radiator_cold:
        strategy = "Mix"
        strategy_reason = "varmepumpe dækker varmepumperum, radiator dækker øvrige kolde rum"
    elif hp_cheapest and hp_cold and len(hp_cold) == len(cold_rooms):
        strategy = "Varmepumpe"
        strategy_reason = "alle kolde rum kan dækkes af varmepumpe"
    elif cheapest_radiator:
        strategy = "Radiator"
        strategy_reason = f"{cheapest_radiator['source']} er bedste radiator-kilde for kolde rum"
    else:
        strategy = "Ukendt"
        strategy_reason = "mangler gyldigt prisgrundlag"

    overheat_waste_rooms = [
        str(r.get("name"))
        for r in rooms
        if r.get("heat_pump") and float(_num(r.get("surplus")) or 0.0) >= 0.7
    ]
    if overheat_waste_rooms:
        strategy_warnings.append("heat pump surplus rooms: " + ", ".join(overheat_waste_rooms[:8]))

    validated_savings = None
    confidence = "estimated"
    if validation_warnings:
        confidence = "not_validated"
    elif strategy_warnings:
        confidence = "strategy_review"
    elif hp_cheapest and savings_per_kwh is not None and hp_heat is not None:
        validated_savings = savings_per_kwh * hp_heat
        confidence = "measured_hp_estimated_substitution"

    return {
        "prices": prices,
        "cheapest_source": cheapest.get("source") if cheapest else None,
        "cheapest_price_dkk_per_heat_kwh": _round(cheapest.get("price_dkk_per_heat_kwh"), 4) if cheapest else None,
        "cheapest_radiator_source": cheapest_radiator.get("source") if cheapest_radiator else None,
        "cheapest_radiator_price_dkk_per_heat_kwh": _round(cheapest_radiator.get("price_dkk_per_heat_kwh"), 4)
        if cheapest_radiator else None,
        "strategy": strategy,
        "strategy_reason": strategy_reason,
        "estimated_savings_dkk_per_kwh": _round(savings_per_kwh, 4),
        "validated_savings_dkk": _round(validated_savings, 2),
        "confidence": confidence,
        "consumption": {
            "gas_m3": _round(gas_m3_f, 3),
            "gas_input_kwh": _round(gas_input_kwh, 3),
            "gas_space_heat_kwh": _round(gas_space, 3),
            "gas_dhw_kwh": _round(gas_dhw, 3),
            "gas_legionella_kwh": _round(legionella, 3),
            "heat_pump_el_kwh": _round(hp_el, 3),
            "heat_pump_heat_kwh": _round(hp_heat, 3),
            "district_heat_kwh": _round(district_kwh, 3),
        },
        "cold_rooms": [str(r.get("name")) for r in cold_rooms],
        "heat_pump_cold_rooms": [str(r.get("name")) for r in hp_cold],
        "radiator_cold_rooms": [str(r.get("name")) for r in radiator_cold],
        "validation_warnings": tuple(validation_warnings),
        "strategy_warnings": tuple(strategy_warnings),
        "warnings": tuple(validation_warnings + strategy_warnings),
    }
