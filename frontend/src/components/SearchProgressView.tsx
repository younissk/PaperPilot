/**
 * Component for displaying search progress with detailed step tracking using Mantine Timeline.
 */

import {
  Timeline,
  Text,
  Paper,
  Progress,
  Stack,
  Title,
  Box,
  Badge,
  ThemeIcon,
  Loader,
  ActionIcon,
  Modal,
  Group,
  Divider,
  List,
} from "@mantine/core";
import { useState } from "react";

interface SearchProgressViewProps {
  currentStep: number;
  stepName: string;
  currentProgress: number;
  totalProgress: number;
  progressMessage: string;
  currentIteration: number;
  totalIterations: number;
  totalAccepted: number;
  query: string;
  queryProfile?: Record<string, unknown> | null;
}

const STEP_NAMES = [
  "Generating Query Profile",
  "Augmenting Search Query",
  "Searching arXiv",
  "Filtering Results",
  "Resolving Paper IDs",
  "Running Snowball Search",
  "Exporting Results",
];

export function SearchProgressView({
  currentStep,
  stepName,
  currentProgress,
  totalProgress,
  progressMessage,
  currentIteration,
  totalIterations,
  query,
  totalAccepted,
  queryProfile,
}: SearchProgressViewProps) {
  const totalSteps = 7;
  const [showQueryProfileModal, setShowQueryProfileModal] = useState(false);

  return (
    <Paper p="xl" radius="md" withBorder>
      <Stack gap="lg">
        <Box>
          <Title order={3} mb="xs">
            Searching: {query}
          </Title>
          {totalAccepted > 0 && (
            <Badge color="primary" size="lg" variant="light">
              {totalAccepted} papers found
            </Badge>
          )}
        </Box>

        <Timeline
          active={currentStep}
          bulletSize={28}
          lineWidth={2}
          color="primary"
        >
          {STEP_NAMES.map((name, index) => {
            const isCompleted = index < currentStep;
            const isCurrent = index === currentStep;
            const isPending = index > currentStep;

            // Special handling for snowball search step (index 5)
            const isSnowballStep = index === 5;
            const displayName = isSnowballStep
              ? stepName || name
              : stepName && isCurrent
                ? stepName
                : name;

            return (
              <Timeline.Item
                key={index}
                bullet={
                  isCompleted ? (
                    <ThemeIcon size={20} radius="xl" color="green">
                      ✓
                    </ThemeIcon>
                  ) : isCurrent ? (
                    <ThemeIcon size={20} radius="xl" color="primary" variant="light">
                      <Loader size="xs" color="primary" />
                    </ThemeIcon>
                  ) : (
                    <ThemeIcon
                      size={20}
                      radius="xl"
                      color="gray"
                      variant="light"
                    >
                      ○
                    </ThemeIcon>
                  )
                }
                title={
                  <Group gap="xs" align="center">
                    <Text fw={isCurrent ? 600 : 500} size="md">
                      {displayName}
                    </Text>
                    {index === 0 && queryProfile && (
                      <ActionIcon
                        variant="subtle"
                        color="primary"
                        size="sm"
                        onClick={() => setShowQueryProfileModal(true)}
                        title="View Query Profile"
                      >
                        ℹ️
                      </ActionIcon>
                    )}
                  </Group>
                }
              >
                {isCurrent && (
                  <Box mt="xs">
                    {progressMessage && (
                      <Text c="dimmed" size="sm" mb="xs">
                        {progressMessage}
                      </Text>
                    )}

                    {isSnowballStep && totalIterations > 0 && (
                      <Text c="dimmed" size="sm" mb="xs">
                        Iteration {currentIteration} of {totalIterations}
                      </Text>
                    )}

                    {totalProgress > 0 && (
                      <Box>
                        <Progress
                          value={
                            totalProgress > 0
                              ? (currentProgress / totalProgress) * 100
                              : 0
                          }
                          size="sm"
                          radius="xl"
                          animated={isCurrent}
                          mb="xs"
                        />
                        <Text size="xs" c="dimmed">
                          {currentProgress} / {totalProgress}
                        </Text>
                      </Box>
                    )}
                  </Box>
                )}

                {isCompleted && index === 5 && totalIterations > 0 && (
                  <Text c="dimmed" size="xs" mt="xs">
                    Completed {totalIterations} iteration
                    {totalIterations !== 1 ? "s" : ""}
                  </Text>
                )}
              </Timeline.Item>
            );
          })}
        </Timeline>
      </Stack>

      <Modal
        opened={showQueryProfileModal}
        onClose={() => setShowQueryProfileModal(false)}
        title="Query Profile"
        size="lg"
        radius="md"
      >
        <Stack gap="md">
          {queryProfile?.domain_description && (
            <Box>
              <Text fw={600} size="sm" mb="xs">
                Domain Description
              </Text>
              <Text size="sm" c="dimmed">
                {String(queryProfile.domain_description)}
              </Text>
            </Box>
          )}

          {queryProfile?.required_concepts &&
            Array.isArray(queryProfile.required_concepts) &&
            queryProfile.required_concepts.length > 0 && (
              <Box>
                <Text fw={600} size="sm" mb="xs">
                  Required Concepts
                </Text>
                <List size="sm" spacing="xs">
                  {(queryProfile.required_concepts as string[]).map(
                    (concept, idx) => (
                      <List.Item key={idx}>{concept}</List.Item>
                    ),
                  )}
                </List>
              </Box>
            )}

          {queryProfile?.optional_concepts &&
            Array.isArray(queryProfile.optional_concepts) &&
            queryProfile.optional_concepts.length > 0 && (
              <Box>
                <Text fw={600} size="sm" mb="xs">
                  Optional Concepts
                </Text>
                <List size="sm" spacing="xs">
                  {(queryProfile.optional_concepts as string[]).map(
                    (concept, idx) => (
                      <List.Item key={idx}>{concept}</List.Item>
                    ),
                  )}
                </List>
              </Box>
            )}

          {queryProfile?.exclusion_concepts &&
            Array.isArray(queryProfile.exclusion_concepts) &&
            queryProfile.exclusion_concepts.length > 0 && (
              <Box>
                <Text fw={600} size="sm" mb="xs">
                  Exclusion Concepts
                </Text>
                <List size="sm" spacing="xs">
                  {(queryProfile.exclusion_concepts as string[]).map(
                    (concept, idx) => (
                      <List.Item key={idx}>{concept}</List.Item>
                    ),
                  )}
                </List>
              </Box>
            )}

          {queryProfile?.domain_boundaries && (
            <Box>
              <Text fw={600} size="sm" mb="xs">
                Domain Boundaries
              </Text>
              <Text size="sm" c="dimmed">
                {String(queryProfile.domain_boundaries)}
              </Text>
            </Box>
          )}

          {queryProfile?.fallback_queries &&
            Array.isArray(queryProfile.fallback_queries) &&
            queryProfile.fallback_queries.length > 0 && (
              <Box>
                <Text fw={600} size="sm" mb="xs">
                  Fallback Queries
                </Text>
                <List size="sm" spacing="xs">
                  {(queryProfile.fallback_queries as string[]).map(
                    (query, idx) => (
                      <List.Item key={idx}>{query}</List.Item>
                    ),
                  )}
                </List>
              </Box>
            )}
        </Stack>
      </Modal>
    </Paper>
  );
}
