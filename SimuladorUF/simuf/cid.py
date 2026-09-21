"""Consultas a la BD CID: UF, composición, EOTs, troncales e itinerarios."""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def listar_ufs(engine: Engine) -> pd.DataFrame:
    q = text(
        """
        SELECT id_uf, nombre_uf, tipo_uf, estado
        FROM gestion_uf.unidades_funcionales
        WHERE COALESCE(estado, true) = true
        ORDER BY nombre_uf
        """
    )
    return pd.read_sql(q, engine)


def columnas_tabla(engine: Engine, schema: str, table: str) -> set[str]:
    q = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        """
    )
    df = pd.read_sql(q, engine, params={"schema": schema, "table": table})
    return set(df["column_name"].astype(str).str.lower())


def _pick_principal_col(cols: set[str]) -> str | None:
    for c in (
        "es_principal",
        "principal",
        "es_troncal_principal",
        "troncal_principal",
        "prioridad",
    ):
        if c in cols:
            return c
    return None


def cargar_troncales_uf(engine: Engine, id_uf: int) -> pd.DataFrame:
    """
    Devuelve filas con: id_troncal (si existe), id_uf, es_principal, wkt_geom.
    Intenta resolver geometría desde la propia fila o vía id_geocerca -> geometria.geocercas.
    """
    cols = columnas_tabla(engine, "gestion_uf", "uf_troncales")
    if not cols:
        raise RuntimeError(
            "No existe la tabla gestion_uf.uf_troncales o no hay permisos de lectura."
        )

    id_col = None
    for cand in ("id_uf_troncal", "id_troncal", "id"):
        if cand in cols:
            id_col = cand
            break
    sel_id = f"t.{id_col} AS id_troncal" if id_col else "NULL::int AS id_troncal"

    principal_col = _pick_principal_col(cols)
    if principal_col:
        if principal_col == "prioridad":
            es_prin = "(t.prioridad = 1)"
        else:
            es_prin = f"COALESCE(t.{principal_col}::boolean, false)"
    else:
        es_prin = "false"

    join_gc = ""
    geom_expr = "NULL::text"
    has_gc = "id_geocerca" in cols and columnas_tabla(engine, "geometria", "geocercas")
    if "geom" in cols and has_gc:
        join_gc = "LEFT JOIN geometria.geocercas g ON g.id_geocerca = t.id_geocerca"
        geom_expr = "ST_AsText(COALESCE(t.geom::geometry, g.geom::geometry))"
    elif "geom" in cols:
        geom_expr = "ST_AsText(t.geom::geometry)"
    elif has_gc:
        join_gc = "JOIN geometria.geocercas g ON g.id_geocerca = t.id_geocerca"
        geom_expr = "ST_AsText(g.geom::geometry)"

    q = text(
        f"""
        SELECT {sel_id},
               t.id_uf,
               {es_prin} AS es_principal,
               {geom_expr} AS wkt_geom
        FROM gestion_uf.uf_troncales t
        {join_gc}
        WHERE t.id_uf = :id_uf
        """
    )
    df = pd.read_sql(q, engine, params={"id_uf": id_uf})
    if df.empty:
        raise RuntimeError(
            f"No hay registros en gestion_uf.uf_troncales para id_uf={id_uf}. "
            "Verifique la UF y la tabla."
        )
    df["es_principal"] = df["es_principal"].fillna(False).astype(bool)
    if df["wkt_geom"].isna().all():
        raise RuntimeError(
            "Las troncales no tienen geometría resoluble (geom en uf_troncales o id_geocerca -> geometria.geocercas). "
            "Ajuste el modelo o amplíe simuf/cid.py."
        )
    return df


def composicion_y_catalogo(
    engine: Engine, id_uf: int, fecha: date
) -> tuple[pd.DataFrame, list[str]]:
    """
    Rutas que componen la UF en la fecha indicada, con agency_id (id_eot_vmt_hex)
    y datos de catálogo.
    """
    q = text(
        """
        SELECT
            c.id_composicion_uf,
            c.ruta_hex,
            c.fecha_inicio,
            c.fecha_fin,
            r.ruta_dec,
            r.ruta_gtfs,
            r.origen,
            r.destino,
            r.identificacion,
            r.id_eot_catalogo,
            e.eot_nombre,
            e.id_eot_vmt_hex AS agency_id
        FROM gestion_uf.composicion_uf c
        JOIN public.catalogo_rutas r ON r.ruta_hex = c.ruta_hex
        LEFT JOIN public.eots e ON e.cod_catalogo = r.id_eot_catalogo
        WHERE c.id_uf = :id_uf
          AND c.fecha_inicio <= :fecha
          AND (c.fecha_fin IS NULL OR c.fecha_fin >= :fecha)
        ORDER BY c.ruta_hex
        """
    )
    df = pd.read_sql(q, engine, params={"id_uf": id_uf, "fecha": fecha})
    rutas = [str(x) for x in df["ruta_hex"].dropna().unique().tolist()]
    return df, rutas


def idrutas_para_idrutaestacion(df_comp: pd.DataFrame) -> list[str]:
    """
    Valores a usar en c_transacciones.idrutaestacion para las rutas de la UF.

    Se incluyen, sin duplicar: ruta_dec (idruta decimal habitual en SNBE),
    ruta_hex del catálogo y, si existe, ruta_gtfs (como entero si aplica).
    """
    vs: set[str] = set()
    if df_comp is None or df_comp.empty:
        return []

    for _, row in df_comp.iterrows():
        rd = row.get("ruta_dec")
        if pd.notna(rd):
            try:
                vs.add(str(int(float(rd))))
            except (ValueError, TypeError):
                s = str(rd).strip()
                if s:
                    vs.add(s)

        rh = row.get("ruta_hex")
        if rh is not None and str(rh).strip():
            vs.add(str(rh).strip())

        rg = row.get("ruta_gtfs")
        if pd.notna(rg):
            try:
                f = float(rg)
                vs.add(str(int(f)) if f == int(f) else str(f))
            except (ValueError, TypeError):
                s = str(rg).strip()
                if s:
                    vs.add(s)

    return sorted(vs)


def itinerarios_origen(
    engine: Engine, rutas_hex: list[str], fecha: date
) -> pd.DataFrame:
    """
    Primer punto del itinerario vigente por ruta (aprox. cabecera / inicio de servicio).
    """
    if not rutas_hex:
        return pd.DataFrame(
            columns=["ruta_hex", "origen_catalogo", "wkt_first_point", "id_itinerario"]
        )
    q = text(
        """
        WITH ranked AS (
            SELECT
                hi.ruta_hex,
                cr.origen AS origen_catalogo,
                hi.id_itinerario,
                ST_AsText(
                    ST_StartPoint(
                        ST_GeometryN(
                            ST_CollectionExtract(ST_LineMerge(hi.geom::geometry), 2),
                            1
                        )
                    )
                ) AS wkt_first_point,
                ROW_NUMBER() OVER (
                    PARTITION BY hi.ruta_hex
                    ORDER BY hi.fecha_inicio_vigencia DESC NULLS LAST
                ) AS rn
            FROM geometria.historico_itinerario hi
            JOIN public.catalogo_rutas cr ON cr.ruta_hex = hi.ruta_hex
            WHERE hi.ruta_hex = ANY(:rutas)
              AND hi.fecha_inicio_vigencia <= :fecha
              AND (hi.fecha_fin_vigencia IS NULL OR hi.fecha_fin_vigencia >= :fecha)
              AND COALESCE(hi.vigente, true) = true
        )
        SELECT ruta_hex, origen_catalogo, wkt_first_point, id_itinerario
        FROM ranked
        WHERE rn = 1
        """
    )
    try:
        return pd.read_sql(q, engine, params={"rutas": rutas_hex, "fecha": fecha})
    except Exception:
        q2 = text(
            """
            WITH ranked AS (
                SELECT
                    hi.ruta_hex,
                    cr.origen AS origen_catalogo,
                    hi.id_itinerario,
                    ST_AsText(ST_Centroid(hi.geom::geometry)) AS wkt_first_point,
                    ROW_NUMBER() OVER (
                        PARTITION BY hi.ruta_hex
                        ORDER BY hi.fecha_inicio_vigencia DESC NULLS LAST
                    ) AS rn
                FROM geometria.historico_itinerario hi
                JOIN public.catalogo_rutas cr ON cr.ruta_hex = hi.ruta_hex
                WHERE hi.ruta_hex = ANY(:rutas)
                  AND hi.fecha_inicio_vigencia <= :fecha
                  AND (hi.fecha_fin_vigencia IS NULL OR hi.fecha_fin_vigencia >= :fecha)
                  AND COALESCE(hi.vigente, true) = true
            )
            SELECT ruta_hex, origen_catalogo, wkt_first_point, id_itinerario
            FROM ranked
            WHERE rn = 1
            """
        )
        return pd.read_sql(q2, engine, params={"rutas": rutas_hex, "fecha": fecha})


def agency_ids_para_uf(df_comp: pd.DataFrame) -> list[str]:
    s = (
        df_comp["agency_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    return sorted({x for x in s if x})
