import React from 'react'
import { Bell, RefreshCw } from 'lucide-react'

export default function Header({ titulo, subtitulo, acciones }) {
  return (
    <header style={{
      position: 'fixed',
      top: 0,
      right: 0,
      left: 'var(--sidebar-width)',
      height: 'var(--header-height)',
      background: 'rgba(10,15,30,0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      zIndex: 90,
    }}>
      <div>
        <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1.2 }}>
          {titulo}
        </h1>
        {subtitulo && (
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
            {subtitulo}
          </p>
        )}
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {acciones}
        
        <div style={{
          width: 1,
          height: 24,
          background: 'var(--color-border)',
          margin: '0 4px',
        }} />
        
        <div style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.8rem',
          fontWeight: 700,
          color: 'white',
        }}>
          TP
        </div>
      </div>
    </header>
  )
}
