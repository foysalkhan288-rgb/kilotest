import { apiClient } from "./client";

export interface ContactOption {
  id: string;
  firstname: string | null;
  lastname: string | null;
  email: string | null;
}

export interface TaskItem {
  id: string;
  contact_id: string;
  title: string | null;
  due: string | null;
  done: boolean;
}

export const listTasks = async (params?: {
  done?: boolean;
}): Promise<TaskItem[]> => {
  const { data } = await apiClient.get<TaskItem[]>("/tasks", { params });
  return data;
};

export const createTask = async (payload: {
  contact_id: string;
  title: string;
  due: string | null;
}): Promise<TaskItem> => {
  const { data } = await apiClient.post<TaskItem>("/tasks", payload);
  return data;
};

export const updateTask = async (
  id: string,
  payload: Partial<Pick<TaskItem, "contact_id" | "title" | "due" | "done">>
): Promise<TaskItem> => {
  const { data } = await apiClient.patch<TaskItem>(`/tasks/${id}`, payload);
  return data;
};

export const deleteTask = async (id: string): Promise<void> => {
  await apiClient.delete(`/tasks/${id}`);
};

export const listContactsForTask = async (): Promise<ContactOption[]> => {
  const { data } = await apiClient.get<ContactOption[]>("/contacts", {
    params: { fields: "id,firstname,lastname,email" },
  });
  return data;
};
