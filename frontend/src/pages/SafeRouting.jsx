import { useEffect, useMemo, useState } from "react";

import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Circle,
  useMap,
  useMapEvents,
} from "react-leaflet";

import L from "leaflet";

import {
  MapPin,
  ShieldCheck,
  AlertTriangle,
  Route,
  RefreshCw,
} from "lucide-react";

import "leaflet/dist/leaflet.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

/* ============================================================
   DEFAULTS
============================================================ */

const DEFAULT_CENTER = [20.5937, 78.9629];

const DEFAULT_START = {
  lat: 17.290,
  lng: 78.330,
  name: "South Corridor Depot",
};

const DEFAULT_END = {
  lat: 17.340,
  lng: 78.380,
  name: "North-East Sector Gateway",
};

/* ============================================================
   ROUTE PRESETS
============================================================ */

const PRESETS = [
  {
    name: "India Landslide Zone",
    start: {
      lat: 17.290,
      lng: 78.330,
      name: "South Corridor Depot",
    },
    end: {
      lat: 17.340,
      lng: 78.380,
      name: "North-East Sector Gateway",
    },
    center: [17.313, 78.353],
    zoom: 12,
  },

  {
    name: "Nepal Koshi Flood Evacuation",
    start: {
      lat: 26.540,
      lng: 86.780,
      name: "Rajbiraj Relief Depot",
    },
    end: {
      lat: 26.810,
      lng: 87.150,
      name: "Dharan High Ground Haven",
    },
    center: [26.65, 86.95],
    zoom: 10,
  },

  {
    name: "Nepal Melamchi Gorge",
    start: {
      lat: 27.750,
      lng: 85.500,
      name: "Kathmandu Valley Gateway",
    },
    end: {
      lat: 27.920,
      lng: 85.680,
      name: "Helambu Alpine Station",
    },
    center: [27.83, 85.58],
    zoom: 11,
  },
];

/* ============================================================
   LEAFLET ICONS
============================================================ */

const startIcon = L.divIcon({
  className: "",
  html: `
    <div style="
      width:32px;
      height:32px;
      border-radius:50%;
      background:#123F66;
      border:3px solid white;
      box-shadow:0 2px 7px rgba(0,0,0,.25);
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:13px;
      font-weight:600;
    ">S</div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const endIcon = L.divIcon({
  className: "",
  html: `
    <div style="
      width:32px;
      height:32px;
      border-radius:50%;
      background:#356D98;
      border:3px solid white;
      box-shadow:0 2px 7px rgba(0,0,0,.25);
      display:flex;
      align-items:center;
      justify-content:center;
      color:white;
      font-size:13px;
      font-weight:600;
    ">E</div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

/* ============================================================
   GEO HELPERS
============================================================ */

function haversineDistanceKm(a, b) {
  const R = 6371;

  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;

  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;

  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) *
      Math.cos(lat2) *
      Math.sin(dLng / 2) ** 2;

  return 2 * R * Math.asin(Math.sqrt(x));
}

function pointToSegmentDistanceKm(point, start, end) {
  const latScale = 111;

  const lngScale =
    111 *
    Math.cos((point.lat * Math.PI) / 180);

  const px = point.lng * lngScale;
  const py = point.lat * latScale;

  const ax = start.lng * lngScale;
  const ay = start.lat * latScale;

  const bx = end.lng * lngScale;
  const by = end.lat * latScale;

  const dx = bx - ax;
  const dy = by - ay;

  if (dx === 0 && dy === 0) {
    return Math.sqrt(
      (px - ax) ** 2 +
        (py - ay) ** 2
    );
  }

  const t = Math.max(
    0,
    Math.min(
      1,
      ((px - ax) * dx +
        (py - ay) * dy) /
        (dx * dx + dy * dy)
    )
  );

  const closestX = ax + t * dx;
  const closestY = ay + t * dy;

  return Math.sqrt(
    (px - closestX) ** 2 +
      (py - closestY) ** 2
  );
}

/* ============================================================
   ROUTE CALCULATION
============================================================ */

function computeSafeRoute(
  start,
  end,
  hazards,
  safetyBufferKm,
  mode
) {
  const directDistance =
    haversineDistanceKm(start, end);

  const collisions = hazards.filter((hazard) => {
    const distance =
      pointToSegmentDistanceKm(
        hazard,
        start,
        end
      );

    return (
      distance <=
      (hazard.radiusKm || 1) +
        safetyBufferKm
    );
  });

  /* DIRECT ROUTE */

  if (collisions.length === 0) {
    return {
      safe: true,

      route: [
        [start.lat, start.lng],
        [end.lat, end.lng],
      ],

      distance: directDistance,

      collisions: [],

      message:
        "Direct route is clear of detected hazards.",
    };
  }

  /* DETOUR */

  const waypoints = [];

  collisions.forEach((hazard) => {
    const buffer =
      (hazard.radiusKm || 1) +
      safetyBufferKm +
      (mode === "beta" ? 1.5 : 0.7);

    const startBearing =
      Math.atan2(
        end.lng - start.lng,
        end.lat - start.lat
      );

    const offsetAngle =
      startBearing + Math.PI / 2;

    const latOffset =
      (buffer / 111) *
      Math.cos(offsetAngle);

    const lngOffset =
      (buffer /
        (111 *
          Math.cos(
            (hazard.lat * Math.PI) / 180
          ))) *
      Math.sin(offsetAngle);

    waypoints.push({
      lat: hazard.lat + latOffset,
      lng: hazard.lng + lngOffset,
    });
  });

  waypoints.sort((a, b) => {
    return (
      haversineDistanceKm(start, a) -
      haversineDistanceKm(start, b)
    );
  });

  const routePoints = [
    [start.lat, start.lng],

    ...waypoints.map((point) => [
      point.lat,
      point.lng,
    ]),

    [end.lat, end.lng],
  ];

  let totalDistance = 0;

  for (
    let i = 1;
    i < routePoints.length;
    i++
  ) {
    totalDistance +=
      haversineDistanceKm(
        {
          lat: routePoints[i - 1][0],
          lng: routePoints[i - 1][1],
        },
        {
          lat: routePoints[i][0],
          lng: routePoints[i][1],
        }
      );
  }

  return {
    safe: false,

    route: routePoints,

    distance: totalDistance,

    collisions,

    message:
      mode === "beta"
        ? "Wide-clearance detour generated around detected hazards."
        : "Detour generated around detected hazards.",
  };
}

/* ============================================================
   MAP CONTROLLER
============================================================ */

function MapController({ center, zoom }) {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, {
        duration: 0.8,
      });
    }
  }, [center, zoom, map]);

  return null;
}

/* ============================================================
   MAP CLICK HANDLER
============================================================ */

function MapClickHandler({
  selecting,
  onSelect,
}) {
  useMapEvents({
    click(e) {
      if (!selecting) return;

      onSelect({
        lat: Number(
          e.latlng.lat.toFixed(6)
        ),
        lng: Number(
          e.latlng.lng.toFixed(6)
        ),
        name: "Selected map point",
      });
    },
  });

  return null;
}

/* ============================================================
   MAIN COMPONENT
============================================================ */

export default function SafeRouting() {
  const [
    backendConnected,
    setBackendConnected,
  ] = useState(false);

  const [start, setStart] =
    useState(DEFAULT_START);

  const [end, setEnd] =
    useState(DEFAULT_END);

  const [selecting, setSelecting] =
    useState(null);

  const [safetyBuffer, setSafetyBuffer] =
    useState(2);

  const [mode, setMode] =
    useState("alpha");

  const [hazards, setHazards] =
    useState([]);

  const [routeResult, setRouteResult] =
    useState(null);

  const [mapCenter, setMapCenter] =
    useState(DEFAULT_CENTER);

  const [mapZoom, setMapZoom] =
    useState(5);

  const [loading, setLoading] =
    useState(false);

  /* ==========================================================
     BACKEND CHECK
  ========================================================== */

  async function checkBackend() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/health`
      );

      setBackendConnected(response.ok);
    } catch {
      setBackendConnected(false);
    }
  }

  useEffect(() => {
    checkBackend();

    const interval = setInterval(
      checkBackend,
      5000
    );

    return () =>
      clearInterval(interval);
  }, []);

  /* ==========================================================
     LOAD HAZARDS
  ========================================================== */

  async function loadHazards() {
    setLoading(true);

    try {
      const [
        landslideResponse,
        floodResponse,
      ] = await Promise.all([
        fetch(
          `${API_BASE_URL}/api/landslide`
        ),
        fetch(
          `${API_BASE_URL}/api/flood`
        ),
      ]);

      const loadedHazards = [];

      /* LANDSLIDES */

      if (landslideResponse.ok) {
        const data =
          await landslideResponse.json();

        const items =
          Array.isArray(data)
            ? data
            : data?.hazards ||
              data?.regions ||
              [];

        items.forEach((item, index) => {
          if (
            item.lat !== undefined &&
            item.lng !== undefined
          ) {
            loadedHazards.push({
              id: `landslide-${index}`,

              lat: Number(item.lat),

              lng: Number(item.lng),

              radiusKm: Number(
                item.radiusKm ||
                  item.radius ||
                  1
              ),

              type: "LANDSLIDE",

              name:
                item.name ||
                `Landslide Zone ${index + 1}`,
            });
          }
        });
      }

      /* FLOODS */

      if (floodResponse.ok) {
        const data =
          await floodResponse.json();

        const items =
          Array.isArray(data)
            ? data
            : data?.hazards ||
              data?.regions ||
              [];

        items.forEach((item, index) => {
          if (
            item.lat !== undefined &&
            item.lng !== undefined
          ) {
            loadedHazards.push({
              id: `flood-${index}`,

              lat: Number(item.lat),

              lng: Number(item.lng),

              radiusKm: Number(
                item.radiusKm ||
                  item.radius ||
                  1
              ),

              type: "FLOOD",

              name:
                item.name ||
                `Flood Zone ${index + 1}`,
            });
          }
        });
      }

      setHazards(loadedHazards);
    } catch (error) {
      console.error(
        "Hazard loading failed:",
        error
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHazards();
  }, []);

  /* ==========================================================
     CALCULATE ROUTE
  ========================================================== */

  function calculateRoute() {
    if (!start || !end) return;

    const result =
      computeSafeRoute(
        start,
        end,
        hazards,
        safetyBuffer,
        mode
      );

    setRouteResult(result);

    setMapCenter([
      (start.lat + end.lat) / 2,
      (start.lng + end.lng) / 2,
    ]);

    setMapZoom(11);
  }

  /* ==========================================================
     MAP SELECTION
  ========================================================== */

  function handleMapSelect(point) {
    if (selecting === "start") {
      setStart(point);
    }

    if (selecting === "end") {
      setEnd(point);
    }

    setSelecting(null);
  }

  /* ==========================================================
     PRESET
  ========================================================== */

  function applyPreset(preset) {
    setStart(preset.start);
    setEnd(preset.end);
    setRouteResult(null);
    setMapCenter(preset.center);
    setMapZoom(preset.zoom);
  }

  /* ==========================================================
     ROUTE STATS
  ========================================================== */

  const routeDistance = useMemo(() => {
    if (!routeResult) return 0;

    return routeResult.distance;
  }, [routeResult]);

  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#243447]">

      {/* ====================================================
          PAGE HEADER
      ==================================================== */}

      <section className="bg-white border-b border-[#D9E0E7]">
        <div className="max-w-7xl mx-auto px-6 py-8">

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">

            <div>
              <p className="text-sm font-medium text-[#123F66]">
                VEYRiX Navigation
              </p>

              <h1 className="text-3xl md:text-4xl font-semibold text-[#123F66] mt-2">
                Safe Routing
              </h1>

              <p className="text-[#667085] mt-2">
                Disaster-aware route planning using detected hazard zones.
              </p>
            </div>

            {/* BACKEND STATUS */}

            <div
              className={`flex items-center gap-2 px-4 py-2 border text-sm font-medium ${
                backendConnected
                  ? "bg-[#E8F5E9] text-[#2E7D32] border-[#A5D6A7]"
                  : "bg-[#FDECEC] text-[#C62828] border-[#EF9A9A]"
              }`}
            >
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  backendConnected
                    ? "bg-[#2E7D32]"
                    : "bg-[#C62828]"
                }`}
              />

              {backendConnected
                ? "Routing system connected"
                : "Routing system disconnected"}
            </div>

          </div>
        </div>
      </section>

      {/* ====================================================
          CONTROLS
      ==================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-6">

        <div className="bg-white border border-[#D9E0E7] p-6">

          {/* PRESETS */}

          <div>
            <h2 className="font-semibold text-[#123F66] mb-3">
              Route Presets
            </h2>

            <div className="flex flex-wrap gap-2">

              {PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() =>
                    applyPreset(preset)
                  }
                  className="
                    px-4
                    py-2
                    text-sm
                    bg-[#F8FAFC]
                    text-[#526579]
                    border
                    border-[#D9E0E7]
                    hover:border-[#123F66]
                    hover:text-[#123F66]
                    transition
                  "
                >
                  {preset.name}
                </button>
              ))}

            </div>
          </div>

          {/* START / END */}

          <div className="grid md:grid-cols-2 gap-6 mt-7">

            {/* START */}

            <div>
              <label className="block text-sm font-medium text-[#243447] mb-2">
                Start Point
              </label>

              <div className="flex gap-2">

                <div className="flex-1 px-4 py-3 border border-[#D9E0E7] bg-[#F8FAFC] text-sm text-[#667085]">
                  {start.lat.toFixed(5)},{" "}
                  {start.lng.toFixed(5)}
                </div>

                <button
                  onClick={() =>
                    setSelecting("start")
                  }
                  className={`
                    px-4
                    border
                    transition
                    ${
                      selecting === "start"
                        ? "bg-[#EAF2F8] border-[#123F66] text-[#123F66]"
                        : "bg-white border-[#D9E0E7] text-[#526579] hover:border-[#123F66]"
                    }
                  `}
                  aria-label="Select start point on map"
                >
                  <MapPin size={18} />
                </button>

              </div>
            </div>

            {/* END */}

            <div>
              <label className="block text-sm font-medium text-[#243447] mb-2">
                Destination
              </label>

              <div className="flex gap-2">

                <div className="flex-1 px-4 py-3 border border-[#D9E0E7] bg-[#F8FAFC] text-sm text-[#667085]">
                  {end.lat.toFixed(5)},{" "}
                  {end.lng.toFixed(5)}
                </div>

                <button
                  onClick={() =>
                    setSelecting("end")
                  }
                  className={`
                    px-4
                    border
                    transition
                    ${
                      selecting === "end"
                        ? "bg-[#EAF2F8] border-[#123F66] text-[#123F66]"
                        : "bg-white border-[#D9E0E7] text-[#526579] hover:border-[#123F66]"
                    }
                  `}
                  aria-label="Select destination on map"
                >
                  <MapPin size={18} />
                </button>

              </div>
            </div>

          </div>

          {/* BUFFER / MODE */}

          <div className="grid md:grid-cols-2 gap-8 mt-7">

            {/* BUFFER */}

            <div>
              <div className="flex justify-between mb-2">

                <label className="text-sm font-medium text-[#243447]">
                  Safety Buffer
                </label>

                <span className="text-sm font-semibold text-[#123F66]">
                  {safetyBuffer} km
                </span>

              </div>

              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={safetyBuffer}
                onChange={(e) =>
                  setSafetyBuffer(
                    Number(e.target.value)
                  )
                }
                className="w-full accent-[#123F66]"
              />
            </div>

            {/* MODE */}

            <div>
              <label className="block text-sm font-medium text-[#243447] mb-2">
                Route Mode
              </label>

              <div className="flex gap-2">

                <button
                  onClick={() =>
                    setMode("alpha")
                  }
                  className={`
                    flex-1
                    py-2.5
                    border
                    text-sm
                    transition
                    ${
                      mode === "alpha"
                        ? "bg-[#123F66] text-white border-[#123F66]"
                        : "bg-white border-[#D9E0E7] text-[#526579] hover:border-[#123F66]"
                    }
                  `}
                >
                  Alpha — Shortest
                </button>

                <button
                  onClick={() =>
                    setMode("beta")
                  }
                  className={`
                    flex-1
                    py-2.5
                    border
                    text-sm
                    transition
                    ${
                      mode === "beta"
                        ? "bg-[#123F66] text-white border-[#123F66]"
                        : "bg-white border-[#D9E0E7] text-[#526579] hover:border-[#123F66]"
                    }
                  `}
                >
                  Beta — Safer
                </button>

              </div>
            </div>

          </div>

          {/* ACTIONS */}

          <div className="mt-7 flex flex-wrap gap-3">

            <button
              onClick={calculateRoute}
              className="
                flex
                items-center
                gap-2
                px-6
                py-3
                bg-[#123F66]
                text-white
                font-medium
                hover:bg-[#0E3150]
                transition
              "
            >
              <Route size={18} />
              Calculate Safe Route
            </button>

            <button
              onClick={loadHazards}
              className="
                flex
                items-center
                gap-2
                px-5
                py-3
                border
                border-[#D9E0E7]
                bg-white
                text-[#526579]
                hover:border-[#123F66]
                hover:text-[#123F66]
                transition
              "
            >
              <RefreshCw
                size={17}
                className={
                  loading
                    ? "animate-spin"
                    : ""
                }
              />

              Refresh Hazards
            </button>

          </div>

          {/* MAP SELECTION */}

          {selecting && (
            <div className="mt-5 px-4 py-3 bg-[#EAF2F8] border border-[#C8D9E7] text-sm text-[#526579]">

              Click anywhere on the map to select the{" "}

              <strong className="text-[#123F66]">
                {selecting === "start"
                  ? "start point"
                  : "destination"}
              </strong>
              .

            </div>
          )}

        </div>
      </section>

      {/* ====================================================
          RESULT
      ==================================================== */}

      {routeResult && (
        <section className="max-w-7xl mx-auto px-6 pb-6">

          <div className="bg-white border border-[#D9E0E7] p-5">

            <div className="flex items-start gap-4">

              <div
                className={`
                  w-10
                  h-10
                  flex
                  items-center
                  justify-center
                  border
                  ${
                    routeResult.safe
                      ? "bg-[#EAF2F8] border-[#C8D9E7] text-[#123F66]"
                      : "bg-[#F1F5F8] border-[#C8D9E7] text-[#123F66]"
                  }
                `}
              >
                {routeResult.safe ? (
                  <ShieldCheck size={21} />
                ) : (
                  <AlertTriangle size={21} />
                )}
              </div>

              <div className="flex-1">

                <h2 className="font-semibold text-[#123F66]">
                  {routeResult.safe
                    ? "Route is Safe"
                    : "Hazards Detected — Detour Generated"}
                </h2>

                <p className="text-sm text-[#667085] mt-1">
                  {routeResult.message}
                </p>

                <div className="flex flex-wrap gap-x-8 gap-y-2 mt-4 text-sm text-[#526579]">

                  <span>
                    <strong className="text-[#243447]">
                      Distance:
                    </strong>{" "}
                    {routeDistance.toFixed(2)} km
                  </span>

                  <span>
                    <strong className="text-[#243447]">
                      Hazards:
                    </strong>{" "}
                    {routeResult.collisions.length}
                  </span>

                  <span>
                    <strong className="text-[#243447]">
                      Mode:
                    </strong>{" "}
                    {mode === "alpha"
                      ? "Shortest"
                      : "Wide Clearance"}
                  </span>

                </div>

              </div>

            </div>

          </div>
        </section>
      )}

      {/* ====================================================
          MAP
      ==================================================== */}

      <section className="max-w-7xl mx-auto px-6 pb-12">

        <div className="border border-[#D9E0E7] bg-white overflow-hidden">

          <div className="h-[650px]">

            <MapContainer
              center={DEFAULT_CENTER}
              zoom={5}
              minZoom={3}
              maxZoom={18}
              scrollWheelZoom={true}
              className="h-full w-full"
            >

              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <MapController
                center={mapCenter}
                zoom={mapZoom}
              />

              <MapClickHandler
                selecting={selecting}
                onSelect={handleMapSelect}
              />

              {/* START */}

              <Marker
                position={[
                  start.lat,
                  start.lng,
                ]}
                icon={startIcon}
              />

              {/* END */}

              <Marker
                position={[
                  end.lat,
                  end.lng,
                ]}
                icon={endIcon}
              />

              {/* DIRECT ROUTE */}

              {!routeResult && (
                <Polyline
                  positions={[
                    [
                      start.lat,
                      start.lng,
                    ],
                    [
                      end.lat,
                      end.lng,
                    ],
                  ]}
                  pathOptions={{
                    color: "#356D98",
                    weight: 4,
                    dashArray: "8 8",
                  }}
                />
              )}

              {/* CALCULATED ROUTE */}

              {routeResult && (
                <Polyline
                  positions={routeResult.route}
                  pathOptions={{
                    color: "#123F66",
                    weight: 6,
                  }}
                />
              )}

              {/* HAZARDS */}

              {hazards.map((hazard) => {

                const collided =
                  routeResult?.collisions?.some(
                    (item) =>
                      item.id === hazard.id
                  );

                return (
                  <Circle
                    key={hazard.id}
                    center={[
                      hazard.lat,
                      hazard.lng,
                    ]}
                    radius={
                      ((hazard.radiusKm || 1) +
                        safetyBuffer) *
                      1000
                    }
                    pathOptions={{
                      color: "#123F66",
                      fillColor: collided
                        ? "#356D98"
                        : "#7FA4C2",
                      fillOpacity: 0.20,
                      weight: collided
                        ? 3
                        : 2,
                    }}
                  />
                );
              })}

            </MapContainer>

          </div>

        </div>

      </section>

    </main>
  );
}