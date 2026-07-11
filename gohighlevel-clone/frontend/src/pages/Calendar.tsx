import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Title,
  Text,
  Button,
  Table,
  Modal,
  TextInput,
  NumberInput,
  Stack,
  Group,
  Tabs,
  Select,
  Badge,
  Box,
  CopyButton,
  Tooltip,
  Paper,
  Switch,
  ScrollArea,
  Alert,
} from "@mantine/core";
import {
  listCalendars,
  createCalendar,
  updateCalendar,
  deleteCalendar,
  publicBookingUrl,
  type Availability,
  type CalendarItem,
  type CreateCalendarPayload,
} from "../api/calendars";
import {
  listAppointments,
  updateAppointment,
  APPOINTMENT_STATUSES,
  type AppointmentItem,
  type AppointmentStatus,
} from "../api/appointments";

const WEEKDAYS = [
  { key: "mon", label: "Monday" },
  { key: "tue", label: "Tuesday" },
  { key: "wed", label: "Wednesday" },
  { key: "thu", label: "Thursday" },
  { key: "fri", label: "Friday" },
  { key: "sat", label: "Saturday" },
  { key: "sun", label: "Sunday" },
];

interface AvailabilityForm {
  timezone: string;
  slot_minutes: number;
  days: Record<string, { enabled: boolean; start: number; end: number }>;
}

function emptyAvailability(): AvailabilityForm {
  const days: AvailabilityForm["days"] = {};
  for (const d of WEEKDAYS) {
    days[d.key] = { enabled: d.key !== "sat" && d.key !== "sun", start: 9, end: 17 };
  }
  return { timezone: "UTC", slot_minutes: 30, days };
}

function availabilityToForm(av: Availability | null | undefined): AvailabilityForm {
  const base = emptyAvailability();
  if (av && typeof av === "object") {
    if (typeof av.timezone === "string") base.timezone = av.timezone;
    if (typeof av.slot_minutes === "number") base.slot_minutes = av.slot_minutes;
    if (av.days && typeof av.days === "object") {
      for (const d of WEEKDAYS) {
        const range = av.days[d.key];
        if (Array.isArray(range) && range.length === 2) {
          base.days[d.key] = {
            enabled: true,
            start: Number(range[0]),
            end: Number(range[1]),
          };
        }
      }
    }
  }
  return base;
}

function formToAvailability(form: AvailabilityForm): Availability {
  const days: Record<string, number[]> = {};
  for (const d of WEEKDAYS) {
    const entry = form.days[d.key];
    if (entry.enabled) {
      days[d.key] = [entry.start, entry.end];
    }
  }
  return { timezone: form.timezone, slot_minutes: form.slot_minutes, days };
}

function contactName(c: AppointmentItem["contact"]): string {
  if (!c) return "—";
  const full = `${c.firstname ?? ""} ${c.lastname ?? ""}`.trim();
  return full || c.email || "—";
}

export default function Calendar() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<string | null>("calendars");

  const calendarsQuery = useQuery({
    queryKey: ["calendars"],
    queryFn: listCalendars,
  });

  const appointmentsQuery = useQuery({
    queryKey: ["appointments"],
    queryFn: () => listAppointments(),
  });

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<CalendarItem | null>(null);
  const [name, setName] = useState("");
  const [availability, setAvailability] = useState<AvailabilityForm>(
    emptyAvailability()
  );
  const [error, setError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: async (payload: CreateCalendarPayload) => {
      if (editing) return updateCalendar(editing.id, payload);
      return createCalendar(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calendars"] });
      setModalOpen(false);
      setEditing(null);
      setError(null);
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail ?? "Failed to save calendar");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCalendar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["calendars"] }),
  });

  const openCreate = () => {
    setEditing(null);
    setName("");
    setAvailability(emptyAvailability());
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (cal: CalendarItem) => {
    setEditing(cal);
    setName(cal.name);
    setAvailability(availabilityToForm(cal.availability));
    setError(null);
    setModalOpen(true);
  };

  const handleSave = () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    saveMutation.mutate({
      name: name.trim(),
      availability: formToAvailability(availability),
    });
  };

  const setDay = (key: string, patch: Partial<AvailabilityForm["days"][string]>) => {
    setAvailability((prev) => ({
      ...prev,
      days: { ...prev.days, [key]: { ...prev.days[key], ...patch } },
    }));
  };

  const calendarRows = useMemo(() => calendarsQuery.data ?? [], [calendarsQuery.data]);

  return (
    <Box p="md">
      <Group justify="space-between" mb="md">
        <Title order={2}>Calendar &amp; Appointments</Title>
        {activeTab === "calendars" && (
          <Button onClick={openCreate}>New Calendar</Button>
        )}
      </Group>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List mb="md">
          <Tabs.Tab value="calendars">Calendars</Tabs.Tab>
          <Tabs.Tab value="appointments">Appointments</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="calendars">
          <Paper withBorder p="md">
            {calendarsQuery.isLoading ? (
              <Text>Loading…</Text>
            ) : calendarRows.length === 0 ? (
              <Text color="dimmed">
                No calendars yet. Create one to get a public booking link.
              </Text>
            ) : (
              <ScrollArea>
                <Table striped highlightOnHover>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Public booking link</th>
                      <th>Availability</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calendarRows.map((cal) => (
                      <tr key={cal.id}>
                        <td>{cal.name}</td>
                        <td>
                          {cal.public_slug ? (
                            <Group gap="xs" wrap="nowrap">
                              <Text size="sm" style={{ maxWidth: 280 }} truncate>
                                {publicBookingUrl(cal.public_slug)}
                              </Text>
                              <CopyButton
                                value={publicBookingUrl(cal.public_slug)}
                                timeout={1500}
                              >
                                {({ copied, copy }) => (
                                  <Tooltip label={copied ? "Copied" : "Copy"}>
                                    <Button
                                      size="xs"
                                      variant="light"
                                      onClick={copy}
                                    >
                                      {copied ? "Copied" : "Copy"}
                                    </Button>
                                  </Tooltip>
                                )}
                              </CopyButton>
                            </Group>
                          ) : (
                            <Text color="dimmed" size="sm">
                              —
                            </Text>
                          )}
                        </td>
                        <td>
                          <Text size="sm">
                            {cal.availability?.slot_minutes ?? 30} min slots ·{" "}
                            {Object.keys(cal.availability?.days ?? {}).length} day(s)
                          </Text>
                        </td>
                        <td>
                          <Group gap="xs">
                            <Button
                              size="xs"
                              variant="light"
                              onClick={() => openEdit(cal)}
                            >
                              Edit
                            </Button>
                            <Button
                              size="xs"
                              color="red"
                              variant="light"
                              loading={
                                deleteMutation.isPending &&
                                deleteMutation.variables === cal.id
                              }
                              onClick={() => deleteMutation.mutate(cal.id)}
                            >
                              Delete
                            </Button>
                          </Group>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ScrollArea>
            )}
          </Paper>
        </Tabs.Panel>

        <Tabs.Panel value="appointments">
          <Paper withBorder p="md">
            {appointmentsQuery.isLoading ? (
              <Text>Loading…</Text>
            ) : (appointmentsQuery.data ?? []).length === 0 ? (
              <Text color="dimmed">No appointments yet.</Text>
            ) : (
              <ScrollArea>
                <Table striped highlightOnHover>
                  <thead>
                    <tr>
                      <th>Contact</th>
                      <th>Start</th>
                      <th>End</th>
                      <th>Status</th>
                      <th>Change status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(appointmentsQuery.data ?? []).map((appt) => (
                      <AppointmentRow
                        key={appt.id}
                        appt={appt}
                        queryClient={queryClient}
                      />
                    ))}
                  </tbody>
                </Table>
              </ScrollArea>
            )}
          </Paper>
        </Tabs.Panel>
      </Tabs>

      <Modal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Edit Calendar" : "New Calendar"}
        size="lg"
      >
        <Stack>
          {error && <Alert color="red">{error}</Alert>}
          <TextInput
            label="Name"
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            placeholder="Sales Discovery Call"
            required
          />
          <Group grow>
            <TextInput
              label="Timezone"
              value={availability.timezone}
              onChange={(e) =>
                setAvailability((p) => ({ ...p, timezone: e.currentTarget.value }))
              }
            />
            <NumberInput
              label="Slot length (minutes)"
              min={5}
              max={240}
              step={5}
              value={availability.slot_minutes}
              onChange={(v) =>
                setAvailability((p) => ({ ...p, slot_minutes: Number(v) || 30 }))
              }
            />
          </Group>
          <Text size="sm" fw={600}>
            Working hours
          </Text>
          <Stack gap="xs">
            {WEEKDAYS.map((d) => {
              const day = availability.days[d.key];
              return (
                <Group key={d.key} gap="sm" wrap="nowrap">
                  <Switch
                    checked={day.enabled}
                    onChange={(e) => setDay(d.key, { enabled: e.currentTarget.checked })}
                    label={d.label}
                    style={{ width: 120 }}
                  />
                  <NumberInput
                    w={90}
                    min={0}
                    max={23}
                    disabled={!day.enabled}
                    value={day.start}
                    onChange={(v) => setDay(d.key, { start: Number(v) || 0 })}
                  />
                  <Text>to</Text>
                  <NumberInput
                    w={90}
                    min={0}
                    max={24}
                    disabled={!day.enabled}
                    value={day.end}
                    onChange={(v) => setDay(d.key, { end: Number(v) || 0 })}
                  />
                </Group>
              );
            })}
          </Stack>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} loading={saveMutation.isPending}>
              Save
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}

function AppointmentRow({
  appt,
  queryClient,
}: {
  appt: AppointmentItem;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const mutation = useMutation({
    mutationFn: (status: AppointmentStatus) =>
      updateAppointment(appt.id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appointments"] }),
  });

  return (
    <tr>
      <td>{contactName(appt.contact)}</td>
      <td>{appt.start ? new Date(appt.start).toLocaleString() : "—"}</td>
      <td>{appt.end ? new Date(appt.end).toLocaleString() : "—"}</td>
      <td>
        <Badge color={appt.status === "no_show" ? "red" : "blue"}>
          {appt.status ?? "—"}
        </Badge>
      </td>
      <td>
        <Select
          w={160}
          data={APPOINTMENT_STATUSES.map((s) => ({ value: s, label: s }))}
          value={appt.status ?? ""}
          onChange={(value) => {
            if (value) mutation.mutate(value as AppointmentStatus);
          }}
          placeholder="Set status"
        />
      </td>
    </tr>
  );
}
