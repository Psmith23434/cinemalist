import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Grid, Image, Text, Badge, Group, Rating, Textarea, Button,
  Box, Stack, Loader, Center, ActionIcon, Divider, Switch,
  Select, MultiSelect, Tooltip, Card,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import '@mantine/dates/styles.css';
import {
  IconArrowLeft, IconHeart, IconHeartFilled, IconTrash,
  IconDeviceFloppy, IconCalendarPlus, IconEye, IconClock,
  IconClockOff, IconTag, IconList, IconPlus, IconX,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { api, posterUrl } from '../api/client';

// Format an ISO date string or Date to "06 Apr 2026"
function fmtDate(val) {
  if (!val) return '—';
  const d = val instanceof Date ? val : new Date(val);
  if (isNaN(d)) return String(val);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function MovieDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [entry,   setEntry]   = useState(null);
  const [watches, setWatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);

  // editable fields
  const [rating,       setRating]       = useState(0);
  const [notes,        setNotes]        = useState('');
  const [isFav,        setIsFav]        = useState(false);
  const [isWatchlisted, setIsWatchlisted] = useState(false);
  const [watchDate,    setWatchDate]    = useState(null);

  // tags
  const [allTags,      setAllTags]      = useState([]);   // [{id, name}]
  const [entryTagIds,  setEntryTagIds]  = useState([]);   // [id, ...]

  // lists
  const [allLists,     setAllLists]     = useState([]);   // [{id, name}]
  const [selectedList, setSelectedList] = useState(null); // list id string
  const [addingToList, setAddingToList] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getEntry(id),
      api.getWatches(id),
      api.getTags(),
      api.getLists(),
    ]).then(([e, w, tags, lists]) => {
      setEntry(e);
      setWatches(Array.isArray(w) ? w : w?.items ?? []);
      setRating(e.rating ?? 0);
      setNotes(e.notes ?? '');
      setIsFav(e.is_favorite ?? false);
      setIsWatchlisted(e.is_watchlisted ?? false);
      if (e.first_watched_at) setWatchDate(new Date(e.first_watched_at));

      // Tags: allTags for the MultiSelect, entryTagIds for current selection
      const tagList = Array.isArray(tags) ? tags : tags?.items ?? [];
      setAllTags(tagList);
      setEntryTagIds((e.tags ?? []).map(t => String(t.id)));

      // Lists
      const listList = Array.isArray(lists) ? lists : lists?.items ?? [];
      setAllLists(listList);
    }).finally(() => setLoading(false));
  }, [id]);

  // ── Save core fields ──────────────────────────────────────────────────────
  async function save() {
    setSaving(true);
    try {
      const updated = await api.updateEntry(id, {
        rating,
        notes,
        is_favorite:       isFav,
        is_watchlisted:    isWatchlisted,
        first_watched_at:  watchDate ? watchDate.toISOString() : null,
      });
      setEntry(updated);
      notifications.show({ message: 'Saved!', color: 'yellow' });
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    } finally {
      setSaving(false);
    }
  }

  // ── Watch history ─────────────────────────────────────────────────────────
  async function logRewatch() {
    try {
      const w = await api.addWatch(id, { watched_at: new Date().toISOString() });
      setWatches(prev => [w, ...prev]);
      notifications.show({ message: 'Rewatch logged!', color: 'yellow' });
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    }
  }

  // ── Delete entry ──────────────────────────────────────────────────────────
  async function deleteEntry() {
    if (!confirm('Remove this movie from your library?')) return;
    await api.deleteEntry(id);
    navigate('/');
  }

  // ── Tags: sync MultiSelect changes to backend ─────────────────────────────
  async function handleTagChange(newIds) {
    const prev = entryTagIds;
    // optimistic update
    setEntryTagIds(newIds);

    const added   = newIds.filter(tid => !prev.includes(tid));
    const removed = prev.filter(tid => !newIds.includes(tid));

    try {
      await Promise.all([
        ...added.map(tid   => api.attachTag(id, tid)),
        ...removed.map(tid => api.detachTag(id, tid)),
      ]);
    } catch (e) {
      // roll back on failure
      setEntryTagIds(prev);
      notifications.show({ message: `Tag error: ${e.message}`, color: 'red' });
    }
  }

  // ── Add to list ───────────────────────────────────────────────────────────
  async function addToList() {
    if (!selectedList) return;
    setAddingToList(true);
    try {
      await api.addToList(selectedList, id);
      const listName = allLists.find(l => String(l.id) === selectedList)?.name ?? 'list';
      notifications.show({ message: `Added to "${listName}"`, color: 'yellow' });
      setSelectedList(null);
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    } finally {
      setAddingToList(false);
    }
  }

  if (loading) return <Center py={80}><Loader color="yellow" /></Center>;
  if (!entry)  return <Text c="red">Entry not found.</Text>;

  const movie  = entry.movie ?? {};
  const poster = posterUrl(movie.poster_path, 'w500');

  const inputStyles = { input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } };

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
        {/* ── Poster ── */}
        <Grid.Col span={{ base: 12, sm: 4 }}>
          {poster ? (
            <Image src={poster} radius="lg" alt={movie.title} />
          ) : (
            <Box style={{ height: 360, background: '#242424', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Text c="dimmed">No poster</Text>
            </Box>
          )}
        </Grid.Col>

        {/* ── Movie info + edit controls ── */}
        <Grid.Col span={{ base: 12, sm: 8 }}>
          <Stack gap="xs">
            <Text fw={800} size="2rem" style={{ color: '#e8e8e8', lineHeight: 1.2 }}>
              {movie.title}
            </Text>
            <Group gap="xs">
              {movie.year     && <Badge color="yellow" variant="light">{movie.year}</Badge>}
              {movie.runtime  && <Badge color="gray"   variant="light">{movie.runtime} min</Badge>}
              {movie.language && <Badge color="gray"   variant="outline">{movie.language.toUpperCase()}</Badge>}
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
            {/* Rating + Favourite + Watchlist row */}
            <Group gap="lg" align="flex-start" wrap="wrap">
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
                  thumbIcon={isFav
                    ? <IconHeartFilled size={10} color="#e2b04a" />
                    : <IconHeart size={10} />}
                />
              </Box>

              {/* ── NEW: Watchlist toggle ── */}
              <Box>
                <Text size="sm" c="dimmed" mb={8}>Watchlist</Text>
                <Switch
                  checked={isWatchlisted}
                  onChange={e => setIsWatchlisted(e.currentTarget.checked)}
                  color="blue"
                  label={isWatchlisted ? 'On watchlist' : 'Not on watchlist'}
                  styles={{ label: { color: '#b8b8b8', fontSize: 12 } }}
                  thumbIcon={isWatchlisted
                    ? <IconClock size={10} color="#4dabf7" />
                    : <IconClockOff size={10} color="#696969" />}
                />
              </Box>
            </Group>

            {/* Watch date */}
            <Box>
              <Text size="sm" c="dimmed" mb={4}>Watch date</Text>
              <DateInput
                value={watchDate}
                onChange={setWatchDate}
                placeholder="Pick a date"
                valueFormat="DD MMM YYYY"
                clearable
                styles={inputStyles}
              />
            </Box>

            {/* Notes */}
            <Box>
              <Text size="sm" c="dimmed" mb={4}>Notes / Review</Text>
              <Textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="What did you think?"
                minRows={3}
                autosize
                styles={inputStyles}
              />
            </Box>

            {/* Save + Log rewatch */}
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

      {/* ── NEW: Tags section ─────────────────────────────────────────────── */}
      <Box mt="xl">
        <Divider mb="md" color="#2e2e2e" />
        <Group mb="xs" gap="xs">
          <IconTag size={15} color="#e2b04a" />
          <Text fw={600} style={{ color: '#e8e8e8' }}>Tags</Text>
        </Group>
        {allTags.length === 0 ? (
          <Text size="sm" c="dimmed">
            No tags yet — create some on the{' '}
            <Text
              span
              size="sm"
              style={{ color: '#e2b04a', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => navigate('/tags')}
            >
              Tags page
            </Text>
            .
          </Text>
        ) : (
          <MultiSelect
            data={allTags.map(t => ({ value: String(t.id), label: t.name }))}
            value={entryTagIds}
            onChange={handleTagChange}
            placeholder="Search or select tags…"
            searchable
            clearable
            styles={{
              input:   { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' },
              dropdown: { background: '#1a1a1a', borderColor: '#2e2e2e' },
              option:  { color: '#e8e8e8' },
            }}
          />
        )}
      </Box>

      {/* ── NEW: Add to list section ──────────────────────────────────────── */}
      <Box mt="xl">
        <Divider mb="md" color="#2e2e2e" />
        <Group mb="xs" gap="xs">
          <IconList size={15} color="#e2b04a" />
          <Text fw={600} style={{ color: '#e8e8e8' }}>Add to List</Text>
        </Group>
        {allLists.length === 0 ? (
          <Text size="sm" c="dimmed">
            No lists yet — create one on the{' '}
            <Text
              span
              size="sm"
              style={{ color: '#e2b04a', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => navigate('/lists')}
            >
              Lists page
            </Text>
            .
          </Text>
        ) : (
          <Group gap="sm" align="flex-end">
            <Select
              placeholder="Choose a list…"
              data={allLists.map(l => ({ value: String(l.id), label: l.name }))}
              value={selectedList}
              onChange={setSelectedList}
              clearable
              style={{ flex: 1, maxWidth: 320 }}
              styles={{
                input:    { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' },
                dropdown: { background: '#1a1a1a', borderColor: '#2e2e2e' },
                option:   { color: '#e8e8e8' },
              }}
            />
            <Button
              leftSection={<IconPlus size={14} />}
              color="yellow"
              variant="light"
              disabled={!selectedList}
              loading={addingToList}
              onClick={addToList}
            >
              Add
            </Button>
          </Group>
        )}
      </Box>

      {/* ── Watch history ────────────────────────────────────────────────── */}
      {watches.length > 0 && (
        <Box mt="xl">
          <Divider mb="md" color="#2e2e2e" />
          <Group mb="sm" gap="xs">
            <IconEye size={15} color="#e2b04a" />
            <Text fw={600} style={{ color: '#e8e8e8' }}>Watch history</Text>
          </Group>
          <Stack gap={6}>
            {watches.map((w, i) => (
              <Group key={w.id ?? i} gap="sm">
                <Badge color="gray" variant="outline" size="sm">
                  {fmtDate(w.watched_at)}
                </Badge>
                {w.note && <Text size="xs" c="dimmed">{w.note}</Text>}
              </Group>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
