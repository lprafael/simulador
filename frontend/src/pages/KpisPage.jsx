import React from 'react'
import Header from '../components/Layout/Header'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip
} from 'recharts'

const DATOS_KPI = [
  { indicador: 'Regularidad', valor: 78, umbral: 70, unidad: '%' },
  { indicador: 'Headway', valor: 8.5, umbral: 8.0, unidad: 'min' },
  { indicador: 'Vel. Comercial', valor: 22.3, umbral: 20.0, unidad: 'km/h' },
  { indicador: 'Cobertura', valor: 94, umbral: 90, unidad: '%' },
  { indicador: 'Bunching', valor: 12, umbral: 15, unidad: '%', invertido: true },
  { indicador: 'Ocupación', valor: 68, umbral: 80, unidad: '%' },
]

const RADAR_DATA = [
  { kpi: 'Regularidad', valor: 78 },
  { kpi: 'Velocidad', valor: 85 },
  { kpi: 'Cobertura', valor: 94 },
  { kpi: 'Ocupación', valor: 68 },
  { kpi: 'Anti-Bunching', valor: 88 },
  { kpi: 'Puntualidad', valor: 72 },
]

export default function KpisPage() {
  return (
    <>
      <Header
        titulo="KPIs Operacionales"
        subtitulo="Indicadores clave de rendimiento del sistema de transporte"
      />
      <div className="page-content">
        {/* Tabla de KPIs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 24, alignItems: 'start' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Indicadores del Sistema</span>
              <span className="badge badge-info">Última simulación</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>
              {DATOS_KPI.map(kpi => {
                const esOk = kpi.invertido ? kpi.valor <= kpi.umbral : kpi.valor >= kpi.umbral
                const pct = kpi.invertido
                  ? Math.max(0, Math.min(100, (1 - kpi.valor / (kpi.umbral * 2)) * 100))
                  : Math.max(0, Math.min(100, (kpi.valor / (kpi.umbral * 1.5)) * 100))
                
                return (
                  <div key={kpi.indicador} style={{
                    display: 'grid',
                    gridTemplateColumns: '140px 1fr 100px',
                    alignItems: 'center',
                    gap: 16,
                    padding: '12px 16px',
                    background: 'var(--color-bg-surface)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${esOk ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}`,
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>
                        {kpi.indicador}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                        Umbral: {kpi.umbral} {kpi.unidad}
                      </div>
                    </div>
                    
                    <div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{
                          width: `${pct}%`,
                          background: esOk
                            ? 'linear-gradient(90deg, #10b981, #06b6d4)'
                            : 'linear-gradient(90deg, #f43f5e, #f59e0b)',
                        }} />
                      </div>
                    </div>
                    
                    <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 8 }}>
                      <span style={{ fontSize: '1.1rem', fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: esOk ? 'var(--color-success)' : 'var(--color-danger)' }}>
                        {kpi.valor}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{kpi.unidad}</span>
                      <span style={{ fontSize: '1rem' }}>{esOk ? '✅' : '⚠️'}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Radar Chart */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Perfil de Rendimiento</span>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="kpi" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569', fontSize: 9 }} />
                <Radar
                  name="Sistema"
                  dataKey="valor"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 8,
                    fontSize: '0.8rem',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {RADAR_DATA.map(d => (
                <div key={d.kpi} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{d.kpi}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="progress-bar" style={{ width: 80 }}>
                      <div className="progress-fill" style={{ width: `${d.valor}%` }} />
                    </div>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, fontVariantNumeric: 'tabular-nums', minWidth: 32, textAlign: 'right' }}>{d.valor}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Definición de KPIs */}
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header">
            <span className="card-title">Definición de Indicadores</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>KPI</th>
                <th>Descripción</th>
                <th>Fórmula</th>
                <th>Umbral</th>
                <th>Fuente</th>
              </tr>
            </thead>
            <tbody>
              {[
                { kpi: 'Headway', desc: 'Intervalo entre buses en un paradero', formula: 't_bus_n+1 − t_bus_n', umbral: '≤ 10 min', fuente: 'AVL / Simulación' },
                { kpi: 'Regularidad', desc: 'Cumplimiento del headway programado', formula: 'N(|hw_real − hw_prog| < 30%) / N_total × 100', umbral: '≥ 70%', fuente: 'Simulación' },
                { kpi: 'Bunching', desc: 'Porcentaje de buses en agrupamiento', formula: 'N(headway < 50% programado) / N_total × 100', umbral: '≤ 15%', fuente: 'Simulación' },
                { kpi: 'Vel. Comercial', desc: 'Velocidad promedio incluyendo tiempos de parada', formula: 'distancia_km / tiempo_total_h', umbral: '≥ 18 km/h', fuente: 'AVL' },
                { kpi: 'Ocupación', desc: 'Pasajeros promedio / Capacidad vehicular', formula: 'pax_abordo / capacidad × 100', umbral: '≤ 80%', fuente: 'Billetaje / Sim.' },
              ].map(r => (
                <tr key={r.kpi}>
                  <td style={{ fontWeight: 600, color: 'var(--color-accent-blue-bright)' }}>{r.kpi}</td>
                  <td>{r.desc}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{r.formula}</td>
                  <td><span className="badge badge-success">{r.umbral}</span></td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{r.fuente}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
