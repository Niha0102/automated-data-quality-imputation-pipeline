import { Bell, Search, ChevronRight, Zap, LogOut } from "lucide-react";
import { useAlerts } from "@/api/hooks";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/datasets":  "Datasets",
  "/jobs":      "Pipeline Jobs",
  "/reports":   "Reports",
  "/settings":  "Settings",
  "/admin":     "Admin Panel",
};

export function Header({ title }: { title: string }) {
  const { data: alertsData } = useAlerts();
  const unread = alertsData?.items?.filter((a: any) => !a.is_resolved).length ?? 0;
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const pageTitle = PAGE_TITLES[location.pathname] ?? title;

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <header className="h-14 flex items-center justify-between px-6 sticky top-0 z-20"
      style={{
        background: "linear-gradient(135deg, #0D47A1 0%, #1565C0 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
        boxShadow: "0 2px 12px rgba(13,71,161,0.3)",
      }}>

      {/* Breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.5)" }}>Platform</span>
        <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.3)" }} />
        <h1 className="text-sm font-bold text-white" style={{ letterSpacing: "-0.01em" }}>{pageTitle}</h1>
      </div>

      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 cursor-pointer transition-all rounded-lg"
          style={{ background: "rgba(255,255,255,0.12)", border: "1.5px solid rgba(255,255,255,0.2)", minWidth: "200px" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.2)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.12)"; }}>
          <Search size={13} style={{ color: "rgba(255,255,255,0.6)" }} />
          <span className="text-xs flex-1" style={{ color: "rgba(255,255,255,0.5)" }}>Search datasets, jobs…</span>
          <kbd className="px-1.5 py-0.5 font-mono text-xs rounded"
            style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.2)", color: "rgba(255,255,255,0.6)" }}>
            ⌘K
          </kbd>
        </div>

        {/* AI Active pill */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
          style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)" }}>
          <Zap size={11} className="text-white" />
          <span className="text-xs font-bold text-white">AI Active</span>
          <span className="w-1.5 h-1.5 rounded-full animate-pulse-dot" style={{ background: "#4ADE80" }} />
        </div>

        {/* Alerts bell */}
        <button className="relative p-2 rounded-lg transition-all"
          style={{ color: "rgba(255,255,255,0.7)" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.15)"; (e.currentTarget as HTMLElement).style.color = "#FFFFFF"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)"; }}>
          <Bell size={16} />
          {unread > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 flex items-center justify-center text-white font-bold ring-2 rounded-full"
              style={{ background: "#DC2626", fontSize: "9px", ringColor: "#1565C0" }}>
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </button>

        {/* Logout */}
        <button onClick={handleLogout} title="Sign out"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all text-sm font-semibold"
          style={{ background: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.85)", border: "1px solid rgba(255,255,255,0.2)" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(220,38,38,0.3)"; (e.currentTarget as HTMLElement).style.color = "#FCA5A5"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.12)"; (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.85)"; }}>
          <LogOut size={14} />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </header>
  );
}
