import { Center, Text, Stack } from '@mantine/core';
import { IconMovie } from '@tabler/icons-react';

export default function PosterFallback({ title, size = 'md' }) {
  const h = size === 'lg' ? 360 : 180;
  return (
    <Center
      style={{
        background: '#242424',
        width: '100%',
        height: h,
        borderRadius: 8,
        border: '1px solid #2e2e2e',
      }}
    >
      <Stack align="center" gap="xs">
        <IconMovie size={32} color="#424242" />
        <Text size="xs" c="dimmed" ta="center" maw={120} lineClamp={2}>{title}</Text>
      </Stack>
    </Center>
  );
}
