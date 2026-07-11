import { apiClient } from "./client";

export type ReviewPlatform = "google" | "facebook";
export type ReviewStatus = "requested" | "responded" | "received";

export interface ReviewItem {
  id: string;
  contact_id: string;
  contact_name: string | null;
  contact_email: string | null;
  platform: ReviewPlatform | null;
  rating: number | null;
  body: string | null;
  status: ReviewStatus | null;
  requested_at: string | null;
  responded_at: string | null;
}

export interface ContactOption {
  id: string;
  firstname: string | null;
  lastname: string | null;
  email: string | null;
}

export const listReviews = async (status?: string): Promise<ReviewItem[]> => {
  const { data } = await apiClient.get<ReviewItem[]>("/reviews", {
    params: status ? { status } : {},
  });
  return data;
};

export const requestReview = async (payload: {
  contact_id: string;
  platform: ReviewPlatform;
}): Promise<{ ok: boolean; review_id: string }> => {
  const { data } = await apiClient.post<{ ok: boolean; review_id: string }>(
    "/reviews/request",
    payload
  );
  return data;
};

export const respondReview = async (
  id: string,
  payload: { body: string; rating?: number | null }
): Promise<ReviewItem> => {
  const { data } = await apiClient.post<ReviewItem>(`/reviews/${id}/respond`, payload);
  return data;
};

export const createReview = async (payload: {
  contact_id: string;
  platform: ReviewPlatform;
  rating?: number | null;
  body?: string | null;
}): Promise<ReviewItem> => {
  const { data } = await apiClient.post<ReviewItem>("/reviews", payload);
  return data;
};

export const listContactsForReview = async (): Promise<ContactOption[]> => {
  const { data } = await apiClient.get<ContactOption[]>("/contacts");
  return data;
};
