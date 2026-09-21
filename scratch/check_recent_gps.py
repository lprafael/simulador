from sqlalchemy import create_engine, text
engine = create_engine('postgresql://jefe-CID:vmtdmt@monitoreo.vmt.gov.py:5432/bbdd-monitoreo-prod')
with engine.connect() as conn:
    print("--- Most recent GPS date ---")
    res = conn.execute(text("SELECT MAX(fecha_hora) FROM public.app_monitoreo_mensajeoperativo"))
    print(res.fetchone()[0])
    
    print("\n--- Sample agencies and routes in GPS table ---")
    res = conn.execute(text("SELECT DISTINCT agency_id, route_id FROM public.app_monitoreo_mensajeoperativo WHERE fecha_hora >= CURRENT_DATE - INTERVAL '7 days' LIMIT 10"))
    for r in res:
        print(dict(r._asdict()))
