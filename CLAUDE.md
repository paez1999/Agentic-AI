---
tags:
  - prompt
  - claude
  - ai-agents
  - crewai
  - supply-chain
  - architecture
aliases:
  - Prompt Claude PoC Supply Chain
---

# CLAUDE - Guía del Proyecto: PoC Multi-Agente de Supply Chain

> [!abstract] 📌 Visión General
> Este proyecto es una Prueba de Concepto (PoC) Multi-Agente enfocada en la cadena de suministro (Supply Chain), construida utilizando el framework **CrewAI**. El sistema opera bajo un bucle de monitoreo continuo (24/7) con un flujo de cinco fases: Monitoreo, Análisis, Decisión, Ejecución y Reporte.

## 🏗️ Arquitectura y Stack Tecnológico

La arquitectura base se compone de las siguientes tecnologías y capas:

- **Orquestación**: Uso de Temporal o LangGraph para controlar el flujo end-to-end.
- **Bus de Eventos**: NATS, empleado para desacoplar a los agentes y publicar alertas/resultados.
- **Capa de Herramientas**: Implementación de servidores MCP (Model Context Protocol) para conectar con sistemas ERP, servicios de clima, noticias y enrutamiento (routing).
- **Estado y Memoria**: 
    - PostgreSQL para el estado y auditoría.
    - Redis para caché e idempotencia.
    - *Opcional*: Base de datos vectorial (Vector DB) para memoria semántica.
- **Capa UI/API**: Streamlit (o cliente web) para la interfaz de usuario y un Gateway REST para iniciar casos y consultar estados.

## 🤖 Sistema de Agentes

El sistema utiliza agentes especializados que interactúan entre sí:

> [!info] Agente 1 - Monitoreo (RiskMonitor)
> - **Enfoque**: Clima, geopolítica y eventos globales.
> - **Fuentes de datos**: APIs de clima, RSS de noticias y sensores IoT.
> - **Output**: Detección de riesgos (ej. Huracán Categoría 4, puerto cerrado).

> [!info] Agente 2 - Sistema ERP (Inventory Manager)
> - **Enfoque**: Gestión de inventario, stock y centros de distribución.
> - **Fuentes de datos**: Bases de datos internas (inventario, almacenes, rutas activas).
> - **Output**: Emite un plan de acción basado en el impacto evaluado (ej. retrasos, stock afectado).

> [!info] Agente 3 - Logística (RouteOptimizer / Policy)
> - **Enfoque**: Envíos y reabastecimiento.
> - **Fuentes de datos**: Operaciones de envío, recepción y tracking.
> - **Output**: Ejecución inmediata y conformación (ej. rutas alternativas, alertas activas) y confirmación de "Ejecución OK".

## 🔌 Protocolos y Patrones de Integración

Al desarrollar o refactorizar el código, se deben respetar los siguientes protocolos para su caso de uso específico:

- **MCP (Model Context Protocol)**: Conecta a los agentes con sistemas externos (ERP, clima, noticias, TMS) de forma estandarizada, permitiendo cambiar de proveedor sin necesidad de reescribir la lógica del agente.
- **HTTP/REST + JSON**: Utilizado para la entrada y salida del sistema (UI, API pública), logrando una integración simple con aplicaciones existentes.
- **A2A (Agent-to-Agent) sobre HTTP/gRPC**: Permite la comunicación directa cuando los agentes delegan subtareas, manteniendo contratos claros y reduciendo el acoplamiento con el orquestador.
- **CloudEvents sobre NATS**: Distribuido para eventos de dominio (como `risk.alert` o `inventory.updated`), aportando trazabilidad, reintentos y un procesamiento asíncrono robusto.
- **WebSocket (Opcional)**: Recomendado para actualizar la UI en tiempo real y brindar visibilidad operativa en vivo del workflow.
- **OAuth2/JWT (+ mTLS opcional)**: Exigido para garantizar la seguridad entre los servicios y el control de acceso en producción.

---
> [!summary] En una frase
> Temporal orquesta, NATS distribuye eventos, MCP conecta las herramientas, y REST/A2A exponen y coordinan las capacidades reales de los agentes.