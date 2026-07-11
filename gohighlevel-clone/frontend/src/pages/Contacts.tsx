import { useMemo, useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Divider,
  Drawer,
  Group,
  Modal,
  Paper,
  ScrollArea,
  Select,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createContact,
  deleteContact,
  getContactOpportunities,
  getContactTasks,
  listContacts,
  updateContact,
  updateContactTags,
  type Contact,
  type ContactPayload,
} from "../api/contacts";
import { createTag, listTags, type Tag } from "../api/tags";

function fullName(c: Contact): string {
  const name = `${c.firstname ?? ""} ${c.lastname ?? ""}`.trim();
  return name || c.email || "(no name)";
}

export default function Contacts() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<Contact | null>(null);

  const [createOpened, { open: openCreate, close: closeCreate }] =
    useDisclosure(false);
  const [drawerOpened, { open: openDrawer, close: closeDrawer }] =
    useDisclosure(false);

  const tagsQuery = useQuery({ queryKey: ["tags"], queryFn: listTags });
  const tags = tagsQuery.data ?? [];

  const contactsQuery = useQuery({
    queryKey: ["contacts", search, tagFilter],
    queryFn: () =>
      listContacts({
        search: search || undefined,
        tag: tagFilter || undefined,
      }),
  });
  const contacts = contactsQuery.data ?? [];

  const openDetail = (contact: Contact) => {
    setSelected(contact);
    openDrawer();
  };

  const invalidateContacts = () =>
    queryClient.invalidateQueries({ queryKey: ["contacts"] });

  const tagOptions = useMemo(
    () => tags.map((t: Tag) => ({ value: t.name, label: t.name })),
    [tags]
  );

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Contacts</Title>
        <Button onClick={openCreate}>+ New contact</Button>
      </Group>

      <Group gap="sm">
        <TextInput
          placeholder="Search name, email, phone, company…"
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          sx={{ flex: 1 }}
        />
        <Select
          placeholder="Filter by tag"
          data={tagOptions}
          value={tagFilter}
          onChange={setTagFilter}
          clearable
          searchable
          sx={{ minWidth: 200 }}
        />
      </Group>

      <Paper withBorder>
        <ScrollArea>
          <Table striped highlightOnHover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Company</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {contacts.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <Text color="dimmed" p="md">
                      No contacts found.
                    </Text>
                  </td>
                </tr>
              ) : (
                contacts.map((c) => (
                  <tr
                    key={c.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => openDetail(c)}
                  >
                    <td>{fullName(c)}</td>
                    <td>{c.email}</td>
                    <td>{c.phone}</td>
                    <td>{c.company}</td>
                    <td>
                      <Group gap={4}>
                        {c.tags.map((t) => (
                          <Badge key={t} variant="light" size="sm">
                            {t}
                          </Badge>
                        ))}
                      </Group>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </ScrollArea>
      </Paper>

      <ContactCreateModal
        opened={createOpened}
        onClose={closeCreate}
        onCreated={() => {
          invalidateContacts();
          closeCreate();
        }}
        tags={tags}
      />

      <ContactDetailDrawer
        opened={drawerOpened}
        onClose={closeDrawer}
        contact={selected}
        tags={tags}
        onChanged={(updated) => {
          setSelected(updated);
          invalidateContacts();
        }}
        onDeleted={() => {
          setSelected(null);
          closeDrawer();
          invalidateContacts();
        }}
      />
    </Stack>
  );
}

// ---------------------------------------------------------------------------
// Create modal
// ---------------------------------------------------------------------------
function ContactCreateModal({
  opened,
  onClose,
  onCreated,
  tags,
}: {
  opened: boolean;
  onClose: () => void;
  onCreated: () => void;
  tags: Tag[];
}) {
  const [form, setForm] = useState<ContactPayload>({
    firstname: "",
    lastname: "",
    email: "",
    phone: "",
    company: "",
    tags: [],
    notes: "",
  });
  const [tagInput, setTagInput] = useState("");

  const set = (key: keyof ContactPayload, value: unknown) =>
    setForm((f) => ({ ...f, [key]: value }));

  const addTag = () => {
    const t = tagInput.trim();
    if (t && !form.tags?.includes(t)) set("tags", [...(form.tags ?? []), t]);
    setTagInput("");
  };

  const mutation = useMutation({
    mutationFn: () => createContact(form),
    onSuccess: onCreated,
  });

  const reset = () => {
    setForm({
      firstname: "",
      lastname: "",
      email: "",
      phone: "",
      company: "",
      tags: [],
      notes: "",
    });
    setTagInput("");
  };

  return (
    <Modal
      opened={opened}
      onClose={() => {
        reset();
        onClose();
      }}
      title="New contact"
      size="md"
    >
      <Stack>
        <Group grow>
          <TextInput
            label="First name"
            value={form.firstname ?? ""}
            onChange={(e) => set("firstname", e.currentTarget.value)}
          />
          <TextInput
            label="Last name"
            value={form.lastname ?? ""}
            onChange={(e) => set("lastname", e.currentTarget.value)}
          />
        </Group>
        <TextInput
          label="Email"
          value={form.email ?? ""}
          onChange={(e) => set("email", e.currentTarget.value)}
        />
        <Group grow>
          <TextInput
            label="Phone"
            value={form.phone ?? ""}
            onChange={(e) => set("phone", e.currentTarget.value)}
          />
          <TextInput
            label="Company"
            value={form.company ?? ""}
            onChange={(e) => set("company", e.currentTarget.value)}
          />
        </Group>

        <Box>
          <Text size="sm" fw={500} mb={4}>
            Tags
          </Text>
          <Group gap={4} mb="xs">
            {(form.tags ?? []).map((t) => (
              <Badge
                key={t}
                variant="light"
                rightSection={
                  <ActionIcon
                    size="xs"
                    variant="transparent"
                    onClick={() =>
                      set(
                        "tags",
                        (form.tags ?? []).filter((x) => x !== t)
                      )
                    }
                    aria-label={`Remove ${t}`}
                  >
                    ✕
                  </ActionIcon>
                }
              >
                {t}
              </Badge>
            ))}
          </Group>
          <Group gap={4}>
            <Select
              placeholder="Add tag"
              data={tags.map((t) => ({ value: t.name, label: t.name }))}
              value={tagInput || null}
              onChange={(v) => setTagInput(v ?? "")}
              searchable
              creatable
              getCreateLabel={(q) => `+ Create "${q}"`}
              onCreate={(q) => {
                if (!(form.tags ?? []).includes(q)) {
                  set("tags", [...(form.tags ?? []), q]);
                }
                setTagInput("");
                return { value: q, label: q };
              }}
              sx={{ flex: 1 }}
            />
            <Button size="xs" variant="light" onClick={addTag}>
              Add
            </Button>
          </Group>
        </Box>

        <Textarea
          label="Notes"
          autosize
          minRows={3}
          value={form.notes ?? ""}
          onChange={(e) => set("notes", e.currentTarget.value)}
        />

        <Group justify="flex-end">
          <Button
            variant="default"
            onClick={() => {
              reset();
              onClose();
            }}
          >
            Cancel
          </Button>
          <Button onClick={() => mutation.mutate()} loading={mutation.isPending}>
            Create
          </Button>
        </Group>
        {mutation.isError && (
          <Text color="red" size="sm">
            Failed to create contact.
          </Text>
        )}
      </Stack>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Detail drawer
// ---------------------------------------------------------------------------
function ContactDetailDrawer({
  opened,
  onClose,
  contact,
  tags,
  onChanged,
  onDeleted,
}: {
  opened: boolean;
  onClose: () => void;
  contact: Contact | null;
  tags: Tag[];
  onChanged: (c: Contact) => void;
  onDeleted: () => void;
}) {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [tagInput, setTagInput] = useState("");

  // Sync local notes state when a new contact is opened.
  const [activeId, setActiveId] = useState<string | null>(null);
  if (contact && contact.id !== activeId) {
    setActiveId(contact.id);
    setNotes(contact.notes ?? "");
    setTagInput("");
  }

  const field = (label: string, value: string | null) => (
    <Box>
      <Text size="xs" color="dimmed" fw={500}>
        {label}
      </Text>
      <Text size="sm">{value || "—"}</Text>
    </Box>
  );

  const tasksQuery = useQuery({
    queryKey: ["contact-tasks", contact?.id],
    queryFn: () => getContactTasks(contact!.id),
    enabled: !!contact,
  });
  const oppsQuery = useQuery({
    queryKey: ["contact-opps", contact?.id],
    queryFn: () => getContactOpportunities(contact!.id),
    enabled: !!contact,
  });

  const notesMutation = useMutation({
    mutationFn: (value: string) =>
      updateContact(contact!.id, { notes: value }),
    onSuccess: (updated) => {
      onChanged(updated);
      queryClient.invalidateQueries({ queryKey: ["contact-tasks", contact!.id] });
    },
  });

  const tagMutation = useMutation({
    mutationFn: (args: { tag: string; action: "add" | "remove" }) =>
      updateContactTags(contact!.id, args.tag, args.action),
    onSuccess: (updated) => onChanged(updated),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteContact(contact!.id),
    onSuccess: onDeleted,
  });

  const addTag = () => {
    const t = (tagInput || "").trim();
    if (!t) return;
    tagMutation.mutate({ tag: t, action: "add" });
    setTagInput("");
  };

  const createAndAddTag = async () => {
    const t = (tagInput || "").trim();
    if (!t) return;
    try {
      await createTag({ name: t });
      queryClient.invalidateQueries({ queryKey: ["tags"] });
    } catch {
      /* tag may already exist */
    }
    tagMutation.mutate({ tag: t, action: "add" });
    setTagInput("");
  };

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      title={contact ? fullName(contact) : "Contact"}
      size="md"
      justify="flex-end"
    >
      {contact && (
        <Stack gap="md">
          <Group gap="sm" grow>
            {field("First name", contact.firstname)}
            {field("Last name", contact.lastname)}
          </Group>
          {field("Email", contact.email)}
          <Group gap="sm" grow>
            {field("Phone", contact.phone)}
            {field("Company", contact.company)}
          </Group>

          <Divider label="Tags" labelPosition="center" />
          <Group gap={4}>
            {contact.tags.map((t) => (
              <Badge
                key={t}
                variant="light"
                rightSection={
                  <ActionIcon
                    size="xs"
                    variant="transparent"
                    onClick={() => tagMutation.mutate({ tag: t, action: "remove" })}
                    aria-label={`Remove ${t}`}
                  >
                    ✕
                  </ActionIcon>
                }
              >
                {t}
              </Badge>
            ))}
          </Group>
          <Group gap={4}>
            <Select
              placeholder="Add tag"
              data={tags.map((t) => ({ value: t.name, label: t.name }))}
              value={tagInput || null}
              onChange={(v) => setTagInput(v ?? "")}
              searchable
              creatable
              getCreateLabel={(q) => `+ Create "${q}"`}
              onCreate={(q) => {
                setTagInput(q);
                createAndAddTag();
                return { value: q, label: q };
              }}
              sx={{ flex: 1 }}
            />
            <Button size="xs" variant="light" onClick={addTag} loading={tagMutation.isPending}>
              Add
            </Button>
          </Group>

          <Divider label="Notes" labelPosition="center" />
          <Textarea
            autosize
            minRows={4}
            value={notes}
            onChange={(e) => setNotes(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              size="xs"
              onClick={() => notesMutation.mutate(notes)}
              loading={notesMutation.isPending}
            >
              Save notes
            </Button>
          </Group>

          <Divider label="Tasks" labelPosition="center" />
          <Stack gap={4}>
            {(tasksQuery.data ?? []).length === 0 ? (
              <Text color="dimmed" size="sm">
                No tasks.
              </Text>
            ) : (
              (tasksQuery.data ?? []).map((t) => (
                <Paper key={t.id} withBorder p="xs">
                  <Group justify="space-between">
                    <Text size="sm">{t.title}</Text>
                    <Badge color={t.done ? "green" : "gray"} variant="light">
                      {t.done ? "done" : "open"}
                    </Badge>
                  </Group>
                </Paper>
              ))
            )}
          </Stack>

          <Divider label="Opportunities" labelPosition="center" />
          <Stack gap={4}>
            {(oppsQuery.data ?? []).length === 0 ? (
              <Text color="dimmed" size="sm">
                No linked opportunities.
              </Text>
            ) : (
              (oppsQuery.data ?? []).map((o) => (
                <Paper key={o.id} withBorder p="xs">
                  <Group justify="space-between">
                    <Text size="sm">{o.name}</Text>
                    <Group gap={6}>
                      <Badge variant="light">
                        {o.value != null
                          ? `$${o.value.toLocaleString()}`
                          : "—"}
                      </Badge>
                      <Badge color="blue" variant="outline">
                        {o.status ?? "open"}
                      </Badge>
                    </Group>
                  </Group>
                </Paper>
              ))
            )}
          </Stack>

          <Divider />
          <Group justify="flex-end">
            <Button
              color="red"
              variant="subtle"
              onClick={() => deleteMutation.mutate()}
              loading={deleteMutation.isPending}
            >
              Delete contact
            </Button>
          </Group>
        </Stack>
      )}
    </Drawer>
  );
}
