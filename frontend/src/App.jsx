import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import MLPrediction from "./pages/MLPrediction";
import Satellite from "./pages/Satellite";
import SafeRouting from "./pages/SafeRouting";


// ============================================================
// RAG COPILOT PAGE
// ============================================================

function Copilot() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold text-[#123F66]">
        VEYRiX RAG Copilot
      </h1>

      <p className="mt-3 text-gray-600">
        Intelligent disaster-management assistant.
      </p>
    </div>
  );
}


// ============================================================
// APP
// ============================================================

export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* ====================================================
            COMMON LAYOUT
        ==================================================== */}

        <Route element={<Layout />}>

          {/* Dashboard */}
          <Route
            path="/"
            element={<Dashboard />}
          />


          {/* ML Prediction */}
          <Route
            path="/ml"
            element={<MLPrediction />}
          />


          {/* Satellite Monitoring */}
          <Route
            path="/satellite"
            element={<Satellite />}
          />


          {/* Safe Routing */}
          <Route
            path="/safe-routing"
            element={<SafeRouting />}
          />


          {/* RAG Copilot */}
          <Route
            path="/copilot"
            element={<Copilot />}
          />

        </Route>

      </Routes>
    </BrowserRouter>
  );
}