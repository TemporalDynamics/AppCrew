#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.demo_notifiers import safe_notify_telegram, safe_record_ledger


OUT_PATH = Path("data/demo_rodri_criteria.yaml")


DEMO_CRITERIA: dict[str, Any] = {
    "owner": "Rodri",
    "role_target": "CTO / VP Engineering / Country Manager",
    "markets": ["Mexico", "LATAM"],
    "industries": ["fintech", "SaaS B2B", "e-commerce", "retail"],
    "positive_signals": [
        "opened_new_market",
        "managed_pnl",
        "scaled_team_20_plus",
        "worked_in_scaleup_context",
        "shows_ownership_beyond_title",
    ],
    "negative_signals": [
        "title_inflation_without_metrics",
        "too_many_short_tenures",
        "purely_corporate_without_ownership",
        "generic_profile_without_evidence",
    ],
    "preferred_background": "Startup o scale-up con algo de estructura; no caos puro, no corporativo sin ownership.",
    "outreach_tone": "Ejecutivo, calido, directo, sin tono masivo ni agresivo.",
    "hard_filters": [
        "no_contact_without_human_approval",
        "no_sensitive_inferences",
        "no_unverified_claims",
    ],
    "human_approval_required": True,
}


QUESTIONS = [
    ("role_target", "Rol objetivo"),
    ("markets", "Mercados objetivo, separados por coma"),
    ("industries", "Industrias foco, separadas por coma"),
    ("positive_signals", "Senales positivas, separadas por coma"),
    ("negative_signals", "Senales de riesgo, separadas por coma"),
    ("preferred_background", "Background preferido"),
    ("outreach_tone", "Tono de contacto"),
]


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def interactive_criteria() -> dict[str, Any]:
    print("Criterion Intake — Cerno\n")
    criteria = dict(DEMO_CRITERIA)
    for key, question in QUESTIONS:
        current = criteria[key]
        default = ", ".join(current) if isinstance(current, list) else str(current)
        answer = input(f"{question} [{default}]: ").strip()
        if not answer:
            continue
        criteria[key] = _split(answer) if isinstance(current, list) else answer
    criteria["human_approval_required"] = True
    return criteria


def write_criteria(criteria: dict[str, Any]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(criteria, f, allow_unicode=True, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo criterion intake for GE")
    parser.add_argument("--demo", action="store_true", help="Use curated demo answers")
    args = parser.parse_args()

    criteria = dict(DEMO_CRITERIA) if args.demo else interactive_criteria()
    write_criteria(criteria)

    summary = (
        f"Criterio cargado para {criteria['role_target']} en "
        f"{', '.join(criteria['markets'])}. "
        f"{len(criteria['positive_signals'])} senales positivas, "
        f"{len(criteria['negative_signals'])} riesgos."
    )

    print(f"\n[OK] Criterio GE escrito en {OUT_PATH}")
    print(summary)
    safe_record_ledger(
        "criterion_intake_created",
        summary,
        evidence={"path": str(OUT_PATH), "criteria": criteria},
        tags=["criterion", "demo"],
    )
    safe_notify_telegram(
        "[GE CREW] Criterio cargado",
        "Criterio de Rodri listo. Las celulas pueden hidratarse con reglas de busqueda y limites humanos.",
    )


if __name__ == "__main__":
    main()
