import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Map, Activity, Play, Bus,
  Route, BarChart2, Settings, ChevronLeft, ChevronRight,
  Zap, Radio, Database, ArrowLeftRight, Users
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/mapa', icon: Map, label: 'Mapa en Vivo' },
  { to: '/carga-buses', icon: Users, label: 'Carga de Buses' },
  { to: '/trafico-whatif', icon: ArrowLeftRight, label: 'Tránsito & What-If' },
  { to: '/simulacion', icon: Play, label: 'Simulación TP' },
  { to: '/predicciones', icon: Zap, label: 'IA & Predicciones' },
  { to: '/kpis', icon: BarChart2, label: 'KPIs Operacionales' },
  { to: '/buses', icon: Bus, label: 'Flota de Buses' },
  { to: '/lineas', icon: Route, label: 'Líneas y Rutas' },
  { to: '/simular-carga-uf', icon: Database, label: 'Simular Carga UF' },
  { to: '/eventos', icon: Activity, label: 'Eventos' },
]

export default function Sidebar({ wsConectado }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside style={{
      position: 'fixed',
      top: 0,
      left: 0,
      height: '100vh',
      width: collapsed ? '72px' : 'var(--sidebar-width)',
      background: 'var(--color-bg-secondary)',
      borderRight: '1px solid var(--color-border)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 100,
      transition: 'width var(--transition-normal)',
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        padding: '20px 16px',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        minHeight: 'var(--header-height)',
      }}>
        <div style={{
          width: 36,
          height: 36,
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 0 20px rgba(59,130,246,0.3)',
        }}>
          <Zap size={18} color="white" />
        </div>
        {!collapsed && (
          <div style={{ animation: 'fadeIn 0.2s ease' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1.2 }}>
              SimTransit
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
              Microsimulador TP
            </div>
          </div>
        )}
      </div>

      {/* Estado WS */}
      {!collapsed && (
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: wsConectado ? 'rgba(16,185,129,0.08)' : 'rgba(244,63,94,0.08)',
            padding: '8px 12px',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${wsConectado ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}`,
          }}>
            <div style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: wsConectado ? 'var(--color-success)' : 'var(--color-danger)',
              animation: wsConectado ? 'pulse-dot 2s infinite' : 'none',
            }} />
            <span style={{ fontSize: '0.75rem', color: wsConectado ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 500 }}>
              {wsConectado ? 'Tiempo Real Activo' : 'Sin Conexión RT'}
            </span>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }} className="sidebar-scroll">
        {navItems.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              marginBottom: 4,
              textDecoration: 'none',
              color: isActive ? 'var(--color-accent-blue-bright)' : 'var(--color-text-secondary)',
              background: isActive ? 'rgba(59,130,246,0.12)' : 'transparent',
              border: `1px solid ${isActive ? 'rgba(59,130,246,0.2)' : 'transparent'}`,
              transition: 'all var(--transition-fast)',
              overflow: 'hidden',
              whiteSpace: 'nowrap',
            })}
            onMouseEnter={(e) => {
              if (!e.currentTarget.style.background.includes('rgba(59,130,246,0.12)')) {
                e.currentTarget.style.background = 'rgba(255,255,255,0.04)'
                e.currentTarget.style.color = 'var(--color-text-primary)'
              }
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.style.background.includes('rgba(59,130,246,0.12)')) {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = 'var(--color-text-secondary)'
              }
            }}
          >
            <Icon size={18} style={{ flexShrink: 0 }} />
            {!collapsed && <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse Button */}
      <div style={{ padding: '12px 8px', borderTop: '1px solid var(--color-border)' }}>
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            padding: '10px',
            background: 'transparent',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  )
}
