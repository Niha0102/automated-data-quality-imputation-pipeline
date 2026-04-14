import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Database, Briefcase, FileText,
  Settings, Shield, LogOut, Activity, BarChart2,
  Bell, ChevronRight,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useAlerts } from "@/api/hooks";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/datasets",  icon: Database,        label: "Datasets"  },
  { to: "/jobs",      icon: Briefcase,       label: "Jobs"      },
  { to: "/reports",   icon: BarChart2,       label: "Reports"   },
  { to: "/settings",  icon: Settings,        label: "Settings"  },
];

const NAVY = "#0D47A1";
const NAVY_DARK = "#0A3880";
const NAVY_LIGHT = "#1565C0";

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { data: alertsData } = useAlerts();
  const unread = alertsData?.items?.filter((a: any) => !a.is_resolved).length ?? 0;
  const initials = user?.email?.[0]?.toUpperCase() ?? "U";

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <aside className="w-60 flex flex-col h-screen fixed left-0 top-0 z-30"
      style={{ background: "linear-gradient(180deg, #0D47A1 0%, #0A3880 100%)", borderRight: "1px solid rgba(255,255,255,0.08)" }}>

      {/* Logo */}
      <div className="px-4 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 flex items-center justify-center flex-shrink-0 rounded-xl"
            style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)" }}>
            <Activity size={17} className="text-white" />
          </div>
          <div>
            <p className="font-extrabold text-sm leading-tight text-white" style={{ letterSpacing: "-0.02em" }}>
              DataQuality AI
            </p>
            <p className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>Intelligence Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        <p className="px-3 mb-2 font-bold uppercase tracking-widest"
          style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }}>
          Navigation
        </p>

        <div className="space-y-0.5">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to}
              className="flex items-center gap-3 px-3 py-2.5 text-sm transition-all duration-150 rounded-lg group relative"
              style={({ isActive }) => isActive
                ? { color: "#FFFFFF", background: "rgba(255,255,255,0.18)", fontWeight: 700 }
                : { color: "rgba(255,255,255,0.65)", fontWeight: 500 }
              }
            >
              {({ isActive }) => (
                <>
                  <div className="w-7 h-7 flex items-center justify-center flex-shrink-0 rounded-lg transition-all"
                    style={{ background: isActive ? "rgba(255,255,255,0.2)" : "transparent" }}>
                    <Icon size={15} style={{ color: isActive ? "#FFFFFF" : "rgba(255,255,255,0.55)" }} />
                  </div>
                  <span className="flex-1">{label}</span>
                  {to === "/jobs" && unread > 0 && (
                    <span className="w-5 h-5 flex items-center justify-center text-white font-bold rounded-full"
                      style={{ background: "#DC2626", fontSize: "9px" }}>
                      {unread > 9 ? "9+" : unread}
                    </span>
                  )}
                  {isActive && <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.5)" }} />}
                </>
              )}
            </NavLink>
          ))}
        </div>

        {user?.role === "admin" && (
          <>
            <p className="px-3 mt-5 mb-2 font-bold uppercase tracking-widest"
              style={{ color: "rgba(255,255,255,0.35)", fontSize: "10px" }}>
              Administration
            </p>
            <NavLink to="/admin"
              className="flex items-center gap-3 px-3 py-2.5 text-sm transition-all duration-150 rounded-lg"
              style={({ isActive }) => isActive
                ? { color: "#FFFFFF", background: "rgba(255,255,255,0.18)", fontWeight: 700 }
                : { color: "rgba(255,255,255,0.65)", fontWeight: 500 }
              }
            >
              {({ isActive }) => (
                <>
                  <div className="w-7 h-7 flex items-center justify-center flex-shrink-0 rounded-lg"
                    style={{ background: isActive ? "rgba(255,255,255,0.2)" : "transparent" }}>
                    <Shield size={15} style={{ color: isActive ? "#FFFFFF" : "rgba(255,255,255,0.55)" }} />
                  </div>
                  <span className="flex-1">Admin Panel</span>
                  {isActive && <ChevronRight size={12} style={{ color: "rgba(255,255,255,0.5)" }} />}
                </>
              )}
            </NavLink>
          </>
        )}

        {unread > 0 && (
          <div className="mt-4 mx-1 p-3 rounded-lg"
            style={{ background: "rgba(220,38,38,0.2)", border: "1px solid rgba(220,38,38,0.4)" }}>
            <div className="flex items-center gap-2">
              <Bell size={12} style={{ color: "#FCA5A5" }} />
              <span className="text-xs font-semibold" style={{ color: "#FCA5A5" }}>
                {unread} active alert{unread > 1 ? "s" : ""}
              </span>
            </div>
          </div>
        )}
      </nav>

      {/* User footer */}
      <div className="px-3 py-3" style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}>
        <div className="flex items-center gap-2.5 px-2.5 py-2.5 rounded-xl group cursor-pointer transition-all"
          style={{ background: "rgba(255,255,255,0.08)" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.15)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)"; }}>
          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0 rounded-lg"
            style={{ background: "rgba(255,255,255,0.2)", border: "1px solid rgba(255,255,255,0.3)" }}>
            <span className="text-white text-xs font-bold">{initials}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold truncate text-white">{user?.email}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full animate-pulse-dot" style={{ background: "#4ADE80" }} />
              <p className="text-xs capitalize" style={{ color: "rgba(255,255,255,0.5)" }}>{user?.role}</p>
            </div>
          </div>
          <button onClick={handleLogout} title="Sign out"
            className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
            style={{ color: "rgba(255,255,255,0.6)" }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#FCA5A5"; (e.currentTarget as HTMLElement).style.background = "rgba(220,38,38,0.25)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.6)"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}
