import React, { useState, useEffect, useRef, useMemo } from 'react'
import Header from '../components/Layout/Header'
import BusMap from '../components/Map/BusMap'
import { cargaBusesApi } from '../services/api'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Calendar, 
  Route as RouteIcon, 
  Bus as BusIcon, 
  Users, 
  Database, 
  Activity, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  Layers, 
  AlertCircle,
  ArrowRight,
  Filter
} from 'lucide-react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts'

export default function CargaBusesPage() {
  const [rutas, setRutas] = useState([])
  const [selectedRuta, setSelectedRuta] = useState('')
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [selectedBus, setSelectedBus] = useState('')
  const [loading, setLoading] = useState(false)
  const [analisis, setAnalisis] = useState(null)
  const [error, setError] = useState(null)

  // Estados de Reproducción (Playback)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackTime, setPlaybackTime] = useState(null)
  const [playbackSpeed, setPlaybackSpeed] = useState(15)
  const [filtroSentido, setFiltroSentido] = useState('todos') // 'todos', 'ida', 'vuelta'
  const [activeTab, setActiveTab] = useState('mapa') // 'mapa', 'trayectos', 'graficos'

  const intervalRef = useRef(null)
  const currentTimeMsRef = useRef(null)
  const speedRef = useRef(15)

  // Cargar catálogo de rutas desde SisCID
  useEffect(() => {
    cargaBusesApi.rutasCatalogo()
      .then(res => {
        const data = res.data || []
        setRutas(data)
        if (data.length > 0) {
          // Seleccionar una ruta representativa por defecto
          const defaultRoute = data.find(r => r.identificador_troncal?.includes('Troncal') || r.ruta_hex === '0016' || r.ruta_hex === '0216') || data[0]
          setSelectedRuta(defaultRoute.ruta_hex)
        }
      })
      .catch(err => {
        console.warn("Error cargando rutas CID:", err)
      })
  }, [])

  // Ejecutar análisis al montar o al cambiar ruta/fecha
  const ejecutarAnalisis = async (rutaAUsar = selectedRuta) => {
    setLoading(true)
    setError(null)
    detenerPlayback()
    try {
      const params = {
        fecha,
        hora_inicio: 0,
        hora_fin: 24,
      }
      if (rutaAUsar) params.id_ruta = rutaAUsar
      if (selectedBus) params.id_bus = selectedBus

      const res = await cargaBusesApi.analizar(params)
      setAnalisis(res.data)

      // Inicializar cursor de tiempo de playback
      if (res.data.timeline && res.data.timeline.length > 0) {
        const timestamps = res.data.timeline.map(p => new Date(p.timestamp).getTime())
        const start = Math.min(...timestamps)
        currentTimeMsRef.current = start
        setPlaybackTime(new Date(start))
      }
    } catch (err) {
      console.error("Error al analizar carga:", err)
      setError(err.response?.data?.detail || "No se pudo obtener el análisis cruzado de carga.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedRuta) {
      ejecutarAnalisis(selectedRuta)
    }
  }, [selectedRuta, fecha])

  // Buses interpolados / filtrados para el momento actual del playback
  const busesEnMomento = useMemo(() => {
    if (!analisis) return []

    // Si no está en playback o no hay timeline, mostrar las últimas posiciones conocidas
    if (!currentTimeMsRef.current || !analisis.timeline || analisis.timeline.length === 0) {
      let bList = analisis.buses_en_mapa || []
      if (filtroSentido !== 'todos') {
        bList = bList.filter(b => b.sentido?.toLowerCase() === filtroSentido.toLowerCase())
      }
      return bList
    }

    const currentMs = currentTimeMsRef.current
    const windowMs = 25 * 60 * 1000 // 25 min de ventana de validez para cada bus

    // Agrupar timeline por bus y encontrar la posición más cercana <= currentMs
    const byBus = {}
    analisis.timeline.forEach(p => {
      const pTs = new Date(p.timestamp).getTime()
      if (pTs <= currentMs && currentMs - pTs <= windowMs) {
        if (!byBus[p.id_bus] || new Date(byBus[p.id_bus].timestamp).getTime() < pTs) {
          byBus[p.id_bus] = p
        }
      }
    })

    let list = Object.values(byBus)
    if (filtroSentido !== 'todos') {
      list = list.filter(b => b.sentido?.toLowerCase() === filtroSentido.toLowerCase())
    }
    return list
  }, [analisis, playbackTime, filtroSentido])

  // Playback control loop
  const iniciarPlayback = () => {
    if (!analisis?.timeline || analisis.timeline.length === 0) return
    setIsPlaying(true)

    const allTs = analisis.timeline.map(p => new Date(p.timestamp).getTime())
    const minTs = Math.min(...allTs)
    const maxTs = Math.max(...allTs)

    if (!currentTimeMsRef.current || currentTimeMsRef.current >= maxTs) {
      currentTimeMsRef.current = minTs
    }

    clearInterval(intervalRef.current)
    intervalRef.current = setInterval(() => {
      const stepMs = 200 * speedRef.current // avanzar proporcional a velocidad
      const nextMs = currentTimeMsRef.current + stepMs

      if (nextMs >= maxTs) {
        currentTimeMsRef.current = maxTs
        setPlaybackTime(new Date(maxTs))
        detenerPlayback()
      } else {
        currentTimeMsRef.current = nextMs
        setPlaybackTime(new Date(nextMs))
      }
    }, 200)
  }

  const detenerPlayback = () => {
    setIsPlaying(false)
    clearInterval(intervalRef.current)
  }

  const reiniciarPlayback = () => {
    detenerPlayback()
    if (analisis?.timeline && analisis.timeline.length > 0) {
      const allTs = analisis.timeline.map(p => new Date(p.timestamp).getTime())
      const minTs = Math.min(...allTs)
      currentTimeMsRef.current = minTs
      setPlaybackTime(new Date(minTs))
    }
  }

  const cambiarVelocidad = (val) => {
    setPlaybackSpeed(val)
    speedRef.current = val
    if (isPlaying) {
      detenerPlayback()
      iniciarPlayback()
    }
  }

  const handleSliderChange = (e) => {
    if (!analisis?.timeline || analisis.timeline.length === 0) return
    const allTs = analisis.timeline.map(p => new Date(p.timestamp).getTime())
    const minTs = Math.min(...allTs)
    const maxTs = Math.max(...allTs)
    const pct = parseFloat(e.target.value) / 100
    const targetMs = minTs + pct * (maxTs - minTs)
    currentTimeMsRef.current = targetMs
    setPlaybackTime(new Date(targetMs))
  }

  // Progreso en porcentaje para el slider
  const sliderPercent = useMemo(() => {
    if (!analisis?.timeline || !currentTimeMsRef.current || analisis.timeline.length === 0) return 0
    const allTs = analisis.timeline.map(p => new Date(p.timestamp).getTime())
    const minTs = Math.min(...allTs)
    const maxTs = Math.max(...allTs)
    if (maxTs <= minTs) return 0
    return Math.min(100, Math.max(0, ((currentTimeMsRef.current - minTs) / (maxTs - minTs)) * 100))
  }, [playbackTime, analisis])

  // Datos para el gráfico de evolución de carga por hora
  const datosGraficoHora = useMemo(() => {
    if (!analisis?.trayectos) return []
    const horasMap = {}
    for (let h = 5; h <= 23; h++) {
      horasMap[h] = { hora: `${h}:00`, pasajeros: 0, trayectos: 0 }
    }

    analisis.trayectos.forEach(tr => {
      if (tr.hora_inicio) {
        const h = new Date(tr.hora_inicio).getHours()
        if (horasMap[h]) {
          horasMap[h].pasajeros += tr.total_pasajeros_levantados || 0
          horasMap[h].trayectos += 1
        }
      }
    })

    return Object.values(horasMap)
  }, [analisis])

  return (
    <>
      <Header
        titulo="Carga de Buses por Trayecto"
        subtitulo="Control cruzado: Catálogo CID (idrutaestacion) · Telemetría GPS Monitoreo · Validaciones Billetaje"
        acciones={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ 
              background: 'rgba(59, 130, 246, 0.15)', 
              color: 'var(--color-accent-blue-bright)', 
              padding: '5px 12px', 
              borderRadius: 20, 
              fontSize: '0.8rem', 
              fontWeight: 700,
              border: '1px solid rgba(59, 130, 246, 0.3)' 
            }}>
              🚌 {busesEnMomento.length} Buses en Tránsito
            </span>
          </div>
        }
      />

      <div className="page-content" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Barra Superior de Filtros y Control Cruzado */}
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, alignItems: 'flex-end' }}>
            
            {/* Selector de Ruta del Catálogo CID */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6 }}>
                <RouteIcon size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Ruta Oficial (Catálogo SisCID)
              </label>
              <select
                value={selectedRuta}
                onChange={(e) => setSelectedRuta(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 8,
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.85rem'
                }}
              >
                <option value="">Todas las Rutas Activas</option>
                {rutas.map(r => (
                  <option key={`${r.ruta_hex}-${r.ruta_dec}`} value={r.ruta_hex}>
                    [{r.ruta_dec ? `idruta: ${r.ruta_dec}` : r.ruta_hex}] {r.identificacion || r.ruta_hex} ({r.sentido ? r.sentido.toUpperCase() : 'IDA'})
                  </option>
                ))}
              </select>
            </div>

            {/* Fecha */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6 }}>
                <Calendar size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Fecha de Operación
              </label>
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 8,
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            {/* Filtro Sentido */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6 }}>
                <Filter size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                Sentido de Trayecto
              </label>
              <div style={{ display: 'flex', gap: 6 }}>
                {['todos', 'ida', 'vuelta'].map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setFiltroSentido(s)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: 6,
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                      background: filtroSentido === s ? 'var(--color-accent-blue)' : 'var(--color-bg-primary)',
                      color: filtroSentido === s ? 'white' : 'var(--color-text-secondary)',
                      border: `1px solid ${filtroSentido === s ? 'var(--color-accent-blue)' : 'var(--color-border)'}`,
                      cursor: 'pointer',
                      transition: 'all 0.15s'
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Botón de Actualizar */}
            <div>
              <button
                type="button"
                onClick={() => ejecutarAnalisis(selectedRuta)}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '10px 16px',
                  borderRadius: 8,
                  background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                  color: 'white',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  border: 'none',
                  cursor: loading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)'
                }}
              >
                {loading ? <Activity size={16} className="animate-spin" /> : <Play size={16} />}
                {loading ? 'Cruzando Datos...' : 'Actualizar Análisis'}
              </button>
            </div>
          </div>

          {/* Tarjeta de Estado del Control Cruzado (3 Bases de Datos) */}
          {analisis?.control_cruzado && (
            <div style={{ 
              marginTop: 14, 
              paddingTop: 12, 
              borderTop: '1px solid var(--color-border)', 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: 12 
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem' }}>
                <CheckCircle2 size={16} color="var(--color-success)" />
                <span><strong>1) SisCID:</strong> {analisis.control_cruzado.cid_rutas_mapeadas} rutas activas</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem' }}>
                <CheckCircle2 size={16} color="var(--color-success)" />
                <span><strong>2) Monitoreo:</strong> {analisis.control_cruzado.monitoreo_puntos_gps} pings GPS ({analisis.control_cruzado.monitoreo_buses_activos} buses)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem' }}>
                <CheckCircle2 size={16} color={analisis.modo_estimado ? 'var(--color-warning)' : 'var(--color-success)'} />
                <span><strong>3) Billetaje:</strong> {analisis.control_cruzado.total_pasajeros_levantados_global} ascensos contabilizados</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem' }}>
                <Layers size={16} color="#c084fc" />
                <span><strong>Trayectos:</strong> {analisis.control_cruzado.total_trayectos_identificados} viajes segmentados</span>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="card" style={{ border: '1px solid var(--color-danger)', background: 'rgba(239, 68, 68, 0.08)', padding: 12 }}>
            <div style={{ display: 'flex', gap: 8, color: 'var(--color-danger)', alignItems: 'center', fontSize: '0.85rem' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Barra de Reproducción Temporal (Scrubber) */}
        <div className="card" style={{ padding: '12px 20px', background: 'var(--color-bg-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            {/* Botones de reproducción */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {isPlaying ? (
                <button
                  type="button"
                  onClick={detenerPlayback}
                  style={{
                    background: 'var(--color-warning)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: 36,
                    height: 36,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer'
                  }}
                >
                  <Pause size={16} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={iniciarPlayback}
                  style={{
                    background: 'var(--color-accent-blue)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: 36,
                    height: 36,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer'
                  }}
                >
                  <Play size={16} />
                </button>
              )}
              <button
                type="button"
                onClick={reiniciarPlayback}
                title="Reiniciar reproducción"
                style={{
                  background: 'var(--color-bg-primary)',
                  color: 'var(--color-text-muted)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '50%',
                  width: 32,
                  height: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <RotateCcw size={14} />
              </button>
            </div>

            {/* Reloj y hora actual */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8, 
              background: 'var(--color-bg-primary)', 
              padding: '6px 14px', 
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              minWidth: 140
            }}>
              <Clock size={16} color="var(--color-accent-blue-bright)" />
              <span style={{ fontSize: '0.95rem', fontWeight: 800, fontFamily: 'monospace' }}>
                {playbackTime ? playbackTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '--:--:--'}
              </span>
            </div>

            {/* Slider de progreso */}
            <div style={{ flex: 1, minWidth: 200, display: 'flex', alignItems: 'center' }}>
              <input
                type="range"
                min="0"
                max="100"
                step="0.1"
                value={sliderPercent}
                onChange={handleSliderChange}
                style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--color-accent-blue)' }}
              />
            </div>

            {/* Selector de velocidad */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Vel:</span>
              {[1, 5, 15, 60].map(v => (
                <button
                  key={v}
                  type="button"
                  onClick={() => cambiarVelocidad(v)}
                  style={{
                    padding: '4px 8px',
                    borderRadius: 4,
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    background: playbackSpeed === v ? 'var(--color-accent-blue)' : 'var(--color-bg-primary)',
                    color: playbackSpeed === v ? 'white' : 'var(--color-text-secondary)',
                    border: '1px solid var(--color-border)',
                    cursor: 'pointer'
                  }}
                >
                  {v}x
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Selector de Pestañas Principales */}
        <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--color-border)', paddingBottom: 2 }}>
          <button
            type="button"
            onClick={() => setActiveTab('mapa')}
            style={{
              padding: '8px 18px',
              borderRadius: '8px 8px 0 0',
              background: activeTab === 'mapa' ? 'var(--color-bg-secondary)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'mapa' ? '3px solid var(--color-accent-blue)' : 'none',
              color: activeTab === 'mapa' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <BusIcon size={16} /> Mapa de Buses con Carga
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('trayectos')}
            style={{
              padding: '8px 18px',
              borderRadius: '8px 8px 0 0',
              background: activeTab === 'trayectos' ? 'var(--color-bg-secondary)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'trayectos' ? '3px solid var(--color-accent-blue)' : 'none',
              color: activeTab === 'trayectos' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <Layers size={16} /> Trayectos y Ascensos ({analisis?.trayectos?.length || 0})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('graficos')}
            style={{
              padding: '8px 18px',
              borderRadius: '8px 8px 0 0',
              background: activeTab === 'graficos' ? 'var(--color-bg-secondary)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'graficos' ? '3px solid var(--color-accent-blue)' : 'none',
              color: activeTab === 'graficos' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            <TrendingUp size={16} /> Curva de Demanda Horaria
          </button>
        </div>

        {/* Pestaña 1: MAPA */}
        {activeTab === 'mapa' && (
          <div style={{ position: 'relative', height: '620px', borderRadius: 12, overflow: 'hidden', border: '1px solid var(--color-border)' }}>
            <BusMap
              buses={busesEnMomento}
              height="100%"
              zoom={12}
            />

            {/* Leyenda Flotante de Ocupación */}
            <div style={{
              position: 'absolute',
              bottom: 24,
              left: 24,
              background: 'rgba(15, 23, 42, 0.92)',
              backdropFilter: 'blur(8px)',
              padding: '12px 16px',
              borderRadius: 10,
              border: '1px solid var(--color-border)',
              zIndex: 1000,
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              fontSize: '0.75rem',
              color: 'var(--color-text-primary)'
            }}>
              <div style={{ fontWeight: 800, marginBottom: 8, letterSpacing: '0.5px', textTransform: 'uppercase', fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                Carga / Pasajeros sobre el Bus
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ background: '#10b981', color: 'white', padding: '1px 6px', borderRadius: 8, fontSize: '0.7rem', fontWeight: 800 }}>1 - 15</span>
                  <span>Baja ocupación</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ background: '#3b82f6', color: 'white', padding: '1px 6px', borderRadius: 8, fontSize: '0.7rem', fontWeight: 800 }}>16 - 34</span>
                  <span>Media ocupación</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ background: '#f59e0b', color: 'white', padding: '1px 6px', borderRadius: 8, fontSize: '0.7rem', fontWeight: 800 }}>35 - 49</span>
                  <span>Alta ocupación</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ background: '#ef4444', color: 'white', padding: '1px 6px', borderRadius: 8, fontSize: '0.7rem', fontWeight: 800 }}>50+</span>
                  <span>Cerca de capacidad / Sobrecarga</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pestaña 2: TRAYECTOS DETECTADOS */}
        {activeTab === 'trayectos' && (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0 }}>Historial de Trayectos Segmentados</h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                  Detecta cuándo el bus inició un trayecto y pasó a otro según <code style={{ color: 'var(--color-accent-blue-bright)' }}>idrutaestacion</code> y cabeceras.
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                Mostrando {analisis?.trayectos?.length || 0} trayectos
              </div>
            </div>

            <div style={{ overflowX: 'auto', maxHeight: '550px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                <thead style={{ background: 'var(--color-bg-primary)', position: 'sticky', top: 0, zIndex: 10 }}>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
                    <th style={{ padding: '10px 14px' }}>ID Trayecto</th>
                    <th style={{ padding: '10px 14px' }}>Móvil (Bus)</th>
                    <th style={{ padding: '10px 14px' }}>idrutaestacion</th>
                    <th style={{ padding: '10px 14px' }}>Ruta CID</th>
                    <th style={{ padding: '10px 14px' }}>Sentido</th>
                    <th style={{ padding: '10px 14px' }}>Cabeceras</th>
                    <th style={{ padding: '10px 14px' }}>Inicio ➔ Fin</th>
                    <th style={{ padding: '10px 14px' }}>Duración</th>
                    <th style={{ padding: '10px 14px', textAlign: 'right' }}>Pasajeros Levantados</th>
                  </tr>
                </thead>
                <tbody>
                  {analisis?.trayectos?.map((tr, idx) => (
                    <tr 
                      key={tr.id_trayecto || idx} 
                      style={{ 
                        borderBottom: '1px solid var(--color-border)',
                        background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' 
                      }}
                    >
                      <td style={{ padding: '10px 14px', fontWeight: 700, color: '#c084fc' }}>
                        {tr.id_trayecto}
                      </td>
                      <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                        🚌 {tr.id_bus}
                      </td>
                      <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontWeight: 700, color: 'var(--color-accent-blue-bright)' }}>
                        {tr.idrutaestacion}
                      </td>
                      <td style={{ padding: '10px 14px', maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {tr.nombre_ruta}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span style={{ 
                          padding: '2px 8px', 
                          borderRadius: 4, 
                          fontSize: '0.7rem', 
                          fontWeight: 700,
                          background: tr.sentido?.toLowerCase() === 'ida' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(168, 85, 247, 0.15)',
                          color: tr.sentido?.toLowerCase() === 'ida' ? '#60a5fa' : '#c084fc'
                        }}>
                          {tr.sentido ? tr.sentido.toUpperCase() : 'IDA'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--color-text-secondary)' }}>
                        {tr.origen} ➔ {tr.destino}
                      </td>
                      <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                        {new Date(tr.hora_inicio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ➔ {new Date(tr.hora_fin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--color-text-muted)' }}>
                        {tr.duracion_min} min
                      </td>
                      <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                        <span style={{ 
                          background: tr.total_pasajeros_levantados >= 40 ? '#ef4444' : tr.total_pasajeros_levantados >= 20 ? '#3b82f6' : '#10b981', 
                          color: 'white', 
                          padding: '3px 10px', 
                          borderRadius: 12, 
                          fontWeight: 800,
                          fontSize: '0.8rem' 
                        }}>
                          {tr.total_pasajeros_levantados} pax
                        </span>
                      </td>
                    </tr>
                  ))}
                  {(!analisis?.trayectos || analisis.trayectos.length === 0) && (
                    <tr>
                      <td colSpan={9} style={{ padding: 32, textAlign: 'center', color: 'var(--color-text-muted)' }}>
                        No se detectaron trayectos con los filtros seleccionados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Pestaña 3: GRÁFICOS DE DEMANDA */}
        {activeTab === 'graficos' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
            <div className="card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <TrendingUp size={16} color="var(--color-accent-blue)" /> Ascensos de Pasajeros por Hora
              </h3>
              <div style={{ height: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={datosGraficoHora}>
                    <defs>
                      <linearGradient id="paxGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="hora" stroke="var(--color-text-muted)" fontSize={11} />
                    <YAxis stroke="var(--color-text-muted)" fontSize={11} />
                    <RechartsTooltip 
                      contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: 8 }}
                      labelStyle={{ color: 'var(--color-text-primary)', fontWeight: 700 }}
                    />
                    <Area type="monotone" dataKey="pasajeros" name="Pasajeros Levantados" stroke="#3b82f6" fillOpacity={1} fill="url(#paxGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Layers size={16} color="#c084fc" /> Frecuencia de Trayectos Despachados
              </h3>
              <div style={{ height: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={datosGraficoHora}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="hora" stroke="var(--color-text-muted)" fontSize={11} />
                    <YAxis stroke="var(--color-text-muted)" fontSize={11} />
                    <RechartsTooltip 
                      contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: 8 }}
                      labelStyle={{ color: 'var(--color-text-primary)', fontWeight: 700 }}
                    />
                    <Bar dataKey="trayectos" name="Trayectos Activos" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
