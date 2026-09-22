-- ============================================================
-- Datos Iniciales / Semilla del Simulador de Transporte Público
-- ============================================================

-- 1. Empresas Operadoras
INSERT INTO empresas (id_empresa, nombre, codigo_eot, ruc, estado) VALUES
(1, 'Empresa de Transporte Automotor San Isidro S.R.L.', 'EOT-001', '80012345-1', true),
(2, 'Transportistas Unidos S.A.', 'EOT-002', '80054321-2', true)
ON CONFLICT (id_empresa) DO NOTHING;

-- 2. Flota de Buses
INSERT INTO buses (id_bus, interno, placa, capacidad, estado, modelo, anio, id_empresa) VALUES
(1, '001', 'ABC-001', 45, 'ACTIVO', 'Agrale MA 15.0', 2019, 1),
(2, '002', 'ABC-002', 45, 'ACTIVO', 'Agrale MA 15.0', 2019, 1),
(3, '003', 'ABC-003', 45, 'ACTIVO', 'Agrale MA 15.0', 2020, 1),
(4, '004', 'ABC-004', 45, 'ACTIVO', 'Marcopolo Torino', 2021, 1),
(5, '005', 'ABC-005', 45, 'ACTIVO', 'Marcopolo Torino', 2021, 1),
(6, '006', 'ABC-006', 45, 'ACTIVO', 'Marcopolo Torino', 2022, 1),
(7, '007', 'DEF-001', 45, 'ACTIVO', 'Mercedes OF-1721', 2020, 2),
(8, '008', 'DEF-002', 45, 'ACTIVO', 'Mercedes OF-1721', 2020, 2),
(9, '009', 'DEF-003', 45, 'ACTIVO', 'Mercedes OF-1721', 2021, 2),
(10, '010', 'DEF-004', 45, 'ACTIVO', 'Caio Apache Vip', 2022, 2),
(11, '011', 'GHI-001', 50, 'ACTIVO', 'Caio Apache Vip', 2022, 2),
(12, '012', 'GHI-002', 50, 'ACTIVO', 'Caio Apache Vip', 2023, 2),
(13, '013', 'GHI-003', 50, 'ACTIVO', 'Caio Apache Vip', 2023, 2),
(14, '014', 'GHI-004', 45, 'INACTIVO', 'Agrale MA 15.0', 2018, 1),
(15, '015', 'GHI-005', 45, 'MANTENIMIENTO', 'Agrale MA 15.0', 2018, 1)
ON CONFLICT (id_bus) DO NOTHING;

-- 3. Paraderos Principales
INSERT INTO paraderos (id_paradero, nombre, tipo, lat, lon, orden_ruta, distancia_desde_inicio_m, estado) VALUES
(1, 'Terminal Fernando de la Mora', 'INICIO', -25.3390, -57.5200, 1, 0, true),
(2, 'Avda. Mcal. López y Madame Lynch', 'INTERMEDIO', -25.3350, -57.5100, 2, 2200, true),
(3, 'Cruce Avda. Eusebio Ayala', 'INTERMEDIO', -25.3300, -57.5000, 3, 4100, true),
(4, 'Mercado 4', 'INTERMEDIO', -25.2990, -57.6160, 4, 6800, true),
(5, 'Plaza de los Héroes / Microcentro', 'INTERMEDIO', -25.2850, -57.6350, 5, 8900, true),
(6, 'Terminal Ómnibus Asunción', 'TERMINAL', -25.2900, -57.6350, 6, 11500, true)
ON CONFLICT (id_paradero) DO NOTHING;

-- Sincronizar secuencias
SELECT setval('buses_id_bus_seq', COALESCE((SELECT MAX(id_bus) FROM buses), 1));
SELECT setval('empresas_id_empresa_seq', COALESCE((SELECT MAX(id_empresa) FROM empresas), 1));
SELECT setval('paraderos_id_paradero_seq', COALESCE((SELECT MAX(id_paradero) FROM paraderos), 1));
