"""Scenario calculator skeleton built from docs/calculation_model.md."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Mapping, Optional

from engine.schemas import SCENARIO_SCHEMAS, ScenarioSchema


Number = Optional[float]
DIW_CORRECTION_DELTAS = {
    "diw_amount_plus_0_001_l": 0.001,
    "diw_amount_plus_0_003_l": 0.003,
    "diw_amount_plus_0_005_l": 0.005,
}


@dataclass
class CalculationResult:
    """Simple result container for review-friendly outputs."""

    scenario: str
    inputs: Dict[str, Number]
    intermediate: Dict[str, Number]
    outputs: Dict[str, Number]

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


def _value(inputs: Mapping[str, float], name: str) -> Number:
    raw = inputs.get(name)
    return float(raw) if raw is not None else None


def _blank_values(schema_fields) -> Dict[str, Number]:
    return {field.internal_name: None for field in schema_fields}


def _base_result(schema: ScenarioSchema, inputs: Mapping[str, float]) -> CalculationResult:
    cleaned_inputs = {field.internal_name: _value(inputs, field.internal_name) for field in schema.input_fields}
    return CalculationResult(
        scenario=schema.name,
        inputs=cleaned_inputs,
        intermediate=_blank_values(schema.intermediate_fields),
        outputs=_blank_values(schema.output_fields),
    )


def _safe_divide(numerator: Number, denominator: Number) -> Number:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _normalize_safety_factor(value: Number) -> Number:
    if value is None:
        return None
    return value / 100.0 if value > 10 else value


def _apply_common_core(result: CalculationResult, raw_inputs: Mapping[str, float]) -> None:
    """Apply only the most certain shared formulas from the design doc."""

    inputs = result.inputs
    intermediate = result.intermediate

    use_concentration = inputs.get("use_concentration")
    offset_concentration = inputs.get("offset_concentration")
    increase_per_glass = inputs.get("increase_per_glass")
    actual_concentration = None
    if use_concentration is not None and offset_concentration is not None:
        actual_concentration = use_concentration - offset_concentration
    intermediate["actual_concentration"] = actual_concentration

    tank_return_concentration = None
    if actual_concentration is not None and increase_per_glass is not None:
        tank_return_concentration = actual_concentration + increase_per_glass
    intermediate["tank_return_concentration"] = tank_return_concentration

    if result.scenario in {"overflow", "bath_drain"}:
        recycle_rate = inputs.get("recycle_rate")
        if recycle_rate is not None and tank_return_concentration is not None:
            intermediate["drs_supply_concentration"] = recycle_rate * tank_return_concentration
    elif result.scenario == "validation":
        recycle_rate = inputs.get("recycle_rate")
        if recycle_rate is not None and tank_return_concentration is not None and increase_per_glass is not None:
            intermediate["drs_supply_concentration"] = recycle_rate * (tank_return_concentration - increase_per_glass)

    # TODO: `turbidity` uses a manual workbook value for DRS supply concentration.
    manual_drs_supply_concentration = None
    if result.scenario == "turbidity":
        manual_drs_supply_concentration = inputs.get("manual_drs_supply_concentration")
    manual_ccss_concentration = None
    if result.scenario == "turbidity":
        manual_ccss_concentration = inputs.get("manual_ccss_concentration")

    drs_supply_for_flow = intermediate.get("drs_supply_concentration")
    if result.scenario == "turbidity":
        drs_supply_for_flow = manual_drs_supply_concentration

    tank_size_l = inputs.get("tank_size_l")
    if (
        tank_size_l is not None
        and tank_return_concentration is not None
        and actual_concentration is not None
        and drs_supply_for_flow is not None
    ):
        numerator = tank_size_l * (tank_return_concentration - actual_concentration)
        denominator = actual_concentration - drs_supply_for_flow
        intermediate["drs_flow_per_glass_lpm"] = _safe_divide(numerator, denominator)

    ccss_supply_for_flow = 0.0
    if result.scenario == "turbidity":
        ccss_supply_for_flow = manual_ccss_concentration
    if (
        tank_size_l is not None
        and tank_return_concentration is not None
        and actual_concentration is not None
        and ccss_supply_for_flow is not None
    ):
        numerator = tank_size_l * (tank_return_concentration - actual_concentration)
        denominator = actual_concentration - ccss_supply_for_flow
        intermediate["ccss_flow_per_glass_lpm"] = _safe_divide(numerator, denominator)

    tact_time_sec = inputs.get("tact_time_sec")
    safety_factor = _normalize_safety_factor(inputs.get("safety_factor"))
    recycle_rate = inputs.get("recycle_rate")
    drs_flow_per_glass = intermediate.get("drs_flow_per_glass_lpm")
    ccss_flow_per_glass = intermediate.get("ccss_flow_per_glass_lpm")
    if (
        drs_flow_per_glass is not None
        and tact_time_sec is not None
        and safety_factor is not None
        and recycle_rate is not None
    ):
        drs_to_dcs_supply_flow_lpm = drs_flow_per_glass * (tact_time_sec / 60.0) * safety_factor
        result.outputs["drs_to_dcs_supply_flow_lpm"] = drs_to_dcs_supply_flow_lpm
        result.outputs["ccss_usage_when_drs_running_lpm"] = drs_to_dcs_supply_flow_lpm * (1.0 - recycle_rate)

    if result.scenario in {"turbidity", "validation"} and ccss_flow_per_glass is not None and safety_factor is not None:
        result.outputs["ccss_direct_usage_lpm"] = ccss_flow_per_glass * safety_factor
    elif result.scenario == "bath_drain" and ccss_flow_per_glass is not None and safety_factor is not None:
        # Workbook/PDF support a bath-drain-only carry-out term of (11.2 × 0.05).
        result.outputs["ccss_direct_usage_lpm"] = (ccss_flow_per_glass * safety_factor) + (11.2 * 0.05)

    control_difference = _value(raw_inputs, "control_difference")
    intermediate["control_difference"] = control_difference

    post_develop_concentration = inputs.get("post_develop_concentration")
    if (
        tank_size_l is not None
        and control_difference is not None
        and post_develop_concentration is not None
    ):
        numerator = tank_size_l * control_difference
        denominator = 25.0 - post_develop_concentration
        intermediate["correction_amount_per_glass_l"] = _safe_divide(numerator, denominator)

    for output_name, overshoot_delta in DIW_CORRECTION_DELTAS.items():
        if tank_size_l is not None:
            result.outputs[output_name] = tank_size_l * overshoot_delta

    # TODO: Flow, correction-time, and daily-usage formulas are intentionally left out
    # for now so the first engine step only contains the most certain shared math.


def calculate_overflow(inputs: Mapping[str, float]) -> CalculationResult:
    result = _base_result(SCENARIO_SCHEMAS["overflow"], inputs)
    _apply_common_core(result, inputs)
    # TODO: Add overflow-specific carry-out handling when the business meaning is confirmed.
    return result


def calculate_turbidity(inputs: Mapping[str, float]) -> CalculationResult:
    result = _base_result(SCENARIO_SCHEMAS["turbidity"], inputs)
    _apply_common_core(result, inputs)
    # TODO: Add turbidity-specific direct CCSS usage once the manual-field logic is confirmed.
    return result


def calculate_bath_drain(inputs: Mapping[str, float]) -> CalculationResult:
    result = _base_result(SCENARIO_SCHEMAS["bath_drain"], inputs)
    _apply_common_core(result, inputs)
    # TODO: Add bath-drain glass-volume and quick-charge logic after workbook rules are confirmed.
    return result


def calculate_validation(inputs: Mapping[str, float]) -> CalculationResult:
    result = _base_result(SCENARIO_SCHEMAS["validation"], inputs)
    _apply_common_core(result, inputs)
    # TODO: Re-check validation-only formulas against the workbook before adding more math.
    return result
