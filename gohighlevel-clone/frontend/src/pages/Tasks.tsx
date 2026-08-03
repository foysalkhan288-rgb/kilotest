import { useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Card,
  Checkbox,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTask,
  deleteTask,
  listContactsForTask,
  listTasks,
  updateTask,
  type ContactOption,
  type TaskItem,
} from "../api/tasks";

export default function Tasks() {
  const queryClient = useQueryClient();
  const [filterDone, setFilterDone] = useState<string | null>("open");

  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<TaskItem | null>(null);

  const [contactId, setContactId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");

  const [editContactId, setEditContactId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDue, setEditDue] = useState("");

  const tasksQuery = useQuery({
    queryKey: ["tasks", filterDone],
    queryFn: () =>
      listTasks({
        done: filterDone === "open" ? false : filterDone === "done" ? true : undefined,
      }),
  });
  const contactsQuery = useQuery({
    queryKey: ["contacts-for-task"],
    queryFn: listContactsForTask,
  });

  const tasks: TaskItem[] = tasksQuery.data ?? [];
  const contacts: ContactOption[] = contactsQuery.data ?? [];

  const contactOptions = contacts.map((c) => ({
    value: c.id,
    label: `${c.firstname ?? ""} ${c.lastname ?? ""}`.trim() || c.email || c.id,
  }));
  const contactLabel = (id: string) =>
    contactOptions.find((o) => o.value === id)?.label ?? "Unknown contact";

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["tasks"] });

  const resetCreate = () => {
    setContactId(null);
    setTitle("");
    setDue("");
  };

  const createMutation = useMutation({
    mutationFn: () => createTask({ contact_id: contactId!, title, due: due || null }),
    onSuccess: () => {
      refresh();
      setCreateOpen(false);
      resetCreate();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateTask>[1]) =>
      updateTask(editTarget!.id, payload),
    onSuccess: () => {
      refresh();
      setEditTarget(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTask(id),
    onSuccess: refresh,
  });

  const openEdit = (task: TaskItem) => {
    setEditTarget(task);
    setEditContactId(task.contact_id);
    setEditTitle(task.title ?? "");
    setEditDue(task.due ? task.due.slice(0, 16) : "");
  };

  const toggleDone = (task: TaskItem) => {
    updateMutation.mutate({ done: !task.done });
  };

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Tasks</Title>
        <Group>
          <Select
            w={160}
            data={[
              { value: "open", label: "Open" },
              { value: "done", label: "Done" },
              { value: "all", label: "All" },
            ]}
            value={filterDone}
            onChange={setFilterDone}
          />
          <Button onClick={() => setCreateOpen(true)}>New task</Button>
        </Group>
      </Group>

      <Paper withBorder radius="md" p="md">
        {tasksQuery.isLoading ? (
          <Text color="dimmed">Loading…</Text>
        ) : tasks.length === 0 ? (
          <Text color="dimmed">No tasks yet.</Text>
        ) : (
          <Box style={{ overflowX: "auto" }}>
            <Table striped highlightOnHover withColumnBorders>
              <thead>
                <tr>
                  <th style={{ width: 48 }}></th>
                  <th>Title</th>
                  <th>Contact</th>
                  <th>Due</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id} style={{ opacity: t.done ? 0.55 : 1 }}>
                    <td>
                      <Checkbox checked={t.done} onChange={() => toggleDone(t)} />
                    </td>
                    <td style={{ textDecoration: t.done ? "line-through" : "none" }}>
                      {t.title ?? "—"}
                    </td>
                    <td>{contactLabel(t.contact_id)}</td>
                    <td>{t.due ? new Date(t.due).toLocaleString() : "—"}</td>
                    <td>
                      <Group gap={4} wrap="nowrap">
                        <ActionIcon
                          variant="subtle"
                          color="blue"
                          onClick={() => openEdit(t)}
                          title="Edit"
                        >
                          ✎
                        </ActionIcon>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          onClick={() => deleteMutation.mutate(t.id)}
                          title="Delete"
                        >
                          🗑
                        </ActionIcon>
                      </Group>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Box>
        )}
      </Paper>

      <Modal
        opened={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetCreate();
        }}
        title="New task"
      >
        <Stack>
          <Select
            label="Contact"
            placeholder="Select a contact"
            data={contactOptions}
            value={contactId}
            onChange={setContactId}
            searchable
            withAsterisk
          />
          <TextInput
            label="Title"
            placeholder="e.g. Follow up call"
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
            withAsterisk
          />
          <TextInput
            label="Due"
            type="datetime-local"
            value={due}
            onChange={(e) => setDue(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              onClick={() => createMutation.mutate()}
              loading={createMutation.isPending}
              disabled={!contactId || !title}
            >
              Create
            </Button>
          </Group>
          {createMutation.isError && (
            <Text color="red" size="sm">
              Failed to create task.
            </Text>
          )}
        </Stack>
      </Modal>

      <Modal
        opened={editTarget !== null}
        onClose={() => setEditTarget(null)}
        title="Edit task"
      >
        <Stack>
          <Select
            label="Contact"
            data={contactOptions}
            value={editContactId}
            onChange={setEditContactId}
            searchable
          />
          <TextInput
            label="Title"
            value={editTitle}
            onChange={(e) => setEditTitle(e.currentTarget.value)}
          />
          <TextInput
            label="Due"
            type="datetime-local"
            value={editDue}
            onChange={(e) => setEditDue(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              onClick={() =>
                updateMutation.mutate({
                  contact_id: editContactId,
                  title: editTitle,
                  due: editDue || null,
                })
              }
              loading={updateMutation.isPending}
            >
              Save
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
