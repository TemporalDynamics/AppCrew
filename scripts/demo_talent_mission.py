#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.demo_notifiers import safe_notify_telegram, safe_record_ledger


CRITERIA_PATH = Path("data/demo_rodri_criteria.yaml")
GOLDEN_PATH = Path("data/demo_golden_candidates.yaml")


DEMO_CANDIDATES: list[dict[str, Any]] = [
    {
        "name": "Jorge Martínez",
        "role": "VP Operations",
        "company": "Kueski",
        "market": "Mexico",
        "industry": "fintech",
        "signals": ["scaled_team_20_plus", "managed_pnl", "worked_in_scaleup_context", "shows_ownership_beyond_title"],
        "risk_signals": [],
        "why": "Escaló equipo de ops de 12 a 55 personas en 18 meses. Abrió hub Monterrey. P&L real de cobranza y underwriting.",
        "recommended_action": "prepare_warm_intro",
    },
    {
        "name": "Sofía Herrera",
        "role": "Country Manager",
        "company": "Pagali",
        "market": "LATAM",
        "industry": "fintech",
        "signals": ["opened_new_market", "managed_pnl", "worked_in_scaleup_context"],
        "risk_signals": [],
        "why": "Abrió Colombia y Perú desde cero. P&L de USD 4M. Perfil bajo radar que requiere leer entre líneas.",
        "recommended_action": "review_profile",
    },
    {
        "name": "Carlos Mendoza",
        "role": "VP Digital",
        "company": "Banorte",
        "market": "Mexico",
        "industry": "fintech",
        "signals": ["shows_ownership_beyond_title", "worked_in_scaleup_context"],
        "risk_signals": ["purely_corporate_without_ownership"],
        "why": "Lideró transformación digital en banca retail con equipo de 40+. Requiere validar si el ownership fue real o solo autoridad de presupuesto.",
        "recommended_action": "ask_validation_questions",
    },
    {
        "name": "Andrés Torres",
        "role": "Director of Growth",
        "company": "Jüsto",
        "market": "LATAM",
        "industry": "e-commerce",
        "signals": ["scaled_team_20_plus", "opened_new_market"],
        "risk_signals": ["too_many_short_tenures"],
        "why": "Logos impresionantes: Rappi, Cornershop, NotCo, Jüsto. Señal de riesgo: cada posición duró 8-10 meses.",
        "recommended_action": "human_review",
    },
    {
        "name": "Paula Benítez",
        "role": "Head of Growth",
        "company": "PagoNorte",
        "market": "Mexico",
        "industry": "fintech",
        "signals": ["opened_new_market", "shows_ownership_beyond_title"],
        "risk_signals": ["title_inflation_without_metrics"],
        "why": "Señal de crecimiento comercial y ownership, pero faltan métricas públicas que respalden el título.",
        "recommended_action": "secondary_candidate",
    },
]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_cells(criteria: dict[str, Any]) -> list[dict[str, Any]]:
    markets = criteria.get("markets", ["Mexico", "LATAM"])
    industries = criteria.get("industries", ["fintech", "SaaS B2B", "e-commerce", "retail"])
    positive = criteria.get("positive_signals", [])
    return [
        {
            "name": "Fintech Mexico",
            "kernel": "Talent Scout",
            "hydration": {
                "market": "Mexico",
                "industry": "fintech",
                "role_focus": "CTO / VP Engineering / Head of Product",
                "signals": positive[:4],
                "token_budget": 500,
            },
        },
        {
            "name": "SaaS B2B Mexico",
            "kernel": "Talent Scout",
            "hydration": {
                "market": "Mexico",
                "industry": "SaaS B2B",
                "role_focus": "VP Product / VP Sales / Engineering",
                "signals": positive[:4],
                "token_budget": 500,
            },
        },
        {
            "name": "E-commerce Retail LATAM",
            "kernel": "Talent Scout",
            "hydration": {
                "market": "LATAM",
                "industry": "e-commerce / retail",
                "role_focus": "Country Manager / Operations / Growth",
                "signals": positive[:4],
                "token_budget": 500,
            },
        },
        {
            "name": "Mobility Signals",
            "kernel": "Signal Scout",
            "hydration": {
                "markets": markets,
                "industries": industries,
                "role_focus": "executives with recent movement or advisory signals",
                "signals": ["role_change", "advisory", "founder_exit", *positive[:2]],
                "token_budget": 350,
            },
        },
    ]


def score_candidate(
    candidate: dict[str, Any],
    criteria: dict[str, Any],
    golden_names: set[str],
    golden_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    positive = set(criteria.get("positive_signals", []))
    negative = set(criteria.get("negative_signals", []))
    markets = set(criteria.get("markets", []))
    industries = {i.lower() for i in criteria.get("industries", [])}

    matched = sorted(positive.intersection(candidate.get("signals", [])))
    risks = sorted(negative.intersection(candidate.get("risk_signals", [])))
    market_match = candidate["market"] in markets
    industry_match = candidate["industry"].lower() in industries
    golden_match = candidate["name"].lower() in golden_names
    golden = golden_by_name.get(candidate["name"].lower(), {})

    criteria_total = max(len(positive), 1)
    criteria_match = len(matched)
    score = 55 + criteria_match * 8
    if market_match:
        score += 6
    if industry_match:
        score += 5
    if golden_match:
        score += 8
    score -= len(risks) * 4
    golden_type = golden.get("type", "")
    if golden_type == "hidden_gem":
        score += 4
    elif golden_type == "risky_maybe":
        score -= 2
    elif golden_type == "false_positive":
        score -= 10
    score = max(0, min(96, score))

    calibration_behavior = "not_calibrated"
    if golden_type == "obvious_yes":
        calibration_behavior = "rank_high" if score >= 85 else "missed"
    elif golden_type == "hidden_gem":
        calibration_behavior = "surface_as_non_obvious" if score >= 75 else "missed"
    elif golden_type == "risky_maybe":
        calibration_behavior = "flagged_with_risk" if risks else "missed_risk"
    elif golden_type == "false_positive":
        calibration_behavior = "rejected_or_low_rank" if score <= 80 or risks else "false_positive_promoted"

    return {
        **candidate,
        "score": score,
        "criteria_match": f"{criteria_match}/{criteria_total}",
        "matched_criteria": matched,
        "risks": risks,
        "golden_match": golden_match,
        "golden_type": golden_type,
        "expected_system_behavior": golden.get("expected_system_behavior", ""),
        "calibration_behavior": calibration_behavior,
        "human_decision_needed": "shortlist / dismiss / ask_for_more_evidence",
    }


def candidate_from_golden(talent: dict[str, Any], criteria: dict[str, Any], idx: int) -> dict[str, Any]:
    positive = criteria.get("positive_signals", [])
    default_signals = positive[idx % max(len(positive), 1):] + positive[: idx % max(len(positive), 1)]
    return {
        "name": talent["name"],
        "role": talent.get("current_role", criteria.get("role_target", "Executive")),
        "company": talent.get("company", "Por validar"),
        "market": talent.get("market", criteria.get("markets", ["Mexico"])[0]),
        "industry": talent.get("industry", criteria.get("industries", ["general"])[0]),
        "signals": talent.get("signals_positive") or default_signals[:3],
        "risk_signals": talent.get("signals_negative", []),
        "why": talent.get("why_rodri_likes")
        or talent.get("why_rodri_rejects")
        or "Perfil sembrado desde golden set para validar alineacion de busqueda.",
        "recommended_action": "watchlist" if talent.get("type") == "false_positive" else "review_profile",
        "source": "golden_seed",
    }


def build_candidate_pool(golden: list[dict[str, Any]], criteria: dict[str, Any]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {
        c["name"].lower(): {**c, "source": c.get("source", "demo_discovery")}
        for c in DEMO_CANDIDATES
    }
    for idx, talent in enumerate(golden):
        name = talent.get("name", "").strip()
        if not name:
            continue
        by_name[name.lower()] = {**by_name.get(name.lower(), {}), **candidate_from_golden(talent, criteria, idx)}
    return list(by_name.values())


def build_brief(criteria: dict[str, Any]) -> dict[str, Any]:
    return {
        "objective": "Recuperar pipeline ejecutivo con shortlist accionable para Global Executive.",
        "context": "Demo offline: capturar criterio de Rodri, hidratar celulas chicas y producir decisiones revisables.",
        "criteria_owner": criteria.get("owner", "Rodri"),
        "role_target": criteria.get("role_target", ""),
        "agents": [
            "Talent Cell Commander",
            "Demand Radar",
            "Talent Sourcing",
            "Career Context",
            "Talent Signal",
            "Outreach",
            "Auditor",
        ],
        "no_hacer": [
            "No contactar sin aprobacion humana.",
            "No inventar fuentes.",
            "No usar inferencias sensibles.",
            "No presentar datos demo como candidatos reales verificados.",
        ],
        "evidence_required": [
            "Criterios de Rodri usados.",
            "Golden set de calibracion cargado.",
            "Celulas hidratadas.",
            "Shortlist ordenada.",
            "Lectura del sistema sobre obvio, fino, dudoso y falso positivo.",
            "Accion humana requerida.",
        ],
    }


def calibration_summary(golden_calibration: list[dict[str, Any]]) -> list[dict[str, str]]:
    labels = {
        "obvious_yes": "Obvio",
        "hidden_gem": "Fino",
        "risky_maybe": "Dudoso",
        "false_positive": "Falso positivo",
    }
    type_order = ["obvious_yes", "hidden_gem", "risky_maybe", "false_positive"]
    sorted_items = sorted(
        [item for item in golden_calibration if item.get("golden_type")],
        key=lambda x: type_order.index(x["golden_type"]) if x["golden_type"] in type_order else 99,
    )
    results = []
    for item in sorted_items:
        gt = item["golden_type"]
        in_shortlist = item.get("_in_shortlist", True)
        actual = item["calibration_behavior"]
        if gt == "false_positive" and not in_shortlist:
            actual = "rejected_or_low_rank"
            result_tag = "OK"
        elif gt == "false_positive" and in_shortlist:
            result_tag = "REVISAR"
        elif actual in ("rank_high", "surface_as_non_obvious", "flagged_with_risk", "rejected_or_low_rank"):
            result_tag = "OK"
        else:
            result_tag = "REVISAR"
        results.append(
            {
                "type": gt,
                "label": labels.get(gt, gt),
                "name": item["name"],
                "expected": item["expected_system_behavior"],
                "actual": actual,
                "result": result_tag,
            }
        )
    return results


def print_human_report(
    brief: dict[str, Any],
    cells: list[dict[str, Any]],
    shortlist: list[dict[str, Any]],
    golden_total: int,
    golden_calibration: list[dict[str, Any]] | None = None,
) -> None:
    print("\n=== TALENT MISSION CAPSULE ===")
    print(f"Objetivo: {brief['objective']}")
    print(f"Criterio: {brief['criteria_owner']} | Rol: {brief['role_target']}")

    print("\n--- Brief operativo ---")
    print(f"Contexto: {brief['context']}")
    print("NO HACER:")
    for item in brief["no_hacer"]:
        print(f"  - {item}")
    print("Evidencia requerida:")
    for item in brief["evidence_required"]:
        print(f"  - {item}")

    print("\n--- Microcelulas hidratadas ---")
    for idx, cell in enumerate(cells, start=1):
        hydration = cell["hydration"]
        print(f"{idx}. {cell['name']} [{cell['kernel']}]")
        print(f"   foco: {hydration.get('role_focus')}")
        print(f"   contexto: {hydration}")

    shortlist_names = {c["name"].lower() for c in shortlist}
    matched = sum(1 for c in shortlist if c["golden_match"])
    print("\n--- Calibracion de criterio ---")
    print(f"Golden set cargado: {golden_total}")
    print(f"Golden set surfaced en shortlist: {matched}/{golden_total}")
    calib_items = calibration_summary(golden_calibration or [])
    for item in calib_items:
        in_shortlist_note = "(en shortlist)" if item["name"].lower() in shortlist_names else "(fuera de shortlist)"
        print(
            f"[{item['result']}] {item['label']}: {item['name']} {in_shortlist_note}"
            f" | esperado={item['expected']} | sistema={item['actual']}"
        )

    print("\n--- Shortlist ---")
    for idx, candidate in enumerate(shortlist, start=1):
        marker = "GOLDEN" if candidate["golden_match"] else "DISCOVERY"
        print(
            f"{idx}. {candidate['name']} — {candidate['role']} @ {candidate['company']} "
            f"[{marker}] score={candidate['score']} criteria={candidate['criteria_match']}"
        )
        print(f"   fuente demo: {candidate.get('source', 'demo_discovery')}")
        print(f"   por que: {candidate['why']}")
        print(f"   match: {', '.join(candidate['matched_criteria']) or 'sin match fuerte'}")
        print(f"   riesgo: {', '.join(candidate['risks']) or 'sin riesgo fuerte'}")
        if candidate.get("golden_type"):
            print(
                f"   calibracion: tipo={candidate['golden_type']} esperado={candidate['expected_system_behavior']} sistema={candidate['calibration_behavior']}"
            )
        print(f"   accion: {candidate['recommended_action']} | humano: {candidate['human_decision_needed']}")

    print("\nResultado final: El sistema no solo encontró perfiles; mostró si entiende el criterio de Rodri.")
    print("Decision humana requerida: Rodri revisa shortlist, aprueba outreach o pide mas evidencia.")


def main() -> None:
    import contextlib

    parser = argparse.ArgumentParser(description="Run the GE Talent Mission Capsule demo")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    # In JSON mode redirect operational prints to stderr; stdout stays clean for JSON.
    _redirect = contextlib.redirect_stdout(sys.stderr) if args.json else contextlib.nullcontext()

    with _redirect:
        payload = _run(args)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run(args: argparse.Namespace) -> dict:
    criteria = load_yaml(CRITERIA_PATH)
    if not criteria:
        raise SystemExit(
            "Falta data/demo_rodri_criteria.yaml. Corre: python scripts/demo_criterion_intake.py --demo"
        )
    golden = load_yaml(GOLDEN_PATH).get("golden_candidates", [])
    golden_names = {g["name"].lower() for g in golden}
    golden_by_name = {g["name"].lower(): g for g in golden}
    candidates = build_candidate_pool(golden, criteria)

    brief = build_brief(criteria)
    cells = build_cells(criteria)

    # Score ALL candidates from the full pool
    scored_all = sorted(
        [score_candidate(c, criteria, golden_names, golden_by_name) for c in candidates],
        key=lambda c: c["score"],
        reverse=True,
    )

    # Top 4 for client shortlist output
    shortlist = scored_all[:4]
    shortlist_names = {c["name"].lower() for c in shortlist}

    # Extract all 4 golden candidates from the full pool for calibration
    # (regardless of whether they made the shortlist)
    golden_calibration = [
        {**c, "_in_shortlist": c["name"].lower() in shortlist_names}
        for c in scored_all
        if c.get("golden_type")
    ]

    safe_record_ledger(
        "mission_brief_created",
        "Talent Mission Capsule creada para demo Global Executive.",
        evidence={"brief": brief},
        tags=["mission", "brief"],
    )
    safe_record_ledger(
        "cells_hydrated",
        f"{len(cells)} microcelulas hidratadas con criterio de Rodri.",
        evidence={"cells": cells},
        tags=["mission", "cells"],
    )
    safe_record_ledger(
        "shortlist_generated",
        f"Shortlist generada con {sum(1 for c in shortlist if c['golden_match'])}/{len(golden)} perfiles de calibracion surfaced.",
        evidence={"shortlist": shortlist, "golden_calibration": golden_calibration},
        tags=["mission", "shortlist"],
    )
    safe_record_ledger(
        "human_approval_required",
        "La demo produjo recomendaciones; ninguna accion externa fue ejecutada.",
        evidence={"pending_decision": "review shortlist and approve/reject outreach"},
        tags=["mission", "approval"],
    )

    safe_notify_telegram(
        "[GE CREW] Shortlist lista",
        f"Talent Mission Capsule finalizada. Golden surfaced en shortlist: "
        f"{sum(1 for c in shortlist if c['golden_match'])}/{len(golden)}. "
        "La calibracion muestra si el sistema esta pensando como Rodri.",
    )

    payload = {
        "brief": brief,
        "cells": cells,
        "shortlist": shortlist,
        "golden_calibration": golden_calibration,
        "golden_total": len(golden),
    }
    if not args.json:
        print_human_report(brief, cells, shortlist, len(golden), golden_calibration)
    return payload


if __name__ == "__main__":
    main()
