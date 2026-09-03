import { Link } from "react-router-dom";
import {
  Brain,
  Satellite,
  Route,
  ArrowRight,
  ShieldAlert,
  Map,
  Activity,
} from "lucide-react";

export default function Dashboard() {
  return (
    <div className="bg-[#F5F7FA]">

      {/* ================= HERO SECTION ================= */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="max-w-3xl">

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 text-[#123F66] text-sm font-medium mb-5">
              <ShieldAlert size={16} />
              Disaster Management System
            </div>

            <h1 className="text-4xl md:text-5xl font-bold text-[#123F66] leading-tight">
              VEYRiX
            </h1>

            <p className="text-xl text-gray-600 mt-3">
              Multi-Hazard Prediction & Monitoring System
            </p>

            <p className="text-gray-500 mt-5 max-w-2xl leading-relaxed">
              VEYRiX is an integrated disaster-management platform designed
              to support hazard prediction, satellite-based monitoring,
              safe routing, and intelligent disaster response.
            </p>

          </div>
        </div>
      </section>


      {/* ================= SERVICES ================= */}
      <section className="max-w-7xl mx-auto px-6 py-12">

        <div className="mb-8">
          <h2 className="text-2xl font-bold text-[#123F66]">
            VEYRiX Services
          </h2>

          <p className="text-gray-500 mt-2">
            Choose a module to explore the disaster-management capabilities.
          </p>
        </div>


        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">


          {/* ================= ML PREDICTION ================= */}
          <Link
            to="/ml"
            className="group bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-200 transition"
          >

            <div className="w-12 h-12 rounded-lg bg-blue-50 text-[#123F66] flex items-center justify-center mb-5">
              <Brain size={25} />
            </div>

            <h3 className="text-xl font-bold text-[#123F66]">
              ML Prediction
            </h3>

            <p className="text-gray-500 mt-3 leading-relaxed">
              Predict disaster risks such as floods and landslides using
              machine-learning models.
            </p>

            <div className="flex items-center gap-2 text-[#123F66] font-medium mt-6">
              Open Module

              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition"
              />
            </div>

          </Link>


          {/* ================= SATELLITE MONITORING ================= */}
          <Link
            to="/satellite"
            className="group bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-200 transition"
          >

            <div className="w-12 h-12 rounded-lg bg-blue-50 text-[#123F66] flex items-center justify-center mb-5">
              <Satellite size={25} />
            </div>

            <h3 className="text-xl font-bold text-[#123F66]">
              Satellite Monitoring
            </h3>

            <p className="text-gray-500 mt-3 leading-relaxed">
              Monitor disaster-affected regions using satellite imagery
              and geospatial information.
            </p>

            <div className="flex items-center gap-2 text-[#123F66] font-medium mt-6">
              Open Module

              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition"
              />
            </div>

          </Link>


          {/* ================= SAFE ROUTING ================= */}
          <Link
            to="/safe-routing"
            className="group bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-200 transition"
          >

            <div className="w-12 h-12 rounded-lg bg-blue-50 text-[#123F66] flex items-center justify-center mb-5">
              <Route size={25} />
            </div>

            <h3 className="text-xl font-bold text-[#123F66]">
              Safe Routing
            </h3>

            <p className="text-gray-500 mt-3 leading-relaxed">
              Find safer routes by considering disaster-affected areas
              and potential hazards.
            </p>

            <div className="flex items-center gap-2 text-[#123F66] font-medium mt-6">
              Open Module

              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition"
              />
            </div>

          </Link>


          {/* ================= RAG COPILOT ================= */}
          <Link
            to="/copilot"
            className="group bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-200 transition"
          >

            <div className="w-12 h-12 rounded-lg bg-blue-50 text-[#123F66] flex items-center justify-center mb-5">
              <Brain size={25} />
            </div>

            <h3 className="text-xl font-bold text-[#123F66]">
              VEYRiX RAG Copilot
            </h3>

            <p className="text-gray-500 mt-3 leading-relaxed">
              Ask questions about disasters, safety procedures, emergency
              response, and VEYRiX using an intelligent AI assistant.
            </p>

            <div className="flex items-center gap-2 text-[#123F66] font-medium mt-6">
              Open Copilot

              <ArrowRight
                size={18}
                className="group-hover:translate-x-1 transition"
              />
            </div>

          </Link>

        </div>

      </section>


      {/* ================= ABOUT VEYRIX ================= */}
      <section className="max-w-7xl mx-auto px-6 pb-14">

        <div className="bg-white border border-gray-200 rounded-xl p-8">

          <div className="flex items-center gap-3 mb-4">

            <Activity
              className="text-[#123F66]"
              size={24}
            />

            <h2 className="text-2xl font-bold text-[#123F66]">
              About VEYRiX
            </h2>

          </div>


          <p className="text-gray-600 leading-relaxed max-w-4xl">
            VEYRiX combines machine learning, satellite monitoring,
            geospatial analysis, safe routing, and AI technologies into
            a unified platform for disaster management. The system aims
            to provide useful information for understanding hazards,
            monitoring affected regions, supporting emergency response,
            and making safer decisions during disaster situations.
          </p>


          {/* ================= FEATURE BOXES ================= */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-8">


            {/* Intelligent Prediction */}
            <div className="border border-gray-200 rounded-lg p-5">

              <Brain
                className="text-[#123F66] mb-3"
                size={22}
              />

              <h3 className="font-semibold text-gray-800">
                Intelligent Prediction
              </h3>

              <p className="text-sm text-gray-500 mt-2">
                Machine-learning based hazard prediction for
                disaster risk assessment.
              </p>

            </div>


            {/* Geospatial Monitoring */}
            <div className="border border-gray-200 rounded-lg p-5">

              <Map
                className="text-[#123F66] mb-3"
                size={22}
              />

              <h3 className="font-semibold text-gray-800">
                Geospatial Monitoring
              </h3>

              <p className="text-sm text-gray-500 mt-2">
                Satellite and geographic information for monitoring
                disaster-affected regions.
              </p>

            </div>


            {/* Safer Navigation */}
            <div className="border border-gray-200 rounded-lg p-5">

              <Route
                className="text-[#123F66] mb-3"
                size={22}
              />

              <h3 className="font-semibold text-gray-800">
                Safer Navigation
              </h3>

              <p className="text-sm text-gray-500 mt-2">
                Routing support for navigating around hazardous
                and affected regions.
              </p>

            </div>

          </div>

        </div>

      </section>

    </div>
  );
}