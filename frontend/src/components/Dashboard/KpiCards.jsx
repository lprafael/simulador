import React from 'react'

export default function KpiCards({ kpis, loading }) {
  const cards = [
    {
      id: 'headway',
      label: 'Headway Promedio',
      value: kpis?.headway_promedio_min ?? kpis?.headway_promedio ?? '—',
      unit: 'min',
      icon: '⏱',
      accent: '#3b82f6',
      bg: 'rgba(59,130,246,0.08)',
      delta: null,
    },
    {
      id: 'regularidad',
      label: 'Regularidad',
      value: kpis?.regularidad_pct ?? kpis?.regularidad ?? '—',
      unit: '%',
      icon: '📊',
      accent: '#10b981',
      bg: 'rgba(16,185,129,0.08)',
      delta: null,
    },
    {
      id: 'bunching',
      label: 'Bunching',
      value: kpis?.pct_bunching ?? '—',
      unit: '%',
      icon: '🚌',
      accent: '#f59e0b',
      bg: 'rgba(245,158,11,0.08)',
      delta: null,
    },
    {
      id: 'velocidad',
      label: 'Vel. Comercial',
      value: kpis?.velocidad_comercial_kmh ?? kpis?.velocidad_comercial ?? '—',
      unit: 'km/h',
      icon: '⚡',
      accent: '#8b5cf6',
      bg: 'rgba(139,92,246,0.08)',
      delta: null,
    },
    {
      id: 'pasajeros',
      label: 'Pasajeros Sim.',
      value: kpis?.total_pasajeros ?? kpis?.total_pasajeros_transportados ?? '—',
      unit: 'pax',
      icon: '👥',
      accent: '#06b6d4',
      bg: 'rgba(6,182,212,0.08)',
      delta: null,
    },
    {
      id: 'eventos',
      label: 'Eventos',
      value: kpis?.total_eventos ?? '—',
      unit: '',
      icon: '📋',
      accent: '#f43f5e',
      bg: 'rgba(244,63,94,0.08)',
      delta: null,
    },
  ]

  if (loading) {
    return (
      <div className="kpi-grid">
        {cards.map((_, i) => (
          <div key={i} className="kpi-card">
            <div className="skeleton" style={{ height: 16, width: '60%', marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 40, width: '80%', marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 12, width: '40%' }} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="kpi-grid">
      {cards.map((card) => {
        const displayValue = typeof card.value === 'number'
          ? card.value.toFixed(1)
          : card.value

        return (
          <div
            key={card.id}
            className="kpi-card fade-in"
            style={{ '--kpi-accent': card.accent }}
          >
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 'var(--radius-md)',
              background: card.bg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.25rem',
              marginBottom: 12,
            }}>
              {card.icon}
            </div>
            
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span className="kpi-value" style={{ color: card.value === '—' ? 'var(--color-text-muted)' : undefined }}>
                {displayValue}
              </span>
              {card.unit && card.value !== '—' && (
                <span className="kpi-unit">{card.unit}</span>
              )}
            </div>
            
            <div className="kpi-label">{card.label}</div>
          </div>
        )
      })}
    </div>
  )
}
