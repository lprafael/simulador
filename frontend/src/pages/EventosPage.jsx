import React, { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import { kpiApi } from '../services/api'
import { RefreshCw } from 'lucide-react'

const EVENTOS_DEMO = [
  { id: 1, tipo_evento: 'ARRIBO', id_bus: 3, timestamp: new Date(Date.now() - 60000).toISOString(), descripcion: 'Bus 003 arriba a Plaza de los Héroes' },
  { id: 2, tipo_evento: 'BUNCHING', id_bus: 4, timestamp: new Date(Date.now() - 120000).toISOString(), descripcion: 'Bus 004 en bunching: headway 2.1 min < umbral' },
  { id: 3, tipo_evento: 'PARTIDA', id_bus: 3, timestamp: new Date(Date.now() - 180000).toISOString(), descripcion: 'Bus 003 parte de Plaza de los Héroes (5 suben, 3 bajan)' },
  { id: 4, tipo_evento: 'ARRIBO', id_bus: 1, timestamp: new Date(Date.now() - 240000).toISOString(), descripcion: 'Bus 001 arriba a Terminal Fernando de la Mora' },
  { id: 5, tipo_evento: 'ATRASO', id_bus: 6, timestamp: new Date(Date.now() - 300000).toISOString(), descripcion: 'Bus 006 con atraso detectado en Mercado 4' },
  { id: 6, tipo_evento: 'ARRIBO', id_bus: 2, timestamp: new Date(Date.now() - 360000).toISOString(), descripcion: 'Bus 002 arriba a Mercado 4' },
  { id: 7, tipo_evento: 'PARTIDA', id_bus: 5, timestamp: new Date(Date.now() - 420000).toISOString(), descripcion: 'Bus 005 parte de Universidad (12 suben, 8 bajan)' },
  { id: 8, tipo_evento: 'ARRIBO', id_bus: 2, timestamp: new Date(Date.now() - 480000).toISOString(), descripcion: 'Bus 002 arriba a Terminal Ómnibus Asunción' },
  { id: 9, tipo_evento: 'BUNCHING', id_bus: 3, timestamp: new Date(Date.now() - 540000).toISOString(), descripcion: 'Bus 003 en bunching: headway 1.8 min < umbral' },
  { id: 10, tipo_evento: 'ARRIBO', id_bus: 1, timestamp: new Date(Date.now() - 600000).toISOString(), descripcion: 'Bus 001 arriba a Cruce Avda. Eusebio Ayala' },
]

const TIPO_CONFIG = {
  BUNCHING: { bg: 'rgba(245,158,11,0.12)', color: '#f59e0b', icon: '⚠️' },
  ARRIBO: { bg: 'rgba(6,182,212,0.1)', color: '#06b6d4', icon: '🟢' },
  PARTIDA: { bg: 'rgba(148,163,184,0.08)', color: '#94a3b8', icon: '🚌' },
  ATRASO: { bg: 'rgba(244,63,94,0.12)', color: '#f43f5e', icon: '🔴' },
}

function tiempoRelativo(isoStr) {
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'ahora mismo'
  if (mins < 60) return `hace ${mins} min`
  return `hace ${Math.floor(mins/60)} h`
}

export default function EventosPage() {
  const [eventos, setEventos] = useState(EVENTOS_DEMO)
  const [loading, setLoading] = useState(false)
  const [filtroTipo, setFiltroTipo] = useState('TODOS')

  const cargar = async () => {
    setLoading(true)
    try {
      const res = await kpiApi.eventosRecientes(50)
      if (res.data.length > 0) setEventos(res.data)
    } catch {
      setEventos(EVENTOS_DEMO)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const eventosFiltrados = eventos.filter(ev => 
    filtroTipo === 'TODOS' || ev.tipo_evento === filtroTipo
  )

  return (
    <>
      <Header
        titulo="Registro de Eventos"
        subtitulo="Eventos operacionales detectados por el sistema"
        acciones={
          <button className="btn btn-outline btn-sm" onClick={cargar} id="btn-refresh-eventos">
            <RefreshCw size={14} />
            Actualizar
          </button>
        }
      />
      <div className="page-content">
        {/* Resumen contadores */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          {Object.entries(TIPO_CONFIG).map(([tipo, cfg]) => {
            const count = eventos.filter(e => e.tipo_evento === tipo).length
            return (
              <button
                key={tipo}
                onClick={() => setFiltroTipo(filtroTipo === tipo ? 'TODOS' : tipo)}
                style={{
                  background: filtroTipo === tipo ? cfg.bg : 'var(--color-bg-card)',
                  border: `1px solid ${filtroTipo === tipo ? cfg.color + '40' : 'var(--color-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 16px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all var(--transition-fast)',
                }}
              >
                <span>{cfg.icon}</span>
                <span style={{ fontWeight: 600, color: filtroTipo === tipo ? cfg.color : 'var(--color-text-secondary)', fontSize: '0.85rem' }}>
                  {tipo}
                </span>
                <span style={{
                  background: cfg.bg,
                  color: cfg.color,
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '1px 8px',
                  borderRadius: 999,
                }}>
                  {count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Lista de eventos */}
        <div className="card">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 64, marginBottom: 4 }} />
              ))
            ) : eventosFiltrados.length === 0 ? (
              <div className="empty-state" style={{ padding: 48 }}>
                <div className="empty-state-icon">📋</div>
                <p>No hay eventos de tipo {filtroTipo}</p>
              </div>
            ) : (
              eventosFiltrados.map((ev, i) => {
                const cfg = TIPO_CONFIG[ev.tipo_evento] || { bg: 'rgba(148,163,184,0.05)', color: '#94a3b8', icon: '📌' }
                return (
                  <div
                    key={ev.id || i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 14,
                      padding: '12px 16px',
                      borderBottom: '1px solid var(--color-border)',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: 'var(--radius-md)',
                      background: cfg.bg,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      flexShrink: 0,
                    }}>
                      {cfg.icon}
                    </div>
                    
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: cfg.color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          {ev.tipo_evento}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                          Bus-{ev.id_bus}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.descripcion}
                      </p>
                    </div>
                    
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', flexShrink: 0, textAlign: 'right' }}>
                      {tiempoRelativo(ev.timestamp || new Date().toISOString())}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </>
  )
}
