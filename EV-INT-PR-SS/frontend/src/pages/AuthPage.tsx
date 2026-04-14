import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { Loader2, Database } from "lucide-react";
import { useLogin } from "@/api/hooks";
import { useAuthStore } from "@/store/authStore";
import { apiClient } from "@/api/client";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
});
type FormData = z.infer<typeof schema>;

export default function AuthPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const loginMutation = useLogin();

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      const res = await loginMutation.mutateAsync(data);
      // Fetch user info
      const meRes = await apiClient.get("/auth/me", {
        headers: { Authorization: `Bearer ${res.access_token}` },
      });
      login(res.access_token, meRes.data);
      navigate("/dashboard");
    } catch {
      // error shown via mutation state
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-accent flex items-center justify-center mb-4">
            <Database size={28} className="text-white" />
          </div>
          <h1 className="text-brand-text text-2xl font-bold">DataQuality AI</h1>
          <p className="text-brand-text-muted text-sm mt-1">Sign in to your account</p>
        </div>

        {/* Form */}
        <div className="bg-brand-surface border border-brand-border rounded-xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-brand-text text-sm font-medium mb-1.5">Email</label>
              <input
                {...register("email")}
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                className="w-full px-4 py-2.5 bg-brand-bg border border-brand-border rounded-lg text-brand-text text-sm placeholder:text-brand-text-muted focus:outline-none focus:border-brand-accent transition-colors"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-brand-text text-sm font-medium mb-1.5">Password</label>
              <input
                {...register("password")}
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full px-4 py-2.5 bg-brand-bg border border-brand-border rounded-lg text-brand-text text-sm placeholder:text-brand-text-muted focus:outline-none focus:border-brand-accent transition-colors"
              />
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            {loginMutation.isError && (
              <p className="text-red-400 text-sm text-center">Invalid credentials. Please try again.</p>
            )}

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="w-full py-2.5 bg-brand-accent hover:bg-brand-accent-hover disabled:opacity-60 text-white rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2"
            >
              {loginMutation.isPending && <Loader2 size={16} className="animate-spin" />}
              Sign In
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
