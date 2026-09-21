import React, { useState, useEffect } from 'react'
import { Play, RefreshCw, Sliders, AlertCircle, CheckCircle2, Clock } from 'lucide-react'
import { simulacionApi, lineasApi } from '../../services/api'
import { useSimulacionStore } from '../../store'

export default function SimulacionPanel({ onResultados }) {
  const { parametros, setParametros, estadoSimulacion, iniciarSimulacion, completarSimulacion, resetSimulacion } = useSimulacionStore()
  const [error, setError] = useState(null)
  const [modoDemo, setModoDemo] = useState(false)
  const [lineasReales, setLineasReales] = useState([])
  const [cargandoLineas, setCargandoLineas] = useState(false)

  // Cargar líneas reales al cambiar modo o al montar
  useEffect(() => {
    const fetchLineas = async () => {
      if (!modoDemo) {
        setCargandoLineas(true)
        try {
          const res = await lineasApi.listar()
          setLineasReales(res.data)
          if (res.data.length > 0) {
            setParametros({ id_linea: res.data[0].id_linea })
          }
        } catch (err) {
          console.error("Error cargando líneas reales:", err)
          setError("No se pudieron cargar las líneas reales del CID.")
        } finally {
          setCargandoLineas(false)
        }
      } else {
        setParametros({ id_linea: 1 })
      }
    }
    
    fetchLineas()

    // Polling si no hay líneas reales aún
    const interval = setInterval(() => {
      if (!modoDemo) {
        setLineasReales(prev => {
          if (prev.length === 0) fetchLineas()
          return prev
        })
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [modoDemo])

  const lineasVisibles = modoDemo ? [
    { id_linea: 1, numero_linea: '30', nombre_comercial: 'Línea 30 - Demo' },
    { id_linea: 2, numero_linea: '31', nombre_comercial: 'Línea 31 - Demo' },
  ] : lineasReales

  const estaEjecutando = estadoSimulacion === 'EJECUTANDO' || estadoSimulacion === 'corriendo'
  const estaCompletado = estadoSimulacion === 'COMPLETADO' || estadoSimulacion === 'completado'

  const ejecutar = async () => {
    setError(null)
    iniciarSimulacion()

    try {
      let resultados = null

      if (modoDemo) {
        const respuesta = await simulacionApi.ejecutarDemo()
        resultados = respuesta.data
      } else {
        const respuesta = await simulacionApi.crear({
          ...parametros,
          nombre: `Simulación ${new Date().toLocaleString()}`
        })
        const sim = respuesta.data
        const idSim = sim?.id_simulacion

        if (idSim) {
          // Polling breve hasta que la simulación termine en background (normalmente < 1s)
          let intentos = 0
          while (intentos < 30) {
            await new Promise(r => setTimeout(r, 600))
            const check = await simulacionApi.obtener(idSim)
            if (check.data?.estado === 'COMPLETADO' && check.data?.resultado_resumen) {
              resultados = {
                id_simulacion: idSim,
                nombre: check.data.nombre,
                estado: 'COMPLETADO',
                kpis: check.data.resultado_resumen,
                ...check.data.resultado_resumen,
              }
              break
            } else if (check.data?.estado === 'ERROR') {
              throw new Error('La simulación reportó un error durante la ejecución')
            }
            intentos++
          }
        }

        if (!resultados) {
          resultados = respuesta.data || {}
        }
      }
      
      completarSimulacion(resultados)
      if (onResultados) onResultados(resultados)
    } catch (err) {
      console.error('Error al ejecutar simulación:', err)
      
      let mensajeError = 'Error al conectar con el servidor'
      
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        mensajeError = 'La simulación está tardando demasiado (tiempo de espera agotado). El proceso continuará en segundo plano, puede revisar los resultados más tarde.'
      } else if (err.response?.data?.detail) {
        mensajeError = err.response.data.detail
      } else if (err.message) {
        mensajeError = err.message
      }
      
      setError(mensajeError)
      resetSimulacion()
    }
  }

  return (
    <div className="space-y-6 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2 text-white">
          <Sliders className="w-5 h-5 text-blue-500" />
          CONFIGURAR SIMULACIÓN
        </h2>
        <div className="flex items-center gap-2">
          <input 
            type="checkbox" 
            id="modoDemo" 
            checked={modoDemo}
            onChange={(e) => setModoDemo(e.target.checked)}
            className="w-4 h-4 rounded border-gray-700 bg-slate-800 text-blue-500"
          />
          <label htmlFor="modoDemo" className="text-sm text-slate-400">Demo (sin BD)</label>
        </div>
      </div>

      {/* Selector de Línea */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-blue-400 uppercase tracking-wider">Línea</label>
        <select
          value={parametros.id_linea || ''}
          onChange={(e) => setParametros({ id_linea: parseInt(e.target.value) })}
          disabled={cargandoLineas || estadoSimulacion === 'EJECUTANDO'}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
        >
          {cargandoLineas && <option>Cargando líneas...</option>}
          {lineasVisibles.map(l => (
            <option key={l.id_linea} value={l.id_linea}>
              {l.numero_linea} — {l.nombre_comercial}
            </option>
          ))}
        </select>
      </div>

      {/* Parámetros */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-500 uppercase">N° Buses</label>
          <input
            type="number"
            value={parametros.num_buses}
            onChange={(e) => setParametros({ num_buses: parseInt(e.target.value) })}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
          />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Duración (min)</label>
          <input
            type="number"
            value={parametros.duracion_sim_min}
            onChange={(e) => setParametros({ duracion_sim_min: parseInt(e.target.value) })}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
          />
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 p-3 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-200">{error}</p>
        </div>
      )}

      {/* Botón de Acción */}
      <button
        onClick={ejecutar}
        disabled={estaEjecutando || (lineasVisibles.length === 0 && !modoDemo)}
        className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-3 transition-all ${
          estaEjecutando
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20 active:scale-95'
        }`}
      >
        {estaEjecutando ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            SIMULANDO...
          </>
        ) : (
          <>
            <Play className="w-5 h-5 fill-current" />
            INICIAR SIMULACIÓN
          </>
        )}
      </button>

      {/* Estado */}
      {estaCompletado && (
        <div className="flex items-center justify-center gap-2 text-green-400 animate-bounce">
          <CheckCircle2 className="w-5 h-5" />
          <span className="text-sm font-bold">¡Simulación finalizada!</span>
        </div>
      )}
    </div>
  )
}
