import { useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  Code,
  Divider,
  Group,
  Paper,
  Select,
  Stack,
  Switch,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createForm,
  deleteForm,
  listForms,
  updateForm,
  type Block,
  type BlockType,
  type Form,
  type FormDefinition,
} from "../api/forms";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const BLOCK_LABELS: Record<BlockType, string> = {
  short_text: "Short Text",
  long_text: "Long Text",
  email: "Email",
  phone: "Phone",
  dropdown: "Dropdown",
  checkbox: "Checkbox",
  submit: "Submit Button",
};

const PALETTE: BlockType[] = [
  "short_text",
  "long_text",
  "email",
  "phone",
  "dropdown",
  "checkbox",
  "submit",
];

const newBlock = (type: BlockType): Block => {
  const label =
    type === "submit"
      ? "Submit"
      : type === "email"
      ? "Email"
      : type.charAt(0).toUpperCase() + type.slice(1).replace("_", " ");
  return { type, label, required: false };
};

function PublishInfo({ form }: { form: Form }) {
  if (!form.published_slug) {
    return (
      <Text color="dimmed" size="sm">
        Save the form to publish and get a public link.
      </Text>
    );
  }
  const publicUrl = `${API_URL}/forms/${form.published_slug}/public`;
  const iframe = `<iframe src="${publicUrl}" width="100%" height="600" frameborder="0" title="${form.name}"></iframe>`;
  const script = `<script src="${API_URL}/embed.js" data-form="${form.published_slug}"></script>`;

  return (
    <Stack gap={6}>
      <Text size="sm" fw={600}>
        Public URL
      </Text>
      <Code block>{publicUrl}</Code>
      <Text size="sm" fw={600}>
        Embed (iframe)
      </Text>
      <Code block>{iframe}</Code>
      <Text size="sm" fw={600}>
        Embed (script)
      </Text>
      <Code block>{script}</Code>
    </Stack>
  );
}

function FormBuilder({ form, onClose }: { form: Form | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(form?.name ?? "Untitled form");
  const [title, setTitle] = useState(form?.definition?.title ?? "");
  const [submitLabel, setSubmitLabel] = useState(
    form?.definition?.submit_label ?? "Submit"
  );
  const [blocks, setBlocks] = useState<Block[]>(
    form?.definition?.blocks ?? []
  );

  const saveMutation = useMutation({
    mutationFn: () => {
      const definition: FormDefinition = {
        title: title || null,
        submit_label: submitLabel || null,
        blocks,
      };
      const payload = { name, definition };
      return form ? updateForm(form.id, payload) : createForm(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["forms"] });
      onClose();
    },
  });

  const addBlock = (type: BlockType) =>
    setBlocks((prev) => [...prev, newBlock(type)]);

  const updateBlock = (idx: number, patch: Partial<Block>) =>
    setBlocks((prev) => prev.map((b, i) => (i === idx ? { ...b, ...patch } : b)));

  const removeBlock = (idx: number) =>
    setBlocks((prev) => prev.filter((_, i) => i !== idx));

  const moveBlock = (idx: number, dir: -1 | 1) =>
    setBlocks((prev) => {
      const next = [...prev];
      const target = idx + dir;
      if (target < 0 || target >= next.length) return prev;
      [next[idx], next[target]] = [next[target], next[idx]];
      return next;
    });

  return (
    <Paper withBorder p="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>{form ? "Edit form" : "New form"}</Title>
        <Button variant="default" size="xs" onClick={onClose}>
          Close
        </Button>
      </Group>

      <Stack gap="md">
        <Group grow>
          <TextInput
            label="Form name"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
          />
          <TextInput
            label="Form title"
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
          />
          <TextInput
            label="Submit button label"
            value={submitLabel}
            onChange={(e) => setSubmitLabel(e.currentTarget.value)}
          />
        </Group>

        <Tabs defaultValue="build">
          <Tabs.List>
            <Tabs.Tab value="build">Builder</Tabs.Tab>
            <Tabs.Tab value="preview">Preview</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="build" pt="md">
            <Group align="flex-start">
              <Stack gap={6} w={200}>
                <Text size="xs" fw={600} color="dimmed">
                  Add block
                </Text>
                {PALETTE.map((type) => (
                  <Button
                    key={type}
                    size="xs"
                    variant="light"
                    onClick={() => addBlock(type)}
                  >
                    + {BLOCK_LABELS[type]}
                  </Button>
                ))}
              </Stack>

              <Stack gap="sm" style={{ flex: 1 }}>
                {blocks.length === 0 && (
                  <Text color="dimmed" size="sm">
                    No blocks yet. Add fields from the palette.
                  </Text>
                )}
                {blocks.map((block, idx) => (
                  <Paper key={idx} withBorder p="xs" radius="sm">
                    <Group justify="space-between" mb={6}>
                      <Badge variant="light">{BLOCK_LABELS[block.type]}</Badge>
                      <Group gap={4}>
                        <ActionIcon
                          size="xs"
                          variant="subtle"
                          onClick={() => moveBlock(idx, -1)}
                          aria-label="Move up"
                        >
                          ↑
                        </ActionIcon>
                        <ActionIcon
                          size="xs"
                          variant="subtle"
                          onClick={() => moveBlock(idx, 1)}
                          aria-label="Move down"
                        >
                          ↓
                        </ActionIcon>
                        <ActionIcon
                          size="xs"
                          color="red"
                          variant="subtle"
                          onClick={() => removeBlock(idx)}
                          aria-label="Remove"
                        >
                          ✕
                        </ActionIcon>
                      </Group>
                    </Group>
                    {block.type !== "submit" && (
                      <Group grow>
                        <TextInput
                          size="xs"
                          label="Label"
                          value={block.label}
                          onChange={(e) =>
                            updateBlock(idx, { label: e.currentTarget.value })
                          }
                        />
                        <TextInput
                          size="xs"
                          label="Placeholder"
                          value={block.placeholder ?? ""}
                          onChange={(e) =>
                            updateBlock(idx, { placeholder: e.currentTarget.value })
                          }
                        />
                      </Group>
                    )}
                    {block.type === "dropdown" && (
                      <Textarea
                        size="xs"
                        label="Options (one per line)"
                        mt={6}
                        autosize
                        minRows={2}
                        value={(block.options ?? []).join("\n")}
                        onChange={(e) =>
                          updateBlock(idx, {
                            options: e.currentTarget.value
                              .split("\n")
                              .map((o) => o.trim())
                              .filter(Boolean),
                          })
                        }
                      />
                    )}
                    {block.type !== "submit" && (
                      <Switch
                        size="xs"
                        mt={6}
                        label="Required"
                        checked={!!block.required}
                        onChange={(e) =>
                          updateBlock(idx, { required: e.currentTarget.checked })
                        }
                      />
                    )}
                  </Paper>
                ))}
              </Stack>
            </Group>
          </Tabs.Panel>

          <Tabs.Panel value="preview" pt="md">
            <Paper withBorder p="md" bg="gray.0">
              <FormPreview
                title={title}
                submitLabel={submitLabel}
                blocks={blocks}
              />
            </Paper>
          </Tabs.Panel>
        </Tabs>

        <Group justify="flex-end">
          <Button
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
          >
            Save form
          </Button>
        </Group>
        {saveMutation.isError && (
          <Text color="red" size="sm">
            Failed to save form
          </Text>
        )}
      </Stack>
    </Paper>
  );
}

function FormPreview({
  title,
  submitLabel,
  blocks,
}: {
  title?: string;
  submitLabel?: string;
  blocks: Block[];
}) {
  return (
    <Box>
      {title && <Title order={4}>{title}</Title>}
      <Stack gap="xs" mt="xs">
        {blocks.map((block, idx) => {
          if (block.type === "submit") {
            return (
              <Button key={idx} mt={4}>
                {block.label || submitLabel || "Submit"}
              </Button>
            );
          }
          if (block.type === "long_text") {
            return (
              <Textarea
                key={idx}
                label={block.label}
                placeholder={block.placeholder ?? ""}
              />
            );
          }
          if (block.type === "dropdown") {
            return (
              <Select
                key={idx}
                label={block.label}
                placeholder={block.placeholder ?? "Select..."}
                data={block.options ?? []}
              />
            );
          }
          if (block.type === "checkbox") {
            return (
              <Checkbox key={idx} label={block.label} />
            );
          }
          const inputType =
            block.type === "email"
              ? "email"
              : block.type === "phone"
              ? "tel"
              : "text";
          return (
            <TextInput
              key={idx}
              type={inputType}
              label={block.label}
              placeholder={block.placeholder ?? ""}
            />
          );
        })}
      </Stack>
    </Box>
  );
}

export default function Forms() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Form | null>(null);
  const [creating, { open: openCreate, close: closeCreate }] = useDisclosure(false);

  const formsQuery = useQuery({ queryKey: ["forms"], queryFn: listForms });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteForm(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["forms"] }),
  });

  const rows = formsQuery.data ?? [];

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Forms</Title>
        <Button onClick={openCreate}>+ New form</Button>
      </Group>

      {creating && (
        <FormBuilder
          form={null}
          onClose={() => {
            closeCreate();
          }}
        />
      )}
      {editing && (
        <FormBuilder
          form={editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}

      {!creating && !editing && (
        <Stack gap="md">
          {rows.length === 0 ? (
            <Paper withBorder p="md">
              <Text color="dimmed">No forms yet. Create your first form.</Text>
            </Paper>
          ) : (
            rows.map((f) => (
              <Paper key={f.id} withBorder p="md">
                <Group justify="space-between">
                  <Box>
                    <Group gap={8}>
                      <Text fw={600}>{f.name}</Text>
                      {f.published_slug && (
                        <Badge
                          variant="outline"
                          component="a"
                          href={`${API_URL}/forms/${f.published_slug}/public`}
                          target="_blank"
                        >
                          Live
                        </Badge>
                      )}
                    </Group>
                    <Text size="xs" color="dimmed">
                      {(f.definition?.blocks ?? []).length} blocks
                    </Text>
                  </Box>
                  <Group gap={4}>
                    <Button size="xs" variant="subtle" onClick={() => setEditing(f)}>
                      Edit
                    </Button>
                    <Button
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => deleteMutation.mutate(f.id)}
                    >
                      Delete
                    </Button>
                  </Group>
                </Group>
                <Divider my="sm" />
                <PublishInfo form={f} />
              </Paper>
            ))
          )}
        </Stack>
      )}
    </Stack>
  );
}
