import { apiClient } from "./client";

export interface Opportunity {
  id: string;
  workspace_id: string;
  contact_id: string | null;
  pipeline_id: string;
  stage_id: string;
  name: string;
  value: number | null;
  status: string | null;
  created_at: string | null;
}

export interface CreateOpportunityInput {
  name: string;
  value?: number | null;
  pipeline_id: string;
  stage_id: string;
  contact_id?: string | null;
  status?: string | null;
}

export interface UpdateOpportunityInput {
  name?: string;
  value?: number | null;
  pipeline_id?: string;
  stage_id?: string;
  contact_id?: string | null;
  status?: string | null;
}

export const listOpportunities = async (
  pipelineId?: string
): Promise<Opportunity[]> => {
  const { data } = await apiClient.get<Opportunity[]>("/opportunities", {
    params: pipelineId ? { pipeline_id: pipelineId } : undefined,
  });
  return data;
};

export const createOpportunity = async (
  input: CreateOpportunityInput
): Promise<Opportunity> => {
  const { data } = await apiClient.post<Opportunity>("/opportunities", input);
  return data;
};

export const updateOpportunity = async (
  id: string,
  input: UpdateOpportunityInput
): Promise<Opportunity> => {
  const { data } = await apiClient.patch<Opportunity>(
    `/opportunities/${id}`,
    input
  );
  return data;
};

export const moveOpportunity = async (
  id: string,
  stageId: string
): Promise<Opportunity> => {
  const { data } = await apiClient.post<Opportunity>(`/opportunities/${id}/move`, {
    stage_id: stageId,
  });
  return data;
};
