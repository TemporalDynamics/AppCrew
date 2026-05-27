# Outreach Agent

## Propósito

Genera borradores de contacto inicial y seguimiento para clientes potenciales y candidatos. Prepara el mensaje, el canal y el contexto. **NUNCA envía sin aprobación humana explícita.**

Su trabajo termina cuando el borrador está listo para revisión del orquestador.

## Precondiciones

- Recibe target (persona/empresa) con contexto suficiente
- Canal definido (InMail, email, connection request)
- Tono/configuración de estilo disponible

## Postcondiciones

- Borrador generado con mensaje, target, canal y score
- La acción queda en estado `PENDING_REVIEW`
- El orquestador es notificado

## Invariantes

1. **NUNCA ejecuta el envío** — es la regla más importante. Outreach prepara, el humano autoriza
2. **El mensaje no se modifica después de aprobado** — si el orquestador edita, se genera nuevo borrador
3. **Trazabilidad completa** — cada borrador tiene un id único y registro de quién lo aprobó/rechazó
4. **Máximo N mensajes por target por día** — evitar saturación (configurable, default 1)
5. **Tono configurable** — el mensaje se adecúa al tono definido en configuración (professional por defecto)

## Interfaz

### Parámetros (desde CEO)

```python
{
    "targets": [
        {
            "name": "Carlos Méndez",
            "role": "CEO",
            "company": "TechMex",
            "channel": "linkedin_inmail",  # o "email", "connection_request"
            "context": "TechMex anunció Serie B, busca CTO",
            "score": 92,
        },
        ...
    ],
    "tone": "professional",  # o "casual", "formal"
    "sender": "Manu",
}
```

### Output (hacia CEO)

```python
[
    {
        "action_id": "outreach_1712345678",
        "target": "Carlos Méndez — CEO TechMex",
        "channel": "linkedin_inmail",
        "message": "Hola Carlos...",
        "score": 92,
        "state": "pending_review",
    },
    ...
]
```

## Canales soportados

| Canal | Método | Requiere aprobación |
|---|---|---|
| LinkedIn InMail | Playwright (sesión autenticada) | Sí |
| Email | Cliente SMTP (configurable) | Sí |
| LinkedIn Connection Request | Playwright | Sí (configurable) |
