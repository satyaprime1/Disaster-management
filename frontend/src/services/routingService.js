const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function checkRoutingBackend() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);

    return response.ok;
  } catch (error) {
    return false;
  }
}

export async function calculateSafeRoute(data) {
  const response = await fetch(
    `${API_BASE_URL}/api/route`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error("Safe routing request failed");
  }

  return response.json();
}