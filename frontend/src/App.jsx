import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Layout/Sidebar'
import Dashboard from './pages/Dashboard'
import MapaPage from './pages/MapaPage'
import SimulacionPage from './pages/SimulacionPage'
import PrediccionesPage from './pages/PrediccionesPage'
import KpisPage from './pages/KpisPage'
import BusesPage from './pages/BusesPage'
import LineasPage from './pages/LineasPage'
import EventosPage from './pages/EventosPage'
import SimulacionCargaUF from './pages/SimulacionCargaUF'
import TraficoWhatIfPage from './pages/TraficoWhatIfPage'
import { useSimulacionStore, useBusStore } from './store'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export default function App() {
  const [wsConectado, setWsConectado] = useState(false)
  const { setWsConectado: setStoreWs, addPosicion } = useSimulacionStore()
  const { actualizarPosicion } = useBusStore()

  // Conectar WebSocket
  useEffect(() => {
    let ws = null
    let reconnectTimer = null
    let pingInterval = null
    let isDisposed = false
    
    const conectar = () => {
      if (isDisposed) return
      
      try {
        ws = new WebSocket(`${WS_URL}/ws/posiciones`)
        
        ws.onopen = () => {
          if (isDisposed) {
            ws.close()
            return
          }
          setWsConectado(true)
          setStoreWs(true)
          console.log('✅ WebSocket conectado a:', `${WS_URL}/ws/posiciones`)
        }
        
        ws.onmessage = (event) => {
          if (isDisposed) return
          try {
            const msg = JSON.parse(event.data)
            
            if (msg.tipo === 'POSICION_GPS' && msg.datos) {
              actualizarPosicion(msg.datos.id_bus, msg.datos)
              addPosicion(msg.datos)
            }
            
            if (msg.tipo === 'HEARTBEAT' && msg.posiciones) {
              msg.posiciones.forEach(pos => {
                actualizarPosicion(pos.id_bus, pos)
              })
            }
          } catch (e) {
            console.warn('Error parsing WS message:', e)
          }
        }
        
        ws.onclose = () => {
          setWsConectado(false)
          setStoreWs(false)
          if (!isDisposed) {
            clearTimeout(reconnectTimer)
            reconnectTimer = setTimeout(conectar, 5000)
          }
        }
        
        ws.onerror = () => {
          setWsConectado(false)
          setStoreWs(false)
        }
        
        // Heartbeat cada 25 segundos
        clearInterval(pingInterval)
        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ tipo: 'PING' }))
          }
        }, 25000)
      } catch (e) {
        console.warn('WebSocket no disponible:', e.message)
        if (!isDisposed) {
          reconnectTimer = setTimeout(conectar, 10000)
        }
      }
    }
    
    conectar()
    
    return () => {
      isDisposed = true
      clearTimeout(reconnectTimer)
      clearInterval(pingInterval)
      if (ws) {
        ws.onopen = null
        ws.onmessage = null
        ws.onerror = null
        ws.onclose = null
        if (ws.readyState === WebSocket.OPEN) {
          ws.close()
        } else if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            try { ws.close() } catch (err) {}
          }
        }
      }
    }
  }, [])

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="app-layout">
        <Sidebar wsConectado={wsConectado} />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/mapa" element={<MapaPage />} />
            <Route path="/simulacion" element={<SimulacionPage />} />
            <Route path="/predicciones" element={<PrediccionesPage />} />
            <Route path="/kpis" element={<KpisPage />} />
            <Route path="/buses" element={<BusesPage />} />
            <Route path="/lineas" element={<LineasPage />} />
            <Route path="/eventos" element={<EventosPage />} />
            <Route path="/simular-carga-uf" element={<SimulacionCargaUF />} />
            <Route path="/trafico-whatif" element={<TraficoWhatIfPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
