import { useState } from "react";
import {
  Card,
  Stack,
  Text,
  Button,
  Group,
  Loader,
  Alert,
  ScrollArea,
} from "@mantine/core";
import { useQueriesList } from "../hooks/queries/useQueries";
import { getSnowballResults } from "../services/api";
import type { Paper } from "../services/api";

interface QueryListProps {
  onSelectQuery?: (query: string, papers: Paper[]) => void;
}

export function QueryList({ onSelectQuery }: QueryListProps) {
  const { data: queriesData, isLoading, error, refetch } = useQueriesList();
  const [loadingQuery, setLoadingQuery] = useState<string | null>(null);

  const queries = queriesData?.queries || [];

  const handleQueryClick = async (query: string) => {
    if (!onSelectQuery) return;
    
    setLoadingQuery(query);
    try {
      const data = await getSnowballResults(query);
      onSelectQuery(query, data.papers || []);
    } catch (err) {
      console.error("Failed to load snowball results:", err);
    } finally {
      setLoadingQuery(null);
    }
  };

  if (isLoading) {
    return (
      <Stack align="center" gap="md">
        <Loader />
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack gap="md">
        <Group justify="flex-end">
          <Button onClick={() => refetch()}>Retry</Button>
        </Group>
        <Alert color="error" title="Error">
          {error instanceof Error ? error.message : "Failed to load queries"}
        </Alert>
      </Stack>
    );
  }

  if (queries.length === 0) {
    return (
      <Stack gap="md">
        <Group justify="flex-end">
          <Button variant="subtle" onClick={() => refetch()}>
            Refresh
          </Button>
        </Group>
        <Text c="dimmed">No previous queries found.</Text>
      </Stack>
    );
  }

  return (
    <Stack gap="md">
      <Group justify="flex-end">
        <Button variant="subtle" onClick={() => refetch()}>
          Refresh
        </Button>
      </Group>

      <ScrollArea h={600}>
        <Stack gap="md">
          {queries.map((query) => (
            <Card
              key={query}
              shadow="sm"
              padding="lg"
              radius={0}
              withBorder
              style={{
                cursor: loadingQuery === query ? "wait" : "pointer",
                opacity: loadingQuery === query ? 0.7 : 1,
              }}
              onClick={() => handleQueryClick(query)}
            >
              <Group justify="space-between">
                <Text fw={500}>{query}</Text>
                {loadingQuery === query && <Loader size="sm" />}
              </Group>
            </Card>
          ))}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
