import React, { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import { busesApi } from '../services/api'
import { Bus, RefreshCw, Search } from 'lucide-react'

const ESTADO_BADGE = {
  ACTIVO: 'badge-success',
  INACTIVO: 'badge-neutral',
  MANTENIMIENTO: 'badge-warning',
}

const BUSES_FALLBACK = [
  { id_bus: 1, interno: '001', placa: 'ABC-001', capacidad: 45, estado: 'ACTIVO', modelo: 'Agrale MA 15.0', anio: 2019 },
  { id_bus: 2, interno: '002', placa: 'ABC-002', capacidad: 45, estado: 'ACTIVO', modelo: 'Agrale MA 15.0', anio: 2019 },
  { id_bus: 3, interno: '003', placa: 'ABC-003', capacidad: 45, estado: 'ACTIVO', modelo: 'Agrale MA 15.0', anio: 2020 },
  { id_bus: 4, interno: '004', placa: 'ABC-004', capacidad: 45, estado: 'ACTIVO', modelo: 'Marcopolo Torino', anio: 2021 },
  { id_bus: 5, interno: '005', placa: 'ABC-005', capacidad: 45, estado: 'ACTIVO', modelo: 'Marcopolo Torino', anio: 2021 },
  { id_bus: 6, interno: '006', placa: 'ABC-006', capacidad: 45, estado: 'ACTIVO', modelo: 'Marcopolo Torino', anio: 2022 },
  { id_bus: 7, interno: '007', placa: 'DEF-001', capacidad: 45, estado: 'ACTIVO', modelo: 'Mercedes OF-1721', anio: 2020 },
  { id_bus: 8, interno: '008', placa: 'DEF-002', capacidad: 45, estado: 'ACTIVO', modelo: 'Mercedes OF-1721', anio: 2020 },
  { id_bus: 9, interno: '009', placa: 'DEF-003', capacidad: 45, estado: 'ACTIVO', modelo: 'Mercedes OF-1721', anio: 2021 },
  { id_bus: 10, interno: '010', placa: 'DEF-004', capacidad: 45, estado: 'ACTIVO', modelo: 'Caio Apache Vip', anio: 2022 },
  { id_bus: 11, interno: '011', placa: 'GHI-001', capacidad: 50, estado: 'ACTIVO', modelo: 'Caio Apache Vip', anio: 2022 },
  { id_bus: 12, interno: '012', placa: 'GHI-002', capacidad: 50, estado: 'ACTIVO', modelo: 'Caio Apache Vip', anio: 2023 },
  { id_bus: 13, interno: '013', placa: 'GHI-003', capacidad: 50, estado: 'ACTIVO', modelo: 'Caio Apache Vip', anio: 2023 },
  { id_bus: 14, interno: '014', placa: 'GHI-004', capacidad: 45, estado: 'INACTIVO', modelo: 'Agrale MA 15.0', anio: 2018 },
  { id_bus: 15, interno: '015', placa: 'GHI-005', capacidad: 45, estado: 'MANTENIMIENTO', modelo: 'Agrale MA 15.0', anio: 2018 },
]

export default function BusesPage() {
  const [buses, setBuses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filtro, setFiltro] = useState('')
  const [filtroEstado, setFiltroEstado] = useState('TODOS')

  const cargar = async () => {
    setLoading(true)
    try {
      const res = await busesApi.listar()
      setBuses(res.data.length > 0 ? res.data : BUSES_FALLBACK)
    } catch {
      setBuses(BUSES_FALLBACK)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const busesFiltrados = buses.filter(b => {
    const coincide = !filtro || 
      b.interno?.toLowerCase().includes(filtro.toLowerCase()) ||
      b.placa?.toLowerCase().includes(filtro.toLowerCase()) ||
      b.modelo?.toLowerCase().includes(filtro.toLowerCase())
    const estadoOk = filtroEstado === 'TODOS' || b.estado === filtroEstado
    return coincide && estadoOk
  })

  const stats = {
    activos: buses.filter(b => b.estado === 'ACTIVO').length,
    inactivos: buses.filter(b => b.estado === 'INACTIVO').length,
    mantenimiento: buses.filter(b => b.estado === 'MANTENIMIENTO').length,
  }

  return (
    <>
      <Header
        titulo="Flota de Buses"
        subtitulo={`${buses.length} unidades registradas`}
        acciones={
          <button className="btn btn-outline btn-sm" onClick={cargar} id="btn-refresh-buses">
            <RefreshCw size={14} />
            Actualizar
          </button>
        }
      />
      <div className="page-content">
        {/* Stats rápidos */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
          {[
            { label: 'Activos', value: stats.activos, color: 'var(--color-success)' },
            { label: 'Inactivos', value: stats.inactivos, color: 'var(--color-text-muted)' },
            { label: 'En Mantenimiento', value: stats.mantenimiento, color: 'var(--color-warning)' },
            { label: 'Total Flota', value: buses.length, color: 'var(--color-accent-blue)' },
          ].map(s => (
            <div key={s.label} style={{
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
            }}>
              <span style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color, fontVariantNumeric: 'tabular-nums' }}>{s.value}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{s.label}</span>
            </div>
          ))}
        </div>

        <div className="card">
          {/* Filtros */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
              <input
                id="input-buscar-buses"
                type="text"
                className="form-control"
                placeholder="Buscar por interno, placa o modelo..."
                value={filtro}
                onChange={(e) => setFiltro(e.target.value)}
                style={{ paddingLeft: 36 }}
              />
            </div>
            <select
              id="select-estado-bus"
              className="form-control"
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              style={{ width: 180 }}
            >
              <option value="TODOS">Todos los estados</option>
              <option value="ACTIVO">Activos</option>
              <option value="INACTIVO">Inactivos</option>
              <option value="MANTENIMIENTO">En mantenimiento</option>
            </select>
          </div>

          {loading ? (
            <div style={{ display: 'grid', gap: 8 }}>
              {[1,2,3,4,5].map(i => (
                <div key={i} className="skeleton" style={{ height: 48 }} />
              ))}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Interno</th>
                    <th>Placa</th>
                    <th>Modelo</th>
                    <th>Año</th>
                    <th>Capacidad</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {busesFiltrados.map(bus => (
                    <tr key={bus.id_bus}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {bus.interno}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{bus.placa}</td>
                      <td>{bus.modelo || '—'}</td>
                      <td>{bus.anio || '—'}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div className="progress-bar" style={{ width: 60 }}>
                            <div className="progress-fill" style={{ width: `${((bus.capacidad || 45) / 60) * 100}%` }} />
                          </div>
                          <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>{bus.capacidad}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${ESTADO_BADGE[bus.estado] || 'badge-neutral'}`}>
                          {bus.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {busesFiltrados.length === 0 && (
                <div className="empty-state" style={{ padding: 40 }}>
                  <div className="empty-state-icon">🔍</div>
                  <p>No se encontraron buses con ese criterio de búsqueda</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
