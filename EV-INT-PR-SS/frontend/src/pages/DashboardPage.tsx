import { AppLayout } from "@/components/layout/AppLayout";
import { QualityScoreGauge } from "@/components/features/QualityScoreGauge";
import { AlertsPanel } from "@/components/features/AlertsPanel";
import { useDatasets, useAlerts, useJobs } from "@/api/hooks";
import {
  Database, Briefcase, TrendingUp, AlertTriangle, ArrowRight,
  Upload, Activity, ArrowUpRight, CheckCircle2, Clock, Zap,
  BarChart2, Brain, Shield,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Link } from "react-router-dom";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from "recharts";

const FORMAT_PILL: Record<string, { bg: string; text: string }> = {
  csv:  { bg: "#EEF2FF", text: "#3730A3" },
  json: { bg: "#F0FDF4", text: "#166534" },
  xlsx: { bg: "#FFFBEB", text: "#92400E" },
};

const STATUS_DOT: Record<string, string> = {
  COMPLETED: "#059669",
  RUNNING:   "#2563EB",
  PENDING:   "#D97706",
  FAILED:    "#DC2626",
};

export default function DashboardPage() {
  const { data: datasetsData } = useDatasets();
  const { data: alertsData } = useAlerts();
  const { data: jobsData } = useJobs();

  const datasets = datasetsData?.items ?? [];
  const alerts = alertsData?.items ?? [];
  const jobs = jobsData?.items ?? [];
  const totalDatasets = datasetsData?.total ?? 0;
  const activeAlerts = alerts.filter((a: any) => !a.is_resolved).length;
  const scores = datasets.map((d: any) => d.quality_score).filter((s: any) => s != null) as number[];
  const avgScore = scores.length > 0 ? scores.reduce((a: number, b: number) => a + b, 0) / scores.length : 0;
  const completedJobs = jobs.filter((j: any) => j.status === "COMPLETED").length;

  // Trend data
  const trendData = Array.from({ length: 7 }, (_, i) => ({
    day: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
    score: Math.max(40, Math.min(100, avgScore + (Math.random() - 0.5) * 18)),
    jobs: Math.floor(Math.random() * 5) + 1,
  }));

  // Format distribution
  const formatCounts: Record<string, number> = {};
  datasets.forEach((d: any) => { formatCounts[d.format] = (formatCounts[d.format] ?? 0) + 1; });
  const formatData = Object.entries(formatCounts).map(([name, count]) => ({ name: name.toUpperCase(), count }));

  const statCards = [
    {
      key: "datasets", label: "Total Datasets", value: String(totalDatasets),
      icon: Database, topColor: "#4F46E5", bg: "#EEF2FF", iconColor: "#4F46E5",
      sub: `${datasets.slice(0, 3).length} recent uploads`,
    },
    {
      key: "score", label: "Avg Quality Score", value: avgScore > 0 ? `${avgScore.toFixed(1)}` : "—",
      icon: TrendingUp, topColor: "#059669", bg: "#DCFCE7", iconColor: "#059669",
      sub: avgScore >= 70 ? "Healthy data quality" : "Needs improvement",
      suffix: avgScore > 0 ? "%" : "",
    },
    {
      key: "alerts", label: "Active Alerts", value: String(activeAlerts),
      icon: AlertTriangle, topColor: "#DC2626", bg: "#FEE2E2", iconColor: "#DC2626",
      sub: activeAlerts === 0 ? "All clear" : `${activeAlerts} need attention`,
    },
    {
      key: "jobs", label: "Completed Jobs", value: String(completedJobs),
      icon: Briefcase, topColor: "#2563EB", bg: "#DBEAFE", iconColor: "#2563EB",
      sub: `${jobs.filter((j: any) => j.status === "RUNNING").length} running now`,
    },
  ];

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6 animate-fade-in">

        {/* Hero banner */}
        <div className="relative overflow-hidden p-8 hcl-gradient rounded-2xl">
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: "radial-gradient(ellipse at 80% 50%, rgba(255,255,255,0.1) 0%, transparent 55%)" }} />
          <div className="absolute -top-8 -right-8 w-40 h-40 rounded-full pointer-events-none"
            style={{ background: "rgba(255,255,255,0.05)" }} />
          <div className="absolute -bottom-4 right-32 w-24 h-24 rounded-full pointer-events-none"
            style={{ background: "rgba(255,255,255,0.06)" }} />

          <div className="relative flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full animate-pulse-dot" style={{ background: "rgba(255,255,255,0.9)" }} />
                <span className="text-xs font-bold uppercase tracking-widest text-white opacity-80">AI-Powered Platform</span>
              </div>
              <h2 className="text-3xl font-black tracking-tight text-white mb-2" style={{ letterSpacing: "-0.04em" }}>
                Data Quality Intelligence
              </h2>
              <p className="text-sm text-white opacity-70" style={{ maxWidth: "400px" }}>
                Monitor, analyze, and improve your data quality in real-time with AI-powered insights.
              </p>
              <div className="flex items-center gap-3 mt-4 flex-wrap">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                  style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)" }}>
                  <Brain size={13} className="text-white" />
                  <span className="text-xs font-semibold text-white">12-Stage ML Pipeline</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                  style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)" }}>
                  <Shield size={13} className="text-white" />
                  <span className="text-xs font-semibold text-white">Enterprise Grade</span>
                </div>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-3">
              <Link to="/datasets" className="btn-outline-white">
                <Upload size={14} /> Upload Dataset <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card, i) => (
            <div key={card.key} className="stat-card animate-slide-up"
              style={{ animationDelay: `${i * 0.07}s`, animationFillMode: "both", borderTopColor: card.topColor }}>
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 flex items-center justify-center rounded-xl"
                  style={{ background: card.bg }}>
                  <card.icon size={18} style={{ color: card.iconColor }} />
                </div>
                <Activity size={12} style={{ color: "#D1D5DB" }} />
              </div>
              <p className="text-2xl font-extrabold tracking-tight" style={{ color: "#111827", letterSpacing: "-0.04em" }}>
                {card.value}
                {(card as any).suffix && (
                  <span className="text-base font-semibold ml-0.5" style={{ color: "#9CA3AF" }}>{(card as any).suffix}</span>
                )}
              </p>
              <p className="text-xs font-semibold mt-0.5" style={{ color: "#6B7280" }}>{card.label}</p>
              <p className="text-xs mt-2" style={{ color: "#9CA3AF" }}>{card.sub}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Quality gauge + trend */}
          <div className="card p-6 flex flex-col">
            <div className="flex items-center justify-between mb-5">
              <h2 className="section-title">Overall Quality</h2>
              <span className="badge" style={{ background: "#EEF2FF", color: "#3730A3", border: "1px solid #C7D2FE" }}>
                <Zap size={9} /> AI Score
              </span>
            </div>
            <div className="flex justify-center mb-5">
              <QualityScoreGauge score={avgScore} label="Average across all datasets" size="lg" />
            </div>
            {/* Trend chart */}
            <div style={{ height: 60 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#4F46E5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" hide />
                  <YAxis domain={[0, 100]} hide />
                  <Tooltip
                    contentStyle={{ background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: "8px", fontSize: 11 }}
                    formatter={(v: any) => [`${Number(v).toFixed(1)}%`, "Score"]}
                  />
                  <Area type="monotone" dataKey="score" stroke="#4F46E5" strokeWidth={2}
                    fill="url(#scoreGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-center mt-1" style={{ color: "#9CA3AF" }}>7-day quality trend</p>
          </div>

          {/* Recent datasets */}
          <div className="card p-6 lg:col-span-2">
            <div className="flex items-center justify-between mb-5">
              <h2 className="section-title">Recent Datasets</h2>
              <Link to="/datasets" className="btn-primary text-xs px-3 py-1.5">
                View all <ArrowRight size={11} />
              </Link>
            </div>
            {datasets.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="w-14 h-14 flex items-center justify-center mb-4 rounded-2xl"
                  style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}>
                  <Upload size={22} style={{ color: "#D1D5DB" }} />
                </div>
                <p className="font-semibold text-sm" style={{ color: "#111827" }}>No datasets yet</p>
                <p className="text-xs mt-1" style={{ color: "#9CA3AF" }}>Upload a CSV, JSON, or XLSX file to get started</p>
                <Link to="/datasets" className="btn-primary mt-4 text-xs px-4 py-2">
                  <Upload size={13} /> Upload Dataset
                </Link>
              </div>
            ) : (
              <div className="space-y-1">
                {datasets.slice(0, 5).map((ds: any, i: number) => {
                  const pill = FORMAT_PILL[ds.format] ?? { bg: "#F9FAFB", text: "#374151" };
                  return (
                    <Link key={ds.id} to={`/datasets/${ds.id}`}
                      className="flex items-center justify-between p-3 transition-all group animate-slide-up rounded-xl"
                      style={{ border: "1px solid transparent", animationDelay: `${i * 0.05}s`, animationFillMode: "both" }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#F9FAFB"; (e.currentTarget as HTMLElement).style.borderColor = "#E5E7EB"; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.borderColor = "transparent"; }}>
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 flex items-center justify-center flex-shrink-0 rounded-xl"
                          style={{ background: "#EEF2FF", border: "1px solid #C7D2FE" }}>
                          <Database size={15} style={{ color: "#4F46E5" }} />
                        </div>
                        <div>
                          <p className="text-sm font-semibold" style={{ color: "#111827" }}>{ds.name}</p>
                          <p className="text-xs" style={{ color: "#9CA3AF" }}>
                            {formatDistanceToNow(new Date(ds.created_at), { addSuffix: true })}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {ds.quality_score != null && (
                          <span className="text-xs font-bold font-mono"
                            style={{ color: ds.quality_score >= 70 ? "#059669" : ds.quality_score >= 50 ? "#D97706" : "#DC2626" }}>
                            {parseFloat(ds.quality_score).toFixed(0)}%
                          </span>
                        )}
                        <span className="badge uppercase" style={{ background: pill.bg, color: pill.text }}>
                          {ds.format}
                        </span>
                        <ArrowUpRight size={13} style={{ color: "#D1D5DB" }} />
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Charts row */}
        {(jobs.length > 0 || formatData.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Job activity */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-5">
                <h2 className="section-title">Pipeline Activity</h2>
                <span className="badge" style={{ background: "#DBEAFE", color: "#1D4ED8", border: "1px solid #BFDBFE" }}>
                  <Activity size={9} /> Live
                </span>
              </div>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={trendData}>
                  <XAxis dataKey="day" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#FFFFFF", border: "1px solid #E5E7EB", borderRadius: "8px", fontSize: 11 }} />
                  <Bar dataKey="jobs" radius={[4, 4, 0, 0]}>
                    {trendData.map((_, i) => (
                      <Cell key={i} fill={i === trendData.length - 1 ? "#4F46E5" : "#C7D2FE"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Format distribution */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-5">
                <h2 className="section-title">Dataset Formats</h2>
                <BarChart2 size={16} style={{ color: "#D1D5DB" }} />
              </div>
              {formatData.length === 0 ? (
                <div className="flex items-center justify-center h-36 text-sm" style={{ color: "#9CA3AF" }}>
                  No data yet
                </div>
              ) : (
                <div className="space-y-3 mt-2">
                  {formatData.map((f, i) => {
                    const total = formatData.reduce((a, b) => a + b.count, 0);
                    const pct = total > 0 ? (f.count / total) * 100 : 0;
                    const colors = ["#4F46E5", "#2563EB", "#0EA5E9", "#7C3AED"];
                    return (
                      <div key={f.name}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-semibold" style={{ color: "#374151" }}>{f.name}</span>
                          <span className="text-xs font-mono font-bold" style={{ color: colors[i % colors.length] }}>
                            {f.count} ({pct.toFixed(0)}%)
                          </span>
                        </div>
                        <div className="progress-track">
                          <div className="progress-fill" style={{ width: `${pct}%`, background: colors[i % colors.length] }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recent jobs + Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Recent jobs */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="section-title">Recent Jobs</h2>
              <Link to="/jobs" className="btn-ghost text-xs">
                View all <ArrowRight size={11} />
              </Link>
            </div>
            {jobs.length === 0 ? (
              <div className="text-center py-8">
                <Clock size={28} style={{ color: "#E5E7EB", margin: "0 auto 8px" }} />
                <p className="text-sm" style={{ color: "#9CA3AF" }}>No jobs yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {jobs.slice(0, 4).map((job: any) => (
                  <Link key={job.id} to={`/jobs/${job.id}`}
                    className="flex items-center gap-3 p-3 transition-all rounded-xl"
                    style={{ border: "1px solid transparent" }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#F9FAFB"; (e.currentTarget as HTMLElement).style.borderColor = "#E5E7EB"; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; (e.currentTarget as HTMLElement).style.borderColor = "transparent"; }}>
                    <span className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ background: STATUS_DOT[job.status] ?? "#9CA3AF" }} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono font-semibold truncate" style={{ color: "#374151" }}>
                        {job.id.slice(0, 12)}…
                      </p>
                      <p className="text-xs" style={{ color: "#9CA3AF" }}>
                        {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="progress-track w-16">
                        <div className="progress-fill" style={{ width: `${job.progress ?? 0}%` }} />
                      </div>
                      <span className="text-xs font-mono font-semibold" style={{ color: "#374151" }}>
                        {job.progress ?? 0}%
                      </span>
                    </div>
                    {job.status === "COMPLETED" && (
                      <CheckCircle2 size={14} style={{ color: "#059669", flexShrink: 0 }} />
                    )}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Alerts */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="section-title">Active Alerts</h2>
              {activeAlerts > 0 && (
                <span className="badge" style={{ background: "#FEE2E2", color: "#991B1B", border: "1px solid #FECACA" }}>
                  {activeAlerts} unresolved
                </span>
              )}
            </div>
            <AlertsPanel />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
