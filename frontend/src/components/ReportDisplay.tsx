/**
 * Component for displaying research report in a formatted, readable way.
 */

import { Title, Text, Stack, Group, Badge, Paper, Grid } from "@mantine/core";
import { PaperList } from "./PaperList";
import type { Paper as PaperType } from "../services/api";

interface ResearchItem {
  title: string;
  summary: string;
  paper_ids: string[];
}

interface OpenProblem {
  title: string;
  text: string;
  paper_ids: string[];
}

interface PaperCard {
  id: string;
  title: string;
  claim: string;
  paradigm_tags: string[];
  year?: number;
  citation_count: number;
  elo_rating?: number;
}

interface ReportData {
  query: string;
  generated_at: string;
  total_papers_used: number;
  introduction: string;
  current_research: ResearchItem[];
  open_problems: OpenProblem[];
  conclusion: string;
  paper_cards: PaperCard[];
}

interface ReportDisplayProps {
  data: ReportData | null;
  papers?: PaperType[];
  query?: string;
}

export function ReportDisplay({
  data,
  papers = [],
  query,
}: ReportDisplayProps) {
  if (!data) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Text c="dimmed">No report data available.</Text>
      </Stack>
    );
  }

  // Create a lookup map for paper cards
  const paperCardMap = new Map(data.paper_cards.map((card) => [card.id, card]));

  const handleCitationClick = (paperId: string) => {
    const element = document.getElementById(`paper-card-${paperId}`);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      // Highlight the card briefly
      element.style.transition = "background-color 0.3s";
      element.style.backgroundColor = "var(--mantine-color-primary-0)";
      setTimeout(() => {
        element.style.backgroundColor = "";
      }, 2000);
    }
  };

  const formatCitations = (text: string, paperIds: string[]): JSX.Element[] => {
    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    // Find all citation markers like [W1234567890]
    const citationRegex = /\[([W]\d+)\]/g;
    let match;
    let key = 0;

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${key++}`}>
            {text.substring(lastIndex, match.index)}
          </span>,
        );
      }

      // Add citation as a clickable badge/pill
      const paperId = match[1];
      const card = paperCardMap.get(paperId);
      parts.push(
        <Badge
          key={`cite-${key++}`}
          size="xs"
          variant="light"
          color="primary"
          style={{
            cursor: "pointer",
            margin: "0 2px",
            verticalAlign: "baseline",
          }}
          title={card?.title || paperId}
          onClick={() => handleCitationClick(paperId)}
        >
          [{paperId}]
        </Badge>,
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${key++}`}>{text.substring(lastIndex)}</span>,
      );
    }

    return parts.length > 0 ? parts : [<span key="text">{text}</span>];
  };

  return (
    <Stack gap="xl" p="md">
      <Stack gap="sm">
        <Title order={2}>Research Report: {data.query}</Title>
        <Group gap="md">
          <Text size="sm" c="dimmed">
            Generated: {new Date(data.generated_at).toLocaleString()}
          </Text>
          <Text size="sm" c="dimmed">
            {data.total_papers_used} papers used
          </Text>
        </Group>
      </Stack>

      <Stack gap="xl">
        <section id="introduction">
          <Title order={3} mb="md">
            Introduction
          </Title>
          <Text>{formatCitations(data.introduction, [])}</Text>
        </section>

        <section id="current-research">
          <Title order={3} mb="md">
            Current Research
          </Title>
          <Stack gap="md">
            {data.current_research.map((item, idx) => (
              <Stack key={idx} id={`current-research-${idx}`} gap="sm">
                <Title order={4}>{item.title}</Title>
                <Text>{formatCitations(item.summary, item.paper_ids)}</Text>
                {item.paper_ids.length > 0 && (
                  <Stack gap="xs" mt="sm">
                    <Text size="sm" fw={500}>
                      Referenced papers:
                    </Text>
                    <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
                      {item.paper_ids.map((paperId) => {
                        const card = paperCardMap.get(paperId);
                        return (
                          <li key={paperId}>
                            <Text
                              size="sm"
                              component="span"
                              c="primary"
                              fw={600}
                            >
                              [{paperId}]
                            </Text>
                            <Text size="sm" component="span" ml="xs">
                              {card ? card.title : paperId}
                            </Text>
                          </li>
                        );
                      })}
                    </ul>
                  </Stack>
                )}
              </Stack>
            ))}
          </Stack>
        </section>

        {data.open_problems && data.open_problems.length > 0 && (
          <section id="open-problems">
            <Title order={3} mb="md">
              Open Problems
            </Title>
            <Stack gap="md">
              {data.open_problems.map((problem, idx) => (
                <Paper
                  key={idx}
                  p="md"
                  withBorder
                  style={{
                    borderLeftColor: "var(--mantine-color-warning-6)",
                    borderLeftWidth: 4,
                  }}
                >
                  <Stack gap="sm">
                    <Title order={4} c="warning">
                      {problem.title}
                    </Title>
                    <Text>{problem.text}</Text>
                    {problem.paper_ids.length > 0 && (
                      <Group gap="xs" mt="sm">
                        <Text size="sm" fw={500}>
                          Sources:
                        </Text>
                        <Text size="sm" c="primary">
                          {problem.paper_ids.map((id) => `[${id}]`).join(", ")}
                        </Text>
                      </Group>
                    )}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </section>
        )}

        <section id="conclusion">
          <Title order={3} mb="md">
            Conclusion
          </Title>
          <Text>{formatCitations(data.conclusion, [])}</Text>
        </section>

        <section id="paper-cards">
          <Title order={3} mb="md">
            Paper Cards ({data.paper_cards.length})
          </Title>
          <Grid>
            {data.paper_cards.map((card) => (
              <Grid.Col key={card.id} span={{ base: 12, sm: 6, md: 4 }}>
                <Paper id={`paper-card-${card.id}`} p="md" withBorder h="100%">
                  <Stack gap="sm">
                    <Title order={4} size="h5">
                      {card.title}
                    </Title>
                    <Group gap="xs">
                      {card.year && <Badge>{card.year}</Badge>}
                      <Badge>{card.citation_count} citations</Badge>
                      {card.elo_rating && (
                        <Badge color="primary">
                          ELO: {card.elo_rating.toFixed(1)}
                        </Badge>
                      )}
                    </Group>
                    <Text size="sm" fs="italic">
                      <strong>Claim:</strong> {card.claim}
                    </Text>
                    {card.paradigm_tags && card.paradigm_tags.length > 0 && (
                      <Group gap="xs">
                        {card.paradigm_tags.map((tag, i) => (
                          <Badge key={i} variant="outline" size="sm">
                            {tag}
                          </Badge>
                        ))}
                      </Group>
                    )}
                    <Text size="xs" c="dimmed" ff="monospace">
                      ID: {card.id}
                    </Text>
                  </Stack>
                </Paper>
              </Grid.Col>
            ))}
          </Grid>
        </section>

        {papers.length > 0 && (
          <section id="sources">
            <Title order={3} mb="md">
              Sources
            </Title>
            <PaperList
              papers={papers}
              title={query ? `Results for: ${query}` : "Search Results"}
            />
          </section>
        )}
      </Stack>
    </Stack>
  );
}
