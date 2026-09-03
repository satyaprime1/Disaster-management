import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Circle,
  Popup,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const DEFAULT_CENTER = [22.5, 82.0];

function MapController({ center, zoom }) {
  const map = useMap();

  useEffect(() => {
    map.flyTo(center, zoom, {
      duration: 1.2,
    });
  }, [center, zoom, map]);

  return null;
}

export default function Satellite() {
  const [landslideGeoJSON, setLandslideGeoJSON] = useState(null);
  const [floodGeoJSON, setFloodGeoJSON] = useState(null);

  const [landslideData, setLandslideData] = useState(null);
  const [floodData, setFloodData] = useState(null);

  const [showLandslides, setShowLandslides] = useState(true);
  const [showFloods, setShowFloods] = useState(true);
  const [showBuffers, setShowBuffers] = useState(true);

  const [mapType, setMapType] = useState("satellite");

  const [mapCenter, setMapCenter] = useState(DEFAULT_CENTER);
  const [mapZoom, setMapZoom] = useState(5);

  const [selectedHazard, setSelectedHazard] = useState(null);

  const [loading, setLoading] = useState(true);
  const [liveStatus, setLiveStatus] = useState(false);

  // Backend connection status
  const [backendConnected, setBackendConnected] = useState(false);

  // ============================================================
  // LOAD STATIC FALLBACK DATA
  // ============================================================

  useEffect(() => {
    async function loadFallbackData() {
      try {
        const [
          landslideGeo,
          floodGeo,
          landslidePred,
          floodPred,
        ] = await Promise.all([
          fetch("/data/landslide_regions.json").then((r) => r.json()),
          fetch("/data/flood_regions.json").then((r) => r.json()),
          fetch("/data/prediction_results.json").then((r) => r.json()),
          fetch("/data/flood_prediction_results.json").then((r) => r.json()),
        ]);

        setLandslideGeoJSON(landslideGeo);
        setFloodGeoJSON(floodGeo);
        setLandslideData(landslidePred);
        setFloodData(floodPred);
      } catch (error) {
        console.error("Fallback satellite data error:", error);
      }
    }

    loadFallbackData();
  }, []);

  // ============================================================
  // CHECK BACKEND CONNECTION
  // ============================================================

  useEffect(() => {
    let mounted = true;

    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);

        if (!mounted) return;

        setBackendConnected(response.ok);
      } catch (error) {
        if (!mounted) return;

        setBackendConnected(false);
      }
    }

    checkBackend();

    const interval = setInterval(checkBackend, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // ============================================================
  // FETCH LIVE SATELLITE DATA
  // ============================================================

  useEffect(() => {
    let mounted = true;

    async function fetchLiveData() {
      try {
        const responses = await Promise.allSettled([
          fetch(`${API_BASE_URL}/api/landslide`).then((r) => r.json()),
          fetch(`${API_BASE_URL}/api/flood`).then((r) => r.json()),
          fetch(`${API_BASE_URL}/api/landslide/geojson`).then((r) =>
            r.json()
          ),
          fetch(`${API_BASE_URL}/api/flood/geojson`).then((r) =>
            r.json()
          ),
        ]);

        if (!mounted) return;

        let receivedLiveData = false;

        if (
          responses[0].status === "fulfilled" &&
          responses[0].value?.available
        ) {
          setLandslideData(responses[0].value);
          receivedLiveData = true;
        }

        if (
          responses[1].status === "fulfilled" &&
          responses[1].value?.available
        ) {
          setFloodData(responses[1].value);
          receivedLiveData = true;
        }

        if (
          responses[2].status === "fulfilled" &&
          responses[2].value?.features?.length
        ) {
          setLandslideGeoJSON(responses[2].value);
          receivedLiveData = true;
        }

        if (
          responses[3].status === "fulfilled" &&
          responses[3].value?.features?.length
        ) {
          setFloodGeoJSON(responses[3].value);
          receivedLiveData = true;
        }

        setLiveStatus(receivedLiveData);
      } catch (error) {
        console.warn("Satellite API unavailable:", error);
        setLiveStatus(false);
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchLiveData();

    const interval = setInterval(fetchLiveData, 15000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // ============================================================
  // HAZARD SUMMARY
  // ============================================================

  const landslideCount =
    landslideData?.affected_regions?.length ||
    landslideGeoJSON?.features?.length ||
    0;

  const floodCount =
    floodData?.coordinates?.length ||
    floodGeoJSON?.features?.length ||
    0;

  const landslidePeak =
    landslideData?.maximum_probability != null
      ? (landslideData.maximum_probability * 100).toFixed(2)
      : "—";

  const floodPeak =
    floodData?.maximum_mndwi != null
      ? floodData.maximum_mndwi.toFixed(3)
      : "—";

  // ============================================================
  // HAZARD MARKERS
  // ============================================================

  const hazards = useMemo(() => {
    const result = [];

    if (landslideData?.affected_regions) {
      landslideData.affected_regions.forEach((region) => {
        result.push({
          id: `LS-${region.region_id}`,
          type: "LANDSLIDE",
          name: `Landslide Zone #${region.region_id}`,
          lat: region.latitude,
          lng: region.longitude,
          probability: region.max_probability || 0,
          radius: 1200,
          country: "India",
          affectedPixels: region.affected_pixels,
        });
      });
    }

    if (floodData?.coordinates) {
      floodData.coordinates.forEach((region) => {
        result.push({
          id: `FL-${region.region_id}`,
          type: "FLOOD",
          name:
            region.name ||
            `Flood Zone #${region.region_id}`,
          lat: region.latitude,
          lng: region.longitude,
          probability: region.probability || 0,
          radius: 1800,
          country: region.country || "Nepal",
        });
      });
    }

    return result;
  }, [landslideData, floodData]);

  // ============================================================
  // MAP LAYERS
  // ============================================================

  const tileUrl =
    mapType === "satellite"
      ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      : mapType === "dark"
      ? "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
      : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  // ============================================================
  // REGION NAVIGATION
  // ============================================================

  function showLandslideRegion() {
    setMapCenter([17.313, 78.353]);
    setMapZoom(11);
    setSelectedHazard(null);
  }

  function showFloodRegion() {
    setMapCenter([26.65, 86.95]);
    setMapZoom(9);
    setSelectedHazard(null);
  }

  function showSouthAsia() {
    setMapCenter(DEFAULT_CENTER);
    setMapZoom(5);
    setSelectedHazard(null);
  }

  function focusHazard(hazard) {
    setSelectedHazard(hazard);
    setMapCenter([hazard.lat, hazard.lng]);
    setMapZoom(13);
  }

  return (
    <div className="bg-[#F5F7FA] min-h-screen">

      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">

            <div>
              <div className="flex items-center gap-3">

                <div className="w-11 h-11 rounded-lg bg-[#123F66] text-white flex items-center justify-center text-xl">
                  🛰️
                </div>

                <div>
                  <h1 className="text-3xl font-bold text-[#123F66]">
                    Satellite Monitoring
                  </h1>

                  <p className="text-gray-500 mt-1">
                    AI-powered satellite hazard detection and geospatial monitoring
                  </p>
                </div>

              </div>
            </div>

            {/* Backend Status */}

            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${
                backendConnected
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  backendConnected
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />

              {backendConnected
                ? "BACKEND CONNECTED"
                : "BACKEND DISCONNECTED"}
            </div>

          </div>

        </div>
      </section>


      {/* ======================================================
          STAT CARDS
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-6">

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

          {/* Landslide */}

          <div className="bg-white border border-gray-200 rounded-xl p-5">

            <p className="text-sm text-gray-500">
              Landslide Zones
            </p>

            <p className="text-3xl font-bold text-[#123F66] mt-2">
              {loading ? "..." : landslideCount}
            </p>

            <p className="text-xs text-gray-500 mt-1">
              Peak probability: {landslidePeak}%
            </p>

          </div>


          {/* Flood */}

          <div className="bg-white border border-gray-200 rounded-xl p-5">

            <p className="text-sm text-gray-500">
              Flood Zones
            </p>

            <p className="text-3xl font-bold text-[#123F66] mt-2">
              {loading ? "..." : floodCount}
            </p>

            <p className="text-xs text-gray-500 mt-1">
              Maximum MNDWI: {floodPeak}
            </p>

          </div>


          {/* Landslide Model */}

          <div className="bg-white border border-gray-200 rounded-xl p-5">

            <p className="text-sm text-gray-500">
              Landslide Model
            </p>

            <p className="text-lg font-bold text-[#123F66] mt-2">
              Attention-ResUNet
            </p>

            <p className="text-xs text-gray-500 mt-1">
              Multispectral + topography
            </p>

          </div>


          {/* Flood Model */}

          <div className="bg-white border border-gray-200 rounded-xl p-5">

            <p className="text-sm text-gray-500">
              Flood Detection
            </p>

            <p className="text-lg font-bold text-[#123F66] mt-2">
              MNDWI + SAR
            </p>

            <p className="text-xs text-gray-500 mt-1">
              Sentinel-1 / Sentinel-2
            </p>

          </div>

        </div>

      </section>


      {/* ======================================================
          MAP CONTROLS
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 pb-4">

        <div className="bg-white border border-gray-200 rounded-xl p-5">

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">

            {/* Map type */}

            <div>

              <p className="text-sm font-semibold text-gray-700 mb-2">
                Base Map
              </p>

              <div className="flex flex-wrap gap-2">

                <button
                  onClick={() => setMapType("satellite")}
                  className={`px-4 py-2 rounded-lg text-sm border transition ${
                    mapType === "satellite"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-gray-600 border-gray-200 hover:border-[#123F66]"
                  }`}
                >
                  🛰️ Satellite
                </button>

                <button
                  onClick={() => setMapType("dark")}
                  className={`px-4 py-2 rounded-lg text-sm border transition ${
                    mapType === "dark"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-gray-600 border-gray-200 hover:border-[#123F66]"
                  }`}
                >
                  🌑 Dark
                </button>

                <button
                  onClick={() => setMapType("osm")}
                  className={`px-4 py-2 rounded-lg text-sm border transition ${
                    mapType === "osm"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-gray-600 border-gray-200 hover:border-[#123F66]"
                  }`}
                >
                  🗺️ Standard
                </button>

              </div>

            </div>


            {/* Region navigation */}

            <div>

              <p className="text-sm font-semibold text-gray-700 mb-2">
                Jump to Region
              </p>

              <div className="flex flex-wrap gap-2">

                <button
                  onClick={showLandslideRegion}
                  className="px-4 py-2 rounded-lg text-sm bg-red-50 text-red-700 border border-red-100 hover:bg-red-100"
                >
                  🌋 India Landslides
                </button>

                <button
                  onClick={showFloodRegion}
                  className="px-4 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100"
                >
                  🌊 Nepal Floods
                </button>

                <button
                  onClick={showSouthAsia}
                  className="px-4 py-2 rounded-lg text-sm bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100"
                >
                  🌏 South Asia
                </button>

              </div>

            </div>

          </div>


          {/* Layer toggles */}

          <div className="flex flex-wrap gap-5 mt-5 pt-4 border-t border-gray-100">

            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">

              <input
                type="checkbox"
                checked={showLandslides}
                onChange={(e) =>
                  setShowLandslides(e.target.checked)
                }
              />

              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />

              Landslide Zones

            </label>


            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">

              <input
                type="checkbox"
                checked={showFloods}
                onChange={(e) =>
                  setShowFloods(e.target.checked)
                }
              />

              <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />

              Flood Zones

            </label>


            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">

              <input
                type="checkbox"
                checked={showBuffers}
                onChange={(e) =>
                  setShowBuffers(e.target.checked)
                }
              />

              <span className="w-2.5 h-2.5 rounded-full bg-gray-500" />

              Danger Buffers

            </label>

          </div>

        </div>

      </section>


      {/* ======================================================
          MAP
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6">

        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">

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
                attribution="&copy; Esri & OpenStreetMap"
                url={tileUrl}
              />

              <MapController
                center={mapCenter}
                zoom={mapZoom}
              />


              {/* ==================================================
                  LANDSLIDE GEOJSON
              ================================================== */}

              {showLandslides && landslideGeoJSON && (
                <GeoJSON
                  key={`landslide-${landslideGeoJSON.features?.length}`}
                  data={landslideGeoJSON}
                  style={{
                    color: "#dc2626",
                    weight: 2,
                    fillColor: "#ef4444",
                    fillOpacity: 0.35,
                  }}
                  onEachFeature={(feature, layer) => {

                    const properties =
                      feature.properties || {};

                    layer.bindPopup(`
                      <div style="min-width:200px">
                        <strong>🌋 Landslide Zone</strong>
                        <br/>
                        Region: ${
                          properties.region_id ?? "Unknown"
                        }
                        <br/>
                        Probability: ${
                          properties.max_probability
                            ? (
                                properties.max_probability * 100
                              ).toFixed(2) + "%"
                            : "Unknown"
                        }
                        <br/>
                        Affected Pixels: ${
                          properties.affected_pixels ??
                          "Unknown"
                        }
                      </div>
                    `);

                  }}
                />
              )}


              {/* ==================================================
                  FLOOD GEOJSON
              ================================================== */}

              {showFloods && floodGeoJSON && (
                <GeoJSON
                  key={`flood-${floodGeoJSON.features?.length}`}
                  data={floodGeoJSON}
                  style={{
                    color: "#0891b2",
                    weight: 2,
                    fillColor: "#06b6d4",
                    fillOpacity: 0.35,
                  }}
                  onEachFeature={(feature, layer) => {

                    const properties =
                      feature.properties || {};

                    layer.bindPopup(`
                      <div style="min-width:220px">
                        <strong>🌊 Flood Zone</strong>
                        <br/>
                        ${
                          properties.name ||
                          "Flood affected region"
                        }
                        <br/>
                        Risk: ${
                          properties.risk || "Unknown"
                        }
                        <br/>
                        Probability: ${
                          properties.probability
                            ? (
                                properties.probability *
                                100
                              ).toFixed(1) + "%"
                            : "Unknown"
                        }
                      </div>
                    `);

                  }}
                />
              )}


              {/* ==================================================
                  HAZARD MARKERS / BUFFERS
              ================================================== */}

              {hazards.map((hazard) => {

                const visible =
                  hazard.type === "LANDSLIDE"
                    ? showLandslides
                    : showFloods;

                if (!visible) return null;

                return (
                  <Circle
                    key={hazard.id}
                    center={[
                      hazard.lat,
                      hazard.lng,
                    ]}
                    radius={
                      showBuffers
                        ? hazard.radius
                        : 0
                    }
                    pathOptions={{
                      color:
                        hazard.type === "LANDSLIDE"
                          ? "#dc2626"
                          : "#0891b2",

                      fillColor:
                        hazard.type === "LANDSLIDE"
                          ? "#ef4444"
                          : "#06b6d4",

                      fillOpacity: 0.12,

                      weight: 1.5,

                      dashArray: "5, 6",
                    }}
                    eventHandlers={{
                      click: () => focusHazard(hazard),
                    }}
                  >

                    <Popup>

                      <div className="min-w-[220px]">

                        <div className="font-bold text-[#123F66]">
                          {hazard.type === "LANDSLIDE"
                            ? "🌋 Landslide Hazard"
                            : "🌊 Flood Hazard"}
                        </div>

                        <div className="font-semibold mt-2">
                          {hazard.name}
                        </div>

                        <div className="text-sm mt-2">
                          <strong>Confidence:</strong>{" "}
                          {(hazard.probability * 100).toFixed(1)}%
                        </div>

                        <div className="text-sm">
                          <strong>Location:</strong>{" "}
                          {hazard.lat.toFixed(4)},
                          {" "}
                          {hazard.lng.toFixed(4)}
                        </div>

                        <div className="text-sm">
                          <strong>Country:</strong>{" "}
                          {hazard.country}
                        </div>

                        {hazard.affectedPixels && (
                          <div className="text-sm">
                            <strong>Affected Pixels:</strong>{" "}
                            {hazard.affectedPixels.toLocaleString()}
                          </div>
                        )}

                      </div>

                    </Popup>

                  </Circle>
                );
              })}

            </MapContainer>

          </div>

        </div>

      </section>


      {/* ======================================================
          SELECTED HAZARD
      ====================================================== */}

      {selectedHazard && (
        <section className="max-w-7xl mx-auto px-6 py-5">

          <div className="bg-white border border-gray-200 rounded-xl p-5">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-sm text-gray-500">
                  Selected Hazard
                </p>

                <h2 className="text-lg font-bold text-[#123F66] mt-1">
                  {selectedHazard.name}
                </h2>

              </div>

              <button
                onClick={() => setSelectedHazard(null)}
                className="text-gray-400 hover:text-gray-700"
              >
                ✕
              </button>

            </div>

          </div>

        </section>
      )}


      {/* ======================================================
          DATA SOURCES
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-8">

        <div className="bg-white border border-gray-200 rounded-xl p-6">

          <h2 className="text-lg font-bold text-[#123F66]">
            Satellite Intelligence
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-5">

            <div>

              <p className="font-semibold text-gray-800">
                Landslide Detection
              </p>

              <p className="text-sm text-gray-500 mt-1">
                Attention-ResUNet using multispectral and
                topographic information.
              </p>

            </div>

            <div>

              <p className="font-semibold text-gray-800">
                Flood Detection
              </p>

              <p className="text-sm text-gray-500 mt-1">
                Sentinel-2 MNDWI combined with Sentinel-1 SAR
                information.
              </p>

            </div>

            <div>

              <p className="font-semibold text-gray-800">
                Live Monitoring
              </p>

              <p className="text-sm text-gray-500 mt-1">
                Satellite monitoring service polls for new
                Copernicus data periodically.
              </p>

            </div>

          </div>

        </div>

      </section>

    </div>
  );
}