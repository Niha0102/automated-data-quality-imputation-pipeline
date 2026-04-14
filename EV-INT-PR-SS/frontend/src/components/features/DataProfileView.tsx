import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface ColumnProfile {
  name: string;
  dtype: string;
  missing_pct: number;
  cardinality: number;
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
  top_values?: { value: string; count: number; pct: number }[];
}

interface Props {
  profile: { columns: ColumnProfile[]; row_count: number; column_count: number };
  semanticTypes?: Record<string, { semantic_type: string; confidence: number }>;
}

export function DataProfileView({ profile, semanticTypes }: Props) {
  const missingData = profile.columns.map((c) => ({
    name: c.name.length > 12 ? c.name.slice(0, 12) + "…" : c.name,
    missing: parseFloat(c.missing_pct.toFixed(1)),
  }));

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl p-4" style={{ background: "#F9FAFB", border: "1px solid #E8E8F0" }}>
          <p className="label mb-1">Total Rows</p>
          <p className="text-2xl font-extrabold tracking-tight" style={{ color: "#0F0F1A", letterSpacing: "-0.04em" }}>
            {profile.row_count.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl p-4" style={{ background: "#F9FAFB", border: "1px solid #E8E8F0" }}>
          <p className="label mb-1">Total Columns</p>
          <p className="text-2xl font-extrabold tracking-tight" style={{ color: "#0F0F1A", letterSpacing: "-0.04em" }}>
            {profile.column_count}
          </p>
        </div>
      </div>

      {/* Missing values chart */}
      <div className="rounded-xl p-5" style={{ background: "#F9FAFB", border: "1px solid #E8E8F0" }}>
        <h3 className="text-sm font-bold mb-4" style={{ color: "#0F0F1A" }}>Missing Values by Column (%)</h3>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={missingData} margin={{ top: 0, right: 0, bottom: 20, left: 0 }}>
            <XAxis dataKey="name" tick={{ fill: "#9CA3AF", fontSize: 11 }} angle={-30} textAnchor="end" />
            <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} domain={[0, 100]} />
            <Tooltip
              contentStyle={{
                background: "#FFFFFF",
                border: "1px solid #E8E8F0",
                borderRadius: 8,
                boxShadow: "0 4px 16px rgb(0 0 0 / 0.08)",
                color: "#0F0F1A",
                fontSize: 12,
              }}
              labelStyle={{ color: "#0F0F1A", fontWeight: 600 }}
              itemStyle={{ color: "#6B7280" }}
            />
            <Bar dataKey="missing" radius={[4, 4, 0, 0]}>
              {missingData.map((entry, i) => (
                <Cell key={i} fill={entry.missing > 50 ? "#DC2626" : entry.missing > 20 ? "#D97706" : "#4338CA"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Column table */}
      <div className="rounded-xl overflow-hidden" style={{ border: "1px solid #E8E8F0" }}>
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="table-header">Column</th>
              <th className="table-header">Type</th>
              <th className="table-header">Semantic</th>
              <th className="table-header text-right">Missing</th>
              <th className="table-header text-right">Cardinality</th>
              <th className="table-header text-right">Mean</th>
            </tr>
          </thead>
          <tbody>
            {profile.columns.map((col) => {
              const sem = semanticTypes?.[col.name];
              return (
                <tr key={col.name} className="table-row">
                  <td className="table-cell font-mono text-xs font-semibold" style={{ color: "#0F0F1A" }}>{col.name}</td>
                  <td className="table-cell">
                    <span className="badge" style={{ background: "#EFF6FF", color: "#1D4ED8", border: "1px solid #BFDBFE" }}>
                      {col.dtype}
                    </span>
                  </td>
                  <td className="table-cell">
                    {sem && (
                      <span className="text-xs" style={{ color: "#6B7280" }}>
                        {sem.semantic_type}{" "}
                        <span className="font-mono font-semibold" style={{ color: "#4338CA" }}>
                          ({(sem.confidence * 100).toFixed(0)}%)
                        </span>
                      </span>
                    )}
                  </td>
                  <td className="table-cell text-right">
                    <span className="font-mono text-xs font-semibold"
                      style={{ color: col.missing_pct > 20 ? "#DC2626" : "#6B7280" }}>
                      {col.missing_pct.toFixed(1)}%
                    </span>
                  </td>
                  <td className="table-cell text-right font-mono text-xs" style={{ color: "#6B7280" }}>
                    {col.cardinality}
                  </td>
                  <td className="table-cell text-right font-mono text-xs" style={{ color: "#6B7280" }}>
                    {col.mean != null ? col.mean.toFixed(2) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
