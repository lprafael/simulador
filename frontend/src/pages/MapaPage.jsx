import React, { useState, useEffect, useMemo } from 'react'
import Header from '../components/Layout/Header'
import BusMap from '../components/Map/BusMap'
import SimulacionPanel from '../components/Simulation/SimulacionPanel'
import { useSimulacionStore, useBusStore } from '../store'
import { kpiApi, planningApi } from '../services/api'
import { Radio, Wifi } from 'lucide-react'

const PARADEROS_DEMO = [
  { id_paradero: 1, nombre: 'Terminal Fernando de la Mora', tipo: 'INICIO', lat: -25.3390, lon: -57.5200, orden_ruta: 1 },
  { id_paradero: 2, nombre: 'Avda. Rodríguez de Francia', tipo: 'INTERMEDIO', lat: -25.3350, lon: -57.5100, orden_ruta: 2 },
  { id_paradero: 3, nombre: 'Cruce Avda. Eusebio Ayala', tipo: 'INTERMEDIO', lat: -25.3300, lon: -57.5000, orden_ruta: 3 },
  { id_paradero: 4, nombre: 'Mercado 4', tipo: 'INTERMEDIO', lat: -25.2990, lon: -57.6160, orden_ruta: 5 },
  { id_paradero: 5, nombre: 'Plaza de los Héroes', tipo: 'INTERMEDIO', lat: -25.2850, lon: -57.6350, orden_ruta: 6 },
  { id_paradero: 6, nombre: 'Terminal Ómnibus Asunción', tipo: 'TERMINAL', lat: -25.2900, lon: -57.6350, orden_ruta: 8 },
]

const BUSES_INICIALES = [
  { id_bus: 1, interno: '001', lat: -25.3390, lon: -57.5200, velocidad: 25, estado: 'ACTIVO' },
  { id_bus: 2, interno: '002', lat: -25.3350, lon: -57.5100, velocidad: 35, estado: 'ACTIVO' },
  { id_bus: 3, interno: '003', lat: -25.3300, lon: -57.5000, velocidad: 40, estado: 'ACTIVO' },
  { id_bus: 4, interno: '004', lat: -25.2990, lon: -57.5600, velocidad: 28, estado: 'ACTIVO' },
  { id_bus: 5, interno: '005', lat: -25.2850, lon: -57.6200, velocidad: 45, estado: 'ACTIVO' },
  { id_bus: 6, interno: '006', lat: -25.2800, lon: -57.6300, velocidad: 30, estado: 'ACTIVO' },
]

export default function MapaPage() {
  const [busesSimulados, setBusesSimulados] = useState(null)
  const [matrizOD, setMatrizOD] = useState([])
  const [congestion, setCongestion] = useState([])
  const [incidentesWaze, setIncidentesWaze] = useState([])
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [showCongestion, setShowCongestion] = useState(false)
  const [showWaze, setShowWaze] = useState(true)

  const { wsConectado } = useSimulacionStore()
  const posicionesRealtime = useBusStore((state) => state.posicionesRealtime)

  // Convertir mapa de posiciones realtime a array
  const busesEnVivo = useMemo(() => {
    const list = Object.values(posicionesRealtime)
    if (list.length === 0) return null
    return list.map(p => ({
      id_bus: p.id_bus,
      interno: p.interno || `BUS-${p.id_bus}`,
      lat: p.lat,
      lon: p.lon,
      velocidad: p.velocidad || 25,
      estado: p.estado || 'ACTIVO',
      rumbo: p.rumbo,
      timestamp: p.timestamp,
    }))
  }, [posicionesRealtime])

  // Buses a mostrar (prioriza simulación activa, luego WebSocket en vivo, luego iniciales)
  const busesMostrar = busesSimulados || busesEnVivo || BUSES_INICIALES

  useEffect(() => {
    // Cargar matriz OD
    planningApi.matrizOD()
      .then(res => setMatrizOD(res.data || []))
      .catch(err => console.warn("OD fallback:", err))
    
    // Polling de congestión e incidentes
    const fetchData = async () => {
      try {
        const [cRes, wRes] = await Promise.allSettled([
          kpiApi.congestion(),
          kpiApi.incidentesWaze()
        ])
        if (cRes.status === 'fulfilled') setCongestion(cRes.value.data || [])
        if (wRes.status === 'fulfilled') setIncidentesWaze(wRes.value.data || [])
      } catch (e) {
        console.error("Error polling data:", e)
      }
    }
    
    fetchData()
    const interval = setInterval(fetchData, 20000)
    return () => clearInterval(interval)
  }, [])

  const handleResultados = (data) => {
    if (!data) return
    const posiciones = data.posiciones || (Array.isArray(data) ? data : [])
    if (posiciones && posiciones.length > 0) {
      const byBus = {}
      posiciones.forEach(p => { if (p && p.id_bus != null) byBus[p.id_bus] = p })
      const busPositions = Object.values(byBus).map((p, i) => ({
        id_bus: p.id_bus,
        interno: p.interno || `BUS-${p.id_bus}`,
        lat: p.lat ?? (PARADEROS_DEMO[i % PARADEROS_DEMO.length]?.lat ?? -25.2900),
        lon: p.lon ?? (PARADEROS_DEMO[i % PARADEROS_DEMO.length]?.lon ?? -57.6350),
        velocidad: p.velocidad_kmh || 25,
        pasajeros_abordo: p.pasajeros_abordo,
        estado: 'SIMULADO',
      }))
      setBusesSimulados(busPositions)
    }
  }

  const cantidadBusesActivos = busesMostrar.length

  return (
    <>
      <Header
        titulo="Mapa Operacional en Vivo"
        subtitulo="Visualización geoespacial de la flota en tiempo real — Gran Asunción, Paraguay"
        acciones={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="live-indicator" style={{
              background: wsConectado ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              border: `1px solid ${wsConectado ? 'var(--color-success)' : 'var(--color-warning)'}`,
              color: wsConectado ? 'var(--color-success)' : 'var(--color-warning)',
              padding: '4px 12px',
              borderRadius: 20,
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}>
              <div className="live-dot" style={{ background: wsConectado ? 'var(--color-success)' : 'var(--color-warning)' }} />
              {wsConectado ? `Telemetría AVL Activa (${cantidadBusesActivos} buses)` : 'Conectando WebSocket...'}
            </div>
          </div>
        }
      />
      <div className="page-content" style={{ padding: 0, paddingTop: 'var(--header-height)' }}>
        <div style={{ display: 'flex', height: 'calc(100vh - var(--header-height))' }}>
          {/* Mapa a pantalla completa */}
          <div style={{ flex: 1 }}>
            <BusMap
              buses={busesMostrar}
              paraderos={PARADEROS_DEMO}
              matrizOD={showHeatmap ? matrizOD : []}
              congestion={showCongestion ? congestion : []}
              incidentesWaze={showWaze ? incidentesWaze : []}
              height="100%"
              zoom={13}
            />
          </div>
          
          {/* Panel lateral */}
          <div style={{
            width: 340,
            background: 'var(--color-bg-secondary)',
            borderLeft: '1px solid var(--color-border)',
            overflow: 'auto',
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}>
            <SimulacionPanel onResultados={handleResultados} />

            {/* Sección: Capas de Análisis Híbrido */}
            <div className="card" style={{ border: '1px solid var(--color-accent-blue)', background: 'rgba(59, 130, 246, 0.05)' }}>
              <div className="card-title" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                🌐 Capas de Inteligencia
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem' }}>📍 Matriz OD (Demanda)</span>
                  <label className="switch">
                    <input type="checkbox" checked={showHeatmap} onChange={(e) => setShowHeatmap(e.target.checked)} />
                    <span className="slider round"></span>
                  </label>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem' }}>🚦 Congestión (Interna)</span>
                  <label className="switch">
                    <input type="checkbox" checked={showCongestion} onChange={(e) => setShowCongestion(e.target.checked)} />
                    <span className="slider round"></span>
                  </label>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem' }}>🍊 Alertas Waze (CCP)</span>
                  <label className="switch">
                    <input type="checkbox" checked={showWaze} onChange={(e) => setShowWaze(e.target.checked)} />
                    <span className="slider round"></span>
                  </label>
                </div>
              </div>
            </div>
            
            {/* Leyenda */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Leyenda del Mapa</div>
              {[
                { color: '#10b981', label: 'Paradero Inicio' },
                { color: '#6b7280', label: 'Paradero Intermedio' },
                { color: '#f43f5e', label: 'Terminal / Fin' },
                { color: '#3b82f6', label: 'Bus en Operación' },
                { color: '#f59e0b', label: 'Bus con Retraso' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: item.color }} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
