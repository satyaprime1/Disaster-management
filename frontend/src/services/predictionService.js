// ============================================================
// API CONFIGURATION
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const OPEN_METEO_GEOCODING_URL =
  "https://geocoding-api.open-meteo.com/v1/search";


// ============================================================
// GET LOCATION FROM OPEN-METEO
// ============================================================
// Used ONLY if the backend does not return coordinates.
// This does NOT generate prediction/weather data.
// ============================================================

const getLocationFromOpenMeteo = async (city) => {

  const url =
    `${OPEN_METEO_GEOCODING_URL}` +
    `?name=${encodeURIComponent(city)}` +
    `&count=1` +
    `&language=en` +
    `&format=json`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      "Location lookup failed."
    );
  }

  const data = await response.json();

  if (
    !data.results ||
    data.results.length === 0
  ) {
    throw new Error(
      `Location "${city}" was not found.`
    );
  }

  const location = data.results[0];

  return {
    city: location.name,
    country: location.country || "India",
    latitude: Number(
      Number(location.latitude).toFixed(5)
    ),
    longitude: Number(
      Number(location.longitude).toFixed(5)
    ),
  };
};


// ============================================================
// NORMALIZE BACKEND RESPONSE
// ============================================================

const normalizePredictionResponse = (result) => {

  if (!result) {
    throw new Error(
      "Backend returned an empty response."
    );
  }


  // ==========================================================
  // LANDSLIDE
  // ==========================================================

  if (result.landslide) {

    const landslide = result.landslide;

    const rawRiskScore =
      landslide.risk_score ??
      landslide.riskScore ??
      landslide.probability ??
      landslide.prediction ??
      0;

    const riskScore =
      Number(rawRiskScore);

    const riskLevel =
      landslide.risk_level ??
      landslide.riskLevel ??
      landslide.risk ??
      "UNKNOWN";

    result.landslide = {

      ...landslide,

      risk_score:
        Number.isFinite(riskScore)
          ? riskScore
          : 0,

      risk_level:
        String(riskLevel).toUpperCase(),

      risk:
        String(riskLevel).toUpperCase(),

    };

  }


  // ==========================================================
  // FLOOD
  // ==========================================================

  if (result.flood) {

    const flood = result.flood;

    const rawFloodScore =
      flood.probability ??
      flood.risk_score ??
      flood.riskScore ??
      flood.prediction;

    const floodScore =
      Number(rawFloodScore);

    const floodRisk =
      flood.risk_level ??
      flood.riskLevel ??
      flood.risk ??
      "UNKNOWN";

    result.flood = {

      ...flood,

      probability:
        Number.isFinite(floodScore)
          ? floodScore
          : 0,

      risk_score:
        Number.isFinite(floodScore)
          ? floodScore
          : 0,

      risk_level:
        String(floodRisk).toUpperCase(),

      risk:
        String(floodRisk).toUpperCase(),

    };

  }


  // ==========================================================
  // ENVIRONMENT
  // ==========================================================
  // IMPORTANT:
  //
  // We DO NOT create temperature,
  // humidity, rainfall, etc.
  //
  // Whatever appears here must come
  // from the backend.
  // ==========================================================

  if (result.environment) {

    console.log(
      "BACKEND ENVIRONMENT DATA:",
      result.environment
    );

  }


  // ==========================================================
  // DEBUG
  // ==========================================================

  console.log(
    "FINAL BACKEND RESULT:",
    result
  );

  console.log(
    "FINAL LANDSLIDE DATA:",
    result.landslide
  );

  console.log(
    "FINAL FLOOD DATA:",
    result.flood
  );

  console.log(
    "FINAL ENVIRONMENT DATA:",
    result.environment
  );


  return result;
};


// ============================================================
// MAIN PREDICTION FUNCTION
// ============================================================

export async function predictCity(city) {

  // ----------------------------------------------------------
  // VALIDATE CITY
  // ----------------------------------------------------------

  if (
    !city ||
    typeof city !== "string" ||
    !city.trim()
  ) {

    throw new Error(
      "Please enter a valid city."
    );

  }

  const cityName =
    city.trim();


  // ----------------------------------------------------------
  // SEND REQUEST TO BACKEND
  // ----------------------------------------------------------

  console.log(
    "========================================"
  );

  console.log(
    "SENDING PREDICTION REQUEST"
  );

  console.log(
    "City:",
    cityName
  );

  console.log(
    "Backend:",
    API_BASE_URL
  );

  console.log(
    "========================================"
  );


  let response;

  try {

    response = await fetch(
      `${API_BASE_URL}/predict`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          city: cityName,
        }),

        cache: "no-store",
      }
    );

  } catch (err) {

    // ========================================================
    // BACKEND COMPLETELY UNREACHABLE
    // ========================================================

    console.error(
      "BACKEND CONNECTION FAILED:",
      err
    );

    throw new Error(
      "Backend is unavailable. Please start the backend server and try again."
    );

  }


  // ==========================================================
  // BACKEND RETURNED ERROR
  // ==========================================================

  if (!response.ok) {

    let errorMessage =
      `Prediction failed (${response.status})`;

    try {

      const errorData =
        await response.json();

      errorMessage =
        errorData.error ||
        errorData.detail ||
        errorData.message ||
        errorMessage;

    } catch {

      // Backend did not return JSON.
      // Keep default error message.

    }


    console.error(
      "BACKEND PREDICTION ERROR:",
      errorMessage
    );


    throw new Error(
      errorMessage
    );

  }


  // ==========================================================
  // READ BACKEND JSON
  // ==========================================================

  let result;

  try {

    result =
      await response.json();

  } catch (err) {

    console.error(
      "Invalid JSON returned by backend:",
      err
    );

    throw new Error(
      "Backend returned an invalid response."
    );

  }


  // ==========================================================
  // DEBUG RAW RESPONSE
  // ==========================================================

  console.log(
    "========================================"
  );

  console.log(
    "RAW BACKEND RESPONSE:"
  );

  console.log(
    result
  );

  console.log(
    "========================================"
  );


  // ==========================================================
  // NORMALIZE RESPONSE
  // ==========================================================

  const normalizedResult =
    normalizePredictionResponse(
      result
    );


  // ==========================================================
  // LOCATION
  // ==========================================================
  // Prefer backend location.
  //
  // If backend did not provide location,
  // Open-Meteo is used ONLY for coordinates.
  //
  // It does NOT generate prediction data.
  // ==========================================================

  if (
    normalizedResult.location &&
    normalizedResult.location.latitude != null &&
    normalizedResult.location.longitude != null
  ) {

    return normalizedResult;

  }


  // ==========================================================
  // BACKEND DID NOT PROVIDE LOCATION
  // ==========================================================

  console.warn(
    "Backend did not provide location."
  );

  let location;

  try {

    location =
      await getLocationFromOpenMeteo(
        cityName
      );

  } catch (err) {

    console.error(
      "Location lookup failed:",
      err
    );

    throw new Error(
      `Backend returned no location for "${cityName}".`
    );

  }


  // ==========================================================
  // RETURN BACKEND RESULT + LOCATION
  // ==========================================================

  return {

    ...normalizedResult,

    location: {

      ...(normalizedResult.location || {}),

      ...location,

    },

  };

}