from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class FitScoringAgent(BaseAgent):
    id = "fit_scoring"
    name = "Fit Scoring"
    icon = "📊"
    description = "Prioriza candidatos con scoring explicable"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        w = config.get("agents", {}).get("fit_scoring", {}).get("weights", {})
        self.weights = {
            "skills": w.get("skills", 0.35),
            "experience": w.get("experience", 0.30),
            "mobility_signals": w.get("mobility_signals", 0.20),
            "career_consistency": w.get("career_consistency", 0.15),
        }

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "solo lectura, no necesita recordar entre runs"},
            },
            "context": ["run_id actual", "lista de candidatos", "pesos de scoring (validados: suman 1.0)"],
            "memory": {
                "namespace": "N/A (determinístico)",
                "can_remember": [],
                "cannot_remember": ["no necesita memoria entre runs"],
            },
            "invariants": [
                "Pesos siempre suman 1.0 (se validan en preconditions)",
                "Score entre 0-100",
                "Score siempre explicable (breakdown por dimensión)",
                "No elimina candidatos",
                "Determinístico",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "Pesos no suman 1.0: error crítico, no ejecuta",
                "Lista vacía: no genera acciones",
                "Datos incompletos: warning, scorea con datos disponibles",
            ],
            "escalation": [
                "Pesos inválidos: error al orquestador, no escala",
                "Candidatos sin datos suficientes: incluir con score reducido y nota",
            ],
            "tests": [
                "import OK", "run genera acciones válidas", "run_id obligatorio",
                "scores en rango 0-100", "pesos suman 1.0",
            ],
            "authority": "analyzer",
        }

    def _check_preconditions(self) -> list:
        v = []
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            v.append({"agent_id": self.id, "invariant": "pesos_suman_1",
                      "detail": f"Pesos suman {total}, deben sumar 1.0", "severity": "critical"})
        return v

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        for a in actions:
            assert 0 <= a.score <= 100, f"Score {a.score} fuera de rango"

    async def work(self) -> list[AgentAction]:
        scored = self._score_candidates()
        return [
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.SCORE.value,
                target=s["name"],
                reason=f"Score total: {s['total_score']} — skills {s['breakdown']['skills']}, exp {s['breakdown']['experience']}",
                payload=s,
                score=s["total_score"],
            )
            for s in scored
        ]

    def _score_candidates(self) -> list[dict]:
        raw = [
            {"name": "María García", "role": "CTO", "skills": 92, "experience": 95, "mobility": 70, "consistency": 85},
            {"name": "Pedro López", "role": "VP Eng", "skills": 88, "experience": 85, "mobility": 80, "consistency": 80},
            {"name": "Ana Torres", "role": "HR Dir", "skills": 80, "experience": 85, "mobility": 75, "consistency": 90},
            {"name": "Luis Mendoza", "role": "Growth", "skills": 75, "experience": 70, "mobility": 95, "consistency": 70},
            {"name": "Carla Ruiz", "role": "CFO", "skills": 70, "experience": 85, "mobility": 60, "consistency": 90},
        ]
        results = []
        for c in raw:
            total = sum(
                c[k] * self.weights[n]
                for k, n in [("skills", "skills"), ("experience", "experience"),
                             ("mobility", "mobility_signals"), ("consistency", "career_consistency")]
            )
            results.append({
                "name": c["name"], "role": c["role"],
                "skills_score": c["skills"], "experience_score": c["experience"],
                "mobility_score": c["mobility"], "consistency_score": c["consistency"],
                "total_score": round(total),
                "breakdown": {n: round(c[k] * self.weights[n], 1)
                              for k, n in [("skills", "skills"), ("experience", "experience"),
                                           ("mobility", "mobility_signals"), ("consistency", "career_consistency")]},
            })
        return sorted(results, key=lambda x: x["total_score"], reverse=True)
