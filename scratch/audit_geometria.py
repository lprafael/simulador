from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Tables in geometria schema ---")
    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'geometria'"))
    for r in res:
        print(r[0])
