import { Card, Image, Text, Group, Rating, Box, Tooltip } from '@mantine/core';
import { IconHeartFilled } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { posterUrl } from '../api/client';

export default function PosterCard({ entry }) {
  const navigate = useNavigate();
  const movie = entry.movie || entry;
  const poster = posterUrl(movie.poster_path);

  return (
    <Card
      shadow="sm"
      radius="lg"
      style={{ cursor: 'pointer', background: '#1a1a1a', border: '1px solid #2e2e2e' }}
      onClick={() => navigate(`/movie/${entry.id}`)}
    >
      <Card.Section>
        {poster ? (
          <Image src={poster} alt={movie.title} height={280} fit="cover" />
        ) : (
          <Box
            style={{
              height: 280, background: '#242424',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Text c="dimmed" size="sm">No poster</Text>
          </Box>
        )}
      </Card.Section>

      <Box p="xs" pt="sm">
        <Tooltip label={movie.title} openDelay={500} disabled={movie.title?.length < 28}>
          <Text fw={600} size="sm" lineClamp={1} style={{ color: '#e8e8e8' }}>
            {movie.title}
          </Text>
        </Tooltip>

        <Group justify="space-between" mt={4} align="center">
          <Text size="xs" c="dimmed">{movie.year ?? '—'}</Text>
          {/* Bug 13 fix: was entry.is_favourite (British) — API field is is_favorite */}
          {entry.is_favorite && <IconHeartFilled size={14} color="#e2b04a" />}
        </Group>

        {entry.rating != null && (
          <Rating value={entry.rating / 2} fractions={2} readOnly size="xs" mt={4} color="yellow" />
        )}
      </Box>
    </Card>
  );
}
