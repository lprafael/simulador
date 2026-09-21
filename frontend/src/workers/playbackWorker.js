/**
 * Playback Web Worker with Linear Interpolation and Event Counting
 * Calculates smooth bus positions and cumulative entry counts.
 */

self.onmessage = function(e) {
  const { type, payload } = e.data;

  if (type === 'INIT') {
    // 1. Group GPS history by bus
    const groupedGps = {};
    payload.history.forEach(h => {
      if (!groupedGps[h.id_bus]) groupedGps[h.id_bus] = [];
      groupedGps[h.id_bus].push({
        ...h,
        _ts: new Date(h.timestamp).getTime()
      });
    });

    for (const id in groupedGps) {
      groupedGps[id].sort((a, b) => a._ts - b._ts);
    }
    self.historyByBus = groupedGps;

    // 2. Group and sort entry events by bus
    const groupedEvents = {};
    (payload.eventos || []).forEach(ev => {
      if (!groupedEvents[ev.id_bus]) groupedEvents[ev.id_bus] = [];
      groupedEvents[ev.id_bus].push({
        ...ev,
        _ts: new Date(ev.timestamp).getTime()
      });
    });

    for (const id in groupedEvents) {
      groupedEvents[id].sort((a, b) => a._ts - b._ts);
    }
    self.eventsByBus = groupedEvents;
    
    const allPoints = payload.history.map(h => new Date(h.timestamp).getTime());
    self.postMessage({ type: 'READY', payload: { 
      startMs: Math.min(...allPoints),
      endMs: Math.max(...allPoints)
    }});
  }

  if (type === 'TICK') {
    const { nextMs } = payload;
    if (!self.historyByBus) return;

    const interpolatedPositions = [];

    for (const idBus in self.historyByBus) {
      const history = self.historyByBus[idBus];
      const events = self.eventsByBus[idBus] || [];
      
      // Count events up to nextMs
      let cumulativeEntries = 0;
      for (const ev of events) {
        if (ev._ts <= nextMs) cumulativeEntries++;
        else break;
      }

      // Interpolation logic
      let p0 = null;
      let p1 = null;

      for (let i = 0; i < history.length; i++) {
        if (history[i]._ts <= nextMs) {
          p0 = history[i];
        } else {
          p1 = history[i];
          break;
        }
      }

      if (p0 && p1) {
        const duration = p1._ts - p0._ts;
        const elapsed = nextMs - p0._ts;
        const t = elapsed / duration;

        interpolatedPositions.push({
          ...p0,
          lat: p0.lat + t * (p1.lat - p0.lat),
          lon: p0.lon + t * (p1.lon - p0.lon),
          numIngresos: cumulativeEntries
        });
      } else if (p0) {
        const age = nextMs - p0._ts;
        if (age < 5 * 60 * 1000) {
          interpolatedPositions.push({
            ...p0,
            numIngresos: cumulativeEntries
          });
        }
      }
    }

    self.postMessage({ 
      type: 'POSITIONS_UPDATE', 
      payload: { 
        buses: interpolatedPositions,
        currentTimeMs: nextMs
      }
    });
  }
};
