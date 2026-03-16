"""Simple schema objects for workbook-based calculation scenarios."""

from dataclasses import dataclass
from typing import Dict, List


SCENARIO_NAMES = ("overflow", "turbidity", "bath_drain", "validation")


@dataclass(frozen=True)
class FieldSpec:
    """Human-readable field description used by the first engine skeleton."""

    internal_name: str
    display_label_ko: str
    unit: str
    meaning: str
    formula_note: str = ""


@dataclass(frozen=True)
class ScenarioSchema:
    """Field grouping for one scenario."""

    name: str
    input_fields: List[FieldSpec]
    intermediate_fields: List[FieldSpec]
    output_fields: List[FieldSpec]


def _f(
    internal_name: str,
    display_label_ko: str,
    unit: str,
    meaning: str,
    formula_note: str = "",
) -> FieldSpec:
    return FieldSpec(
        internal_name=internal_name,
        display_label_ko=display_label_ko,
        unit=unit,
        meaning=meaning,
        formula_note=formula_note,
    )


COMMON_INTERMEDIATE_FIELDS = [
    _f("actual_concentration", "실제 농도", "wt%", "사용 농도에서 오프셋을 뺀 값", "use - offset"),
    _f(
        "tank_return_concentration",
        "DEV. Tank 회수 농도",
        "wt%",
        "1장 처리 후 탱크 농도",
        "actual + increase per glass",
    ),
    _f("drs_supply_concentration", "DRS 공급 농도", "wt%", "DRS 공급 쪽 농도", "Scenario-specific"),
    _f("drs_flow_per_glass_lpm", "Glass 1장당 공급 유량(DRS)", "lpm", "1장 기준 DRS 유량"),
    _f("drs_drop_per_liter", "DRS 1Liter당 하락 농도", "wt%", "DRS 1L당 농도 하락"),
    _f("ccss_flow_per_glass_lpm", "Glass 1장당 공급 유량 (CCSS)", "lpm", "1장 기준 CCSS 유량"),
    _f("ccss_drop_per_liter", "CCSS 1Liter당 하락 농도", "wt%", "CCSS 1L당 농도 하락"),
    _f("control_difference", "관리 농도 차이 값", "wt%", "관리 농도와 develop 후 농도 차이"),
    _f("correction_amount_per_glass_l", "Glass develop에 대한 보정량", "Liter", "1장 기준 보정량"),
    _f("daily_correction_usage_l", "하루 사용량", "Liter/day", "하루 보정 사용량"),
    _f("correction_time_per_step_sec", "보정 타임 0.001당", "Sec", "0.001 기준 보정 시간"),
]


COMMON_OUTPUT_FIELDS = [
    _f("drs_to_dcs_supply_flow_lpm", "DRS → DCS 공급유량", "lpm", "최종 DRS 공급 유량"),
    _f(
        "ccss_usage_when_drs_running_lpm",
        "DRS 가동시 CCSS 분당 사용량",
        "lpm",
        "DRS 가동 중 CCSS 분당 사용량",
    ),
    _f(
        "ccss_direct_usage_lpm",
        "CCSS 사용시 CCSS분당 사용량",
        "lpm",
        "CCSS 직접 사용 시 분당 사용량",
    ),
    _f("drs_daily_usage_l", "DRS 하루 사용량", "Liter/day", "DRS 하루 사용량"),
    _f(
        "ccss_daily_usage_when_drs_running_l",
        "DRS 가동시 CCSS 하루 사용량",
        "Liter/day",
        "DRS 가동 중 CCSS 하루 사용량",
    ),
    _f(
        "ccss_daily_direct_usage_l",
        "CCSS 사용시 CCSS 하루 사용량",
        "Liter/day",
        "CCSS 직접 사용 시 하루 사용량",
    ),
]


SCENARIO_SCHEMAS: Dict[str, ScenarioSchema] = {
    "overflow": ScenarioSchema(
        name="overflow",
        input_fields=[
            _f("use_concentration", "사용 C2 농도", "wt%", "시작 C2 농도"),
            _f("offset_concentration", "Off Set C2 농도", "wt%", "차감할 오프셋 농도"),
            _f("tank_size_l", "Tank capa. (Operating Level)", "Liter", "메인 탱크 용량"),
            _f("increase_per_glass", "Glass 1장당 탄산염 증가농도", "wt%", "1장 처리 시 증가 농도"),
            _f("recycle_rate", "DRS 재생률(회수율) + CARRAY OVER(OUT)", "ratio", "회수율"),
            _f("tact_time_sec", "Tact time", "sec", "메인 tact time"),
            _f("safety_factor", "안전율", "ratio", "안전율 배수"),
            _f("control_concentration", "관리 농도", "wt%", "DCS/DIW 관리 농도"),
            _f("post_develop_concentration", "Glass develop후 농도", "wt%", "develop 후 농도"),
            _f("correction_flow_lpm", "보정 유량 (1분당)", "lpm", "보정 유량"),
        ],
        intermediate_fields=COMMON_INTERMEDIATE_FIELDS,
        output_fields=COMMON_OUTPUT_FIELDS
        + [_f("overflow_carryout_note", "carry out or over", "", "오버플로우 강조 표시", "TODO")],
    ),
    "turbidity": ScenarioSchema(
        name="turbidity",
        input_fields=[
            _f("use_concentration", "사용 탁도 농도", "wt%", "시작 탁도 농도"),
            _f("offset_concentration", "Off Set 탁도 농도", "wt%", "차감할 오프셋 농도"),
            _f("tank_size_l", "Tank Size", "Liter", "메인 탱크 용량"),
            _f("increase_per_glass", "Glass 1장당 탁도 증가농도", "wt%", "1장 처리 시 증가 농도"),
            _f("recycle_rate", "DRS 재생률(회수율) + CARRAY OVER(OUT)", "ratio", "회수율"),
            _f("manual_drs_supply_concentration", "DRS 공급 탁도", "wt%", "수동 DRS 공급 농도"),
            _f("manual_ccss_concentration", "CCSS 탁도", "wt%", "수동 CCSS 농도"),
            _f("tact_time_sec", "Tact time", "sec", "tact time"),
            _f("safety_factor", "안전율", "ratio", "안전율 배수"),
            _f("control_concentration", "관리 농도", "wt%", "관리 농도"),
            _f("post_develop_concentration", "Glass develop후 농도", "wt%", "develop 후 농도"),
            _f("correction_flow_lpm", "보정 유량 (1분당)", "lpm", "보정 유량"),
        ],
        intermediate_fields=COMMON_INTERMEDIATE_FIELDS,
        output_fields=COMMON_OUTPUT_FIELDS,
    ),
    "bath_drain": ScenarioSchema(
        name="bath_drain",
        input_fields=[
            _f("glass_volume_l", "Glass Size ( 6G : 1500X1850X4 )", "Liter", "유리 부피", "1500*1850*4/1000000"),
            _f("use_concentration", "사용 C2 농도", "wt%", "시작 C2 농도"),
            _f("offset_concentration", "Off Set C2 농도", "wt%", "차감할 오프셋 농도"),
            _f("tank_size_l", "Tank Size", "Liter", "메인 탱크 용량"),
            _f("increase_per_glass", "Glass 1장당 탄산염 증가농도", "wt%", "1장 처리 시 증가 농도"),
            _f("recycle_rate", "DRS 재생률(회수율) + CARRAY OVER(OUT)", "ratio", "회수율"),
            _f("tact_time_sec", "Tact time", "sec", "메인 tact time"),
            _f("safety_factor", "안전율", "ratio", "안전율 배수"),
            _f("control_concentration", "관리 농도", "wt%", "관리 농도"),
            _f("post_develop_concentration", "Glass develop후 농도", "wt%", "develop 후 농도"),
            _f("correction_flow_lpm", "보정 유량 (1분당)", "lpm", "보정 유량"),
        ],
        intermediate_fields=COMMON_INTERMEDIATE_FIELDS,
        output_fields=COMMON_OUTPUT_FIELDS,
    ),
    "validation": ScenarioSchema(
        name="validation",
        input_fields=[
            _f("use_concentration", "사용 C2 농도", "wt%", "시작 C2 농도"),
            _f("offset_concentration", "Off Set C2 농도", "wt%", "차감할 오프셋 농도"),
            _f("tank_size_l", "Tank Size", "Liter", "메인 탱크 용량"),
            _f("increase_per_glass", "Glass 1장당 탄산염 증가농도", "wt%", "1장 처리 시 증가 농도"),
            _f("recycle_rate", "DRS 재생률(회수율) + CARRAY OVER(OUT)", "ratio", "검증용 회수율"),
            _f("tact_time_sec", "Tact time", "sec", "메인 tact time"),
            _f("safety_factor", "안전율", "ratio", "검증용 안전율"),
            _f("control_concentration", "관리 농도", "wt%", "관리 농도"),
            _f("post_develop_concentration", "Glass develop후 농도", "wt%", "develop 후 농도"),
            _f("correction_flow_lpm", "보정 유량 (1분당)", "lpm", "보정 유량"),
        ],
        intermediate_fields=COMMON_INTERMEDIATE_FIELDS,
        output_fields=COMMON_OUTPUT_FIELDS,
    ),
}


def get_schema(name: str) -> ScenarioSchema:
    """Return the schema for one scenario name."""

    return SCENARIO_SCHEMAS[name]
