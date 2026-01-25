/**
 * Component for displaying report generation progress with detailed step tracking.
 */

import {
  Timeline,
  Text,
  Paper,
  Progress,
  Stack,
  Title,
  Box,
  ThemeIcon,
  Loader,
  Group,
} from "@mantine/core";

interface ReportProgressViewProps {
  currentStep: number;
  stepName: string;
  currentProgress: number;
  totalProgress: number;
  progressMessage: string;
  query: string;
}

const STEP_NAMES = [
  "Selecting Top Papers",
  "Generating Paper Cards",
  "Creating Report Outline",
  "Writing Sections",
  "Auditing Citations",
  "Writing Introduction & Conclusion",
  "Assembling Report",
  "Final Quality Check",
];

export function ReportProgressView({
  currentStep,
  stepName,
  currentProgress,
  totalProgress,
  progressMessage,
  query,
}: ReportProgressViewProps) {
  const totalSteps = 8;
  const overallProgress =
    ((currentStep + (totalProgress > 0 ? currentProgress / totalProgress : 0)) /
      totalSteps) *
    100;

  return (
    <Paper p="xl" radius="md" withBorder>
      <Stack gap="lg">
        <Box>
          <Title order={3} mb="xs">
            Generating Report: {query}
          </Title>
        </Box>

        <Box>
          <Group justify="space-between" mb="xs">
            <Text fw={500} size="sm">
              Overall Progress
            </Text>
            <Text fw={700} size="md" c="primary">
              {Math.round(overallProgress)}%
            </Text>
          </Group>
          <Progress
            value={overallProgress}
            size="lg"
            radius="xl"
            animated
            color="primary"
          />
        </Box>

        <Box p="md" style={{ borderLeft: "4px solid var(--mantine-color-primary-6)" }}>
          <Stack gap="xs">
            <Text size="sm" c="dimmed">
              Step {currentStep + 1} of {totalSteps}
            </Text>
            <Text fw={600} size="lg" c="primary">
              {stepName || STEP_NAMES[currentStep] || "Processing..."}
            </Text>

            {totalProgress > 0 && (
              <Box mt="sm">
                <Group justify="space-between" mb="xs">
                  <Text size="sm" c="dimmed">
                    {progressMessage ||
                      `Processing ${currentProgress} of ${totalProgress}...`}
                  </Text>
                  <Text size="sm" c="dimmed" fw={500}>
                    {currentProgress} / {totalProgress}
                  </Text>
                </Group>
                <Progress
                  value={(currentProgress / totalProgress) * 100}
                  size="sm"
                  radius="xl"
                  animated
                />
              </Box>
            )}

            {totalProgress === 0 && progressMessage && (
              <Text size="sm" c="dimmed" mt="xs">
                {progressMessage}
              </Text>
            )}
          </Stack>
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
                  <Text fw={isCurrent ? 600 : 500} size="md">
                    {name}
                  </Text>
                }
              >
                {isCurrent && totalProgress > 0 && (
                  <Text size="xs" c="dimmed" mt="xs">
                    {currentProgress} / {totalProgress}
                  </Text>
                )}
              </Timeline.Item>
            );
          })}
        </Timeline>
      </Stack>
    </Paper>
  );
}
