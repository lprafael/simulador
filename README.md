# SimTransit — Microsimulador de Transporte Público

SimTransit es una plataforma integral de microsimulación y monitoreo operacional diseñada para el análisis, control y optimización del transporte público urbano. Utiliza modelos de simulación de eventos discretos para representar la interacción entre buses, pasajeros y paraderos en tiempo real.

## 🚀 Características Principales

*   **Motor de Simulación (SimPy):** Modelado preciso de agentes (buses y pasajeros) con variables de congestión y tiempos de parada dinámicos.
*   **Visualización Geoespacial:** Mapa interactivo basado en Leaflet con representación de flota en tiempo real (Asunción, Paraguay como escenario base).
*   **Análisis Operacional:** Cálculo automático de KPIs como Headway, Regularidad, Bunching y Velocidad Comercial.
*   **Arquitectura Moderna:** Backend con FastAPI, base de datos geoespacial PostGIS y frontend reactivo con React 18 + Vite.
*   **Dashboard de Control:** Interfaz premium con glassmorphism, gráficos dinámicos (Recharts) y monitoreo de eventos.

## 🛠️ Stack Tecnológico

*   **Backend:** Python 3.11, FastAPI, SimPy, SQLAlchemy, GeoPandas.
*   **Frontend:** React, Zustand, Leaflet, Recharts, Lucide Icons.
*   **Base de Datos:** PostgreSQL 15 + PostGIS.
*   **Infraestructura:** Docker, Docker Compose, Nginx.

## 📋 Requisitos

*   Docker y Docker Compose.
*   (Opcional para desarrollo local) Python 3.11+ y Node.js 20+.

## 🛠️ Instalación y Ejecución

1.  **Clonar el repositorio y navegar a la carpeta:**
    ```bash
    cd SIMULADOR
    ```

2.  **Configurar variables de entorno:**
    El sistema ya cuenta con un archivo `.env` configurado por defecto.

3.  **Iniciar con Docker Compose:**
    ```bash
    docker-compose up --build
    ```

4.  **Acceder a las interfaces:**
    *   **Frontend:** [http://localhost](http://localhost) (o [http://localhost:3000](http://localhost:3000))
    *   **API Docs:** [http://localhost/docs](http://localhost/docs)
    *   **Base de Datos:** Puerto 5432.

## 📂 Estructura del Proyecto

*   `/backend`: API FastAPI y motor de simulación.
*   `/frontend`: SPA React con Dashboard y Mapas.
*   `/nginx`: Configuración del proxy inverso.
*   `/backend/db`: Scripts de inicialización SQL y semillas de datos.

## 🚦 Casos de Uso

*   **Detección de Bunching:** Visualice cuándo los buses se agrupan y pierden la regularidad.
*   **Optimización de Frecuencias:** Pruebe diferentes headways para ver el impacto en el tiempo de espera de los pasajeros.
*   **Monitoreo en Tiempo Real:** Simulación de AVL para entrenamiento de reguladores.

---
Desarrollado para el Centro de Innovación y Desarrollo (CID).
