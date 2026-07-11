import { useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Code,
  Divider,
  Group,
  Paper,
  Select,
  Stack,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createPage,
  deletePage,
  listPages,
  updatePage,
  type Page,
  type PageBlock,
  type PageBlockType,
  type PageDefinition,
} from "../api/pages";
import { listForms, type Form } from "../api/forms";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const BLOCK_LABELS: Record<PageBlockType, string> = {
  heading: "Heading",
  text: "Text",
  image: "Image",
  button: "Button",
  spacer: "Spacer",
  form_embed: "Form Embed",
};

const PALETTE: PageBlockType[] = [
  "heading",
  "text",
  "image",
  "button",
  "spacer",
  "form_embed",
];

const TEMPLATES: {
  key: string;
  name: string;
  definition: PageDefinition;
}[] = [
  {
    key: "blank",
    name: "Blank",
    definition: { title: "", blocks: [] },
  },
  {
    key: "rsvp",
    name: "Event RSVP",
    definition: {
      title: "You're invited!",
      blocks: [
        { type: "heading", content: "Join us for our event", level: 1 },
        {
          type: "text",
          content: "Reserve your spot before it fills up.",
        },
        { type: "button", content: "RSVP Now", url: "#" },
        { type: "spacer", height: 40 },
      ],
    },
  },
  {
    key: "lead",
    name: "Lead Capture",
    definition: {
      title: "Get your free guide",
      blocks: [
        { type: "heading", content: "Free Download", level: 1 },
        {
          type: "text",
          content: "Enter your details below and we'll send it over.",
        },
        { type: "form_embed", form_slug: null },
      ],
    },
  },
];

const newBlock = (type: PageBlockType): PageBlock => {
  switch (type) {
    case "heading":
      return { type, content: "Heading", level: 2 };
    case "text":
      return { type, content: "Some text..." };
    case "image":
      return { type, src: "", content: "" };
    case "button":
      return { type, content: "Click me", url: "#" };
    case "spacer":
      return { type, height: 32 };
    case "form_embed":
      return { type, form_slug: null };
    default:
      return { type };
  }
};

function PublishInfo({ page }: { page: Page }) {
  if (!page.published_slug) {
    return (
      <Text color="dimmed" size="sm">
        Save the page to publish and get a public link.
      </Text>
    );
  }
  const publicUrl = `${API_URL}/p/${page.published_slug}`;
  const iframe = `<iframe src="${publicUrl}" width="100%" height="800" frameborder="0" title="${page.name}"></iframe>`;

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
    </Stack>
  );
}

function PageBuilder({ page, onClose }: { page: Page | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const formsQuery = useQuery({ queryKey: ["forms"], queryFn: listForms });

  const [name, setName] = useState(page?.name ?? "Untitled page");
  const [title, setTitle] = useState(page?.definition?.title ?? "");
  const [blocks, setBlocks] = useState<PageBlock[]>(
    page?.definition?.blocks ?? []
  );

  const saveMutation = useMutation({
    mutationFn: () => {
      const definition: PageDefinition = { title: title || null, blocks };
      const payload = { name, definition };
      return page ? updatePage(page.id, payload) : createPage(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pages"] });
      onClose();
    },
  });

  const addBlock = (type: PageBlockType) =>
    setBlocks((prev) => [...prev, newBlock(type)]);

  const updateBlock = (idx: number, patch: Partial<PageBlock>) =>
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

  const applyTemplate = (key: string) => {
    const tpl = TEMPLATES.find((t) => t.key === key);
    if (!tpl) return;
    setTitle(tpl.definition.title ?? "");
    setBlocks(tpl.definition.blocks.map((b) => ({ ...b })));
  };

  const formOptions =
    formsQuery.data?.map((f: Form) => ({
      value: f.published_slug ?? f.id,
      label: f.name,
    })) ?? [];

  return (
    <Paper withBorder p="md">
      <Group justify="space-between" mb="sm">
        <Title order={4}>{page ? "Edit page" : "New page"}</Title>
        <Button variant="default" size="xs" onClick={onClose}>
          Close
        </Button>
      </Group>

      <Stack gap="md">
        <Group grow>
          <TextInput
            label="Page name"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
          />
          <TextInput
            label="Page title"
            value={title}
            onChange={(e) => setTitle(e.currentTarget.value)}
          />
          <Select
            label="Start from template"
            placeholder="Choose a template"
            data={TEMPLATES.map((t) => ({ value: t.key, label: t.name }))}
            onChange={applyTemplate}
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
                    No blocks yet. Add content from the palette or pick a template.
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

                    {(block.type === "heading" ||
                      block.type === "text" ||
                      block.type === "button") && (
                      <Textarea
                        size="xs"
                        label="Content"
                        autosize
                        minRows={2}
                        value={block.content ?? ""}
                        onChange={(e) =>
                          updateBlock(idx, { content: e.currentTarget.value })
                        }
                      />
                    )}

                    {block.type === "heading" && (
                      <Select
                        size="xs"
                        label="Level"
                        mt={6}
                        data={["1", "2", "3"]}
                        value={String(block.level ?? 2)}
                        onChange={(v) =>
                          updateBlock(idx, { level: Number(v ?? 2) })
                        }
                      />
                    )}

                    {block.type === "button" && (
                      <TextInput
                        size="xs"
                        label="URL"
                        mt={6}
                        value={block.url ?? ""}
                        onChange={(e) =>
                          updateBlock(idx, { url: e.currentTarget.value })
                        }
                      />
                    )}

                    {block.type === "image" && (
                      <TextInput
                        size="xs"
                        label="Image URL"
                        value={block.src ?? ""}
                        onChange={(e) =>
                          updateBlock(idx, { src: e.currentTarget.value })
                        }
                      />
                    )}

                    {block.type === "spacer" && (
                      <TextInput
                        size="xs"
                        label="Height (px)"
                        type="number"
                        mt={6}
                        value={String(block.height ?? 32)}
                        onChange={(e) =>
                          updateBlock(idx, {
                            height: Number(e.currentTarget.value) || 0,
                          })
                        }
                      />
                    )}

                    {block.type === "form_embed" && (
                      <Select
                        size="xs"
                        label="Form"
                        mt={6}
                        placeholder="Select a published form"
                        data={formOptions}
                        value={block.form_slug ?? null}
                        onChange={(v) => updateBlock(idx, { form_slug: v })}
                      />
                    )}
                  </Paper>
                ))}
              </Stack>
            </Group>
          </Tabs.Panel>

          <Tabs.Panel value="preview" pt="md">
            <Paper withBorder p="md" bg="gray.0">
              <PagePreview title={title} blocks={blocks} />
            </Paper>
          </Tabs.Panel>
        </Tabs>

        <Group justify="flex-end">
          <Button
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
          >
            Save page
          </Button>
        </Group>
        {saveMutation.isError && (
          <Text color="red" size="sm">
            Failed to save page
          </Text>
        )}
      </Stack>
    </Paper>
  );
}

function PagePreview({
  title,
  blocks,
}: {
  title?: string;
  blocks: PageBlock[];
}) {
  return (
    <Box>
      {title && <Title order={3}>{title}</Title>}
      <Stack gap="sm" mt="xs">
        {blocks.map((block, idx) => {
          switch (block.type) {
            case "heading":
              return (
                <Title key={idx} order={(block.level as 1 | 2 | 3) ?? 2}>
                  {block.content}
                </Title>
              );
            case "text":
              return (
                <Text key={idx}>{block.content}</Text>
              );
            case "image":
              return block.src ? (
                <img
                  key={idx}
                  src={block.src}
                  alt={block.content ?? ""}
                  style={{ maxWidth: "100%" }}
                />
              ) : (
                <Paper key={idx} withBorder p="md" color="dimmed">
                  <Text size="sm" color="dimmed">
                    Image (no URL set)
                  </Text>
                </Paper>
              );
            case "button":
              return (
                <Button
                  key={idx}
                  component="a"
                  href={block.url ?? "#"}
                  target="_blank"
                >
                  {block.content}
                </Button>
              );
            case "spacer":
              return (
                <Box
                  key={idx}
                  style={{ height: block.height ?? 32 }}
                />
              );
            case "form_embed":
              return (
                <Paper key={idx} withBorder p="md">
                  <Text size="sm" color="dimmed">
                    {block.form_slug
                      ? `Embedded form: ${block.form_slug}`
                      : "Form embed (choose a form)"}
                  </Text>
                </Paper>
              );
            default:
              return null;
          }
        })}
      </Stack>
    </Box>
  );
}

export default function Pages() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Page | null>(null);
  const [creating, { open: openCreate, close: closeCreate }] = useDisclosure(false);

  const pagesQuery = useQuery({ queryKey: ["pages"], queryFn: listPages });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePage(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pages"] }),
  });

  const rows = pagesQuery.data ?? [];

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Pages</Title>
        <Button onClick={openCreate}>+ New page</Button>
      </Group>

      {creating && (
        <PageBuilder
          page={null}
          onClose={() => {
            closeCreate();
          }}
        />
      )}
      {editing && (
        <PageBuilder
          page={editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}

      {!creating && !editing && (
        <Stack gap="md">
          {rows.length === 0 ? (
            <Paper withBorder p="md">
              <Text color="dimmed">No pages yet. Create your first landing page.</Text>
            </Paper>
          ) : (
            rows.map((p) => (
              <Paper key={p.id} withBorder p="md">
                <Group justify="space-between">
                  <Box>
                    <Group gap={8}>
                      <Text fw={600}>{p.name}</Text>
                      {p.published_slug && (
                        <Badge
                          variant="outline"
                          component="a"
                          href={`${API_URL}/p/${p.published_slug}`}
                          target="_blank"
                        >
                          Live
                        </Badge>
                      )}
                    </Group>
                    <Text size="xs" color="dimmed">
                      {(p.definition?.blocks ?? []).length} blocks
                    </Text>
                  </Box>
                  <Group gap={4}>
                    <Button size="xs" variant="subtle" onClick={() => setEditing(p)}>
                      Edit
                    </Button>
                    <Button
                      size="xs"
                      variant="subtle"
                      color="red"
                      onClick={() => deleteMutation.mutate(p.id)}
                    >
                      Delete
                    </Button>
                  </Group>
                </Group>
                <Divider my="sm" />
                <PublishInfo page={p} />
              </Paper>
            ))
          )}
        </Stack>
      )}
    </Stack>
  );
}
