import { useState, useEffect, useCallback } from 'react';
import {
  Title, Text, Card, Group, Button, TextInput, Stack,
  ActionIcon, Loader, Center, Modal, SimpleGrid, Badge,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconTrash, IconList } from '@tabler/icons-react';
import { listsApi } from '../api/client';

export default function ListsPage() {
  const [lists, setLists]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [newName, setNewName]   = useState('');
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { setLists(await listsApi.list()); }
    catch (e) { notifications.show({ color: 'red', message: e.message }); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await listsApi.create({ name: newName.trim() });
      setNewName('');
      await load();
    } catch (e) { notifications.show({ color: 'red', message: e.message }); }
    finally { setCreating(false); }
  };

  const remove = async (id) => {
    try { await listsApi.delete(id); await load(); }
    catch (e) { notifications.show({ color: 'red', message: e.message }); }
  };

  return (
    <>
      <Title order={2} mb="lg" style={{ color: '#C9C9C9' }}>My Lists</Title>
      <Group mb="xl">
        <TextInput
          placeholder="New list name…"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && create()}
          style={{ flex: 1 }}
          styles={{ input: { background: '#1a1a1a', border: '1px solid #2e2e2e', color: '#C9C9C9' } }}
        />
        <Button color="yellow" leftSection={<IconPlus size={14} />} loading={creating} onClick={create}>
          Create
        </Button>
      </Group>

      {loading ? <Center h={200}><Loader color="yellow" /></Center>
        : lists.length === 0 ? (
          <Center h={200}><Stack align="center"><IconList size={48} color="#424242" /><Text c="dimmed">No lists yet.</Text></Stack></Center>
        ) : (
          <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
            {lists.map(list => (
              <Card key={list.id} padding="md" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
                <Group justify="space-between">
                  <Stack gap={2}>
                    <Text fw={600} style={{ color: '#C9C9C9' }}>{list.name}</Text>
                    {list.description && <Text size="xs" c="dimmed">{list.description}</Text>}
                  </Stack>
                  <ActionIcon variant="subtle" color="red" onClick={() => remove(list.id)} aria-label="Delete list">
                    <IconTrash size={16} />
                  </ActionIcon>
                </Group>
              </Card>
            ))}
          </SimpleGrid>
        )}
    </>
  );
}
