export const CARTO_API_KEY = import.meta.env.VITE_CARTO_API_KEY || 'cb1_3skd_1_b01311b843bcb7fb316c4384'

export const MAP_TILE_CONFIG = {
  url: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png${CARTO_API_KEY ? `?key=${CARTO_API_KEY}` : ''}`,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  maxZoom: 19,
}
