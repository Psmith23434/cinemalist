import { useState, useEffect } from 'react';
import {
  Grid, Card, Text, Group, Stack, Loader, Center,
  Box, RingProgress, Progress,
} from '@mantine/core';
import { BarChart } from '@mantine/charts';
import {
  IconMovie, IconStar, IconRepeat, IconHeart,
} from '@tabler/icons-react';
import { api } from '../api/client';

function StatCard({ icon: Icon, label, value, color = 'yellow' }) {
  return (
    <Card shadow="sm" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
      <Group gap="md" align="center">
        <Box
          style={{
            background: 'rgba(226,176,74,0.1)', borderRadius: 10,
            width: 44, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <Icon size={22} color="#e2b04a" stroke={1.5} />
        </Box>
        <Box>
          <Text size="xs" c="dimmed">{label}</Text>
          <Text fw={700} size="xl" style={{ color: '#e8e8e8' }}>{value ?? '—'}</Text>
        </Box>
      </Group>
    </Card>
  );
}

export default function StatsPage() {
  const [stats,   setStats]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Center py={80}><Loader color="yellow" /></Center>;
  if (!stats)  return <Text c="dimmed">No stats available yet.</Text>;

  const byYear   = (stats.by_year   ?? []).map(y => ({ year: String(y.year), count: y.count }));
  const byGenre  = stats.top_genres ?? [];
  const ratingDist = stats.rating_distribution ?? [];

  return (
    <Box>
      <Text fw={700} size="xl" mb="lg" style={{ color: '#e2b04a' }}>Statistics</Text>

      <Grid gutter="md" mb="xl">
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <StatCard icon={IconMovie}  label="Total watched"   value={stats.total_watched} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <StatCard icon={IconStar}   label="Average rating"  value={stats.average_rating ? `${Number(stats.average_rating).toFixed(1)} / 10` : '—'} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <StatCard icon={IconRepeat} label="Total rewatches" value={stats.total_rewatches ?? 0} />
        </Grid.Col>
        <Grid.Col span={{ base: 6, sm: 3 }}>
          <StatCard icon={IconHeart}  label="Favourites"      value={stats.total_favorites ?? 0} />
        </Grid.Col>
      </Grid>

      <Grid gutter="md">
        {byYear.length > 0 && (
          <Grid.Col span={{ base: 12, md: 7 }}>
            <Card shadow="sm" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
              <Text fw={600} mb="md" style={{ color: '#e8e8e8' }}>Movies by year</Text>
              <BarChart
                h={220}
                data={byYear}
                dataKey="year"
                series={[{ name: 'count', color: 'yellow.5', label: 'Films' }]}
                tickLine="none"
                gridAxis="none"
                style={{ '--chart-text-color': '#696969' }}
              />
            </Card>
          </Grid.Col>
        )}

        {byGenre.length > 0 && (
          <Grid.Col span={{ base: 12, md: 5 }}>
            <Card shadow="sm" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
              <Text fw={600} mb="md" style={{ color: '#e8e8e8' }}>Top genres</Text>
              <Stack gap="xs">
                {byGenre.slice(0, 8).map((g, i) => (
                  <Box key={g.genre ?? i}>
                    <Group justify="space-between" mb={2}>
                      <Text size="sm" style={{ color: '#b8b8b8' }}>{g.genre}</Text>
                      <Text size="xs" c="dimmed">{g.count}</Text>
                    </Group>
                    <Progress
                      value={(g.count / byGenre[0].count) * 100}
                      color="yellow"
                      size="sm"
                      radius="xl"
                      styles={{ root: { background: '#2e2e2e' } }}
                    />
                  </Box>
                ))}
              </Stack>
            </Card>
          </Grid.Col>
        )}

        {ratingDist.length > 0 && (
          <Grid.Col span={12}>
            <Card shadow="sm" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
              <Text fw={600} mb="md" style={{ color: '#e8e8e8' }}>Rating distribution</Text>
              <BarChart
                h={160}
                data={ratingDist.map(r => ({ rating: `${r.rating}★`, count: r.count }))}
                dataKey="rating"
                series={[{ name: 'count', color: 'yellow.4', label: 'Films' }]}
                tickLine="none"
                gridAxis="none"
                style={{ '--chart-text-color': '#696969' }}
              />
            </Card>
          </Grid.Col>
        )}
      </Grid>
    </Box>
  );
}
