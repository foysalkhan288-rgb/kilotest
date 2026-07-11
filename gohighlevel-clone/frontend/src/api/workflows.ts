import { apiClient } from "./client";

export type EventType =
  | "form.submitted"
  | "contact.created"
  | "tag.added"
  | "appointment.booked"
  | "appointment.no_show";

export type ActionType =
  | "send_email"
  | "add_tag"
  | "remove_tag"
  | "create_task"
  | "move_opportunity_stage"
  | "notify"
  | "wait"
  | "if_else";

export interface WorkflowAction {
  type: ActionType | string;
  // Action-specific keys (subject, html, tag, title, stage_name, message,
  // minutes, then, else, field, equals, ...). Typed loosely on purpose.
  [key: string]: unknown;
}

export interface Workflow {
  id: string;
  workspace_id: string;
  name: string;
  trigger: { event_type?: string } | null;
  actions: WorkflowAction[] | null;
  active: boolean;
}

export interface WorkflowPayload {
  name: string;
  trigger: { event_type: string };
  actions: WorkflowAction[];
  active?: boolean;
}

export const listWorkflows = async (): Promise<Workflow[]> => {
  const { data } = await apiClient.get<Workflow[]>("/workflows");
  return data;
};

export const createWorkflow = async (
  payload: WorkflowPayload
): Promise<Workflow> => {
  const { data } = await apiClient.post<Workflow>("/workflows", payload);
  return data;
};

export const updateWorkflow = async (
  id: string,
  payload: Partial<WorkflowPayload>
): Promise<Workflow> => {
  const { data } = await apiClient.patch<Workflow>(`/workflows/${id}`, payload);
  return data;
};

export const deleteWorkflow = async (id: string): Promise<void> => {
  await apiClient.delete(`/workflows/${id}`);
};

export const toggleWorkflow = async (id: string): Promise<Workflow> => {
  const { data } = await apiClient.post<Workflow>(`/workflows/${id}/toggle`);
  return data;
};
