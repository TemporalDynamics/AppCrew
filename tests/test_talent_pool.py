import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from contracts.talent import CandidateSignal, CandidateEvidence


def _make_signal(name="Ana García", role="CEO", company="Acme", source="torre",
                 source_url="https://torre.co/ana_garcia", **kwargs) -> CandidateSignal:
    return CandidateSignal(
        name=name,
        current_role=role,
        company=company,
        location="Mexico City",
        source=source,
        source_url=source_url,
        availability_signal="open_to_work",
        skills=["leadership", "strategy"],
        evidence=[CandidateEvidence(label="headline", value="CEO at Acme", url=source_url)],
        raw_score=0.75,
        confidence="medium",
        **kwargs,
    )


def _patched_pool(tmp_path: Path):
    """Return a context manager that patches DB_PATH to a temp file."""
    import core.talent_pool as tp
    return patch.object(tp, "DB_PATH", tmp_path / "test_pool.db")


def test_upsert_dedup(tmp_path):
    """Insertar el mismo candidato dos veces → times_surfaced == 2"""
    import core.talent_pool as tp

    with patch.object(tp, "DB_PATH", tmp_path / "pool.db"):
        # Re-run _ensure_tables with patched path
        tp._ensure_tables()

        signal = _make_signal()
        key1 = tp.TalentPool.upsert_candidate(signal)
        key2 = tp.TalentPool.upsert_candidate(signal)

        assert key1 == key2, "Same signal should produce same dedup_key"

        with tp._get_db() as conn:
            row = conn.execute(
                "SELECT times_surfaced FROM candidates WHERE dedup_key = ?", (key1,)
            ).fetchone()
        assert row is not None
        assert row["times_surfaced"] == 2, f"Expected 2 but got {row['times_surfaced']}"


def test_blind_view_hides_name(tmp_path):
    """get_candidate_blind() no expone nombre real"""
    import core.talent_pool as tp

    with patch.object(tp, "DB_PATH", tmp_path / "pool.db"):
        tp._ensure_tables()

        signal = _make_signal(name="Rodrigo Betolaza")
        key = tp.TalentPool.upsert_candidate(signal)

        full = tp.TalentPool.get_candidate(key)
        blind = tp.TalentPool.get_candidate_blind(key)

        assert full is not None
        assert full["name"] == "Rodrigo Betolaza", "Full view should expose real name"

        assert blind["name"] != "Rodrigo Betolaza", "Blind view must not expose real name"
        assert blind["name"].startswith("Candidato #"), f"Expected blind ID prefix, got: {blind['name']}"
        assert blind["source_url"] == "", "Blind view must hide source_url"
        assert blind["company"] == "Empresa confidencial", "Blind view must hide company"

        # These must still be visible
        assert "availability_signal" in blind
        assert "skills" in blind
        assert "location" in blind


def test_coverage_report(tmp_path):
    """record_search + record_matches → get_search_coverage con conteos correctos"""
    import core.talent_pool as tp

    with patch.object(tp, "DB_PATH", tmp_path / "pool.db"):
        tp._ensure_tables()

        # Insert three candidates
        s1 = _make_signal(name="Ana García", source_url="https://torre.co/ana")
        s2 = _make_signal(name="Luis Pérez", source="brave_search", source_url="https://example.com/luis")
        s3 = _make_signal(name="María López", source_url="https://torre.co/maria")

        k1 = tp.TalentPool.upsert_candidate(s1)
        k2 = tp.TalentPool.upsert_candidate(s2)
        k3 = tp.TalentPool.upsert_candidate(s3)

        search_id = "search_test_001"
        tp.TalentPool.record_search(search_id, {"role": "CEO", "markets": ["Mexico"]})

        tp.TalentPool.record_match(search_id, k1, score=90, band="priority_1",
                                   criteria_match="3/3", matched_criteria=["pnl", "team"], risks=[])
        tp.TalentPool.record_match(search_id, k2, score=60, band="priority_2",
                                   criteria_match="2/3", matched_criteria=["pnl"], risks=["relocation"])
        tp.TalentPool.record_match(search_id, k3, score=40, band="review_needed",
                                   criteria_match="1/3", matched_criteria=[], risks=[])

        coverage = tp.TalentPool.get_search_coverage(search_id)

        assert coverage["search_id"] == search_id
        assert coverage["total_matches"] == 3, f"Expected 3 total matches, got {coverage['total_matches']}"
        assert coverage["by_band"]["priority_1"] == 1
        assert coverage["by_band"]["priority_2"] == 1
        assert coverage["by_band"]["review_needed"] == 1

        # By source
        assert coverage["by_source"].get("torre", 0) == 2
        assert coverage["by_source"].get("brave_search", 0) == 1

        # By status — all new
        assert coverage["by_status"].get("new", 0) == 3


def test_pool_size(tmp_path):
    """get_pool_size() refleja el número real de candidatos"""
    import core.talent_pool as tp

    with patch.object(tp, "DB_PATH", tmp_path / "pool.db"):
        tp._ensure_tables()

        assert tp.TalentPool.get_pool_size() == 0

        tp.TalentPool.upsert_candidate(_make_signal(name="Uno", source_url="https://torre.co/uno"))
        assert tp.TalentPool.get_pool_size() == 1

        tp.TalentPool.upsert_candidate(_make_signal(name="Dos", source_url="https://torre.co/dos"))
        assert tp.TalentPool.get_pool_size() == 2

        # Upsert same candidate — size stays 2
        tp.TalentPool.upsert_candidate(_make_signal(name="Uno", source_url="https://torre.co/uno"))
        assert tp.TalentPool.get_pool_size() == 2


def test_record_review_updates_status(tmp_path):
    """record_review() actualiza el status del candidato correctamente"""
    import core.talent_pool as tp

    with patch.object(tp, "DB_PATH", tmp_path / "pool.db"):
        tp._ensure_tables()

        signal = _make_signal()
        key = tp.TalentPool.upsert_candidate(signal)

        cand_before = tp.TalentPool.get_candidate(key)
        assert cand_before["status"] == "new"

        tp.TalentPool.record_review(key, decision="approved", search_id="s_001", comment="excelente")

        cand_after = tp.TalentPool.get_candidate(key)
        assert cand_after["status"] == "approved"

        # Rejected path
        signal2 = _make_signal(name="Rechazado", source_url="https://torre.co/rechazado")
        key2 = tp.TalentPool.upsert_candidate(signal2)
        tp.TalentPool.record_review(key2, decision="rejected")
        assert tp.TalentPool.get_candidate(key2)["status"] == "rejected"
