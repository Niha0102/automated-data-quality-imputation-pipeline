import { useState } from "react";
import { Sparkles, Send, Loader2 } from "lucide-react";
import { useSubmitJob } from "@/api/hooks";
import { useNavigate } from "react-router-dom";

interface Props {
  datasetId?: string;
}

export function NLQueryBar({ datasetId }: Props) {
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const submitJob = useSubmitJob();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !datasetId) return;
    setPreview(`Interpreting: "${query}" → Running full pipeline with NL configuration`);
    try {
      const job = await submitJob.mutateAsync({
        dataset_id: datasetId,
        nl_query: query,
        pipeline_config: {},
      });
      setQuery("");
      setPreview(null);
      navigate(`/jobs/${job.id}`);
    } catch {
      setPreview("Failed to submit job. Please try again.");
    }
  };

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <Sparkles size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "#7C3AED" }} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='Ask AI: "Clean this dataset and prepare for ML training"'
            className="input pl-10"
            style={{ background: "#F9FAFB" }}
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || !datasetId || submitJob.isPending}
          className="btn-primary px-4"
        >
          {submitJob.isPending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          Run
        </button>
      </form>
      {preview && (
        <p className="text-xs px-3 py-2 rounded-lg" style={{ background: "#F5F3FF", color: "#5B21B6", border: "1px solid #DDD6FE" }}>
          {preview}
        </p>
      )}
    </div>
  );
}
