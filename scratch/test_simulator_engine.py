
import sys
import os

# Añadir el directorio backend al path para poder importar app
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.simulacion.motor import (
    MotorSimulacion, ConfigSimulacion, ConfigRuta, ConfigParadero
)

def run_test_simulation():
    print("--- Iniciando prueba del motor de simulacion ---")
    
    # 1. Configurar paraderos
    paraderos_demo = [
        ConfigParadero(id_paradero=1, nombre="Terminal Norte", orden=0, distancia_m=0, tasa_llegada_pax=0.5),
        ConfigParadero(id_paradero=2, nombre="Avda. Eusebio Ayala", orden=1, distancia_m=1800, tasa_llegada_pax=2.0),
        ConfigParadero(id_paradero=3, nombre="Mercado 4", orden=2, distancia_m=4200, tasa_llegada_pax=3.0),
        ConfigParadero(id_paradero=4, nombre="Plaza de los Heroes", orden=3, distancia_m=6500, tasa_llegada_pax=2.5),
        ConfigParadero(id_paradero=5, nombre="Hospital de Clinicas", orden=4, distancia_m=8800, tasa_llegada_pax=1.5),
        ConfigParadero(id_paradero=6, nombre="UNA - FCQ", orden=5, distancia_m=11000, tasa_llegada_pax=2.0),
        ConfigParadero(id_paradero=7, nombre="Shopping del Sol", orden=6, distancia_m=13500, tasa_llegada_pax=1.8),
        ConfigParadero(id_paradero=8, nombre="Terminal Sur", orden=7, distancia_m=15000, tasa_llegada_pax=0.3),
    ]
    
    # 2. Configurar simulacion
    config = ConfigSimulacion(
        id_linea=1,
        nombre_linea="Linea 30 - Prueba Motor",
        ruta=ConfigRuta(
            id_ruta=1,
            id_linea=1,
            nombre="Ruta de Prueba",
            paraderos=paraderos_demo,
            distancia_total_km=15.0,
        ),
        num_buses=4,
        headway_programado_min=10.0,
        velocidad_kmh=20.0,
        duracion_sim_min=60.0,  # 1 hora de simulacion
        tasa_pasajeros_global=10.0,
        semilla=42,
    )
    
    # 3. Ejecutar motor
    motor = MotorSimulacion(config)
    resultado = motor.ejecutar(id_simulacion=999)
    
    # 4. Mostrar resultados
    print("\n[OK] Simulacion completada exitosamente!")
    print(f"--- Resultados para: {resultado.nombre} ---")
    print(f"Duracion simulada: {resultado.duracion_sim_min} minutos")
    print(f"Total pasajeros transportados: {resultado.total_pasajeros_transportados}")
    print(f"Total eventos registrados: {resultado.total_eventos}")
    print(f"Headway promedio: {resultado.headway_promedio_min} min (Programado: {config.headway_programado_min} min)")
    print(f"Regularidad: {resultado.regularidad_pct}%")
    print(f"Bunching detectado: {resultado.pct_bunching}%")
    
    # Mostrar algunos eventos
    print("\nUltimos 5 eventos:")
    for evento in resultado.eventos[-5:]:
        print(f"[{evento['tiempo_sim']:.2f} min] {evento['tipo_evento']}: {evento['descripcion']}")

if __name__ == "__main__":
    run_test_simulation()
