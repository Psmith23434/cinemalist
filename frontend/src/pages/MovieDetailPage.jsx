import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Grid, Image, Text, Badge, Group, Rating, Textarea, Button,
  Box, Stack, Loader, Center, ActionIcon, Divider, Switch,
  NumberInput, Tooltip, Card,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import '@mantine/dates/styles.css';
import {
  IconArrowLeft, IconHeart, IconHeartFilled, IconTrash,
  IconDeviceFloppy, IconCalendarPlus, IconEye,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { api, posterUrl } from '../api/client';

export default function MovieDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [entry,   setEntry]   = useState(null);
  const [watches, setWatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);

  // editable fields
  const [rating,    setRating]    = useState(0);
  const [notes,     setNotes]     = useState('');
  const [isFav,     setIsFav]     = useState(false);
  const [watchDate, setWatchDate] = useState(null);

  useEffect(() => {
    Promise.all([api.getEntry(id), api.getWatches(id)])
      .then(([e, w]) => {
        setEntry(e);
        setWatches(w ?? []);
        setRating(e.rating ?? 0);
        setNotes(e.notes ?? '');
        setIsFav(e.is_favourite ?? false);
        if (e.watched_on) setWatchDate(new Date(e.watched_on));
      })
      .finally(() => setLoading(false));
  }, [id]);

  async function save() {
    setSaving(true);
    try {
      const updated = await api.updateEntry(id, {
        rating,
        notes,
        is_favourite: isFav,
        watched_on: watchDate ? watchDate.toISOString().slice(0, 10) : null,
      });
      setEntry(updated);
      notifications.show({ message: 'Saved!', color: 'yellow' });
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    } finally {
      setSaving(false);
    }
  }

  async function logRewatch() {
    try {
      const w = await api.addWatch(id, { watched_at: new Date().toISOString().slice(0, 10) });
      setWatches(prev => [w, ...prev]);
      notifications.show({ message: 'Rewatch logged!', color: 'yellow' });
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    }
  }

  async function deleteEntry() {
    if (!confirm('Remove this movie from your library?')) return;
    await api.deleteEntry(id);
    navigate('/');
  }

  if (loading) return <Center py={80}><Loader color="yellow" /></Center>;
  if (!entry)  return <Text c="red">Entry not found.</Text>;

  const movie  = entry.movie ?? {};
  const poster = posterUrl(movie.poster_path, 'w500');

  return (
    <Box>
      <Group mb="lg" justify="space-between">
        <Button
          variant="subtle" color="gray" size="sm"
          leftSection={<IconArrowLeft size={14} />}
          onClick={() => navigate(-1)}
        >
          Back
        </Button>
        <ActionIcon color="red" variant="light" onClick={deleteEntry}>
          <IconTrash size={16} />
        </ActionIcon>
      </Group>

      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, sm: 4 }}>
          {poster ? (
            <Image src={poster} radius="lg" alt={movie.title} />
          ) : (
            <Box style={{ height: 360, background: '#242424', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Text c="dimmed">No poster</Text>
            </Box>
          )}
        </Grid.Col>

        <Grid.Col span={{ base: 12, sm: 8 }}>
          <Stack gap="xs">
            <Text fw={800} size="2rem" style={{ color: '#e8e8e8', lineHeight: 1.2 }}>
              {movie.title}
            </Text>
            <Group gap="xs">
              {movie.year && <Badge color="yellow" variant="light">{movie.year}</Badge>}
              {movie.runtime && <Badge color="gray" variant="light">{movie.runtime} min</Badge>}
              {movie.language && <Badge color="gray" variant="outline">{movie.language.toUpperCase()}</Badge>}
            </Group>
            {movie.overview && (
              <Text c="dimmed" size="sm" mt="xs" style={{ maxWidth: 560 }}>{movie.overview}</Text>
            )}
            {movie.director && (
              <Text size="sm"><Text span c="dimmed">Director: </Text>{movie.director}</Text>
            )}
            {movie.tmdb_rating && (
              <Text size="sm"><Text span c="dimmed">TMDb: </Text>★ {movie.tmdb_rating.toFixed(1)} / 10</Text>
            )}
          </Stack>

          <Divider my="lg" color="#2e2e2e" />

          <Stack gap="md">
            <Group gap="lg" align="flex-start">
              <Box>
                <Text size="sm" c="dimmed" mb={4}>Your rating</Text>
                <Rating
                  value={rating / 2}
                  onChange={v => setRating(v * 2)}
                  fractions={2}
                  size="xl"
                  color="yellow"
                  count={5}
                />
                <Text size="xs" c="dimmed" mt={2}>{rating > 0 ? `${rating} / 10` : 'Not rated'}</Text>
              </Box>
              <Box>
                <Text size="sm" c="dimmed" mb={8}>Favourite</Text>
                <Switch
                  checked={isFav}
                  onChange={e => setIsFav(e.currentTarget.checked)}
                  color="yellow"
                  thumbIcon={isFav ? <IconHeartFilled size={10} color="#e2b04a" /> : <IconHeart size={10} />}
                />
              </Box>
            </Group>

            <Box>
              <Text size="sm" c="dimmed" mb={4}>Watch date</Text>
              <DateInput
                value={watchDate}
                onChange={setWatchDate}
                placeholder="Pick a date"
                valueFormat="DD MMM YYYY"
                clearable
                styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
              />
            </Box>

            <Box>
              <Text size="sm" c="dimmed" mb={4}>Notes / Review</Text>
              <Textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="What did you think?"
                minRows={3}
                autosize
                styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
              />
            </Box>

            <Group>
              <Button
                leftSection={<IconDeviceFloppy size={14} />}
                color="yellow"
                onClick={save}
                loading={saving}
              >
                Save
              </Button>
              <Button
                leftSection={<IconCalendarPlus size={14} />}
                variant="light"
                color="gray"
                onClick={logRewatch}
              >
                Log rewatch
              </Button>
            </Group>
          </Stack>
        </Grid.Col>
      </Grid>

      {watches.length > 0 && (
        <Box mt="xl">
          <Text fw={600} mb="sm" style={{ color: '#e8e8e8' }}>
            <IconEye size={14} style={{ marginRight: 6 }} />Watch history
          </Text>
          <Stack gap={6}>
            {watches.map((w, i) => (
              <Group key={w.id ?? i} gap="sm">
                <Badge color="gray" variant="outline" size="sm">{w.watched_at ?? w.watched_on}</Badge>
                {w.note && <Text size="xs" c="dimmed">{w.note}</Text>}
              </Group>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
