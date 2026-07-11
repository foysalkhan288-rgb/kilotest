import { apiClient } from "./client";

export interface Conversation {
  id: string;
  contact_id: string;
  contact_name: string;
  contact_email: string | null;
  channel: string;
  last_message: string;
  has_email: boolean;
  has_form: boolean;
}

export interface InboxMessage {
  id: string;
  direction: "in" | "out";
  body: string;
  subject: string | null;
  created_at: string | null;
}

export interface ConversationThread {
  id: string;
  contact_id: string;
  contact_name: string;
  contact_email: string | null;
  messages: InboxMessage[];
}

export const listConversations = async (): Promise<Conversation[]> => {
  const { data } = await apiClient.get<Conversation[]>("/conversations");
  return data;
};

export const getConversation = async (id: string): Promise<ConversationThread> => {
  const { data } = await apiClient.get<ConversationThread>(`/conversations/${id}`);
  return data;
};
