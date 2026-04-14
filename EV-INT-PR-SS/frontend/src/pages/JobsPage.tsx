import { AppLayout } from "@/components/layout/AppLayout";
import { useJobs } from "@/api/hooks";
import { Link } from "react-router-dom";
import { Briefcase, CheckCircle2, XCircle, Clock, Loader2, ArrowRight, Activity, ArrowUpRight, Upload } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const STATUS_CONFIG: Record<string, { icon: any; bg: string; text: string; border: string; label: string; dot: string }> = {
  PENDING:   { icon: Clock,        bg: "#FFFBEB", text: "#92400E", border: "#FDE68A", label: "Pending",   dot: "#D97706" },
  RUNNING:   { icon: Loader2,      bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE", label: "Running",   dot: "#2563EB" },
  COMPLETED: { icon: CheckCircle2, bg: "#DCFCE7", text: "#166534", border: "#BBF7D0", label: "Completed", dot: "#16A34A" },
  FAILED:    { icon: XCircle,      bg: "#FEF2F2", text: "#991B1B", border: "#FECACA", label: "Failed",    dot: "#DC2626" },
};

export default function JobsPage() {
  const { data, isLoading } = useJobs();
  const jobs = data?.items ?? [];

  return (
    <AppLayout title="Jobs">
      <div className="space-y-5 animate-fade-in">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{data?.total ?? 0} Pipeline Jobs</h1>
            <p className="text-sm mt-0.5" style={{ color: "#64748B" }}>Track your data quality pipeline runs in real-time</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge" style={{ background: "#EFF6FF", color: "#1D4ED8", border: "1px solid #BFDBFE" }}>
              <Activity size={10} /> Live Monitoring
            </span>
            <Link to="/datasets" className="btn-primary">
              <Upload size={14} /> New Job
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 size={28} className="animate-spin" style={{ color: "#4338CA" }} />
          </div>
        ) : jobs.length === 0 ? (
          <div className="card p-16 text-center">
            <div className="w-16 h-16 flex items-center justify-center mx-auto mb-4"
              style={{ background: "#F4F4F6", border: "1px solid #E5E5EF", borderRadius: "4px" }}>
              <Briefcase size={28} style={{ color: "#9CA3AF" }} />
            </div>
            <p className="font-bold text-lg" style={{ color: "#1A1A2E" }}>No jobs yet</p>
            <p className="text-sm mt-1.5" style={{ color: "#6B7280" }}>Upload a dataset and run a pipeline to see jobs here</p>
            <Link to="/datasets" className="btn-primary mt-5 mx-auto">
              Go to Datasets <ArrowRight size={14} />
            </Link>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="table-header">Job ID</th>
                  <th className="table-header">Dataset</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Progress</th>
                  <th className="table-header">Created</th>
                  <th className="table-header w-10"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job: any) => {
                  const cfg = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.PENDING;
                  const Icon = cfg.icon;
                  return (
                    <tr key={job.id} className="table-row">
                      <td className="table-cell">
                        <Link to={`/jobs/${job.id}`} className="font-mono text-xs font-semibold"
                          style={{ color: "#2563EB" }}>
                          {job.id.slice(0, 8)}…
                        </Link>
                      </td>
                      <td className="table-cell font-mono text-xs" style={{ color: "#6B7280" }}>
                        {job.dataset_id ? (
                          <Link to={`/datasets/${job.dataset_id}`} className="transition-colors"
                            style={{ color: "#6B7280" }}
                            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#2563EB"; }}
                            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#6B7280"; }}>
                            {job.dataset_id.slice(0, 8)}…
                          </Link>
                        ) : "—"}
                      </td>
                      <td className="table-cell">
                        <span className="badge gap-1.5" style={{ background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}` }}>
                          <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.dot }} />
                          <Icon size={11} className={job.status === "RUNNING" ? "animate-spin" : ""} />
                          {cfg.label}
                        </span>
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center gap-2.5">
                          <div className="progress-track w-28">
                            <div className="progress-fill" style={{ width: `${job.progress ?? 0}%` }} />
                          </div>
                          <span className="text-xs tabular-nums font-mono font-semibold" style={{ color: "#334155" }}>
                            {job.progress ?? 0}%
                          </span>
                        </div>
                      </td>
                      <td className="table-cell text-xs" style={{ color: "#94A3B8" }}>
                        {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                      </td>
                      <td className="table-cell">
                        <Link to={`/jobs/${job.id}`} className="p-1.5 rounded transition-colors inline-flex"
                          style={{ color: "#9CA3AF" }}
                          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#2563EB"; (e.currentTarget as HTMLElement).style.background = "#EFF6FF"; }}
                          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#9CA3AF"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                          <ArrowUpRight size={14} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
