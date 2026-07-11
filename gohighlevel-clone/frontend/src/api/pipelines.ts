import { apiClient } from "./client";

export interface PipelineStage {
  id: string;
  pipeline_id: string;
  name: string;
  position: number;
}

export interface Pipeline {
  id: string;
  workspace_id: string;
  name: string;
  stages: PipelineStage[];
}

export const listPipelines = async (): Promise<Pipeline[]> => {
  const { data } = await apiClient.get<Pipeline[]>("/pipelines");
  return data;
};

export const createPipeline = async (name: string): Promise<Pipeline> => {
  const { data } = await apiClient.post<Pipeline>("/pipelines", { name });
  return data;
};

export const createStage = async (
  pipelineId: string,
  name: string,
  position: number
): Promise<PipelineStage> => {
  const { data } = await apiClient.post<PipelineStage>(
    `/pipelines/${pipelineId}/stages`,
    { name, position }
  );
  return data;
};
