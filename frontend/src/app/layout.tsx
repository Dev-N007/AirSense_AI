import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-heading",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AirSense AI - Delhi Air Quality Intelligence Platform",
  description: "AI-Powered Urban Air Quality forecasting, SHAP explainability, and automated GRAP action recommendations for Delhi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Static sidebar navigation paths
  const navItems = [
    { name: "Dashboard", href: "/", icon: "📊" },
    { name: "Forecast & SHAP", href: "/forecast", icon: "📈" },
    { name: "Geospatial Map", href: "/map", icon: "🗺️" },
    { name: "Admin Recommendations", href: "/recommendations", icon: "🛡️" },
    { name: "Citizen Advisory", href: "/advisory", icon: "📢" },
  ];

  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} h-full dark`}>
      <body className="min-h-full bg-slate-950 text-slate-100 font-sans flex overflow-hidden">
        {/* Immersive background glow effects */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-500/10 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 blur-[120px] pointer-events-none" />

        {/* Root Shell */}
        <div className="flex w-full h-screen z-10">
          
          {/* Sidebar */}
          <aside className="w-64 bg-slate-900/60 backdrop-blur-md border-r border-slate-800 flex flex-col justify-between shrink-0">
            <div>
              {/* Brand Logo */}
              <div className="p-6 border-b border-slate-800/80 flex items-center gap-3">
                <span className="text-3xl">🍃</span>
                <div>
                  <h1 className="font-heading font-bold text-xl bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
                    AirSense AI
                  </h1>
                  <p className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
                    Predict. Explain. Act.
                  </p>
                </div>
              </div>

              {/* Navigation Links */}
              <nav className="p-4 space-y-1">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/50 transition-all duration-200 group font-medium"
                  >
                    <span className="text-xl group-hover:scale-110 transition-transform duration-200">
                      {item.icon}
                    </span>
                    <span className="text-sm">{item.name}</span>
                  </Link>
                ))}
              </nav>
            </div>

            {/* Admin Profile & Status Footer */}
            <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-emerald-500 to-blue-600 flex items-center justify-center font-heading font-bold text-sm text-white shadow-lg shadow-emerald-500/10">
                  DA
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Delhi Admin</h4>
                  <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    System Active
                  </p>
                </div>
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            
            {/* Header */}
            <header className="h-16 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md">
                  ET AI 2026
                </span>
                <span className="text-xs text-slate-400">Target City: Delhi, India</span>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-[10px] text-slate-400 font-semibold uppercase">Delhi Local Time</p>
                  <p className="text-xs font-bold text-slate-200 font-mono">00:06 AM IST</p>
                </div>
                <div className="px-3 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/60 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                  <span className="text-[10px] font-bold text-slate-300">AQI Alert Active</span>
                </div>
              </div>
            </header>

            {/* Page Content Container */}
            <main className="flex-1 overflow-y-auto p-8 relative">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
