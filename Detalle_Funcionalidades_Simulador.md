# Detalle de Funcionalidades - Simulador de Transporte Público (CID)

Este documento detalla las capacidades actuales del simulador, las herramientas de gestión integradas y el potencial de expansión hacia un Gemelo Digital del sistema de transporte.

---

## 1. Funcionalidades Operacionales (Actuales)

El simulador permite visualizar y analizar la operación real y teórica del sistema de transporte en tiempo real.

### 🛰️ Monitoreo y AVL (Automatic Vehicle Location)
*   **Visualización en Tiempo Real:** Seguimiento de buses sobre cartografía digital con precisión geoespacial.
*   **Map Matching:** Ajuste automático de posiciones GPS a las trayectorias de las rutas definidas.
*   **Estado de Flota:** Monitoreo de velocidad, rumbo y estado operativo de cada unidad.
*   **Reproducción Histórica:** Herramienta para "retroceder el tiempo" y analizar incidentes o comportamientos pasados.

### 📈 Analítica Operacional e Indicadores (KPIs)
*   **Control de Headway (Frecuencia):** Medición del tiempo entre buses en un mismo punto para detectar irregularidades.
*   **Detección de Bunching:** Alertas automáticas cuando dos o más buses de la misma línea se "pegan", degradando el servicio.
*   **Velocidad Comercial:** Cálculo dinámico de la velocidad efectiva de los buses incluyendo tiempos de parada.
*   **Índice de Regularidad:** Evaluación del cumplimiento de los intervalos de paso programados.

### 🛣️ Infraestructura y Red
*   **Gestión de Unidades Funcionales (UF):** Implementación del modelo según Ley N° 7617 para la gestión por consorcios y grupos de líneas.
*   **Modelado de Rutas y Paraderos:** Base de datos geoespacial (PostGIS) con trazados precisos y puntos de parada autorizados.

---

## 2. Gestión de Parque Automotor (Módulo Integrado)

Herramienta crítica para la fiscalización y control administrativo de la flota habilitada.

*   **Expediente Digital del Bus:** Registro completo de marca, modelo, chasis, año y capacidad.
*   **Control de ITV (Inspección Técnica):** Seguimiento de vencimientos de inspecciones con alertas proactivas (60, 30, 15 días).
*   **Gestión de Seguros:** Monitoreo de pólizas de pasajeros y terceros.
*   **Vinculación UF-Bus:** Validación automática de la "Flota Mínima Habilitada" por cada Unidad Funcional.
*   **Alertas de Documentación:** Notificaciones de vencimiento de habilitaciones, POD y RTD.

---

## 3. Motor de Simulación (Capacidades de Microsimulación)

El núcleo del sistema utiliza **SimPy** para modelar eventos discretos.

*   **Simulación de Recorridos:** Modelado de buses teóricos para comparar la operación ideal vs. la real.
*   **Tiempos de Parada Dinámicos:** Cálculo de demora en paraderos basado en parámetros operativos.
*   **Modelado de Congestión:** Simulación de retrasos por tráfico en corredores específicos.

---

## 4. Funcionalidades en Desarrollo y Futuras (Lo que puede brindar)

El sistema está diseñado para evolucionar hacia un **Gemelo Digital (Digital Twin)** avanzado.

### 👥 Simulación de Pasajeros (Fase Próxima)
*   **Modelado de Demanda:** Simulación de llegada de pasajeros a los paraderos.
*   **Ascenso y Descenso:** Cálculo preciso de tiempos de parada basado en el flujo de personas.
*   **Matrices Origen-Destino:** Análisis de transferencias y viajes multimodales.

### 🧠 Inteligencia Artificial y Predicción
*   **Predicción de Arribos (ETA):** Algoritmos de IA para predecir cuándo llegará el bus al paradero con mayor precisión.
*   **Detección Predictiva de Saturación:** Alertas antes de que ocurra un problema de capacidad.
*   **Optimización de Frecuencias:** Sugerencias automáticas para ajustar la salida de buses según la demanda real detectada.

### 🏗️ Planificación Estratégica
*   **Simulación de Políticas Públicas:** Evaluar el impacto de cambios en la tarifa o creación de nuevas líneas antes de implementarlas.
*   **Evaluación de Infraestructura:** Modelar el beneficio de implementar carriles exclusivos o cambios en la red vial.
*   **Integración con Semáforos Inteligentes:** Prioridad semafórica para buses basada en los datos del simulador.

---

## 🛠️ Herramientas de Visualización
*   **Dashboard Ejecutivo:** Pantalla de control con KPIs globales para la toma de decisiones.
*   **Mapas de Calor:** Identificación visual de zonas de mayor congestión o retrasos frecuentes.
*   **Reportes Dinámicos:** Exportación de datos operativos a Excel/PDF para auditoría y fiscalización.

---
> [!TIP]
> La arquitectura basada en **FastAPI (Python)** y **PostGIS** garantiza que el sistema pueda escalar para manejar miles de buses y millones de posiciones GPS diariamente.
