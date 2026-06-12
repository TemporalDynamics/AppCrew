# Talo

Sistema operativo de búsquedas ejecutivas asistidas por agentes: definís un criterio, corrés una búsqueda, revisás talento, tomás decisiones y guardás evidencia.

## Estado

MVP funcional con pipeline de agentes, dashboard web, 3 fuentes de talento (Torre.co, Brave Search, Firecrawl), persistencia SQLite, notificaciones Telegram y ledger verificable.

## Stack

- Python 3.11+ / FastAPI
- SQLite (WAL mode)
- Pipeline de agentes con ciclo de aprobación humana
- Dashboard web (Jinja2 + Jinja)

## Arranque rápido

```bash
pip install -r requirements.txt
playwright install chromium
python run.py
# Dashboard en http://127.0.0.1:8080
```

Sin API keys el sistema opera en modo demo con datos de semilla.

## Flujo principal

1. **Definir criterio** (`/setup`) — describís el perfil que buscás en lenguaje humano
2. **Ejecutar agentes** (`/run`) — activás el pipeline de búsqueda
3. **Revisar talentos** (`/talents`) — revisás los perfiles encontrados y clasificás
4. **Perfil de candidato** (`/candidate/{id}`) — profundizás, agregás notas, evidencia, entrevistas
5. **Decidir** — shortlist, contacto, contratación

## Superficie de producto

- **Principal**: Inicio, Búsquedas, Nueva Búsqueda, Ejecutar, Talentos
- **Operaciones**: Command Room, Blind Review, Coverage, Shortlist, CEO, Settings
- **Aislado**: Carga de CV (`/cargar-cv`)
