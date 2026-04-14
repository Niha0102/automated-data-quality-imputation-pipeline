import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";

interface Props {
  score: number;
  label?: string;
  size?: "sm" | "md" | "lg";
}

function getColor(score: number): string {
  if (score >= 70) return "#059669";
  if (score >= 50) return "#D97706";
  return "#DC2626";
}

function getGradientId(score: number): string {
  if (score >= 70) return "gaugeGreen";
  if (score >= 50) return "gaugeAmber";
  return "gaugeRed";
}

function getLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Fair";
  return "Poor";
}

function getBg(score: number): string {
  if (score >= 70) return "#DCFCE7";
  if (score >= 50) return "#FEF3C7";
  return "#FEE2E2";
}

export function QualityScoreGauge({ score, label, size = "md" }: Props) {
  const color = getColor(score);
  const bg = getBg(score);
  const gradId = getGradientId(score);
  const data = [{ value: Math.max(score, 0.5), fill: `url(#${gradId})` }];
  const sizeMap = { sm: 80, md: 130, lg: 170 };
  const dim = sizeMap[size];
  const fontSize = size === "sm" ? 14 : size === "md" ? 22 : 30;

  return (
    <div className="flex flex-col items-center gap-2" data-testid="quality-gauge">
      <div style={{ width: dim, height: dim }} className="relative">
        <svg width="0" height="0" style={{ position: "absolute" }}>
          <defs>
            <linearGradient id="gaugeGreen" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
            <linearGradient id="gaugeAmber" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FBBF24" />
              <stop offset="100%" stopColor="#D97706" />
            </linearGradient>
            <linearGradient id="gaugeRed" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#F87171" />
              <stop offset="100%" stopColor="#DC2626" />
            </linearGradient>
          </defs>
        </svg>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="62%" outerRadius="88%"
            startAngle={220} endAngle={-40}
            data={data}
          >
            <RadialBar
              dataKey="value"
              cornerRadius={6}
              background={{ fill: "#F0F0F8" }}
              max={100}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-extrabold tabular-nums" style={{
            color: "#0F0F1A",
            fontSize,
            letterSpacing: "-0.04em",
            lineHeight: 1,
          }}>
            {score.toFixed(0)}
          </span>
          <span className="text-xs font-semibold mt-0.5" style={{ color: "#9CA3AF" }}>/ 100</span>
          {size !== "sm" && (
            <span className="text-xs font-bold px-2 py-0.5 mt-1.5"
              style={{ background: bg, color, borderRadius: "4px" }}>
              {getLabel(score)}
            </span>
          )}
        </div>
      </div>
      {label && (
        <p className="text-xs text-center font-semibold" style={{ color: "#6B7280" }}>{label}</p>
      )}
    </div>
  );
}
