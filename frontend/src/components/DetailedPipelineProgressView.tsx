/**
 * Component for displaying detailed pipeline progress with phase-specific views.
 * Shows SearchProgressView for search, RankingLeaderboardView for ranking, and ReportProgressView for report.
 */

import { Stack, Group, Badge, Progress, Box, Text, Button, Modal } from "@mantine/core";
import { useState } from "react";
import { SearchProgressView } from "./SearchProgressView";
import { RankingLeaderboardView } from "./RankingLeaderboardView";
import { ReportProgressView } from "./ReportProgressView";
import { MemoryGame } from "./MemoryGame";

interface DetailedPipelineProgressViewProps {
  query: string;
  phase: "search" | "ranking" | "report" | "";
  // Search phase props
  searchStep?: number;
  searchStepName?: string;
  searchProgress?: number;
  searchTotal?: number;
  searchMessage?: string;
  searchIteration?: number;
  searchTotalIterations?: number;
  searchTotalAccepted?: number;
  queryProfile?: Record<string, unknown> | null;
  // Ranking phase props
  rankingPapers?: Array<{
    rank?: number;
    elo?: number;
    elo_change?: number;
    wins?: number;
    losses?: number;
    draws?: number;
    title: string;
    year?: number | null;
    paper_id: string;
  }>;
  matchStats?: {
    total_completed: number;
    p1_wins: number;
    p2_wins: number;
    draws: number;
  } | null;
  currentMatch?: {
    paper1_title: string;
    paper2_title: string;
    winner?: number | null;
    reason?: string;
  } | null;
  lastMatch?: {
    paper1_title: string;
    paper2_title: string;
    winner?: number | null;
    reason?: string;
  } | null;
  rankingProgress?: number;
  rankingTotal?: number;
  rankingMessage?: string;
  // Report phase props
  reportStep?: number;
  reportStepName?: string;
  reportProgress?: number;
  reportTotal?: number;
  reportMessage?: string;
}

const PHASES = [
  { id: "search", name: "Search", icon: "🔍" },
  { id: "ranking", name: "Rank", icon: "⚖️" },
  { id: "report", name: "Report", icon: "📝" },
] as const;

export function DetailedPipelineProgressView({
  query,
  phase,
  // Search props
  searchStep = 0,
  searchStepName = "",
  searchProgress = 0,
  searchTotal = 0,
  searchMessage = "",
  searchIteration = 0,
  searchTotalIterations = 0,
  searchTotalAccepted = 0,
  queryProfile = null,
  // Ranking props
  rankingPapers = [],
  matchStats = null,
  currentMatch = null,
  lastMatch = null,
  rankingProgress = 0,
  rankingTotal = 0,
  rankingMessage = "",
  // Report props
  reportStep = 0,
  reportStepName = "",
  reportProgress = 0,
  reportTotal = 0,
  reportMessage = "",
}: DetailedPipelineProgressViewProps) {
  // Calculate overall progress
  const getPhaseProgress = (phaseId: string): number => {
    if (phaseId === "search") {
      if (phase === "search") {
        return searchTotal > 0
          ? ((searchStep + searchProgress / searchTotal) / 7) * 100
          : (searchStep / 7) * 100;
      }
      return phase === "ranking" || phase === "report" ? 100 : 0;
    } else if (phaseId === "ranking") {
      if (phase === "ranking") {
        return rankingTotal > 0 ? (rankingProgress / rankingTotal) * 100 : 0;
      }
      return phase === "report" ? 100 : 0;
    } else if (phaseId === "report") {
      if (phase === "report") {
        return reportTotal > 0
          ? ((reportStep + reportProgress / reportTotal) / 8) * 100
          : (reportStep / 8) * 100;
      }
      return 0;
    }
    return 0;
  };

  const overallProgress =
    (getPhaseProgress("search") +
      getPhaseProgress("ranking") +
      getPhaseProgress("report")) /
    3;

  const getPhaseStatus = (
    phaseId: string,
  ): "completed" | "active" | "pending" => {
    if (phaseId === "search") {
      if (phase === "search") return "active";
      return phase === "ranking" || phase === "report"
        ? "completed"
        : "pending";
    } else if (phaseId === "ranking") {
      if (phase === "ranking") return "active";
      return phase === "report" ? "completed" : "pending";
    } else if (phaseId === "report") {
      if (phase === "report") return "active";
      return "pending";
    }
    return "pending";
  };

  const [showMemoryGame, setShowMemoryGame] = useState(false);

  return (
    <Stack gap="lg">
      {/* Phase Indicator */}
      <Box>
        <Group gap="md" justify="space-between" mb="xs">
          <Text size="lg" fw={600}>
            Pipeline: {query}
          </Text>
          <Group gap="md">
            <Button
              variant="light"
              color="accent"
              onClick={() => setShowMemoryGame(true)}
              size="md"
            >
              🎮 Play Memory Game
            </Button>
            <Badge color="primary" size="lg" variant="light">
              {Math.round(overallProgress)}% Complete
            </Badge>
          </Group>
        </Group>
        <Progress
          value={overallProgress}
          size="md"
          radius="xl"
          animated
          color="primary"
        />
        <Group gap="md" mt="xs" justify="center">
          {PHASES.map((phaseInfo, index) => {
            const status = getPhaseStatus(phaseInfo.id);
            const isActive = status === "active";
            const isCompleted = status === "completed";

            return (
              <Group key={phaseInfo.id} gap="xs">
                <Badge
                  color={isCompleted ? "green" : isActive ? "primary" : "gray"}
                  variant={isActive ? "filled" : "light"}
                  size="lg"
                >
                  {phaseInfo.icon} {phaseInfo.name}
                </Badge>
                {index < PHASES.length - 1 && (
                  <Text size="lg" c="dimmed">
                    →
                  </Text>
                )}
              </Group>
            );
          })}
        </Group>
      </Box>

      {/* Phase-Specific View */}
      {phase === "search" && (
        <SearchProgressView
          currentStep={searchStep}
          stepName={searchStepName}
          currentProgress={searchProgress}
          totalProgress={searchTotal}
          progressMessage={searchMessage}
          currentIteration={searchIteration}
          totalIterations={searchTotalIterations}
          totalAccepted={searchTotalAccepted}
          query={query}
          queryProfile={queryProfile}
        />
      )}

      {phase === "ranking" && (
        <RankingLeaderboardView
          papers={rankingPapers}
          matchStats={matchStats}
          currentMatch={currentMatch}
          lastMatch={lastMatch}
          currentProgress={rankingProgress}
          totalProgress={rankingTotal}
          progressMessage={rankingMessage}
        />
      )}

      {phase === "report" && (
        <ReportProgressView
          currentStep={reportStep}
          stepName={reportStepName}
          currentProgress={reportProgress}
          totalProgress={reportTotal}
          progressMessage={reportMessage}
          query={query}
        />
      )}

      {!phase && (
        <Box p="xl" ta="center">
          <Text c="dimmed">Waiting for pipeline to start...</Text>
        </Box>
      )}

      <Modal
        opened={showMemoryGame}
        onClose={() => setShowMemoryGame(false)}
        title="Memory Game"
        size="xl"
        radius={0}
        centered
        styles={{
          body: {
            maxHeight: "85vh",
            overflowY: "auto",
            padding: "var(--mantine-spacing-md)",
          },
        }}
      >
        <MemoryGame />
      </Modal>
    </Stack>
  );
}
