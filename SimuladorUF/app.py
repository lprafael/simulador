"""
Simulador UF — ingresos a troncales, validaciones SNBE y agregados por hora/franja.

Ejecutar desde esta carpeta:
  pip install -r requirements.txt
  streamlit run app.py
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from simuf import analysis, cid, monitoreo, settings, snbe

TZ_ASU = ZoneInfo("America/Asuncion")

FRANJAS_DEFAULT: list[tuple[str, int, int]] = [
    ("Madrugada (00-05)", 0, 5),
    ("Pico mañana (05-09)", 5, 9),
    ("Media mañana (09-12)", 9, 12),
    ("Mediodía (12-15)", 12, 15),
    ("Tarde (15-19)", 15, 19),
    ("Noche (19-24)", 19, 24),
]


def _parse_franjas_text(txt: str) -> list[tuple[str, int, int]]:
    out: list[tuple[str, int, int]] = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            continue
        nombre, h0s, h1s = parts
        out.append((nombre, int(h0s), int(h1s)))
    return out or FRANJAS_DEFAULT


def _engine(url: str):
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=120)
def _ufs_cached(cid_url: str) -> pd.DataFrame:
    return cid.listar_ufs(_engine(cid_url))


def main():
    st.set_page_config(page_title="Simulador UF — Troncales y ocupación", layout="wide")
    st.title("Simulador UF — ingresos a troncales y validaciones")
    st.caption(
        "Integra CID (composición UF y geocercas), monitoreo (GPS por agency_id) y SNBE (validaciones). "
        "Las validaciones previas al ingreso sirven como indicador de demanda (no equivalen a ocupación real del vehículo)."
    )

    cid_s, mon_s, snbe_s = settings.load_settings()
    eng_cid = _engine(cid_s.url)
    eng_mon = _engine(mon_s.url)
    eng_snbe = _engine(snbe_s.url)

    with st.sidebar:
        st.header("Parámetros")
        try:
            ufs = _ufs_cached(cid_s.url)
        except Exception as e:
            st.error(f"No se pudo leer CID: {e}")
            ufs = pd.DataFrame()

        id_uf = None
        if not ufs.empty:
            id_opts = {f"{r['nombre_uf']} (id={r['id_uf']})": int(r["id_uf"]) for _, r in ufs.iterrows()}
            label_sel = st.selectbox("Unidad funcional", list(id_opts.keys()))
            id_uf = id_opts[label_sel]

        fecha = st.date_input("Fecha de análisis", value=date.today())
        h_ini = st.time_input("Hora inicio (local Asunción)", value=time(5, 0))
        h_fin = st.time_input("Hora fin (local Asunción)", value=time(22, 0))
        buf_tr = st.slider("Buffer geocerca troncal (m)", 30, 250, 90)
        buf_or = st.slider("Buffer punto de origen ruta (m)", 30, 400, 150)
        vent_val_min = st.slider("Ventana validaciones antes del ingreso (min)", 5, 180, 60)
        look_or_min = st.slider("Ventana para atribuir origen antes del ingreso (min)", 5, 120, 45)
        sep_entrada_min = st.slider("Separación mínima entre ingresos mismo bus/zona (min)", 15, 180, 45)
        lim_buses = st.number_input("Límite de filas GPS (0 = sin límite)", 0, 5_000_000, 400_000)
        snbe_filtro_estricto = st.checkbox(
            "SNBE: solo eventos validación (idproducto/tipoevento)",
            value=snbe_s.aplicar_filtro_producto_tipo_validacion,
            help="Desmarcado: todas las filas de c_transacciones que cumplan fecha, idrutaestacion e idsam. "
            "Marcado: ``tipoevento IN (4, 8)`` y ``idproducto`` 4d4f/4553 (como scripts de transbordos / monitoreo).",
        )
        st.subheader("Franjas horarias (nombre,h0,h1 por línea)")
        franjas_txt = st.text_area(
            "Franjas",
            value="\n".join(f"{a},{b},{c}" for a, b, c in FRANJAS_DEFAULT),
            height=160,
        )
        ejecutar = st.button("Ejecutar análisis", type="primary")

    tab_res, tab_evt, tab_val, tab_inf = st.tabs(
        ["Resumen", "Eventos de ingreso", "Validaciones SNBE", "Conexión / esquema"]
    )

    with tab_inf:
        st.markdown(
            "### Comprobación rápida\n"
            "- **CID**: `gestion_uf.*`, `catalogo_rutas`, `eots`, `geometria.historico_itinerario`.\n"
            "- **Monitoreo**: `TABLA_MONITOREO_GPS` (por defecto `app_monitoreo_mensajeoperativo`).\n"
            "- **SNBE** (``hostZUREMIT`` / ``opentransit-prod`` en `.env`): `public.c_transacciones`. "
            "Filtro por **`idrutaestacion`** (ids de ruta de la UF desde `catalogo_rutas`) y **`idsam`**. "
            "Las fechas en SQL usan **hora local Asunción** (naive), igual que la selección del sidebar. "
            "Tras leer, `fechahoraevento` se normaliza a UTC para cruzar con ingresos GPS. "
            "Opcional: `SNBE_APLICAR_FILTRO_PRODUCTO_TIPO=true` o el checkbox equivalente para filtrar solo validación (idproducto/tipoevento).\n"
            "\n**Mapeo mean_id → idsam**: si la tabla GPS incluye la columna `idsam`, se usa; si no, se asume "
            "que `mean_id` coincide con `idsam` (revise en su entorno)."
        )
        if st.button("Probar conexión a las tres bases"):
            try:
                pd.read_sql(text("SELECT 1"), eng_cid)
                st.success("CID: OK")
            except Exception as e:
                st.error(f"CID: fallo — {e}")
            try:
                pd.read_sql(text("SELECT 1"), eng_mon)
                st.success("Monitoreo: OK")
            except Exception as e:
                st.error(f"Monitoreo: fallo — {e}")
            try:
                pd.read_sql(text("SELECT 1"), eng_snbe)
                st.success("SNBE: OK")
            except Exception as e:
                st.error(f"SNBE: fallo — {e}")

    if not ejecutar:
        st.info("Elija la UF y los parámetros en la barra lateral, luego pulse **Ejecutar análisis**.")
        return

    if id_uf is None:
        st.error("No hay UF seleccionable.")
        return

    franjas = _parse_franjas_text(franjas_txt)

    t0_local = datetime.combine(fecha, h_ini, tzinfo=TZ_ASU)
    t1_local = datetime.combine(fecha, h_fin, tzinfo=TZ_ASU)
    if t1_local <= t0_local:
        t1_local += timedelta(days=1)
    t0 = t0_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    t1 = t1_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    # SNBE: fechahoraevento suele almacenarse como hora local sin TZ — usar el mismo reloj que el usuario eligió.
    t0_snbe = t0_local.replace(tzinfo=None)
    t1_snbe = t1_local.replace(tzinfo=None)

    try:
        df_tr = cid.cargar_troncales_uf(eng_cid, id_uf)
        df_comp, rutas = cid.composicion_y_catalogo(eng_cid, id_uf, fecha)
        agency_ids = cid.agency_ids_para_uf(df_comp)
        df_it = cid.itinerarios_origen(eng_cid, rutas, fecha)
    except Exception as e:
        st.exception(e)
        return

    idrutas_snbe = cid.idrutas_para_idrutaestacion(df_comp)
    if not idrutas_snbe:
        st.warning(
            "No se obtuvieron valores para **idrutaestacion** desde el catálogo (ruta_dec / ruta_hex / ruta_gtfs). "
            "Las consultas a SNBE no filtrarán por ruta hasta que esos campos estén poblados."
        )

    with st.expander("Composición y agency_id (monitoreo)", expanded=False):
        st.dataframe(df_comp, use_container_width=True)
        st.write("**agency_id** usados en filtro GPS:", agency_ids or "(ninguno — revise join con eots)")
        st.write(
            "**idrutaestacion (SNBE)** — valores derivados del catálogo para esta UF:",
            idrutas_snbe or "(vacío)",
        )

    if not agency_ids:
        st.error(
            "No se obtuvieron agency_id (`eots.id_eot_vmt_hex`) para las rutas de la UF. "
            "Verifique `catalogo_rutas.id_eot_catalogo` y `eots.cod_catalogo`."
        )
        return

    try:
        troncales = analysis.construir_zonas_troncales(df_tr, float(buf_tr))
        zonas_origen = analysis.construir_zonas_origen(df_it, float(buf_or))
    except Exception as e:
        st.exception(e)
        return

    with st.expander("Troncales (CID)", expanded=False):
        st.dataframe(df_tr, use_container_width=True)

    try:
        df_gps = monitoreo.cargar_gps(
            eng_mon,
            mon_s.tabla_gps,
            agency_ids,
            t0,
            t1,
            mean_ids=None,
        )
    except Exception as e:
        st.exception(e)
        return

    if lim_buses and len(df_gps) > lim_buses:
        df_gps = df_gps.iloc[: int(lim_buses)].copy()
        st.warning(f"GPS truncado a las primeras {int(lim_buses)} filas (límite configurado).")

    st.metric("Puntos GPS cargados", len(df_gps))
    if df_gps.empty:
        st.warning("Sin datos GPS para los agency_id y el intervalo indicados.")
        return

    eventos = analysis.detectar_ingresos(
        df_gps,
        troncales,
        min_separacion_entrada=timedelta(minutes=float(sep_entrada_min)),
    )
    if eventos.empty:
        st.warning(
            "No se detectaron ingresos a las geocercas de troncal con los parámetros actuales "
            "(buffers, intervalo o geometrías)."
        )
        return

    origen_ser = analysis.atribuir_origen(
        df_gps,
        eventos,
        zonas_origen,
        lookback=timedelta(minutes=float(look_or_min)),
    )
    eventos = eventos.copy()
    eventos["origen_atribuido"] = origen_ser.values

    mean_map = analysis.mean_id_a_idsam(df_gps)
    mean_ids_evt = {str(m).strip().upper() for m in eventos["mean_id"].unique()}
    idsams = sorted(
        {mean_map[mid] for mid in mean_ids_evt if mid in mean_map}
        | mean_ids_evt
    )

    det_val = pd.DataFrame()
    snbe_diag: dict | None = None
    agg_snbe_ruta = pd.DataFrame()
    try:
        df_val = snbe.cargar_validaciones(
            eng_snbe,
            snbe_s.tabla_transacciones,
            idsams,
            idrutas_snbe,
            t0_snbe,
            t1_snbe,
            aplicar_filtro_producto_tipo=snbe_filtro_estricto,
            margen_previo_minutos=int(vent_val_min),
        )
    except Exception as e:
        st.warning(f"SNBE: no se pudieron cargar validaciones ({e}). Se continúa solo con ingresos.")
        df_val = pd.DataFrame()

    cruce_diag: dict[str, int] = {}
    if df_val.empty and idrutas_snbe and idsams:
        try:
            cruce_diag = snbe.diagnostico_cruce_snbe(
                eng_snbe,
                snbe_s.tabla_transacciones,
                t0_snbe,
                t1_snbe,
                idrutas_snbe,
                idsams,
                aplicar_filtro_producto_tipo=snbe_filtro_estricto,
                margen_previo_minutos=int(vent_val_min),
            )
        except Exception:
            cruce_diag = {}

    try:
        snbe_diag = snbe.diagnostico_snbe_ventana(
            eng_snbe,
            snbe_s.tabla_transacciones,
            t0_snbe,
            t1_snbe,
            idrutas_snbe,
        )
        if idrutas_snbe:
            agg_snbe_ruta = snbe.contar_idsam_por_ruta_snbe(
                eng_snbe,
                snbe_s.tabla_transacciones,
                idrutas_snbe,
                t0_snbe,
                t1_snbe,
                aplicar_filtro_producto_tipo=snbe_filtro_estricto,
                margen_previo_minutos=int(vent_val_min),
            )
    except Exception:
        snbe_diag = None
        agg_snbe_ruta = pd.DataFrame()

    vent = timedelta(minutes=float(vent_val_min))
    n_val, det_val = analysis.contar_validaciones_previas(eventos, df_val, mean_map, vent)
    eventos["n_validaciones_previas"] = n_val.values

    por_hora, por_franja = analysis.agregar_por_hora_y_franja(eventos, franjas)

    with tab_res:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos detectados", len(eventos))
        c2.metric("Buses distintos", eventos["mean_id"].nunique())
        c3.metric("Validaciones (ventana previa, total)", int(eventos["n_validaciones_previas"].sum()))
        st.caption(
            f"Filas cargadas desde SNBE para el cruce (ruta + idsam + filtro opcional): **{len(df_val)}**. "
            f"La consulta incluye hasta **{int(vent_val_min)} min antes** del inicio del horario GPS "
            "para poder contar validaciones previas a ingresos tempranos."
        )
        if cruce_diag:
            st.info(
                "**Desglose SNBE** (misma ventana ampliada hacia atrás que la consulta principal): "
                f"solo tiempo = {cruce_diag.get('n_solo_tiempo_ampliado', '—')}; "
                f"tiempo + `idrutaestacion` UF = {cruce_diag.get('n_tiempo_y_ruta_uf', '—')}; "
                f"+ filtro validación (tipoevento/producto) = {cruce_diag.get('n_mas_filtro_validacion_estricto', '—')}; "
                f"+ `idsam` de buses con ingreso = {cruce_diag.get('n_mas_idsam_buses_ingreso', '—')}. "
                "Si el último valor es **0** y el anterior no, los **idsam** en billetaje no coinciden con los **mean_id** del monitoreo "
                "(se amplían variantes numéricas y se incluye `mean_id` e `idsam` GPS en la consulta)."
            )
        if df_val.empty and snbe_diag:
            st.caption(
                f"**Diagnóstico SNBE (misma ventana horaria local):** filas en `c_transacciones` = "
                f"{snbe_diag.get('filas_en_ventana')}; con `idrutaestacion` ∈ UF = "
                f"{snbe_diag.get('filas_ventana_y_ruta_uf')}. Si el segundo es 0, el catálogo no coincide con SNBE."
            )
        st.subheader("Ingresos por hora (local) y tipo de troncal")
        st.bar_chart(
            por_hora.pivot(index="hora", columns="tipo_troncal", values="n_ingresos").fillna(0),
            use_container_width=True,
        )
        st.subheader("Ingresos por franja, tipo de troncal y origen atribuido")
        st.dataframe(por_franja, use_container_width=True, height=320)

    with tab_evt:
        disp = eventos.copy()
        disp["fecha_hora_ingreso"] = pd.to_datetime(disp["fecha_hora_ingreso"], utc=True).dt.tz_convert(TZ_ASU)
        st.dataframe(
            disp.sort_values("fecha_hora_ingreso"),
            use_container_width=True,
            height=420,
        )
        st.download_button(
            "Descargar eventos CSV",
            disp.to_csv(index=False).encode("utf-8"),
            file_name=f"uf_{id_uf}_eventos_troncales_{fecha}.csv",
            mime="text/csv",
        )

    with tab_val:
        st.markdown(
            "Transacciones en **`public.c_transacciones`** (BD `hostZUREMIT` / `opentransit-prod`). "
            "Filtro por **`idrutaestacion`** (ids de ruta de la UF) y **`idsam`** (buses con ingreso detectado). "
            "El filtro **idproducto / tipoevento** solo se aplica si activó la opción en el panel lateral."
        )
        if snbe_diag:
            with st.expander("Diagnóstico: ¿hay datos SNBE en la ventana?", expanded=df_val.empty):
                st.json({k: v for k, v in snbe_diag.items() if k != "top_idrutaestacion_en_ventana"})
                top = snbe_diag.get("top_idrutaestacion_en_ventana") or []
                if top:
                    st.caption("Rutas con más transacciones ese día (cualquier idrutaestacion):")
                    st.dataframe(pd.DataFrame(top), use_container_width=True)
        if not agg_snbe_ruta.empty:
            st.subheader("Por idrutaestacion de la UF: transacciones e idsam distintos")
            st.dataframe(agg_snbe_ruta, use_container_width=True)

        if det_val is not None and not det_val.empty:
            dshow = det_val.copy()
            dshow["fecha_hora_ingreso"] = pd.to_datetime(
                dshow["fecha_hora_ingreso"], utc=True
            ).dt.tz_convert(TZ_ASU)
            dshow["fechahoraevento"] = pd.to_datetime(dshow["fechahoraevento"], utc=True).dt.tz_convert(TZ_ASU)
            st.subheader("Detalle cruce ingreso ↔ validación (máx. 5000 filas)")
            st.dataframe(dshow.head(5000), use_container_width=True, height=400)
        else:
            st.info(
                "Sin filas en la consulta principal (ruta + idsam + ventana). "
                "Revise el diagnóstico arriba: si hay filas por ruta pero 0 con sus idsam, el mapeo mean_id→idsam no coincide con SNBE."
            )

    st.success("Análisis terminado.")


if __name__ == "__main__":
    main()
