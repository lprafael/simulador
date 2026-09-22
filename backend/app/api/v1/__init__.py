from fastapi import APIRouter
from . import buses, lineas, paraderos, posiciones, simulacion, kpi, predicciones, unidades_funcionales, planning, trafico, carga_buses

router = APIRouter()

router.include_router(buses.router, prefix="/buses", tags=["Buses"])
router.include_router(lineas.router, prefix="/lineas", tags=["Líneas"])
router.include_router(unidades_funcionales.router, prefix="/unidades-funcionales", tags=["UFs"])
router.include_router(planning.router, prefix="/planning", tags=["Planificación"])
router.include_router(paraderos.router, prefix="/paraderos", tags=["Paraderos"])
router.include_router(posiciones.router, prefix="/posiciones", tags=["Posiciones GPS"])
router.include_router(simulacion.router, prefix="/simulacion", tags=["Simulación"])
router.include_router(kpi.router, prefix="/kpi", tags=["KPIs"])
router.include_router(predicciones.router, prefix="/predicciones", tags=["Predicciones"])
router.include_router(trafico.router, prefix="/trafico", tags=["Tráfico & What-If"])
router.include_router(carga_buses.router, prefix="/carga-buses", tags=["Carga de Buses & Trayectos"])
