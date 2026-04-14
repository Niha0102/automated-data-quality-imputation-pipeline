import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";

const AuthPage = lazy(() => import("@/pages/AuthPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const DatasetsPage = lazy(() => import("@/pages/DatasetsPage"));
const DatasetDetailPage = lazy(() => import("@/pages/DatasetDetailPage"));
const JobDetailPage = lazy(() => import("@/pages/JobDetailPage"));
const ReportPage = lazy(() => import("@/pages/ReportPage"));
const JobsPage = lazy(() => import("@/pages/JobsPage"));
const AdminPage = lazy(() => import("@/pages/AdminPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-screen bg-brand-bg">
      <Loader2 size={32} className="animate-spin text-brand-accent" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" theme="light" richColors />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/reports/:id" element={<ReportPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
