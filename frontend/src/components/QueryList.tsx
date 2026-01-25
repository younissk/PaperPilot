import { useState } from "react";
import {
  Card,
  Stack,
  Text,
  Button,
  Group,
  Badge,
  Loader,
  Alert,
  ScrollArea,
} from "@mantine/core";
import {
  useQueriesList,
  useQueryMetadata,
  useSnowballResults,
} from "../hooks/queries/useQueries";
import { showError } from "../utils/notifications";
import type { Paper } from "../services/api";

interface QueryListProps {
  onSelectQuery?: (query: string, papers: Paper[]) => void;
}

export function QueryList({ onSelectQuery }: QueryListProps) {
  const { data: queriesData, isLoading, error, refetch } = useQueriesList();
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null);

  const { data: metadataData } = useQueryMetadata(selectedQuery);
  const { data: snowballData, isLoading: loadingSnowball } =
    useSnowballResults(selectedQuery);

  const queries = queriesData?.queries || [];

  const handleQueryClick = (query: string) => {
    setSelectedQuery(query);
    if (onSelectQuery && snowballData) {
      onSelectQuery(query, snowballData.papers);
    }
  };

  if (isLoading) {
    return (
      <Stack align="center" gap="md">
        <Text size="lg" fw={500}>
          Previous Queries
        </Text>
        <Loader />
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack gap="md">
        <Group justify="space-between">
          <Text size="lg" fw={500}>
            Previous Queries
          </Text>
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
        <Group justify="space-between">
          <Text size="lg" fw={500}>
            Previous Queries
          </Text>
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
      <Group justify="space-between">
        <Text size="lg" fw={500}>
          Previous Queries
        </Text>
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
                cursor: "pointer",
                borderColor:
                  selectedQuery === query
                    ? "var(--mantine-color-primary-6)"
                    : undefined,
                borderWidth: selectedQuery === query ? 2 : 1,
              }}
              onClick={() => handleQueryClick(query)}
            >
              <Stack gap="sm">
                <Text fw={500}>{query}</Text>
                {loadingSnowball && selectedQuery === query && (
                  <Group gap="xs">
                    <Loader size="sm" />
                    <Text size="sm" c="dimmed">
                      Loading...
                    </Text>
                  </Group>
                )}
                {metadataData && selectedQuery === query && (
                  <Stack gap="xs" mt="sm">
                    {Object.entries(metadataData.metadata).map(
                      ([key, value]) => (
                        <Group key={key} gap="xs">
                          <Text size="sm" fw={500} c="dimmed">
                            {key}:
                          </Text>
                          <Text size="sm">
                            {typeof value === "object"
                              ? JSON.stringify(value)
                              : String(value)}
                          </Text>
                        </Group>
                      ),
                    )}
                  </Stack>
                )}
              </Stack>
            </Card>
          ))}
        </Stack>
      </ScrollArea>
    </Stack>
  );
}
