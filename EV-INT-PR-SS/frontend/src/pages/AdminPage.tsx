import { AppLayout } from "@/components/layout/AppLayout";
import { useAdminUsers } from "@/api/hooks";
import { Loader2, Shield, UserCheck, UserX, Users } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function AdminPage() {
  const { data, isLoading } = useAdminUsers();
  const users = data?.items ?? [];

  return (
    <AppLayout title="Admin Panel">
      <div className="space-y-5 animate-fade-in">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">User Management</h1>
            <p className="text-sm mt-0.5" style={{ color: "#6B7280" }}>Manage user accounts and permissions</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge" style={{ background: "#EDE9FE", color: "#5B21B6", border: "1px solid #C4B5FD" }}>
              <Shield size={10} /> Admin Access
            </span>
            <button className="btn-primary">
              <Users size={14} /> Invite User
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Total Users", value: data?.total ?? 0,                                    bg: "#EDE9FE", border: "#C4B5FD", color: "#5B21B6" },
            { label: "Active",      value: users.filter((u: any) => u.is_active).length,        bg: "#DCFCE7", border: "#BBF7D0", color: "#059669" },
            { label: "Admins",      value: users.filter((u: any) => u.role === "admin").length, bg: "#EFF6FF", border: "#BFDBFE", color: "#2563EB" },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                style={{ background: s.bg, border: `1px solid ${s.border}` }}>
                <span className="text-sm font-black" style={{ color: s.color }}>{s.value}</span>
              </div>
              <p className="text-2xl font-extrabold tracking-tight" style={{ color: "#0F0F1A", letterSpacing: "-0.04em" }}>{s.value}</p>
              <p className="text-xs font-medium mt-1" style={{ color: "#6B7280" }}>{s.label}</p>
            </div>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="animate-spin" style={{ color: "#4338CA" }} />
          </div>
        ) : users.length === 0 ? (
          <div className="card p-16 text-center">
            <div className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4"
              style={{ background: "#F9FAFB", border: "1px solid #E8E8F0" }}>
              <Users size={28} style={{ color: "#9CA3AF" }} />
            </div>
            <p className="font-bold text-lg" style={{ color: "#0F0F1A" }}>No users found</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="table-header">User</th>
                  <th className="table-header">Role</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user: any) => (
                  <tr key={user.id} className="table-row">
                    <td className="table-cell">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ background: "linear-gradient(135deg, #4338CA, #2563EB)" }}>
                          <span className="text-white text-xs font-bold">{user.email[0].toUpperCase()}</span>
                        </div>
                        <span className="font-semibold" style={{ color: "#0F0F1A" }}>{user.email}</span>
                      </div>
                    </td>
                    <td className="table-cell">
                      <span className="badge" style={
                        user.role === "admin"
                          ? { background: "#EDE9FE", color: "#5B21B6", border: "1px solid #C4B5FD" }
                          : { background: "#F9FAFB", color: "#6B7280", border: "1px solid #E8E8F0" }
                      }>
                        {user.role === "admin" && <Shield size={10} />}
                        {user.role}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="badge gap-1" style={
                        user.is_active
                          ? { background: "#DCFCE7", color: "#166534", border: "1px solid #BBF7D0" }
                          : { background: "#FEF2F2", color: "#991B1B", border: "1px solid #FECACA" }
                      }>
                        {user.is_active ? <UserCheck size={11} /> : <UserX size={11} />}
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="table-cell text-xs" style={{ color: "#9CA3AF" }}>
                      {formatDistanceToNow(new Date(user.created_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
