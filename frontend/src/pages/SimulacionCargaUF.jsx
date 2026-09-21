import React, { useState, useEffect, useRef, useMemo } from 'react'
import Header from '../components/Layout/Header'
import { ufApi } from '../services/api'
import { 
  Play, 
  Calendar, 
  Map as MapIcon, 
  BarChart as BarChartIcon, 
  Truck, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Users,
  Eye,
  Settings2,
  FastForward,
  RotateCcw,
  Download,
  ChevronDown,
  ChevronUp,
  Info,
  Activity,
  History
} from 'lucide-react'
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { MAP_TILE_CONFIG } from '../config/map'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  Legend as RechartsLegend 
} from 'recharts'

// --- Estilos Reutilizables ---
const STYLES = {
  label: { display: 'block', fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 6 },
  input: { width: '100%', padding: '10px', borderRadius: '8px', background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' },
  cardMetric: { padding: '16px', display: 'flex', flexDirection: 'column', gap: 4 },
  metricValue: { fontSize: '1.5rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: 8 },
  tabButton: (active) => ({
    padding: '8px 16px',
    borderRadius: '8px 8px 0 0',
    background: active ? 'var(--color-bg-secondary)' : 'transparent',
    border: 'none',
    borderBottom: active ? '2px solid var(--color-accent-blue)' : 'none',
    color: active ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.2s'
  })
}

// Fix Leaflet icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// --- Componentes Auxiliares ---

function BoundsUpdater({ data }) {
  const map = useMap()
  useEffect(() => {
    if (!data) return
    const features = []
    if (data.troncales) data.troncales.forEach(t => { if(t.geojson) try { features.push(JSON.parse(t.geojson)) } catch(e){} })
    if (data.geocercas) data.geocercas.forEach(g => { if(g.geojson) try { features.push(JSON.parse(g.geojson)) } catch(e){} })
    
    if (features.length > 0) {
      const group = L.featureGroup(features.map(f => L.geoJSON(f)))
      map.fitBounds(group.getBounds(), { padding: [50, 50] })
    }
  }, [data, map])
  return null
}

const MetricCard = ({ label, value, icon: Icon, iconColor }) => (
  <div className="card" style={STYLES.cardMetric}>
    <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{label}</div>
    <div style={STYLES.metricValue}>
      <Icon size={20} color={iconColor} />
      {value}
    </div>
  </div>
)

export default function SimulacionCargaUF() {
  const [ufs, setUfs] = useState([])
  const [selectedUf, setSelectedUf] = useState('')
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [referencias, setReferencias] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('resumen')
  
  // Parámetros Avanzados
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [horaInicio, setHoraInicio] = useState(0)
  const [horaFin, setHoraFin] = useState(24)
  const [bufTroncal, setBufTroncal] = useState(90)
  const [sepEntrada, setSepEntrada] = useState(45)
  const [ventanaVal, setVentanaVal] = useState(60)

  // Estados para Playback
  const [playbackActive, setPlaybackActive] = useState(false)
  const [playbackTime, setPlaybackTime] = useState(null)
  const [playbackSpeed, setPlaybackSpeed] = useState(60)
  const [busesEnMapa, setBusesEnMapa] = useState([])
  const playbackIntervalRef = useRef(null)
  
  // Refs para que el interval siempre lea valores actualizados (evita closures)
  const playbackSpeedRef = useRef(60)
  const currentTimeRef = useRef(null)
  const workerRef = useRef(null)

  // Inicializar Worker
  useEffect(() => {
    workerRef.current = new Worker(new URL('../workers/playbackWorker.js', import.meta.url))
    
    workerRef.current.onmessage = (e) => {
      const { type, payload } = e.data
      if (type === 'POSITIONS_UPDATE') {
        setBusesEnMapa(payload.buses)
        setPlaybackTime(new Date(payload.currentTimeMs))
      }
    }

    return () => {
      if (workerRef.current) workerRef.current.terminate()
      if (playbackIntervalRef.current) clearInterval(playbackIntervalRef.current)
    }
  }, [])

  useEffect(() => {
    ufApi.listar().then(res => setUfs(res.data)).catch(err => console.error(err))
  }, [])


  useEffect(() => {
    if (selectedUf) {
      setReferencias(null)
      stopPlayback()
      setResultado(null)
      ufApi.obtenerReferenciasGeograficas(selectedUf)
        .then(res => setReferencias(res.data))
        .catch(err => console.error("Error cargando referencias:", err))
    } else {
      setReferencias(null)
    }
  }, [selectedUf])

  const stopPlayback = () => {
    if (playbackIntervalRef.current) {
      clearInterval(playbackIntervalRef.current)
      playbackIntervalRef.current = null
    }
    setPlaybackActive(false)
  }

  const startPlayback = () => {
    if (!resultado?.history?.length) return
    if (!workerRef.current) return

    // Inicializar historial y eventos en el worker
    workerRef.current.postMessage({ 
      type: 'INIT', 
      payload: { 
        history: resultado.history,
        eventos: resultado.eventos 
      } 
    })

    const history = resultado.history
    const timestamps = history.map(h => new Date(h.timestamp).getTime())
    const startMs = currentTimeRef.current || timestamps[0]
    const endMs = timestamps.reduce((max, ts) => Math.max(max, ts), timestamps[0])
    
    currentTimeRef.current = startMs
    setPlaybackActive(true)

    playbackIntervalRef.current = setInterval(() => {
      // 100ms interval (10fps). 
      // Si speed es 60, avanzamos 6000ms (6s) cada 100ms de tiempo real.
      const advance = 100 * playbackSpeedRef.current
      const next = currentTimeRef.current + advance
      currentTimeRef.current = next

      workerRef.current.postMessage({ 
        type: 'TICK', 
        payload: { nextMs: next } 
      })

      if (next >= endMs) stopPlayback()
    }, 100)
  }

  const togglePlayback = () => {
    if (playbackActive) stopPlayback()
    else startPlayback()
  }

  const resetPlayback = () => {
    stopPlayback()
    currentTimeRef.current = null
    setPlaybackTime(null)
    setBusesEnMapa([])
  }

  // Sincronizar playbackSpeedRef cuando el estado cambia
  const handleSpeedChange = (val) => {
    playbackSpeedRef.current = val
    setPlaybackSpeed(val)
    // Si está reproduciendo, reiniciar el interval con la nueva velocidad
    if (playbackActive) {
      clearInterval(playbackIntervalRef.current)
      
      const history = resultado.history
      const timestamps = history.map(h => new Date(h.timestamp).getTime())
      const endMs = timestamps.reduce((max, ts) => Math.max(max, ts), timestamps[0])

      playbackIntervalRef.current = setInterval(() => {
        const advance = 100 * playbackSpeedRef.current
        const next = currentTimeRef.current + advance
        currentTimeRef.current = next

        workerRef.current.postMessage({ 
          type: 'TICK', 
          payload: { nextMs: next } 
        })

        if (next >= endMs) stopPlayback()
      }, 100)
    }
  }

  const handleSimular = async () => {
    if (!selectedUf) return
    setLoading(true)
    setError(null)
    setResultado(null)
    try {
      const params = {
        hora_inicio: horaInicio,
        hora_fin: horaFin,
        buf_troncal_m: bufTroncal,
        sep_entrada_min: sepEntrada,
        ventana_val_min: ventanaVal
      }
      const res = await ufApi.simularCarga(selectedUf, fecha, params)
      setResultado(res.data)
      resetPlayback()
    } catch (err) {
      setError(err.response?.data?.detail || "Error al ejecutar la simulación")
    } finally {
      setLoading(false)
    }
  }

  const exportarCSV = (tipo) => {
    if (!resultado) return
    let data = []
    let filename = ""
    
    if (tipo === 'eventos') {
      data = resultado.eventos || []
      filename = `eventos_uf_${selectedUf}_${fecha}.csv`
    } else {
      data = resultado.metrics || []
      filename = `metricas_uf_${selectedUf}_${fecha}.csv`
    }
    
    if (data.length === 0) return
    
    const headers = Object.keys(data[0]).join(',')
    const rows = data.map(obj => Object.values(obj).join(','))
    const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + rows.join("\n")
    
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const parseGeojson = (str) => {
    try { return JSON.parse(str) } catch (e) { return null }
  }

  return (
    <>
      <Header 
        titulo="Simular Carga de UF" 
        subtitulo="Análisis detallado de ocupación y validaciones SNBE"
      />
      
      <div className="page-content">
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20, height: 'calc(100vh - 160px)' }}>
          
          {/* Panel de Control Izquierdo */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', paddingRight: 4 }}>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Play size={18} color="var(--color-accent-blue)" /> Parámetros
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={STYLES.label}>Unidad Funcional</label>
                  <select 
                    value={selectedUf} 
                    onChange={(e) => setSelectedUf(e.target.value)}
                    style={STYLES.input}
                  >
                    <option value="">Seleccione una UF...</option>
                    {ufs.map(uf => (
                      <option key={uf.id_uf} value={uf.id_uf}>{uf.uf_nombre || `UF ${uf.id_uf}`}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={STYLES.label}>Fecha de Análisis</label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="date" 
                      value={fecha} 
                      onChange={(e) => setFecha(e.target.value)}
                      style={{ ...STYLES.input, paddingLeft: '35px' }}
                    />
                    <Calendar size={16} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
                  </div>
                </div>

                {/* Parámetros Avanzados */}
                <div style={{ border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden' }}>
                  <button 
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    style={{ width: '100%', padding: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg-secondary)', border: 'none', color: 'var(--color-text-primary)', cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', fontWeight: 600 }}>
                      <Settings2 size={16} /> Configuración Avanzada
                    </div>
                    {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  
                  {showAdvanced && (
                    <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--color-bg-primary)' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        <div>
                          <label style={{ ...STYLES.label, fontSize: '0.7rem' }}>Hora Inicio</label>
                          <input type="number" min="0" max="23" value={horaInicio} onChange={e => setHoraInicio(parseInt(e.target.value))} style={STYLES.input} />
                        </div>
                        <div>
                          <label style={{ ...STYLES.label, fontSize: '0.7rem' }}>Hora Fin</label>
                          <input type="number" min="1" max="24" value={horaFin} onChange={e => setHoraFin(parseInt(e.target.value))} style={STYLES.input} />
                        </div>
                      </div>
                      <div>
                        <label style={{ ...STYLES.label, fontSize: '0.7rem' }}>Buffer Troncal (m): {bufTroncal}</label>
                        <input type="range" min="30" max="250" value={bufTroncal} onChange={e => setBufTroncal(parseInt(e.target.value))} style={{ width: '100%' }} />
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        <div>
                          <label style={{ ...STYLES.label, fontSize: '0.7rem' }}>Sep. Ingreso (min)</label>
                          <input type="number" min="5" max="180" value={sepEntrada} onChange={e => setSepEntrada(parseInt(e.target.value))} style={STYLES.input} />
                        </div>
                        <div>
                          <label style={{ ...STYLES.label, fontSize: '0.7rem' }}>Ventana Val. (min)</label>
                          <input type="number" min="5" max="180" value={ventanaVal} onChange={e => setVentanaVal(parseInt(e.target.value))} style={STYLES.input} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <button 
                  className="btn btn-primary" 
                  onClick={handleSimular} 
                  disabled={loading || !selectedUf}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, height: '42px' }}
                >
                  {loading ? 'Simulando...' : <><Play size={16} /> Ejecutar Análisis</>}
                </button>

                {resultado && (
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button 
                      className="btn" 
                      onClick={togglePlayback}
                      style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: playbackActive ? 'var(--color-danger)' : 'var(--color-success)', color: 'white', border: 'none' }}
                    >
                      {playbackActive ? <><Clock size={14} /> Pausar</> : <><Eye size={14} /> Reproducir</>}
                    </button>
                    <button className="btn btn-secondary" onClick={resetPlayback} style={{ width: '42px', padding: 0 }} title="Reiniciar"><RotateCcw size={16} /></button>
                    <button className="btn btn-secondary" onClick={() => exportarCSV('metricas')} style={{ width: '42px', padding: 0 }} title="Exportar CSV"><Download size={16} /></button>
                  </div>
                )}
              </div>
            </div>

            {playbackActive && (
              <div className="card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid var(--color-accent-blue)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'monospace' }}>
                    {playbackTime?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600 }}>Vel: {playbackSpeed}x</span>
                </div>
                <input type="range" min="1" max="300" value={playbackSpeed} onChange={e => handleSpeedChange(parseInt(e.target.value))} style={{ width: '100%' }} />
              </div>
            )}

            {error && (
              <div className="card" style={{ border: '1px solid var(--color-danger)', background: 'rgba(244, 63, 94, 0.05)' }}>
                <div style={{ display: 'flex', gap: 10, color: 'var(--color-danger)' }}>
                  <AlertCircle size={20} />
                  <div style={{ fontSize: '0.8rem' }}>{error}</div>
                </div>
              </div>
            )}

            {/* Diagnóstico SNBE Quick View */}
            {resultado?.snbe_diag && (
              <div className="card" style={{ padding: '12px', background: resultado.snbe_diag.total_validaciones > 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(245, 158, 11, 0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', fontWeight: 700, marginBottom: 8 }}>
                  <Info size={14} /> Diagnóstico de Datos
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div style={{ fontSize: '0.7rem' }}>Buses GPS: <strong>{resultado.snbe_diag.buses_gps_distintos}</strong></div>
                  <div style={{ fontSize: '0.7rem' }}>Validaciones: <strong>{resultado.snbe_diag.total_validaciones}</strong></div>
                </div>
              </div>
            )}

            {/* Lista de Métricas por Franja */}
            {resultado && activeTab === 'resumen' && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {resultado.metrics.map((m, i) => (
                  <div key={i} className="card" style={{ 
                    padding: '12px', 
                    borderLeft: `4px solid ${m.es_principal ? 'var(--color-accent-blue)' : '#94a3b8'}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{m.troncal}</span>
                      <span style={{ fontSize: '0.7rem', background: 'var(--color-bg-secondary)', padding: '2px 6px', borderRadius: '4px' }}>{m.franja}</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                      <div>
                        <div style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>Buses GPS</div>
                        <div style={{ fontWeight: 700 }}>{m.cantidad_buses}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>Bill. Hora</div>
                        <div style={{ fontWeight: 700, color: 'var(--color-accent-blue)' }}>{m.buses_billetaje}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>Ocup. Media</div>
                        <div style={{ fontWeight: 800, color: 'var(--color-success)' }}>{Math.round(m.promedio_ocupacion)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Área Principal Derecha */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Mapa */}
            <div className="card" style={{ flex: 1, padding: 0, overflow: 'hidden', position: 'relative', minHeight: '400px' }}>
              <MapContainer 
                center={[-25.3, -57.6]} 
                zoom={12} 
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url={MAP_TILE_CONFIG.url}
                  attribution={MAP_TILE_CONFIG.attribution}
                  maxZoom={MAP_TILE_CONFIG.maxZoom}
                />
                
                {/* Geocercas y Troncales */}
                {referencias?.geocercas?.map((g, i) => (
                  <GeoJSON 
                    key={`geocerca-${g.id_geocerca}-${i}`}
                    data={parseGeojson(g.geojson)}
                    style={{
                      fillColor: g.id_tipo === 1 ? '#10b981' : g.id_tipo === 3 ? '#8b5cf6' : '#3b82f6',
                      fillOpacity: g.id_tipo === 3 ? 0.05 : 0.2,
                      color: g.id_tipo === 1 ? '#10b981' : g.id_tipo === 3 ? '#8b5cf6' : '#3b82f6',
                      weight: 1,
                      dashArray: '5, 5'
                    }}
                  >
                    <Popup>
                      <strong>{g.tipo_nombre}</strong><br/>
                      Ruta: {g.ruta_hex}
                    </Popup>
                  </GeoJSON>
                ))}

                {referencias?.troncales?.map(t => (
                  <GeoJSON 
                    key={`troncal-${t.id_troncal}`} 
                    data={parseGeojson(t.geojson)} 
                    style={{ 
                      color: t.es_principal ? '#3b82f6' : '#94a3b8', 
                      weight: t.es_principal ? 4 : 2,
                      opacity: 0.9
                    }} 
                  />
                ))}

                {/* Buses en Playback */}
                {playbackActive && busesEnMapa.map(bus => {
                  const numIngresos = bus.numIngresos || 0
                  return (
                    <Marker 
                      key={`bus-${bus.id_bus}`}
                      position={[bus.lat, bus.lon]}
                      icon={L.divIcon({
                        html: `
                          <div style="
                            background: var(--color-accent-blue); 
                            width: 18px; 
                            height: 18px; 
                            border: 2px solid white; 
                            border-radius: 4px; 
                            box-shadow: 0 0 10px #3b82f6;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 10px;
                            font-weight: bold;
                          ">
                            ${numIngresos}
                          </div>
                        `,
                        className: '',
                        iconSize: [18, 18],
                        iconAnchor: [9, 9]
                      })}
                    >
                      <Popup>
                        <div style={{ fontSize: '0.8rem' }}>
                          <strong>Bus: {bus.id_bus}</strong><br/>
                          Ruta: {bus.ruta_hex}<br/>
                          Ingresos hasta ahora: <span style={{ color: 'var(--color-accent-blue)', fontWeight: 700 }}>{numIngresos}</span><br/>
                          Hora GPS: {new Date(bus.timestamp).toLocaleTimeString()}
                        </div>
                      </Popup>
                    </Marker>
                  )
                })}

                <BoundsUpdater data={referencias} />
              </MapContainer>
              
              <div style={{ 
                position: 'absolute', bottom: 20, left: 20, background: 'var(--color-bg-secondary)', padding: '10px', borderRadius: '8px', zIndex: 1000, boxShadow: '0 4px 12px rgba(0,0,0,0.5)', fontSize: '0.7rem'
              }}>
                <div style={{ fontWeight: 700, marginBottom: 5 }}>LEYENDA</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 12, height: 2, background: '#3b82f6' }}></div> Troncal P.</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 12, height: 2, background: '#94a3b8' }}></div> Troncal S.</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 12, height: 8, background: 'rgba(16, 185, 129, 0.2)', border: '1px dashed #10b981' }}></div> Inicio</div>
              </div>
            </div>

            {/* Tabs de Resultados */}
            <div style={{ display: 'flex', flexDirection: 'column', height: '300px' }}>
              <div style={{ display: 'flex', gap: 4, padding: '0 10px' }}>
                <button onClick={() => setActiveTab('resumen')} style={STYLES.tabButton(activeTab === 'resumen')}><Activity size={14} /> Resumen</button>
                <button onClick={() => setActiveTab('graficos')} style={STYLES.tabButton(activeTab === 'graficos')}><BarChartIcon size={14} /> Gráficos</button>
                <button onClick={() => setActiveTab('eventos')} style={STYLES.tabButton(activeTab === 'eventos')}><History size={14} /> Eventos</button>
                <button onClick={() => setActiveTab('snbe')} style={STYLES.tabButton(activeTab === 'snbe')}><Users size={14} /> Diagnóstico</button>
              </div>
              
              <div className="card" style={{ flex: 1, borderTopLeftRadius: 0, overflow: 'auto' }}>
                {activeTab === 'resumen' && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                    <MetricCard 
                      label="Buses Detectados" 
                      value={resultado ? resultado.snbe_diag.buses_con_ingreso : '---'} 
                      icon={Truck} 
                      iconColor="var(--color-accent-blue)" 
                    />
                    <MetricCard 
                      label="Validaciones Totales" 
                      value={resultado ? resultado.snbe_diag.total_validaciones : '---'} 
                      icon={Users} 
                      iconColor="#10b981" 
                    />
                    <MetricCard 
                      label="Promedio Ocupación" 
                      value={resultado ? Math.round(resultado.metrics.reduce((acc, m) => acc + m.promedio_ocupacion, 0) / (resultado.metrics.length || 1)) : '---'} 
                      icon={BarChartIcon} 
                      iconColor="#f59e0b" 
                    />
                    <MetricCard 
                      label="Estado Análisis" 
                      value={loading ? "Procesando" : resultado ? "Completado" : "Pendiente"} 
                      icon={CheckCircle2} 
                      iconColor={resultado ? "var(--color-success)" : "var(--color-text-muted)"} 
                    />
                  </div>
                )}

                {activeTab === 'graficos' && resultado && (
                  <div style={{ height: '220px', width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={resultado.por_hora}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="hora" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <RechartsTooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                        <RechartsLegend />
                        <Bar name="Ingresos" dataKey="n_ingresos" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar name="Validaciones" dataKey="n_validaciones" fill="#10b981" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {activeTab === 'eventos' && resultado && (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead style={{ position: 'sticky', top: 0, background: 'var(--color-bg-secondary)' }}>
                      <tr>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Bus</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Ruta</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Troncal</th>
                        <th style={{ textAlign: 'left', padding: '8px' }}>Hora</th>
                        <th style={{ textAlign: 'right', padding: '8px' }}>Val.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resultado.eventos.map((ev, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '8px' }}>{ev.id_bus}</td>
                          <td style={{ padding: '8px' }}>{ev.ruta_hex}</td>
                          <td style={{ padding: '8px' }}>{ev.nombre_troncal}</td>
                          <td style={{ padding: '8px' }}>{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                          <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700 }}>{ev.validaciones}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {activeTab === 'snbe' && resultado && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 20 }}>
                      <div>
                        <h4 style={{ fontSize: '0.9rem', marginBottom: 10 }}>Resumen de Billetaje</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.8rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Validaciones totales detectadas:</span> <strong>{resultado.snbe_diag.total_validaciones}</strong></div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Buses sin ninguna validación:</span> <strong style={{ color: 'var(--color-danger)' }}>{resultado.snbe_diag.buses_sin_validaciones}</strong></div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Rutas decimales mapeadas:</span> <strong>{resultado.snbe_diag.rutas_dec_usadas.join(', ')}</strong></div>
                        </div>
                      </div>
                      <div style={{ background: 'rgba(59, 130, 246, 0.05)', padding: '12px', borderRadius: '8px' }}>
                        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', lineHeight: '1.4' }}>
                          <Info size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                          Si el número de validaciones es 0 o muy bajo, verifique que los identificadores de bus (idsam) coincidan entre el sistema de GPS y Billetaje, y que las rutas decimales en el catálogo sean correctas.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {!resultado && !loading && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-muted)' }}>
                    <BarChartIcon size={48} opacity={0.2} />
                    <p>Ejecute una simulación para ver métricas detalladas</p>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  )
}
