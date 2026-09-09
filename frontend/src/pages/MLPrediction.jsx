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
      console.error(
        "Prediction error:",
        err
      );

      setError(
        err.message ||
          "The prediction service could not analyse this region. Please try again."
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
    longitude: 77.209,
  };

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#243447]">

      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

      <section className="bg-white border-b border-[#D9E0E7]">
        <div className="max-w-7xl mx-auto px-6 py-8">

          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5">

            {/* HEADER CONTENT */}

            <div>
              <p className="text-sm font-medium text-[#123F66]">
                VEYRiX Prediction
              </p>

              <h1 className="text-3xl md:text-4xl font-semibold text-[#243447] mt-2">
                ML Hazard Prediction
              </h1>

              <p className="text-[#667085] mt-2 max-w-2xl">
                Flood and landslide risk analysis using machine learning.
              </p>
            </div>

            {/* ==================================================
                BACKEND STATUS
            ================================================== */}

            <div
              className={`
                flex
                items-center
                gap-2
                px-4
                py-2
                border
                text-sm
                font-medium
                ${
                  backendConnected
                    ? "bg-[#E8F5E9] text-[#2E7D32] border-[#A5D6A7]"
                    : "bg-[#FDECEC] text-[#C62828] border-[#EF9A9A]"
                }
              `}
            >

              <span
                className={`
                  w-2.5
                  h-2.5
                  rounded-full
                  ${
                    backendConnected
                      ? "bg-[#2E7D32]"
                      : "bg-[#C62828]"
                  }
                `}
              />

              {backendConnected
                ? "Prediction system connected"
                : "Prediction system disconnected"}

            </div>

          </div>

        </div>
      </section>

      {/* ======================================================
          MAP / LOCATION SELECTION
      ====================================================== */}

      <section className="max-w-7xl mx-auto px-6 py-6">

        <div className="border border-[#D9E0E7] bg-white overflow-hidden">

          <div className="h-[500px]">

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

        </div>

      </section>

      {/* ======================================================
          LOADING
      ====================================================== */}

      {loading && (
        <section className="max-w-7xl mx-auto px-6 pb-6">

          <div className="border border-[#D9E0E7] bg-white p-5">

            <LoadingScreen />

          </div>

        </section>
      )}

      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (
        <section className="max-w-7xl mx-auto px-6 pb-6">

          <div className="border border-[#D9E0E7] bg-[#EAF2F8] p-5">

            <ErrorMessage
              message={error}
              onRetry={() =>
                handleAnalyze(
                  defaultLocation.city
                )
              }
            />

          </div>

        </section>
      )}

      {/* ======================================================
          RESULTS
      ====================================================== */}

      {!loading && result && (
        <section className="max-w-7xl mx-auto px-6 pb-8">

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

            {/* ==================================================
                MAIN RESULTS
            ================================================== */}

            <div className="lg:col-span-2 space-y-6">

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

            {/* ==================================================
                SIDE INFORMATION
            ================================================== */}

            <div className="space-y-6">

              <WeatherPanel
                data={result.environment}
              />

              <ModelDetails />

            </div>

          </div>

        </section>
      )}

      {/* ======================================================
          EMPTY STATE
      ====================================================== */}

      {!loading &&
        !result &&
        !error && (
          <section className="max-w-7xl mx-auto px-6 pb-10">

            <div className="border-t border-b border-[#D9E0E7] bg-white py-10">

              <div className="max-w-xl">

                <p className="text-sm font-medium text-[#123F66]">
                  Begin Analysis
                </p>

                <h3 className="text-2xl font-semibold text-[#243447] mt-2">
                  Select a region to assess its risk
                </h3>

                <p className="text-sm text-[#667085] mt-3 leading-6">
                  Use the search bar on the map to select
                  a city or region and evaluate its flood
                  and landslide risk.
                </p>

              </div>

            </div>

          </section>
        )}

    </main>
  );
}

export default MLPrediction;