"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import "./globals.css";
import { Activity, Database, GitCompare, LayoutDashboard, LineChart, FlaskConical, Terminal } from "lucide-react";

const NAV = [
  { href: "/",               label: "Research Workspace",      icon: LayoutDashboard },
  { href: "/explorer",       label: "Dataset Registry",        icon: Database },
  { href: "/timeline",       label: "Longitudinal Signals",    icon: Activity },
  { href: "/representations",label: "Representation Hub",      icon: LineChart },
  { href: "/compare",        label: "Representation Comparison", icon: GitCompare },
  { href: "/benchmark",      label: "Benchmark Center",         icon: FlaskConical },
  { href: "http://localhost:8000/docs", label: "Research API Playground", icon: Terminal },
];

const WORKFLOW = [
  "Dataset",
  "Universal Hormonal Schema",
  "Timeline",
  "HSF",
  "Representation",
  "Registry",
  "Benchmark",
  "Applications"
];

const isStepActive = (step: string, path: string) => {
  if (path === "/") {
    return true; // on dashboard, show the complete vision
  }
  if (path === "/explorer" && ["Dataset", "Universal Hormonal Schema", "Registry"].includes(step)) return true;
  if (path === "/timeline" && ["Dataset", "Universal Hormonal Schema", "Timeline"].includes(step)) return true;
  if (path === "/representations" && ["HSF", "Representation"].includes(step)) return true;
  if (path === "/compare" && ["Representation", "Registry"].includes(step)) return true;
  if (path === "/benchmark" && ["Benchmark", "Applications"].includes(step)) return true;
  return false;
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 min-h-screen flex font-sans">
        {/* Sidebar */}
        <aside className="w-56 shrink-0 border-r border-zinc-900 bg-zinc-950 flex flex-col py-6 px-4 gap-1">
          <div className="mb-6 px-2">
            <span className="text-sm font-semibold text-violet-400 tracking-wide">HormoneOS</span>
            <p className="text-[10px] text-zinc-500 mt-0.5 font-medium">Research Infrastructure</p>
          </div>
          {NAV.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors border ${
                  isActive
                    ? "text-violet-400 bg-violet-950/20 font-medium border-violet-900/35"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900 border-transparent"
                }`}
                {...(href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
              >
                <Icon size={15} />
                <span className="truncate">{label}</span>
              </Link>
            );
          })}
        </aside>

        {/* Main Wrapper */}
        <div className="flex-1 flex flex-col min-h-screen">
          {/* Persistent Research Workflow Header */}
          <div className="bg-zinc-950 border-b border-zinc-900/60 py-3 px-8 flex flex-col md:flex-row md:items-center md:justify-between gap-2.5 shrink-0">
            <span className="text-[9px] text-zinc-500 font-semibold uppercase tracking-widest">Active Research Pipeline:</span>
            <div className="flex flex-wrap items-center gap-1.5 text-[9px] font-mono font-medium">
              {WORKFLOW.map((step, idx) => {
                const active = isStepActive(step, pathname);
                return (
                  <div key={step} className="flex items-center gap-1.5">
                    <span className={`px-2 py-0.5 rounded-md border transition-all duration-300 ${
                      active
                        ? step === "Universal Hormonal Schema"
                          ? "bg-violet-950/40 text-violet-400 border-violet-800/40"
                          : step === "HSF"
                          ? "bg-sky-950/40 text-sky-400 border-sky-800/40"
                          : "bg-zinc-900 text-zinc-200 border-zinc-700"
                        : "bg-zinc-950/20 text-zinc-600 border-zinc-900/50"
                    }`}>
                      {step}
                    </span>
                    {idx < WORKFLOW.length - 1 && (
                      <span className={`transition-colors duration-300 ${active ? "text-zinc-600 animate-pulse" : "text-zinc-800"}`}>➜</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Main Scrollable Content */}
          <main className="flex-1 overflow-auto p-8 bg-zinc-950">{children}</main>
        </div>
      </body>
    </html>
  );
}
