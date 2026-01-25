/**
 * Component for displaying live ELO ranking leaderboard with match information.
 */

import {
  Paper,
  Stack,
  Group,
  Text,
  Progress,
  Badge,
  Box,
  Title,
  Table,
  ScrollArea,
  Card,
  Divider,
} from "@mantine/core";

interface RankingLeaderboardViewProps {
  papers: Array<{
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
  matchStats: {
    total_completed: number;
    p1_wins: number;
    p2_wins: number;
    draws: number;
  } | null;
  currentMatch: {
    paper1_title: string;
    paper2_title: string;
    winner?: number | null;
    reason?: string;
  } | null;
  lastMatch: {
    paper1_title: string;
    paper2_title: string;
    winner?: number | null;
    reason?: string;
  } | null;
  currentProgress: number;
  totalProgress: number;
  progressMessage: string;
}

export function RankingLeaderboardView({
  papers,
  matchStats,
  currentMatch,
  lastMatch,
  currentProgress,
  totalProgress,
  progressMessage,
}: RankingLeaderboardViewProps) {
  // Get top papers (limit to 30 for performance)
  const topPapers = papers.slice(0, 30);
  const progressPercent =
    totalProgress > 0 ? (currentProgress / totalProgress) * 100 : 0;

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return (
        <Badge color="yellow" variant="filled" size="lg">
          🥇 {rank}
        </Badge>
      );
    } else if (rank === 2) {
      return (
        <Badge color="gray" variant="filled" size="lg">
          🥈 {rank}
        </Badge>
      );
    } else if (rank === 3) {
      return (
        <Badge color="orange" variant="filled" size="lg">
          🥉 {rank}
        </Badge>
      );
    }
    return (
      <Text size="sm" c="dimmed">
        {rank}
      </Text>
    );
  };

  const getEloChange = (change: number) => {
    if (change > 0) {
      return (
        <Text size="sm" c="green">
          +{change.toFixed(0)}
        </Text>
      );
    } else if (change < 0) {
      return (
        <Text size="sm" c="red">
          {change.toFixed(0)}
        </Text>
      );
    }
    return (
      <Text size="sm" c="dimmed">
        0
      </Text>
    );
  };

  return (
    <Paper p="xl" radius="md" withBorder>
      <Stack gap="lg">
        {/* Header */}
        <Box>
          <Title order={3} mb="xs">
            Ranking Papers
          </Title>
          <Group gap="xs">
            <Badge color="primary" size="lg" variant="light">
              {matchStats?.total_completed || 0} matches completed
            </Badge>
            {papers.length > 0 && (
              <Badge color="blue" size="lg" variant="light">
                {papers.length} papers
              </Badge>
            )}
          </Group>
        </Box>

        {/* Progress Bar */}
        <Box>
          <Text size="sm" c="dimmed" mb="xs">
            {progressMessage || `Match ${currentProgress} of ${totalProgress}`}
          </Text>
          <Progress
            value={progressPercent}
            size="lg"
            radius="xl"
            animated
            color="primary"
          />
        </Box>

        <Group align="flex-start" gap="lg" grow>
          {/* Left: Leaderboard Table */}
          <Box style={{ flex: 2 }}>
            <Card p="md" radius="md" withBorder>
              <Title order={4} mb="md">
                Live Leaderboard
              </Title>
              <ScrollArea h={500}>
                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th style={{ width: 60 }}>Rank</Table.Th>
                      <Table.Th style={{ width: 80 }}>Elo</Table.Th>
                      <Table.Th style={{ width: 80 }}>Change</Table.Th>
                      <Table.Th style={{ width: 100 }}>W/L/D</Table.Th>
                      <Table.Th>Title</Table.Th>
                      <Table.Th style={{ width: 60 }}>Year</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {topPapers.map((paper) => (
                      <Table.Tr key={paper.paper_id}>
                        <Table.Td>
                          {paper.rank ? getRankBadge(paper.rank) : "-"}
                        </Table.Td>
                        <Table.Td>
                          <Text fw={500} size="sm">
                            {paper.elo?.toFixed(0) || "-"}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          {paper.elo_change !== undefined
                            ? getEloChange(paper.elo_change)
                            : "-"}
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm" c="dimmed">
                            {paper.wins !== undefined &&
                            paper.losses !== undefined &&
                            paper.draws !== undefined
                              ? `${paper.wins}/${paper.losses}/${paper.draws}`
                              : "-"}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm" lineClamp={1}>
                            {paper.title}
                          </Text>
                        </Table.Td>
                        <Table.Td>
                          <Text size="sm" c="dimmed">
                            {paper.year || "-"}
                          </Text>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                    {papers.length === 0 && (
                      <Table.Tr>
                        <Table.Td colSpan={6}>
                          <Text c="dimmed" ta="center" py="xl">
                            Waiting for ranking to start...
                          </Text>
                        </Table.Td>
                      </Table.Tr>
                    )}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
              {papers.length > 30 && (
                <Text size="xs" c="dimmed" mt="xs" ta="center">
                  Showing top 30 of {papers.length} papers
                </Text>
              )}
            </Card>
          </Box>

          {/* Right: Match Information */}
          <Stack gap="md" style={{ flex: 1 }}>
            {/* Current Match */}
            <Card p="md" radius="md" withBorder>
              <Title order={5} mb="sm">
                Current Match
              </Title>
              {currentMatch ? (
                <Stack gap="xs">
                  <Box>
                    <Text size="sm" fw={500} c="cyan" mb={4}>
                      Paper 1
                    </Text>
                    <Text size="sm" lineClamp={2}>
                      {currentMatch.paper1_title}
                    </Text>
                  </Box>
                  <Divider
                    label={
                      <Text size="xs" c="dimmed" fw={700}>
                        VS
                      </Text>
                    }
                    labelPosition="center"
                  />
                  <Box>
                    <Text size="sm" fw={500} c="magenta" mb={4}>
                      Paper 2
                    </Text>
                    <Text size="sm" lineClamp={2}>
                      {currentMatch.paper2_title}
                    </Text>
                  </Box>
                  <Badge color="yellow" variant="light" size="sm" mt="xs">
                    ⚔️ Judging...
                  </Badge>
                </Stack>
              ) : (
                <Text size="sm" c="dimmed">
                  Waiting for next match...
                </Text>
              )}
            </Card>

            {/* Last Match Result */}
            <Card p="md" radius="md" withBorder>
              <Title order={5} mb="sm">
                Last Result
              </Title>
              {lastMatch ? (
                <Stack gap="xs">
                  {lastMatch.winner === 1 ? (
                    <>
                      <Box>
                        <Badge color="green" size="sm" mb={4}>
                          🏆 WINNER
                        </Badge>
                        <Text size="sm" fw={500} c="green" lineClamp={2}>
                          {lastMatch.paper1_title}
                        </Text>
                      </Box>
                      <Text size="xs" c="dimmed" lineClamp={2}>
                        vs {lastMatch.paper2_title}
                      </Text>
                    </>
                  ) : lastMatch.winner === 2 ? (
                    <>
                      <Text size="xs" c="dimmed" lineClamp={2}>
                        {lastMatch.paper1_title}
                      </Text>
                      <Box>
                        <Badge color="green" size="sm" mb={4}>
                          🏆 WINNER
                        </Badge>
                        <Text size="sm" fw={500} c="green" lineClamp={2}>
                          {lastMatch.paper2_title}
                        </Text>
                      </Box>
                    </>
                  ) : (
                    <>
                      <Badge color="yellow" size="sm" mb={4}>
                        🤝 DRAW
                      </Badge>
                      <Text size="sm" c="dimmed" lineClamp={2}>
                        {lastMatch.paper1_title}
                      </Text>
                      <Text size="sm" c="dimmed" lineClamp={2}>
                        {lastMatch.paper2_title}
                      </Text>
                    </>
                  )}
                  {lastMatch.reason && (
                    <Text size="xs" c="dimmed" mt="xs" lineClamp={3}>
                      {lastMatch.reason}
                    </Text>
                  )}
                </Stack>
              ) : (
                <Text size="sm" c="dimmed">
                  No matches completed yet
                </Text>
              )}
            </Card>

            {/* Match Statistics */}
            {matchStats && (
              <Card p="md" radius="md" withBorder>
                <Title order={5} mb="sm">
                  Statistics
                </Title>
                <Stack gap="xs">
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      Total Matches
                    </Text>
                    <Text size="sm" fw={500}>
                      {matchStats.total_completed}
                    </Text>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      Paper 1 Wins
                    </Text>
                    <Text size="sm" fw={500} c="cyan">
                      {matchStats.p1_wins}
                    </Text>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      Paper 2 Wins
                    </Text>
                    <Text size="sm" fw={500} c="magenta">
                      {matchStats.p2_wins}
                    </Text>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm" c="dimmed">
                      Draws
                    </Text>
                    <Text size="sm" fw={500} c="yellow">
                      {matchStats.draws}
                    </Text>
                  </Group>
                </Stack>
              </Card>
            )}
          </Stack>
        </Group>
      </Stack>
    </Paper>
  );
}
