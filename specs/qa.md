# Delivery QA Agent

## Propósito

Control de calidad antes de presentar cualquier shortlist, oportunidad o comunicación. Verifica consistencia, completitud y adherencia a los estándares definidos.

NO modifica datos — solo reporta issues.

## Precondiciones

- Existen datos en el sistema (candidatos, oportunidades, carpetas ejecutivas)
- Los estándares de calidad están definidos

## Postcondiciones

- Reporte generado con estado PASS/FAIL
- Lista de issues encontrados (si hay)
- Cada issue tiene severidad y recomendación

## Invariantes

1. **Solo lectura** — nunca modifica datos, nunca elimina nada. Solo inspecciona y reporta
2. **Siempre produce un reporte** — aunque no haya issues, genera un PASS explícito
3. **Issue con severidad** — cada issue clasifica gravedad (40=leve, 70=moderado, 100=crítico)
4. **Accionable** — cada issue incluye qué hacer para resolverlo
5. **No bloqueante** — QA informa, no impide. La decisión final es del orquestador

## Interfaz

### Parámetros (desde CEO)

```python
{
    "scope": "all",  # o "candidates", "opportunities", "folders"
}
```

### Output (hacia CEO)

```python
{
    "status": "FAIL",
    "checks_run": 10,
    "issues": [
        {
            "scope": "TechMex/01_Mercado",
            "type": "empty_folder",
            "detail": "Carpeta 01_Mercado en TechMex está vacía",
            "severity": 40,
            "recommendation": "Agregar informe de mercado de la industria",
        },
        ...
    ],
}
```

## Checks ejecutados

| Check | ¿Qué verifica? | Severidad si falla |
|---|---|---|
| Carpetas vacías | Cada carpeta ejecutiva tiene contenido | 40 (leve) |
| Candidatos sin score | Todo candidato tiene score de Fit Scoring | 70 (moderado) |
| Oportunidades sin fuente | Toda oportunidad indica origen | 50 (leve) |
| Borradores sin target | Outreach siempre tiene destinatario | 80 (grave) |
| Consistencia de datos | Coherencia entre agentes | 60 (moderado) |
