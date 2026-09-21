from sqlalchemy import create_engine, text
# MONITOREO_DB_URL=postgresql://jefe-CID:vmtdmt@monitoreo.vmt.gov.py:5432/bbdd-monitoreo-prod
engine = create_engine('postgresql://jefe-CID:vmtdmt@monitoreo.vmt.gov.py:5432/bbdd-monitoreo-prod')
with engine.connect() as conn:
    print("--- Sample GPS messages in MONITOREO DB ---")
    try:
        res = conn.execute(text("SELECT agency_id, route_id, identidad, latitude, longitude, fecha_hora FROM public.app_monitoreo_mensajeoperativo LIMIT 5"))
        for r in res:
            print(dict(r._asdict()))
    except Exception as e:
        print(f"Error: {e}")
