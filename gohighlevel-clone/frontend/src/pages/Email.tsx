import { useState } from "react";
import {
  Box,
  Button,
  Card,
  Group,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput,
  Title,
  Badge,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listContacts,
  listEmails,
  sendCampaign,
  sendEmail,
  type EmailItem,
} from "../api/email";
import type { ContactItem } from "../api/contacts";

export default function Email() {
  const queryClient = useQueryClient();

  const [contactId, setContactId] = useState<string | null>(null);
  const [toEmail, setToEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [campaignSubject, setCampaignSubject] = useState("");
  const [campaignBody, setCampaignBody] = useState("");
  const [campaignTag, setCampaignTag] = useState<string | null>(null);

  const contactsQuery = useQuery({ queryKey: ["contacts"], queryFn: listContacts });
  const emailsQuery = useQuery({ queryKey: ["emails"], queryFn: listEmails });

  const sendMutation = useMutation({
    mutationFn: () =>
      sendEmail({
        to_email: toEmail,
        subject,
        html: body,
        contact_id: contactId,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      setToEmail("");
      setSubject("");
      setBody("");
    },
  });

  const campaignMutation = useMutation({
    mutationFn: () =>
      sendCampaign({
        subject: campaignSubject,
        html: campaignBody,
        tag: campaignTag,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      setCampaignSubject("");
      setCampaignBody("");
      setCampaignTag(null);
    },
  });

  const contactOptions =
    contactsQuery.data?.map((c: ContactItem) => ({
      value: c.id,
      label: `${c.firstname ?? ""} ${c.lastname ?? ""}`.trim() || c.email || c.id,
    })) ?? [];

  const selectedContact = contactsQuery.data?.find((c) => c.id === contactId);
  const effectiveTo = toEmail || selectedContact?.email || "";

  const emails: EmailItem[] = emailsQuery.data ?? [];

  return (
    <Stack gap="md">
      <Title order={2}>Email</Title>

      <Group align="flex-start" grow>
        <Card withBorder radius="md" p="md">
          <Title order={4} mb="sm">
            Compose
          </Title>
          <Stack>
            <Select
              label="Contact (optional)"
              placeholder="Select a contact"
              data={contactOptions}
              value={contactId}
              onChange={setContactId}
              searchable
              clearable
            />
            <TextInput
              label="To email"
              placeholder="customer@example.com"
              value={toEmail}
              onChange={(e) => setToEmail(e.currentTarget.value)}
              disabled={!!selectedContact?.email}
            />
            <TextInput
              label="Subject"
              value={subject}
              onChange={(e) => setSubject(e.currentTarget.value)}
            />
            <Textarea
              label="Body (HTML)"
              autosize
              minRows={6}
              value={body}
              onChange={(e) => setBody(e.currentTarget.value)}
            />
            <Group justify="flex-end">
              <Button
                onClick={() => sendMutation.mutate()}
                loading={sendMutation.isPending}
                disabled={!effectiveTo || !subject}
              >
                Send
              </Button>
            </Group>
            {sendMutation.isSuccess && (
              <Badge color={sendMutation.data?.status === "sent" ? "green" : "red"}>
                {sendMutation.data?.status === "sent"
                  ? "Email sent"
                  : "Queued (failed to deliver)"}
              </Badge>
            )}
            {sendMutation.isError && (
              <Text color="red" size="sm">
                Failed to send
              </Text>
            )}
          </Stack>
        </Card>

        <Card withBorder radius="md" p="md">
          <Title order={4} mb="sm">
            Campaign
          </Title>
          <Stack>
            <TextInput
              label="Subject"
              value={campaignSubject}
              onChange={(e) => setCampaignSubject(e.currentTarget.value)}
            />
            <Textarea
              label="Body (HTML)"
              autosize
              minRows={6}
              value={campaignBody}
              onChange={(e) => setCampaignBody(e.currentTarget.value)}
            />
            <TextInput
              label="Tag (optional)"
              placeholder="Only contacts with this tag"
              value={campaignTag ?? ""}
              onChange={(e) => setCampaignTag(e.currentTarget.value || null)}
            />
            <Group justify="flex-end">
              <Button
                variant="light"
                onClick={() => campaignMutation.mutate()}
                loading={campaignMutation.isPending}
                disabled={!campaignSubject}
              >
                Send Campaign
              </Button>
            </Group>
            {campaignMutation.isSuccess && (
              <Badge color="blue">
                Sent {campaignMutation.data?.sent} / {campaignMutation.data?.total}
              </Badge>
            )}
          </Stack>
        </Card>
      </Group>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="sm">
          Sent emails
        </Title>
        {emails.length === 0 ? (
          <Text color="dimmed">No emails yet.</Text>
        ) : (
          <Box style={{ overflowX: "auto" }}>
            <Table striped highlightOnHover withBorder withColumnBorders>
              <thead>
                <tr>
                  <th>To</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Sent at</th>
                </tr>
              </thead>
              <tbody>
                {emails.map((e) => (
                  <tr key={e.id}>
                    <td>{e.contact_id ?? "—"}</td>
                    <td>{e.subject ?? "—"}</td>
                    <td>
                      <Badge color={e.status === "sent" ? "green" : "red"}>
                        {e.status}
                      </Badge>
                    </td>
                    <td>{e.sent_at ? new Date(e.sent_at).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Box>
        )}
      </Paper>
    </Stack>
  );
}
