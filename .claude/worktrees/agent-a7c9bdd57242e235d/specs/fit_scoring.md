# Fit Scoring Agent

## Propósito

Prioriza candidatos con un score explicable basado en habilidades, trayectoria, señales de movilidad y consistencia de carrera.

NO busca candidatos, NO prepara mensajes, NO descarta candidatos unilateralmente (el score es una recomendación).

## Precondiciones

- Recibe una lista de candidatos con datos mínimos: skills, experiencia, rol
- Los pesos de scoring están definidos y suman 1.0

## Postcondiciones

- Cada candidato tiene un score total entre 0-100
- Cada score incluye breakdown por dimensión
- Los candidatos se devuelven ordenados por score descendente

## Invariantes

1. **Los pesos siempre suman 1.0** — si se modifican, el agente normaliza automáticamente
2. **Score siempre explicable** — cada score total tiene desglose por dimensión
3. **No elimina candidatos** — todos los que entran, salen con score. El corte lo decide el humano
4. **Rango fijo 0-100** — todos los scores se normalizan a este rango
5. **Determinístico** — mismo input produce mismo output (sin aleatoriedad)

## Interfaz

### Parámetros (desde CEO)

```python
{
    "candidates": [
        {"name": "María García", "skills": 92, "experience": 95, "mobility": 70, "consistency": 85},
        ...
    ]
}
```

### Output (hacia CEO)

```python
[
    {
        "name": "María García",
        "role": "CTO",
        "total_score": 87,
        "breakdown": {
            "skills": 32.2,    # 92 * 0.35
            "experience": 28.5, # 95 * 0.30
            "mobility": 14.0,   # 70 * 0.20
            "consistency": 12.75, # 85 * 0.15
        },
        "weights_used": {"skills": 0.35, "experience": 0.30, "mobility": 0.20, "consistency": 0.15},
    },
    ...
]
```

## Pesos por defecto

| Dimensión | Peso | Fundamento |
|---|---|---|
| Skills | 0.35 | Capacidad técnica para el rol |
| Experiencia | 0.30 | Trayectoria relevante |
| Señales de movilidad | 0.20 | Probabilidad de estar abierto a cambios |
| Consistencia de carrera | 0.15 | Estabilidad y crecimiento coherente |
