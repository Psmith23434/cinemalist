import { Group, Select, TextInput, SegmentedControl, ActionIcon, Tooltip } from '@mantine/core';
import { IconSearch, IconSortAscending, IconSortDescending } from '@tabler/icons-react';

export default function FilterBar({ filters, onChange }) {
  const { query, genre, sortBy, sortDir, status } = filters;

  const update = (key, value) => onChange({ ...filters, [key]: value });

  const GENRES = [
    '', 'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
    'Documentary', 'Drama', 'Fantasy', 'History', 'Horror',
    'Music', 'Mystery', 'Romance', 'Science Fiction', 'Thriller',
    'War', 'Western',
  ].map(g => ({ value: g, label: g || 'All genres' }));

  const SORTS = [
    { value: 'added_at',    label: 'Date added' },
    { value: 'rating',      label: 'My rating' },
    { value: 'title',       label: 'Title' },
    { value: 'release_date', label: 'Release year' },
    { value: 'watch_date',  label: 'Watch date' },
  ];

  return (
    <Group gap="sm" wrap="wrap" mb="lg">
      <TextInput
        placeholder="Search your library…"
        leftSection={<IconSearch size={14} />}
        value={query}
        onChange={e => update('query', e.target.value)}
        style={{ flex: '1 1 200px', minWidth: 160 }}
        styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
      />
      <Select
        data={GENRES}
        value={genre}
        onChange={v => update('genre', v || '')}
        style={{ minWidth: 150 }}
        styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
        comboboxProps={{ withinPortal: true }}
      />
      <SegmentedControl
        value={status}
        onChange={v => update('status', v)}
        data={[
          { value: 'watched',   label: 'Watched' },
          { value: 'watchlist', label: 'Watchlist' },
          { value: 'all',       label: 'All' },
        ]}
        size="xs"
        styles={{ root: { background: '#1a1a1a' } }}
      />
      <Select
        data={SORTS}
        value={sortBy}
        onChange={v => update('sortBy', v)}
        style={{ minWidth: 150 }}
        styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
        comboboxProps={{ withinPortal: true }}
      />
      <Tooltip label={sortDir === 'asc' ? 'Ascending' : 'Descending'}>
        <ActionIcon
          variant="default"
          onClick={() => update('sortDir', sortDir === 'asc' ? 'desc' : 'asc')}
          style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}
          aria-label="Toggle sort direction"
        >
          {sortDir === 'asc'
            ? <IconSortAscending size={16} />
            : <IconSortDescending size={16} />}
        </ActionIcon>
      </Tooltip>
    </Group>
  );
}
