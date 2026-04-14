import { AppLayout } from "@/components/layout/AppLayout";
import { useMe } from "@/api/hooks";
import { User, Settings, Sliders, Bell, Shield } from "lucide-react";

function SettingRow({ label, value, badge }: { label: string; value: string; badge?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3.5 px-4 rounded-lg transition-colors"
      style={{ border: "1px solid #EBEBF5" }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "#F9FAFB"; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
      <div>
        <p className="label mb-0.5">{label}</p>
        <p className="text-sm font-medium" style={{ color: "#0F0F1A" }}>{value}</p>
      </div>
      {badge && <div>{badge}</div>}
    </div>
  );
}

function SettingSection({ icon, iconBg, iconBorder, iconColor, title, children }: {
  icon: React.ReactNode; iconBg: string; iconBorder: string; iconColor: string; title: string; children: React.ReactNode;
}) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ background: iconBg, border: `1px solid ${iconBorder}` }}>
          <div style={{ color: iconColor }}>{icon}</div>
        </div>
        <h3 className="section-title">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function ComingSoon({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-between py-3.5 px-4 rounded-lg"
      style={{ background: "#F9FAFB", border: "1px solid #EBEBF5" }}>
      <p className="text-sm" style={{ color: "#9CA3AF" }}>{text}</p>
      <span className="badge" style={{ background: "#F5F3FF", color: "#7C3AED", border: "1px solid #DDD6FE" }}>
        Coming soon
      </span>
    </div>
  );
}

export default function SettingsPage() {
  const { data: user } = useMe();

  return (
    <AppLayout title="Settings">
      <div className="max-w-2xl space-y-5 animate-fade-in">

        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-sm mt-0.5" style={{ color: "#6B7280" }}>Manage your account and platform preferences</p>
        </div>

        <SettingSection icon={<User size={16} />} iconBg="#EDE9FE" iconBorder="#C4B5FD" iconColor="#5B21B6" title="Account">
          <div className="space-y-2">
            <SettingRow label="Email Address" value={user?.email ?? "—"} />
            <SettingRow
              label="Role"
              value={user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "—"}
              badge={
                <span className="badge" style={
                  user?.role === "admin"
                    ? { background: "#EDE9FE", color: "#5B21B6", border: "1px solid #C4B5FD" }
                    : { background: "#F9FAFB", color: "#6B7280", border: "1px solid #E8E8F0" }
                }>
                  {user?.role === "admin" && <Shield size={10} />}
                  {user?.role}
                </span>
              }
            />
            <SettingRow label="Account Status" value="Active"
              badge={
                <span className="badge" style={{ background: "#DCFCE7", color: "#166534", border: "1px solid #BBF7D0" }}>
                  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "#059669" }} />
                  Active
                </span>
              }
            />
          </div>
        </SettingSection>

        <SettingSection icon={<Sliders size={16} />} iconBg="#EFF6FF" iconBorder="#BFDBFE" iconColor="#2563EB" title="Pipeline Defaults">
          <div className="space-y-2">
            <ComingSoon text="Imputation strategy (mean, median, mode)" />
            <ComingSoon text="Outlier detection threshold" />
            <ComingSoon text="Drift detection sensitivity" />
          </div>
        </SettingSection>

        <SettingSection icon={<Bell size={16} />} iconBg="#FFFBEB" iconBorder="#FDE68A" iconColor="#D97706" title="Notifications">
          <div className="space-y-2">
            <ComingSoon text="Email alerts for quality score drops" />
            <ComingSoon text="Slack integration for pipeline failures" />
            <ComingSoon text="Weekly quality digest reports" />
          </div>
        </SettingSection>

        <SettingSection icon={<Settings size={16} />} iconBg="#F5F3FF" iconBorder="#DDD6FE" iconColor="#7C3AED" title="Preferences">
          <div className="space-y-2">
            <ComingSoon text="Theme and display preferences" />
            <ComingSoon text="Default date format and timezone" />
            <ComingSoon text="Data export format preferences" />
          </div>
        </SettingSection>

        <div className="card p-6" style={{ border: "1px solid #FECACA" }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}>
              <Shield size={16} style={{ color: "#DC2626" }} />
            </div>
            <h3 className="section-title" style={{ color: "#DC2626" }}>Danger Zone</h3>
          </div>
          <div className="flex items-center justify-between p-4 rounded-lg"
            style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}>
            <div>
              <p className="text-sm font-semibold" style={{ color: "#0F0F1A" }}>Delete Account</p>
              <p className="text-xs mt-0.5" style={{ color: "#6B7280" }}>Permanently delete your account and all data</p>
            </div>
            <button className="btn-danger text-xs px-3 py-2">Delete Account</button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
