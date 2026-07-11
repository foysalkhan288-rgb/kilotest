import { useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Divider,
  Group,
  JsonInput,
  Modal,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createWorkflow,
  deleteWorkflow,
  listWorkflows,
  toggleWorkflow,
  updateWorkflow,
  type ActionType,
  type EventType,
  type Workflow,
  type WorkflowAction,
} from "../api/workflows";

const EVENT_TYPES: { value: EventType; label: string }[] = [
  { value: "form.submitted", label: "Form submitted" },
  { value: "contact.created", label: "Contact created" },
  { value: "tag.added", label: "Tag added" },
  { value: "appointment.booked", label: "Appointment booked" },
  { value: "appointment.no_show", label: "Appointment no-show" },
];

const ACTION_TYPES: { value: ActionType; label: string }[] = [
  { value: "send_email", label: "Send email" },
  { value: "add_tag", label: "Add tag" },
  { value: "remove_tag", label: "Remove tag" },
  { value: "create_task", label: "Create task" },
  { value: "move_opportunity_stage", label: "Move opportunity stage" },
  { value: "notify", label: "Notify" },
  { value: "wait", label: "Wait" },
  { value: "if_else", label: "If / Else" },
];

const emptyAction = (type: ActionType = "send_email"): WorkflowAction => {
  switch (type) {
    case "send_email":
      return { type, subject: "", html: "" };
    case "add_tag":
    case "remove_tag":
      return { type, tag: "" };
    case "create_task":
      return { type, title: "" };
    case "move_opportunity_stage":
      return { type, stage_name: "" };
    case "notify":
      return { type, message: "" };
    case "wait":
      return { type, minutes: 60, then: [] as WorkflowAction[] };
    case "if_else":
      return {
        type,
        field: "contact.email",
        equals: "",
        then: [] as WorkflowAction[],
        else: [] as WorkflowAction[],
      };
    default:
      return { type };
  }
};

function ActionRow({
  action,
  onChange,
  onRemove,
}: {
  action: WorkflowAction;
  onChange: (next: WorkflowAction) => void;
  onRemove: () => void;
}) {
  const set = (patch: Partial<WorkflowAction>) => onChange({ ...action, ...patch });

  return (
    <Paper withBorder p="xs" radius="sm">
      <Group justify="space-between" mb="xs">
        <Select
          size="xs"
          w={220}
          data={ACTION_TYPES}
          value={action.type}
          onChange={(v) =>
            onChange(emptyAction((v as ActionType) ?? "send_email"))
          }
        />
        <ActionIcon color="red" variant="subtle" onClick={onRemove} aria-label="Remove action">
          ✕
        </ActionIcon>
      </Group>

      {action.type === "send_email" && (
        <Stack gap={6}>
          <TextInput
            size="xs"
            label="Subject"
            value={(action.subject as string) ?? ""}
            onChange={(e) => set({ subject: e.currentTarget.value })}
          />
          <Textarea
            size="xs"
            label="HTML body"
            autosize
            minRows={3}
            value={(action.html as string) ?? ""}
            onChange={(e) => set({ html: e.currentTarget.value })}
          />
        </Stack>
      )}

      {(action.type === "add_tag" || action.type === "remove_tag") && (
        <TextInput
          size="xs"
          label="Tag"
          value={(action.tag as string) ?? ""}
          onChange={(e) => set({ tag: e.currentTarget.value })}
        />
      )}

      {action.type === "create_task" && (
        <TextInput
          size="xs"
          label="Task title"
          value={(action.title as string) ?? ""}
          onChange={(e) => set({ title: e.currentTarget.value })}
        />
      )}

      {action.type === "move_opportunity_stage" && (
        <TextInput
          size="xs"
          label="Target stage name"
          value={(action.stage_name as string) ?? ""}
          onChange={(e) => set({ stage_name: e.currentTarget.value })}
        />
      )}

      {action.type === "notify" && (
        <Textarea
          size="xs"
          label="Message"
          autosize
          minRows={2}
          value={(action.message as string) ?? ""}
          onChange={(e) => set({ message: e.currentTarget.value })}
        />
      )}

      {action.type === "wait" && (
        <Stack gap={6}>
          <TextInput
            size="xs"
            type="number"
            label="Wait minutes"
            value={String((action.minutes as number) ?? 0)}
            onChange={(e) => set({ minutes: Number(e.currentTarget.value) || 0 })}
          />
          <Text size="xs" fw={600} mt={4}>
            Then
          </Text>
          <ActionList
            actions={(action.then as WorkflowAction[]) ?? []}
            onChange={(then) => set({ then })}
          />
        </Stack>
      )}

      {action.type === "if_else" && (
        <Stack gap={6}>
          <Group grow>
            <TextInput
              size="xs"
              label="Field (contact.<attr> / context.<key>)"
              value={(action.field as string) ?? ""}
              onChange={(e) => set({ field: e.currentTarget.value })}
            />
            <TextInput
              size="xs"
              label="Equals"
              value={String((action.equals as string) ?? "")}
              onChange={(e) => set({ equals: e.currentTarget.value })}
            />
          </Group>
          <Box>
            <Text size="xs" fw={600}>
              Then
            </Text>
            <ActionList
              actions={(action.then as WorkflowAction[]) ?? []}
              onChange={(then) => set({ then })}
            />
          </Box>
          <Box>
            <Text size="xs" fw={600}>
              Else
            </Text>
            <ActionList
              actions={(action.else as WorkflowAction[]) ?? []}
              onChange={(els) => set({ else: els })}
            />
          </Box>
        </Stack>
      )}
    </Paper>
  );
}

function ActionList({
  actions,
  onChange,
}: {
  actions: WorkflowAction[];
  onChange: (next: WorkflowAction[]) => void;
}) {
  return (
    <Stack gap={6}>
      {actions.map((action, idx) => (
        <ActionRow
          key={idx}
          action={action}
          onChange={(next) => {
            const copy = [...actions];
            copy[idx] = next;
            onChange(copy);
          }}
          onRemove={() => onChange(actions.filter((_, i) => i !== idx))}
        />
      ))}
      <Button
        size="xs"
        variant="light"
        onClick={() => onChange([...(actions ?? []), emptyAction()])}
      >
        Add action
      </Button>
    </Stack>
  );
}

function WorkflowEditor({
  workflow,
  onClose,
}: {
  workflow: Workflow | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(workflow?.name ?? "");
  const [eventType, setEventType] = useState<EventType | null>(
    (workflow?.trigger?.event_type as EventType) ?? "contact.created"
  );
  const [actions, setActions] = useState<WorkflowAction[]>(
    workflow?.actions ?? []
  );
  const [rawMode, setRawMode] = useState(false);
  const [raw, setRaw] = useState("");

  const open = () => {
    if (rawMode) {
      try {
        setActions(JSON.parse(raw));
      } catch {
        return;
      }
    }
  };

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        name,
        trigger: { event_type: eventType ?? "contact.created" },
        actions,
      };
      return workflow
        ? updateWorkflow(workflow.id, payload)
        : createWorkflow(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      onClose();
    },
  });

  return (
    <Modal
      opened={true}
      onClose={onClose}
      title={workflow ? "Edit workflow" : "New workflow"}
      size="lg"
    >
      <Stack>
        <TextInput
          label="Name"
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
        />
        <Select
          label="Trigger"
          data={EVENT_TYPES}
          value={eventType}
          onChange={(v) => setEventType((v as EventType) ?? null)}
        />

        <Divider label="Actions" labelPosition="center" />
        <Group justify="flex-end">
          <Checkbox
            label="Edit actions as JSON"
            checked={rawMode}
            onChange={(e) => {
              if (!rawMode) setRaw(JSON.stringify(actions, null, 2));
              setRawMode(e.currentTarget.checked);
            }}
          />
        </Group>

        {rawMode ? (
          <JsonInput
            label="Actions JSON"
            validationError="Invalid JSON"
            autosize
            minRows={6}
            value={raw}
            onChange={(v) => {
              setRaw(v);
              try {
                setActions(JSON.parse(v));
              } catch {
                /* ignore invalid while typing */
              }
            }}
            onBlur={open}
          />
        ) : (
          <ActionList actions={actions} onChange={setActions} />
        )}

        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
            Save
          </Button>
        </Group>
        {saveMutation.isError && (
          <Text color="red" size="sm">
            Failed to save workflow
          </Text>
        )}
      </Stack>
    </Modal>
  );
}

export default function Workflows() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Workflow | null>(null);
  const [creating, { open: openCreate, close: closeCreate }] = useDisclosure(false);

  const workflowsQuery = useQuery({ queryKey: ["workflows"], queryFn: listWorkflows });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => toggleWorkflow(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workflows"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteWorkflow(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workflows"] }),
  });

  const rows = workflowsQuery.data ?? [];

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Workflows</Title>
        <Button onClick={openCreate}>
          + New workflow
        </Button>
      </Group>

      {rows.length === 0 ? (
        <Paper withBorder p="md">
          <Text color="dimmed">No workflows yet. Create your first automation.</Text>
        </Paper>
      ) : (
        <Table striped highlightOnHover withBorder>
          <thead>
            <tr>
              <th>Name</th>
              <th>Trigger</th>
              <th>Actions</th>
              <th>Active</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((w) => (
              <tr key={w.id}>
                <td>{w.name}</td>
                <td>
                  <Badge variant="light">
                    {w.trigger?.event_type ?? "—"}
                  </Badge>
                </td>
                <td>{(w.actions ?? []).length}</td>
                <td>
                  <Switch
                    checked={w.active}
                    onChange={() => toggleMutation.mutate(w.id)}
                    disabled={toggleMutation.isPending}
                  />
                </td>
                <td>
                  <Group gap={4} justify="flex-end">
                    <Button size="xs" variant="subtle" onClick={() => setEditing(w)}>
                      Edit
                    </Button>
                    <Button
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => deleteMutation.mutate(w.id)}
                    >
                      Delete
                    </Button>
                  </Group>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {creating && (
        <WorkflowEditor
          workflow={null}
          onClose={() => {
            closeCreate();
          }}
        />
      )}
      {editing && (
        <WorkflowEditor
          workflow={editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}
    </Stack>
  );
}
