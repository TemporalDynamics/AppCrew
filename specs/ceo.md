# CEO Agent

## Propósito

Es el **puente entre el humano y los agentes**. Recibe tareas en lenguaje natural del orquestador (Manu o quien se designe), las traduce a órdenes para los workers, recolecta resultados y sintetiza una respuesta accionable.

NO ejecuta trabajo de los workers — delega, coordina y reporta.

## Precondiciones

- Al menos un worker agent debe estar registrado y habilitado
- El humano debe haber definido una tarea o intención

## Postcondiciones

- La tarea fue descompuesta en subtareas y asignada a los workers correspondientes
- Todos los resultados fueron recolectados
- Se generó un resumen para el humano
- Cualquier acción que requiera aprobación humana fue elevada al orquestador

## Invariantes

1. **Solo el CEO habla con el humano** — los workers no se comunican directamente con la persona
2. **Toda comunicación se loguea** — cada interacción humano→CEO y CEO→worker queda registrada
3. **No ejecuta acciones externas** — el CEO no envía mensajes, no busca talento, no scorea. Solo coordina
4. **Siempre reporta estado** — después de cada ronda de ejecución, entrega un resumen al humano
5. **Escala cuando no sabe** — si una tarea no se puede descomponer en workers conocidos, pide ayuda al humano
6. **Contexto acumulativo** — mantiene el hilo de la conversación/tarea a través de rondas

## Interfaz

### Entrada (desde humano)

```python
class HumanTask:
    text: str           # "Buscá CTOs en México que hayan trabajado en Google"
    context: dict       # opcional: cuenta, prioridad, notas
    reply_to: str       # id de tarea anterior (para seguimiento)
```

### Salida (hacia humano)

```python
class CEOResponse:
    summary: str               # "Encontré 3 candidatos. 2 requieren aprobación para outreach."
    actions_taken: list[dict]  # qué agentes se ejecutaron
    pending_approval: list     # acciones que necesitan revisión humana
    errors: list[str]          # si algo falló
```

### Órdenes (hacia workers)

```python
class AgentOrder:
    agent_id: str        # "demand_radar", "talent_sourcing", etc.
    params: dict         # parámetros específicos del agente
    parent_task: str     # tarea humano original (para trazabilidad)
```

## Flujo típico

```
Humano: "Buscar CTOs en México que hayan expandido equipos"

CEO:
  1. Interpreta: rol=CTO, país=México, señal=expansión
  2. Ordena a Talent Sourcing: buscar CTOs México
  3. Ordena a Demand Radar: buscar empresas mexicanas en expansión
  4. Espera resultados de ambos
  5. Ordena a Fit Scoring: scorear candidatos encontrados
  6. Sintetiza:
     - 3 CTOs encontrados, 2 con alta probabilidad de movilidad
     - 2 empresas en expansión que podrían contratar
  7. Reporta al humano con resumen + próximos pasos sugeridos
```

## Estados

| Estado | Significado |
|---|---|
| `listening` | Esperando tarea del humano |
| `interpreting` | Analizando tarea y descomponiendo |
| `delegating` | Enviando órdenes a workers |
| `collecting` | Esperando resultados de workers |
| `synthesizing` | Armando respuesta |
| `reporting` | Entregando resumen al humano |
| `escalating` | Pidiendo ayuda al humano |
