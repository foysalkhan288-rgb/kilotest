import axios from "axios";
import { apiClient } from "./client";

export interface Availability {
  timezone?: string;
  days?: Record<string, number[]>;
  slot_minutes?: number;
}

export interface CalendarItem {
  id: string;
  workspace_id: string;
  name: string;
  public_slug: string | null;
  availability: Availability | null;
}

export interface PublicCalendar {
  name: string;
  availability: Availability | null;
  public_slug: string;
}

export interface CreateCalendarPayload {
  name: string;
  availability?: Availability | null;
}

export type UpdateCalendarPayload = Partial<CreateCalendarPayload>;

export interface BookingPayload {
  name: string;
  email: string;
  phone?: string | null;
  start: string;
}

export interface BookingResult {
  ok: boolean;
  appointment_id: string;
}

const PUBLIC_BASE = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/api/v1`;
const publicClient = axios.create({
  baseURL: PUBLIC_BASE,
  headers: { "Content-Type": "application/json" },
});

export const listCalendars = async (): Promise<CalendarItem[]> => {
  const { data } = await apiClient.get<CalendarItem[]>("/calendars");
  return data;
};

export const createCalendar = async (
  payload: CreateCalendarPayload
): Promise<CalendarItem> => {
  const { data } = await apiClient.post<CalendarItem>("/calendars", payload);
  return data;
};

export const updateCalendar = async (
  id: string,
  payload: UpdateCalendarPayload
): Promise<CalendarItem> => {
  const { data } = await apiClient.patch<CalendarItem>(
    `/calendars/${id}`,
    payload
  );
  return data;
};

export const deleteCalendar = async (id: string): Promise<void> => {
  await apiClient.delete(`/calendars/${id}`);
};

export const getPublicCalendar = async (slug: string): Promise<PublicCalendar> => {
  const { data } = await publicClient.get<PublicCalendar>(`/book/${slug}`);
  return data;
};

export const bookAppointment = async (
  slug: string,
  payload: BookingPayload
): Promise<BookingResult> => {
  const { data } = await publicClient.post<BookingResult>(
    `/book/${slug}`,
    payload
  );
  return data;
};

export const publicBookingUrl = (slug: string): string =>
  `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/book/${slug}`;
