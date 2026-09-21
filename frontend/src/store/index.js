import { create } from 'zustand'

export const useSimulacionStore = create((set, get) => ({
  // Estado simulación
  simulacionActiva: null,
  estadoSimulacion: 'idle', // idle | configurando | corriendo | completado | error
  progreso: 0,
  
  // Resultados
  resultados: null,
  posicionesSimuladas: [],
  eventosSimulacion: [],
  kpisSimulacion: null,
  
  // Parámetros
  parametros: {
    id_linea: 1,
    headway_min: 8,
    velocidad_kmh: 25,
    num_buses: 5,
    duracion_sim_min: 90,
    tasa_pasajeros_por_min: 15,
    tiempo_parada_base_min: 0.5,
    semilla_aleatoria: null,
  },
  
  // WebSocket
  wsConectado: false,
  
  // Acciones
  setParametros: (params) => set((state) => ({
    parametros: { ...state.parametros, ...params }
  })),
  
  iniciarSimulacion: () => set({ estadoSimulacion: 'corriendo', progreso: 0, resultados: null }),
  
  completarSimulacion: (resultados) => set({
    estadoSimulacion: 'completado',
    progreso: 100,
    resultados,
    kpisSimulacion: resultados?.kpis || null,
    posicionesSimuladas: resultados?.posiciones || [],
    eventosSimulacion: resultados?.eventos || [],
  }),
  
  resetSimulacion: () => set({
    estadoSimulacion: 'idle',
    progreso: 0,
    resultados: null,
    posicionesSimuladas: [],
    eventosSimulacion: [],
    kpisSimulacion: null,
  }),
  
  setWsConectado: (estado) => set({ wsConectado: estado }),
  addPosicion: (pos) => set((state) => ({
    posicionesSimuladas: [...state.posicionesSimuladas.slice(-500), pos]
  })),
}))


export const useBusStore = create((set, get) => ({
  buses: [],
  busesActivos: {},
  lineaSeleccionada: null,
  posicionesRealtime: {},
  
  setBuses: (buses) => set({ buses }),
  setLineaSeleccionada: (id) => set({ lineaSeleccionada: id }),
  
  actualizarPosicion: (idBus, posicion) => set((state) => ({
    posicionesRealtime: {
      ...state.posicionesRealtime,
      [idBus]: { ...posicion, ultimaActualizacion: Date.now() }
    }
  })),
  
  marcarBusActivo: (idBus, estado) => set((state) => ({
    busesActivos: { ...state.busesActivos, [idBus]: estado }
  })),
}))
