import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

// ── Auth ──────────────────────────────────────────────────────────────────────
export const useLogin = () =>
  useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      apiClient.post("/auth/login", data).then((r) => r.data),
  });

export const useMe = () =>
  useQuery({ queryKey: ["me"], queryFn: () => apiClient.get("/auth/me").then((r) => r.data) });

// ── Datasets ──────────────────────────────────────────────────────────────────
export const useDatasets = (skip = 0, limit = 20) =>
  useQuery({
    queryKey: ["datasets", skip, limit],
    queryFn: () => apiClient.get(`/datasets?skip=${skip}&limit=${limit}`).then((r) => r.data),
  });

export const useDataset = (id: string) =>
  useQuery({
    queryKey: ["dataset", id],
    queryFn: () => apiClient.get(`/datasets/${id}`).then((r) => r.data),
    enabled: !!id,
  });

export const useDatasetVersions = (id: string) =>
  useQuery({
    queryKey: ["dataset-versions", id],
    queryFn: () => apiClient.get(`/datasets/${id}/versions`).then((r) => r.data),
    enabled: !!id,
  });

export const useUploadDataset = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return apiClient.post("/datasets", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
};

export const useDeleteDataset = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/datasets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
};

// ── Jobs ──────────────────────────────────────────────────────────────────────
export const useJobs = (skip = 0, limit = 20) =>
  useQuery({
    queryKey: ["jobs", skip, limit],
    queryFn: () => apiClient.get(`/jobs?skip=${skip}&limit=${limit}`).then((r) => r.data),
  });

export const useJob = (id: string) =>
  useQuery({
    queryKey: ["job", id],
    queryFn: () => apiClient.get(`/jobs/${id}`).then((r) => r.data),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "RUNNING" || status === "PENDING" ? 3000 : false;
    },
  });

export const useSubmitJob = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { dataset_id: string; pipeline_config?: object; nl_query?: string }) =>
      apiClient.post("/jobs", data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
};

// ── Alerts ────────────────────────────────────────────────────────────────────
export const useAlerts = () =>
  useQuery({
    queryKey: ["alerts"],
    queryFn: () => apiClient.get("/alerts").then((r) => r.data),
    refetchInterval: 30_000,
  });

export const useAcknowledgeAlert = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.patch(`/alerts/${id}/acknowledge`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
};

// ── Reports ───────────────────────────────────────────────────────────────────
export const useReport = (jobId: string) =>
  useQuery({
    queryKey: ["report", jobId],
    queryFn: () => apiClient.get(`/reports/${jobId}`).then((r) => r.data),
    enabled: !!jobId,
  });

// ── Admin ─────────────────────────────────────────────────────────────────────
export const useAdminUsers = () =>
  useQuery({
    queryKey: ["admin-users"],
    queryFn: () => apiClient.get("/admin/users").then((r) => r.data),
  });
