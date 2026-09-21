# Lógica Avanzada de Cálculo: Matriz Origen-Destino (OD)

Este documento detalla la metodología técnica para la estimación de matrices OD en el sistema de transporte, específicamente para entornos donde el usuario solo registra su entrada (Tap-in) y no su salida.

---

## 1. El Desafío del "Tap-in Only"
En el sistema de billetaje electrónico de Paraguay, solo conocemos el punto de ascenso. Para planificar infraestructura y optimizar frecuencias, es imperativo conocer el destino. La metodología propuesta utiliza **Inferencia de Destino por Encadenamiento (Trip Chaining)**.

---

## 2. Algoritmo de Estimación Avanzada

El proceso se divide en cuatro fases críticas:

### Fase 1: Preparación y Enriquecimiento de Datos
1.  **Limpieza:** Filtrado de transacciones inválidas o duplicadas.
2.  **Georreferenciación:** Cruce de cada `transaccion_id` con la posición GPS del bus (`AVL`) y el `id_paradero` más cercano en ese instante.
3.  **Identificación de Usuario:** Agrupamiento por `id_tarjeta` y ordenamiento cronológico por día.

### Fase 2: Identificación de Etapas y Viajes (Journeys)
No todos los ascensos son viajes nuevos; muchos son **transbordos**.
*   **Criterio de Transbordo:** Si el tiempo entre el descenso estimado del bus A y el ascenso al bus B es menor a **X minutos** (ej. 60 min) y la distancia es menor a **Y metros**, se considera una "etapa" del mismo viaje.
*   **Criterio de Viaje Nuevo:** Si el tiempo supera el umbral, se considera que el usuario realizó una actividad en su destino previo.

### Fase 3: Inferencia de Destino (Core Logic)
El destino de la etapa $n$ se infiere según las siguientes reglas de prioridad:

1.  **Regla del Próximo Ascenso:** El destino de la etapa $i$ es el paradero de origen de la etapa $i+1$.
    *   *Refinamiento:* Se busca el paradero de la ruta de la etapa $i$ más cercano al origen de $i+1$.
2.  **Regla del Cierre Diario (Retorno al Hogar):** Para la última etapa del día, el destino es el paradero de origen de la **primera etapa** del día del mismo usuario.
3.  **Regla de Probabilidad de Ruta:** Si el usuario no vuelve a aparecer en el sistema ese día, se estima el destino basándose en el paradero de mayor descenso histórico de esa línea/ruta.

### Fase 4: Validación Espacial y Temporal
*   **Consistencia de Velocidad:** Se verifica que el tiempo entre etapas permita el desplazamiento físico.
*   **Accesibilidad:** El paradero de destino inferido debe pertenecer a la secuencia de paradas de la línea que el usuario abordó.

---

## 3. Estructura de la Matriz Final

La matriz no solo es una tabla de Excel, sino un objeto multidimensional:

| Origen (Zona/Paradero) | Destino (Zona/Paradero) | Franja Horaria | Tipo de Día | Cantidad de Viajes |
| :--- | :--- | :--- | :--- | :--- |
| Terminal Asunción | Campus UNA | 07:00 - 08:00 | Laboral | 1,240 |
| Luque Centro | Microcentro | 06:00 - 07:00 | Laboral | 2,850 |

---

## 4. Ventajas de la Versión Avanzada
*   **Cálculo de Tiempos de Viaje:** Al tener origen y destino estimado, podemos calcular la duración promedio del viaje "puerta a puerta".
*   **Análisis de Transbordos:** Identifica los puntos calientes donde la infraestructura de transbordo necesita mejoras.
*   **Matrices por Propósito:** Permite diferenciar viajes de estudio/trabajo (mañana) vs compras/ocio.

---
> [!IMPORTANT]
> Esta lógica permite una precisión estimada del **80-85%** en sistemas metropolitanos, eliminando la necesidad de encuestas manuales costosas.
