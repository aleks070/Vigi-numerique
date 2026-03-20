import { useEffect, useState, useRef } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ─── Couleurs par état réseau ─────────────────────────────────
const STATE_COLORS = {
  nominal:          '#10B981',
  sous_surveillance: '#F59E0B',
  degrade:          '#F97316',
  perturbe:         '#EF4444',
  incident_majeur:  '#7C3AED',
}

const STATE_LABELS = {
  nominal:          'Nominal',
  sous_surveillance: 'Surveillance',
  degrade:          'Dégradé',
  perturbe:         'Perturbé',
  incident_majeur:  'Incident majeur',
}

export default function Map() {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const [layers, setLayers] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  // ── Chargement des données ────────────────────────────────
  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/map/layers`)
        setLayers(res.data)
      } catch (e) {
        console.error('Erreur chargement carte:', e)
      } finally {
        setLoading(false)
      }
    }
    load()
    const interval = setInterval(load, 60000)
    return () => clearInterval(interval)
  }, [])

  // ── Initialisation Leaflet ────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Import dynamique de Leaflet
    import('leaflet').then(L => {
      // Fix icônes Leaflet avec Vite
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      // Centré sur l'Île-de-France
      const map = L.map(mapRef.current, {
        center: [48.8566, 2.3522],
        zoom: 11,
        zoomControl: true,
      })

      // Fond de carte OpenStreetMap
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
      }).addTo(map)

      mapInstanceRef.current = { map, L, markersLayer: null }
    })

    return () => {
      if (mapInstanceRef.current?.map) {
        mapInstanceRef.current.map.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // ── Mise à jour des markers ───────────────────────────────
  useEffect(() => {
    if (!layers || !mapInstanceRef.current) return

    const { map, L, markersLayer } = mapInstanceRef.current

    // Supprime les anciens markers
    if (markersLayer) {
      markersLayer.clearLayers()
    }

    const newLayer = L.layerGroup().addTo(map)

    // ── Stations ─────────────────────────────────────────────
    layers.stations.features.forEach(feature => {
      const { stop_name, network_state, anomaly_score, stop_id } = feature.properties
      const [lon, lat] = feature.geometry.coordinates
      const color = STATE_COLORS[network_state] || STATE_COLORS.nominal

      const marker = L.circleMarker([lat, lon], {
        radius: network_state === 'nominal' ? 6 : 9,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      })

      marker.bindTooltip(stop_name, {
        permanent: false,
        direction: 'top',
        className: 'leaflet-tooltip-vigi',
      })

      marker.on('click', () => {
        setSelected({
          type: 'station',
          name: stop_name,
          state: network_state,
          score: anomaly_score,
          id: stop_id,
        })
      })

      marker.addTo(newLayer)
    })

    // ── Incidents ─────────────────────────────────────────────
    layers.incidents.features.forEach(feature => {
      const { line_id, label, description, stop_name } = feature.properties
      const [lon, lat] = feature.geometry.coordinates

      const icon = L.divIcon({
        html: `<div style="
          background: #EF4444; color: white;
          border-radius: 50%; width: 24px; height: 24px;
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 700; border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">!</div>`,
        className: '',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      })

      const marker = L.marker([lat, lon], { icon })
      marker.bindTooltip(`Incident — ${line_id}`, { direction: 'top' })
      marker.on('click', () => {
        setSelected({
          type: 'incident',
          name: stop_name || line_id,
          line: line_id,
          label: label || 'Incident officiel',
          description,
        })
      })
      marker.addTo(newLayer)
    })

    mapInstanceRef.current.markersLayer = newLayer

  }, [layers])

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 108px)' }}>

      {/* ── Carte ── */}
      <div style={{ flex: 1, position: 'relative' }}>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        />

        {loading && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(255,255,255,0.8)', borderRadius: 'var(--radius)',
            fontSize: 13, color: 'var(--text-muted)',
          }}>
            Chargement de la carte...
          </div>
        )}

        <div
          ref={mapRef}
          style={{
            width: '100%', height: '100%',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border)',
            overflow: 'hidden',
          }}
        />

        {/* Légende */}
        <div style={{
          position: 'absolute', bottom: 24, left: 24, zIndex: 1000,
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius)', padding: '12px 14px',
          boxShadow: 'var(--shadow-md)',
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            État réseau
          </div>
          {Object.entries(STATE_LABELS).map(([state, label]) => (
            <div key={state} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <div style={{
                width: 10, height: 10, borderRadius: '50%',
                background: STATE_COLORS[state],
              }} />
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
            </div>
          ))}
        </div>

        {/* Compteurs */}
        {layers && (
          <div style={{
            position: 'absolute', top: 16, right: 16, zIndex: 1000,
            display: 'flex', gap: 8,
          }}>
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)', padding: '6px 12px',
              fontSize: 12, color: 'var(--text-secondary)',
            }}>
              {layers.meta.stations_count} stations
            </div>
            {layers.meta.incidents_count > 0 && (
              <div style={{
                background: 'var(--perturbe-bg)', border: '1px solid var(--perturbe)',
                borderRadius: 'var(--radius-sm)', padding: '6px 12px',
                fontSize: 12, color: 'var(--perturbe)', fontWeight: 500,
              }}>
                {layers.meta.incidents_count} incident(s)
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Panneau détail ── */}
      <div style={{
        width: 280, background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: 16,
        display: 'flex', flexDirection: 'column', gap: 12,
        overflowY: 'auto',
      }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          Détail
        </div>

        {!selected ? (
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
            Cliquez sur une station ou un incident pour voir les détails.
          </div>
        ) : selected.type === 'station' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Station</div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{selected.name}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>État</div>
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '3px 10px', borderRadius: 20,
                fontSize: 11, fontWeight: 600,
                background: `${STATE_COLORS[selected.state]}20`,
                color: STATE_COLORS[selected.state],
              }}>
                {STATE_LABELS[selected.state]}
              </span>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Score d'anomalie</div>
              <div style={{ fontSize: 28, fontWeight: 300, fontFamily: 'DM Mono, monospace' }}>
                {Math.round(selected.score)}<span style={{ fontSize: 13, color: 'var(--text-muted)' }}>/100</span>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Incident officiel</div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{selected.label}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Ligne</div>
              <div style={{ fontSize: 13 }}>{selected.line}</div>
            </div>
            {selected.description && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>Description</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{selected.description}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}