import { useState, useEffect } from 'react';
import {
  Group, Badge, Text, TextInput, Button, Box,
  ActionIcon, Loader, Center,
} from '@mantine/core';
import { IconTag, IconPlus, IconX } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { api } from '../api/client';
import EmptyState from '../components/EmptyState';

export default function TagsPage() {
  const [tags,    setTags]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTag,  setNewTag]  = useState('');

  useEffect(() => {
    api.getTags()
      .then(data => setTags(Array.isArray(data) ? data : data.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  async function create() {
    if (!newTag.trim()) return;
    try {
      const t = await api.createTag({ name: newTag.trim() });
      setTags(prev => [...prev, t]);
      setNewTag('');
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    }
  }

  async function remove(id) {
    await api.deleteTag(id);
    setTags(prev => prev.filter(t => t.id !== id));
  }

  return (
    <Box>
      <Text fw={700} size="xl" mb="md" style={{ color: '#e2b04a' }}>Tags</Text>

      <Group mb="lg" gap="sm">
        <TextInput
          placeholder="New tag name…"
          value={newTag}
          onChange={e => setNewTag(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && create()}
          styles={{ input: { background: '#1a1a1a', borderColor: '#2e2e2e', color: '#e8e8e8' } }}
        />
        <Button leftSection={<IconPlus size={14} />} color="yellow" onClick={create} size="sm">Add</Button>
      </Group>

      {loading ? (
        <Center py={60}><Loader color="yellow" /></Center>
      ) : tags.length === 0 ? (
        <EmptyState icon={IconTag} title="No tags yet" description="Create tags to categorise your movies." />
      ) : (
        <Group gap="sm" wrap="wrap">
          {tags.map(t => (
            <Badge
              key={t.id}
              color="yellow"
              variant="light"
              size="lg"
              rightSection={
                <ActionIcon size="xs" color="yellow" variant="transparent" onClick={() => remove(t.id)}>
                  <IconX size={10} />
                </ActionIcon>
              }
            >
              {t.name}
            </Badge>
          ))}
        </Group>
      )}
    </Box>
  );
}
