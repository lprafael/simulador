from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Tables in gestion_uf ---")
    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'gestion_uf'"))
    for r in res:
        print(r[0])
    
    print("\n--- Columns in gestion_uf.unidades_funcionales ---")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'gestion_uf' AND table_name = 'unidades_funcionales'"))
    for r in res:
        print(r[0])
