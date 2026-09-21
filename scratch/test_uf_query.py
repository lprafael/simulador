from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Querying UFs ---")
    query = text("SELECT id_uf, nombre_uf FROM gestion_uf.unidades_funcionales")
    res = conn.execute(query)
    rows = [dict(r._asdict()) for r in res]
    print(f"Found {len(rows)} UFs")
    for r in rows:
        print(r)
