import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Loader2, Play, GitBranch, BarChart2, Briefcase, Database, Calendar, ArrowLeft } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { NLQueryBar } from "@/components/features/NLQueryBar";
import { useDataset, useDatasetVersions, useSubmitJob } from "@/api/hooks";
import { formatDistanceToNow } from "date-fns";

type Tab = "profile" | "versions" | "jobs";

const FORMAT_PILL: Record<string, { bg: string; text: string; border: string }> = {
  csv:  { bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE" },
  json: { bg: "#F5F3FF", text: "#6D28D9", border: "#DDD6FE" },
  xlsx: { bg: "#FFFBEB", text: "#92400E", border: "#FDE68A" },
};

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("profile");
  const { data: dataset, isLoading } = useDataset(id!);
  const { data: versions } = useDatasetVersions(id!);
  const submitJob = useSubmitJob();

  if (isLoading) return (
    <AppLayout title="Dataset">
      <div className="flex items-center justify-center py-16">
        <Loader2 size={24} className="animate-spin" style={{ color: "#4338CA" }} />
      </div>
    </AppLayout>
  );
  if (!dataset) return <AppLayout title="Dataset"><p style={{ color: "#6B7280" }}>Dataset not found.</p></AppLayout>;

  const handleRunPipeline = async () => {
    const job = await submitJob.mutateAsync({ dataset_id: id!, pipeline_config: {} });
    navigate(`/jobs/${job.id}`);
  };

  const pill = FORMAT_PILL[dataset.format] ?? { bg: "#F9FAFB", text: "#374151", border: "#E8E8F0" };

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: "profile",  label: "Profile",  icon: BarChart2 },
    { key: "versions", label: "Versions", icon: GitBranch },
    { key: "jobs",     label: "Jobs",     icon: Briefcase },
  ];

  return (
    <AppLayout title={dataset.name}>
      <div className="space-y-5 animate-fade-in">

        {/* Back */}
        <Link to="/datasets" className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
          style={{ color: "#6B7280" }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#4338CA"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#6B7280"; }}>
          <ArrowLeft size={14} /> Back to Datasets
        </Link>

        {/* Header */}
        <div className="card p-6">
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: "#EDE9FE", border: "1px solid #C4B5FD" }}>
                <Database size={22} style={{ color: "#5B21B6" }} />
              </div>
              <div>
                <h2 className="text-xl font-extrabold tracking-tight" style={{ color: "#0F0F1A", letterSpacing: "-0.03em" }}>
                  {dataset.name}
                </h2>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="badge uppercase" style={{ background: pill.bg, color: pill.text, border: `1px solid ${pill.border}` }}>
                    {dataset.format}
                  </span>
                  {dataset.row_count && (
                    <span className="text-xs font-mono font-medium" style={{ color: "#6B7280" }}>
                      {dataset.row_count.toLocaleString()} rows
                    </span>
                  )}
                  {dataset.column_count && (
                    <span className="text-xs font-mono font-medium" style={{ color: "#6B7280" }}>
                      {dataset.column_count} columns
                    </span>
                  )}
                  <span className="flex items-center gap-1 text-xs" style={{ color: "#9CA3AF" }}>
                    <Calendar size={11} />
                    {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
            </div>
            <button onClick={handleRunPipeline} disabled={submitJob.isPending} className="btn-primary">
              {submitJob.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              Run Pipeline
            </button>
          </div>
          <NLQueryBar datasetId={id} />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-xl w-fit" style={{ background: "#F1F5F9", border: "1px solid #E8E8F0" }}>
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-150"
              style={tab === key
                ? { background: "#FFFFFF", color: "#0F0F1A", boxShadow: "0 1px 3px rgb(0 0 0 / 0.08)", border: "1px solid #E8E8F0" }
                : { color: "#6B7280", border: "1px solid transparent" }
              }>
              <Icon size={14} />{label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "profile" && (
          <div className="card p-10 text-center">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: "#F9FAFB", border: "1px solid #E8E8F0" }}>
              <BarChart2 size={22} style={{ color: "#9CA3AF" }} />
            </div>
            <p className="font-semibold" style={{ color: "#0F0F1A" }}>No profile yet</p>
            <p className="text-sm mt-1" style={{ color: "#6B7280" }}>Run the pipeline to generate a data profile.</p>
            <button onClick={handleRunPipeline} disabled={submitJob.isPending} className="btn-primary mt-4 mx-auto">
              <Play size={14} /> Run Pipeline
            </button>
          </div>
        )}

        {tab === "versions" && (
          <div className="card overflow-hidden">
            {!versions || versions.length === 0 ? (
              <div className="p-10 text-center">
                <p className="text-sm" style={{ color: "#6B7280" }}>No versions yet. Run the pipeline to create one.</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr>
                    <th className="table-header">Version</th>
                    <th className="table-header text-right">Quality Score</th>
                    <th className="table-header">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((v: any) => (
                    <tr key={v.id} className="table-row">
                      <td className="table-cell font-mono font-bold" style={{ color: "#0F0F1A" }}>v{v.version_number}</td>
                      <td className="table-cell text-right">
                        {v.quality_score != null ? (
                          <span className="font-bold font-mono" style={{
                            color: v.quality_score >= 70 ? "#059669" : v.quality_score >= 50 ? "#D97706" : "#DC2626"
                          }}>
                            {parseFloat(v.quality_score).toFixed(1)}%
                          </span>
                        ) : "—"}
                      </td>
                      <td className="table-cell text-xs" style={{ color: "#9CA3AF" }}>
                        {formatDistanceToNow(new Date(v.created_at), { addSuffix: true })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {tab === "jobs" && (
          <div className="card p-10 text-center">
            <p className="text-sm" style={{ color: "#6B7280" }}>Job history coming soon.</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
