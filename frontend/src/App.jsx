import { AppShell, Burger, Group, Text, NavLink, Stack, Badge, rem } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Routes, Route, NavLink as RouterNavLink, useNavigate } from 'react-router-dom';
import {
  IconMovie, IconList, IconChartBar, IconSearch,
  IconHeart, IconClock, IconTag, IconPlus,
} from '@tabler/icons-react';

import Logo from './components/Logo';
import LibraryPage from './pages/LibraryPage';
import MovieDetailPage from './pages/MovieDetailPage';
import AddMoviePage from './pages/AddMoviePage';
import WatchlistPage from './pages/WatchlistPage';
import ListsPage from './pages/ListsPage';
import StatsPage from './pages/StatsPage';
import FavouritesPage from './pages/FavouritesPage';
import TagsPage from './pages/TagsPage';

const NAV_ITEMS = [
  { label: 'Library',     icon: IconMovie,    path: '/' },
  { label: 'Watchlist',   icon: IconClock,    path: '/watchlist' },
  { label: 'Favourites',  icon: IconHeart,    path: '/favourites' },
  { label: 'Lists',       icon: IconList,     path: '/lists' },
  { label: 'Tags',        icon: IconTag,      path: '/tags' },
  { label: 'Statistics',  icon: IconChartBar, path: '/stats' },
];

export default function App() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();

  return (
    <>
      <div className="filmstrip-bar" />
      <AppShell
        header={{ height: 56 }}
        navbar={{ width: 220, breakpoint: 'sm', collapsed: { mobile: !opened } }}
        padding="md"
        styles={{
          main:   { background: '#141414', paddingTop: 'calc(56px + var(--mantine-spacing-md) + 4px)' },
          header: { background: '#1a1a1a', borderBottom: '1px solid #2e2e2e', top: '4px' },
          navbar: { background: '#1a1a1a', borderRight: '1px solid #2e2e2e', top: '60px' },
        }}
      >
        <AppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Group gap="sm">
              <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" color="#e2b04a" />
              <Logo />
            </Group>
            <Badge
              variant="light"
              color="yellow"
              style={{ cursor: 'pointer' }}
              leftSection={<IconSearch size={12} />}
              onClick={() => navigate('/add')}
            >
              Add movie
            </Badge>
          </Group>
        </AppShell.Header>

        <AppShell.Navbar p="sm">
          <Stack gap={2}>
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.path}
                component={RouterNavLink}
                to={item.path}
                end={item.path === '/'}
                label={item.label}
                leftSection={<item.icon size={16} stroke={1.5} />}
                styles={{
                  root: {
                    borderRadius: '8px',
                    color: '#b8b8b8',
                    '&[data-active]': {
                      background: 'rgba(226,176,74,0.12)',
                      color: '#e2b04a',
                    },
                    '&:hover': {
                      background: '#242424',
                      color: '#C9C9C9',
                    },
                  },
                }}
              />
            ))}
          </Stack>

          <Stack gap={2} mt="auto" pt="md" style={{ borderTop: '1px solid #2e2e2e' }}>
            <NavLink
              component={RouterNavLink}
              to="/add"
              label="Add Movie"
              leftSection={<IconPlus size={16} stroke={1.5} />}
              styles={{
                root: {
                  borderRadius: '8px',
                  color: '#e2b04a',
                  fontWeight: 600,
                  '&:hover': { background: 'rgba(226,176,74,0.12)' },
                },
              }}
            />
          </Stack>
        </AppShell.Navbar>

        <AppShell.Main>
          <Routes>
            <Route path="/"            element={<LibraryPage />} />
            <Route path="/movie/:id"   element={<MovieDetailPage />} />
            <Route path="/add"         element={<AddMoviePage />} />
            <Route path="/watchlist"   element={<WatchlistPage />} />
            <Route path="/favourites"  element={<FavouritesPage />} />
            <Route path="/lists"       element={<ListsPage />} />
            <Route path="/tags"        element={<TagsPage />} />
            <Route path="/stats"       element={<StatsPage />} />
          </Routes>
        </AppShell.Main>
      </AppShell>
    </>
  );
}
