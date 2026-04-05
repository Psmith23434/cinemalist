import { useState, useEffect, useCallback } from 'react';
import {
  Title, Text, Group, Badge, Button, TextInput,
  ActionIcon, Loader, Center, Stack, Wrap,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconX, IconTag } from '@tabler/icons-react';
import { tagsApi } from '../api/client';

export default function TagsPage() {
  const [tags, setTags]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [newTag, setNewTag]     = useState('');
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setTags(await tagsApi.list()); }
    catch (e) { notifications.show({ color: 'red', message: e.message }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!newTag.trim()) return;
    setCreating(true);
    try { await tagsApi.create(newTag.trim()); setNewTag(''); await load(); }
    catch (e) { notifications.show({ color: 'red', message: e.message }); }
    finally { setCreating(false); }
  };

  const remove = async (id) => {
    try { await tagsApi.delete(id); await load(); }
    catch (e) { notifications.show({ color: 'red', message: e.message }); }
  };

  return (
    <>
      <Title order={2} mb="lg" style={{ color: '#C9C9C9' }}>Tags</Title>
      <Group mb="xl">
        <TextInput
          placeholder="New tag (e.g. #slow-burn)…"
          value={newTag}
          onChange={e => setNewTag(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && create()}
          style={{ flex: 1 }}
          styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
        />
        <Button color="yellow" leftSection={<IconPlus size={14} />} loading={creating} onClick={create}>
          Add Tag
        </Button>
      </Group>

      {loading ? <Center h={200}><Loader color="yellow" /></Center>
        : tags.length === 0 ? (
          <Center h={200}><Stack align="center"><IconTag size={48} color="#424242" /><Text c="dimmed">No tags yet.</Text></Stack></Center>
        ) : (
          <Group gap="sm">
            {tags.map(tag => (
              <Badge
                key={tag.id}
                size="lg"
                variant="light"
                color="yellow"
                rightSection={
                  <ActionIcon size="xs" variant="transparent" color="yellow" onClick={() => remove(tag.id)} aria-label={`Delete tag ${tag.name}`}>
                    <IconX size={10} />
                  </ActionIcon>
                }
              >
                {tag.name}
              </Badge>
            ))}
          </Group>
        )}
    </>
  );
}
