import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // 5 minutos para simulaciones pesadas
})

// ─── Buses ───
export const busesApi = {
  listar: (params = {}) => api.get('/buses', { params }),
  obtener: (id) => api.get(`/buses/${id}`),
  crear: (data) => api.post('/buses', data),
  actualizar: (id, data) => api.put(`/buses/${id}`, data),
}

// ─── Líneas ───
export const lineasApi = {
  listar: () => api.get('/lineas'),
  obtener: (id) => api.get(`/lineas/${id}`),
  obtenerRutas: (id_linea) => api.get(`/lineas/${id_linea}/rutas`),
  obtenerGeometria: (ruta_hex) => api.get(`/lineas/geometria/${ruta_hex}`),
}

// ─── Unidades Funcionales ───
export const ufApi = {
  listar: () => api.get('/unidades-funcionales'),
  listarLineas: (id_uf) => api.get(`/unidades-funcionales/${id_uf}/lineas`),
  simularCarga: (id_uf, fecha, params = {}) =>
    api.get(`/unidades-funcionales/${id_uf}/simular-carga`, { params: { fecha, ...params } }),
  obtenerReferenciasGeograficas: (id_uf) =>
    api.get(`/unidades-funcionales/${id_uf}/referencias-geograficas`),
}

// ─── Paraderos ───
export const paraderosApi = {
  listar: (id_ruta = null) => api.get('/paraderos', { params: id_ruta ? { id_ruta } : {} }),
}

// ─── KPIs ───
export const kpiApi = {
  resumen: () => api.get('/kpi/resumen'),
  headway: (id_linea) => api.get(`/kpi/headway/${id_linea}`),
  simulacion: (id_sim) => api.get(`/kpi/simulacion/${id_sim}`),
  eventosRecientes: (limite = 20, tipo = null) =>
    api.get('/kpi/eventos/recientes', { params: { limite, ...(tipo && { tipo }) } }),
  congestion: () => api.get('/kpi/congestion'),
  incidentesWaze: () => api.get('/kpi/incidentes-waze'),
}

// ─── Simulación ───
export const simulacionApi = {
  listar: () => api.get('/simulacion'),
  obtener: (id) => api.get(`/simulacion/${id}`),

  ejecutarDemo: () => api.post('/simulacion/demo'),

  crear: (data) => api.post('/simulacion/', {
    nombre: data.nombre || `Simulación ${new Date().toLocaleTimeString()}`,
    parametros: {
      id_linea: data.id_linea,
      headway_min: data.headway_min,
      velocidad_kmh: data.velocidad_kmh,
      num_buses: data.num_buses,
      duracion_sim_min: data.duracion_sim_min,
      tasa_pasajeros_por_min: data.tasa_pasajeros_por_min,
      tiempo_parada_base_min: data.tiempo_parada_base_min || 0.5,
      semilla_aleatoria: data.semilla_aleatoria || null,
    }
  }),
}

// ─── Predicciones ───
export const prediccionesApi = {
  getEta: (id_bus) => api.get(`/predicciones/eta/${id_bus}`),
  getOptimizacion: (id_linea, demanda) =>
    api.get(`/predicciones/optimizacion/${id_linea}`, { params: { demanda } }),
}

// ─── Planificación ───
export const planningApi = {
  optimizarFlota: (id_linea, frecuencia) =>
    api.get(`/planning/optimizar-flota/${id_linea}`, { params: { frecuencia } }),
}

// ─── Tráfico y What-If ───
export const traficoApi = {
  municipios: () => api.get('/trafico/municipios'),
  redVial: (municipio, franja = 'PICO_MANANA') =>
    api.get('/trafico/red-vial', { params: { municipio, franja } }),
  simularWhatIf: (data) => api.post('/trafico/simular-whatif', data),
  wazeLive: (municipio = null) =>
    api.get('/trafico/waze/live', { params: municipio ? { municipio } : {} }),
  guardarEscenario: (data) => api.post('/trafico/guardar-escenario', data),
  listarEscenarios: () => api.get('/trafico/escenarios'),
}

export default api
