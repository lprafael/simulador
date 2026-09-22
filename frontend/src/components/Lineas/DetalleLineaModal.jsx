import React, { useState, useEffect } from 'react'
import { X, Route, Truck, MapPin, Play, RefreshCw } from 'lucide-react'
import { lineasApi } from '../../services/api'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import L from 'leaflet'
import { MAP_TILE_CONFIG } from '../../config/map'
import { useNavigate } from 'react-router-dom'
import { useSimulacionStore } from '../../store'

function GeoJsonFitBounds({ geojson }) {
  const map = useMap()
  useEffect(() => {
    if (geojson) {
      try {
        const layer = L.geoJSON(geojson)
        map.fitBounds(layer.getBounds(), { padding: [30, 30] })
      } catch (e) {
        console.warn('Error fitting bounds:', e)
      }
    }
  }, [geojson, map])
  return null
}

export default function DetalleLineaModal({ linea, onClose }) {
  const [rutas, setRutas] = useState([])
  const [rutaSel, setRutaSel] = useState(null)
  const [geoJSON, setGeoJSON] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingGeom, setLoadingGeom] = useState(false)
  const navigate = useNavigate()
  const { setParametros } = useSimulacionStore()

  useEffect(() => {
    if (!linea) return
    const cargarRutas = async () => {
      setLoading(true)
      try {
        const res = await lineasApi.obtenerRutas(linea.id_linea)
        setRutas(res.data)
        if (res.data.length > 0) {
          seleccionarRuta(res.data[0])
        }
      } catch (err) {
        console.error('Error cargando rutas de línea:', err)
      } finally {
        setLoading(false)
      }
    }
    cargarRutas()
  }, [linea])

  const seleccionarRuta = async (r) => {
    setRutaSel(r)
    setLoadingGeom(true)
    try {
      const res = await lineasApi.obtenerGeometria(r.ruta_hex)
      setGeoJSON(res.data)
    } catch (err) {
      console.error('Error cargando geometría de ruta:', err)
      setGeoJSON(null)
    } finally {
      setLoadingGeom(false)
    }
  }

  const handleLanzarSimulacion = () => {
    setParametros({ id_linea: linea.id_linea })
    onClose()
    navigate('/simulacion')
  }

  if (!linea) return null

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: 20
    }}>
      <div style={{
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        width: '100%',
        maxWidth: 800,
        maxHeight: '90vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0,0,0,0.5)'
      }}>
        {/* Header Modal */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--color-bg-surface)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-md)',
              background: `${linea.color_hex || '#3b82f6'}25`,
              border: `2px solid ${linea.color_hex || '#3b82f6'}50`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.2rem',
              color: linea.color_hex || 'var(--color-accent-blue)'
            }}>
              {linea.codigo}
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                {linea.nombre || linea.descripcion || `Línea ${linea.codigo}`}
              </h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                {linea.empresa || 'Empresa de Transporte Operadora'}
              </span>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="btn btn-outline btn-sm"
            style={{ padding: 6, borderRadius: '50%' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body Modal */}
        <div style={{ padding: 24, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Selector de Itinerarios */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8 }}>
              ITINERARIOS REGISTRADOS EN SISCID ({rutas.length})
            </label>
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text-muted)' }}>
                <RefreshCw size={14} className="spinning" /> Cargando itinerarios...
              </div>
            ) : rutas.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                No se registraron itinerarios específicos para esta línea.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {rutas.map(r => {
                  const activa = rutaSel?.ruta_hex === r.ruta_hex
                  return (
                    <button
                      key={r.ruta_hex}
                      onClick={() => seleccionarRuta(r)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${activa ? 'var(--color-accent-blue)' : 'var(--color-border)'}`,
                        background: activa ? 'rgba(59, 130, 246, 0.15)' : 'var(--color-bg-surface)',
                        color: activa ? 'var(--color-accent-blue)' : 'var(--color-text-primary)',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: activa ? 700 : 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                    >
                      <Route size={14} />
                      <span>{r.sentido ? r.sentido.toUpperCase() : 'RUTA'}: {r.identificacion || r.ruta_hex.substring(0, 10)}</span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Mapa de visualización del trazado GeoJSON */}
          <div style={{ height: 280, borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--color-border)', position: 'relative' }}>
            {loadingGeom && (
              <div style={{
                position: 'absolute',
                inset: 0,
                background: 'rgba(0,0,0,0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 400,
                color: 'white',
                gap: 8
              }}>
                <RefreshCw size={18} className="spinning" /> Cargando trazado GeoJSON...
              </div>
            )}
            <MapContainer
              center={[-25.2867, -57.6474]}
              zoom={12}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer {...MAP_TILE_CONFIG} />
              {geoJSON && (
                <>
                  <GeoJSON
                    key={rutaSel?.ruta_hex}
                    data={geoJSON}
                    style={{
                      color: linea.color_hex || '#3b82f6',
                      weight: 4,
                      opacity: 0.85
                    }}
                  />
                  <GeoJsonFitBounds geojson={geoJSON} />
                </>
              )}
            </MapContainer>
          </div>

          {/* Datos Operacionales de la Línea */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            <div style={{ background: 'var(--color-bg-surface)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>CÓDIGO CATÁLOGO</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{linea.codigo}</div>
            </div>
            <div style={{ background: 'var(--color-bg-surface)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>LONGITUD ESTIMADA</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{linea.distancia_km ? `${linea.distancia_km} km` : '18.4 km'}</div>
            </div>
            <div style={{ background: 'var(--color-bg-surface)', padding: 12, borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>ESTADO OPERACIONAL</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-success)' }}>Activa (SisCID)</div>
            </div>
          </div>
        </div>

        {/* Footer Modal */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--color-border)',
          background: 'var(--color-bg-surface)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 12
        }}>
          <button className="btn btn-outline" onClick={onClose}>
            Cerrar
          </button>
          <button className="btn btn-primary" onClick={handleLanzarSimulacion}>
            <Play size={15} /> Simular Operación de esta Línea
          </button>
        </div>
      </div>
    </div>
  )
}
