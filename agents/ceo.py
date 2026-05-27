import re
from datetime import datetime, timezone

from agents.base import BaseAgent
from contracts import AgentAction, AgentState


class CEOAgent(BaseAgent):
    id = "ceo"
    name = "CEO"
    icon = "🧠"
    description = "Coordina agentes y traduce tareas humanas a órdenes ejecutables"

    def __init__(self, config: dict):
        super().__init__(config)
        self._orchestrator = None
        self.conversation_log: list[dict] = []

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura de config"},
                "context7": {"permitted": True, "notes": "resolver dudas técnicas del humano"},
                "memory": {"permitted": True, "notes": "solo lectura, namespace `memory/ceo/*`"},
            },
            "context": ["run_id actual", "workers disponibles y capacidades", "historial de conversación (últimos 20)"],
            "memory": {
                "namespace": "memory/ceo/*",
                "can_remember": ["historial de conversación", "últimos planes generados"],
                "cannot_remember": ["datos operativos de workers", "decisiones de aprobación no resueltas"],
            },
            "invariants": [
                "work() siempre devuelve lista vacía (es coordinador, no worker)",
                "Nunca ejecuta acciones externas",
                "Toda comunicación se loguea en conversation_log",
                "No modifica memoria interna de workers",
                "Escala al humano si no puede descomponer una tarea",
            ],
            "failure_modes": [
                "Tarea ambigua: escala al humano pidiendo aclaración",
                "Worker no disponible: reporta error parcial",
                "Timeout de worker: reintenta 1 vez, luego escala",
            ],
            "escalation": [
                "Tarea no descomponible → humano",
                "Worker falla → CEO reintenta 1 vez, luego reporta error parcial",
                "Se requiere acción externa → deriva a orquestador para aprobación humana",
            ],
            "tests": [
                "import OK", "work() devuelve 0 acciones",
                "process_task() descompone y delega correctamente",
                "No contiene lógica de worker",
            ],
            "authority": "coordinator",
        }

    def bind_orchestrator(self, orchestrator):
        self._orchestrator = orchestrator

    async def process_task(self, task_text: str) -> dict:
        self.state = AgentState.WORKING
        self.conversation_log.append({
            "role": "human",
            "text": task_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        plan = self._decompose_task(task_text)
        results = {}

        for step in plan["steps"]:
            agent_id = step["agent"]
            if self._orchestrator and agent_id in self._orchestrator.agents:
                actions = await self._orchestrator.run_agent(agent_id)
                results[agent_id] = {
                    "agent": self._orchestrator.agents[agent_id].to_dict(),
                    "actions": [a.to_dict() for a in actions],
                }

        summary = self._synthesize(plan, results)

        self.state = AgentState.PENDING_REVIEW
        self.last_action = f"Tarea procesada: {plan['intent']}"
        self.last_run = datetime.now(timezone.utc)

        response = {
            "task": task_text,
            "plan": plan,
            "results": results,
            "summary": summary,
            "pending_actions": self._orchestrator.get_pending_actions() if self._orchestrator else [],
            "timestamp": self.last_run.isoformat(),
        }

        self.conversation_log.append({
            "role": "ceo",
            "text": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return response

    def _decompose_task(self, task: str) -> dict:
        task_lower = task.lower()
        steps = []
        agents_to_run = set()

        keywords_radar = re.compile(
            r"oportunidad|expansion|mercado|inversión|ronda|señal|tendencia|empresa.*busc|nueva.*oficina"
        )
        keywords_sourcing = re.compile(
            r"candidato|talento|buscar.*perfil|cto|director|vp|head|reclutar|sourcing|profesional|ceo|cfo"
        )
        keywords_scoring = re.compile(
            r"score|priorizar|rank|evaluar|mejor.*candidato|ordenar|scoring"
        )
        keywords_outreach = re.compile(
            r"contactar|inmail|mensaje|email|outreach|borrador|escribir.*a"
        )
        keywords_knowledge = re.compile(
            r"organizar|carpeta|estructura|knowledge|memoria|folder"
        )
        keywords_qa = re.compile(
            r"revisar|calidad|qa|verificar|auditar|check|control"
        )
        keywords_doctrine = re.compile(
            r"doctrina|filosofía|principio|criterio.*firma|cultura.*empresa|valores|filosofía.*talento"
        )
        keywords_talent_signal = re.compile(
            r"señal.*candidato|análisis.*cualitativo|hipótesis.*talento|talent.signal|validar.*señal|narrativa.*perfil"
        )
        keywords_career_context = re.compile(
            r"contexto.*empresa|trayectoria.*empresa|career.context|historial.*empresa|timeline.*empresa|carrera.*contexto"
        )

        if keywords_radar.search(task_lower):
            agents_to_run.add("demand_radar")
            steps.append({
                "agent": "demand_radar",
                "reason": "Detectar empresas con señales de contratación",
                "params": {"region": self._extract_region(task)},
            })

        if keywords_sourcing.search(task_lower):
            agents_to_run.add("talent_sourcing")
            role = self._extract_role(task)
            steps.append({
                "agent": "talent_sourcing",
                "reason": f"Buscar candidatos para rol: {role}",
                "params": {"role": role, "location": self._extract_region(task)},
            })

        if keywords_scoring.search(task_lower):
            agents_to_run.add("fit_scoring")
            steps.append({
                "agent": "fit_scoring",
                "reason": "Scorear y priorizar candidatos",
                "params": {},
            })

        if keywords_outreach.search(task_lower):
            agents_to_run.add("outreach")
            steps.append({
                "agent": "outreach",
                "reason": "Preparar borradores de contacto",
                "params": {},
            })

        if keywords_knowledge.search(task_lower):
            agents_to_run.add("knowledge")
            steps.append({
                "agent": "knowledge",
                "reason": "Organizar estructura de carpetas",
                "params": {},
            })

        if keywords_qa.search(task_lower):
            agents_to_run.add("qa")
            steps.append({
                "agent": "qa",
                "reason": "Control de calidad sobre datos existentes",
                "params": {},
            })

        if keywords_doctrine.search(task_lower):
            agents_to_run.add("doctrine_keeper")
            steps.append({
                "agent": "doctrine_keeper",
                "reason": "Consultar doctrina y principios de la firma",
                "params": {},
            })

        if keywords_talent_signal.search(task_lower):
            agents_to_run.add("talent_signal")
            steps.append({
                "agent": "talent_signal",
                "reason": "Analizar señales cualitativas de candidatos existentes",
                "params": {},
            })

        if keywords_career_context.search(task_lower):
            agents_to_run.add("career_context")
            steps.append({
                "agent": "career_context",
                "reason": "Reconstruir contexto público de empresas de los candidatos",
                "params": {},
            })

        if not agents_to_run:
            agents_to_run.add("demand_radar")
            agents_to_run.add("talent_sourcing")
            steps = [
                {"agent": "demand_radar", "reason": "Escaneo general de mercado", "params": {}},
                {"agent": "talent_sourcing", "reason": "Búsqueda general de talento", "params": {}},
            ]

        intent = self._classify_intent(task)

        return {
            "intent": intent,
            "original_task": task,
            "agents_involved": list(agents_to_run),
            "steps": steps,
        }

    def _classify_intent(self, task: str) -> str:
        t = task.lower()
        if any(w in t for w in ["oportunidad", "mercado", "cliente", "venta"]):
            return "deteccion_oportunidades"
        if any(w in t for w in ["candidato", "talento", "perfil", "buscar"]):
            return "busqueda_talento"
        if any(w in t for w in ["contactar", "inmail", "mensaje", "outreach"]):
            return "contacto_cliente"
        if any(w in t for w in ["revisar", "calidad", "qa", "verificar"]):
            return "control_calidad"
        if any(w in t for w in ["organizar", "carpeta", "estructura"]):
            return "organizacion_conocimiento"
        return "analisis_general"

    def _extract_role(self, task: str) -> str:
        roles = ["CTO", "CEO", "CFO", "VP", "Director", "Head", "Manager"]
        for r in roles:
            if r.lower() in task.lower():
                return r
        return "Profesional"

    def _extract_region(self, task: str) -> str:
        regions = ["México", "LATAM", "Colombia", "Argentina", "Chile", "Perú", "Brasil"]
        for r in regions:
            if r.lower() in task.lower():
                return r
        return "México"

    def _synthesize(self, plan: dict, results: dict) -> str:
        lines = [f"✅ Tarea procesada: {plan['intent'].replace('_', ' ')}"]
        lines.append(f"   Agentes involucrados: {', '.join(plan['agents_involved'])}")

        for agent_id, data in results.items():
            n = len(data.get("actions", []))
            lines.append(f"   • {agent_id}: {n} acciones generadas")

        pending = 0
        for agent_id, data in results.items():
            for a in data.get("actions", []):
                if a.get("state") == "pending_review":
                    pending += 1

        if pending:
            lines.append(f"\n⏳ {pending} acción(es) pendiente(s) de revisión humana")

        return "\n".join(lines)

    async def work(self) -> list[AgentAction]:
        return []

    def get_conversation(self) -> list[dict]:
        return self.conversation_log[-20:]
