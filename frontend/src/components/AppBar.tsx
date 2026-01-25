import { Group, Text, Button, Stack } from '@mantine/core';
import { Link, useLocation } from 'react-router-dom';
import { useHealthCheck } from '../hooks/queries/useHealthCheck';

export function AppBar() {
  const location = useLocation();
  const { data: healthData, isError } = useHealthCheck();

  return (
    <Group justify="space-between" h="100%" p="md">
      <Group>
        <Text
          component={Link}
          to="/"
          fw={700}
          size="xl"
          variant="gradient"
          gradient={{ from: 'primary', to: 'accent', deg: 135 }}
          style={{ textDecoration: 'none' }}
        >
          PaperPilot
        </Text>
        <Stack gap={4}>
          <Group gap="xs">
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: isError ? '#F3787A' : healthData ? '#7CE1D7' : '#F8D797',
                animation: !healthData && !isError ? 'pulse 1.5s ease-in-out infinite' : 'none',
              }}
            />
            <Text size="xs" c="dimmed">
              {isError ? 'API Offline' : healthData ? 'API Online' : 'Checking...'}
            </Text>
          </Group>
        </Stack>
      </Group>
      <Group gap="md">
        <Button
          component={Link}
          to="/queries"
          variant={location.pathname === '/queries' ? 'filled' : 'subtle'}
        >
          Searches
        </Button>
        <Button
          component={Link}
          to="/about"
          variant={location.pathname === '/about' ? 'filled' : 'subtle'}
        >
          About
        </Button>
      </Group>
    </Group>
  );
}
