from sqlalchemy import create_engine, text
cid_engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
mon_engine = create_engine('postgresql://jefe-CID:vmtdmt@monitoreo.vmt.gov.py:5432/bbdd-monitoreo-prod')

with cid_engine.connect() as cid_conn:
    print("--- CID Agency IDs ---")
    res = cid_conn.execute(text("SELECT eot_id, eot_nombre, id_eot_vmt_hex FROM public.eots LIMIT 5"))
    for r in res:
        print(dict(r._asdict()))

with mon_engine.connect() as mon_conn:
    print("\n--- Monitoreo Agency IDs ---")
    res = mon_conn.execute(text("SELECT DISTINCT agency_id FROM public.app_monitoreo_mensajeoperativo LIMIT 5"))
    for r in res:
        print(dict(r._asdict()))
