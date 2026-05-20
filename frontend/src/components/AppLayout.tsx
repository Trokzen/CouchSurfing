import { ReactNode, useState } from 'react';
import { AppShell, Burger, Group, NavLink, Avatar, Text, Box } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconHome, IconCalendar, IconBuildingStore, IconPlus, IconLogin, IconUserPlus, IconLogout } from '@tabler/icons-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { showNotification } from '@mantine/notifications';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
  const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure(true);
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    showNotification({
      title: 'Logged out',
      message: 'You have been successfully logged out',
      color: 'blue',
    });
    navigate('/login');
  };

  const navLinks = [
    { link: '/listings', label: 'Browse Listings', icon: IconHome },
    ...(isAuthenticated && user?.role === 'host' ? [
      { link: '/my-listings', label: 'My Listings', icon: IconBuildingStore },
      { link: '/listings/create', label: 'Create Listing', icon: IconPlus },
    ] : []),
    ...(isAuthenticated ? [
      { link: '/bookings', label: 'My Bookings', icon: IconCalendar },
    ] : []),
  ];

  const authLinks = isAuthenticated ? (
    <Group gap="sm" justify="flex-end">
      <NavLink
        component={Link}
        to="/bookings"
        label={user?.full_name || 'Profile'}
        leftSection={<Avatar size={24} radius="xl" />}
        active={location.pathname.startsWith('/bookings')}
      />
      <NavLink
        onClick={handleLogout}
        label="Logout"
        leftSection={<IconLogout size={18} />}
      />
    </Group>
  ) : (
    <Group gap="sm" justify="flex-end">
      <NavLink
        component={Link}
        to="/login"
        label="Login"
        leftSection={<IconLogin size={18} />}
        active={location.pathname === '/login'}
      />
      <NavLink
        component={Link}
        to="/register"
        label="Register"
        leftSection={<IconUserPlus size={18} />}
        active={location.pathname === '/register'}
      />
    </Group>
  );

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 250,
        breakpoint: 'sm',
        collapsed: { mobile: !mobileOpened, desktop: !desktopOpened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger
              opened={mobileOpened || desktopOpened}
              onClick={() => {
                toggleMobile();
                toggleDesktop();
              }}
              size="sm"
            />
            <Text fw={700} size="lg">
              🏠 CouchSurfing
            </Text>
          </Group>
          {authLinks}
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Box>
          {navLinks.map((item) => (
            <NavLink
              key={item.label}
              component={Link}
              to={item.link}
              label={item.label}
              leftSection={<item.icon size={18} stroke={1.5} />}
              active={location.pathname === item.link || location.pathname.startsWith(item.link + '/')}
              onClick={() => toggleMobile()}
            />
          ))}
        </Box>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
