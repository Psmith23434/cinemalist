import { useState, useEffect, useCallback } from 'react';
import {
  Title, Text, Image, Group, Badge, Stack, Divider,
  Rating, Textarea, Button, ActionIcon, Loader, Center,
  Box, Paper, Tooltip, Select, NumberInput, Modal,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { notifications } from '@mantine/notifications';
import { useParams, useNavigate } from 'react-router-dom';
import {
  IconHeart, IconHeartFilled, IconTrash, IconEdit,
  IconCheck, IconPlus, IconCalendar, IconDeviceTv,
} from '@tabler/icons-react';
import { entriesApi, notesApi, watchApi } from '../api/client';

const POSTER_BASE = 'https://image.tmdb.org/t/p/w500';

export default function MovieDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [entry, setEntry]         = useState(null);
  const [notes, setNotes]         = useState([]);
  const [watches, setWatches]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [saving, setSaving]       = useState(false);
  const [noteText, setNoteText]   = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editRating, setEditRating] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [e, n, w] = await Promise.all([
        entriesApi.get(id),
        notesApi.list(id),
        watchApi.list(id),
      ]);
      setEntry(e);
      setNotes(n);
      setWatches(w);
      setEditRating(e.rating);
    } catch (err) {
      notifications.show({ color: 'red', message: err.message });
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const update = async (patch) => {
    setSaving(true);
    try {
      await entriesApi.update(id, patch);
      await load();
      notifications.show({ color: 'teal', message: 'Saved' });
    } catch (err) {
      notifications.show({ color: 'red', message: err.message });
    } finally {
      setSaving(false);
    }
  };

  const addNote = async () => {
    if (!noteText.trim()) return;
    try {
      await notesApi.add(id, { content: noteText, is_review: false });
      setNoteText('');
      await load();
    } catch (err) {
      notifications.show({ color: 'red', message: err.message });
    }
  };

  const deleteEntry = async () => {
    try {
      await entriesApi.delete(id);
      navigate('/');
    } catch (err) {
      notifications.show({ color: 'red', message: err.message });
    }
  };

  if (loading) return <Center h={400}><Loader color="yellow" /></Center>;
  if (!entry)  return <Center h={400}><Text c="dimmed">Entry not found.</Text></Center>;

  const { movie } = entry;
  const year = movie.release_date ? movie.release_date.slice(0, 4) : '—';
  const genres = movie.genres || [];

  return (
    <>
      {/* Delete confirmation */}
      <Modal
        opened={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Remove from library?"
        centered
        styles={{ content: { background: '#1a1a1a' }, header: { background: '#1a1a1a' } }}
      >
        <Text size="sm" c="dimmed" mb="lg">
          This will permanently remove "{movie.title}" from your library.
        </Text>
        <Group>
          <Button variant="default" onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="red" onClick={deleteEntry}>Delete</Button>
        </Group>
      </Modal>

      <Group align="flex-start" gap="xl" wrap="wrap">
        {/* Poster */}
        <Box style={{ width: 200, flexShrink: 0 }}>
          <Image
            src={movie.poster_path ? `${POSTER_BASE}${movie.poster_path}` : undefined}
            alt={movie.title}
            radius="lg"
            style={{ border: '1px solid #2e2e2e' }}
            fallbackSrc="https://via.placeholder.com/200x300/242424/696969?text=No+Poster"
          />
        </Box>

        {/* Details */}
        <Stack style={{ flex: 1, minWidth: 260 }} gap="md">
          <Group justify="space-between" align="flex-start">
            <Box>
              <Title order={2} style={{ color: '#C9C9C9' }}>{movie.title}</Title>
              <Text size="sm" c="dimmed">{year} · {movie.runtime ? `${movie.runtime} min` : '—'}</Text>
            </Box>
            <Group gap="xs">
              <Tooltip label={entry.is_favorite ? 'Remove from favourites' : 'Add to favourites'}>
                <ActionIcon
                  variant="subtle"
                  onClick={() => update({ is_favorite: !entry.is_favorite })}
                  aria-label="Toggle favourite"
                  color={entry.is_favorite ? 'yellow' : 'gray'}
                >
                  {entry.is_favorite ? <IconHeartFilled size={20} /> : <IconHeart size={20} />}
                </ActionIcon>
              </Tooltip>
              <Tooltip label="Remove from library">
                <ActionIcon variant="subtle" color="red" onClick={() => setDeleteOpen(true)} aria-label="Delete entry">
                  <IconTrash size={18} />
                </ActionIcon>
              </Tooltip>
            </Group>
          </Group>

          {/* Genres */}
          {genres.length > 0 && (
            <Group gap="xs">
              {genres.map(g => (
                <Badge key={g.id || g} size="sm" variant="light" color="gray">{g.name || g}</Badge>
              ))}
            </Group>
          )}

          {/* TMDb rating */}
          {movie.vote_average > 0 && (
            <Text size="sm" c="dimmed">TMDb: ★ {movie.vote_average?.toFixed(1)}</Text>
          )}

          {/* Overview */}
          {movie.overview && (
            <Text size="sm" style={{ maxWidth: '65ch', color: '#b8b8b8', lineHeight: 1.6 }}>
              {movie.overview}
            </Text>
          )}

          <Divider style={{ borderColor: '#2e2e2e' }} />

          {/* Your rating */}
          <Box>
            <Text size="sm" fw={600} mb={6} style={{ color: '#C9C9C9' }}>Your Rating</Text>
            <Group gap="md" align="center">
              <Rating
                value={(editRating || 0) / 2}
                fractions={2}
                size="lg"
                color="yellow"
                onChange={v => setEditRating(v * 2)}
              />
              <Text size="sm" c="dimmed" style={{ fontVariantNumeric: 'tabular-nums' }}>
                {editRating != null ? `${editRating.toFixed(1)} / 10` : 'Not rated'}
              </Text>
              <Button
                size="xs"
                color="yellow"
                loading={saving}
                disabled={editRating === entry.rating}
                onClick={() => update({ rating: editRating })}
              >
                Save
              </Button>
            </Group>
          </Box>

          {/* Status */}
          <Select
            label="Status"
            value={entry.status}
            onChange={v => update({ status: v })}
            data={[
              { value: 'watched',    label: '✓ Watched' },
              { value: 'watchlist',  label: '⏰ Watchlist' },
              { value: 'rewatching', label: '↺ Rewatching' },
              { value: 'dropped',    label: '✕ Dropped' },
            ]}
            styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
          />
        </Stack>
      </Group>

      <Divider my="xl" style={{ borderColor: '#2e2e2e' }} />

      {/* Notes */}
      <Box mb="xl">
        <Title order={4} mb="md" style={{ color: '#C9C9C9' }}>Notes & Reviews</Title>
        <Group align="flex-end" gap="sm" mb="md">
          <Textarea
            placeholder="Add a note about this film…"
            value={noteText}
            onChange={e => setNoteText(e.target.value)}
            autosize
            minRows={2}
            style={{ flex: 1 }}
            styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
          />
          <Button
            color="yellow"
            leftSection={<IconPlus size={14} />}
            onClick={addNote}
            disabled={!noteText.trim()}
          >
            Add
          </Button>
        </Group>
        <Stack gap="sm">
          {notes.map(note => (
            <Paper
              key={note.id}
              p="sm"
              radius="md"
              style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}
            >
              <Group justify="space-between" align="flex-start">
                <Text size="sm" style={{ color: '#b8b8b8', flex: 1 }}>{note.content}</Text>
                <ActionIcon
                  variant="subtle"
                  color="red"
                  size="sm"
                  onClick={async () => {
                    await notesApi.delete(id, note.id);
                    await load();
                  }}
                  aria-label="Delete note"
                >
                  <IconTrash size={12} />
                </ActionIcon>
              </Group>
              <Text size="xs" c="dimmed" mt={4}>
                {new Date(note.created_at).toLocaleDateString()}
              </Text>
            </Paper>
          ))}
          {notes.length === 0 && (
            <Text size="sm" c="dimmed">No notes yet.</Text>
          )}
        </Stack>
      </Box>

      {/* Watch history */}
      <Box>
        <Title order={4} mb="md" style={{ color: '#C9C9C9' }}>Watch History</Title>
        <Stack gap="xs">
          {watches.map(w => (
            <Group key={w.id} justify="space-between">
              <Group gap="sm">
                <IconCalendar size={14} color="#696969" />
                <Text size="sm" c="dimmed">{new Date(w.watched_on).toLocaleDateString()}</Text>
                {w.platform && (
                  <Badge size="xs" variant="outline" color="gray">
                    <IconDeviceTv size={10} style={{ marginRight: 3 }} />
                    {w.platform}
                  </Badge>
                )}
              </Group>
              <ActionIcon
                variant="subtle" color="red" size="sm"
                onClick={async () => { await watchApi.delete(id, w.id); await load(); }}
                aria-label="Remove watch event"
              >
                <IconTrash size={12} />
              </ActionIcon>
            </Group>
          ))}
          {watches.length === 0 && <Text size="sm" c="dimmed">No watch events logged.</Text>}
        </Stack>
        <Button
          size="xs"
          mt="md"
          variant="light"
          leftSection={<IconPlus size={12} />}
          onClick={async () => {
            await watchApi.add(id, { watched_on: new Date().toISOString().slice(0, 10) });
            await load();
          }}
        >
          Log watch today
        </Button>
      </Box>
    </>
  );
}
