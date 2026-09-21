from sqlalchemy import create_engine, text
engine = create_engine('postgresql://cid_admin_user:vmtdmtcidccm@168.90.177.232:2024/bbdd-monitoreo-cid')
with engine.connect() as conn:
    print("--- Querying Complex UFs ---")
    query = text("""
            SELECT 
                uf.id_uf,
                uf.nombre_uf as uf_nombre,
                c.nombre as consorcio_nombre,
                e.eot_nombre as empresa_nombre,
                e.id_eot_vmt_hex as codigo_eot
            FROM gestion_uf.unidades_funcionales uf
            LEFT JOIN gestion_uf.contratos ct ON uf.id_uf = ct.id_uf
            LEFT JOIN gestion_uf.composicion_consorcio cc ON ct.id_eot = cc.id_eot
            LEFT JOIN public.consorcios c ON cc.id_consorcio = c.id_consorcio
            LEFT JOIN public.eots e ON cc.id_eot = e.eot_id
    """)
    try:
        res = conn.execute(query)
        rows = [dict(r._asdict()) for r in res]
        print(f"Found {len(rows)} UFs with complex query")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"Error in complex query: {e}")
