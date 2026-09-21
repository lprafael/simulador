from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Columns in public.catalogo_rutas ---")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'catalogo_rutas'"))
    for r in res:
        print(r[0])
    
    print("\n--- Columns in public.eots ---")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'eots'"))
    for r in res:
        print(r[0])
