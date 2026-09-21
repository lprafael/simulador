"""Consultas al sistema de billetaje (SNBE / OpenTransit) en PostgreSQL."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

_TABLA_OK = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def columnas_snbe(engine: Engine, tabla: str) -> set[str]:
    q = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :table
        """
    )
    df = pd.read_sql(q, engine, params={"table": tabla})
    return set(df["column_name"].astype(str).str.lower())


def normaliza_fechahoraevento_a_utc(df: pd.DataFrame) -> pd.DataFrame:
    """
    ``fechahoraevento`` en c_transacciones suele ser **timestamp sin zona** en hora local.
    Se interpreta como America/Asuncion y se convierte a UTC para cruzar con ingresos (GPS en UTC).
    """
    if df.empty or "fechahoraevento" not in df.columns:
        return df
    out = df.copy()
    ts = pd.to_datetime(out["fechahoraevento"], errors="coerce")
    if getattr(ts.dt, "tz", None) is not None:
        out["fechahoraevento"] = ts.dt.tz_convert("UTC")
    else:
        out["fechahoraevento"] = (
            ts.dt.tz_localize(
                "America/Asuncion",
                ambiguous="infer",
                nonexistent="shift_forward",
            ).dt.tz_convert("UTC")
        )
    return out


def _idrutas_sql_placeholders(idrutas_estacion: list[str]) -> tuple[str, dict]:
    """Placeholders para comparar idrutaestacion como texto normalizado."""
    params: dict = {}
    parts = []
    for i, v in enumerate(idrutas_estacion):
        key = f"r{i}"
        params[key] = str(v).strip()
        parts.append(f":{key}")
    return ", ".join(parts), params


def _idsams_sql_placeholders(idsams: list[str]) -> tuple[str, dict]:
    params: dict = {}
    parts = []
    for i, v in enumerate(idsams):
        key = f"s{i}"
        params[key] = str(v).strip()
        parts.append(f":{key}")
    return ", ".join(parts), params


def variantes_idsam_para_snbe(idsams: list[str], max_claves: int = 2000) -> list[str]:
    """
    Expande los identificadores de bus del monitoreo (``mean_id`` / ``idsam`` GPS) a las formas
    más frecuentes en ``c_transacciones.idsam`` (mayúsculas, sin ceros a la izquierda, relleno numérico).
    """
    vs: set[str] = set()
    for raw in idsams:
        s = str(raw).strip()
        if not s:
            continue
        vs.add(s)
        vs.add(s.upper())
        vs.add(s.lower())
        lz = s.lstrip("0") or "0"
        vs.add(lz)
        vs.add(lz.upper())
        if s.isdigit():
            try:
                n = int(s)
                vs.add(str(n))
                for pad in (6, 8, 10, 12, 16):
                    vs.add(str(n).zfill(pad))
            except ValueError:
                pass
        if lz.isdigit():
            try:
                n = int(lz)
                vs.add(str(n))
                for pad in (6, 8, 10, 12, 16):
                    vs.add(str(n).zfill(pad))
            except ValueError:
                pass
    out = sorted({x for x in vs if x})
    return out[:max_claves]


def _idsams_sql_placeholders_expandido(idsams: list[str]) -> tuple[str, dict]:
    exp = variantes_idsam_para_snbe(idsams)
    params: dict = {}
    parts = []
    for i, v in enumerate(exp):
        key = f"s{i}"
        params[key] = str(v).strip()
        parts.append(f":{key}")
    return ", ".join(parts), params


def _sql_filtro_validacion_estricta(cols: set[str], aplicar: bool) -> str:
    """
    Alineado con scripts de transbordos / validaciones: ``tipoevento IN (4, 8)``
    y ``idproducto`` típico de billete (hex en texto).
    """
    if not aplicar:
        return ""
    parts: list[str] = []
    if "tipoevento" in cols:
        parts.append(
            "(tipoevento IN (4, 8) OR CAST(tipoevento AS text) IN ('4', '8'))"
        )
    if "idproducto" in cols:
        parts.append(
            "LOWER(TRIM(CAST(idproducto AS text))) IN ('4d4f', '4553')"
        )
    if not parts:
        return ""
    return " AND " + " AND ".join(parts)


def diagnostico_snbe_ventana(
    engine: Engine,
    tabla: str,
    t0_local: datetime,
    t1_local: datetime,
    idrutas_estacion: list[str],
    limite_muestra: int = 25,
) -> dict:
    """
    Ayuda a depurar filtros: conteos en la ventana horaria (fechas **locales**, sin TZ en SQL).
    """
    if not _TABLA_OK.match(tabla or ""):
        raise ValueError("Nombre de tabla SNBE no válido.")
    cols = columnas_snbe(engine, tabla)
    out: dict = {"columnas_ok": "idrutaestacion" in cols and "fechahoraevento" in cols and "idsam" in cols}
    base = {"t0": t0_local, "t1": t1_local}
    q1 = text(
        f"""
        SELECT COUNT(*) AS n
        FROM public.{tabla}
        WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
        """
    )
    out["filas_en_ventana"] = int(pd.read_sql(q1, engine, params=base).iloc[0]["n"])

    if idrutas_estacion and "idrutaestacion" in cols:
        ph, pr = _idrutas_sql_placeholders(idrutas_estacion)
        params2 = {**base, **pr}
        q2 = text(
            f"""
            SELECT COUNT(*) AS n
            FROM public.{tabla}
            WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
              AND trim(both from CAST(idrutaestacion AS text)) IN ({ph})
            """
        )
        out["filas_ventana_y_ruta_uf"] = int(pd.read_sql(q2, engine, params=params2).iloc[0]["n"])
        params3 = {**base, "lim": int(limite_muestra)}
        q3 = text(
            f"""
            SELECT trim(both from CAST(idrutaestacion AS text)) AS idruta, COUNT(*) AS n
            FROM public.{tabla}
            WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
            GROUP BY 1
            ORDER BY n DESC
            LIMIT :lim
            """
        )
        out["top_idrutaestacion_en_ventana"] = pd.read_sql(q3, engine, params=params3).to_dict("records")
    else:
        out["filas_ventana_y_ruta_uf"] = None
        out["top_idrutaestacion_en_ventana"] = []

    return out


def cargar_validaciones(
    engine: Engine,
    tabla: str,
    idsams: list[str],
    idrutas_estacion: list[str],
    t0_local: datetime,
    t1_local: datetime,
    *,
    aplicar_filtro_producto_tipo: bool = False,
    margen_previo_minutos: int = 0,
) -> pd.DataFrame:
    """
    ``public.c_transacciones`` usando conexión hostZUREMIT / opentransit-prod (u otra en .env).

    - ``t0_local`` / ``t1_local``: **naive**, hora **America/Asunción** (misma convención que típicamente
      guarda el servidor SNBE en ``fechahoraevento`` sin offset).
    - ``margen_previo_minutos``: amplía el inicio de la consulta hacia atrás (p. ej. ventana de
      validaciones antes del ingreso), para no perder transacciones ocurridas antes de ``t0_local``
      pero dentro de ``[ingreso - ventana, ingreso)``.
    - Filtro de ruta: ``trim(cast(idrutaestacion as text)) IN (...)`` con los ids de ruta de la UF.
    - ``idsam``: comparación como texto recortado.
    - Filtro estricto (validación / transbordo típico): **solo** si ``aplicar_filtro_producto_tipo``.
    """
    if not _TABLA_OK.match(tabla or ""):
        raise ValueError("Nombre de tabla SNBE no válido.")
    if not idsams:
        return pd.DataFrame()

    cols = columnas_snbe(engine, tabla)
    if "idsam" not in cols or "fechahoraevento" not in cols:
        raise RuntimeError(
            f"La tabla public.{tabla} no expone las columnas esperadas (idsam, fechahoraevento)."
        )
    if "idrutaestacion" not in cols:
        raise RuntimeError(
            f"La tabla public.{tabla} no tiene la columna idrutaestacion (requerida para filtrar por rutas de la UF)."
        )
    if not idrutas_estacion:
        return pd.DataFrame(
            columns=["idsam", "fechahoraevento", "idrutaestacion", "tipoevento", "idproducto"]
        )

    t_query_start = t0_local
    if margen_previo_minutos and margen_previo_minutos > 0:
        t_query_start = t0_local - timedelta(minutes=int(margen_previo_minutos))

    filtros_extra = _sql_filtro_validacion_estricta(cols, aplicar_filtro_producto_tipo)

    rutas_ph, pr_params = _idrutas_sql_placeholders(idrutas_estacion)
    idsam_ph, sp_params = _idsams_sql_placeholders_expandido(idsams)

    params: dict = {"t0": t_query_start, "t1": t1_local, **pr_params, **sp_params}

    sel_extra = ""
    if "tipoevento" in cols:
        sel_extra += ", tipoevento"
    else:
        sel_extra += ", NULL::int AS tipoevento"
    if "idproducto" in cols:
        sel_extra += ", idproducto"
    else:
        sel_extra += ", NULL::text AS idproducto"

    q = text(
        f"""
        SELECT idsam, fechahoraevento, idrutaestacion AS ruta_ref{sel_extra}
        FROM public.{tabla}
        WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
          AND trim(both from CAST(idsam AS text)) IN ({idsam_ph})
          AND trim(both from CAST(idrutaestacion AS text)) IN ({rutas_ph})
          {filtros_extra}
        """
    )
    df = pd.read_sql(q, engine, params=params)
    return normaliza_fechahoraevento_a_utc(df)


def contar_idsam_por_ruta_snbe(
    engine: Engine,
    tabla: str,
    idrutas_estacion: list[str],
    t0_local: datetime,
    t1_local: datetime,
    *,
    aplicar_filtro_producto_tipo: bool = False,
    margen_previo_minutos: int = 0,
) -> pd.DataFrame:
    """
    Agregado: cantidad de filas y ``idsam`` distintos por ``idrutaestacion`` en la ventana
    (sin filtrar por lista de buses), útil para verificar datos SNBE vs catálogo UF.
    """
    if not idrutas_estacion:
        return pd.DataFrame(columns=["idrutaestacion", "n_transacciones", "n_idsam_distintos"])

    cols = columnas_snbe(engine, tabla)
    if "idrutaestacion" not in cols or "idsam" not in cols or "fechahoraevento" not in cols:
        return pd.DataFrame()

    t_query_start = t0_local
    if margen_previo_minutos and margen_previo_minutos > 0:
        t_query_start = t0_local - timedelta(minutes=int(margen_previo_minutos))

    filtros_extra = _sql_filtro_validacion_estricta(cols, aplicar_filtro_producto_tipo)

    rutas_ph, pr_params = _idrutas_sql_placeholders(idrutas_estacion)
    params: dict = {"t0": t_query_start, "t1": t1_local, **pr_params}

    q = text(
        f"""
        SELECT
            trim(both from CAST(idrutaestacion AS text)) AS idrutaestacion,
            COUNT(*) AS n_transacciones,
            COUNT(DISTINCT trim(both from CAST(idsam AS text))) AS n_idsam_distintos
        FROM public.{tabla}
        WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
          AND trim(both from CAST(idrutaestacion AS text)) IN ({rutas_ph})
          {filtros_extra}
        GROUP BY 1
        ORDER BY n_transacciones DESC
        """
    )
    return pd.read_sql(q, engine, params=params)


def diagnostico_cruce_snbe(
    engine: Engine,
    tabla: str,
    t0_local: datetime,
    t1_local: datetime,
    idrutas_estacion: list[str],
    idsams: list[str],
    *,
    aplicar_filtro_producto_tipo: bool,
    margen_previo_minutos: int,
) -> dict[str, int]:
    """
    Conteos para entender por qué ``cargar_validaciones`` devuelve 0 filas:
    misma ventana ampliada y mismos filtros, variando ruta / estricto / idsam.
    """
    if not _TABLA_OK.match(tabla or ""):
        return {}
    cols = columnas_snbe(engine, tabla)
    if "fechahoraevento" not in cols or "idrutaestacion" not in cols:
        return {}

    tqs = t0_local
    if margen_previo_minutos and margen_previo_minutos > 0:
        tqs = t0_local - timedelta(minutes=int(margen_previo_minutos))

    base = {"t0": tqs, "t1": t1_local}
    q0 = text(
        f"""
        SELECT COUNT(*)::bigint AS n
        FROM public.{tabla}
        WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
        """
    )
    n0 = int(pd.read_sql(q0, engine, params=base).iloc[0]["n"])

    if not idrutas_estacion:
        return {"n_solo_tiempo_ampliado": n0}

    ph_r, pr = _idrutas_sql_placeholders(idrutas_estacion)
    p1 = {**base, **pr}
    q1 = text(
        f"""
        SELECT COUNT(*)::bigint AS n
        FROM public.{tabla}
        WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
          AND trim(both from CAST(idrutaestacion AS text)) IN ({ph_r})
        """
    )
    n1 = int(pd.read_sql(q1, engine, params=p1).iloc[0]["n"])

    strict_sql = _sql_filtro_validacion_estricta(cols, aplicar_filtro_producto_tipo)
    n2 = n1
    if aplicar_filtro_producto_tipo and strict_sql:
        q2 = text(
            f"""
            SELECT COUNT(*)::bigint AS n
            FROM public.{tabla}
            WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
              AND trim(both from CAST(idrutaestacion AS text)) IN ({ph_r})
              {strict_sql}
            """
        )
        n2 = int(pd.read_sql(q2, engine, params=p1).iloc[0]["n"])

    n3 = n2
    if idsams and "idsam" in cols:
        ph_s, ps = _idsams_sql_placeholders_expandido(idsams)
        p2 = {**p1, **ps}
        filt = strict_sql if aplicar_filtro_producto_tipo else ""
        q3 = text(
            f"""
            SELECT COUNT(*)::bigint AS n
            FROM public.{tabla}
            WHERE fechahoraevento >= :t0 AND fechahoraevento < :t1
              AND trim(both from CAST(idrutaestacion AS text)) IN ({ph_r})
              AND trim(both from CAST(idsam AS text)) IN ({ph_s})
              {filt}
            """
        )
        n3 = int(pd.read_sql(q3, engine, params=p2).iloc[0]["n"])

    return {
        "n_solo_tiempo_ampliado": n0,
        "n_tiempo_y_ruta_uf": n1,
        "n_mas_filtro_validacion_estricto": n2,
        "n_mas_idsam_buses_ingreso": n3,
    }
