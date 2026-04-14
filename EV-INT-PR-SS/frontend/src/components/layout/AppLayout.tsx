import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useAuthStore } from "@/store/authStore";

interface Props { children: ReactNode; title?: string; }

export function AppLayout({ children, title = "Dashboard" }: Props) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "#F0F4F8" }}>
      <Sidebar />
      <div className="flex-1 flex flex-col ml-60 overflow-hidden">
        <Header title={title} />
        <main className="flex-1 overflow-y-auto p-6 animate-fade-in" style={{ background: "#F0F4F8" }}>
          {children}
        </main>
      </div>
    </div>
  );
}
