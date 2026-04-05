import { useState, useEffect } from 'react';
import {
  Title, Text, SimpleGrid, Card, Loader, Center, Stack,
  Group, Badge, Progress, RingProgress, Box, Divider,
} from '@mantine/core';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import { IconStar, IconMovie, IconChartBar, IconHeart } from '@tabler/icons-react';
import { statsApi } from '../api/client';

const GOLD = '#e2b04a';
const COLORS = [GOLD, '#5591c7', '#6daa45', '#d163a7', '#fdab43', '#a86fdf', '#dd6974', '#4f98a3'];

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <Card padding="lg" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
      <Group gap="md" align="flex-start">
        <Icon size={24} color={GOLD} stroke={1.5} />
        <Box>
          <Text size="xl" fw={700} style={{ color: '#C9C9C9', fontVariantNumeric: 'tabular-nums' }}>{value}</Text>
          <Text size="sm" c="dimmed">{label}</Text>
          {sub && <Text size="xs" c="dimmed" mt={2}>{sub}</Text>}
        </Box>
      </Group>
    </Card>
  );
}

export default function StatsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statsApi.overview()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Center h={400}><Loader color="yellow" /></Center>;
  if (!stats) return <Center h={400}><Text c="dimmed">Could not load statistics.</Text></Center>;

  const {
    total_watched = 0,
    total_watchlist = 0,
    total_favourites = 0,
    average_rating = 0,
    genre_breakdown = [],
    rating_distribution = [],
    watched_by_year = [],
    top_movies = [],
  } = stats;

  return (
    <>
      <Title order={2} mb="lg" style={{ color: '#C9C9C9' }}>Statistics</Title>

      {/* KPI row */}
      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="md" mb="xl">
        <StatCard icon={IconMovie}    label="Films watched"  value={total_watched} />
        <StatCard icon={IconChartBar} label="Average rating" value={average_rating ? average_rating.toFixed(1) : '—'} sub="out of 10" />
        <StatCard icon={IconHeart}    label="Favourites"     value={total_favourites} />
        <StatCard icon={IconMovie}    label="On watchlist"   value={total_watchlist} />
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="xl" mb="xl">
        {/* Genre breakdown */}
        {genre_breakdown.length > 0 && (
          <Card padding="lg" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
            <Text fw={600} mb="md" style={{ color: '#C9C9C9' }}>Top Genres</Text>
            <Stack gap="xs">
              {genre_breakdown.slice(0, 8).map((g, i) => (
                <Box key={g.name}>
                  <Group justify="space-between" mb={2}>
                    <Text size="sm" c="dimmed">{g.name}</Text>
                    <Text size="sm" style={{ color: '#C9C9C9', fontVariantNumeric: 'tabular-nums' }}>{g.count}</Text>
                  </Group>
                  <Progress
                    value={(g.count / (genre_breakdown[0]?.count || 1)) * 100}
                    color="yellow"
                    size="xs"
                    radius="xl"
                  />
                </Box>
              ))}
            </Stack>
          </Card>
        )}

        {/* Rating distribution */}
        {rating_distribution.length > 0 && (
          <Card padding="lg" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
            <Text fw={600} mb="md" style={{ color: '#C9C9C9' }}>Rating Distribution</Text>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={rating_distribution} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2e" />
                <XAxis dataKey="rating" tick={{ fill: '#696969', fontSize: 11 }} />
                <YAxis tick={{ fill: '#696969', fontSize: 11 }} />
                <RechartsTip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #2e2e2e', borderRadius: 8 }}
                  labelStyle={{ color: '#C9C9C9' }}
                  itemStyle={{ color: '#e2b04a' }}
                />
                <Bar dataKey="count" fill={GOLD} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Films by year */}
        {watched_by_year.length > 0 && (
          <Card padding="lg" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
            <Text fw={600} mb="md" style={{ color: '#C9C9C9' }}>Films Added by Year</Text>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={watched_by_year} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2e" />
                <XAxis dataKey="year" tick={{ fill: '#696969', fontSize: 11 }} />
                <YAxis tick={{ fill: '#696969', fontSize: 11 }} />
                <RechartsTip
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #2e2e2e', borderRadius: 8 }}
                  labelStyle={{ color: '#C9C9C9' }}
                  itemStyle={{ color: '#e2b04a' }}
                />
                <Bar dataKey="count" fill="#4f98a3" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Top rated */}
        {top_movies.length > 0 && (
          <Card padding="lg" radius="lg" style={{ background: '#1a1a1a', border: '1px solid #2e2e2e' }}>
            <Text fw={600} mb="md" style={{ color: '#C9C9C9' }}>Your Top Rated</Text>
            <Stack gap="sm">
              {top_movies.slice(0, 8).map((m, i) => (
                <Group key={m.title} justify="space-between">
                  <Group gap="sm">
                    <Text size="xs" c="dimmed" style={{ fontVariantNumeric: 'tabular-nums', minWidth: 16 }}>{i + 1}.</Text>
                    <Text size="sm" style={{ color: '#b8b8b8' }} lineClamp={1}>{m.title}</Text>
                  </Group>
                  <Badge size="sm" color="yellow" variant="light">{m.rating?.toFixed(1)}</Badge>
                </Group>
              ))}
            </Stack>
          </Card>
        )}
      </SimpleGrid>
    </>
  );
}
