import { Group, Text } from '@mantine/core';
import { IconMovie } from '@tabler/icons-react';

export default function Logo() {
  return (
    <Group gap={8} align="center">
      <IconMovie size={22} color="#e2b04a" stroke={1.5} />
      <Text fw={700} size="lg" style={{ color: '#e2b04a', letterSpacing: '0.03em' }}>
        CinemaList
      </Text>
    </Group>
  );
}
