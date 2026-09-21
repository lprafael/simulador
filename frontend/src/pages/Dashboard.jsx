import React, { useState, useEffect } from 'react'
import { RefreshCw, Activity, Bus, Zap, TrendingUp } from 'lucide-react'
import Header from '../components/Layout/Header'
import KpiCards from '../components/Dashboard/KpiCards'
import SimulacionPanel from '../components/Simulation/SimulacionPanel'
import PlanningPanel from '../components/Simulation/PlanningPanel'
import BusMap from '../components/Map/BusMap'
import { kpiApi, busesApi, ufApi, lineasApi } from '../services/api'
import { useSimulacionStore, useBusStore } from '../store'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend
} from 'recharts'

// Buses de prueba para el mapa (posiciones simuladas en Asunción)
const BUSES_DEMO = [
  { id_bus: 1, interno: '001', lat: -25.3390, lon: -57.5200, velocidad: 0, estado: 'ACTIVO' },
  { id_bus: 2, interno: '002', lat: -25.3350, lon: -57.5100, velocidad: 35, estado: 'ACTIVO' },
  { id_bus: 3, interno: '003', lat: -25.3300, lon: -57.5000, velocidad: 40, estado: 'ACTIVO' },
  { id_bus: 4, interno: '004', lat: -25.3250, lon: -57.4900, velocidad: 28, estado: 'ACTIVO' },
  { id_bus: 5, interno: '005', lat: -25.2990, lon: -57.5600, velocidad: 45, estado: 'ACTIVO' },
  { id_bus: 6, interno: '006', lat: -25.2850, lon: -57.6200, velocidad: 30, estado: 'ACTIVO' },
]

const PARADEROS_DEMO = [
  { id_paradero: 1, nombre: 'Terminal Fernando de la Mora', tipo: 'INICIO', lat: -25.3390, lon: -57.5200, orden_ruta: 1 },
  { id_paradero: 2, nombre: 'Avda. Rodríguez de Francia', tipo: 'INTERMEDIO', lat: -25.3350, lon: -57.5100, orden_ruta: 2 },
  { id_paradero: 3, nombre: 'Cruce Avda. Eusebio Ayala', tipo: 'INTERMEDIO', lat: -25.3300, lon: -57.5000, orden_ruta: 3 },
  { id_paradero: 4, nombre: 'Mercado 4', tipo: 'INTERMEDIO', lat: -25.2990, lon: -57.6160, orden_ruta: 5 },
  { id_paradero: 5, nombre: 'Plaza de los Héroes', tipo: 'INTERMEDIO', lat: -25.2850, lon: -57.6350, orden_ruta: 6 },
  { id_paradero: 6, nombre: 'Terminal Ómnibus Asunción', tipo: 'TERMINAL', lat: -25.2900, lon: -57.6350, orden_ruta: 8 },
]

// Tooltip personalizado para Recharts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        fontSize: '0.8rem',
      }}>
        <p style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, fontWeight: 600 }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function Dashboard() {
  const [kpis, setKpis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [buses, setBuses] = useState(BUSES_DEMO)
  const [resultadosSim, setResultadosSim] = useState(null)
  const [chartData, setChartData] = useState([])
  const [eventosRecientes, setEventosRecientes] = useState([])
  
  const { posicionesSimuladas, eventosSimulacion } = useSimulacionStore()

  const cargarKPIs = async () => {
    setLoading(true)
    try {
      const res = await kpiApi.resumen()
      setKpis(res.data?.ultima_simulacion?.kpis || null)
    } catch (err) {
      // Servidor no disponible, usar valores demo
    } finally {
      setLoading(false)
    }
  }

  const [unidadesFuncionales, setUnidadesFuncionales] = useState([])
  const [lineasFiltradas, setLineasFiltradas] = useState([])
  const [rutasFiltradas, setRutasFiltradas] = useState([])
  
  const [idUfSel, setIdUfSel] = useState('')
  const [idLineaSel, setIdLineaSel] = useState('')
  const [rutaGeoJSON, setRutaGeoJSON] = useState(null)

  const cargarUFs = async () => {
    try {
      const res = await ufApi.listar()
      setUnidadesFuncionales(res.data)
    } catch (err) {
      console.warn("Error cargando UFs:", err)
    }
  }

  const handleSeleccionarUF = async (idUf) => {
    setIdUfSel(idUf)
    setIdLineaSel('')
    setRutasFiltradas([])
    setLineasFiltradas([])
    if (!idUf) return

    try {
      const res = await ufApi.listarLineas(idUf)
      setLineasFiltradas(res.data)
    } catch (err) {
      console.error("Error cargando líneas por UF:", err)
    }
  }

  const handleSeleccionarLinea = async (idLinea) => {
    setIdLineaSel(idLinea)
    setRutasFiltradas([])
    if (!idLinea) return

    try {
      const res = await lineasApi.obtenerRutas(idLinea)
      setRutasFiltradas(res.data)
    } catch (err) {
      console.error("Error cargando rutas de la línea:", err)
    }
  }

  const handleSeleccionarRuta = async (ruta_hex) => {
    if (!ruta_hex) {
      setRutaGeoJSON(null)
      return
    }
    try {
      const res = await lineasApi.obtenerGeometria(ruta_hex)
      setRutaGeoJSON(res.data)
    } catch (err) {
      console.error("Error cargando geometría:", err)
    }
  }

  useEffect(() => {
    cargarKPIs()
    cargarUFs()
  }, [])

  const handleResultadosSimulacion = (data) => {
    setResultadosSim(data)
    
    // KPIs desde simulación
    setKpis(data.kpis || data)
    
    // Preparar datos para gráfico de headways
    if (data.headways) {
      const hw = Object.entries(data.headways)
      const chartPoints = hw.flatMap(([paraderoId, headwayList]) =>
        headwayList.map((hw, i) => ({
          name: `P${paraderoId}-${i+1}`,
          headway: Number(hw.toFixed(2)),
          programado: 8,
        }))
      ).slice(0, 40)
      setChartData(chartPoints)
    }
    
    // Eventos
    if (data.eventos) {
      setEventosRecientes(data.eventos.slice(0, 15))
    }
    
    // Posiciones en mapa
    if (data.posiciones && data.posiciones.length > 0) {
      // Tomar última posición de cada bus
      const byBus = {}
      data.posiciones.forEach(p => { byBus[p.id_bus] = p })
      const busPositions = Object.values(byBus).map(p => ({
        id_bus: p.id_bus,
        interno: p.interno || `BUS-${p.id_bus}`,
        lat: PARADEROS_DEMO[p.id_bus % PARADEROS_DEMO.length]?.lat ?? -25.2900,
        lon: PARADEROS_DEMO[p.id_bus % PARADEROS_DEMO.length]?.lon ?? -57.6350,
        velocidad: p.velocidad_kmh || 25,
        pasajeros_abordo: p.pasajeros_abordo,
        estado: 'SIMULADO',
      }))
      if (busPositions.length > 0) setBuses(busPositions)
    }
  }

  const ocupacionData = resultadosSim?.estados_buses?.map(b => ({
    nombre: b.interno,
    ascensos: b.total_ascensos,
    descensos: b.total_descensos,
  })) || []

  const TIPO_EVENTO_COLOR = {
    'BUNCHING': 'var(--color-warning)',
    'ARRIBO': 'var(--color-info)',
    'PARTIDA': 'var(--color-text-muted)',
    'ATRASO': 'var(--color-danger)',
  }

  return (
    <>
      <Header
        titulo="Dashboard Operacional"
        subtitulo="Sistema de Microsimulación de Transporte Público — Asunción, Paraguay"
        acciones={
          <button className="btn btn-outline btn-sm" onClick={cargarKPIs} id="btn-refresh-kpis">
            <RefreshCw size={14} />
            Actualizar
          </button>
        }
      />

      <div className="page-content">
        {/* KPI Cards */}
        <section style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h2 style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Indicadores Operacionales
            </h2>
            {kpis && (
              <div className="live-indicator">
                <div className="live-dot" />
                Datos de última simulación
              </div>
            )}
          </div>
          <KpiCards kpis={kpis} loading={loading} />
        </section>

        {/* Mapa + Panel de Simulación */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-xl)' }}>
          {/* Mapa */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--color-border)', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="card-title">Infraestructura Real</span>
                
                {/* Selector 1: Unidad Funcional */}
                <select 
                  className="form-control" 
                  style={{ width: 140, padding: '2px 8px', fontSize: '0.75rem' }}
                  value={idUfSel}
                  onChange={(e) => handleSeleccionarUF(e.target.value)}
                >
                  <option value="">1. Unidad Funcional</option>
                  {unidadesFuncionales.map(uf => (
                    <option key={uf.id_uf} value={uf.id_uf}>{uf.uf_nombre}</option>
                  ))}
                </select>

                {/* Selector 2: Línea */}
                <select 
                  className="form-control" 
                  style={{ width: 140, padding: '2px 8px', fontSize: '0.75rem' }}
                  value={idLineaSel}
                  disabled={!idUfSel}
                  onChange={(e) => handleSeleccionarLinea(e.target.value)}
                >
                  <option value="">2. Línea</option>
                  {lineasFiltradas.map(l => (
                    <option key={l.id_linea} value={l.id_linea}>{l.codigo} - {l.nombre}</option>
                  ))}
                </select>

                {/* Selector 3: Ruta (Itinerario) */}
                <select 
                  className="form-control" 
                  style={{ width: 180, padding: '2px 8px', fontSize: '0.75rem' }}
                  disabled={!idLineaSel}
                  onChange={(e) => handleSeleccionarRuta(e.target.value)}
                >
                  <option value="">3. Ruta / Itinerario</option>
                  {rutasFiltradas.map(r => (
                    <option key={r.ruta_hex} value={r.ruta_hex}>
                      {r.sentido.toUpperCase()} - {r.identificacion || r.ruta_hex}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                <span>🟢 Activo</span>
                <span>🟡 Bunching</span>
                <span>🔴 Alerta</span>
              </div>
            </div>
            <div style={{ height: 420 }}>
              <BusMap
                buses={buses}
                rutaCoords={rutaGeoJSON}
                paraderos={PARADEROS_DEMO}
                height="420px"
              />
            </div>
          </div>

          {/* Panel de Simulación */}
          <SimulacionPanel onResultados={handleResultadosSimulacion} />
        </div>

        {/* Panel de Planificación Operativa (Calculador de Flota) */}
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-xl)' }}>
           <PlanningPanel idLinea={idLineaSel} />
           <div className="card" style={{ background: 'linear-gradient(135deg, var(--color-bg-card) 0%, rgba(59, 130, 246, 0.05) 100%)' }}>
             <div className="card-header">
               <span className="card-title">Análisis de Capacidad Proyectada</span>
             </div>
             <div style={{ padding: 24, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <TrendingUp size={48} color="var(--color-accent-blue)" style={{ marginBottom: 16, opacity: 0.5 }} />
                <h3 style={{ fontSize: '1.1rem', marginBottom: 8 }}>Dimensionamiento de Oferta</h3>
                <p style={{ color: 'var(--color-text-muted)', maxWidth: 500, fontSize: '0.9rem' }}>
                  Ajuste el control de frecuencia en el panel de la izquierda para calcular cuántos buses necesita la UF para mantener el nivel de servicio deseado. El sistema calculará automáticamente la capacidad de pasajeros por hora.
                </p>
             </div>
           </div>
        </div>

        {/* Gráficos de resultados */}
        {resultadosSim && (
          <div className="grid-2" style={{ marginBottom: 'var(--spacing-xl)' }}>
            {/* Gráfico Headway */}
            {chartData.length > 0 && (
              <div className="card fade-in">
                <div className="card-header">
                  <span className="card-title">Headway por Observación</span>
                  <span className="badge badge-info">minutos</span>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis tick={{ fill: '#475569', fontSize: 10 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                    <Line
                      type="monotone"
                      dataKey="headway"
                      name="Headway real"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="programado"
                      name="Programado"
                      stroke="#f59e0b"
                      strokeWidth={1.5}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Gráfico Pasajeros por Bus */}
            {ocupacionData.length > 0 && (
              <div className="card fade-in">
                <div className="card-header">
                  <span className="card-title">Pasajeros por Bus</span>
                  <span className="badge badge-success">simulados</span>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={ocupacionData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="nombre" tick={{ fill: '#475569', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#475569', fontSize: 10 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                    <Bar dataKey="ascensos" name="Ascensos" fill="#10b981" radius={[4,4,0,0]} />
                    <Bar dataKey="descensos" name="Descensos" fill="#3b82f6" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* Tabla de Eventos Recientes */}
        {eventosRecientes.length > 0 && (
          <div className="card fade-in">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Activity size={16} color="var(--color-accent-rose)" />
                <span className="card-title">Eventos de Simulación</span>
              </div>
              <span className="badge badge-neutral">{eventosRecientes.length} eventos</span>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Bus</th>
                    <th>Tiempo (min)</th>
                    <th>Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {eventosRecientes.map((ev, i) => (
                    <tr key={i}>
                      <td>
                        <span className="badge" style={{
                          background: `${TIPO_EVENTO_COLOR[ev.tipo_evento]}20`,
                          color: TIPO_EVENTO_COLOR[ev.tipo_evento] || 'var(--color-text-secondary)',
                        }}>
                          {ev.tipo_evento}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                        Bus-{ev.id_bus}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                        {ev.tiempo_sim?.toFixed(1)}
                      </td>
                      <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                        {ev.descripcion}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Estado inicial sin simulación */}
        {!resultadosSim && !loading && (
          <div className="card" style={{ marginTop: 0 }}>
            <div className="empty-state">
              <div className="empty-state-icon">🚌</div>
              <h3 style={{ marginBottom: 8, color: 'var(--color-text-primary)' }}>Sistema Listo</h3>
              <p style={{ maxWidth: 400 }}>
                Configure los parámetros de simulación en el panel de la derecha y ejecute una simulación para ver los resultados operacionales, gráficos de headway y análisis de bunching.
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
