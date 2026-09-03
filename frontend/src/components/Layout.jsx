import { Outlet, Link } from "react-router-dom";

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#F5F7FA] text-[#1F2937] flex flex-col">

      {/* HEADER */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#123F66] flex items-center justify-center text-white font-bold">
              V
            </div>

            <div>
              <h1 className="text-xl font-bold text-[#123F66]">
                VEYRiX
              </h1>

              <p className="text-xs text-gray-500">
                Multi-Hazard Prediction & Monitoring System
              </p>
            </div>
          </Link>

          <nav className="flex items-center gap-6 text-sm">
            <Link
              to="/"
              className="text-gray-600 hover:text-[#123F66]"
            >
              Dashboard
            </Link>

            <Link
              to="/ml"
              className="text-gray-600 hover:text-[#123F66]"
            >
              ML Prediction
            </Link>

            <Link
              to="/satellite"
              className="text-gray-600 hover:text-[#123F66]"
            >
              Satellite
            </Link>

            <Link
              to="/safe-routing"
              className="text-gray-600 hover:text-[#123F66]"
            >
              Safe Routing
            </Link>
          </nav>

        </div>
      </header>


      {/* PAGE CONTENT */}
      <main className="flex-1">
        <Outlet />
      </main>


      {/* CONTRIBUTORS */}
      <section className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-8">

          <h2 className="text-lg font-bold text-[#123F66] mb-5">
            VEYRiX Contributors
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">

            <div>
              <p className="font-medium">Yadavalli Satya Harsha</p>
              <p className="text-gray-500">yadavallibhavanirao@gmail.com</p>
            </div>

            <div>
              <p className="font-medium">Vanampally Sai Vishal Reddy</p>
              <p className="text-gray-500">v14406746@gmail.com</p>
            </div>

            <div>
              <p className="font-medium">Tirupati Shashank</p>
              <p className="text-gray-500">shashanksasi3@gmail.com</p>
            </div>

            <div>
              <p className="font-medium">Eemani Sai Harshini</p>
              <p className="text-gray-500">eemanisaiharshini@gmail.com</p>
            </div>

            <div>
              <p className="font-medium">Shaik Saleha</p>
              <p className="text-gray-500">salehashaikj986@gmail.com</p>
            </div>

            <div>
              <p className="font-medium">Nelluri Shalini Gayathri</p>
              <p className="text-gray-500">nelluri.sg@gmail.com</p>
            </div>

          </div>

        </div>
      </section>


      {/* FOOTER */}
      <footer className="bg-[#123F66] text-white">
        <div className="max-w-7xl mx-auto px-6 py-5 text-center text-sm">
          <p>
            © 2026 VEYRiX. All rights reserved.
          </p>

          <p className="text-blue-200 mt-1">
            Multi-Hazard Prediction & Monitoring System
          </p>
        </div>
      </footer>

    </div>
  );
}