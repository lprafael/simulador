import React, { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import BusMap from '../components/Map/BusMap'
import SimulacionPanel from '../components/Simulation/SimulacionPanel'
import { useSimulacionStore } from '../store'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const PARADEROS_DEMO = [
  { id_paradero: 1, nombre: 'Terminal Fernando de la Mora', tipo: 'INICIO', lat: -25.3390, lon: -57.5200, orden_ruta: 1 },
  { id_paradero: 2, nombre: 'Avda. Rodríguez de Francia', tipo: 'INTERMEDIO', lat: -25.3350, lon: -57.5100, orden_ruta: 2 },
  { id_paradero: 3, nombre: 'Cruce Avda. Eusebio Ayala', tipo: 'INTERMEDIO', lat: -25.3300, lon: -57.5000, orden_ruta: 3 },
  { id_paradero: 4, nombre: 'Mercado 4', tipo: 'INTERMEDIO', lat: -25.2990, lon: -57.6160, orden_ruta: 5 },
  { id_paradero: 5, nombre: 'Plaza de los Héroes', tipo: 'INTERMEDIO', lat: -25.2850, lon: -57.6350, orden_ruta: 6 },
  { id_paradero: 6, nombre: 'Terminal Ómnibus Asunción', tipo: 'TERMINAL', lat: -25.2900, lon: -57.6350, orden_ruta: 8 },
]

export default function MapaPage() {
  const [buses, setBuses] = useState([
    { id_bus: 1, interno: '001', lat: -25.3390, lon: -57.5200, velocidad: 0, estado: 'ACTIVO' },
    { id_bus: 2, interno: '002', lat: -25.3350, lon: -57.5100, velocidad: 35, estado: 'ACTIVO' },
    { id_bus: 3, interno: '003', lat: -25.3300, lon: -57.5000, velocidad: 40, estado: 'ACTIVO' },
    { id_bus: 4, interno: '004', lat: -25.2990, lon: -57.5600, velocidad: 28, estado: 'ACTIVO' },
    { id_bus: 5, interno: '005', lat: -25.2850, lon: -57.6200, velocidad: 45, estado: 'ACTIVO' },
    { id_bus: 6, interno: '006', lat: -25.2800, lon: -57.6300, velocidad: 30, estado: 'ACTIVO' },
  ])
  
  const [matrizOD, setMatrizOD] = useState([])
  const [congestion, setCongestion] = useState([])
  const [incidentesWaze, setIncidentesWaze] = useState([])
  const [showHeatmap, setShowHeatmap] = useState(false)
  const [showCongestion, setShowCongestion] = useState(false)
  const [showWaze, setShowWaze] = useState(false)

  useEffect(() => {
    // Cargar matriz OD inicial
    fetch(`${API_URL}/api/v1/planning/matriz-od`)
      .then(res => res.json())
      .then(data => setMatrizOD(data))
      .catch(err => console.error("Error cargando OD:", err))
    
    // Polling de congestión e incidentes
    const fetchData = async () => {
      try {
        const [cRes, wRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/kpi/congestion`),
          fetch(`${API_URL}/api/v1/kpi/incidentes-waze`)
        ])
        setCongestion(await cRes.json())
        setIncidentesWaze(await wRes.json())
      } catch (e) { console.error("Error polling data:", e) }
    }
    
    fetchData()
    const interval = setInterval(fetchData, 30000)
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
      setBuses(busPositions)
    }
  }

  return (
    <>
      <Header
        titulo="Mapa Operacional en Vivo"
        subtitulo="Visualización geoespacial de la flota — Asunción, Paraguay"
      />
      <div className="page-content" style={{ padding: 0, paddingTop: 'var(--header-height)' }}>
        <div style={{ display: 'flex', height: 'calc(100vh - var(--header-height))' }}>
          {/* Mapa a pantalla completa */}
          <div style={{ flex: 1 }}>
            <BusMap
              buses={buses}
              paraderos={PARADEROS_DEMO}
              matrizOD={showHeatmap ? matrizOD : []}
              congestion={showCongestion ? congestion : []}
              incidentesWaze={showWaze ? incidentesWaze : []}
              height="100%"
              zoom={12}
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
                { color: '#f43f5e', label: 'Paradero Terminal' },
                { color: '#3b82f6', label: 'Bus en operación' },
                { color: '#f59e0b', label: 'Bus en bunching' },
                { color: 'rgba(244, 63, 94, 0.4)', label: 'Zona Alta Demanda (OD)' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <div style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: item.color,
                    border: '2px solid rgba(255,255,255,0.3)',
                    flexShrink: 0,
                  }} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{item.label}</span>
                </div>
              ))}
            </div>
            
            {/* Stats flotantes */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Estado Flota</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Buses activos</span>
                <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>{buses.length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Paraderos</span>
                <span style={{ fontWeight: 700 }}>{PARADEROS_DEMO.length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Cobertura</span>
                <span style={{ fontWeight: 700, color: 'var(--color-accent-blue)' }}>15 km</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
