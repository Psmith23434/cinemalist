import { Card, Image, Text, Badge, Group, Rating, ActionIcon, Tooltip, Box } from '@mantine/core';
import { IconHeart, IconHeartFilled, IconEye } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { notifications } from '@mantine/notifications';

const POSTER_BASE = 'https://image.tmdb.org/t/p/w342';
const PLACEHOLDER = 'https://via.placeholder.com/342x513/242424/696969?text=No+Poster';

export default function MovieCard({ entry, onUpdate }) {
  const navigate = useNavigate();
  const { movie, rating, is_favorite, status, id } = entry;

  const posterUrl = movie.poster_path
    ? `${POSTER_BASE}${movie.poster_path}`
    : PLACEHOLDER;

  const toggleFav = async (e) => {
    e.stopPropagation();
    try {
      await api.patch(`/entries/${id}`, { is_favorite: !is_favorite });
      onUpdate?.();
    } catch {
      notifications.show({ color: 'red', message: 'Failed to update favourite' });
    }
  };

  const year = movie.release_date ? movie.release_date.slice(0, 4) : '—';

  return (
    <Card
      shadow="sm"
      padding={0}
      radius="lg"
      style={{
        cursor: 'pointer',
        background: '#1a1a1a',
        border: '1px solid #2e2e2e',
        overflow: 'hidden',
        transition: 'transform 180ms ease, box-shadow 180ms ease',
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.5)'; }}
      onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
      onClick={() => navigate(`/movie/${id}`)}
    >
      {/* Poster */}
      <Box style={{ position: 'relative' }}>
        <Image
          src={posterUrl}
          alt={movie.title}
          className="poster-img"
          fallbackSrc={PLACEHOLDER}
        />
        {/* Favourite button overlay */}
        <ActionIcon
          variant="filled"
          size="sm"
          radius="xl"
          style={{
            position: 'absolute', top: 8, right: 8,
            background: is_favorite ? 'rgba(226,176,74,0.9)' : 'rgba(20,20,20,0.75)',
            border: 'none',
          }}
          onClick={toggleFav}
          aria-label={is_favorite ? 'Remove from favourites' : 'Add to favourites'}
        >
          {is_favorite
            ? <IconHeartFilled size={12} color="#141414" />
            : <IconHeart size={12} color="#b8b8b8" />}
        </ActionIcon>
        {/* Status badge */}
        {status === 'watchlist' && (
          <Badge
            size="xs"
            style={{ position: 'absolute', top: 8, left: 8, background: 'rgba(20,20,20,0.8)', color: '#e2b04a' }}
          >
            Watchlist
          </Badge>
        )}
      </Box>

      {/* Info */}
      <Box p="xs">
        <Text size="sm" fw={600} lineClamp={1} style={{ color: '#C9C9C9' }}>
          {movie.title}
        </Text>
        <Group justify="space-between" mt={4} wrap="nowrap">
          <Text size="xs" c="dimmed">{year}</Text>
          {rating != null && (
            <Group gap={2} wrap="nowrap">
              <IconEye size={10} color="#696969" />
              <Text size="xs" c="dimmed" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {rating.toFixed(1)}
              </Text>
            </Group>
          )}
        </Group>
        {rating != null && (
          <Rating
            value={rating / 2}
            fractions={2}
            size="xs"
            readOnly
            mt={4}
            color="yellow"
          />
        )}
      </Box>
    </Card>
  );
}
