import { Link } from "react-router-dom";
import {
  Brain,
  Satellite,
  Route,
  ArrowRight,
  ShieldAlert,
  Map,
} from "lucide-react";

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#243447]">

      {/* ================= HERO ================= */}
      <section className="bg-white border-b border-[#D9E0E7]">
        <div className="max-w-7xl mx-auto px-6 py-16 md:py-20">

          <div className="max-w-4xl">

            <p className="text-sm font-medium text-[#123F66] mb-5">
              VEYRiX — Multi-Hazard Prediction & Monitoring System
            </p>

            <h1 className="text-4xl md:text-6xl font-semibold tracking-tight text-[#243447]">
              Technology for
              <br />
              disaster preparedness.
            </h1>

            <p className="text-lg text-[#667085] leading-7 max-w-2xl mt-6">
              VEYRiX brings together machine learning, satellite imagery,
              geospatial analysis and route planning to support disaster
              monitoring and informed decision-making.
            </p>

            <div className="flex flex-wrap gap-3 mt-8">

              <Link
                to="/ml"
                className="inline-flex items-center gap-2 bg-[#123F66] text-white px-5 py-3 text-sm font-medium hover:bg-[#0D304D] transition"
              >
                Explore the system
                <ArrowRight size={17} />
              </Link>

              <Link
                to="/satellite"
                className="inline-flex items-center gap-2 border border-[#D9E0E7] text-[#123F66] px-5 py-3 text-sm font-medium hover:bg-[#EAF2F8] transition"
              >
                View satellite monitoring
              </Link>

            </div>

          </div>

        </div>
      </section>


      {/* ================= INTRO ================= */}
      <section className="bg-[#EAF2F8] border-b border-[#D9E0E7]">

        <div className="max-w-7xl mx-auto px-6 py-10">

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

            <div>
              <p className="text-sm text-[#123F66] font-medium">
                Prediction
              </p>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Analyse environmental and geographical factors to identify
                potential disaster risks.
              </p>
            </div>

            <div>
              <p className="text-sm text-[#123F66] font-medium">
                Monitoring
              </p>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Use satellite and geospatial information to understand
                affected areas.
              </p>
            </div>

            <div>
              <p className="text-sm text-[#123F66] font-medium">
                Response
              </p>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Support safer navigation and access to relevant disaster
                response information.
              </p>
            </div>

          </div>

        </div>

      </section>


      {/* ================= SERVICES ================= */}
      <section className="max-w-7xl mx-auto px-6 py-16">

        <div className="max-w-2xl mb-10">

          <p className="text-sm font-medium text-[#123F66]">
            Platform
          </p>

          <h2 className="text-3xl font-semibold text-[#243447] mt-2">
            VEYRiX capabilities
          </h2>

          <p className="text-[#667085] mt-3 leading-6">
            Explore the tools available for prediction, monitoring,
            navigation and disaster-related information.
          </p>

        </div>


        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-0 border-t border-[#D9E0E7]">

          {/* ML */}
          <Link
            to="/ml"
            className="group py-8 border-b border-[#D9E0E7] flex gap-5"
          >

            <div className="text-[#123F66] pt-1">
              <Brain size={23} strokeWidth={1.7} />
            </div>

            <div className="flex-1">

              <div className="flex items-start justify-between gap-4">

                <h3 className="text-lg font-semibold text-[#243447]">
                  Machine Learning Prediction
                </h3>

                <ArrowRight
                  size={18}
                  className="text-[#667085] group-hover:translate-x-1 group-hover:text-[#123F66] transition"
                />

              </div>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Predict potential flood and landslide risks using
                machine-learning based analysis.
              </p>

            </div>

          </Link>


          {/* Satellite */}
          <Link
            to="/satellite"
            className="group py-8 border-b border-[#D9E0E7] flex gap-5"
          >

            <div className="text-[#123F66] pt-1">
              <Satellite size={23} strokeWidth={1.7} />
            </div>

            <div className="flex-1">

              <div className="flex items-start justify-between gap-4">

                <h3 className="text-lg font-semibold text-[#243447]">
                  Satellite Monitoring
                </h3>

                <ArrowRight
                  size={18}
                  className="text-[#667085] group-hover:translate-x-1 group-hover:text-[#123F66] transition"
                />

              </div>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Analyse satellite imagery and geographic information
                for disaster-affected regions.
              </p>

            </div>

          </Link>


          {/* Safe Routing */}
          <Link
            to="/safe-routing"
            className="group py-8 border-b border-[#D9E0E7] flex gap-5"
          >

            <div className="text-[#123F66] pt-1">
              <Route size={23} strokeWidth={1.7} />
            </div>

            <div className="flex-1">

              <div className="flex items-start justify-between gap-4">

                <h3 className="text-lg font-semibold text-[#243447]">
                  Safe Route Planning
                </h3>

                <ArrowRight
                  size={18}
                  className="text-[#667085] group-hover:translate-x-1 group-hover:text-[#123F66] transition"
                />

              </div>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Find routes while considering hazardous and
                disaster-affected areas.
              </p>

            </div>

          </Link>


          {/* Copilot */}
          <Link
            to="/copilot"
            className="group py-8 border-b border-[#D9E0E7] flex gap-5"
          >

            <div className="text-[#123F66] pt-1">
              <ShieldAlert size={23} strokeWidth={1.7} />
            </div>

            <div className="flex-1">

              <div className="flex items-start justify-between gap-4">

                <h3 className="text-lg font-semibold text-[#243447]">
                  VEYRiX RAG Copilot
                </h3>

                <ArrowRight
                  size={18}
                  className="text-[#667085] group-hover:translate-x-1 group-hover:text-[#123F66] transition"
                />

              </div>

              <p className="text-sm text-[#667085] mt-2 leading-6">
                Access information about disasters, safety procedures,
                emergency response and the VEYRiX platform.
              </p>

            </div>

          </Link>

        </div>

      </section>


      {/* ================= ABOUT ================= */}
      <section className="bg-[#EAF2F8] border-t border-[#D9E0E7]">

        <div className="max-w-7xl mx-auto px-6 py-16">

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">

            {/* LEFT */}
            <div>

              <p className="text-sm font-medium text-[#123F66]">
                About VEYRiX
              </p>

              <h2 className="text-3xl md:text-4xl font-semibold text-[#243447] mt-3 leading-tight">
                One platform.
                <br />
                Multiple perspectives.
              </h2>

            </div>


            {/* RIGHT */}
            <div className="lg:col-span-3">

              <p className="text-[#40566D] leading-7 max-w-3xl">
                VEYRiX combines machine learning, satellite monitoring,
                geospatial analysis, safe routing and artificial intelligence
                into a unified disaster-management platform.
              </p>

              <p className="text-[#667085] leading-7 max-w-3xl mt-4">
                The system is intended to help users understand potential
                hazards, monitor affected regions, analyse geographical
                conditions and make better-informed decisions during
                emergency situations.
              </p>


              {/* FEATURE BOXES */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-10 pt-8 border-t border-[#D9E0E7]">

                {/* Intelligent Prediction */}
                <div>

                  <Brain
                    size={20}
                    className="text-[#123F66] mb-4"
                    strokeWidth={1.7}
                  />

                  <h3 className="font-semibold text-[#243447]">
                    Intelligent Prediction
                  </h3>

                  <p className="text-sm text-[#667085] mt-2 leading-6">
                    Data-driven assessment of potential hazards.
                  </p>

                </div>


                {/* Geospatial Analysis */}
                <div>

                  <Map
                    size={20}
                    className="text-[#123F66] mb-4"
                    strokeWidth={1.7}
                  />

                  <h3 className="font-semibold text-[#243447]">
                    Geospatial Analysis
                  </h3>

                  <p className="text-sm text-[#667085] mt-2 leading-6">
                    Geographic and satellite information for analysis.
                  </p>

                </div>


                {/* Safer Navigation */}
                <div>

                  <Route
                    size={20}
                    className="text-[#123F66] mb-4"
                    strokeWidth={1.7}
                  />

                  <h3 className="font-semibold text-[#243447]">
                    Safer Navigation
                  </h3>

                  <p className="text-sm text-[#667085] mt-2 leading-6">
                    Route planning around hazardous areas.
                  </p>

                </div>

              </div>

            </div>

          </div>

        </div>

      </section>

    </main>
  );
}