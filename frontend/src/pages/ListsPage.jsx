import { useState, useEffect } from 'react';
import {
  Stack, Card, Text, Group, Button, TextInput,
  Modal, Textarea, ActionIcon, Loader, Center, Box, Badge,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconList, IconPlus, IconTrash, IconChevronRight } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import EmptyState from '../components/EmptyState';

export default function ListsPage() {
  const [lists,    setLists]    = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [name,     setName]     = useState('');
  const [desc,     setDesc]     = useState('');
  const [opened,  { open, close }] = useDisclosure(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.getLists()
      .then(data => setLists(Array.isArray(data) ? data : data.items ?? []))
      .finally(() => setLoading(false));
  }, []);

  async function create() {
    if (!name.trim()) return;
    try {
      const l = await api.createList({ name, description: desc });
      setLists(prev => [l, ...prev]);
      setName(''); setDesc('');
      close();
    } catch (e) {
      notifications.show({ message: e.message, color: 'red' });
    }
  }

  async function remove(id) {
    if (!confirm('Delete this list?')) return;
    await api.deleteList(id);
    setLists(prev => prev.filter(l => l.id !== id));
  }

  return (
    <Box>
      <Group justify="space-between" mb="md">
        <Text fw={700} size="xl" style={{ color: '#e2b04a' }}>Lists</Text>
        <Button leftSection={<IconPlus size={14} />} color="yellow" onClick={open} size="sm">New list</Button>
      </Group>

      <Modal opened={opened} onClose={close} title="Create a new list" centered styles={{ content: { background: '#1a1a1a' }, header: { background: '#1a1a1a' } }}>
        <Stack>
          <TextInput label="Name" placeholder="e.g. 2024 Watches" value={name} onChange={e => setName(e.target.value)}
            styles={{ input: { background: '#141414', borderColor: '#2e2e2e', color: '#e8e8e8' } }} />
          <Textarea label="Description (optional)" placeholder="What's this list for?" value={desc} onChange={e => setDesc(e.target.value)}
            styles={{ input: { background: '#141414', borderColor: '#2e2e2e', color: '#e8e8e8' } }} />
          <Button color="yellow" onClick={create}>Create</Button>
        </Stack>
      </Modal>

      {loading ? (
        <Center py={80}><Loader color="yellow" /></Center>
      ) : lists.length === 0 ? (
        <EmptyState icon={IconList} title="No lists yet" description="Create a list to organise your movies." />
      ) : (
        <Stack gap="sm">
          {lists.map(l => (
            <Card key={l.id} shadow="sm" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e', cursor: 'pointer' }}
              onClick={() => navigate(`/lists/${l.id}`)}>
              <Group justify="space-between">
                <Box>
                  <Text fw={600} style={{ color: '#e8e8e8' }}>{l.name}</Text>
                  {l.description && <Text size="xs" c="dimmed" mt={2}>{l.description}</Text>}
                </Box>
                <Group gap="xs">
                  <Badge color="gray" variant="outline" size="sm">{l.item_count ?? 0} films</Badge>
                  <ActionIcon color="red" variant="subtle" onClick={e => { e.stopPropagation(); remove(l.id); }}>
                    <IconTrash size={14} />
                  </ActionIcon>
                  <IconChevronRight size={14} color="#696969" />
                </Group>
              </Group>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  );
}
