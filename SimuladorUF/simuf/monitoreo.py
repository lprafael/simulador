"""Lectura de posiciones GPS desde la base de monitoreo."""

from __future__ import annotations

from datetime import datetime

import re

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

_TABLA_OK = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def columnas_gps(engine: Engine, tabla: str) -> set[str]:
    q = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :table
        """
    )
    df = pd.read_sql(q, engine, params={"table": tabla})
    return set(df["column_name"].astype(str).str.lower())


def cargar_gps(
    engine: Engine,
    tabla: str,
    agency_ids: list[str],
    t0: datetime,
    t1: datetime,
    mean_ids: list[str] | None = None,
) -> pd.DataFrame:
    if not _TABLA_OK.match(tabla or ""):
        raise ValueError("Nombre de tabla GPS no válido (use solo letras, números y _).")

    if not agency_ids:
        return pd.DataFrame(
            columns=["mean_id", "fecha_hora", "latitude", "longitude", "agency_id"]
        )

    cols = columnas_gps(engine, tabla)
    extra = []
    if "idsam" in cols:
        extra.append("idsam")
    if "route_id" in cols:
        extra.append("route_id")
    if "trip_id" in cols:
        extra.append("trip_id")

    extra_suffix = (", " + ", ".join(extra)) if extra else ""
    agency_placeholders = ", ".join(f":a{i}" for i in range(len(agency_ids)))
    params: dict = {f"a{i}": v for i, v in enumerate(agency_ids)}
    params["t0"] = t0
    params["t1"] = t1

    mean_filter = ""
    if mean_ids:
        mean_placeholders = ", ".join(f":m{i}" for i in range(len(mean_ids)))
        mean_filter = f" AND UPPER(TRIM(mean_id)) IN ({mean_placeholders})"
        for i, v in enumerate(mean_ids):
            params[f"m{i}"] = str(v).strip().upper()

    q = text(
        f"""
        SELECT mean_id, fecha_hora, latitude, longitude, agency_id{extra_suffix}
        FROM public.{tabla}
        WHERE agency_id IN ({agency_placeholders})
          AND fecha_hora >= :t0 AND fecha_hora < :t1
          AND mean_id IS NOT NULL AND TRIM(mean_id) <> ''
          {mean_filter}
        ORDER BY mean_id, fecha_hora
        """
    )

    return pd.read_sql(q, engine, params=params)
