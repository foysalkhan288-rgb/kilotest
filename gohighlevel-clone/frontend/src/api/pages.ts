import { apiClient } from "./client";

export type PageBlockType =
  | "heading"
  | "text"
  | "image"
  | "button"
  | "spacer"
  | "form_embed";

export interface PageBlock {
  type: PageBlockType;
  content?: string | null;
  level?: number | null;
  url?: string | null;
  src?: string | null;
  height?: number | null;
  form_slug?: string | null;
}

export interface PageDefinition {
  blocks: PageBlock[];
  title?: string | null;
}

export interface Page {
  id: string;
  workspace_id: string;
  name: string;
  definition: PageDefinition;
  published_slug: string | null;
}

export type PagePayload = {
  name: string;
  definition: PageDefinition;
};

export const listPages = async (): Promise<Page[]> => {
  const { data } = await apiClient.get<Page[]>("/pages");
  return data;
};

export const createPage = async (payload: PagePayload): Promise<Page> => {
  const { data } = await apiClient.post<Page>("/pages", payload);
  return data;
};

export const updatePage = async (
  id: string,
  payload: Partial<PagePayload>
): Promise<Page> => {
  const { data } = await apiClient.patch<Page>(`/pages/${id}`, payload);
  return data;
};

export const deletePage = async (id: string): Promise<void> => {
  await apiClient.delete(`/pages/${id}`);
};

export const getPagePublic = async (
  slug: string
): Promise<{ name: string; definition: PageDefinition; published_slug: string }> => {
  const { data } = await apiClient.get(`/p/${slug}`);
  return data;
};
