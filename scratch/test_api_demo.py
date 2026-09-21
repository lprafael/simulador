
import requests
import json

def test_api_demo():
    url = "http://localhost:8000/api/v1/simulacion/demo"
    print(f"--- Probando API Demo en {url} ---")
    
    try:
        response = requests.post(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] La API respondio correctamente!")
            print(f"Estado: {data.get('estado')}")
            print(f"Linea: {data.get('nombre')}")
            kpis = data.get('kpis', {})
            print(f"KPI - Headway Promedio: {kpis.get('headway_promedio_min')} min")
            print(f"KPI - Regularidad: {kpis.get('regularidad_pct')}%")
            print(f"Total Eventos: {kpis.get('total_eventos')}")
        else:
            print(f"\n[ERROR] La API retorno status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n[ERROR] No se pudo conectar a la API: {e}")

if __name__ == "__main__":
    test_api_demo()
