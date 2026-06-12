# ReviewPolicy Skill — Estados de revisión por action_type

## Propósito
Define qué estados de revisión están permitidos para cada tipo de acción.
Ninguna UI, API o agente puede inventar estados. Todo pasa por ReviewPolicy.

## Mapa de estados permitidos

| Action Type | Estados válidos |
|-------------|----------------|
| `opportunity` | `qualified`, `dismissed`, `escalated` |
| `candidate` | `shortlisted`, `dismissed`, `escalated` |
| `score` | `acknowledged`, `dismissed` |
| `inmail` | `approved`, `rejected`, `needs_revision` |
| `folder_structure` | `approved`, `rejected` |
| `quality_issue` | `acknowledged`, `dismissed`, `resolved`, `escalated` |
| `qa_summary` | `acknowledged` |
| `signal` | `validated_signal`, `needs_human_review`, `weak_signal`, `escalated` |
| `context_signal` | `acknowledged`, `needs_human_review`, `dismissed`, `escalated` |
| `doctrine_snapshot` | `acknowledged` |
| cualquier otro | `acknowledged`, `dismissed` |

## Matriz de semántica de revisión

Qué significa revisar cada tipo de acción y qué alcance tiene cada estado:

| Tipo | Revisar significa | Dismiss significa | Scope |
|------|-------------------|-------------------|-------|
| `candidate` | Decidir si entra en shortlist de una búsqueda | No sirve para esta búsqueda. No excluye globalmente. | `search_context` |
| `score` | Aceptar o descartar ese análisis | Ignorar ese puntaje. No elimina al candidato. | `search_context` |
| `signal` | Validar/debilitar una hipótesis humana | La señal es débil, no el candidato. | `candidate_id` |
| `context_signal` | Aceptar/descartar contexto empresarial | El contexto no aporta. No afecta al candidato. | `candidate_id` |
| `opportunity` | Calificar oportunidad comercial | No perseguir esta oportunidad ahora. | `company_id` |
| `inmail` | Aprobar/rechazar/redactar draft | No enviar ese mensaje. | `thread_id` |
| `doctrine_snapshot` | Confirmar lectura de doctrina | Solo limpiar la notificación. | — |
| `folder_structure` | Aprobar estructura creada | Rechazar esa estructura. No borra datos. | `account_id` |
| `qa_summary` | Confirmar revisión de QA | Solo marcar visto. | — |

## Reglas

1. **No hay estado por defecto.** Toda acción nace en `pending_review`.
2. **ReviewPolicy es la única autoridad.** Código externo nunca hardcodea estados.
3. **`approved` y `rejected` solo para acciones que ejecutan algo.**
   Acciones informativas (score, signal, qa_summary) usan `acknowledged`.
4. **`escalated` siempre es válido** para cualquier action type que lo declare.
5. **`needs_human_review` para señales que requieren criterio humano.**
6. **Review states no eliminan entidades. Solo resuelven acciones.**
   Toda decisión destructiva o global requiere estado explícito (`blacklisted`, `dismissed_globally`).
7. **decision_scope evita falsos negativos.**
   `dedup_key` incluye `decision_scope`. Un candidato descartado para una búsqueda
   puede aparecer en otra búsqueda distinta.

## Implementación

El mapping está en `contracts/__init__.py` → `ReviewPolicy._MAPPING`.
No duplicar esta lógica en otro lado.

## Fallback seguro

Si un action_type no está en el mapping, los estados por defecto son:
`["acknowledged", "dismissed"]` — nunca falla, pero mejor agregar el tipo.
