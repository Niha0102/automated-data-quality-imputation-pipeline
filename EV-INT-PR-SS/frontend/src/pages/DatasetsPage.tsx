import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Link } from "react-router-dom";
import { Upload, Database, Trash2, Loader2, X, CheckCircle2, FileText, ArrowUpRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { AppLayout } from "@/components/layout/AppLayout";
import { useDatasets, useUploadDataset, useDeleteDataset } from "@/api/hooks";

const ACCEPTED = {
  "text/csv": [".csv"],
  "application/json": [".json"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
};

const FORMAT_PILL: Record<string, { bg: string; text: string; border: string }> = {
  csv:  { bg: "#EFF6FF", text: "#1D4ED8", border: "#BFDBFE" },
  json: { bg: "#F5F3FF", text: "#6D28D9", border: "#DDD6FE" },
  xlsx: { bg: "#FFFBEB", text: "#92400E", border: "#FDE68A" },
};

function UploadDialog({ onClose }: { onClose: () => void }) {
  const upload = useUploadDataset();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  const onDrop = useCallback((accepted: File[], rejected: any[]) => {
    if (rejected.length > 0) { setError("Only CSV, JSON, and XLSX files are supported."); return; }
    setError(""); setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: ACCEPTED, maxFiles: 1, maxSize: 2 * 1024 * 1024 * 1024,
  });

  const handleUpload = async () => {
    if (!file) return;
    try { await upload.mutateAsync(file); onClose(); }
    catch (e: any) { setError(e.response?.data?.detail ?? "Upload failed. Please try again."); }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: "rgba(10,22,40,0.6)", backdropFilter: "blur(4px)" }}>
      <div className="w-full max-w-md animate-scale-in"
        style={{ background: "#FFFFFF", border: "1px solid #E5E5EF", borderRadius: "4px", boxShadow: "0 25px 80px -10px rgba(0,0,0,0.2)" }}>

        <div className="flex items-center justify-between px-6 py-5" style={{ borderBottom: "1px solid #E5E5EF" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 flex items-center justify-center"
              style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "4px" }}>
              <Upload size={16} style={{ color: "#2563EB" }} />
            </div>
            <h2 className="font-bold text-base" style={{ color: "#1A1A2E" }}>Upload Dataset</h2>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={17} /></button>
        </div>

        <div className="p-6 space-y-4">
          <div {...getRootProps()} className="p-10 text-center cursor-pointer transition-all duration-200"
            style={{
              border: `2px dashed ${isDragActive ? "#2563EB" : "#D1D1E0"}`,
              background: isDragActive ? "#EFF6FF" : "#F8F8FC",
              borderRadius: "4px",
            }}>
            <input {...getInputProps()} />
            {file ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 flex items-center justify-center"
                  style={{ background: "#DCFCE7", border: "1px solid #BBF7D0", borderRadius: "4px" }}>
                  <CheckCircle2 size={26} style={{ color: "#16A34A" }} />
                </div>
                <p className="font-semibold text-sm" style={{ color: "#1A1A2E" }}>{file.name}</p>
                <p className="text-xs" style={{ color: "#6B7280" }}>{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 flex items-center justify-center"
                  style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "4px" }}>
                  <Upload size={24} style={{ color: "#2563EB" }} />
                </div>
                <p className="font-semibold text-sm" style={{ color: "#1A1A2E" }}>
                  {isDragActive ? "Drop it here!" : "Drop file or click to browse"}
                </p>
                <p className="text-xs" style={{ color: "#9CA3AF" }}>CSV, JSON, XLSX · Max 2 GB</p>
              </div>
            )}
          </div>
          {error && (
            <div className="p-3 rounded-lg" style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}>
              <p className="text-sm" style={{ color: "#DC2626" }}>{error}</p>
            </div>
          )}
        </div>

        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleUpload} disabled={!file || upload.isPending} className="btn-primary flex-1">
            {upload.isPending && <Loader2 size={14} className="animate-spin" />}
            {upload.isPending ? "Uploading..." : "Upload Dataset"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DatasetsPage() {
  const [showUpload, setShowUpload] = useState(false);
  const { data, isLoading } = useDatasets();
  const deleteDataset = useDeleteDataset();
  const datasets = data?.items ?? [];

  return (
    <AppLayout title="Datasets">
      <div className="space-y-5 animate-fade-in">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{data?.total ?? 0} Datasets</h1>
            <p className="text-sm mt-0.5" style={{ color: "#64748B" }}>Upload and manage your data files for quality analysis</p>
          </div>
          <button onClick={() => setShowUpload(true)} className="btn-primary">
            <Upload size={14} /> Upload Dataset
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="animate-spin" style={{ color: "#4338CA" }} />
          </div>
        ) : datasets.length === 0 ? (
          <div className="card p-16 text-center">
            <div className="w-16 h-16 flex items-center justify-center mx-auto mb-4"
              style={{ background: "#F4F4F6", border: "1px solid #E5E5EF", borderRadius: "4px" }}>
              <Database size={28} style={{ color: "#9CA3AF" }} />
            </div>
            <p className="font-bold text-lg" style={{ color: "#1A1A2E" }}>No datasets yet</p>
            <p className="text-sm mt-1.5" style={{ color: "#6B7280" }}>Upload a CSV, JSON, or XLSX file to get started</p>
            <button onClick={() => setShowUpload(true)} className="btn-primary mt-5 mx-auto">
              <Upload size={14} /> Upload your first dataset
            </button>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Format</th>
                  <th className="table-header text-right">Rows</th>
                  <th className="table-header text-right">Columns</th>
                  <th className="table-header">Uploaded</th>
                  <th className="table-header w-10"></th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((ds: any) => {
                  const pill = FORMAT_PILL[ds.format] ?? { bg: "#F1F5F9", text: "#475569", border: "#E2E8F0" };
                  return (
                    <tr key={ds.id} className="table-row">
                      <td className="table-cell">
                        <Link to={`/datasets/${ds.id}`} className="flex items-center gap-3 group">
                          <div className="w-8 h-8 flex items-center justify-center flex-shrink-0"
                            style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "4px" }}>
                            <FileText size={13} style={{ color: "#2563EB" }} />
                          </div>
                          <span className="font-semibold" style={{ color: "#1A1A2E" }}>{ds.name}</span>
                        </Link>
                      </td>
                      <td className="table-cell">
                        <span className="badge uppercase" style={{ background: pill.bg, color: pill.text, border: `1px solid ${pill.border}` }}>
                          {ds.format}
                        </span>
                      </td>
                      <td className="table-cell text-right font-mono text-xs" style={{ color: "#64748B" }}>
                        {ds.row_count?.toLocaleString() ?? "—"}
                      </td>
                      <td className="table-cell text-right font-mono text-xs" style={{ color: "#64748B" }}>
                        {ds.column_count?.toLocaleString() ?? "—"}
                      </td>
                      <td className="table-cell text-xs" style={{ color: "#94A3B8" }}>
                        {formatDistanceToNow(new Date(ds.created_at), { addSuffix: true })}
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center gap-1">
                          <Link to={`/datasets/${ds.id}`} className="p-1.5 rounded transition-colors"
                            style={{ color: "#9CA3AF" }}
                            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#2563EB"; (e.currentTarget as HTMLElement).style.background = "#EFF6FF"; }}
                            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#9CA3AF"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                            <ArrowUpRight size={14} />
                          </Link>
                          <button onClick={() => deleteDataset.mutate(ds.id)}
                            className="p-1.5 rounded transition-colors"
                            style={{ color: "#9CA3AF" }}
                            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#DC2626"; (e.currentTarget as HTMLElement).style.background = "#FEF2F2"; }}
                            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#9CA3AF"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {showUpload && <UploadDialog onClose={() => setShowUpload(false)} />}
    </AppLayout>
  );
}
