import { NavLink, Outlet, Link } from "react-router-dom";

const navItems = [
  { to: "/", label: "Home", end: true },
  { to: "/ml", label: "ML Prediction" },
  { to: "/satellite", label: "Satellite" },
  { to: "/safe-routing", label: "Safe Routing" },
];

const contributors = [
  { name: "Yadavalli Satya Harsha", email: "yadavallibhavanirao@gmail.com" },
  { name: "Vanampally Sai Vishal Reddy", email: "v14406746@gmail.com" },
  { name: "Tirupati Shashank", email: "shashanksasi3@gmail.com" },
  { name: "Eemani Sai Harshini", email: "eemanisaiharshini@gmail.com" },
  { name: "Nelluri Shalini Gayathri", email: "nelluri.sg@gmail.com" },
  { name: "Shaik Saleha", email: "salehashaikj986@gmail.com" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-[#f7f9fb] text-[#253142] flex flex-col">
      <header className="bg-white border-b border-[#dfe5eb]">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="min-h-[78px] flex items-center justify-between gap-8">
            <Link to="/" className="flex items-center gap-3 shrink-0" aria-label="VEYRiX home">
              <img
                src="/assets/veyrix-symbol.png"
                alt="VEYRiX"
                className="w-12 h-12 object-contain"
              />
              <div className="leading-none">
                <div className="text-[22px] font-bold tracking-[0.08em] text-[#123f66]">
                  VEYRiX
                </div>
                <div className="mt-1 text-[10px] tracking-[0.08em] uppercase text-[#6b7785]">
                  Multi-Hazard Prediction &amp; Monitoring System
                </div>
              </div>
            </Link>

            <nav className="hidden md:flex items-center self-stretch gap-7" aria-label="Main navigation">
              {navItems.map(({ to, label, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `relative flex items-center text-sm font-medium transition-colors ${
                      isActive ? "text-[#123f66]" : "text-[#596575] hover:text-[#123f66]"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {label}
                      {isActive && (
                        <span className="absolute left-0 right-0 -bottom-[1px] h-[2px] bg-[#1b73a8]" />
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      {/* CONTRIBUTORS */}
      <section className="bg-white border-t border-[#dfe5eb] mt-12">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 py-9">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8">
            <div className="lg:max-w-xs">
              <h2 className="text-lg font-bold text-[#123f66]">VEYRiX Contributors</h2>
              <p className="mt-2 text-sm leading-6 text-[#718096]">
                Project contributors involved in developing and implementing the VEYRiX platform.
              </p>
            </div>

            <div className="w-full lg:max-w-3xl grid grid-cols-1 sm:grid-cols-2 gap-x-12 gap-y-5">
              {contributors.map((contributor) => (
                <div key={contributor.email} className="border-l-2 border-[#e5ebf1] pl-4">
                  <p className="text-sm font-semibold text-[#344054]">{contributor.name}</p>
                  <p className="mt-1 text-xs text-[#718096] break-all">{contributor.email}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-[#123f66] text-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <img src="/assets/veyrix-symbol.png" alt="" className="w-8 h-8 object-contain" />
            <div>
              <p className="text-sm font-semibold">VEYRiX</p>
              <p className="text-[11px] text-blue-100">
                Multi-Hazard Prediction &amp; Monitoring System
              </p>
            </div>
          </div>
          <p className="text-xs text-blue-100">© 2026 VEYRiX. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
