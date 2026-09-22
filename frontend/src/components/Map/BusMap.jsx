import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import { MAP_TILE_CONFIG } from '../../config/map'

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Ícono personalizado para bus con indicador numérico de carga de pasajeros
const crearIconoBus = (color = '#3b82f6', estado = 'activo', pasajeros = null) => {
  const size = estado === 'bunching' ? 22 : 18
  
  let badgeColor = '#64748b' // neutro
  if (pasajeros !== null && pasajeros !== undefined) {
    const num = Number(pasajeros) || 0
    if (num >= 50) badgeColor = '#ef4444' // sobrecarga (rojo)
    else if (num >= 35) badgeColor = '#f59e0b' // alta (ámbar)
    else if (num >= 15) badgeColor = '#3b82f6' // media (azul)
    else if (num > 0) badgeColor = '#10b981' // baja/normal (verde)
  }

  const badgeHtml = (pasajeros !== null && pasajeros !== undefined) ? `
    <div style="
      background: ${badgeColor};
      color: white;
      font-size: 10px;
      font-weight: 800;
      padding: 0 4px;
      border-radius: 9px;
      border: 1.5px solid white;
      box-shadow: 0 2px 6px rgba(0,0,0,0.6);
      margin-bottom: 2px;
      letter-spacing: -0.5px;
      min-width: 18px;
      height: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
    ">${pasajeros}</div>
  ` : ''

  return L.divIcon({
    html: `
      <div style="display: flex; flex-direction: column; align-items: center; pointer-events: auto;">
        ${badgeHtml}
        <div style="
          width: ${size}px;
          height: ${size}px;
          background: ${color};
          border: 2px solid white;
          border-radius: 5px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 8px rgba(0,0,0,0.5), 0 0 ${estado === 'bunching' ? '12px' : '6px'} ${color}60;
          font-size: 10px;
          color: white;
          font-weight: bold;
        ">🚌</div>
      </div>
    `,
    className: '',
    iconSize: [32, 42],
    iconAnchor: [16, 32],
  })
}

// Ícono para paradero
const iconoParadero = (tipo) => {
  const colors = { INICIO: '#10b981', TERMINAL: '#f43f5e', INTERMEDIO: '#6b7280' }
  const color = colors[tipo] || '#6b7280'
  return L.divIcon({
    html: `<div style="
      width: 10px; height: 10px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 1px 4px rgba(0,0,0,0.5);
    "></div>`,
    className: '',
    iconSize: [10, 10],
    iconAnchor: [5, 5],
  })
}

// Bounds auto-updater
function BoundsUpdater({ buses }) {
  const map = useMap()
  useEffect(() => {
    if (buses && buses.length > 0) {
      const coords = buses.filter(b => b.lat && b.lon).map(b => [b.lat, b.lon])
      if (coords.length > 0) {
        try {
          map.fitBounds(coords, { padding: [40, 40], maxZoom: 14 })
        } catch (e) {}
      }
    }
  }, []) // Solo en mount
  return null
}

export default function BusMap({
  buses = [],
  paraderos = [],
  matrizOD = [],
  congestion = [],
  incidentesWaze = [],
  rutaCoords = null,
  posicionesSimuladas = [],
  height = '100%',
  center = [-25.2867, -57.6474], // Asunción, Paraguay
  zoom = 12,
}) {
  const [selectedBus, setSelectedBus] = useState(null)

  // Mapeo de paraderos para acceso rápido por ID
  const paraderosMap = React.useMemo(() => {
    const map = {}
    paraderos.forEach(p => { map[p.id_paradero] = p })
    return map
  }, [paraderos])

  // Iconos Waze
  const crearIconoWaze = (tipo) => {
    const emoji = tipo === 'ACCIDENT' ? '🚨' : '🚗'
    const color = tipo === 'ACCIDENT' ? '#ef4444' : '#f59e0b'
    return L.divIcon({
      html: `<div style="background: ${color}; padding: 4px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); font-size: 14px;">${emoji}</div>`,
      className: '',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    })
  }

  // Construir posiciones de buses desde simulación
  const busPositions = React.useMemo(() => {
    if (posicionesSimuladas.length > 0) {
      const byBus = {}
      posicionesSimuladas.forEach(pos => {
        byBus[pos.id_bus] = pos
      })
      return Object.values(byBus)
    }
    return buses.filter(b => b.lat && b.lon)
  }, [buses, posicionesSimuladas])

  // Procesar Heatmap de la Matriz OD
  const heatmapData = React.useMemo(() => {
    if (!matrizOD || matrizOD.length === 0) return []
    
    return matrizOD.map(item => {
      const p = paraderosMap[item.origen_id]
      if (p && p.lat && p.lon) {
        return {
          id: `heat-${item.origen_id}`,
          lat: p.lat,
          lon: p.lon,
          intensidad: item.cantidad_viajes,
          label: `Origen de ${item.cantidad_viajes} viajes`
        }
      }
      return null
    }).filter(Boolean)
  }, [matrizOD, paraderosMap])

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height, width: '100%' }}
      zoomControl={true}
    >
      {/* Capa base oscura */}
      <TileLayer
        url={MAP_TILE_CONFIG.url}
        attribution={MAP_TILE_CONFIG.attribution}
        maxZoom={MAP_TILE_CONFIG.maxZoom}
      />

      {/* Capa de Congestión Interna (Buses) */}
      {congestion.map(c => {
        const p = paraderosMap[c.id_ruta]
        if (!p) return null
        const color = c.nivel === 'ALTO' ? '#ef4444' : '#f59e0b'
        return (
          <Circle
            key={`cong-${c.id_ruta}`}
            center={[p.lat, p.lon]}
            radius={200}
            pathOptions={{ fillColor: color, fillOpacity: 0.3, color: color, weight: 1, dashArray: '5, 5' }}
          >
            <Popup>
              <strong>🚦 Tráfico (Estimado AVL)</strong><br/>
              Nivel: {c.nivel}<br/>
              Velocidad Promedio: {c.velocidad_promedio} km/h
            </Popup>
          </Circle>
        )
      })}

      {/* Capa de Waze (Alertas) */}
      {incidentesWaze.map((w, i) => (
        <Marker
          key={`waze-${i}`}
          position={[w.location.lat, w.location.lon]}
          icon={crearIconoWaze(w.type)}
        >
          <Popup>
            <div style={{ fontFamily: 'Inter, sans-serif' }}>
              <strong style={{ color: '#f59e0b' }}>🍊 Alerta Waze</strong><br/>
              <strong>{w.type === 'JAM' ? 'Embotellamiento' : 'Accidente'}</strong><br/>
              <span>📍 {w.street}</span><br/>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Fiabilidad: {w.reliability}/10</span>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Capa de Heatmap (Simulada con Círculos) */}
      {heatmapData.map(h => (
        <React.Fragment key={h.id}>
          {/* Círculo exterior difuminado */}
          <Circle
            center={[h.lat, h.lon]}
            radius={300 + (h.intensidad * 2)}
            pathOptions={{
              fillColor: '#f43f5e',
              fillOpacity: 0.2,
              color: 'transparent',
              weight: 0
            }}
          />
          {/* Núcleo caliente */}
          <Circle
            center={[h.lat, h.lon]}
            radius={100 + (h.intensidad / 2)}
            pathOptions={{
              fillColor: '#f43f5e',
              fillOpacity: 0.5,
              color: '#f43f5e',
              weight: 1
            }}
          >
            <Popup>
              <strong>Zona de Alta Demanda</strong><br/>
              {h.label}
            </Popup>
          </Circle>
        </React.Fragment>
      ))}

      {/* Geometría Real (GeoJSON) */}
      {rutaCoords && rutaCoords.type === 'LineString' && (
        <GeoJSON 
          data={rutaCoords} 
          style={{ color: '#3b82f6', weight: 4, opacity: 0.8 }} 
        />
      )}

      {/* Línea de ruta (Fallback / Coordenadas simples) */}
      {Array.isArray(rutaCoords) && rutaCoords.length > 1 && (
        <Polyline
          positions={rutaCoords}
          pathOptions={{
            color: '#3b82f6',
            weight: 3,
            opacity: 0.7,
            dashArray: '8, 4',
          }}
        />
      )}

      {/* Paraderos */}
      {paraderos.map((p) => (
        p.lat && p.lon && (
          <Marker
            key={`paradero-${p.id_paradero}`}
            position={[p.lat, p.lon]}
            icon={iconoParadero(p.tipo)}
          >
            <Popup>
              <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 150 }}>
                <strong>{p.nombre}</strong>
                <br />
                <span style={{ color: '#94a3b8', fontSize: 12 }}>
                  {p.tipo} · #{p.orden_ruta}
                </span>
              </div>
            </Popup>
          </Marker>
        )
      ))}

      {/* Buses */}
      {busPositions.map((bus) => {
        const bunching = bus.bunching || false
        const color = bunching ? '#f59e0b' : (bus.color || '#3b82f6')
        const pax = bus.carga_actual ?? bus.pasajeros_levantados ?? bus.pasajeros_abordo ?? bus.carga_pasajeros
        return (
          <Marker
            key={`bus-${bus.id_bus}`}
            position={[bus.lat, bus.lon]}
            icon={crearIconoBus(color, bunching ? 'bunching' : 'activo', pax)}
            eventHandlers={{ click: () => setSelectedBus(bus) }}
          >
            <Popup>
              <div style={{ fontFamily: 'Inter, sans-serif', minWidth: 200 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ fontWeight: 800, fontSize: '0.9rem' }}>
                    🚌 Bus {bus.interno || bus.id_bus}
                  </div>
                  {pax !== undefined && (
                    <span style={{
                      background: pax >= 45 ? '#ef4444' : pax >= 30 ? '#f59e0b' : '#10b981',
                      color: 'white',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      padding: '2px 7px',
                      borderRadius: '10px'
                    }}>
                      {pax} pax
                    </span>
                  )}
                </div>
                {bus.ruta_nombre && (
                  <div style={{ color: '#60a5fa', fontSize: '0.75rem', fontWeight: 600, marginBottom: 2 }}>
                    {bus.ruta_nombre}
                  </div>
                )}
                {bus.idrutaestacion && (
                  <div style={{ color: '#94a3b8', fontSize: 12 }}>
                    idrutaestacion: <strong style={{ color: 'white' }}>{bus.idrutaestacion}</strong> {bus.sentido ? `(${bus.sentido.toUpperCase()})` : ''}
                  </div>
                )}
                {bus.origen && bus.destino && (
                  <div style={{ color: '#cbd5e1', fontSize: 11, marginTop: 2 }}>
                    📍 {bus.origen} ➔ {bus.destino}
                  </div>
                )}
                {bus.id_trayecto && (
                  <div style={{ color: '#c084fc', fontSize: 11, marginTop: 2 }}>
                    Trayecto actual: <strong>{bus.id_trayecto}</strong>
                  </div>
                )}
                {bus.placa && <div style={{ color: '#94a3b8', fontSize: 12 }}>Placa: {bus.placa}</div>}
                <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 2 }}>
                  Vel: {bus.velocidad ?? bus.velocidad_kmh ?? '—'} km/h
                </div>
                {bunching && (
                  <div style={{ color: '#f59e0b', fontSize: 12, marginTop: 4, fontWeight: 600 }}>
                    ⚠ BUNCHING DETECTADO
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        )
      })}

      {/* Auto bounds */}
      {busPositions.length > 0 && <BoundsUpdater buses={busPositions} />}
    </MapContainer>
  )
}
