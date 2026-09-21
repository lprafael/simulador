import React, { useState } from 'react'
import Header from '../components/Layout/Header'
import SimulacionPanel from '../components/Simulation/SimulacionPanel'
import KpiCards from '../components/Dashboard/KpiCards'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, Legend, ReferenceLine
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '10px 14px', fontSize: '0.8rem' }}>
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

export default function SimulacionPage() {
  const [resultados, setResultados] = useState(null)
  const [headwayData, setHeadwayData] = useState([])
  const [ocupacionData, setOcupacionData] = useState([])

  const handleResultados = (data) => {
    setResultados(data)
    
    // Construir serie de headways
    if (data.headways) {
      const points = []
      Object.entries(data.headways).forEach(([pid, hwList]) => {
        hwList.forEach((hw, i) => {
          points.push({
            t: `P${pid}-${i+1}`,
            headway: Number(hw.toFixed(2)),
            programado: data.kpis?.headway_programado || 8,
          })
        })
      })
      setHeadwayData(points.slice(0, 50))
    }
    
    // Ocupación por bus
    if (data.estados_buses) {
      setOcupacionData(data.estados_buses.map(b => ({
        bus: b.interno,
        ascensos: b.total_ascensos,
        descensos: b.total_descensos,
      })))
    }
  }

  const kpisDisplay = resultados ? {
    headway_promedio_min: resultados.kpis?.headway_promedio_min,
    regularidad_pct: resultados.kpis?.regularidad_pct,
    pct_bunching: resultados.kpis?.pct_bunching,
    velocidad_comercial_kmh: resultados.kpis?.velocidad_comercial_kmh,
    total_pasajeros: resultados.kpis?.total_pasajeros,
    total_eventos: resultados.kpis?.total_eventos,
  } : null

  return (
    <>
      <Header
        titulo="Motor de Simulación"
        subtitulo="Configuración y ejecución de microsimulaciones operacionales"
      />
      <div className="page-content">
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24, alignItems: 'start' }}>
          {/* Panel de control */}
          <SimulacionPanel onResultados={handleResultados} />
          
          {/* Resultados */}
          <div>
            {resultados ? (
              <div className="fade-in">
                {/* KPIs */}
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
                    Resultados de Simulación
                  </h3>
                  <KpiCards kpis={kpisDisplay} />
                </div>
                
                {/* Gráfico Headway */}
                {headwayData.length > 0 && (
                  <div className="card" style={{ marginBottom: 24 }}>
                    <div className="card-header">
                      <span className="card-title">Análisis de Headway</span>
                      <span className="badge badge-warning">
                        σ = {resultados.kpis?.headway_std_min?.toFixed(2)} min
                      </span>
                    </div>
                    <ResponsiveContainer width="100%" height={220}>
                      <AreaChart data={headwayData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                        <defs>
                          <linearGradient id="gradHeadway" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                        <XAxis dataKey="t" tick={{ fill: '#475569', fontSize: 10 }} interval="preserveStartEnd" />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} unit=" min" />
                        <Tooltip content={<CustomTooltip />} />
                        <ReferenceLine y={8} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: 'Programado', fill: '#f59e0b', fontSize: 10 }} />
                        <Area
                          type="monotone"
                          dataKey="headway"
                          name="Headway real"
                          stroke="#3b82f6"
                          fill="url(#gradHeadway)"
                          strokeWidth={2}
                          dot={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
                
                {/* Gráfico Ocupación por Bus */}
                {ocupacionData.length > 0 && (
                  <div className="card" style={{ marginBottom: 24 }}>
                    <div className="card-header">
                      <span className="card-title">Pasajeros por Bus</span>
                      <span className="badge badge-success">simulados</span>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={ocupacionData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                        <XAxis dataKey="bus" tick={{ fill: '#475569', fontSize: 11 }} />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                        <Bar dataKey="ascensos" name="Subieron" fill="#10b981" radius={[4,4,0,0]} />
                        <Bar dataKey="descensos" name="Bajaron" fill="#3b82f6" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
                
                {/* Tabla de eventos de simulación */}
                {resultados.eventos && resultados.eventos.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">Registro de Eventos</span>
                      <span className="badge badge-neutral">{resultados.total_eventos || resultados.kpis?.total_eventos} total</span>
                    </div>
                    <div style={{ overflowX: 'auto', maxHeight: 300, overflowY: 'auto' }}>
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Tipo</th>
                            <th>Bus</th>
                            <th>T. Sim (min)</th>
                            <th>Descripción</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultados.eventos.map((ev, i) => (
                            <tr key={i}>
                              <td>
                                <span className="badge" style={{
                                  background: {
                                    BUNCHING: 'rgba(245,158,11,0.15)',
                                    ARRIBO: 'rgba(6,182,212,0.15)',
                                    PARTIDA: 'rgba(148,163,184,0.1)',
                                    ATRASO: 'rgba(244,63,94,0.15)',
                                  }[ev.tipo_evento] || 'rgba(148,163,184,0.1)',
                                  color: {
                                    BUNCHING: '#f59e0b',
                                    ARRIBO: '#06b6d4',
                                    PARTIDA: '#94a3b8',
                                    ATRASO: '#f43f5e',
                                  }[ev.tipo_evento] || '#94a3b8',
                                }}>
                                  {ev.tipo_evento}
                                </span>
                              </td>
                              <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                Bus-{ev.id_bus}
                              </td>
                              <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                                {ev.tiempo_sim?.toFixed(2)}
                              </td>
                              <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                                {ev.descripcion}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="card">
                <div className="empty-state">
                  <div className="empty-state-icon">⚡</div>
                  <h3 style={{ color: 'var(--color-text-primary)', marginBottom: 8 }}>Motor de Simulación Listo</h3>
                  <p>Configure los parámetros y ejecute una simulación para visualizar el análisis de headways, detección de bunching y KPIs operacionales.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
