import React, { useEffect, useState } from "react";
import { predictCity } from "../services/predictionService";

import CitySearch from "../components/CitySearch";
import OverallRisk from "../components/OverallRisk";
import HazardCards from "../components/HazardCards";
import LandslideCard from "../components/LandslideCard";
import FloodCard from "../components/FloodCard";
import SatelliteCard from "../components/SatelliteCard";
import RiskMap from "../components/RiskMap";
import WeatherPanel from "../components/WeatherPanel";
import AlertPanel from "../components/AlertPanel";
import LoadingScreen from "../components/LoadingScreen";
import ErrorMessage from "../components/ErrorMessage";
import ModelDetails from "../components/ModelDetails";

// ============================================================
// BACKEND API URL
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

// ============================================================
// ML PREDICTION PAGE
// ============================================================

function MLPrediction() {

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [backendConnected, setBackendConnected] = useState(false);

  // ==========================================================
  // BACKEND CONNECTION CHECK
  // ==========================================================

  useEffect(() => {

    let mounted = true;

    const checkBackend = async () => {

      try {

        const response = await fetch(
          `${API_BASE_URL}/health`,
          {
            method: "GET",
            cache: "no-store",
          }
        );

        if (mounted) {
          setBackendConnected(response.ok);
        }

      } catch (err) {

        if (mounted) {
          setBackendConnected(false);
        }

      }

    };

    checkBackend();

    const interval = setInterval(
      checkBackend,
      5000
    );

    return () => {

      mounted = false;
      clearInterval(interval);

    };

  }, []);

  // ==========================================================
  // CITY ANALYSIS
  // ==========================================================

  const handleAnalyze = async (city) => {

    setLoading(true);
    setError("");

    try {

      const data = await predictCity(city);

      setResult(data);

    } catch (err) {

      console.error("Prediction error:", err);

      setError(
        err.message ||
        "The predictive telemetry pipeline failed. Please try again."
      );

      setResult(null);

    } finally {

      setLoading(false);

    }

  };

  // ==========================================================
  // DEFAULT LOCATION
  // ==========================================================

  const defaultLocation = {
    city: "New Delhi",
    country: "India",
    latitude: 28.6139,
    longitude: 77.2090,
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <div className="max-w-7xl w-full mx-auto px-4 py-6 space-y-6">

      {/* PAGE TITLE */}

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">

        <div>

          <h1 className="text-2xl font-bold text-[#123B63]">
            ML Hazard Prediction
          </h1>

          <p className="text-sm text-[#667085] mt-1">
            Flood and landslide risk analysis using machine learning.
          </p>

        </div>

        <div
          className={`px-3 py-2 rounded-full text-xs font-medium ${
            backendConnected
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {backendConnected
            ? "● Prediction System Online"
            : "● Backend Disconnected"}
        </div>

      </div>


      {/* ======================================================
          MAP
      ====================================================== */}

      <div
        className="
          relative
          border
          border-[#D9E0E7]
          bg-white
          rounded-lg
          overflow-hidden
          shadow-sm
          h-[500px]
          flex
          flex-col
        "
      >

        <RiskMap
          location={
            result
              ? result.location
              : defaultLocation
          }

          searchComponent={

            <CitySearch
              onAnalyze={handleAnalyze}
              loading={loading}
            />

          }

        />

      </div>


      {/* ======================================================
          LOADING
      ====================================================== */}

      {loading && (
        <LoadingScreen />
      )}


      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (

        <div className="max-w-lg mx-auto">

          <ErrorMessage
            message={error}
            onRetry={() =>
              handleAnalyze(
                defaultLocation.city
              )
            }
          />

        </div>

      )}


      {/* ======================================================
          RESULTS
      ====================================================== */}

      {!loading && result && (

        <div
          className="
            grid
            grid-cols-1
            lg:grid-cols-3
            gap-6
            items-start
          "
        >

          {/* LEFT + MIDDLE */}

          <div
            className="
              lg:col-span-2
              space-y-6
            "
          >

            <OverallRisk
              data={result.overall}
              location={result.location}
            />


            <HazardCards>

              <LandslideCard
                data={result.landslide}
              />

              <FloodCard
                data={result.flood}
              />

              <SatelliteCard
                data={result.satellite}
              />

            </HazardCards>


            <AlertPanel
              result={result}
            />

          </div>


          {/* RIGHT */}

          <div className="space-y-6">

            <WeatherPanel
              data={result.environment}
            />

            <ModelDetails />

          </div>

        </div>

      )}


      {/* ======================================================
          EMPTY STATE
      ====================================================== */}

      {!loading && !result && !error && (

        <div
          className="
            text-center
            py-10
            bg-white
            border
            border-[#D9E0E7]
            rounded-lg
            max-w-lg
            mx-auto
            shadow-sm
            p-8
          "
        >

          <h3
            className="
              text-sm
              font-bold
              text-[#123B63]
              uppercase
              tracking-wider
            "
          >
            No Region Selected
          </h3>


          <p
            className="
              text-xs
              text-[#667085]
              mt-2
              leading-relaxed
              max-w-sm
              mx-auto
            "
          >
            Use the search bar on the map to select a region
            and evaluate its flood and landslide risk.
          </p>

        </div>

      )}

    </div>

  );

}

export default MLPrediction;