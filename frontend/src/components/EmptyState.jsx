import { Stack, Text, ThemeIcon } from '@mantine/core';

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <Stack align="center" gap="sm" py={64}>
      <ThemeIcon size={56} radius="xl" variant="light" color="yellow">
        <Icon size={28} stroke={1.2} />
      </ThemeIcon>
      <Text fw={600} size="lg" style={{ color: '#e8e8e8' }}>{title}</Text>
      {description && <Text c="dimmed" size="sm" ta="center" maw={340}>{description}</Text>}
      {action}
    </Stack>
  );
}
