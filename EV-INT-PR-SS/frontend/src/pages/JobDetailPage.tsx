import { useParams, Link } from "react-router-dom";
import { Loader2, CheckCircle, XCircle, ChevronRight, Activity, Clock, ArrowLeft } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { useJob } from "@/api/hooks";
import { useJobUpdates } from "@/hooks/useJobUpdates";
import { useJobStore } from "@/store/jobStore";
import { formatDistanceToNow } from "date-fns";

const STAGES = [
  { key: "load",          label: "Load Dataset",          pct: 5   },
  { key: "profile",       label: "Profile Data",           pct: 15  },
  { key: "score_initial", label: "Initial Quality Score",  pct: 20  },
  { key: "impute",        label: "Impute Missing Values",  pct: 30  },
  { key: "outlier",       label: "Detect Outliers",        pct: 40  },
  { key: "transform",     label: "Transform Data",         pct: 55  },
  { key: "anomaly",       label: "Anomaly Detection",      pct: 65  },
  { key: "drift",         label: "Drift Detection",        pct: 75  },
  { key: "score_final",   label: "Final Quality Score",    pct: 80  },
  { key: "ai_advisor",    label: "AI Analysis",            pct: 88  },
  { key: "report",        label: "Generate Report",        pct: 95  },
  { key: "save",          label: "Save Results",           pct: 100 },
];

const STATUS_STYLE: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  COMPLETED: { bg: "#DCFCE7", text: "#166534", border: "#BBF7D0", dot: "#059669" },
  FAILED:    { bg: "#FEF2F2", text: "#991B1B", border: "#FECACA", dot: "#DC2626" },
  RUNNING:   { bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE", dot: "#2563EB" },
  PENDING:   { bg: "#F5F3FF", text: "#5B21B6", border: "#DDD6FE", dot: "#7C3AED" },
};

function StageStep({ label, progress, stagePct }: { label: string; progress: number; stagePct: number }) {
  const done = progress >= stagePct;
  const active = progress >= stagePct - 15 && progress < stagePct;
  return (
    <div className="flex items-center gap-3 py-2.5">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-all duration-300"
        style={{
          background: done ? "#DCFCE7" : active ? "#EFF6FF" : "#F9FAFB",
          border: `1px solid ${done ? "#BBF7D0" : active ? "#BFDBFE" : "#E8E8F0"}`,
        }}>
        {done
          ? <CheckCircle size={14} style={{ color: "#059669" }} />
          : active
          ? <Activity size={12} style={{ color: "#2563EB" }} className="animate-pulse" />
          : <div className="w-2 h-2 rounded-full" style={{ background: "#D1D5DB" }} />
        }
      </div>
      <span className="text-sm font-medium transition-colors duration-300"
        style={{ color: done ? "#0F0F1A" : active ? "#2563EB" : "#9CA3AF" }}>
        {label}
      </span>
      {done && <span className="ml-auto text-xs font-semibold" style={{ color: "#059669" }}>Done</span>}
      {active && <span className="ml-auto text-xs font-semibold animate-pulse" style={{ color: "#2563EB" }}>Running…</span>}
    </div>
  );
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading } = useJob(id!);
  useJobUpdates(id);
  const liveProgress = useJobStore((s) => s.jobs[id!]?.progress ?? job?.progress ?? 0);
  const liveStatus = useJobStore((s) => s.jobs[id!]?.status ?? job?.status ?? "PENDING");

  if (isLoading) return (
    <AppLayout title="Job">
      <div className="flex items-center justify-center py-16">
        <Loader2 size={24} className="animate-spin" style={{ color: "#4338CA" }} />
      </div>
    </AppLayout>
  );
  if (!job) return <AppLayout title="Job"><p style={{ color: "#6B7280" }}>Job not found.</p></AppLayout>;

  const ss = STATUS_STYLE[liveStatus] ?? STATUS_STYLE.PENDING;
  const completedStages = STAGES.filter(s => liveProgress >= s.pct).length;

  return (
    <AppLayout title="Job Detail">
      <div className="space-y-5 animate-fade-in max-w-3xl">

        {/* Back */}
        <Link to="/jobs" className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
          style={{ color: "#6B7280" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#4338CA"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#6B7280"; }}>
          <ArrowLeft size={14} /> Back to Jobs
        </Link>

        {/* Header card */}
        <div className="card p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <p className="label mb-1">Job ID</p>
              <p className="font-mono text-sm font-semibold" style={{ color: "#0F0F1A" }}>{job.id}</p>
            </div>
            <span className="badge gap-1.5" style={{ background: ss.bg, color: ss.text, border: `1px solid ${ss.border}` }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: ss.dot }} />
              {liveStatus === "RUNNING" && <Activity size={11} className="animate-pulse" />}
              {liveStatus === "COMPLETED" && <CheckCircle size={11} />}
              {liveStatus === "FAILED" && <XCircle size={11} />}
              {liveStatus === "PENDING" && <Clock size={11} />}
              {liveStatus}
            </span>
          </div>

          {/* Progress */}
          <div className="mb-5">
            <div className="flex items-center justify-between mb-2">
              <span className="label">Pipeline Progress</span>
              <span className="text-sm font-bold font-mono" style={{ color: "#0F0F1A" }}>{liveProgress}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${liveProgress}%` }} />
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs" style={{ color: "#9CA3AF" }}>
                {completedStages} of {STAGES.length} stages complete
              </span>
              {liveStatus === "RUNNING" && (
                <span className="text-xs font-medium animate-pulse" style={{ color: "#2563EB" }}>Processing…</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs" style={{ color: "#9CA3AF" }}>
            <span className="flex items-center gap-1.5">
              <Clock size={11} />
              Started {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
            </span>
            {liveStatus === "COMPLETED" && (
              <Link to={`/reports/${job.id}`} className="btn-primary flex items-center gap-1.5 text-xs px-3 py-2">
                View Report <ChevronRight size={12} />
              </Link>
            )}
          </div>

          {job.error_message && (
            <div className="mt-4 p-3 rounded-xl" style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}>
              <div className="flex items-center gap-2 text-sm" style={{ color: "#DC2626" }}>
                <XCircle size={14} />
                <span>{job.error_message}</span>
              </div>
            </div>
          )}
        </div>

        {/* Pipeline stages */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "#EFF6FF", border: "1px solid #BFDBFE" }}>
              <Activity size={15} style={{ color: "#2563EB" }} />
            </div>
            <h3 className="section-title">Pipeline Stages</h3>
          </div>
          <div className="divide-y" style={{ borderColor: "#F1F5F9" }}>
            {STAGES.map((stage) => (
              <StageStep key={stage.key} label={stage.label} progress={liveProgress} stagePct={stage.pct} />
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
