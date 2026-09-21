-- ============================================================
-- Sistema de Microsimulación de Transporte Público
-- Esquema inicial de base de datos
-- PostgreSQL + PostGIS
-- ============================================================

-- Activar extensiones
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────
-- Consorcios y Unidades Funcionales (Nuevos modelos)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS consorcios (
    id_consorcio SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    id_externo_cid VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS unidades_funcionales (
    id_uf SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    id_consorcio INTEGER REFERENCES consorcios(id_consorcio),
    id_externo_cid VARCHAR(50)
);

-- ─────────────────────────────────────────────────────────────
-- Empresas operadoras
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS empresas (
    id_empresa SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    codigo_eot VARCHAR(20) UNIQUE,
    ruc VARCHAR(20),
    id_consorcio INTEGER REFERENCES consorcios(id_consorcio),
    estado BOOLEAN DEFAULT true,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Líneas de transporte
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lineas (
    id_linea SERIAL PRIMARY KEY,
    numero_linea VARCHAR(20) NOT NULL UNIQUE,
    nombre_comercial VARCHAR(200),
    identificador_troncal VARCHAR(100),
    color_hex VARCHAR(7) DEFAULT '#3B82F6',
    estado BOOLEAN DEFAULT true,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS composicion_uf (
    id_comp_uf SERIAL PRIMARY KEY,
    id_uf INTEGER REFERENCES unidades_funcionales(id_uf),
    id_linea INTEGER REFERENCES lineas(id_linea)
);

-- ─────────────────────────────────────────────────────────────
-- Rutas (geometría del recorrido)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rutas (
    id_ruta SERIAL PRIMARY KEY,
    id_linea INTEGER REFERENCES lineas(id_linea),
    sentido VARCHAR(10) CHECK (sentido IN ('IDA', 'VUELTA')),
    nombre VARCHAR(200),
    geom GEOMETRY(LINESTRING, 4326),
    id_externo_cid INTEGER,
    distancia_km NUMERIC(8,2),
    tiempo_ciclo_min NUMERIC(6,1)
);

CREATE INDEX IF NOT EXISTS idx_rutas_geom ON rutas USING GIST(geom);

-- ─────────────────────────────────────────────────────────────
-- Paraderos (paradas de bus)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS paraderos (
    id_paradero SERIAL PRIMARY KEY,
    nombre VARCHAR(200),
    tipo VARCHAR(20) CHECK (tipo IN ('INICIO', 'INTERMEDIO', 'TERMINAL')),
    geom GEOMETRY(POINT, 4326),
    lat NUMERIC(10,7),
    lon NUMERIC(10,7),
    orden_ruta INTEGER,
    distancia_desde_inicio_m NUMERIC(10,1),
    id_ruta INTEGER REFERENCES rutas(id_ruta),
    estado BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_paraderos_geom ON paraderos USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_paraderos_ruta ON paraderos(id_ruta);

-- ─────────────────────────────────────────────────────────────
-- Buses
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS buses (
    id_bus SERIAL PRIMARY KEY,
    interno VARCHAR(20),
    placa VARCHAR(20),
    capacidad INTEGER DEFAULT 45,
    estado VARCHAR(20) DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO', 'MANTENIMIENTO')),
    modelo VARCHAR(100),
    anio INTEGER,
    id_empresa INTEGER REFERENCES empresas(id_empresa),
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_buses_empresa ON buses(id_empresa);
CREATE INDEX IF NOT EXISTS idx_buses_estado ON buses(estado);

-- ─────────────────────────────────────────────────────────────
-- Simulaciones
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulaciones (
    id_simulacion SERIAL PRIMARY KEY,
    nombre VARCHAR(200),
    estado VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'CORRIENDO', 'COMPLETADO', 'ERROR')),
    parametros JSONB,
    resultado_resumen JSONB,
    fecha_inicio_sim TIMESTAMPTZ,
    fecha_fin_sim TIMESTAMPTZ,
    id_linea INTEGER REFERENCES lineas(id_linea),
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Posiciones GPS (tabla principal AVL)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posiciones_gps (
    id BIGSERIAL,
    id_bus INTEGER REFERENCES buses(id_bus),
    geom GEOMETRY(POINT, 4326),
    lat NUMERIC(10,7),
    lon NUMERIC(10,7),
    velocidad NUMERIC(5,1),
    rumbo INTEGER,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fuente VARCHAR(20) DEFAULT 'AVL',
    id_simulacion INTEGER REFERENCES simulaciones(id_simulacion)
);

CREATE INDEX IF NOT EXISTS idx_gps_bus_time ON posiciones_gps(id_bus, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gps_geom ON posiciones_gps USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON posiciones_gps(timestamp DESC);

-- ─────────────────────────────────────────────────────────────
-- Eventos Operacionales
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eventos_operacionales (
    id SERIAL PRIMARY KEY,
    tipo_evento VARCHAR(50),
    id_bus INTEGER REFERENCES buses(id_bus),
    id_paradero INTEGER REFERENCES paraderos(id_paradero),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    descripcion TEXT,
    metadata_evento JSONB,
    id_simulacion INTEGER REFERENCES simulaciones(id_simulacion)
);

CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos_operacionales(tipo_evento);
CREATE INDEX IF NOT EXISTS idx_eventos_timestamp ON eventos_operacionales(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_eventos_bus ON eventos_operacionales(id_bus);

-- ─────────────────────────────────────────────────────────────
-- Pasajeros Simulados
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pasajeros_simulados (
    id_pasajero BIGSERIAL PRIMARY KEY,
    id_simulacion INTEGER REFERENCES simulaciones(id_simulacion),
    id_paradero_origen INTEGER REFERENCES paraderos(id_paradero),
    id_paradero_destino INTEGER REFERENCES paraderos(id_paradero),
    hora_llegada NUMERIC(10,2),    -- minutos desde inicio
    hora_abordaje NUMERIC(10,2),
    hora_descenso NUMERIC(10,2),
    tiempo_espera NUMERIC(8,2),
    id_bus INTEGER REFERENCES buses(id_bus)
);

CREATE INDEX IF NOT EXISTS idx_pax_sim ON pasajeros_simulados(id_simulacion);

-- ─────────────────────────────────────────────────────────────
-- Vista: Buses con última posición
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_buses_posicion_actual AS
SELECT 
    b.id_bus,
    b.interno,
    b.placa,
    b.estado,
    b.capacidad,
    e.nombre AS empresa,
    p.lat,
    p.lon,
    p.velocidad,
    p.timestamp AS ultima_actualizacion
FROM buses b
LEFT JOIN empresas e ON b.id_empresa = e.id_empresa
LEFT JOIN LATERAL (
    SELECT lat, lon, velocidad, timestamp
    FROM posiciones_gps
    WHERE id_bus = b.id_bus
    ORDER BY timestamp DESC
    LIMIT 1
) p ON true
WHERE b.estado = 'ACTIVO';

-- ─────────────────────────────────────────────────────────────
-- Vista: KPI headway por línea (última simulación)
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_kpi_lineas AS
SELECT 
    l.id_linea,
    l.numero_linea AS codigo,
    l.nombre_comercial AS descripcion,
    s.resultado_resumen->>'headway_promedio_min' AS headway_promedio,
    s.resultado_resumen->>'regularidad_pct' AS regularidad,
    s.resultado_resumen->>'pct_bunching' AS pct_bunching,
    s.creado_en AS fecha_ultima_sim
FROM lineas l
LEFT JOIN LATERAL (
    SELECT resultado_resumen, creado_en
    FROM simulaciones
    WHERE id_linea = l.id_linea AND estado = 'COMPLETADO'
    ORDER BY creado_en DESC
    LIMIT 1
) s ON true
WHERE l.estado = true;

-- ─────────────────────────────────────────────────────────────
-- Módulo de Tránsito y Escenarios What-If (Gran Asunción)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tramos_viales (
    id_tramo SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE,
    nombre_calle VARCHAR(200) NOT NULL,
    municipio VARCHAR(100) NOT NULL DEFAULT 'Asunción',
    categoria VARCHAR(50) DEFAULT 'ARTERIAL',
    sentido VARCHAR(20) DEFAULT 'DOBLE' CHECK (sentido IN ('DOBLE', 'UNICO_DIRECTO', 'UNICO_INVERSO', 'CERRADO')),
    nodo_origen VARCHAR(50) NOT NULL,
    nodo_destino VARCHAR(50) NOT NULL,
    carriles INTEGER DEFAULT 2,
    longitud_m NUMERIC(10,2) DEFAULT 500.0,
    velocidad_limite_kmh NUMERIC(5,1) DEFAULT 50.0,
    capacidad_veh_hora INTEGER DEFAULT 1600,
    flujo_base_veh_hora INTEGER DEFAULT 800,
    geom GEOMETRY(LINESTRING, 4326),
    coordenadas JSONB,
    lineas_colectivo JSONB DEFAULT '[]'::jsonb,
    estado BOOLEAN DEFAULT true,
    actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tramos_municipio ON tramos_viales(municipio);
CREATE INDEX IF NOT EXISTS idx_tramos_geom ON tramos_viales USING GIST(geom);

CREATE TABLE IF NOT EXISTS escenarios_what_if (
    id_escenario SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    municipio VARCHAR(100) NOT NULL DEFAULT 'Asunción',
    franja_horaria VARCHAR(50) DEFAULT 'PICO_MANANA',
    descripcion TEXT,
    modificaciones JSONB NOT NULL DEFAULT '[]'::jsonb,
    kpis_resultado JSONB,
    creado_por VARCHAR(100) DEFAULT 'Dirección de Tránsito',
    creado_en TIMESTAMPTZ DEFAULT NOW()
);
