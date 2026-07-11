import {
  Card,
  Group,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../api/dashboard";

function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}`;
}

function formatTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString();
}

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading || !data) {
    return <Text>Loading…</Text>;
  }

  return (
    <Stack gap="md">
      <Title order={2}>Dashboard</Title>

      <SimpleGrid columns={{ base: 1, sm: 3 }} gap="md">
        <Card withBorder p="md">
          <Group justify="space-between">
            <div>
              <Text size="xs" color="dimmed" fw={700} tt="uppercase">
                Total contacts
              </Text>
              <Text size="xl" fw={700}>
                {data.total_contacts}
              </Text>
            </div>
            <ThemeIcon variant="light" size={40} radius="md" color="blue">
              C
            </ThemeIcon>
          </Group>
        </Card>

        <Card withBorder p="md">
          <Group justify="space-between">
            <div>
              <Text size="xs" color="dimmed" fw={700} tt="uppercase">
                Open pipeline value
              </Text>
              <Text size="xl" fw={700}>
                {formatCurrency(data.open_pipeline_value)}
              </Text>
            </div>
            <ThemeIcon variant="light" size={40} radius="md" color="green">
              $
            </ThemeIcon>
          </Group>
        </Card>

        <Card withBorder p="md">
          <Group justify="space-between">
            <div>
              <Text size="xs" color="dimmed" fw={700} tt="uppercase">
                Appointments today
              </Text>
              <Text size="xl" fw={700}>
                {data.appointments_today}
              </Text>
            </div>
            <ThemeIcon variant="light" size={40} radius="md" color="orange">
              A
            </ThemeIcon>
          </Group>
        </Card>
      </SimpleGrid>

      <Card withBorder p="md">
        <Title order={4} mb="sm">
          Recent activity
        </Title>
        {data.recent_activity.length === 0 ? (
          <Text color="dimmed" size="sm">
            No activity yet.
          </Text>
        ) : (
          <Stack gap="xs">
            {data.recent_activity.map((item) => (
              <Group key={item.id} gap="sm" wrap={false}>
                <Text size="xs" color="dimmed" w={160}>
                  {formatTime(item.created_at)}
                </Text>
                <Text size="sm">{item.message}</Text>
              </Group>
            ))}
          </Stack>
        )}
      </Card>
    </Stack>
  );
}
