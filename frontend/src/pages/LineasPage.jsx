import React, { useState, useEffect } from 'react'
import Header from '../components/Layout/Header'
import { lineasApi } from '../services/api'
import { RefreshCw, MapPin, Truck, Route, Info } from 'lucide-react'
import DetalleLineaModal from '../components/Lineas/DetalleLineaModal'

export default function LineasPage() {
  const [lineas, setLineas] = useState([])
  const [loading, setLoading] = useState(true)
  const [lineaSeleccionada, setLineaSeleccionada] = useState(null)

  useEffect(() => {
    cargarLineas()
  }, [])

  const cargarLineas = async () => {
    setLoading(true)
    try {
      const res = await lineasApi.listar()
      setLineas(res.data)
    } catch (err) {
      console.error("Error cargando líneas:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header
        titulo="Líneas y Rutas"
        subtitulo={loading ? "Cargando datos reales..." : `${lineas.length} líneas operativas en el sistema CID`}
        acciones={
          <button className="btn btn-outline btn-sm" onClick={cargarLineas} id="btn-refresh-lineas">
            <RefreshCw size={14} className={loading ? "spinning" : ""} />
            Actualizar
          </button>
        }
      />
      <div className="page-content">
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
            <RefreshCw className="spinning" size={32} color="var(--color-accent-blue)" />
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 16 }}>
            {lineas.map(linea => (
              <div key={linea.id_linea} className="card" style={{
                borderLeft: `4px solid ${linea.color_hex || 'var(--color-accent-blue)'}`,
                display: 'grid',
                gridTemplateColumns: '80px 1fr auto',
                alignItems: 'center',
                gap: 20,
              }}>
                <div style={{
                  width: 72,
                  height: 72,
                  borderRadius: 'var(--radius-lg)',
                  background: `${linea.color_hex || '#3b82f6'}20`,
                  border: `2px solid ${linea.color_hex || '#3b82f6'}40`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Línea</span>
                  <span style={{ fontSize: '1.8rem', fontWeight: 800, color: linea.color_hex || 'var(--color-accent-blue)', lineHeight: 1 }}>
                    {linea.codigo}
                  </span>
                </div>
                
                <div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
                    {linea.descripcion}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginBottom: 8 }}>
                    {linea.empresa || 'Empresa de Transporte'}
                  </p>
                  <div style={{ display: 'flex', gap: 16 }}>
                    {[
                      { label: 'Distancia', value: `${linea.distancia_km || '—'} km`, icon: <Route size={12}/> },
                      { label: 'Empresa ID', value: linea.id_empresa, icon: <Truck size={12}/> },
                      { label: 'Estado', value: 'Operativo', icon: <MapPin size={12}/> },
                    ].map(stat => (
                      <div key={stat.label} style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                          {stat.icon} {stat.label}
                        </span>
                        <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{stat.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <button 
                    className="btn btn-outline btn-sm" 
                    onClick={() => setLineaSeleccionada(linea)}
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <Info size={14} /> Ver Detalle
                  </button>
                  <span className={`badge ${linea.estado ? 'badge-success' : 'badge-danger'}`}>
                    {linea.estado ? 'Activa' : 'Inactiva'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {lineaSeleccionada && (
        <DetalleLineaModal 
          linea={lineaSeleccionada} 
          onClose={() => setLineaSeleccionada(null)} 
        />
      )}
    </>
  )
}
