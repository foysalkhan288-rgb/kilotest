import { apiClient } from "./client";

export interface Tag {
  id: string;
  workspace_id: string;
  name: string;
  color: string | null;
}

export const listTags = async (): Promise<Tag[]> => {
  const { data } = await apiClient.get<Tag[]>("/tags");
  return data;
};

export const createTag = async (payload: {
  name: string;
  color?: string | null;
}): Promise<Tag> => {
  const { data } = await apiClient.post<Tag>("/tags", payload);
  return data;
};
