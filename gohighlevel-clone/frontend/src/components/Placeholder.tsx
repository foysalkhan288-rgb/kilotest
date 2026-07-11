import { Title, Text, Center, Stack } from "@mantine/core";

interface PlaceholderProps {
  title: string;
}

export default function Placeholder({ title }: PlaceholderProps) {
  return (
    <Center mih="70vh">
      <Stack align="center" gap="xs">
        <Title order={2}>{title}</Title>
        <Text color="dimmed">TODO: implemented in Wave 2</Text>
      </Stack>
    </Center>
  );
}
