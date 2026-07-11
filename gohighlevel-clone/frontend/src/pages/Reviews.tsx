import { useState } from "react";
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Card,
  Group,
  Modal,
  Paper,
  Rating,
  Select,
  Stack,
  Table,
  Text,
  Textarea,
  Title,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createReview,
  listContactsForReview,
  listReviews,
  requestReview,
  respondReview,
  type ReviewItem,
  type ReviewPlatform,
} from "../api/reviews";

const STATUS_COLORS: Record<string, string> = {
  requested: "yellow",
  responded: "green",
  received: "blue",
};

const PLATFORM_OPTIONS = [
  { value: "google", label: "Google" },
  { value: "facebook", label: "Facebook" },
];

function Stars({ value }: { value: number | null }) {
  if (value == null) return <Text color="dimmed">—</Text>;
  return <Badge color="yellow" variant="light">{value} / 5</Badge>;
}

export default function Reviews() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const [requestOpen, setRequestOpen] = useState(false);
  const [respondOpen, setRespondOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  const [requestContact, setRequestContact] = useState<string | null>(null);
  const [requestPlatform, setRequestPlatform] = useState<ReviewPlatform>("google");

  const [respondTarget, setRespondTarget] = useState<ReviewItem | null>(null);
  const [respondBody, setRespondBody] = useState("");
  const [respondRating, setRespondRating] = useState<number | null>(null);

  const [createContact, setCreateContact] = useState<string | null>(null);
  const [createPlatform, setCreatePlatform] = useState<ReviewPlatform>("google");
  const [createRating, setCreateRating] = useState<number | null>(null);
  const [createBody, setCreateBody] = useState("");

  const reviewsQuery = useQuery({
    queryKey: ["reviews", statusFilter],
    queryFn: () => listReviews(statusFilter ?? undefined),
  });
  const contactsQuery = useQuery({
    queryKey: ["contacts-for-review"],
    queryFn: listContactsForReview,
  });

  const reviews: ReviewItem[] = reviewsQuery.data ?? [];
  const contacts = contactsQuery.data ?? [];

  const contactOptions = contacts.map((c) => ({
    value: c.id,
    label: `${c.firstname ?? ""} ${c.lastname ?? ""}`.trim() || c.email || c.id,
    disabled: !c.email,
  }));

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["reviews"] });

  const requestMutation = useMutation({
    mutationFn: () => requestReview({ contact_id: requestContact!, platform: requestPlatform }),
    onSuccess: () => {
      refresh();
      setRequestOpen(false);
      setRequestContact(null);
      setRequestPlatform("google");
    },
  });

  const respondMutation = useMutation({
    mutationFn: () =>
      respondReview(respondTarget!.id, { body: respondBody, rating: respondRating }),
    onSuccess: () => {
      refresh();
      setRespondOpen(false);
      setRespondTarget(null);
      setRespondBody("");
      setRespondRating(null);
    },
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createReview({
        contact_id: createContact!,
        platform: createPlatform,
        rating: createRating,
        body: createBody,
      }),
    onSuccess: () => {
      refresh();
      setCreateOpen(false);
      setCreateContact(null);
      setCreatePlatform("google");
      setCreateRating(null);
      setCreateBody("");
    },
  });

  const openRespond = (review: ReviewItem) => {
    setRespondTarget(review);
    setRespondBody(review.body ?? "");
    setRespondRating(review.rating);
    setRespondOpen(true);
  };

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={2}>Reviews</Title>
        <Group>
          <Select
            placeholder="All statuses"
            data={[
              { value: "requested", label: "Requested" },
              { value: "responded", label: "Responded" },
              { value: "received", label: "Received" },
            ]}
            value={statusFilter}
            onChange={setStatusFilter}
            clearable
            w={180}
          />
          <Button variant="default" onClick={() => setCreateOpen(true)}>
            Log review
          </Button>
          <Button onClick={() => setRequestOpen(true)}>Request review</Button>
        </Group>
      </Group>

      <Paper withBorder radius="md" p="md">
        {reviewsQuery.isLoading ? (
          <Text color="dimmed">Loading…</Text>
        ) : reviews.length === 0 ? (
          <Text color="dimmed">No reviews yet.</Text>
        ) : (
          <Box style={{ overflowX: "auto" }}>
            <Table striped highlightOnHover withBorder withColumnBorders>
              <thead>
                <tr>
                  <th>Contact</th>
                  <th>Platform</th>
                  <th>Rating</th>
                  <th>Status</th>
                  <th>Body</th>
                  <th>Requested</th>
                  <th>Responded</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((r) => (
                  <tr key={r.id}>
                    <td>{r.contact_name ?? r.contact_email ?? "—"}</td>
                    <td>
                      <Badge variant="outline">{r.platform ?? "—"}</Badge>
                    </td>
                    <td>
                      <Stars value={r.rating} />
                    </td>
                    <td>
                      <Badge color={STATUS_COLORS[r.status ?? ""] ?? "gray"}>
                        {r.status ?? "—"}
                      </Badge>
                    </td>
                    <td style={{ maxWidth: 280 }}>{r.body ?? "—"}</td>
                    <td>
                      {r.requested_at ? new Date(r.requested_at).toLocaleDateString() : "—"}
                    </td>
                    <td>
                      {r.responded_at ? new Date(r.responded_at).toLocaleDateString() : "—"}
                    </td>
                    <td>
                      <ActionIcon
                        variant="subtle"
                        color="blue"
                        disabled={r.status === "responded"}
                        onClick={() => openRespond(r)}
                        title="Mark responded"
                      >
                        ✓
                      </ActionIcon>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Box>
        )}
      </Paper>

      {/* Request review modal */}
      <Modal
        opened={requestOpen}
        onClose={() => setRequestOpen(false)}
        title="Request a review"
      >
        <Stack>
          <Select
            label="Contact"
            placeholder="Select a contact"
            data={contactOptions}
            value={requestContact}
            onChange={setRequestContact}
            searchable
            withAsterisk
          />
          <Select
            label="Platform"
            data={PLATFORM_OPTIONS}
            value={requestPlatform}
            onChange={(v) => setRequestPlatform((v as ReviewPlatform) ?? "google")}
            withAsterisk
          />
          <Group justify="flex-end">
            <Button
              onClick={() => requestMutation.mutate()}
              loading={requestMutation.isPending}
              disabled={!requestContact}
            >
              Send request
            </Button>
          </Group>
          {requestMutation.isError && (
            <Text color="red" size="sm">
              Failed to send request.
            </Text>
          )}
          {requestMutation.isSuccess && (
            <Text color="green" size="sm">
              Review request sent.
            </Text>
          )}
        </Stack>
      </Modal>

      {/* Respond modal */}
      <Modal
        opened={respondOpen}
        onClose={() => setRespondOpen(false)}
        title="Respond to review"
      >
        <Stack>
          <div>
            <Text size="sm" color="dimmed">
              {respondTarget?.contact_name ?? respondTarget?.contact_email ?? ""}
            </Text>
          </div>
          <Rating value={respondRating ?? 0} onChange={setRespondRating} />
          <Textarea
            label="Response"
            autosize
            minRows={4}
            value={respondBody}
            onChange={(e) => setRespondBody(e.currentTarget.value)}
            withAsterisk
          />
          <Group justify="flex-end">
            <Button
              onClick={() => respondMutation.mutate()}
              loading={respondMutation.isPending}
              disabled={!respondBody}
            >
              Save response
            </Button>
          </Group>
          {respondMutation.isError && (
            <Text color="red" size="sm">
              Failed to save response.
            </Text>
          )}
        </Stack>
      </Modal>

      {/* Log review modal */}
      <Modal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Log a received review"
      >
        <Stack>
          <Select
            label="Contact"
            placeholder="Select a contact"
            data={contactOptions}
            value={createContact}
            onChange={setCreateContact}
            searchable
            withAsterisk
          />
          <Select
            label="Platform"
            data={PLATFORM_OPTIONS}
            value={createPlatform}
            onChange={(v) => setCreatePlatform((v as ReviewPlatform) ?? "google")}
            withAsterisk
          />
          <Rating value={createRating ?? 0} onChange={setCreateRating} />
          <Textarea
            label="Review body"
            autosize
            minRows={4}
            value={createBody}
            onChange={(e) => setCreateBody(e.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              onClick={() => createMutation.mutate()}
              loading={createMutation.isPending}
              disabled={!createContact}
            >
              Save review
            </Button>
          </Group>
          {createMutation.isError && (
            <Text color="red" size="sm">
              Failed to save review.
            </Text>
          )}
        </Stack>
      </Modal>
    </Stack>
  );
}
