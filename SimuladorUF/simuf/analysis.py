"""Detección de ingresos a geocercas, atribución de origen y cruce con validaciones SNBE."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from typing import Iterable

import pandas as pd
from pyproj import Transformer
from shapely import from_wkt
from shapely.geometry import Point
from shapely.ops import transform as shp_transform


@lru_cache(maxsize=1)
def _transformer():
    return Transformer.from_crs("EPSG:4326", "EPSG:32721", always_xy=True)


@dataclass
class Zona:
    id: int
    nombre: str
    es_principal: bool
    geom_metric: object  # shapely geometry en EPSG:32721 (área de ingreso)


def a_metrica(geom_wgs):
    tr = _transformer()
    return shp_transform(lambda x, y, z=None: tr.transform(x, y), geom_wgs)


def geometria_zona_desde_wkt(wkt: str, buffer_m: float) -> object:
    g = from_wkt(wkt)
    gm = a_metrica(g)
    if gm.is_empty:
        raise ValueError("Geometría vacía")
    t = gm.geom_type
    if t == "Point":
        return gm.buffer(buffer_m)
    if t == "LineString":
        return gm.buffer(buffer_m)
    if t == "MultiLineString":
        return gm.buffer(buffer_m)
    if t in ("Polygon", "MultiPolygon"):
        return gm.buffer(0)
    if t == "GeometryCollection":
        return gm.convex_hull.buffer(buffer_m)
    return gm.convex_hull.buffer(buffer_m)


def construir_zonas_troncales(df_tr: pd.DataFrame, buffer_m: float) -> list[Zona]:
    out: list[Zona] = []
    for i, row in df_tr.iterrows():
        wkt = row.get("wkt_geom")
        if not isinstance(wkt, str) or not wkt.strip():
            continue
        es_p = bool(row.get("es_principal", False))
        tid = int(row["id_troncal"]) if pd.notna(row.get("id_troncal")) else i
        nombre = "Troncal principal" if es_p else f"Troncal secundaria ({tid})"
        z = geometria_zona_desde_wkt(wkt.strip(), buffer_m)
        out.append(Zona(id=tid, nombre=nombre, es_principal=es_p, geom_metric=z))
    if not out:
        raise ValueError("No se pudo construir ninguna zona de troncal a partir de WKT.")
    # Si ninguna marcada como principal, la primera pasa a principal (heurística)
    if not any(z.es_principal for z in out):
        out[0] = Zona(
            id=out[0].id,
            nombre="Troncal principal (inferida)",
            es_principal=True,
            geom_metric=out[0].geom_metric,
        )
    return out


def construir_zonas_origen(df_it: pd.DataFrame, buffer_m: float) -> list[dict]:
    zonas = []
    for _, row in df_it.iterrows():
        wkt = row.get("wkt_first_point")
        if not isinstance(wkt, str) or not wkt.strip():
            label = str(row.get("origen_catalogo") or row.get("ruta_hex") or "Origen")
            zonas.append(
                {
                    "ruta_hex": row["ruta_hex"],
                    "label": label,
                    "geom_metric": None,
                }
            )
            continue
        try:
            pt = geometria_zona_desde_wkt(wkt.strip(), buffer_m)
        except Exception:
            pt = None
        label = f"{row.get('origen_catalogo') or ''} ({row['ruta_hex']})".strip()
        zonas.append({"ruta_hex": row["ruta_hex"], "label": label or row["ruta_hex"], "geom_metric": pt})
    return zonas


def _punto_metric(lon: float, lat: float):
    tr = _transformer()
    x, y = tr.transform(lon, lat)
    return Point(x, y)


def _tipo_troncal(z: Zona) -> str:
    return "principal" if z.es_principal else "secundaria"


def detectar_ingresos(
    df_gps: pd.DataFrame,
    troncales: list[Zona],
    min_separacion_entrada: timedelta = timedelta(minutes=45),
) -> pd.DataFrame:
    if df_gps.empty:
        return pd.DataFrame(
            columns=[
                "mean_id",
                "fecha_hora_ingreso",
                "id_zona",
                "nombre_zona",
                "tipo_troncal",
            ]
        )

    df = df_gps.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], utc=True, errors="coerce")
    df = df.dropna(subset=["fecha_hora", "latitude", "longitude"])
    df["mean_id"] = df["mean_id"].astype(str).str.strip().str.upper()

    eventos = []
    ultima_entrada: dict[tuple[str, int], pd.Timestamp] = {}

    for mean_id, dfb in df.groupby("mean_id", sort=False):
        dfb = dfb.sort_values("fecha_hora")
        prev_dentro: set[int] = set()
        for _, r in dfb.iterrows():
            try:
                lon = float(r["longitude"])
                lat = float(r["latitude"])
            except (TypeError, ValueError):
                continue
            p = _punto_metric(lon, lat)
            dentro_ids = {z.id for z in troncales if z.geom_metric.intersects(p)}
            nuevos = dentro_ids - prev_dentro
            for zid in nuevos:
                z = next(x for x in troncales if x.id == zid)
                t = r["fecha_hora"]
                key = (mean_id, zid)
                if key in ultima_entrada:
                    if t - ultima_entrada[key] < min_separacion_entrada:
                        continue
                ultima_entrada[key] = t
                eventos.append(
                    {
                        "mean_id": mean_id,
                        "fecha_hora_ingreso": t,
                        "id_zona": z.id,
                        "nombre_zona": z.nombre,
                        "tipo_troncal": _tipo_troncal(z),
                    }
                )
            prev_dentro = dentro_ids

    return pd.DataFrame(eventos)


def atribuir_origen(
    df_gps: pd.DataFrame,
    eventos: pd.DataFrame,
    zonas_origen: list[dict],
    lookback: timedelta,
) -> pd.Series:
    """Devuelve Serie alineada con eventos: etiqueta de origen o 'Indeterminado'."""
    if eventos.empty:
        return pd.Series(dtype=object)

    df = df_gps.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], utc=True, errors="coerce")
    df["mean_id"] = df["mean_id"].astype(str).str.strip().str.upper()
    df = df.sort_values(["mean_id", "fecha_hora"])

    labels = []
    for _, ev in eventos.iterrows():
        mid = str(ev["mean_id"]).strip().upper()
        t1 = pd.Timestamp(ev["fecha_hora_ingreso"])
        if t1.tzinfo is None:
            t1 = t1.tz_localize("UTC")
        t0 = t1 - lookback
        vent = df[(df["mean_id"] == mid) & (df["fecha_hora"] >= t0) & (df["fecha_hora"] < t1)]
        if vent.empty:
            labels.append("Indeterminado")
            continue
        last = vent.iloc[-1]
        try:
            p = _punto_metric(float(last["longitude"]), float(last["latitude"]))
        except (TypeError, ValueError):
            labels.append("Indeterminado")
            continue
        hit = None
        for zo in reversed(list(zonas_origen)):
            g = zo.get("geom_metric")
            if g is not None and g.intersects(p):
                hit = zo["label"]
                break
        labels.append(hit or "Indeterminado")
    return pd.Series(labels, index=eventos.index, name="origen_atribuido")


def coincide_idsam_monitoreo_snbe(idsam_snbe: str, clave_monitoreo: str) -> bool:
    """Compara ``idsam`` en SNBE con la clave usada en monitoreo (mean_id / idsam GPS)."""
    a = str(idsam_snbe).strip()
    b = str(clave_monitoreo).strip()
    if not a or not b:
        return False
    if a == b or a.upper() == b.upper():
        return True
    try:
        if int(a) == int(b):
            return True
    except ValueError:
        pass
    a2, b2 = a.lstrip("0") or "0", b.lstrip("0") or "0"
    if a2 == b2 or a2.upper() == b2.upper():
        return True
    try:
        return int(a2) == int(b2)
    except ValueError:
        return False


def contar_validaciones_previas(
    eventos: pd.DataFrame,
    df_val: pd.DataFrame,
    mean_to_idsam: dict[str, str],
    ventana: timedelta,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Por evento: número de validaciones SNBE en [t_ingreso - ventana, t_ingreso).
    También devuelve detalle largo (evento + validación) para drill-down.
    """
    if eventos.empty:
        return pd.Series(dtype=int), pd.DataFrame()

    if df_val.empty or "fechahoraevento" not in df_val.columns:
        s = pd.Series(0, index=eventos.index, name="n_validaciones_previas")
        return s, pd.DataFrame()

    dv = df_val.copy()
    dv["fechahoraevento"] = pd.to_datetime(dv["fechahoraevento"], utc=True, errors="coerce")
    dv["idsam"] = dv["idsam"].astype(str).str.strip()

    counts = []
    detalle_rows = []
    for idx, ev in eventos.iterrows():
        mid = str(ev["mean_id"]).strip().upper()
        idsam_key = str(mean_to_idsam.get(mid, mid)).strip()
        t1 = pd.Timestamp(ev["fecha_hora_ingreso"])
        if t1.tzinfo is None:
            t1 = t1.tz_localize("UTC")
        t0 = t1 - ventana
        mask_tiempo = (dv["fechahoraevento"] >= t0) & (dv["fechahoraevento"] < t1)
        mask_bus = dv["idsam"].apply(
            lambda x, ik=idsam_key, m=mid: coincide_idsam_monitoreo_snbe(str(x), ik)
            or coincide_idsam_monitoreo_snbe(str(x), m)
        )
        sub = dv[mask_bus & mask_tiempo]
        counts.append(len(sub))
        for _, vr in sub.iterrows():
            detalle_rows.append(
                {
                    "evento_idx": idx,
                    "mean_id": mid,
                    "fecha_hora_ingreso": t1,
                    "tipo_troncal": ev.get("tipo_troncal"),
                    "fechahoraevento": vr["fechahoraevento"],
                    "ruta_ref": vr.get("ruta_ref"),
                }
            )

    s = pd.Series(counts, index=eventos.index, name="n_validaciones_previas")
    det = pd.DataFrame(detalle_rows)
    return s, det


def mean_id_a_idsam(df_gps: pd.DataFrame) -> dict[str, str]:
    d = {}
    if "idsam" in df_gps.columns:
        for mid, grp in df_gps.groupby(df_gps["mean_id"].astype(str).str.strip().str.upper()):
            non_null = grp["idsam"].dropna()
            if not non_null.empty:
                d[str(mid).strip().upper()] = str(non_null.iloc[-1]).strip()
    for mid in df_gps["mean_id"].astype(str).str.strip().str.upper().unique():
        k = str(mid).strip().upper()
        d.setdefault(k, str(k).strip())
    return d


def agregar_por_hora_y_franja(
    eventos: pd.DataFrame,
    franjas: Iterable[tuple[str, int, int]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    franjas: iterable de (nombre, hora_inicio, hora_fin) con horas en [0,24).
    """
    if eventos.empty:
        return pd.DataFrame(), pd.DataFrame()

    ev = eventos.copy()
    ev["fecha_hora_ingreso"] = pd.to_datetime(ev["fecha_hora_ingreso"], utc=True, errors="coerce")
    ev["hora_local"] = ev["fecha_hora_ingreso"].dt.tz_convert("America/Asuncion")
    ev["hora"] = ev["hora_local"].dt.hour
    por_hora = (
        ev.groupby(["tipo_troncal", "hora"], as_index=False)
        .size()
        .rename(columns={"size": "n_ingresos"})
    )

    def franja_row(r):
        h = int(r["hora"])
        for nombre, h0, h1 in franjas:
            if h0 <= h < h1 or (h0 > h1 and (h >= h0 or h < h1)):
                return nombre
        return "Resto"

    ev["franja"] = ev.apply(franja_row, axis=1)
    por_franja = (
        ev.groupby(["tipo_troncal", "franja", "origen_atribuido"], as_index=False)
        .size()
        .rename(columns={"size": "n_ingresos"})
    )
    return por_hora, por_franja
