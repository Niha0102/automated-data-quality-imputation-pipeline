import { useParams, Link } from "react-router-dom";
import {
  Loader2, Download, CheckCircle, AlertTriangle, Lightbulb,
  TrendingUp, ArrowLeft, FileText, BarChart2, Shield, Zap,
  Target, Activity, ChevronRight, Star, AlertCircle,
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { QualityScoreGauge } from "@/components/features/QualityScoreGauge";
import { DataProfileView } from "@/components/features/DataProfileView";
import { useReport } from "@/api/hooks";
import { apiClient } from "@/api/client";
import { useState } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium" style={{ color: "#374151" }}>{label}</span>
        <span className="text-sm font-bold font-mono" style={{ color }}>{value.toFixed(1)}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const { data: report, isLoading } = useReport(id!);
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "profile" | "issues">("overview");

  const handleDownload = async () => {
    setDownloading(true);
    try {
      // Try to get a download URL from the backend
      const res = await apiClient.get(`/reports/${id}/download`);
      if (res.data?.download_url) {
        window.open(res.data.download_url, "_blank");
      } else {
        // Fallback: generate a JSON download from the report data
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `report-${id?.slice(0, 8)}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      // Fallback: download report as JSON
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${id?.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  };

  if (isLoading) return (
    <AppLayout title="Report">
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="w-16 h-16 flex items-center justify-center hcl-gradient" style={{ borderRadius: "16px" }}>
          <Activity size={28} className="text-white animate-pulse" />
        </div>
        <p className="text-sm font-medium" style={{ color: "#6B7280" }}>Loading report...</p>
      </div>
    </AppLayout>
  );
  if (!report) return (
    <AppLayout title="Report">
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <FileText size={40} style={{ color: "#D1D5DB" }} />
        <p className="font-semibold" style={{ color: "#374151" }}>Report not found</p>
        <Link to="/jobs" className="btn-primary text-sm">Back to Jobs</Link>
      </div>
    </AppLayout>
  );

  const overallScore = report.quality_score ?? 0;
  const completeness = report.completeness ?? 0;
  const consistency = report.consistency ?? 0;
  const accuracy = report.accuracy ?? 0;
  const validity = report.validity ?? Math.round((completeness + consistency) / 2);

  const radarData = [
    { subject: "Completeness", value: completeness },
    { subject: "Consistency", value: consistency },
    { subject: "Accuracy", value: accuracy },
    { subject: "Validity", value: validity },
    { subject: "Uniqueness", value: report.uniqueness ?? 85 },
  ];

  const scoreColor = overallScore >= 70 ? "#059669" : overallScore >= 50 ? "#D97706" : "#DC2626";
  const scoreGrade = overallScore >= 90 ? "A+" : overallScore >= 80 ? "A" : overallScore >= 70 ? "B" : overallScore >= 60 ? "C" : "D";

  const tabs = [
    { key: "overview" as const, label: "Overview", icon: BarChart2 },
    { key: "issues" as const, label: `Issues & Fixes`, icon: AlertCircle },
    { key: "profile" as const, label: "Data Profile", icon: Target },
  ];

  return (
    <AppLayout title="Quality Report">
      <div className="space-y-6 animate-fade-in max-w-5xl">

        {/* Back + actions */}
        <div className="flex items-center justify-between">
          <Link to="/jobs" className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
            style={{ color: "#6B7280" }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#2563EB"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#6B7280"; }}>
            <ArrowLeft size={14} /> Back to Jobs
          </Link>
          <button onClick={handleDownload} disabled={downloading} className="btn-primary gap-2">
            {downloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {downloading ? "Downloading..." : "Download Report"}
          </button>
        </div>

        {/* Hero score card */}
        <div className="relative overflow-hidden hcl-gradient p-8" style={{ borderRadius: "12px" }}>
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: "radial-gradient(ellipse at 85% 50%, rgba(255,255,255,0.1) 0%, transparent 55%)" }} />
          <div className="relative flex items-center justify-between flex-wrap gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full animate-pulse-dot bg-white" style={{ opacity: 0.8 }} />
                <span className="text-xs font-bold uppercase tracking-widest text-white" style={{ opacity: 0.8 }}>
                  AI Quality Analysis Complete
                </span>
              </div>
              <h1 className="text-4xl font-black text-white mb-2" style={{ letterSpacing: "-0.04em" }}>
                Quality Report
              </h1>
              <p className="text-sm text-white" style={{ opacity: 0.7 }}>
                Job ID: <span className="font-mono">{id?.slice(0, 16)}…</span>
              </p>
              <div className="flex items-center gap-3 mt-4">
                <div className="flex items-center gap-2 px-3 py-1.5"
                  style={{ background: "rgba(255,255,255,0.15)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.25)" }}>
                  <Star size={13} className="text-white" />
                  <span className="text-sm font-bold text-white">Grade: {scoreGrade}</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5"
                  style={{ background: "rgba(255,255,255,0.15)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.25)" }}>
                  <Shield size={13} className="text-white" />
                  <span className="text-sm font-bold text-white">{overallScore >= 70 ? "Healthy" : overallScore >= 50 ? "Needs Attention" : "Critical"}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div className="text-6xl font-black text-white" style={{ letterSpacing: "-0.05em" }}>
                  {overallScore.toFixed(0)}
                </div>
                <div className="text-sm text-white font-semibold mt-1" style={{ opacity: 0.7 }}>/ 100</div>
                <div className="text-xs text-white mt-1 font-bold uppercase tracking-wider" style={{ opacity: 0.6 }}>
                  Quality Score
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1" style={{ background: "#F2F3F7", borderRadius: "8px", border: "1px solid #E8E8F0", width: "fit-content" }}>
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-semibold transition-all duration-200"
              style={{
                borderRadius: "6px",
                background: activeTab === key ? "#FFFFFF" : "transparent",
                color: activeTab === key ? "#1A1A2E" : "#6B7280",
                boxShadow: activeTab === key ? "0 1px 4px rgba(0,0,0,0.08)" : "none",
              }}>
              <Icon size={14} />{label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div className="space-y-5 animate-fade-in">

            {/* Score gauges */}
            <div className="card p-6">
              <h2 className="section-title mb-6">Quality Dimensions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <QualityScoreGauge score={completeness} label="Completeness" size="md" />
                <QualityScoreGauge score={consistency} label="Consistency" size="md" />
                <QualityScoreGauge score={accuracy} label="Accuracy" size="md" />
                <QualityScoreGauge score={validity} label="Validity" size="md" />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Radar chart */}
              <div className="card p-6">
                <h2 className="section-title mb-4">Quality Radar</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#E8E8F0" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: "#6B7280", fontSize: 11, fontWeight: 600 }} />
                    <Radar dataKey="value" stroke="#4338CA" fill="#4338CA" fillOpacity={0.15} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Score bars */}
              <div className="card p-6">
                <h2 className="section-title mb-5">Score Breakdown</h2>
                <div className="space-y-4">
                  <ScoreBar label="Completeness" value={completeness}
                    color={completeness >= 70 ? "#059669" : completeness >= 50 ? "#D97706" : "#DC2626"} />
                  <ScoreBar label="Consistency" value={consistency}
                    color={consistency >= 70 ? "#059669" : consistency >= 50 ? "#D97706" : "#DC2626"} />
                  <ScoreBar label="Accuracy" value={accuracy}
                    color={accuracy >= 70 ? "#059669" : accuracy >= 50 ? "#D97706" : "#DC2626"} />
                  <ScoreBar label="Validity" value={validity}
                    color={validity >= 70 ? "#059669" : validity >= 50 ? "#D97706" : "#DC2626"} />
                </div>
              </div>
            </div>

            {/* Executive summary */}
            {report.narrative && (
              <div className="card p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 flex items-center justify-center hcl-gradient" style={{ borderRadius: "8px" }}>
                    <Zap size={16} className="text-white" />
                  </div>
                  <h2 className="section-title">AI Executive Summary</h2>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: "#374151", lineHeight: 1.8 }}>
                  {report.narrative}
                </p>
              </div>
            )}

            {/* Recommendations */}
            {report.recommendations?.length > 0 && (
              <div className="card p-6">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-9 h-9 flex items-center justify-center"
                    style={{ background: "#EDE9FE", border: "1px solid #C4B5FD", borderRadius: "8px" }}>
                    <Lightbulb size={16} style={{ color: "#7C3AED" }} />
                  </div>
                  <h2 className="section-title">AI Recommendations</h2>
                  <span className="ml-auto badge" style={{ background: "#EDE9FE", color: "#5B21B6", border: "1px solid #C4B5FD" }}>
                    {report.recommendations.length} suggestions
                  </span>
                </div>
                <div className="space-y-2.5">
                  {report.recommendations.map((rec: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-4 transition-colors"
                      style={{ background: "#FAFAFA", border: "1px solid #F0F0F8", borderRadius: "8px" }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#F5F3FF"; (e.currentTarget as HTMLElement).style.borderColor = "#DDD6FE"; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "#FAFAFA"; (e.currentTarget as HTMLElement).style.borderColor = "#F0F0F8"; }}>
                      <div className="w-6 h-6 flex items-center justify-center flex-shrink-0 mt-0.5"
                        style={{ background: "#EDE9FE", borderRadius: "4px" }}>
                        <span className="text-xs font-bold" style={{ color: "#5B21B6" }}>{i + 1}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono font-bold px-2 py-0.5"
                            style={{ background: "#EFF6FF", color: "#1D4ED8", border: "1px solid #BFDBFE", borderRadius: "4px" }}>
                            {rec.column ?? "General"}
                          </span>
                          <span className="text-sm font-semibold" style={{ color: "#1A1A2E" }}>{rec.action}</span>
                        </div>
                        {rec.reason && (
                          <p className="text-xs mt-1.5" style={{ color: "#6B7280" }}>{rec.reason}</p>
                        )}
                      </div>
                      <ChevronRight size={14} style={{ color: "#D1D5DB", flexShrink: 0 }} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── ISSUES & FIXES TAB ── */}
        {activeTab === "issues" && (
          <div className="space-y-5 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Issues */}
              <div className="card p-6">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-9 h-9 flex items-center justify-center"
                    style={{ background: "#FEF3C7", border: "1px solid #FDE68A", borderRadius: "8px" }}>
                    <AlertTriangle size={16} style={{ color: "#D97706" }} />
                  </div>
                  <h2 className="section-title">Issues Found</h2>
                  <span className="ml-auto badge" style={{ background: "#FEF3C7", color: "#92400E", border: "1px solid #FDE68A" }}>
                    {report.issues?.length ?? 0}
                  </span>
                </div>
                {!report.issues?.length ? (
                  <div className="text-center py-8">
                    <CheckCircle size={32} style={{ color: "#D1FAE5", margin: "0 auto 8px" }} />
                    <p className="text-sm font-medium" style={{ color: "#6B7280" }}>No issues detected</p>
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {report.issues.map((issue: string, i: number) => (
                      <li key={i} className="flex items-start gap-2.5 p-3"
                        style={{ background: "#FFFBEB", border: "1px solid #FDE68A", borderRadius: "6px" }}>
                        <AlertTriangle size={13} className="mt-0.5 flex-shrink-0" style={{ color: "#D97706" }} />
                        <span className="text-sm" style={{ color: "#78350F" }}>{issue}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Fixes */}
              <div className="card p-6">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-9 h-9 flex items-center justify-center"
                    style={{ background: "#DCFCE7", border: "1px solid #BBF7D0", borderRadius: "8px" }}>
                    <CheckCircle size={16} style={{ color: "#16A34A" }} />
                  </div>
                  <h2 className="section-title">Fixes Applied</h2>
                  <span className="ml-auto badge" style={{ background: "#DCFCE7", color: "#166534", border: "1px solid #BBF7D0" }}>
                    {report.fixes?.length ?? 0}
                  </span>
                </div>
                {!report.fixes?.length ? (
                  <div className="text-center py-8">
                    <p className="text-sm font-medium" style={{ color: "#6B7280" }}>No fixes applied</p>
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {report.fixes.map((fix: string, i: number) => (
                      <li key={i} className="flex items-start gap-2.5 p-3"
                        style={{ background: "#F0FDF4", border: "1px solid #BBF7D0", borderRadius: "6px" }}>
                        <CheckCircle size={13} className="mt-0.5 flex-shrink-0" style={{ color: "#16A34A" }} />
                        <span className="text-sm" style={{ color: "#14532D" }}>{fix}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Issues bar chart */}
            {report.issues?.length > 0 && (
              <div className="card p-6">
                <h2 className="section-title mb-4">Issue Distribution</h2>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={report.issues.slice(0, 8).map((issue: string, i: number) => ({
                    name: `Issue ${i + 1}`,
                    severity: Math.max(20, 100 - i * 12),
                  }))}>
                    <XAxis dataKey="name" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ background: "#FFFFFF", border: "1px solid #E8E8F0", borderRadius: "8px", fontSize: 12 }}
                    />
                    <Bar dataKey="severity" radius={[4, 4, 0, 0]}>
                      {report.issues.slice(0, 8).map((_: any, i: number) => (
                        <Cell key={i} fill={i < 2 ? "#DC2626" : i < 5 ? "#D97706" : "#059669"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* ── PROFILE TAB ── */}
        {activeTab === "profile" && (
          <div className="card p-6 animate-fade-in">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 flex items-center justify-center"
                style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px" }}>
                <Target size={16} style={{ color: "#2563EB" }} />
              </div>
              <h2 className="section-title">Data Profile</h2>
            </div>
            {report.profile ? (
              <DataProfileView profile={report.profile} semanticTypes={report.semantic_types} />
            ) : (
              <div className="text-center py-12">
                <BarChart2 size={36} style={{ color: "#D1D5DB", margin: "0 auto 12px" }} />
                <p className="font-semibold" style={{ color: "#374151" }}>No profile data available</p>
                <p className="text-sm mt-1" style={{ color: "#9CA3AF" }}>Profile is generated during pipeline execution</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
