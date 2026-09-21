"""Carga y normalización de variables de entorno para las tres bases."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


def _strip_key(k: str) -> str:
    return k.strip()


def _load_env() -> None:
    base = Path(__file__).resolve().parent.parent
    load_dotenv(base / ".env", override=False)
    for p in (base.parent / ".env",):
        if p.is_file():
            load_dotenv(p, override=False)


@dataclass
class CidSettings:
    url: str


@dataclass
class MonSettings:
    url: str
    tabla_gps: str


@dataclass
class SnbeSettings:
    url: str
    tabla_transacciones: str
    # Si true: tipoevento IN (4,8) y idproducto 4d4f/4553 (alineado a scripts transbordos / monitoreo).
    # Por defecto false: muchas instalaciones guardan otros códigos → sin filtro devuelve transacciones útiles.
    aplicar_filtro_producto_tipo_validacion: bool


def _get_clean(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else default


def build_cid_url() -> str:
    host = _get_clean("DB_HOST")
    port = _get_clean("DB_PORT", "5432")
    db = _get_clean("DB_NAME")
    user = quote_plus(_get_clean("DB_USER"))
    pwd = quote_plus(_get_clean("DB_PASSWORD"))
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


def build_mon_url() -> str:
    # Soporta claves con o sin espacios alrededor del '=' en .env
    host = _get_clean("hostMON")
    port = _get_clean("portMON", "5432")
    db = _get_clean("databaseMON")
    user = quote_plus(_get_clean("userMON"))
    pwd = quote_plus(_get_clean("passwordMON"))
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


def build_snbe_url() -> str:
    host = _get_clean("hostZUREMIT")
    port = _get_clean("portZUREMIT", "5432")
    db = _get_clean("databaseZUREMIT")
    user = quote_plus(_get_clean("userZUREMIT"))
    pwd = quote_plus(_get_clean("passwordZUREMIT"))
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


def load_settings() -> tuple[CidSettings, MonSettings, SnbeSettings]:
    _load_env()
    cid = CidSettings(url=build_cid_url())
    mon = MonSettings(
        url=build_mon_url(),
        tabla_gps=_get_clean("TABLA_MONITOREO_GPS", "app_monitoreo_mensajeoperativo"),
    )
    snbe = SnbeSettings(
        url=build_snbe_url(),
        tabla_transacciones=_get_clean("SNBE_TABLA_TRANSACCIONES", "c_transacciones"),
        aplicar_filtro_producto_tipo_validacion=_get_clean(
            "SNBE_APLICAR_FILTRO_PRODUCTO_TIPO", ""
        ).lower()
        in ("1", "true", "yes", "si", "sí"),
    )
    return cid, mon, snbe
