import { apiClient } from "./client";

export interface Contact {
  id: string;
  workspace_id: string;
  firstname: string | null;
  lastname: string | null;
  email: string | null;
  phone: string | null;
  company: string | null;
  tags: string[];
  custom_fields: Record<string, unknown>;
  notes: string | null;
  created_at: string | null;
}

export interface ContactPayload {
  firstname?: string | null;
  lastname?: string | null;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  tags?: string[];
  custom_fields?: Record<string, unknown>;
  notes?: string | null;
}

export interface Task {
  id: string;
  contact_id: string;
  title: string | null;
  due: string | null;
  done: boolean;
}

export interface Opportunity {
  id: string;
  contact_id: string | null;
  pipeline_id: string;
  stage_id: string;
  name: string;
  value: number | null;
  status: string | null;
}

export const listContacts = async (params?: {
  search?: string;
  tag?: string;
}): Promise<Contact[]> => {
  const { data } = await apiClient.get<Contact[]>("/contacts", { params });
  return data;
};

export const createContact = async (
  payload: ContactPayload
): Promise<Contact> => {
  const { data } = await apiClient.post<Contact>("/contacts", payload);
  return data;
};

export const updateContact = async (
  id: string,
  payload: ContactPayload
): Promise<Contact> => {
  const { data } = await apiClient.patch<Contact>(`/contacts/${id}`, payload);
  return data;
};

export const deleteContact = async (id: string): Promise<void> => {
  await apiClient.delete(`/contacts/${id}`);
};

export const updateContactTags = async (
  id: string,
  tag: string,
  action: "add" | "remove"
): Promise<Contact> => {
  const { data } = await apiClient.post<Contact>(`/contacts/${id}/tags`, {
    tag,
    action,
  });
  return data;
};

export const getContactTasks = async (id: string): Promise<Task[]> => {
  const { data } = await apiClient.get<Task[]>(`/contacts/${id}/tasks`);
  return data;
};

export const getContactOpportunities = async (
  id: string
): Promise<Opportunity[]> => {
  const { data } = await apiClient.get<Opportunity[]>(
    `/contacts/${id}/opportunities`
  );
  return data;
};
