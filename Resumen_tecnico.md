# Documento Técnico Base

## Sistema de Microsimulación y Monitoreo Operacional del Transporte Público

### Arquitectura basada en PostgreSQL, Python y React

---

# 1. Introducción

El presente documento tiene por objetivo definir una base técnica y conceptual para el desarrollo de un Sistema de Microsimulación y Monitoreo Operacional del Transporte Público, orientado al análisis, simulación, control y optimización de la operación de buses urbanos mediante tecnologías modernas de procesamiento geoespacial, simulación computacional y visualización en tiempo real.

La propuesta toma como referencia conceptual modelos académicos de microsimulación como SIMTRANSIT, incorporando además capacidades modernas de integración con sistemas AVL, billetaje electrónico, analítica operacional y tecnologías ITS (Intelligent Transportation Systems).

El sistema permitirá representar digitalmente la operación del transporte público metropolitano mediante un modelo híbrido compuesto por:

* Motor de simulación operacional
* Procesamiento geoespacial
* Monitoreo en tiempo real
* Analítica operacional
* Gemelo digital del sistema de transporte

---

# 2. Objetivos del Sistema

## 2.1 Objetivo General

Desarrollar una plataforma informática integral para la simulación, monitoreo y análisis operacional del transporte público urbano utilizando datos georreferenciados y modelos de microsimulación.

---

## 2.2 Objetivos Específicos

* Simular la operación de buses en corredores urbanos.
* Modelar interacción entre buses, pasajeros y paraderos.
* Analizar regularidad operacional y headways.
* Detectar fenómenos de bunching.
* Simular escenarios operacionales futuros.
* Integrar información AVL y billetaje electrónico.
* Implementar visualización geoespacial en tiempo real.
* Construir una base para un futuro Digital Twin del sistema de transporte.

---

# 3. Alcance del Proyecto

El sistema contemplará inicialmente:

## Fase Inicial

* Monitoreo en tiempo real de buses.
* Simulación básica de recorridos.
* Modelado de paraderos.
* Indicadores de regularidad operacional.
* Dashboard operacional.

## Fase Intermedia

* Simulación de pasajeros.
* Cálculo dinámico de tiempos de parada.
* Simulación de congestión operacional.
* Predicción de atrasos.

## Fase Avanzada

* Gemelo digital operacional.
* Simulación de políticas públicas.
* Modelos predictivos con IA.
* Optimización automática de frecuencias.

---

# 4. Arquitectura General del Sistema

```text
┌─────────────────────────────┐
│        Frontend React       │
│  Dashboards + Mapas + KPI   │
└──────────────┬──────────────┘
               │
        REST / WebSockets
               │
┌──────────────▼──────────────┐
│        API Backend          │
│         FastAPI             │
└──────────────┬──────────────┘
               │
 ┌─────────────┼─────────────┐
 │             │             │
 ▼             ▼             ▼
Motor       Analítica      Integración
Simulación    IA           AVL/Billetaje

               │
               ▼
┌─────────────────────────────┐
│ PostgreSQL + PostGIS        │
│ Datos operacionales         │
│ Datos geoespaciales         │
│ Simulación                  │
└─────────────────────────────┘
```

---

# 5. Stack Tecnológico

## Backend

| Tecnología | Función                   |
| ---------- | ------------------------- |
| Python     | Lógica principal          |
| FastAPI    | API REST                  |
| SQLAlchemy | ORM                       |
| SimPy      | Motor de simulación       |
| GeoPandas  | Procesamiento geoespacial |
| Pandas     | Analítica                 |
| Redis      | Eventos en tiempo real    |

---

## Base de Datos

| Tecnología  | Función             |
| ----------- | ------------------- |
| PostgreSQL  | Base relacional     |
| PostGIS     | Datos geoespaciales |
| TimescaleDB | Series temporales   |

---

## Frontend

| Tecnología       | Función                  |
| ---------------- | ------------------------ |
| React            | Interfaz web             |
| Vite             | Build frontend           |
| Leaflet / Mapbox | Visualización geográfica |
| Recharts         | Gráficos                 |
| Zustand          | Manejo de estado         |

---

## Infraestructura

| Tecnología     | Función               |
| -------------- | --------------------- |
| Docker         | Contenedores          |
| Nginx          | Reverse Proxy         |
| Azure          | Infraestructura cloud |
| GitHub Actions | CI/CD                 |

---

# 6. Componentes Principales

---

## 6.1 Módulo AVL

Responsable de:

* Recepción de posiciones GPS.
* Validación de datos.
* Map matching.
* Almacenamiento histórico.
* Generación de eventos operacionales.

### Datos Procesados

* Latitud
* Longitud
* Velocidad
* Sentido
* Timestamp
* Estado operacional

---

## 6.2 Módulo de Simulación

Motor encargado de:

* Simular desplazamiento de buses.
* Calcular tiempos de parada.
* Modelar frecuencia operacional.
* Simular congestión.

### Variables simuladas

* Headway
* Velocidad comercial
* Tiempo de ciclo
* Ocupación
* Regularidad

---

## 6.3 Módulo de Pasajeros

Modelará:

* Llegada de pasajeros.
* Ascenso y descenso.
* Demanda por paradero.
* Transferencias.

### Parámetros

* Tasa de llegada
* Tiempo marginal de ascenso
* Tiempo marginal de descenso
* Capacidad vehicular

---

## 6.4 Módulo de Analítica

Permitirá:

* KPI operacionales.
* Indicadores históricos.
* Predicción de atrasos.
* Detección de bunching.
* Evaluación de cumplimiento.

---

## 6.5 Dashboard Operacional

Visualización en tiempo real:

* Buses en mapa.
* Estado operacional.
* Alertas.
* KPI.
* Simulación en vivo.

---

# 7. Modelo de Datos Inicial

## Tablas principales

### empresas

```sql
id_empresa
nombre
estado
```

### lineas

```sql
id_linea
codigo
descripcion
```

### rutas

```sql
id_ruta
geom
sentido
```

### paraderos

```sql
id_paradero
nombre
geom
tipo
```

### buses

```sql
id_bus
interno
placa
capacidad
```

### posiciones_gps

```sql
id
id_bus
geom
velocidad
timestamp
```

### eventos_operacionales

```sql
id
tipo_evento
id_bus
timestamp
descripcion
```

### pasajeros_simulados

```sql
id_pasajero
origen
destino
hora_llegada
```

---

# 8. Funcionalidades Iniciales

## MVP

### Operacionales

* Visualización GPS.
* Reproducción histórica.
* Headway.
* Regularidad.

### Simulación

* Movimiento de buses.
* Tiempos de parada.
* Congestión básica.

### Analítica

* KPI operacionales.
* Detección de atrasos.

---

# 9. Funcionalidades Futuras

* IA predictiva.
* Optimización de frecuencias.
* Semaforización inteligente.
* Evaluación de carriles exclusivos.
* Integración ITS.
* Simulación de políticas públicas.
* Digital Twin completo.

---

# 10. Integración con Sistemas Existentes

El sistema podrá integrarse con:

* Sistema AVL.
* Sistema de Billetaje Electrónico.
* Sistemas GIS institucionales.
* APIs externas.
* Plataformas de fiscalización.

---

# 11. Seguridad

## Medidas recomendadas

* JWT Authentication
* OAuth2
* Restricción por IP
* VPN institucional
* Auditoría de accesos
* Encriptación TLS
* Roles y permisos

---

# 12. Escalabilidad

La arquitectura permitirá:

* procesamiento distribuido,
* múltiples corredores,
* simulaciones paralelas,
* almacenamiento histórico masivo,
* expansión metropolitana.

---

# 13. Casos de Uso Estratégicos

## Operacionales

* Control de regularidad.
* Fiscalización.
* Detección de incumplimientos.

## Técnicos

* Evaluación de infraestructura.
* Diseño de corredores.
* Análisis de demanda.

## Estratégicos

* Planeamiento operacional.
* Simulación de reformas.
* Evaluación normativa.

---

# 14. Roadmap de Implementación

## Etapa 1

Infraestructura base.

* PostgreSQL/PostGIS
* API FastAPI
* React Dashboard

## Etapa 2

Integración AVL.

* Tiempo real
* Georreferenciación

## Etapa 3

Motor de simulación.

* Headways
* Paraderos
* Frecuencias

## Etapa 4

Pasajeros simulados.

* Demanda
* Ascenso/descenso

## Etapa 5

IA y predicción.

* Bunching
* Saturación
* Optimización

---

# 15. Conclusión

La implementación de una plataforma de microsimulación operacional basada en PostgreSQL, Python y React permitirá desarrollar capacidades avanzadas de monitoreo, análisis y optimización del transporte público metropolitano.

La utilización de datos reales provenientes de AVL y billetaje electrónico permitirá evolucionar progresivamente hacia un modelo de Digital Twin del sistema de transporte público, constituyendo una herramienta estratégica para la toma de decisiones técnicas y operacionales.
