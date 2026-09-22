import React, { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import { prediccionesApi, busesApi } from '../services/api'
import { Clock, TrendingUp, AlertTriangle, CheckCircle, Zap, Search } from 'lucide-react'

export default function PrediccionesPage() {
  const [busId, setBusId] = useState(1)
  const [buses, setBuses] = useState([])
  const [etas, setEtas] = useState([])
  const [optimizacion, setOptimizacion] = useState(null)
  const [loading, setLoading] = useState(false)
  const [demanda, setDemanda] = useState(800)

  // Cargar lista de buses disponibles
  useEffect(() => {
    const cargarBuses = async () => {
      try {
        const res = await busesApi.listar()
        if (res.data && res.data.length > 0) {
          setBuses(res.data)
          setBusId(res.data[0].id_bus)
        } else {
          setBuses([1, 2, 3, 4, 5, 6].map(id => ({ id_bus: id, interno: id.toString().padStart(3, '0') })))
        }
      } catch {
        setBuses([1, 2, 3, 4, 5, 6].map(id => ({ id_bus: id, interno: id.toString().padStart(3, '0') })))
      }
    }
    cargarBuses()
  }, [])

  const cargarPredicciones = async () => {
    if (!busId) return
    setLoading(true)
    try {
      const [resEta, resOpt] = await Promise.allSettled([
        prediccionesApi.getEta(busId),
        prediccionesApi.getOptimizacion(1, demanda)
      ])

      if (resEta.status === 'fulfilled' && resEta.value.data) {
        setEtas(resEta.value.data.predicciones || [])
      } else {
        console.warn('No se pudieron obtener ETAs para el bus:', busId, resEta.reason)
        setEtas([])
      }

      if (resOpt.status === 'fulfilled' && resOpt.value.data) {
        setOptimizacion(resOpt.value.data)
      } else {
        console.warn('No se pudo obtener optimización:', resOpt.reason)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarPredicciones()
  }, [busId, demanda])

  return (
    <>
      <Header 
        titulo="IA Operacional & Predicciones" 
        subtitulo="Estimación de tiempos de llegada y optimización de frecuencias"
      />
      <div className="page-content">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: 24 }}>
          
          {/* Panel Principal: ETAs */}
          <div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Clock size={20} color="var(--color-accent-blue)" />
                  <span className="card-title">Proyección de Arribos (ETA)</span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <select 
                    className="form-control" 
                    style={{ minWidth: 160, padding: '4px 10px' }}
                    value={busId}
                    onChange={(e) => setBusId(Number(e.target.value))}
                  >
                    {buses.map(b => (
                      <option key={b.id_bus} value={b.id_bus}>
                        Bus {b.interno || b.id_bus.toString().padStart(3, '0')} {b.placa ? `(${b.placa})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Paradero</th>
                      <th>Distancia</th>
                      <th>ETA (min)</th>
                      <th>Hora Est.</th>
                      <th>Probabilidad</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      [1,2,3,4,5].map(i => <tr key={i}><td colSpan="5" className="skeleton" style={{ height: 40 }}></td></tr>)
                    ) : etas.length > 0 ? (
                      etas.map((p, i) => (
                        <tr key={i} className="fade-in" style={{ animationDelay: `${i * 50}ms` }}>
                          <td style={{ fontWeight: 600 }}>{p.nombre}</td>
                          <td style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem' }}>{p.distancia_restante_m} m</td>
                          <td>
                            <span className="badge badge-info" style={{ fontSize: '0.9rem', fontWeight: 700 }}>
                              {p.eta_minutos} min
                            </span>
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                            {new Date(p.hora_estimada).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <div className="progress-bar" style={{ width: 60 }}>
                                <div className="progress-fill" style={{ width: `${95 - i*5}%` }} />
                              </div>
                              <span style={{ fontSize: '0.75rem' }}>{95 - i*5}%</span>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr><td colSpan="5" className="empty-state">No hay predicciones disponibles</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Alertas de IA */}
            <div className="grid-2">
              <div className="alert alert-warning card">
                <div style={{ display: 'flex', gap: 12 }}>
                  <AlertTriangle size={24} />
                  <div>
                    <div style={{ fontWeight: 700, marginBottom: 4 }}>Congestión Detectada</div>
                    <p style={{ fontSize: '0.85rem', color: 'inherit', opacity: 0.8 }}>
                      El corredor Avda. Eusebio Ayala presenta una velocidad 20% inferior a la media. 
                      Se proyectan atrasos de hasta 4 min en las próximas 3 paradas.
                    </p>
                  </div>
                </div>
              </div>
              <div className="alert alert-success card">
                <div style={{ display: 'flex', gap: 12 }}>
                  <CheckCircle size={24} />
                  <div>
                    <div style={{ fontWeight: 700, marginBottom: 4 }}>Optimización Sugerida</div>
                    <p style={{ fontSize: '0.85rem', color: 'inherit', opacity: 0.8 }}>
                      Reduciendo el despacho en 2 min se podría mitigar el efecto de bunching detectado en la zona céntrica.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Panel Lateral: Optimización */}
          <div className="card-glass" style={{ border: '1px solid var(--color-border-active)', height: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <TrendingUp size={20} color="var(--color-accent-cyan)" />
              <span className="card-title">Motor de Optimización</span>
            </div>

            <div className="form-group">
              <label className="form-label">Demanda Proyectada (pax/h)</label>
              <input 
                type="range" 
                min="100" max="2000" step="100" 
                value={demanda} 
                onChange={(e) => setDemanda(Number(e.target.value))}
              />
              <div style={{ textAlign: 'right', fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-accent-cyan)' }}>
                {demanda} <span style={{ fontSize: '0.7rem', fontWeight: 400 }}>pax/h</span>
              </div>
            </div>

            <div className="divider" />

            {optimizacion ? (
              <div className="fade-in">
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                    Headway Recomendado
                  </div>
                  <div style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--color-text-primary)', lineHeight: 1 }}>
                    {optimizacion.analisis.headway_sugerido_min}
                    <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 6 }}>min</span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 4 }}>Buses Requeridos</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{optimizacion.analisis.buses_necesarios}</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 4 }}>Nivel de Servicio</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-success)' }}>{optimizacion.analisis.nivel_servicio_estimado}</div>
                  </div>
                </div>

                <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                  <Zap size={16} />
                  Aplicar Recomendación
                </button>
                
                <p style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 12, textAlign: 'center' }}>
                  * Cálculo basado en tiempo de ciclo de 60 min y factor de carga del 80%.
                </p>
              </div>
            ) : (
              <div className="skeleton" style={{ height: 200 }} />
            )}
          </div>

        </div>
      </div>
    </>
  )
}
