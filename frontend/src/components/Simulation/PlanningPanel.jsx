import React, { useState, useEffect } from 'react'
import { Calculator, Users, Clock, Truck } from 'lucide-react'
import { planningApi } from '../../services/api'

export default function PlanningPanel({ idLinea }) {
  const [frecuencia, setFrecuencia] = useState(10)
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading] = useState(false)

  const calcularOptimización = async () => {
    if (!idLinea) return
    setLoading(true)
    try {
      const res = await planningApi.optimizarFlota(idLinea, frecuencia)
      setResultado(res.data)
    } catch (err) {
      console.error("Error en optimización:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (idLinea) calcularOptimización()
  }, [idLinea, frecuencia])

  if (!idLinea) return (
    <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--color-text-muted)' }}>
      <div>
        <Truck size={40} style={{ marginBottom: 12, opacity: 0.5 }} />
        <p>Seleccione una Línea para<br/>calcular la flota necesaria</p>
      </div>
    </div>
  )

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Calculator size={18} color="var(--color-accent-blue)" />
          <span className="card-title">Planificación Operativa</span>
        </div>
      </div>

      <div style={{ padding: '16px' }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: 8, fontWeight: 600 }}>
            INTERVALO DE SALIDA (FRECUENCIA)
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <input 
              type="range" 
              min="2" 
              max="30" 
              step="1"
              value={frecuencia}
              onChange={(e) => setFrecuencia(e.target.value)}
              style={{ flex: 1 }}
            />
            <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-accent-blue)', minWidth: 60 }}>
              {frecuencia} min
            </span>
          </div>
        </div>

        {resultado && (
          <div className="grid-2" style={{ gap: 12 }}>
            <div style={{ background: 'var(--color-bg-page)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                <Truck size={12} /> FLOTA OPERATIVA
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{resultado.flota_necesaria} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>buses</span></div>
            </div>

            <div style={{ background: 'var(--color-bg-page)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                <Users size={12} /> CAPACIDAD OFERTA
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{resultado.capacidad_oferta_pax_hora} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>pax/h</span></div>
            </div>

            <div style={{ background: 'var(--color-bg-page)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                <Clock size={12} /> TIEMPO DE CICLO
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{resultado.tiempo_ciclo_estimado_min} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>min</span></div>
            </div>

            <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: 12, borderRadius: 8, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.7rem', color: '#10b981', marginBottom: 4 }}>
                <Activity size={12} /> FLOTA DE RESERVA
              </div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>+ {resultado.flota_reserva_sugerida} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>buses</span></div>
            </div>
          </div>
        )}

        <div style={{ marginTop: 20, fontSize: '0.7rem', color: 'var(--color-text-muted)', fontStyle: 'italic', background: 'var(--color-bg-card)', padding: 10, borderRadius: 6 }}>
          * El cálculo considera un factor de regulación en terminal del 15% y una capacidad estándar de 80 pasajeros por unidad.
        </div>
      </div>
    </div>
  )
}

import { Activity } from 'lucide-react'
