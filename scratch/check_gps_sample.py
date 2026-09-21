from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Sample GPS messages ---")
    res = conn.execute(text("SELECT agency_id, route_id, identidad, latitude, longitude FROM public.app_monitoreo_mensajeoperativo LIMIT 5"))
    for r in res:
        print(dict(r._asdict()))
