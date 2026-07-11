import { apiClient } from "./client";

export type BlockType =
  | "short_text"
  | "long_text"
  | "email"
  | "phone"
  | "dropdown"
  | "checkbox"
  | "submit";

export interface Block {
  type: BlockType;
  label: string;
  required?: boolean;
  options?: string[];
  placeholder?: string;
}

export interface FormDefinition {
  blocks: Block[];
  title?: string | null;
  submit_label?: string | null;
}

export interface Form {
  id: string;
  workspace_id: string;
  name: string;
  definition: FormDefinition;
  published_slug: string | null;
  created_at?: string | null;
}

export type FormPayload = {
  name: string;
  definition: FormDefinition;
};

export const listForms = async (): Promise<Form[]> => {
  const { data } = await apiClient.get<Form[]>("/forms");
  return data;
};

export const createForm = async (payload: FormPayload): Promise<Form> => {
  const { data } = await apiClient.post<Form>("/forms", payload);
  return data;
};

export const updateForm = async (
  id: string,
  payload: Partial<FormPayload>
): Promise<Form> => {
  const { data } = await apiClient.patch<Form>(`/forms/${id}`, payload);
  return data;
};

export const deleteForm = async (id: string): Promise<void> => {
  await apiClient.delete(`/forms/${id}`);
};

export const getFormPublic = async (
  slug: string
): Promise<{ name: string; definition: FormDefinition; published_slug: string }> => {
  const { data } = await apiClient.get(`/forms/${slug}/public`);
  return data;
};

export const submitForm = async (
  slug: string,
  values: Record<string, unknown>
): Promise<{ ok: boolean; submission_id: string }> => {
  const { data } = await apiClient.post(`/forms/${slug}/submit`, {
    data: values,
  });
  return data;
};
