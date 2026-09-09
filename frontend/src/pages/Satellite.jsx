import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Circle,
  Popup,
  useMap,
} from "react-leaflet";

import { X } from "lucide-react";

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

export default function SatelliteMonitoring() {
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
          name: region.name || `Flood Zone #${region.region_id}`,
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

    setMapCenter([
      hazard.lat,
      hazard.lng,
    ]);

    setMapZoom(13);
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="bg-[#F8FAFC] min-h-screen text-[#243447]">

      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

      <section className="bg-white border-b border-[#D9E0E7]">

        <div className="max-w-7xl mx-auto px-6 py-8">

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">

            {/* Heading */}

            <div>

              <h1 className="text-3xl font-semibold text-[#243447]">
                Satellite Monitoring
              </h1>

              <p className="text-[#667085] mt-1">
                Satellite-based hazard detection and geospatial monitoring
              </p>

            </div>


            {/* Backend Status */}

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
                ? "Satellite System connected"
                : "Satellite System disconnected"}

            </div>

          </div>

        </div>

      </section>


      {/* ======================================================
          STATISTICS
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-6">

        <div className="grid grid-cols-1 md:grid-cols-4 border-t border-l border-[#D9E0E7]">

          <div className="bg-white border-r border-b border-[#D9E0E7] p-5">

            <p className="text-sm text-[#667085]">
              Landslide Zones
            </p>

            <p className="text-3xl font-semibold text-[#123F66] mt-2">
              {loading ? "..." : landslideCount}
            </p>

            <p className="text-xs text-[#667085] mt-1">
              Peak probability: {landslidePeak}%
            </p>

          </div>


          <div className="bg-white border-r border-b border-[#D9E0E7] p-5">

            <p className="text-sm text-[#667085]">
              Flood Zones
            </p>

            <p className="text-3xl font-semibold text-[#123F66] mt-2">
              {loading ? "..." : floodCount}
            </p>

            <p className="text-xs text-[#667085] mt-1">
              Maximum MNDWI: {floodPeak}
            </p>

          </div>


          <div className="bg-white border-r border-b border-[#D9E0E7] p-5">

            <p className="text-sm text-[#667085]">
              Landslide Model
            </p>

            <p className="text-lg font-semibold text-[#243447] mt-2">
              Attention-ResUNet
            </p>

            <p className="text-xs text-[#667085] mt-1">
              Multispectral + topography
            </p>

          </div>


          <div className="bg-white border-r border-b border-[#D9E0E7] p-5">

            <p className="text-sm text-[#667085]">
              Flood Detection
            </p>

            <p className="text-lg font-semibold text-[#243447] mt-2">
              MNDWI + SAR
            </p>

            <p className="text-xs text-[#667085] mt-1">
              Sentinel-1 / Sentinel-2
            </p>

          </div>

        </div>

      </section>


      {/* ======================================================
          MAP CONTROLS
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 pb-5">

        <div className="bg-white border border-[#D9E0E7] p-5">

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">

            {/* Base Map */}

            <div>

              <p className="text-sm font-semibold text-[#243447] mb-3">
                Base Map
              </p>

              <div className="flex flex-wrap gap-2">

                <button
                  onClick={() => setMapType("satellite")}
                  className={`px-4 py-2 text-sm border transition ${
                    mapType === "satellite"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-[#667085] border-[#D9E0E7] hover:border-[#123F66] hover:text-[#123F66]"
                  }`}
                >
                  Satellite
                </button>

                <button
                  onClick={() => setMapType("dark")}
                  className={`px-4 py-2 text-sm border transition ${
                    mapType === "dark"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-[#667085] border-[#D9E0E7] hover:border-[#123F66] hover:text-[#123F66]"
                  }`}
                >
                  Dark
                </button>

                <button
                  onClick={() => setMapType("osm")}
                  className={`px-4 py-2 text-sm border transition ${
                    mapType === "osm"
                      ? "bg-[#123F66] text-white border-[#123F66]"
                      : "bg-white text-[#667085] border-[#D9E0E7] hover:border-[#123F66] hover:text-[#123F66]"
                  }`}
                >
                  Standard
                </button>

              </div>

            </div>


            {/* Jump to Region */}

            <div>

              <p className="text-sm font-semibold text-[#243447] mb-3">
                Jump to Region
              </p>

              <div className="flex flex-wrap gap-2">

                <button
                  onClick={showLandslideRegion}
                  className="px-4 py-2 text-sm bg-[#EAF2F8] text-[#123F66] border border-[#D9E0E7] hover:bg-[#DCEAF5] transition"
                >
                  India Landslides
                </button>

                <button
                  onClick={showFloodRegion}
                  className="px-4 py-2 text-sm bg-[#EAF2F8] text-[#123F66] border border-[#D9E0E7] hover:bg-[#DCEAF5] transition"
                >
                  Nepal Floods
                </button>

                <button
                  onClick={showSouthAsia}
                  className="px-4 py-2 text-sm bg-white text-[#667085] border border-[#D9E0E7] hover:bg-[#EAF2F8] hover:text-[#123F66] transition"
                >
                  South Asia
                </button>

              </div>

            </div>

          </div>


          {/* Layer Toggles */}

          <div className="flex flex-wrap gap-6 mt-5 pt-4 border-t border-[#D9E0E7]">

            <label className="flex items-center gap-2 text-sm text-[#667085] cursor-pointer">

              <input
                type="checkbox"
                checked={showLandslides}
                onChange={(e) =>
                  setShowLandslides(e.target.checked)
                }
                className="accent-[#123F66]"
              />

              <span className="w-2.5 h-2.5 rounded-full bg-[#123F66]" />

              Landslide Zones

            </label>


            <label className="flex items-center gap-2 text-sm text-[#667085] cursor-pointer">

              <input
                type="checkbox"
                checked={showFloods}
                onChange={(e) =>
                  setShowFloods(e.target.checked)
                }
                className="accent-[#123F66]"
              />

              <span className="w-2.5 h-2.5 rounded-full bg-[#4D7FA3]" />

              Flood Zones

            </label>


            <label className="flex items-center gap-2 text-sm text-[#667085] cursor-pointer">

              <input
                type="checkbox"
                checked={showBuffers}
                onChange={(e) =>
                  setShowBuffers(e.target.checked)
                }
                className="accent-[#123F66]"
              />

              <span className="w-2.5 h-2.5 rounded-full bg-[#7EA6C2]" />

              Danger Buffers

            </label>

          </div>

        </div>

      </section>


      {/* ======================================================
          MAP
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6">

        <div className="border border-[#D9E0E7] overflow-hidden">

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


              {/* LANDSLIDE GEOJSON */}

              {showLandslides && landslideGeoJSON && (

                <GeoJSON
                  key={`landslide-${landslideGeoJSON.features?.length}`}
                  data={landslideGeoJSON}

                  style={{
                    color: "#123F66",
                    weight: 2,
                    fillColor: "#123F66",
                    fillOpacity: 0.35,
                  }}

                  onEachFeature={(feature, layer) => {

                    const properties =
                      feature.properties || {};

                    layer.bindPopup(`

                      <div style="min-width:200px">

                        <strong>
                          Landslide Zone
                        </strong>

                        <br/>

                        Region:
                        ${
                          properties.region_id ??
                          "Unknown"
                        }

                        <br/>

                        Probability:
                        ${
                          properties.max_probability
                            ? (
                                properties.max_probability *
                                100
                              ).toFixed(2) + "%"
                            : "Unknown"
                        }

                        <br/>

                        Affected Pixels:
                        ${
                          properties.affected_pixels ??
                          "Unknown"
                        }

                      </div>

                    `);

                  }}

                />

              )}


              {/* FLOOD GEOJSON */}

              {showFloods && floodGeoJSON && (

                <GeoJSON
                  key={`flood-${floodGeoJSON.features?.length}`}
                  data={floodGeoJSON}

                  style={{
                    color: "#4D7FA3",
                    weight: 2,
                    fillColor: "#4D7FA3",
                    fillOpacity: 0.35,
                  }}

                  onEachFeature={(feature, layer) => {

                    const properties =
                      feature.properties || {};

                    layer.bindPopup(`

                      <div style="min-width:220px">

                        <strong>
                          Flood Zone
                        </strong>

                        <br/>

                        ${
                          properties.name ||
                          "Flood affected region"
                        }

                        <br/>

                        Risk:
                        ${
                          properties.risk ||
                          "Unknown"
                        }

                        <br/>

                        Probability:
                        ${
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


              {/* HAZARD MARKERS */}

              {hazards.map((hazard) => {

                const visible =
                  hazard.type === "LANDSLIDE"
                    ? showLandslides
                    : showFloods;

                if (!visible) {
                  return null;
                }

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
                          ? "#123F66"
                          : "#4D7FA3",

                      fillColor:
                        hazard.type === "LANDSLIDE"
                          ? "#123F66"
                          : "#4D7FA3",

                      fillOpacity: 0.12,

                      weight: 1.5,

                      dashArray: "5, 6",

                    }}

                    eventHandlers={{
                      click: () =>
                        focusHazard(hazard),
                    }}
                  >

                    <Popup>

                      <div className="min-w-[220px]">

                        <div className="font-semibold text-[#123F66]">

                          {hazard.type === "LANDSLIDE"
                            ? "Landslide Hazard"
                            : "Flood Hazard"}

                        </div>

                        <div className="font-semibold mt-2">
                          {hazard.name}
                        </div>

                        <div className="text-sm mt-2">

                          <strong>
                            Confidence:
                          </strong>{" "}

                          {(
                            hazard.probability * 100
                          ).toFixed(1)}
                          %

                        </div>

                        <div className="text-sm">

                          <strong>
                            Location:
                          </strong>{" "}

                          {hazard.lat.toFixed(4)},
                          {" "}
                          {hazard.lng.toFixed(4)}

                        </div>

                        <div className="text-sm">

                          <strong>
                            Country:
                          </strong>{" "}

                          {hazard.country}

                        </div>

                        {hazard.affectedPixels && (

                          <div className="text-sm">

                            <strong>
                              Affected Pixels:
                            </strong>{" "}

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

          <div className="bg-white border border-[#D9E0E7] p-5">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-sm text-[#667085]">
                  Selected Hazard
                </p>

                <h2 className="text-lg font-semibold text-[#243447] mt-1">
                  {selectedHazard.name}
                </h2>

              </div>

              <button
                onClick={() =>
                  setSelectedHazard(null)
                }
                className="text-[#667085] hover:text-[#123F66] transition"
                aria-label="Close selected hazard"
              >
                <X size={20} />
              </button>

            </div>

          </div>

        </section>

      )}


      {/* ======================================================
          DATA SOURCES
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-8">

        <div className="bg-white border border-[#D9E0E7] p-6">

          <h2 className="text-lg font-semibold text-[#243447]">
            Satellite Intelligence
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-6">

            <div>

              <p className="font-semibold text-[#243447]">
                Landslide Detection
              </p>

              <p className="text-sm text-[#667085] mt-1 leading-6">
                Attention-ResUNet using multispectral and
                topographic information.
              </p>

            </div>


            <div>

              <p className="font-semibold text-[#243447]">
                Flood Detection
              </p>

              <p className="text-sm text-[#667085] mt-1 leading-6">
                Sentinel-2 MNDWI combined with Sentinel-1 SAR
                information.
              </p>

            </div>


            <div>

              <p className="font-semibold text-[#243447]">
                Live Monitoring
              </p>

              <p className="text-sm text-[#667085] mt-1 leading-6">
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