/**
 * Component for displaying pipeline progress (Search → Rank → Report) with beautiful 3-phase UI.
 */

import {
  Paper,
  Stack,
  Group,
  Text,
  Progress,
  Badge,
  Box,
  ThemeIcon,
  Title,
  Card,
  Divider,
  Loader,
} from "@mantine/core";

interface PipelineProgressViewProps {
  query: string;
  phase: "search" | "ranking" | "report" | "";
  phaseStep: number;
  phaseStepName: string;
  phaseProgress: number;
  phaseTotal: number;
  progressMessage: string;
  papers: Array<{
    paper_id: string;
    title: string;
    rank?: number;
    elo?: number;
  }>;
}

const PHASES = [
  {
    id: "search",
    name: "Search",
    icon: "🔍",
    description: "Finding relevant papers",
  },
  {
    id: "ranking",
    name: "Rank",
    icon: "⚖️",
    description: "Ranking by relevance",
  },
  {
    id: "report",
    name: "Report",
    icon: "📝",
    description: "Generating report",
  },
] as const;

export function PipelineProgressView({
  query,
  phase,
  phaseStep,
  phaseStepName,
  phaseProgress,
  phaseTotal,
  progressMessage,
  papers,
}: PipelineProgressViewProps) {
  // Calculate overall progress
  const getPhaseProgress = (phaseId: string): number => {
    if (phaseId === "search") {
      if (phase === "search") {
        // Search has 7 steps (0-6)
        return phaseTotal > 0
          ? ((phaseStep + phaseProgress / phaseTotal) / 7) * 100
          : (phaseStep / 7) * 100;
      }
      return phase === "ranking" || phase === "report" ? 100 : 0;
    } else if (phaseId === "ranking") {
      if (phase === "ranking") {
        // Ranking progress based on matches
        return phaseTotal > 0 ? (phaseProgress / phaseTotal) * 100 : 0;
      }
      return phase === "report" ? 100 : 0;
    } else if (phaseId === "report") {
      if (phase === "report") {
        // Report has 8 steps (0-7)
        return phaseTotal > 0
          ? ((phaseStep + phaseProgress / phaseTotal) / 8) * 100
          : (phaseStep / 8) * 100;
      }
      return 0;
    }
    return 0;
  };

  const getPhaseStatus = (phaseId: string): "completed" | "active" | "pending" => {
    if (phaseId === "search") {
      if (phase === "search") return "active";
      return phase === "ranking" || phase === "report" ? "completed" : "pending";
    } else if (phaseId === "ranking") {
      if (phase === "ranking") return "active";
      return phase === "report" ? "completed" : "pending";
    } else if (phaseId === "report") {
      if (phase === "report") return "active";
      return "pending";
    }
    return "pending";
  };

  // Calculate overall pipeline progress
  const overallProgress =
    (getPhaseProgress("search") + getPhaseProgress("ranking") + getPhaseProgress("report")) / 3;

  // Get paper count for current phase
  const getPaperCount = (): number => {
    if (phase === "search") {
      return papers.length;
    } else if (phase === "ranking" || phase === "report") {
      return papers.filter((p) => p.rank !== undefined).length || papers.length;
    }
    return 0;
  };

  return (
    <Paper p="xl" radius="md" withBorder>
      <Stack gap="lg">
        {/* Header */}
        <Box>
          <Title order={3} mb="xs">
            Pipeline: {query}
          </Title>
          <Group gap="xs">
            <Badge color="primary" size="lg" variant="light">
              {Math.round(overallProgress)}% Complete
            </Badge>
            {getPaperCount() > 0 && (
              <Badge color="blue" size="lg" variant="light">
                {getPaperCount()} papers
              </Badge>
            )}
          </Group>
        </Box>

        {/* Overall Progress Bar */}
        <Box>
          <Progress
            value={overallProgress}
            size="lg"
            radius="xl"
            animated={phase !== ""}
            color="primary"
          />
        </Box>

        {/* Three Phase Cards */}
        <Group gap="md" align="stretch" style={{ width: "100%" }}>
          {PHASES.map((phaseInfo, index) => {
            const status = getPhaseStatus(phaseInfo.id);
            const progress = getPhaseProgress(phaseInfo.id);
            const isActive = status === "active";
            const isCompleted = status === "completed";

            return (
              <Box key={phaseInfo.id} style={{ flex: 1, position: "relative" }}>
                {/* Connector Arrow */}
                {index < PHASES.length - 1 && (
                  <Box
                    style={{
                      position: "absolute",
                      right: "-16px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      zIndex: 1,
                    }}
                  >
                    <Text
                      size="xl"
                      c={isCompleted || isActive ? "primary" : "dimmed"}
                      fw={700}
                    >
                      →
                    </Text>
                  </Box>
                )}

                <Card
                  p="md"
                  radius="md"
                  withBorder
                  style={{
                    borderColor:
                      isActive
                        ? "var(--mantine-color-primary-6)"
                        : isCompleted
                          ? "var(--mantine-color-green-6)"
                          : "var(--mantine-color-gray-4)",
                    backgroundColor: isActive
                      ? "var(--mantine-color-primary-0)"
                      : isCompleted
                        ? "var(--mantine-color-green-0)"
                        : "var(--mantine-color-gray-0)",
                    transition: "all 0.3s ease",
                    transform: isActive ? "scale(1.02)" : "scale(1)",
                  }}
                >
                  <Stack gap="sm">
                    {/* Phase Header */}
                    <Group gap="xs" justify="space-between">
                      <Group gap="xs">
                        <ThemeIcon
                          size={32}
                          radius="xl"
                          color={
                            isCompleted
                              ? "green"
                              : isActive
                                ? "primary"
                                : "gray"
                          }
                          variant={isActive ? "filled" : "light"}
                        >
                          <Text size="lg">{phaseInfo.icon}</Text>
                        </ThemeIcon>
                        <Box>
                          <Text fw={isActive ? 700 : 500} size="md">
                            {phaseInfo.name}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {phaseInfo.description}
                          </Text>
                        </Box>
                      </Group>
                      {isCompleted && (
                        <ThemeIcon size={20} radius="xl" color="green">
                          ✓
                        </ThemeIcon>
                      )}
                      {isActive && (
                        <ThemeIcon size={20} radius="xl" color="primary" variant="light">
                          <Loader size="xs" color="primary" />
                        </ThemeIcon>
                      )}
                    </Group>

                    {/* Phase Progress */}
                    {isActive && (
                      <>
                        <Divider />
                        <Box>
                          {phaseStepName && (
                            <Text size="sm" fw={500} mb="xs">
                              {phaseStepName}
                            </Text>
                          )}
                          {progressMessage && (
                            <Text size="xs" c="dimmed" mb="xs">
                              {progressMessage}
                            </Text>
                          )}
                          {phaseTotal > 0 && (
                            <>
                              <Progress
                                value={progress}
                                size="sm"
                                radius="xl"
                                animated
                                mb="xs"
                              />
                              <Text size="xs" c="dimmed">
                                {phaseProgress} / {phaseTotal}
                              </Text>
                            </>
                          )}
                        </Box>
                      </>
                    )}

                    {/* Phase Status */}
                    {isCompleted && (
                      <Text size="xs" c="green" fw={500}>
                        ✓ Completed
                      </Text>
                    )}
                    {status === "pending" && (
                      <Text size="xs" c="dimmed">
                        Waiting...
                      </Text>
                    )}
                  </Stack>
                </Card>
              </Box>
            );
          })}
        </Group>
      </Stack>
    </Paper>
  );
}
