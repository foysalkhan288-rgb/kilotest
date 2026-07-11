import { apiClient } from "./client";

export interface EmailItem {
  id: string;
  contact_id: string | null;
  subject: string | null;
  body: string | null;
  status: string | null;
  sent_at: string | null;
}

export interface SendEmailPayload {
  to_email: string;
  subject: string;
  html: string;
  contact_id?: string | null;
}

export interface CampaignPayload {
  subject: string;
  html: string;
  tag?: string | null;
}

export interface CampaignResult {
  total: number;
  sent: number;
  failed: number;
  skipped_no_email: number;
}

export const sendEmail = async (
  payload: SendEmailPayload
): Promise<{ id: string; status: string }> => {
  const { data } = await apiClient.post<{ id: string; status: string }>(
    "/emails/send",
    payload
  );
  return data;
};

export const sendCampaign = async (
  payload: CampaignPayload
): Promise<CampaignResult> => {
  const { data } = await apiClient.post<CampaignResult>("/emails/campaign", payload);
  return data;
};

export const listEmails = async (): Promise<EmailItem[]> => {
  const { data } = await apiClient.get<EmailItem[]>("/emails");
  return data;
};
