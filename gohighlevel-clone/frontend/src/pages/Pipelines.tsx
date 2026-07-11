import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Card,
  Group,
  LoadingOverlay,
  Modal,
  NumberInput,
  ScrollArea,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { IconPlus } from "@tabler/icons-react";
import {
  createPipeline,
  createStage,
  listPipelines,
  type Pipeline,
  type PipelineStage,
} from "../api/pipelines";
import {
  createOpportunity,
  listOpportunities,
  moveOpportunity,
  type Opportunity,
} from "../api/opportunities";

const currency = (value: number | null | undefined) =>
  value == null
    ? "—"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }).format(value);

export default function Pipelines() {
  const queryClient = useQueryClient();

  const pipelinesQuery = useQuery({
    queryKey: ["pipelines"],
    queryFn: listPipelines,
  });

  const [pipelineId, setPipelineId] = useState<string | null>(null);

  useEffect(() => {
    if (!pipelineId && pipelinesQuery.data && pipelinesQuery.data.length > 0) {
      setPipelineId(pipelinesQuery.data[0].id);
    }
  }, [pipelinesQuery.data, pipelineId]);

  const selectedPipeline = useMemo<Pipeline | null>(
    () => pipelinesQuery.data?.find((p) => p.id === pipelineId) ?? null,
    [pipelinesQuery.data, pipelineId]
  );

  const opportunitiesQuery = useQuery({
    queryKey: ["opportunities", pipelineId],
    queryFn: () => listOpportunities(pipelineId ?? undefined),
    enabled: !!pipelineId,
  });

  const opportunitiesByStage = useMemo(() => {
    const map: Record<string, Opportunity[]> = {};
    for (const stage of selectedPipeline?.stages ?? []) {
      map[stage.id] = [];
    }
    for (const opp of opportunitiesQuery.data ?? []) {
      if (!map[opp.stage_id]) map[opp.stage_id] = [];
      map[opp.stage_id].push(opp);
    }
    return map;
  }, [opportunitiesQuery.data, selectedPipeline]);

  const moveMutation = useMutation({
    mutationFn: ({ id, stageId }: { id: string; stageId: string }) =>
      moveOpportunity(id, stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities", pipelineId] });
    },
  });

  // ----- Modals -----
  const [newPipelineOpened, newPipeline] = useDisclosure(false);
  const [newStageOpened, newStage] = useDisclosure(false);
  const [newDealOpened, newDeal] = useDisclosure(false);

  const [pipelineName, setPipelineName] = useState("");
  const [stageName, setStageName] = useState("");
  const [dealName, setDealName] = useState("");
  const [dealValue, setDealValue] = useState<number | undefined>(undefined);
  const [dealStage, setDealStage] = useState<string | null>(null);

  const createPipelineMutation = useMutation({
    mutationFn: () => createPipeline(pipelineName),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      setPipelineId(created.id);
      setPipelineName("");
      newPipeline.close();
    },
  });

  const createStageMutation = useMutation({
    mutationFn: () =>
      createStage(pipelineId!, stageName, (selectedPipeline?.stages.length ?? 0) + 1),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      setStageName("");
      newStage.close();
    },
  });

  const createDealMutation = useMutation({
    mutationFn: () =>
      createOpportunity({
        name: dealName,
        value: dealValue ?? null,
        pipeline_id: pipelineId!,
        stage_id: dealStage ?? selectedPipeline?.stages[0]?.id ?? "",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities", pipelineId] });
      setDealName("");
      setDealValue(undefined);
      setDealStage(null);
      newDeal.close();
    },
  });

  const [draggedId, setDraggedId] = useState<string | null>(null);

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Title order={2}>Pipelines</Title>
        <Group>
          <Button
            leftSection={<IconPlus size={16} />}
            variant="default"
            onClick={newPipeline.open}
          >
            New Pipeline
          </Button>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={newDeal.open}
            disabled={!pipelineId}
          >
            New Deal
          </Button>
        </Group>
      </Group>

      {pipelinesQuery.data && pipelinesQuery.data.length > 0 && (
        <Group mb="md">
          <Select
            label="Active pipeline"
            data={pipelinesQuery.data.map((p) => ({
              value: p.id,
              label: p.name,
            }))}
            value={pipelineId}
            onChange={setPipelineId}
            searchable={false}
            w={260}
          />
          <Button
            variant="light"
            leftSection={<IconPlus size={16} />}
            onClick={newStage.open}
            disabled={!pipelineId}
          >
            Add stage
          </Button>
        </Group>
      )}

      <Box pos="relative" style={{ minHeight: 200 }}>
        <LoadingOverlay visible={pipelinesQuery.isLoading || opportunitiesQuery.isLoading} />
        {!pipelineId && !pipelinesQuery.isLoading && (
          <Card withBorder p="xl">
            <Stack align="center">
              <Text color="dimmed">No pipelines yet.</Text>
              <Button onClick={newPipeline.open}>Create your first pipeline</Button>
            </Stack>
          </Card>
        )}

        {selectedPipeline && (
          <ScrollArea type="never">
            <SimpleGrid
              cols={selectedPipeline.stages.length || 1}
              gap="md"
              verticalSpacing="md"
              style={{ minWidth: 220 * (selectedPipeline.stages.length || 1) }}
            >
              {selectedPipeline.stages.map((stage: PipelineStage) => (
                <Box
                  key={stage.id}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const id = e.dataTransfer.getData("text/plain") || draggedId;
                    if (id && id !== stage.id) {
                      moveMutation.mutate({ id, stageId: stage.id });
                    }
                    setDraggedId(null);
                  }}
                >
                  <Card withBorder radius="md" p={0}>
                    <Group justify="space-between" px="sm" py="xs" bg="gray.0">
                      <Text fw={600}>{stage.name}</Text>
                      <Text size="xs" color="dimmed">
                        {(opportunitiesByStage[stage.id] ?? []).length}
                      </Text>
                    </Group>
                    <Stack gap="xs" p="xs">
                      {(opportunitiesByStage[stage.id] ?? []).map((opp) => (
                        <Card
                          key={opp.id}
                          withBorder
                          padding="xs"
                          radius="sm"
                          draggable
                          onDragStart={(e) => {
                            e.dataTransfer.setData("text/plain", opp.id);
                            e.dataTransfer.effectAllowed = "move";
                            setDraggedId(opp.id);
                          }}
                          onDragEnd={() => setDraggedId(null)}
                          sx={{ cursor: "grab" }}
                        >
                          <Text size="sm" fw={500}>
                            {opp.name}
                          </Text>
                          <Text size="sm" color="teal.7">
                            {currency(opp.value)}
                          </Text>
                        </Card>
                      ))}
                      {(opportunitiesByStage[stage.id] ?? []).length === 0 && (
                        <Text size="xs" color="dimmed" p="xs">
                          Drop deals here
                        </Text>
                      )}
                    </Stack>
                  </Card>
                </Box>
              ))}
            </SimpleGrid>
          </ScrollArea>
        )}
      </Box>

      {/* New pipeline modal */}
      <Modal
        opened={newPipelineOpened}
        onClose={newPipeline.close}
        title="New pipeline"
      >
        <Stack>
          <TextInput
            label="Name"
            placeholder="Sales Pipeline"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.currentTarget.value)}
          />
          <Button
            onClick={() => createPipelineMutation.mutate()}
            loading={createPipelineMutation.isLoading}
            disabled={!pipelineName.trim()}
          >
            Create
          </Button>
        </Stack>
      </Modal>

      {/* New stage modal */}
      <Modal opened={newStageOpened} onClose={newStage.close} title="Add stage">
        <Stack>
          <TextInput
            label="Stage name"
            placeholder="Qualified"
            value={stageName}
            onChange={(e) => setStageName(e.currentTarget.value)}
          />
          <Button
            onClick={() => createStageMutation.mutate()}
            loading={createStageMutation.isLoading}
            disabled={!stageName.trim() || !pipelineId}
          >
            Add
          </Button>
        </Stack>
      </Modal>

      {/* New deal modal */}
      <Modal opened={newDealOpened} onClose={newDeal.close} title="New deal">
        <Stack>
          <TextInput
            label="Deal name"
            placeholder="Acme Co. — Website redesign"
            value={dealName}
            onChange={(e) => setDealName(e.currentTarget.value)}
          />
          <NumberInput
            label="Value (USD)"
            placeholder="0"
            value={dealValue}
            onChange={(v) => setDealValue(typeof v === "number" ? v : undefined)}
            min={0}
            decimalScale={2}
          />
          <Select
            label="Stage"
            data={selectedPipeline?.stages.map((s) => ({
              value: s.id,
              label: s.name,
            })) ?? []}
            value={dealStage ?? selectedPipeline?.stages[0]?.id ?? null}
            onChange={setDealStage}
            searchable={false}
          />
          <Button
            onClick={() => createDealMutation.mutate()}
            loading={createDealMutation.isLoading}
            disabled={!dealName.trim() || !pipelineId}
          >
            Create deal
          </Button>
        </Stack>
      </Modal>
    </Box>
  );
}
