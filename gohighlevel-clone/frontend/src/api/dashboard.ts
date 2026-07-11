import { apiClient } from "./client";

export interface ActivityItem {
  id: string;
  type: string | null;
  message: string | null;
  created_at: string | null;
}

export interface DashboardSummary {
  total_contacts: number;
  open_pipeline_value: number;
  appointments_today: number;
  recent_activity: ActivityItem[];
}

export const getDashboard = async (): Promise<DashboardSummary> => {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
  return data;
};
