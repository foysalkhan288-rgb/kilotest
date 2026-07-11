import { apiClient } from "./client";

export type AppointmentStatus =
  | "booked"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export const APPOINTMENT_STATUSES: AppointmentStatus[] = [
  "booked",
  "confirmed",
  "completed",
  "cancelled",
  "no_show",
];

export interface ContactLite {
  id: string;
  firstname: string | null;
  lastname: string | null;
  email: string | null;
}

export interface AppointmentItem {
  id: string;
  workspace_id: string;
  contact_id: string;
  start: string | null;
  end: string | null;
  status: AppointmentStatus | null;
  created_at: string;
  contact?: ContactLite | null;
}

export const listAppointments = async (
  date?: string
): Promise<AppointmentItem[]> => {
  const { data } = await apiClient.get<AppointmentItem[]>("/appointments", {
    params: date ? { date } : {},
  });
  return data;
};

export const updateAppointment = async (
  id: string,
  patch: { status: AppointmentStatus }
): Promise<AppointmentItem> => {
  const { data } = await apiClient.patch<AppointmentItem>(
    `/appointments/${id}`,
    patch
  );
  return data;
};
