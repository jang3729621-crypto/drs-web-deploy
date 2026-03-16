from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import streamlit as st

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
    
from engine.calculator import (
    CalculationResult,
    calculate_bath_drain,
    calculate_overflow,
    calculate_turbidity,
    calculate_validation,
)


APP_VERSION = "v1.0"
PRESETS_PATH = Path(__file__).with_name("presets.json")

UI_LABELS: Dict[str, str] = {
    "input_panel_title": "입력",
    "input_panel_caption": "주요 입력을 먼저 확인하고, 추가 조건은 고급 입력에서 조정하세요.",
    "preset_none": "선택 안 함",
    "preset_select": "저장된 프리셋",
    "preset_load": "불러오기",
    "preset_delete": "삭제",
    "preset_name": "새 프리셋 이름",
    "preset_name_placeholder": "예: 기본 조건",
    "preset_save": "저장",
    "preset_load_success": "프리셋을 불러왔습니다.",
    "preset_delete_success": "프리셋을 삭제했습니다.",
    "preset_save_success": "프리셋을 저장했습니다.",
    "preset_name_required": "프리셋 이름을 입력하세요.",
    "advanced_inputs": "고급 입력",
    "reset_defaults": "기본값 복원",
    "reset_defaults_help": "현재 시나리오 입력을 workbook 기본값으로 되돌립니다.",
    "operator_summary_title": "핵심 실행값",
    "operator_summary_caption": "현재 입력 기준 바로 확인할 값",
    "status_notes_title": "상태 / 주의사항",
    "category_details_title": "카테고리별 상세",
}

CARD_TITLES: Dict[str, str] = {
    "drs_base": "DRS 기준",
    "drs_ccss": "DRS 운전 시 CCSS",
    "ccss_direct": "CCSS 직접 사용",
    "stock_25": "TMAH 25% 보정",
    "diw": "DIW 보정",
}

CARD_NOTES: Dict[str, str] = {
    "drs_base": "현재 조건 기준 공급 농도",
    "drs_ccss": "분당 기준 보충량",
    "ccss_direct_default": "분당 기준 사용량",
    "ccss_direct_workbook": "workbook 기준 참고값",
    "ccss_direct_formula_review": "공식 재검토 항목",
    "stock_25": "보정 필요량",
    "diw": "단계별 기준량",
}


SCENARIO_DEFAULTS: Dict[str, Dict[str, float]] = {
    "overflow": {
        "use_concentration": 0.5,
        "offset_concentration": 0.1,
        "increase_per_glass": 0.0015,
        "tank_size_l": 580.0,
        "recycle_rate": 0.9,
        "tact_time_sec": 40.0,
        "safety_factor": 1.2,
        "control_difference": 0.003,
        "post_develop_concentration": 2.4475,
    },
    "turbidity": {
        "use_concentration": 0.3,
        "offset_concentration": 0.0,
        "increase_per_glass": 0.00462,
        "tank_size_l": 450.0,
        "recycle_rate": 0.9,
        "manual_drs_supply_concentration": 0.05,
        "manual_ccss_concentration": 0.0,
        "tact_time_sec": 60.0,
        "safety_factor": 1.2,
        "control_difference": 0.006,
        "post_develop_concentration": 2.377,
    },
    "bath_drain": {
        "use_concentration": 0.5,
        "offset_concentration": 0.2,
        "increase_per_glass": 0.001,
        "tank_size_l": 450.0,
        "recycle_rate": 0.9,
        "tact_time_sec": 60.0,
        "safety_factor": 1.2,
        "control_difference": 0.005,
        "post_develop_concentration": 2.377,
    },
    "validation": {
        "use_concentration": 0.5,
        "offset_concentration": 0.0,
        "increase_per_glass": 0.001,
        "tank_size_l": 450.0,
        "recycle_rate": 0.85,
        "tact_time_sec": 60.0,
        "safety_factor": 1.5,
        "control_difference": 0.004,
        "post_develop_concentration": 2.378,
    },
}


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "overflow": {
        "display_name": "C2 사용량(Overflow)",
        "sheet_name": "C2 사용량(Overflow)",
        "calculator": calculate_overflow,
        "status": "일부 항목 검토 필요",
        "status_note": "주요 결과는 사용 가능하지만 CCSS 사용시 CCSS분당 사용량은 workbook 불일치로 재확인 필요합니다.",
        "scenario_type": "c2",
    },
    "turbidity": {
        "display_name": "탁도 사용량",
        "sheet_name": "탁도 사용량",
        "calculator": calculate_turbidity,
        "status": "사용 가능",
        "status_note": "현재 화면에 표시되는 주요 결과는 사용 가능합니다. 일부 helper 값은 workbook 표기 기준으로 보여줍니다.",
        "scenario_type": "turbidity",
    },
    "bath_drain": {
        "display_name": "C2 사용량 (bath drain)",
        "sheet_name": "C2 사용량 (bath drain)",
        "calculator": calculate_bath_drain,
        "status": "사용 가능",
        "status_note": "현재 화면에 표시되는 주요 결과는 사용 가능합니다. bath drain 전용 carry-out 항이 direct CCSS 결과에 반영됩니다.",
        "scenario_type": "c2",
    },
    "validation": {
        "display_name": "C2 검증 Sheeet",
        "sheet_name": "C2 검증 Sheeet",
        "calculator": calculate_validation,
        "status": "사용 가능",
        "status_note": "검증 조건 기준으로 현재 표시되는 주요 결과는 사용 가능합니다. helper 값은 workbook 표기 기준으로 함께 제공합니다.",
        "scenario_type": "c2",
    },
}


INPUT_META: Dict[str, Dict[str, str]] = {
    "use_concentration": {"label": "사용 C2 농도", "unit": "wt%", "note": "현재 목표 사용값입니다."},
    "offset_concentration": {"label": "Off Set C2 농도", "unit": "wt%", "note": "실제 기준값을 잡을 때 빼는 값입니다."},
    "increase_per_glass": {"label": "Glass 1장당 탄산염 증가농도", "unit": "wt% / glass", "note": "패널 1장 처리 후 늘어나는 값입니다."},
    "tank_size_l": {"label": "Tank Size", "unit": "L", "note": "탱크 총 용량입니다."},
    "recycle_rate": {"label": "DRS 재생률(회수율) + CARRAY OVER(OUT)", "unit": "recycle rate", "note": "회수 비율입니다."},
    "tact_time_sec": {"label": "Tact time", "unit": "sec", "note": "연속 공급 유량 계산에 쓰는 tact time입니다."},
    "safety_factor": {"label": "안전율", "unit": "ratio", "note": "1.2 또는 120 모두 허용합니다."},
    "control_difference": {"label": "관리 농도 차이 값", "unit": "wt%", "note": "TMAH 25% 보정 기준 차이 값입니다."},
    "post_develop_concentration": {"label": "Glass develop후 농도", "unit": "wt%", "note": "패널 처리 후 TMAH 농도입니다."},
    "manual_drs_supply_concentration": {"label": "DRS 공급 탁도", "unit": "wt%", "note": "탁도 시나리오에서 직접 넣는 DRS 공급 값입니다."},
    "manual_ccss_concentration": {"label": "CCSS 농도", "unit": "wt%", "note": "탁도 시나리오에서 직접 넣는 CCSS 농도입니다."},
}


SCENARIO_INPUT_OVERRIDES: Dict[str, Dict[str, Dict[str, str]]] = {
    "overflow": {"tank_size_l": {"label": "Tank capa. (Operating Level)"}},
    "turbidity": {
        "use_concentration": {"label": "사용 탁도 농도"},
        "offset_concentration": {"label": "Off Set 탁도 농도"},
        "increase_per_glass": {"label": "Glass 1장당 탁도 증가농도"},
    },
    "bath_drain": {},
    "validation": {},
}


RESULT_META: Dict[str, Dict[str, Any]] = {
    "actual_concentration": {"label": "실제 C2 농도", "unit": "wt%", "note": "현재 제어 기준값입니다.", "source_type": "computed"},
    "tank_return_concentration": {"label": "DEV. Tank 회수 C2농도", "unit": "wt%", "note": "유리 1장 처리 후 탱크 농도입니다.", "source_type": "computed"},
    "drs_supply_concentration": {"label": "DRS 공급 C2 농도", "unit": "wt%", "note": "회수율을 반영한 DRS 공급 기준 농도입니다.", "source_type": "computed"},
    "drs_to_dcs_supply_flow_lpm": {"label": "DRS → DCS 공급유량", "unit": "LPM", "note": "현재 조건에서 연속 공급 기준으로 필요한 DRS 공급유량입니다.", "source_type": "computed"},
    "drs_flow_per_glass_lpm": {"label": "Glass 1장당 공급 유량(DRS)", "unit": "LPM (workbook 표기 기준 / 내부 helper 단계)", "note": "workbook 표기 기준의 보조 계산값입니다.", "source_type": "helper"},
    "ccss_usage_when_drs_running_lpm": {"label": "DRS 가동시 CCSS 분당 사용량", "unit": "LPM", "note": "현재 조건에서 DRS 운전 시 필요한 CCSS 보충량입니다.", "source_type": "computed"},
    "ccss_direct_usage_lpm": {"label": "CCSS 사용시 CCSS분당 사용량", "unit": "LPM", "note": "CCSS를 직접 사용할 때의 분당 기준 사용량입니다.", "source_type": "computed"},
    "ccss_flow_per_glass_lpm": {"label": "Glass 1장당 공급 유량(CCSS)", "unit": "LPM (workbook 표기 기준 / 내부 helper 단계)", "note": "workbook 표기 기준의 보조 계산값입니다.", "source_type": "helper"},
    "correction_amount_per_glass_l": {"label": "Glass develop에 대한 보정량", "unit": "L", "note": "TMAH 25% 원액 보정량입니다.", "source_type": "computed"},
    "stock_daily_usage_l": {"label": "하루 사용량 (TMAH 25%)", "unit": "L/day", "note": "TMAH 25% workbook 대표 하루 사용량입니다.", "source_type": "workbook_reference"},
    "stock_correction_time_per_step_sec": {"label": "보정 타임 0.001당 (TMAH 25%)", "unit": "sec", "note": "TMAH 25% workbook 표시 시간입니다.", "source_type": "workbook_reference"},
    "diw_amount_plus_0_001_l": {"label": "TMAH 0.001 상승시 보정량", "unit": "L", "note": "농도 +0.001 기준 DIW 보정량입니다.", "source_type": "computed"},
    "diw_amount_plus_0_003_l": {"label": "TMAH 0.003 상승시 보정량", "unit": "L", "note": "농도 +0.003 기준 DIW 보정량입니다.", "source_type": "computed"},
    "diw_amount_plus_0_005_l": {"label": "TMAH 0.005 상승시 보정량", "unit": "L", "note": "농도 +0.005 기준 DIW 보정량입니다.", "source_type": "computed"},
    "diw_correction_time_per_step_sec": {"label": "보정 타임 0.001당 (DIW)", "unit": "sec", "note": "DIW workbook 표시 시간입니다.", "source_type": "workbook_reference"},
}


WORKBOOK_REFERENCE_VALUES: Dict[str, Dict[str, float]] = {
    "overflow": {
        "ccss_direct_usage_lpm": 2.300000000000001,
        "stock_daily_usage_l": 244.42168274030453,
        "stock_correction_time_per_step_sec": 0.07715330894580319,
        "diw_correction_time_per_step_sec": 0.11600000000000002,
    },
    "turbidity": {
        "stock_daily_usage_l": 171.86049595544682,
        "stock_correction_time_per_step_sec": 0.11934756663572696,
        "diw_correction_time_per_step_sec": 0.09,
    },
    "bath_drain": {
        "stock_daily_usage_l": 143.21708,
        "stock_correction_time_per_step_sec": 0.198913,
        "diw_correction_time_per_step_sec": 0.09,
    },
    "validation": {
        "stock_daily_usage_l": 114.578729,
        "stock_correction_time_per_step_sec": 0.159137,
        "diw_correction_time_per_step_sec": 0.09,
    },
}


SUMMARY_FIELD_ORDER = [
    "actual_concentration",
    "tank_return_concentration",
    "drs_supply_concentration",
    "drs_to_dcs_supply_flow_lpm",
    "drs_flow_per_glass_lpm",
    "ccss_usage_when_drs_running_lpm",
    "ccss_direct_usage_lpm",
    "ccss_flow_per_glass_lpm",
    "correction_amount_per_glass_l",
    "stock_daily_usage_l",
    "stock_correction_time_per_step_sec",
    "diw_amount_plus_0_001_l",
    "diw_amount_plus_0_003_l",
    "diw_amount_plus_0_005_l",
    "diw_correction_time_per_step_sec",
]

PRIMARY_INPUT_FIELDS = ["use_concentration", "offset_concentration", "increase_per_glass", "tank_size_l"]
ADVANCED_INPUT_FIELDS = [
    "recycle_rate",
    "tact_time_sec",
    "safety_factor",
    "control_difference",
    "post_develop_concentration",
    "manual_drs_supply_concentration",
    "manual_ccss_concentration",
]


def _input_widget_key(scenario_name: str, field_name: str) -> str:
    return f"{scenario_name}:{field_name}"


def _preset_select_key(scenario_name: str) -> str:
    return f"{scenario_name}:preset_select"


def _preset_name_key(scenario_name: str) -> str:
    return f"{scenario_name}:preset_name"


def _pending_preset_select_key(scenario_name: str) -> str:
    return f"{scenario_name}:pending_preset_select"


def _reset_scenario_state_to_defaults(scenario_name: str, defaults: Mapping[str, float]) -> None:
    for field_name, default_value in defaults.items():
        st.session_state[_input_widget_key(scenario_name, field_name)] = default_value


def _format_number_by_unit(value: float, unit: str = "", field_key: str = "") -> str:
    if field_key in {"actual_concentration", "tank_return_concentration", "drs_supply_concentration"}:
        precision = 5
    elif unit in {"wt%", "wt% / glass"}:
        precision = 5
    elif unit in {"LPM", "L", "L/day", "sec"}:
        precision = 3
    elif unit in {"ratio", "recycle rate"}:
        precision = 4
    else:
        precision = 4
    return f"{value:.{precision}f}".rstrip("0").rstrip(".")


def _format_result(value: Any, unit: str = "", field_key: str = "") -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return _format_number_by_unit(value, unit, field_key)
    return str(value)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_ratio_for_compare(field_name: str, value: Any) -> float | None:
    numeric = _safe_float(value)
    if numeric is None:
        return None
    if field_name == "safety_factor" and numeric > 10:
        return numeric / 100.0
    if field_name == "recycle_rate" and numeric > 1:
        return numeric / 100.0
    return numeric


def _load_presets() -> Dict[str, Dict[str, Dict[str, float]]]:
    if not PRESETS_PATH.exists():
        return {}
    try:
        return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_presets(data: Mapping[str, Any]) -> None:
    PRESETS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _current_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S%z")


def _result_meta_for_scenario(scenario_name: str, field_key: str) -> Dict[str, Any]:
    meta = dict(RESULT_META[field_key])
    scenario_type = SCENARIOS[scenario_name]["scenario_type"]
    if field_key == "actual_concentration":
        meta["label"] = "실제 탁도 농도" if scenario_type == "turbidity" else "실제 C2 농도"
    elif field_key == "tank_return_concentration":
        meta["label"] = "DEV. Tank 회수 탁도농도" if scenario_type == "turbidity" else "DEV. Tank 회수 C2농도"
    elif field_key == "drs_supply_concentration":
        meta["label"] = "DRS 공급 탁도" if scenario_type == "turbidity" else "DRS 공급 C2 농도"
    return meta


def _normalize_result_state(state: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = dict(state)
    display_value = (
        normalized.get("display_value")
        if normalized.get("display_value") is not None
        else normalized.get("computed_value")
        if normalized.get("computed_value") is not None
        else normalized.get("value")
        if normalized.get("value") is not None
        else normalized.get("raw_value")
    )
    normalized["display_value"] = display_value
    normalized["display_text"] = (
        normalized.get("display_text")
        or normalized.get("value_text")
        or _format_result(display_value, normalized.get("unit", ""), normalized.get("field_key", ""))
    )
    normalized["status"] = normalized.get("status", "")
    normalized["note"] = normalized.get("note", "")
    normalized["unit"] = normalized.get("unit", "")
    normalized["label"] = normalized.get("label", "")
    normalized["field_key"] = normalized.get("field_key", "")
    normalized["source_type"] = normalized.get("source_type", "computed")
    return normalized


def _source_value_for_field(result: CalculationResult, field_key: str) -> float | None:
    if field_key in result.intermediate:
        return result.intermediate.get(field_key)
    return result.outputs.get(field_key)


def _reference_matches_current_defaults(scenario_name: str, inputs: Mapping[str, Any]) -> bool:
    defaults = SCENARIO_DEFAULTS[scenario_name]
    for field_name, default_value in defaults.items():
        current_value = inputs.get(field_name)
        if field_name in {"recycle_rate", "safety_factor"}:
            default_cmp = _normalize_ratio_for_compare(field_name, default_value)
            current_cmp = _normalize_ratio_for_compare(field_name, current_value)
        else:
            default_cmp = _safe_float(default_value)
            current_cmp = _safe_float(current_value)
        if default_cmp is None and current_cmp is None:
            continue
        if default_cmp is None or current_cmp is None:
            return False
        if abs(default_cmp - current_cmp) > 1e-9:
            return False
    return True


def _reference_display_state(
    scenario_name: str,
    field_key: str,
    inputs: Mapping[str, Any],
    *,
    value: float | None = None,
    status: str | None = None,
    note: str | None = None,
) -> Dict[str, Any]:
    meta = _result_meta_for_scenario(scenario_name, field_key)
    reference_value = value if value is not None else WORKBOOK_REFERENCE_VALUES.get(scenario_name, {}).get(field_key)
    reference_note = note or meta["note"]
    if not _reference_matches_current_defaults(scenario_name, inputs):
        reference_note = f"{reference_note} 현재 입력 기준 재계산값이 아니며, 입력 변경 시 참고용입니다."
    return _normalize_result_state(
        {
            "field_key": field_key,
            "label": meta["label"],
            "display_value": reference_value,
            "status": status or "workbook 기준값",
            "note": reference_note,
            "unit": meta["unit"],
            "source_type": "workbook_reference",
        }
    )


def _result_display_state(
    scenario_name: str,
    config: Mapping[str, Any],
    inputs: Mapping[str, Any],
    result: CalculationResult,
    field_key: str,
) -> Dict[str, Any]:
    meta = _result_meta_for_scenario(scenario_name, field_key)
    source_value = _source_value_for_field(result, field_key)

    if field_key == "drs_supply_concentration" and scenario_name == "turbidity":
        return _normalize_result_state(
            {
                "field_key": field_key,
                "label": meta["label"],
                "display_value": inputs.get("manual_drs_supply_concentration"),
                "status": "workbook 기준",
                "note": "탁도 시나리오는 workbook에서 수동 입력값을 기준으로 사용합니다.",
                "unit": meta["unit"],
                "source_type": "workbook_reference",
            }
        )

    if field_key == "ccss_direct_usage_lpm" and scenario_name == "overflow":
        return _reference_display_state(
            scenario_name,
            field_key,
            inputs,
            status="workbook 기준값 · 공식 재검토",
            note="overflow workbook 표시값 2.3 LPM을 우선 보여줍니다. 안전율 공식을 그대로 닫을 수 없어 공식 재검토가 필요합니다.",
        )

    if field_key in {"stock_daily_usage_l", "stock_correction_time_per_step_sec", "diw_correction_time_per_step_sec"}:
        return _reference_display_state(scenario_name, field_key, inputs)

    if source_value is not None:
        status = "검증완료" if meta["source_type"] == "computed" else "단위 재검토"
        return _normalize_result_state(
            {
                "field_key": field_key,
                "label": meta["label"],
                "display_value": source_value,
                "status": status,
                "note": meta["note"],
                "unit": meta["unit"],
                "source_type": meta["source_type"],
            }
        )

    if field_key in WORKBOOK_REFERENCE_VALUES.get(scenario_name, {}):
        return _reference_display_state(scenario_name, field_key, inputs)

    return _normalize_result_state(
        {
            "field_key": field_key,
            "label": meta["label"],
            "display_value": None,
            "status": "값 없음",
            "note": "현재 조건에서는 값을 만들 수 없습니다.",
            "unit": meta["unit"],
            "source_type": meta["source_type"],
        }
    )


def _build_result_summary_rows(config: Mapping[str, Any], result: CalculationResult) -> list[Dict[str, Any]]:
    scenario_name = result.scenario
    rows = []
    for field_key in SUMMARY_FIELD_ORDER:
        state = _result_display_state(scenario_name, config, result.inputs, result, field_key)
        rows.append(
            {
                "field_key": state["field_key"],
                "label": state["label"],
                "display_value": state["display_value"],
                "display_text": state["display_text"],
                "unit": state["unit"],
                "status": state["status"],
                "note": state["note"],
                "source_type": state["source_type"],
            }
        )
    return rows


def _summary_value_map(summary_rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        row.get("field_key", ""): _normalize_result_state(row).get("display_value")
        for row in summary_rows
        if row.get("field_key")
    }


def _summary_row_lookup(summary_rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        row.get("field_key", ""): _normalize_result_state(row)
        for row in summary_rows
        if row.get("field_key")
    }


def _summary_rows_to_csv(
    scenario_name: str,
    config: Mapping[str, Any],
    inputs: Mapping[str, Any],
    summary_rows: Iterable[Mapping[str, Any]],
    report_timestamp: str,
) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["구분", "항목", "값", "상태", "단위", "설명"])
    writer.writerow([])
    writer.writerow(["시나리오 정보", "시나리오 이름", scenario_name, "", "", "현재 선택한 시나리오의 내부 이름입니다."])
    writer.writerow(["시나리오 정보", "시나리오 표시명", config["display_name"], "", "", "보고서용 한글 시나리오 이름입니다."])
    writer.writerow(["시나리오 정보", "시나리오 상태", config["status"], "", "", "현재 앱 기준 사용 가능 상태입니다."])
    writer.writerow(["시나리오 정보", "상태 메모", config["status_note"], "", "", "workbook 검토 범위를 함께 적은 요약입니다."])
    writer.writerow(["시나리오 정보", "워크북 시트", config["sheet_name"], "", "", "검토 기준으로 본 워크북 시트입니다."])
    writer.writerow(["시나리오 정보", "보고서 생성 시각", report_timestamp, "", "", "현재 화면 기준으로 정리한 로컬 시각입니다."])
    writer.writerow([])
    for field_name, current_value in inputs.items():
        meta = dict(INPUT_META.get(field_name, {}))
        meta.update(SCENARIO_INPUT_OVERRIDES.get(scenario_name, {}).get(field_name, {}))
        writer.writerow(["입력값", meta.get("label", field_name), _format_result(current_value), "", meta.get("unit", ""), meta.get("note", "")])
    writer.writerow([])
    for row in summary_rows:
        state = _normalize_result_state(row)
        writer.writerow(["결과 요약", state["label"], state["display_text"], state["status"], state["unit"], state["note"]])
    return buffer.getvalue()


def _group_summary_rows(summary_rows: Iterable[Mapping[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    grouped = {"실시간 계산 결과": [], "workbook 기준 참고값": [], "helper / 검토용 값": []}
    for row in summary_rows:
        state = _normalize_result_state(row)
        grouped_key = "실시간 계산 결과"
        if state["source_type"] == "workbook_reference":
            grouped_key = "workbook 기준 참고값"
        elif state["source_type"] == "helper":
            grouped_key = "helper / 검토용 값"
        grouped[grouped_key].append(state)
    return grouped


def _summary_rows_to_report_html(report_context: Mapping[str, Any]) -> str:
    config = report_context["config"]
    grouped_rows = _group_summary_rows(report_context["summary_rows"])

    def _section_html(title: str, rows: Iterable[Mapping[str, Any]]) -> str:
        body = []
        for row in rows:
            state = _normalize_result_state(row)
            body.append(
                "<tr>"
                f"<td>{html.escape(state['label'])}</td>"
                f"<td>{html.escape(state['display_text'])}</td>"
                f"<td>{html.escape(state['unit'])}</td>"
                f"<td>{html.escape(state['status'])}</td>"
                f"<td>{html.escape(state['note'])}</td>"
                "</tr>"
            )
        return (
            f"<h2>{html.escape(title)}</h2>"
            "<table><thead><tr><th>결과 항목</th><th>값</th><th>단위</th><th>상태</th><th>설명</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    input_rows = []
    for field_name, field_value in report_context["inputs"].items():
        meta = dict(INPUT_META.get(field_name, {}))
        meta.update(SCENARIO_INPUT_OVERRIDES.get(report_context["scenario_name"], {}).get(field_name, {}))
        input_rows.append(
            "<tr>"
            f"<td>{html.escape(meta.get('label', field_name))}</td>"
            f"<td>{html.escape(_format_result(field_value))}</td>"
            f"<td>{html.escape(meta.get('unit', ''))}</td>"
            f"<td>{html.escape(meta.get('note', ''))}</td>"
            "</tr>"
        )

    sections = [ _section_html(title, rows) for title, rows in grouped_rows.items() if rows ]
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(config['display_name'])} 보고서</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 18px; color: #222; }}
    h1, h2 {{ margin: 0 0 10px; }}
    h2 {{ margin-top: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; table-layout: fixed; }}
    th, td {{ border: 1px solid #ccc; padding: 7px 9px; text-align: left; vertical-align: top; overflow-wrap: anywhere; word-break: keep-all; }}
    th {{ background: #f4f4f4; }}
    .meta td:first-child {{ width: 180px; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>{html.escape(config['display_name'])} 보고서</h1>
  <table class="meta">
    <tbody>
      <tr><td>시나리오 이름</td><td>{html.escape(report_context['scenario_name'])}</td></tr>
      <tr><td>시나리오 상태</td><td>{html.escape(config['status'])}</td></tr>
      <tr><td>상태 메모</td><td>{html.escape(config['status_note'])}</td></tr>
      <tr><td>워크북 시트</td><td>{html.escape(config['sheet_name'])}</td></tr>
      <tr><td>보고서 생성 시각</td><td>{html.escape(report_context['report_timestamp'])}</td></tr>
    </tbody>
  </table>
  <h2>현재 입력값</h2>
  <table><thead><tr><th>항목</th><th>값</th><th>단위</th><th>설명</th></tr></thead><tbody>{''.join(input_rows)}</tbody></table>
  {''.join(sections)}
</body>
</html>"""


def _status_badge_html(status: str) -> str:
    color_map = {
        "검증완료": "#0f766e",
        "workbook 기준": "#8b5cf6",
        "helper 참고": "#2563eb",
        "공식 재검토": "#b45309",
        "값 없음": "#6b7280",
    }
    color = color_map.get(status, "#475569")
    return (
        f"<span style='display:inline-block;padding:2px 8px;border:1px solid {color};"
        f"border-radius:999px;font-size:12px;font-weight:600;color:{color};'>{html.escape(status)}</span>"
    )


def _compact_note(text: str) -> str:
    return text if len(text) <= 56 else text[:53] + "..."


def _table_unit_text(row: Mapping[str, Any]) -> str:
    unit = str(row.get("unit", "")).strip()
    if " (" in unit:
        return unit.split(" (", 1)[0].strip()
    return unit


def _table_status_text(row: Mapping[str, Any]) -> str:
    source_type = str(row.get("source_type", ""))
    status = str(row.get("status", ""))
    if source_type == "helper":
        return "helper 참고"
    if "공식 재검토" in status:
        return "공식 재검토"
    if "workbook 기준" in status:
        return "workbook 기준"
    if status == "검증완료":
        return "검증완료"
    if status == "값 없음":
        return "값 없음"
    return status or "-"


def _table_note_text(row: Mapping[str, Any]) -> str:
    note = str(row.get("note", "")).strip()
    unit = str(row.get("unit", "")).strip()
    source_type = str(row.get("source_type", ""))
    if " (" in unit:
        unit_note = unit.split(" (", 1)[1].rstrip(")")
        note = f"{note} {unit_note}".strip()
    if source_type == "helper" and "보조 계산값" not in note:
        note = f"{note} 보조 계산값입니다.".strip()
    return _compact_note(note)


def _render_compact_state_line(prefix: str, state: Mapping[str, Any]) -> None:
    normalized = _normalize_result_state(state)
    st.markdown(
        f"<div style='margin-bottom:8px;'><strong>{html.escape(prefix)}</strong>: "
        f"{html.escape(normalized['display_text'])} {html.escape(normalized['unit'])} "
        f"{_status_badge_html(normalized['status'])}</div>",
        unsafe_allow_html=True,
    )


def _render_operator_summary(config: Mapping[str, Any], result: CalculationResult) -> None:
    st.markdown(f"### {UI_LABELS['operator_summary_title']}")
    st.caption(UI_LABELS["operator_summary_caption"])
    row_lookup = _summary_row_lookup(_build_result_summary_rows(config, result))
    _render_compact_state_line("DRS 공급 기준", row_lookup.get("drs_supply_concentration", {}))
    _render_compact_state_line("DRS 운전 시 CCSS 보충", row_lookup.get("ccss_usage_when_drs_running_lpm", {}))
    _render_compact_state_line("CCSS 직접 사용 기준량", row_lookup.get("ccss_direct_usage_lpm", {}))
    _render_compact_state_line("TMAH 25% 보정 필요량", row_lookup.get("correction_amount_per_glass_l", {}))
    diw_state = _normalize_result_state(row_lookup.get("diw_amount_plus_0_001_l", {}))
    if diw_state["display_value"] is not None:
        diw_003 = _normalize_result_state(row_lookup.get("diw_amount_plus_0_003_l", {}))
        diw_005 = _normalize_result_state(row_lookup.get("diw_amount_plus_0_005_l", {}))
        st.markdown(
            f"<div style='margin-bottom:8px;'><strong>DIW 보정량</strong>: "
            f"+0.001 {html.escape(diw_state['display_text'])} L / "
            f"+0.003 {html.escape(diw_003['display_text'])} L / "
            f"+0.005 {html.escape(diw_005['display_text'])} L "
            f"{_status_badge_html(diw_state['status'])}</div>",
            unsafe_allow_html=True,
        )


def _render_recommended_actions(config: Mapping[str, Any], result: CalculationResult) -> None:
    st.markdown(f"#### {UI_LABELS['status_notes_title']}")
    notes = [f"시나리오 상태: {config['status']}", config["status_note"]]
    if config["status"] != "사용 가능":
        notes.append("workbook 기준 참고값은 입력이 기본값과 다르면 현재 입력 기준 재계산값이 아닐 수 있습니다.")
    else:
        notes.append("helper / 보조 계산값은 계산 확인용입니다.")
    st.markdown(
        "<div style='border:1px solid rgba(148,163,184,0.24);border-radius:12px;padding:10px 12px;"
        "margin-top:10px;background:rgba(15,23,42,0.06);'>"
        + "".join(
            f"<div style='font-size:12px;opacity:0.86;margin-bottom:5px;'>{html.escape(note)}</div>"
            for note in notes[:3]
        )
        + "</div>",
        unsafe_allow_html=True,
    )
def _render_needed_actions_grouped(
    config: Mapping[str, Any],
    result: CalculationResult,
    summary_rows: Iterable[Mapping[str, Any]],
) -> None:
    row_lookup = _summary_row_lookup(summary_rows)
    st.markdown(f"### {UI_LABELS['category_details_title']}")
    st.caption("카테고리별로 세부 수치를 나눠 봅니다.")
    groups = [
        (
            "DRS / CCSS 대응",
            "연속 공급과 CCSS 보충 기준을 함께 봅니다.",
            "category-accent-drs",
            ["drs_to_dcs_supply_flow_lpm", "ccss_usage_when_drs_running_lpm", "ccss_direct_usage_lpm"],
        ),
        (
            "TMAH 25% 원액 보정",
            "현재 조건에서 필요한 TMAH 25% 보정량입니다.",
            "category-accent-stock",
            ["correction_amount_per_glass_l"],
        ),
        (
            "DIW 희석 보정",
            "상승 단계별 DIW 보정량을 확인합니다.",
            "category-accent-diw",
            ["diw_amount_plus_0_001_l", "diw_amount_plus_0_003_l", "diw_amount_plus_0_005_l"],
        ),
    ]
    columns = st.columns(3)
    for index, (title, subtitle, accent_class, keys) in enumerate(groups):
        with columns[index]:
            body_rows = []
            for key in keys:
                state = _normalize_result_state(row_lookup.get(key, {}))
                body_rows.append(
                    "<div class='category-item'>"
                    f"<div class='category-item-label'>{html.escape(state['label'])}</div>"
                    f"<div class='category-item-value'>{html.escape(state['display_text'])} {html.escape(state['unit'])}</div>"
                    f"<div class='category-item-status'>{_status_badge_html(state['status'])}</div>"
                    "</div>"
                )
            st.markdown(
                f"<div class='category-card {accent_class}'>"
                f"<div class='category-card-title'>{html.escape(title)}</div>"
                f"<div class='category-card-subtitle'>{html.escape(subtitle)}</div>"
                "<div class='category-card-divider'></div>"
                f"{''.join(body_rows)}"
                "</div>",
                unsafe_allow_html=True,
            )


def _render_grouped_summary_table(title: str, rows: Iterable[Mapping[str, Any]]) -> None:
    rows = [_normalize_result_state(row) for row in rows]
    if not rows:
        st.info("표시할 값이 없습니다.")
        return
    st.markdown(f"#### {title}")
    header_html = """
    <colgroup>
      <col style="width: 31%;">
      <col style="width: 13%;">
      <col style="width: 10%;">
      <col style="width: 14%;">
      <col style="width: 32%;">
    </colgroup>
    <thead>
      <tr>
        <th>결과 항목</th>
        <th>값</th>
        <th>단위</th>
        <th>상태</th>
        <th>설명</th>
      </tr>
    </thead>
    """
    body_rows = []
    for row in rows:
        table_unit = _table_unit_text(row)
        table_status = _table_status_text(row)
        table_note = _table_note_text(row)
        body_rows.append(
            "<tr>"
            f"<td class='summary-label'>{html.escape(str(row['label']))}</td>"
            f"<td class='summary-value'>{html.escape(str(row['display_text']))}</td>"
            f"<td class='summary-unit'>{html.escape(table_unit)}</td>"
            f"<td class='summary-status'><div class='summary-status-wrap'>{_status_badge_html(table_status)}</div></td>"
            f"<td class='summary-note'>{html.escape(table_note)}</td>"
            "</tr>"
        )
    st.markdown(
        "<div class='summary-table-wrap'>"
        "<table class='summary-report-table'>"
        f"{header_html}"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def _build_report_context(
    scenario_name: str,
    config: Mapping[str, Any],
    inputs: Mapping[str, Any],
    summary_rows: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "scenario_name": scenario_name,
        "config": config,
        "inputs": dict(inputs),
        "summary_rows": list(summary_rows),
        "report_timestamp": _current_timestamp(),
    }


def _render_report_only_mode(report_context: Mapping[str, Any]) -> None:
    config = report_context["config"]
    summary_rows = [_normalize_result_state(row) for row in report_context["summary_rows"]]
    st.markdown("## 인쇄용 보고서 전용 화면")
    st.markdown(f"### {config['display_name']}")
    st.table(
        [
            {"항목": "시나리오 이름", "값": report_context["scenario_name"]},
            {"항목": "시나리오 상태", "값": config["status"]},
            {"항목": "상태 메모", "값": config["status_note"]},
            {"항목": "워크북 시트", "값": config["sheet_name"]},
            {"항목": "보고서 생성 시각", "값": report_context["report_timestamp"]},
        ]
    )
    input_rows = []
    for field_name, field_value in report_context["inputs"].items():
        meta = dict(INPUT_META.get(field_name, {}))
        meta.update(SCENARIO_INPUT_OVERRIDES.get(report_context["scenario_name"], {}).get(field_name, {}))
        input_rows.append({"항목": meta.get("label", field_name), "값": _format_result(field_value), "단위": meta.get("unit", ""), "설명": meta.get("note", "")})
    st.markdown("#### 현재 입력값")
    st.table(input_rows)
    grouped = _group_summary_rows(summary_rows)
    for title, rows in grouped.items():
        _render_grouped_summary_table(title, rows)


def _parse_query_report_context() -> Dict[str, Any] | None:
    if st.query_params.get("mode") != "report":
        return None
    scenario_name = st.query_params.get("scenario")
    if not scenario_name or scenario_name not in SCENARIOS:
        return None
    inputs = dict(SCENARIO_DEFAULTS[scenario_name])
    for key in list(inputs.keys()):
        raw = st.query_params.get(key)
        if raw is not None:
            parsed = _safe_float(raw)
            if parsed is not None:
                inputs[key] = parsed
    config = SCENARIOS[scenario_name]
    result = config["calculator"](inputs)
    summary_rows = _build_result_summary_rows(config, result)
    return _build_report_context(scenario_name, config, inputs, summary_rows)


def _validate_inputs(inputs: Mapping[str, Any]) -> tuple[str, list[str]]:
    messages: list[str] = []
    if (_safe_float(inputs.get("tank_size_l")) or 0) <= 0:
        messages.append("Tank Size는 0보다 커야 합니다.")
    if (_safe_float(inputs.get("tact_time_sec")) or 0) <= 0:
        messages.append("Tact time은 0보다 커야 합니다.")
    safety = _normalize_ratio_for_compare("safety_factor", inputs.get("safety_factor"))
    if safety is not None and safety <= 0:
        messages.append("안전율은 0보다 커야 합니다.")
    recycle = _normalize_ratio_for_compare("recycle_rate", inputs.get("recycle_rate"))
    if recycle is not None and not 0 <= recycle <= 1:
        messages.append("재생률(회수율)은 0~1 또는 0~100 기준으로 입력해야 합니다.")
    for field_name in ("use_concentration", "offset_concentration", "increase_per_glass"):
        value = _safe_float(inputs.get(field_name))
        if value is not None and value < 0:
            messages.append(f"{INPUT_META[field_name]['label']}는 음수일 수 없습니다.")
    return ("정상 입력", []) if not messages else ("입력값 확인 필요", messages)


def _validate_unique_input_groups(scenario_name: str, primary_fields: Iterable[str], advanced_fields: Iterable[str]) -> None:
    overlap = sorted(set(primary_fields) & set(advanced_fields))
    if overlap:
        raise ValueError(f"Duplicate input field group configuration for scenario '{scenario_name}': {', '.join(overlap)}")


def _get_input_field_groups(scenario_name: str, defaults: Mapping[str, float]) -> tuple[list[str], list[str]]:
    primary_fields = list(PRIMARY_INPUT_FIELDS)
    if "recycle_rate" in defaults:
        primary_fields.append("recycle_rate")
    if "manual_drs_supply_concentration" in defaults:
        primary_fields.append("manual_drs_supply_concentration")
    primary_fields = list(dict.fromkeys(primary_fields))
    advanced_fields = [field for field in dict.fromkeys(ADVANCED_INPUT_FIELDS) if field in defaults and field not in primary_fields]
    _validate_unique_input_groups(scenario_name, primary_fields, advanced_fields)
    return primary_fields, advanced_fields


def _render_preset_load_delete_controls(scenario_name: str, defaults: Mapping[str, float]) -> None:
    presets = _load_presets().get(scenario_name, {})
    options = [UI_LABELS["preset_none"], *sorted(presets.keys())]
    select_key = _preset_select_key(scenario_name)
    pending_key = _pending_preset_select_key(scenario_name)
    pending_value = st.session_state.get(pending_key)
    if pending_value in options:
        st.session_state[select_key] = pending_value
        st.session_state.pop(pending_key, None)
    elif st.session_state.get(select_key) not in options:
        st.session_state[select_key] = UI_LABELS["preset_none"]

    col1, col2, col3 = st.columns([2.5, 0.85, 0.85], gap="small")
    with col1:
        st.selectbox(UI_LABELS["preset_select"], options, key=select_key)
    with col2:
        st.markdown("<div class='input-action-offset'></div>", unsafe_allow_html=True)
        if st.button(
            UI_LABELS["preset_load"],
            key=f"{scenario_name}:preset_load",
            use_container_width=True,
            disabled=st.session_state[select_key] == UI_LABELS["preset_none"],
        ):
            selected_values = presets.get(st.session_state[select_key], {})
            for field_name, default_value in defaults.items():
                st.session_state[_input_widget_key(scenario_name, field_name)] = selected_values.get(field_name, default_value)
            st.success(UI_LABELS["preset_load_success"])
            st.rerun()
    with col3:
        st.markdown("<div class='input-action-offset'></div>", unsafe_allow_html=True)
        if st.button(
            UI_LABELS["preset_delete"],
            key=f"{scenario_name}:preset_delete",
            use_container_width=True,
            disabled=st.session_state[select_key] == UI_LABELS["preset_none"],
        ):
            selected = st.session_state[select_key]
            if selected in presets:
                all_presets = _load_presets()
                all_presets.get(scenario_name, {}).pop(selected, None)
                if not all_presets.get(scenario_name):
                    all_presets.pop(scenario_name, None)
                _save_presets(all_presets)
                st.session_state[pending_key] = UI_LABELS["preset_none"]
                st.success(UI_LABELS["preset_delete_success"])
                st.rerun()
def _render_preset_save_controls(scenario_name: str, defaults: Mapping[str, float], inputs: Mapping[str, Any]) -> None:
    col1, col2, col3 = st.columns([2.0, 1.1, 1.1], gap="small")
    with col1:
        st.text_input(
            UI_LABELS["preset_name"],
            key=_preset_name_key(scenario_name),
            placeholder=UI_LABELS["preset_name_placeholder"],
        )
    with col2:
        st.markdown("<div class='input-action-offset'></div>", unsafe_allow_html=True)
        if st.button(UI_LABELS["preset_save"], key=f"{scenario_name}:preset_save", use_container_width=True):
            preset_name = st.session_state.get(_preset_name_key(scenario_name), "").strip()
            if not preset_name:
                st.warning(UI_LABELS["preset_name_required"])
            else:
                all_presets = _load_presets()
                scenario_presets = dict(all_presets.get(scenario_name, {}))
                scenario_presets[preset_name] = {
                    field_name: _safe_float(inputs.get(field_name)) if _safe_float(inputs.get(field_name)) is not None else defaults.get(field_name)
                    for field_name in defaults
                }
                all_presets[scenario_name] = scenario_presets
                _save_presets(all_presets)
                st.session_state[_pending_preset_select_key(scenario_name)] = preset_name
                st.success(UI_LABELS["preset_save_success"])
                st.rerun()
    with col3:
        st.markdown("<div class='input-action-offset'></div>", unsafe_allow_html=True)
        st.button(
            UI_LABELS["reset_defaults"],
            key=f"{scenario_name}:reset",
            use_container_width=True,
            on_click=_reset_scenario_state_to_defaults,
            args=(scenario_name, defaults),
        )
def _render_input_panel(scenario_name: str) -> Dict[str, Any]:
    defaults = SCENARIO_DEFAULTS[scenario_name]
    inputs: Dict[str, Any] = {}
    st.markdown(f"### {UI_LABELS['input_panel_title']}")
    st.caption(UI_LABELS["input_panel_caption"])
    _render_preset_load_delete_controls(scenario_name, defaults)
    primary_fields, advanced_fields = _get_input_field_groups(scenario_name, defaults)
    cols = st.columns(2, gap="medium")
    for index, field_name in enumerate(primary_fields):
        meta = dict(INPUT_META.get(field_name, {}))
        meta.update(SCENARIO_INPUT_OVERRIDES.get(scenario_name, {}).get(field_name, {}))
        with cols[index % 2]:
            inputs[field_name] = st.number_input(
                meta.get("label", field_name),
                value=float(defaults.get(field_name, 0.0)),
                key=_input_widget_key(scenario_name, field_name),
                format="%.4f",
                help=meta.get("note", ""),
            )
            st.caption(meta.get("unit", ""))
    with st.expander(UI_LABELS["advanced_inputs"], expanded=False):
        adv_cols = st.columns(2, gap="medium")
        for index, field_name in enumerate(advanced_fields):
            meta = dict(INPUT_META.get(field_name, {}))
            meta.update(SCENARIO_INPUT_OVERRIDES.get(scenario_name, {}).get(field_name, {}))
            with adv_cols[index % 2]:
                inputs[field_name] = st.number_input(
                    meta.get("label", field_name),
                    value=float(defaults.get(field_name, 0.0)),
                    key=_input_widget_key(scenario_name, field_name),
                    format="%.4f",
                    help=meta.get("note", ""),
                )
                st.caption(meta.get("unit", ""))
    _render_preset_save_controls(scenario_name, defaults, {**defaults, **inputs})
    return {**defaults, **inputs}
def _render_input_change_summary(scenario_name: str, inputs: Mapping[str, Any]) -> None:
    st.markdown("#### 입력 변경 요약")
    defaults = SCENARIO_DEFAULTS[scenario_name]
    changed_rows = []
    for field_name, default_value in defaults.items():
        current_value = inputs.get(field_name)
        if field_name in {"recycle_rate", "safety_factor"}:
            default_cmp = _normalize_ratio_for_compare(field_name, default_value)
            current_cmp = _normalize_ratio_for_compare(field_name, current_value)
        else:
            default_cmp = _safe_float(default_value)
            current_cmp = _safe_float(current_value)
        if default_cmp is None or current_cmp is None or abs(default_cmp - current_cmp) <= 1e-9:
            continue
        meta = dict(INPUT_META.get(field_name, {}))
        meta.update(SCENARIO_INPUT_OVERRIDES.get(scenario_name, {}).get(field_name, {}))
        changed_rows.append({"필드": meta.get("label", field_name), "기본값": _format_result(default_value), "현재 값": _format_result(current_value)})
    if changed_rows:
        st.caption("workbook 기준 참고값 항목은 기본값과 달라지면 현재 입력 기준 재계산값이 아닐 수 있습니다.")
        st.table(changed_rows)
    else:
        st.caption("현재 입력은 workbook 기본값과 같습니다.")


def _render_quick_help() -> None:
    with st.expander("빠른 사용법 / 해석 기준", expanded=False):
        st.markdown("- 먼저 볼 곳: `운전 요약`, `권장 조치`, `실시간 계산 결과`")
        st.markdown("- `workbook 기준`은 workbook reference value입니다.")
        st.markdown("- 상태 badge: `검증완료`, `workbook 기준`, `근사식`, `단위 재검토`, `공식 재검토`")
        st.markdown("- 필요하면 `워크북 기본값으로 되돌리기`를 눌러 초기화하세요.")


def _render_comparison_tab() -> None:
    live_fields = [
        "actual_concentration",
        "tank_return_concentration",
        "drs_supply_concentration",
        "drs_to_dcs_supply_flow_lpm",
        "ccss_usage_when_drs_running_lpm",
        "correction_amount_per_glass_l",
        "diw_amount_plus_0_001_l",
        "diw_amount_plus_0_003_l",
        "diw_amount_plus_0_005_l",
    ]
    table_rows = []
    for field_key in live_fields:
        row = {"결과 항목": _result_meta_for_scenario("overflow", field_key)["label"]}
        for scenario_name, config in SCENARIOS.items():
            summary_rows = _build_result_summary_rows(config, config["calculator"](SCENARIO_DEFAULTS[scenario_name]))
            row[config["display_name"]] = _summary_row_lookup(summary_rows)[field_key]["display_text"]
        table_rows.append(row)
    st.table(table_rows)


def _inject_ui_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 0.85rem; padding-bottom: 0.6rem; max-width: 1400px;}
        div[data-testid="stTabs"] button {
            font-size: 0.96rem;
            font-weight: 700;
            padding-top: 0.45rem;
            padding-bottom: 0.45rem;
        }
        div[data-testid="stNumberInput"], div[data-testid="stSelectbox"], div[data-testid="stTextInput"] {
            margin-bottom: -0.05rem;
        }
        div[data-testid="stCaptionContainer"] p {font-size: 0.78rem; opacity: 0.82;}
        div.stButton > button {min-height: 2.78rem;}
        .input-action-offset {height: 1.72rem;}
        .category-card {
            border: 1px solid rgba(148,163,184,0.24);
            border-radius: 14px;
            padding: 12px 13px;
            min-height: 100%;
            background: rgba(15,23,42,0.08);
        }
        .category-card-title {
            font-size: 0.96rem;
            font-weight: 700;
            margin-bottom: 3px;
        }
        .category-card-subtitle {
            font-size: 0.78rem;
            color: rgba(226,232,240,0.72);
            line-height: 1.35;
            margin-bottom: 8px;
        }
        .category-card-divider {
            height: 3px;
            border-radius: 999px;
            margin-bottom: 10px;
            background: rgba(148,163,184,0.22);
        }
        .category-accent-drs .category-card-divider {background: linear-gradient(90deg, #38bdf8, rgba(56,189,248,0.18));}
        .category-accent-stock .category-card-divider {background: linear-gradient(90deg, #f59e0b, rgba(245,158,11,0.18));}
        .category-accent-diw .category-card-divider {background: linear-gradient(90deg, #34d399, rgba(52,211,153,0.18));}
        .category-item {padding: 7px 0 8px 0; border-bottom: 1px solid rgba(148,163,184,0.12);}
        .category-item:last-child {border-bottom: none; padding-bottom: 0;}
        .category-item-label {
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 2px;
            line-height: 1.32;
        }
        .category-item-value {
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 4px;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }
        .category-item-status {display: inline-flex; align-items: center;}
        .summary-table-wrap {margin-top: 0.35rem;}
        .summary-report-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            border: 1px solid rgba(148,163,184,0.22);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(15,23,42,0.10);
        }
        .summary-report-table thead th {
            text-align: left;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.62rem 0.7rem;
            border-bottom: 1px solid rgba(148,163,184,0.20);
            background: rgba(148,163,184,0.08);
        }
        .summary-report-table tbody td {
            padding: 0.58rem 0.7rem;
            vertical-align: top;
            border-bottom: 1px solid rgba(148,163,184,0.12);
            line-height: 1.35;
            word-break: keep-all;
            overflow-wrap: anywhere;
        }
        .summary-report-table tbody tr:last-child td {border-bottom: none;}
        .summary-report-table .summary-label {font-weight: 600;}
        .summary-report-table .summary-value {
            font-weight: 700;
            white-space: nowrap;
            text-align: right;
        }
        .summary-report-table .summary-unit {
            color: rgba(226,232,240,0.88);
            white-space: nowrap;
            text-align: center;
        }
        .summary-report-table .summary-status {
            white-space: nowrap;
            text-align: center;
        }
        .summary-report-table .summary-status-wrap {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 1.9rem;
            max-width: 100%;
        }
        .summary-report-table .summary-status-wrap > span {
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .summary-report-table .summary-note {
            color: rgba(226,232,240,0.72);
            font-size: 0.84rem;
            line-height: 1.45;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def _render_scenario_view(scenario_name: str) -> None:
    config = SCENARIOS[scenario_name]
    st.markdown("## 운전 조건 선택")
    st.caption("입력을 먼저 확인하고, 오른쪽의 핵심 실행값을 우선 확인하세요.")
    left_col, right_col = st.columns([1.05, 0.95], gap="large")
    with left_col.container(border=True):
        inputs = _render_input_panel(scenario_name)
    with right_col.container(border=True):
        validation_status, validation_messages = _validate_inputs(inputs)
        if validation_status == "정상 입력":
            st.success("정상 입력")
        else:
            st.warning(validation_status)
            for message in validation_messages:
                st.write(f"- {message}")
        result = config["calculator"](inputs)
        _render_operator_summary(config, result)
        _render_recommended_actions(config, result)

    summary_rows = _build_result_summary_rows(config, result)
    _render_needed_actions_grouped(config, result, summary_rows)

    grouped = _group_summary_rows(summary_rows)
    tab_live, tab_ref, tab_helper, tab_export, tab_compare = st.tabs(
        ["실시간 계산 결과", "workbook 기준 참고값", "helper / 보조 계산값", "내보내기 / 보고서", "비교 / 검토"]
    )
    with tab_live:
        st.caption("현재 입력 기준으로 바로 계산되는 주요 결과입니다.")
        _render_grouped_summary_table("실시간 계산 결과", grouped["실시간 계산 결과"])
    with tab_ref:
        st.caption("workbook 기준 참고값입니다. 기본값과 다르면 현재 입력 기준 재계산값이 아닐 수 있습니다.")
        _render_grouped_summary_table("workbook 기준 참고값", grouped["workbook 기준 참고값"])
        _render_input_change_summary(scenario_name, inputs)
    with tab_helper:
        st.info("보조 계산값입니다. 메인 운전 판단값이 아니라 workbook 표기 추적이나 계산 확인용으로 보세요.")
        _render_grouped_summary_table("helper / 보조 계산값", grouped["helper / 검토용 값"])
        _render_quick_help()
    with tab_export:
        st.markdown("#### 내보내기 / 보고서")
        csv_text = _summary_rows_to_csv(scenario_name, config, inputs, summary_rows, _current_timestamp())
        report_context = _build_report_context(scenario_name, config, inputs, summary_rows)
        report_html = _summary_rows_to_report_html(report_context)
        export_cols = st.columns(2)
        with export_cols[0]:
            st.download_button("CSV 다운로드", data=csv_text, file_name=f"drs_result_summary_{scenario_name}.csv", mime="text/csv", use_container_width=True)
        with export_cols[1]:
            st.download_button("HTML 보고서 다운로드", data=report_html, file_name=f"{scenario_name}_report.html", mime="text/html", use_container_width=True)
    with tab_compare:
        _render_comparison_tab()


def main() -> None:
    st.set_page_config(page_title=f"DRS Calculator {APP_VERSION}", layout="wide")
    _inject_ui_css()
    report_context = _parse_query_report_context()
    if report_context is not None:
        _render_report_only_mode(report_context)
        st.stop()
    st.title(f"DRS Calculator {APP_VERSION}")
    st.caption("workbook 기반 DRS / CCSS / TMAH 25% / DIW 계산 도구")
    scenario_name = st.selectbox("시나리오 선택", list(SCENARIOS.keys()), format_func=lambda name: SCENARIOS[name]["display_name"])
    _render_scenario_view(scenario_name)


if __name__ == "__main__":
    main()
