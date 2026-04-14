import { create } from "zustand";

interface JobProgress {
  jobId: string;
  progress: number;
  status: string;
}

interface JobState {
  jobs: Record<string, JobProgress>;
  updateJob: (jobId: string, data: Partial<JobProgress>) => void;
}

export const useJobStore = create<JobState>((set) => ({
  jobs: {},
  updateJob: (jobId, data) =>
    set((state) => ({
      jobs: {
        ...state.jobs,
        [jobId]: { ...{ jobId, progress: 0, status: "PENDING" }, ...state.jobs[jobId], ...data },
      },
    })),
}));
