import React, { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import Header from '../components/Layout/Header'
import { traficoApi } from '../services/api'
import {
  Shuffle, ArrowLeftRight, Ban, Bus, AlertTriangle, CheckCircle2,
  TrendingDown, TrendingUp, Clock, RotateCcw, Play, MapPin,
  ChevronRight, Car, Flame, ShieldAlert, Sparkles, Layers, RefreshCw
} from 'lucide-react'

// Componente para re-centrar el mapa dinámicamente
function MapRecenter({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1.2 })
    }
  }, [center, zoom, map])
  return null
}

// Icono personalizado para Waze en el mapa
const crearIconoWaze = (tipo) => {
  let emoji = '🚗'
  let bg = '#f59e0b'
  if (tipo === 'ACCIDENT') { emoji = '🚨'; bg = '#ef4444' }
  if (tipo === 'ROAD_CLOSED') { emoji = '🚧'; bg = '#6366f1' }
  if (tipo === 'HAZARD') { emoji = '⚠️'; bg = '#eab308' }
  
  return L.divIcon({
    html: `<div style="
      background: ${bg};
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      border: 2px solid white;
      box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    ">${emoji}</div>`,
    className: '',
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  })
}

// Colores según nivel de servicio (LOS)
const getColorLOS = (los, cerrado = false) => {
  if (cerrado) return '#475569'
  if (los === 'A/B') return '#10b981' // Verde fluido
  if (los === 'C') return '#f59e0b'   // Amarillo moderado
  if (los === 'D/E') return '#f97316' // Naranja congestionado
  return '#ef4444'                   // Rojo colapso
}

export default function TraficoWhatIfPage() {
  // Estados de control
  const [municipios, setMunicipios] = useState([])
  const [municipioSel, setMunicipioSel] = useState('Asunción')
  const [franjaHoraria, setFranjaHoraria] = useState('PICO_MANANA')
  const [showWaze, setShowWaze] = useState(true)
  const [showWazeLiveMap, setShowWazeLiveMap] = useState(false)
  const [showBuses, setShowBuses] = useState(true)
  
  // Datos de la red
  const [tramosBase, setTramosBase] = useState([])
  const [cargandoRed, setCargandoRed] = useState(false)
  const [wazeData, setWazeData] = useState({ alerts: [], jams: [] })
  
  // Modificaciones What-If (id_tramo -> { nuevo_sentido, carril_bus_exclusivo, motivo })
  const [modificaciones, setModificaciones] = useState({})
  
  // Resultados de la simulación
  const [simulando, setSimulando] = useState(false)
  const [resultadoSim, setResultadoSim] = useState(null)
  const [tramoSeleccionado, setTramoSeleccionado] = useState(null)
  const [tabActiva, setTabActiva] = useState('diagnostico') // 'diagnostico' | 'colapso' | 'tp' | 'reporte'

  // Centros por municipio
  const centrosMunicipios = {
    'Asunción': { center: [-25.2867, -57.6350], zoom: 13 },
    'Fernando de la Mora': { center: [-25.3330, -57.5350], zoom: 13 },
    'San Lorenzo': { center: [-25.3420, -57.5050], zoom: 14 },
    'Luque': { center: [-25.2650, -57.5150], zoom: 13 },
    'Lambaré': { center: [-25.3400, -57.6150], zoom: 13 },
    'Todos': { center: [-25.3000, -57.5600], zoom: 12 }
  }

  // Cargar lista de municipios
  useEffect(() => {
    traficoApi.municipios()
      .then(res => setMunicipios(res.data))
      .catch(err => console.error('Error cargando municipios:', err))
  }, [])

  // Cargar red vial y datos Waze
  const cargarDatos = async () => {
    setCargandoRed(true)
    try {
      const [resRed, resWaze] = await Promise.all([
        traficoApi.redVial(municipioSel === 'Todos' ? null : municipioSel, franjaHoraria),
        traficoApi.wazeLive(municipioSel === 'Todos' ? null : municipioSel)
      ])
      setTramosBase(resRed.data.tramos || [])
      setWazeData(resWaze.data)
      setResultadoSim(null) // Reset al cambiar contexto
    } catch (e) {
      console.error('Error al cargar datos viales:', e)
    } finally {
      setCargandoRed(false)
    }
  }

  useEffect(() => {
    cargarDatos()
  }, [municipioSel, franjaHoraria])

  // Aplicar modificación sobre un tramo
  const aplicarModificacion = (idTramo, nuevoSentido, carrilBus = false) => {
    setModificaciones(prev => {
      const next = { ...prev }
      if (nuevoSentido === 'ORIGINAL') {
        delete next[idTramo]
      } else {
        next[idTramo] = {
          id_tramo: idTramo,
          nuevo_sentido: nuevoSentido,
          carril_bus_exclusivo: carrilBus,
          motivo: 'Evaluación What-If Municipalidad'
        }
      }
      return next
    })
  }

  // Restablecer todas las intervenciones
  const restablecerRed = () => {
    setModificaciones({})
    setResultadoSim(null)
    cargarDatos()
  }

  // Ejecutar simulación What-If
  const ejecutarSimulacion = async () => {
    setSimulando(true)
    try {
      const payload = {
        municipio: municipioSel,
        franja_horaria: franjaHoraria,
        modificaciones: Object.values(modificaciones)
      }
      const res = await traficoApi.simularWhatIf(payload)
      setResultadoSim(res.data)
      setTabActiva('diagnostico')
    } catch (e) {
      console.error('Error al simular tráfico:', e)
    } finally {
      setSimulando(false)
    }
  }

  // Mapa de tramos renderizables combinando base y simulación
  const tramosAMostrar = useMemo(() => {
    if (resultadoSim && resultadoSim.tramos) {
      return resultadoSim.tramos
    }
    return tramosBase.map(t => ({
      id_tramo: t.id_tramo,
      nombre_calle: t.nombre_calle,
      municipio: t.municipio,
      sentido_anterior: t.sentido,
      sentido_nuevo: modificaciones[t.id_tramo]?.nuevo_sentido || t.sentido,
      velocidad_efectiva_anterior_kmh: t.velocidad_efectiva_kmh,
      velocidad_efectiva_nueva_kmh: t.velocidad_efectiva_kmh,
      tiempo_recorrido_anterior_min: t.tiempo_recorrido_min,
      tiempo_recorrido_nuevo_min: t.tiempo_recorrido_min,
      nivel_servicio_anterior: t.nivel_servicio,
      nivel_servicio_nuevo: t.nivel_servicio,
      ratio_saturacion: t.ratio_saturacion,
      lineas_afectadas: t.lineas_colectivo || [],
      coordenadas: t.coordenadas || [],
      flujo_anterior_veh_h: t.flujo_actual_veh_hora,
      flujo_nuevo_veh_h: t.flujo_actual_veh_hora,
      capacidad_veh_h: t.capacidad_veh_hora
    }))
  }, [tramosBase, resultadoSim, modificaciones])

  const centerConfig = centrosMunicipios[municipioSel] || centrosMunicipios['Asunción']
  const totalModificados = Object.keys(modificaciones).length

  return (
    <>
      <Header
        titulo="Simulador Integral de Tránsito (SIGT)"
        subtitulo="Asunción y Gran Asunción — Escenarios What-If y Calibración Waze for Cities"
      />

      <div className="page-content" style={{ padding: 0, height: 'calc(100vh - var(--header-height))', display: 'flex', flexDirection: 'column' }}>
        
        {/* BARRA DE CONTROL SUPERIOR */}
        <div style={{
          background: 'var(--color-bg-secondary)',
          borderBottom: '1px solid var(--color-border)',
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          zIndex: 10
        }}>
          {/* Selector de Municipio */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <MapPin size={18} style={{ color: 'var(--color-accent-blue)' }} />
            <select
              value={municipioSel}
              onChange={(e) => setMunicipioSel(e.target.value)}
              className="select"
              style={{
                background: 'var(--color-bg-input)',
                color: 'var(--color-text-primary)',
                borderColor: 'var(--color-border)',
                fontWeight: 600,
                fontSize: '0.85rem'
              }}
            >
              <option value="Asunción">🏛️ Asunción (Capital)</option>
              <option value="Fernando de la Mora">🏙️ Fernando de la Mora</option>
              <option value="San Lorenzo">🌳 San Lorenzo</option>
              <option value="Luque">✈️ Luque</option>
              <option value="Lambaré">🌊 Lambaré</option>
              <option value="Todos">🌐 Gran Asunción (Área Metropolitana)</option>
            </select>

            {/* Franja Horaria */}
            <select
              value={franjaHoraria}
              onChange={(e) => setFranjaHoraria(e.target.value)}
              className="select"
              style={{
                background: 'var(--color-bg-input)',
                color: 'var(--color-text-primary)',
                borderColor: 'var(--color-border)',
                fontSize: '0.85rem'
              }}
            >
              <option value="PICO_MANANA">☀️ Hora Pico Mañana (07:00 - 08:30)</option>
              <option value="VALLE">🌤️ Hora Valle (11:00 - 14:00)</option>
              <option value="PICO_TARDE">🌆 Hora Pico Tarde (17:30 - 19:30)</option>
            </select>
          </div>

          {/* Capas Waze y Buses */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => setShowWaze(!showWaze)}
              className={`btn btn-sm ${showWaze ? 'btn-warning' : 'btn-outline'}`}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <Flame size={15} />
              <span>Waze Feed ({wazeData.alerts?.length || 0})</span>
            </button>

            <button
              onClick={() => setShowWazeLiveMap(!showWazeLiveMap)}
              className={`btn btn-sm ${showWazeLiveMap ? 'btn-info' : 'btn-outline'}`}
              style={{ display: 'flex', alignItems: 'center', gap: 6, borderColor: 'rgba(6,182,212,0.4)' }}
              title="Abrir mapa oficial en vivo de Waze"
            >
              <Layers size={15} />
              <span>{showWazeLiveMap ? 'Cerrar Waze Live' : 'Waze Live Map'}</span>
            </button>

            <button
              onClick={() => setShowBuses(!showBuses)}
              className={`btn btn-sm ${showBuses ? 'btn-info' : 'btn-outline'}`}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <Bus size={15} />
              <span>Líneas TP</span>
            </button>

            {totalModificados > 0 && (
              <button
                onClick={restablecerRed}
                className="btn btn-sm btn-outline"
                style={{ color: 'var(--color-accent-rose)', borderColor: 'rgba(244,63,94,0.4)', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <RotateCcw size={15} />
                <span>Restablecer ({totalModificados})</span>
              </button>
            )}

            {/* BOTÓN EJECUTAR SIMULACIÓN */}
            <button
              onClick={ejecutarSimulacion}
              disabled={simulando}
              className="btn btn-sm btn-primary"
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                boxShadow: '0 0 15px rgba(59,130,246,0.3)'
              }}
            >
              {simulando ? (
                <>
                  <RefreshCw size={15} className="animate-spin" />
                  <span>Simulando Red...</span>
                </>
              ) : (
                <>
                  <Play size={15} />
                  <span>Simular Tránsito What-If</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ÁREA PRINCIPAL: MAPA + PANEL LATERAL */}
        <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
          
          {/* CONTENEDOR DEL MAPA */}
          <div style={{ flex: 1, height: '100%', position: 'relative' }}>
            <MapContainer
              center={centerConfig.center}
              zoom={centerConfig.zoom}
              style={{ width: '100%', height: '100%', background: '#0a0f1e' }}
            >
              <MapRecenter center={centerConfig.center} zoom={centerConfig.zoom} />
              
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />

              {/* TRAMOS VIALES CON COLORES DE TRÁFICO Y SENTIDOS */}
              {tramosAMostrar.map((tramo) => {
                const esModificado = !!modificaciones[tramo.id_tramo]
                const estaCerrado = (tramo.sentido_nuevo === 'CERRADO')
                const color = getColorLOS(tramo.nivel_servicio_nuevo, estaCerrado)
                const isSelected = tramoSeleccionado?.id_tramo === tramo.id_tramo

                return (
                  <Polyline
                    key={`tramo-${tramo.id_tramo}-${tramo.sentido_nuevo}`}
                    positions={tramo.coordenadas}
                    pathOptions={{
                      color: esModificado ? '#38bdf8' : color,
                      weight: isSelected ? 8 : (esModificado ? 6 : 5),
                      opacity: estaCerrado ? 0.4 : 0.85,
                      dashArray: estaCerrado ? '6, 8' : (esModificado ? '4, 4' : null)
                    }}
                    eventHandlers={{
                      click: () => setTramoSeleccionado(tramo)
                    }}
                  >
                    <Popup>
                      <div style={{ color: '#0f172a', minWidth: 220, fontSize: '0.85rem' }}>
                        <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#1e293b', marginBottom: 4 }}>
                          {tramo.nombre_calle}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>
                          {tramo.municipio} • Sentido: <strong>{tramo.sentido_nuevo}</strong>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 10, background: '#f8fafc', padding: 6, borderRadius: 6 }}>
                          <div>Velocidad: <strong>{tramo.velocidad_efectiva_nueva_kmh} km/h</strong></div>
                          <div>LOS: <strong style={{ color: color }}>{tramo.nivel_servicio_nuevo}</strong></div>
                          <div>Flujo: <strong>{tramo.flujo_nuevo_veh_h} v/h</strong></div>
                          <div>Capacidad: <strong>{tramo.capacidad_veh_h} v/h</strong></div>
                        </div>
                        {tramo.lineas_afectadas?.length > 0 && (
                          <div style={{ fontSize: '0.75rem', color: '#0284c7', marginBottom: 8 }}>
                            🚌 Buses: {tramo.lineas_afectadas.join(', ')}
                          </div>
                        )}
                        <button
                          onClick={() => setTramoSeleccionado(tramo)}
                          style={{
                            width: '100%',
                            background: '#2563eb',
                            color: 'white',
                            border: 'none',
                            padding: '6px 10px',
                            borderRadius: 6,
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          Configurar What-If
                        </button>
                      </div>
                    </Popup>
                  </Polyline>
                )
              })}

              {/* CAPA DE ALERTAS WAZE EN VIVO */}
              {showWaze && wazeData.alerts?.map((alerta) => (
                <Marker
                  key={alerta.id}
                  position={[alerta.location.lat, alerta.location.lon]}
                  icon={crearIconoWaze(alerta.type)}
                >
                  <Popup>
                    <div style={{ color: '#0f172a', minWidth: 200, fontSize: '0.85rem' }}>
                      <div style={{ fontWeight: 700, color: '#b45309', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span>Waze Alert: {alerta.type}</span>
                      </div>
                      <div style={{ fontWeight: 600, marginTop: 4 }}>{alerta.street}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                        {alerta.descripcion || alerta.subtype}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: 6 }}>
                        Confiabilidad Waze: {alerta.reliability}/10
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>

            {/* VISOR OFICIAL EMBEBIDO DE WAZE LIVE MAP */}
            {showWazeLiveMap && (
              <div style={{
                position: 'absolute',
                top: 16,
                right: 16,
                width: '460px',
                height: '420px',
                background: 'rgba(15, 23, 42, 0.95)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(6, 182, 212, 0.4)',
                borderRadius: '16px',
                boxShadow: '0 12px 36px rgba(0,0,0,0.6)',
                zIndex: 1000,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}>
                <div style={{
                  padding: '10px 16px',
                  background: 'rgba(30, 41, 59, 0.8)',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    <span>🚗 Waze Live Map — {municipioSel}</span>
                    <span className="badge badge-primary" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>En Vivo</span>
                  </div>
                  <button
                    onClick={() => setShowWazeLiveMap(false)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: '1rem', fontWeight: 700 }}
                  >
                    ✕
                  </button>
                </div>
                <div style={{ flex: 1, position: 'relative' }}>
                  <iframe
                    src={`https://embed.waze.com/iframe?zoom=13&lat=${centerConfig.center[0]}&lon=${centerConfig.center[1]}&ct=livemap`}
                    width="100%"
                    height="100%"
                    allowFullScreen
                    style={{ border: 0 }}
                    title="Waze Live Map"
                  />
                </div>
              </div>
            )}

            {/* LEYENDA DEL MAPA FLOTANTE */}
            <div style={{
              position: 'absolute',
              bottom: 24,
              left: 24,
              background: 'rgba(15, 23, 42, 0.88)',
              backdropFilter: 'blur(10px)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              fontSize: '0.75rem',
              zIndex: 1000,
              boxShadow: 'var(--shadow-md)'
            }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Nivel de Servicio (LOS)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 14, height: 4, background: '#10b981', borderRadius: 2 }}></span>
                  <span>Fluido (LOS A/B)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 14, height: 4, background: '#f59e0b', borderRadius: 2 }}></span>
                  <span>Moderado (LOS C)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 14, height: 4, background: '#f97316', borderRadius: 2 }}></span>
                  <span>Tráfico Pesado (LOS D/E)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 14, height: 4, background: '#ef4444', borderRadius: 2 }}></span>
                  <span>Colapso / Saturación (LOS F)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ width: 14, height: 4, background: '#38bdf8', borderRadius: 2 }}></span>
                  <span>Tramo Modificado What-If</span>
                </div>
              </div>
            </div>
          </div>

          {/* PANEL LATERAL: CONFIGURACIÓN WHAT-IF & RESULTADOS */}
          <div style={{
            width: 440,
            background: 'var(--color-bg-secondary)',
            borderLeft: '1px solid var(--color-border)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
            zIndex: 10
          }}>
            
            {/* MODAL / PANEL DE ACCIONES DEL TRAMO SELECCIONADO */}
            {tramoSeleccionado ? (
              <div style={{ padding: 18, borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg-surface)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span className="badge badge-info">{tramoSeleccionado.municipio}</span>
                  <button
                    onClick={() => setTramoSeleccionado(null)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: '1.1rem' }}
                  >
                    ✕
                  </button>
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
                  {tramoSeleccionado.nombre_calle}
                </h3>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: 14 }}>
                  Sentido Actual: <span style={{ color: 'var(--color-accent-cyan)', fontWeight: 600 }}>{tramoSeleccionado.sentido_nuevo}</span>
                </div>

                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
                  Probar Intervención What-If:
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <button
                    onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, 'UNICO_DIRECTO')}
                    className="btn btn-sm btn-outline"
                    style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    ➡️ Sentido Único
                  </button>
                  <button
                    onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, 'UNICO_INVERSO')}
                    className="btn btn-sm btn-outline"
                    style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    ⬅️ Invertir Sentido
                  </button>
                  <button
                    onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, 'DOBLE')}
                    className="btn btn-sm btn-outline"
                    style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    ↔️ Doble Sentido
                  </button>
                  <button
                    onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, 'CERRADO')}
                    className="btn btn-sm btn-outline"
                    style={{ fontSize: '0.75rem', color: '#f43f5e', borderColor: '#f43f5e50', display: 'flex', alignItems: 'center', gap: 4 }}
                  >
                    ⛔ Cerrar por Obras
                  </button>
                </div>

                <div style={{ marginTop: 10 }}>
                  <button
                    onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, tramoSeleccionado.sentido_nuevo, true)}
                    className="btn btn-sm btn-outline"
                    style={{ width: '100%', fontSize: '0.75rem', color: '#06b6d4', borderColor: '#06b6d450', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                  >
                    <Bus size={14} /> Asignar Carril Exclusivo para Colectivos
                  </button>
                </div>

                {modificaciones[tramoSeleccionado.id_tramo] && (
                  <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-accent-emerald)' }}>
                      ✓ Cambio programado para la simulación
                    </span>
                    <button
                      onClick={() => aplicarModificacion(tramoSeleccionado.id_tramo, 'ORIGINAL')}
                      style={{ background: 'transparent', border: 'none', color: '#f43f5e', fontSize: '0.75rem', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      Revertir
                    </button>
                  </div>
                )}
              </div>
            ) : null}

            {/* PESTAÑAS DE RESULTADOS */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg-primary)' }}>
              <button
                onClick={() => setTabActiva('diagnostico')}
                style={{
                  flex: 1,
                  padding: '12px 8px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: tabActiva === 'diagnostico' ? '2px solid var(--color-accent-blue)' : 'none',
                  color: tabActiva === 'diagnostico' ? 'var(--color-accent-blue)' : 'var(--color-text-muted)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Diagnóstico
              </button>
              <button
                onClick={() => setTabActiva('colapso')}
                style={{
                  flex: 1,
                  padding: '12px 8px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: tabActiva === 'colapso' ? '2px solid var(--color-accent-rose)' : 'none',
                  color: tabActiva === 'colapso' ? 'var(--color-accent-rose)' : 'var(--color-text-muted)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Paralelas ({resultadoSim?.calles_en_colapso?.length || 0})
              </button>
              <button
                onClick={() => setTabActiva('tp')}
                style={{
                  flex: 1,
                  padding: '12px 8px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: tabActiva === 'tp' ? '2px solid var(--color-accent-cyan)' : 'none',
                  color: tabActiva === 'tp' ? 'var(--color-accent-cyan)' : 'var(--color-text-muted)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Buses ({resultadoSim?.lineas_transporte_impactadas?.length || 0})
              </button>
              <button
                onClick={() => setTabActiva('reporte')}
                style={{
                  flex: 1,
                  padding: '12px 8px',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: tabActiva === 'reporte' ? '2px solid var(--color-accent-emerald)' : 'none',
                  color: tabActiva === 'reporte' ? 'var(--color-accent-emerald)' : 'var(--color-text-muted)',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Reporte
              </button>
            </div>

            {/* CONTENIDO DE LAS PESTAÑAS */}
            <div style={{ padding: 18, flex: 1, overflowY: 'auto' }}>
              
              {/* TAB 1: DIAGNÓSTICO COMPARATIVO */}
              {tabActiva === 'diagnostico' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {resultadoSim ? (
                    <>
                      <div className="card" style={{ padding: 14 }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                          Velocidad Promedio de la Red
                        </div>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                            {resultadoSim.velocidad_promedio_nueva_kmh} km/h
                          </span>
                          <span style={{
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            color: resultadoSim.variacion_velocidad_pct >= 0 ? '#10b981' : '#ef4444',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 2
                          }}>
                            {resultadoSim.variacion_velocidad_pct >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                            {resultadoSim.variacion_velocidad_pct}% vs. base ({resultadoSim.velocidad_promedio_anterior_kmh} km/h)
                          </span>
                        </div>
                      </div>

                      <div className="card" style={{ padding: 14 }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                          Tiempo de Viaje Promedio por Corredor
                        </div>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                            {resultadoSim.tiempo_viaje_promedio_nuevo_min} min
                          </span>
                          <span style={{
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            color: resultadoSim.variacion_tiempo_viaje_pct <= 0 ? '#10b981' : '#ef4444'
                          }}>
                            {resultadoSim.variacion_tiempo_viaje_pct > 0 ? `+${resultadoSim.variacion_tiempo_viaje_pct}% demora` : `${resultadoSim.variacion_tiempo_viaje_pct}% más rápido`}
                          </span>
                        </div>
                      </div>

                      <div style={{ background: 'var(--color-bg-card)', padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: 6, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Sparkles size={16} color="#38bdf8" /> Diagnóstico del Algoritmo BPR
                        </div>
                        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                          {resultadoSim.resumen_ejecutivo}
                        </p>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--color-text-muted)' }}>
                      <Car size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                      <p style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 4 }}>
                        Red en estado de observación
                      </p>
                      <p style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
                        Haz clic sobre cualquier calle en el mapa de Asunción o Gran Asunción para cambiar su sentido o cerrarla, y presiona <strong>"Simular Tránsito What-If"</strong>.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: CALLES PARALELAS Y DERRAME DE TRÁFICO */}
              {tabActiva === 'colapso' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {resultadoSim?.calles_en_colapso?.length > 0 ? (
                    resultadoSim.calles_en_colapso.map((calle, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'rgba(239, 68, 68, 0.08)',
                          border: '1px solid rgba(239, 68, 68, 0.25)',
                          borderRadius: 'var(--radius-md)',
                          padding: 12
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                          <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f87171' }}>
                            {calle.calle}
                          </span>
                          <span className="badge badge-danger">
                            {calle.saturacion_pct}% Capacidad
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: 6 }}>
                          {calle.municipio} • Retraso extra: <strong>+{calle.retraso_adicional_min} min</strong>
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                          Causa: {calle.motivo}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '24px 8px', color: 'var(--color-text-muted)' }}>
                      <CheckCircle2 size={32} style={{ margin: '0 auto 10px', color: '#10b981' }} />
                      <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        Sin saturación en calles paralelas
                      </p>
                      <p style={{ fontSize: '0.78rem', marginTop: 4 }}>
                        El flujo vehicular redistribuido no supera la capacidad máxima de las arterias aledañas.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: TRANSPORTE PÚBLICO IMPACTADO */}
              {tabActiva === 'tp' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {resultadoSim?.lineas_transporte_impactadas?.length > 0 ? (
                    resultadoSim.lineas_transporte_impactadas.map((linea, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--color-bg-card)',
                          border: '1px solid var(--color-border)',
                          borderRadius: 'var(--radius-md)',
                          padding: 12
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <span style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--color-accent-cyan)' }}>
                            🚌 {linea.linea}
                          </span>
                          {linea.desvio_obligatorio ? (
                            <span className="badge badge-danger">Desvío Obligatorio</span>
                          ) : (
                            <span className="badge badge-warning">Retraso por Cola</span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginBottom: 6 }}>
                          Demora estimada por ciclo: <strong>+{linea.retraso_estimado_min} min</strong>
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
                          Corredores intervenidos: {linea.tramos_afectados.join(', ')}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '24px 8px', color: 'var(--color-text-muted)' }}>
                      <Bus size={32} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
                      <p style={{ fontSize: '0.85rem' }}>
                        No hay líneas de colectivos perjudicadas en las calles modificadas.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: REPORTE EJECUTIVO MUNICIPAL */}
              {tabActiva === 'reporte' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ background: 'var(--color-bg-card)', padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: 8 }}>
                      DICTAMEN TÉCNICO DE TRÁNSITO
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                      <strong>Municipio:</strong> {municipioSel}<br />
                      <strong>Franja Evaluada:</strong> {franjaHoraria.replace('_', ' ')}<br />
                      <strong>Intervenciones:</strong> {totalModificados} tramo(s) alterados<br />
                      <strong>Variación en Velocidad:</strong> {resultadoSim?.variacion_velocidad_pct || 0}%<br />
                      <strong>Calles en Alerta Roja:</strong> {resultadoSim?.calles_en_colapso?.length || 0} paralelas<br />
                      <strong>Líneas Colectivos Afectadas:</strong> {resultadoSim?.lineas_transporte_impactadas?.length || 0} líneas
                    </div>
                  </div>

                  <button
                    onClick={() => window.print()}
                    className="btn btn-sm btn-outline"
                    style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
                  >
                    <span>Imprimir Reporte para Dirección de Tránsito</span>
                  </button>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </>
  )
}
