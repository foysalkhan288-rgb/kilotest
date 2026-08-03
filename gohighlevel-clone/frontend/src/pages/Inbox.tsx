import { useState } from "react";
import {
  Badge,
  Box,
  Group,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { getConversation, listConversations } from "../api/inbox";

export default function Inbox() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const conversationsQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
  });

  const threadQuery = useQuery({
    queryKey: ["conversation", selectedId],
    queryFn: () => getConversation(selectedId as string),
    enabled: !!selectedId,
  });

  const conversations = conversationsQuery.data ?? [];
  const thread = threadQuery.data;

  return (
    <Stack gap="md" style={{ height: "calc(100vh - 90px)" }}>
      <Title order={2}>Inbox</Title>
      <Group align="flex-start" gap="md" grow style={{ flex: 1, minHeight: 0 }}>
        <Paper withBorder radius="md" p="xs" style={{ flex: "0 0 320px", minHeight: 0 }}>
          <Title order={5} mb="xs">
            Conversations
          </Title>
          <ScrollArea style={{ height: "100%" }} offsetScrollbars>
            {conversations.length === 0 ? (
              <Text color="dimmed" size="sm" p="xs">
                No conversations yet.
              </Text>
            ) : (
              <Stack gap={4}>
                {conversations.map((c) => (
                  <Paper
                    key={c.id}
                    withBorder={selectedId === c.id}
                    radius="sm"
                    p="xs"
                    style={{
                      cursor: "pointer",
                      backgroundColor:
                        selectedId === c.id ? "var(--mantine-color-gray-1)" : undefined,
                    }}
                    onClick={() => setSelectedId(c.id)}
                  >
                    <Group justify="space-between" wrap="nowrap">
                      <Box style={{ overflow: "hidden" }}>
                        <Text fw={600} truncate>
                          {c.contact_name}
                        </Text>
                        <Text size="xs" color="dimmed" truncate>
                          {c.last_message || "No messages"}
                        </Text>
                      </Box>
                      <Badge size="xs" variant="outline">
                        {c.channel}
                      </Badge>
                    </Group>
                  </Paper>
                ))}
              </Stack>
            )}
          </ScrollArea>
        </Paper>

        <Paper withBorder radius="md" p="md" style={{ flex: 1, minHeight: 0 }}>
          {!selectedId ? (
            <Text color="dimmed">Select a conversation to view messages.</Text>
          ) : threadQuery.isLoading ? (
            <Text color="dimmed">Loading…</Text>
          ) : thread ? (
            <Stack gap="md" style={{ height: "100%" }}>
              <Group justify="space-between">
                <Box>
                  <Text fw={700}>{thread.contact_name}</Text>
                  <Text size="sm" color="dimmed">
                    {thread.contact_email}
                  </Text>
                </Box>
              </Group>
              <ScrollArea style={{ flex: 1, minHeight: 0 }} offsetScrollbars>
                <Stack gap="sm">
                  {thread.messages.length === 0 && (
                    <Text color="dimmed" size="sm">
                      No messages.
                    </Text>
                  )}
                  {thread.messages.map((m) => (
                    <Paper
                      key={m.id}
                      radius="md"
                      p="sm"
                      style={{
                        maxWidth: "80%",
                        alignSelf:
                          m.direction === "out" ? "flex-end" : "flex-start",
                        backgroundColor:
                          m.direction === "out"
                            ? "var(--mantine-color-blue-1)"
                            : "var(--mantine-color-gray-1)",
                      }}
                    >
                      {m.subject && (
                        <Text size="xs" fw={600} mb={4}>
                          {m.subject}
                        </Text>
                      )}
                      <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                        {m.body}
                      </Text>
                      <Text size="xs" color="dimmed" mt={4}>
                        {m.created_at ? new Date(m.created_at).toLocaleString() : ""}
                      </Text>
                    </Paper>
                  ))}
                </Stack>
              </ScrollArea>
            </Stack>
          ) : (
            <Text color="red">Could not load conversation.</Text>
          )}
        </Paper>
      </Group>
    </Stack>
  );
}
