# Plan de Hardening 30/60 Días

**Proyecto:** Global Executive Agent System  
**Fecha:** 14 de mayo de 2026  
**Objetivo:** pasar de MVP funcional a operación confiable para cliente real.

---

## 1. Objetivos del hardening

1. Reemplazar mocks críticos por conectores reales priorizados.
2. Fortalecer calidad, seguridad y trazabilidad operativa.
3. Medir rendimiento real (tiempo por task, tasa de aprobación, valor comercial generado).

---

## 2. Fase 0 (Semana 0): Preparación

1. Definir entorno de demo y entorno de piloto separados.
2. Congelar contratos de datos v1.
3. Definir checklist de “go/no-go” para demo ejecutiva.
4. Acordar fuentes permitidas y política de uso.

---

## 3. Días 1-30 (Hardening base)

### 3.1 Integraciones críticas

1. Activar al menos 1 conector real de demanda de mercado.
2. Activar al menos 1 flujo real de sourcing controlado.
3. Implementar ejecución observada de task con medición de duración.

### 3.2 CEO Agent

1. Migrar parser básico a LLM con prompts versionados.
2. Agregar clasificación de intención y confirmación antes de acciones sensibles.
3. Registrar razones de decisión del agente para auditoría.

### 3.3 Calidad y pruebas

1. Suite smoke diaria de punta a punta.
2. Pruebas de contrato por agente.
3. Prueba de fallback cuando falla una fuente externa.

### 3.4 Seguridad mínima operativa

1. RBAC básico (Socio, Orquestador, Recruiter, Viewer).
2. Enmascarado de PII en logs no críticos.
3. Política de retención inicial (ejemplo: 90 días operativos).

**Entregable Día 30:** piloto interno operando con al menos 2 flujos reales y métricas consistentes.

---

## 4. Días 31-60 (Hardening de escalamiento)

### 4.1 Operación multi-cuenta

1. Segmentar pipelines por cliente/país.
2. SLA por task y alertas por atraso.
3. Tablero ejecutivo con KPIs comparables por cuenta.

### 4.2 Robustez técnica

1. Reintentos idempotentes en tareas críticas.
2. Mejoras de manejo de errores y recuperación.
3. Backups + restauración probada.

### 4.3 Observabilidad y costos

1. Métricas de latencia por agente y por task.
2. Costo por ejecución y costo por pipeline.
3. Alertas automáticas por degradación.

### 4.4 Cierre de producción piloto

1. UAT con escenarios reales GE.
2. Manual operativo (runbook).
3. Aprobación de salida a producción del primer cliente.

**Entregable Día 60:** operación de piloto lista para comercializar con riesgo controlado.

---

## 5. KPIs del hardening

1. Tiempo promedio por task end-to-end.
2. % tasks completadas sin intervención técnica.
3. % acciones aprobadas/rechazadas por orquestador.
4. Tasa de error por conector.
5. Tiempo de recuperación ante falla.
6. Costo por ejecución útil.

---

## 6. Criterio de éxito

Hardening exitoso = el sistema corre en entorno real, con datos reales, trazabilidad completa, costos conocidos y operación predecible para GE.

