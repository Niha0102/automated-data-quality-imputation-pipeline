import { AlertTriangle, CheckCircle2, TrendingDown, Activity, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useAlerts, useAcknowledgeAlert } from "@/api/hooks";

const TYPE_CONFIG: Record<string, { icon: any; bg: string; text: string; border: string; dot: string }> = {
  quality_drop:   { icon: TrendingDown,  bg: "#FEF2F2", text: "#DC2626", border: "#FECACA", dot: "#DC2626" },
  drift_detected: { icon: Activity,      bg: "#FFFBEB", text: "#D97706", border: "#FDE68A", dot: "#D97706" },
  default:        { icon: AlertTriangle, bg: "#FFF7ED", text: "#EA580C", border: "#FED7AA", dot: "#EA580C" },
};

export function AlertsPanel() {
  const { data, isLoading } = useAlerts();
  const acknowledge = useAcknowledgeAlert();
  const alerts = (data?.items ?? []).filter((a: any) => !a.is_resolved);

  if (isLoading) return (
    <div className="flex items-center gap-3 text-sm py-6" style={{ color: "#9CA3AF" }}>
      <div className="w-4 h-4 border-2 rounded-full animate-spin" style={{ borderColor: "#E8E8F0", borderTopColor: "#4338CA" }} />
      Loading alerts...
    </div>
  );

  if (alerts.length === 0) return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <div className="w-14 h-14 rounded-xl flex items-center justify-center mb-4"
        style={{ background: "#DCFCE7", border: "1px solid #BBF7D0" }}>
        <CheckCircle2 size={24} style={{ color: "#059669" }} />
      </div>
      <p className="font-semibold text-sm" style={{ color: "#0F0F1A" }}>All clear</p>
      <p className="text-xs mt-1" style={{ color: "#6B7280" }}>No active alerts at this time</p>
    </div>
  );

  return (
    <div className="space-y-2">
      {alerts.map((alert: any) => {
        const cfg = TYPE_CONFIG[alert.type] ?? TYPE_CONFIG.default;
        const Icon = cfg.icon;
        return (
          <div key={alert.id}
            className="flex items-start gap-3 p-4 rounded-xl transition-all duration-150"
            style={{ background: cfg.bg, border: `1px solid ${cfg.border}` }}>
            <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "#FFFFFF", border: `1px solid ${cfg.border}` }}>
              <Icon size={15} style={{ color: cfg.text }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: cfg.dot }} />
                <p className="text-sm font-semibold" style={{ color: "#0F0F1A" }}>{alert.message}</p>
              </div>
              <p className="text-xs" style={{ color: "#6B7280" }}>
                {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
              </p>
            </div>
            <button
              onClick={() => acknowledge.mutate(alert.id)}
              disabled={acknowledge.isPending}
              className="p-1.5 rounded-lg transition-colors flex-shrink-0"
              style={{ color: "#9CA3AF" }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#0F0F1A"; (e.currentTarget as HTMLElement).style.background = "#FFFFFF"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#9CA3AF"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
              title="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
