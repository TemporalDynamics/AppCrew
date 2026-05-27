# Knowledge Agent

## Propósito

Organiza la memoria operativa del sistema. Mantiene la estructura de carpetas ejecutivas por cuenta, proceso y vacante. Asegura que la información esté donde debe estar y sea accesible.

NO interpreta datos, NO scorea, NO genera contenido nuevo.

## Precondiciones

- La lista de cuentas activas existe (o se crea una nueva)
- La estructura de carpetas está definida

## Postcondiciones

- Cada cuenta tiene su estructura de carpetas creada
- Las carpetas existentes no se modifican (solo se crean las que faltan)

## Invariantes

1. **Nunca elimina datos** — solo crea estructura nueva, nunca borra carpetas o archivos existentes
2. **Estructura uniforme** — todas las cuentas tienen exactamente la misma estructura de carpetas
3. **Idempotente** — ejecutarlo N veces produce el mismo resultado que ejecutarlo 1 vez
4. **Sin contenido generado** — el Knowledge Agent no escribe archivos de contenido, solo carpetas

## Interfaz

### Parámetros (desde CEO)

```python
{
    "accounts": ["TechMex", "FinTechMX"],  # opcional, usa las existentes
}
```

### Output (hacia CEO)

```python
[
    {
        "account": "TechMex",
        "folders_created": ["01_Mercado", "02_Oportunidades", ...],
        "path": "data/knowledge/TechMex",
    },
    ...
]
```

## Estructura de carpetas (por cuenta)

```
{cuenta}/
├── 01_Mercado/
├── 02_Oportunidades/
├── 03_Candidatos/
├── 04_Contactos_y_Seguimiento/
├── 05_Insights_Semanales/
└── 06_Riesgos_y_Bloqueos/
```
