# Talent Sourcing Agent

## Propósito

Busca talento por rol, industria, seniority y país. Opera principalmente sobre LinkedIn (vía Playwright con sesión autenticada) y fuentes complementarias (GitHub, portales de empleo).

NO contacta candidatos, NO envía InMails, NO scorea.

## Precondiciones

- Criterios de búsqueda definidos (rol, ubicación, seniority)
- Sesión de LinkedIn configurada (para búsqueda real; mock data si no)

## Postcondiciones

- Lista de candidatos con nombre, rol, empresa actual, ubicación y score preliminar
- Cada candidato tiene linkedin_url (real o simulado)
- Los resultados están acotados por `max_results`

## Invariantes

1. **Solo lectura** — nunca escribe en LinkedIn, nunca envía solicitudes de conexión
2. **No comparte datos fuera del sistema** — los perfiles encontrados no se exportan a terceros
3. **Respeto de tasa** — las búsquedas en LinkedIn respetan delays humanos (2-7s entre acciones)
4. **Cada candidato tiene ubicación** — no se reportan candidatos sin geografía
5. **Límite por búsqueda** — máximo `max_results` por ejecución (configurable, default 20)

## Interfaz

### Parámetros (desde CEO)

```python
{
    "role": "CTO",
    "industry": "Fintech",
    "seniority": "Senior",
    "location": "México",
    "max_results": 10,
}
```

### Output (hacia CEO)

```python
[
    {
        "name": "María García",
        "role": "CTO",
        "company": "TechMex",
        "location": "CDMX",
        "linkedin_url": "https://linkedin.com/in/...",
        "summary": "Ex-Google, 12 años en tech lead. En transición.",
        "score": 88,
    },
    ...
]
```
