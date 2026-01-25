/**
 * Component for displaying research report in a formatted, readable way.
 */

import { Title, Text, Stack, Group, Badge, Paper, Popover, Anchor } from "@mantine/core";
import { useState, useMemo } from "react";
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

  // Create a lookup map for paper cards (memoized for performance)
  const paperCardMap = useMemo(
    () => new Map(data.paper_cards.map((card) => [card.id, card])),
    [data.paper_cards]
  );

  // State for popover management - track unique citation instance keys
  const [openedPopover, setOpenedPopover] = useState<string | null>(null);

  // Get paper link - handles different ID formats
  const getPaperLink = (paperId: string): string | null => {
    // OpenAlex IDs start with W, format: https://openalex.org/W1234567890
    if (paperId.startsWith("W")) {
      return `https://openalex.org/${paperId}`;
    }
    // S2 format IDs don't have direct links, return null
    if (paperId.startsWith("S2:")) {
      return null;
    }
    // Fallback: search on OpenAlex
    return `https://openalex.org/search?q=${encodeURIComponent(paperId)}`;
  };

  // Reusable function to render a clickable citation
  const renderCitation = (paperId: string, uniqueKey: string | number): JSX.Element => {
    const card = paperCardMap.get(paperId);
    const citationKey = String(uniqueKey);
    const isOpen = openedPopover === citationKey;
    const link = getPaperLink(paperId);

    return (
      <Popover
        key={citationKey}
        opened={isOpen}
        onChange={(opened) => setOpenedPopover(opened ? citationKey : null)}
        position="bottom"
        withArrow
        shadow="md"
        withinPortal
        transitionProps={{ duration: 150 }}
      >
        <Popover.Target>
          <Badge
            size="xs"
            variant="light"
            color="primary"
            style={{
              cursor: "pointer",
              margin: "0 2px",
              verticalAlign: "baseline",
              display: "inline-block",
            }}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setOpenedPopover(isOpen ? null : citationKey);
            }}
          >
            [{paperId}]
          </Badge>
        </Popover.Target>
        <Popover.Dropdown>
          <Stack gap="sm" style={{ maxWidth: 300 }}>
            {card ? (
              <>
                <Text size="sm" fw={600}>
                  {card.title}
                </Text>
                <Text size="xs" c="dimmed">
                  {card.claim}
                </Text>
                <Group gap="xs">
                  {card.year && <Badge size="xs">{card.year}</Badge>}
                  <Badge size="xs">{card.citation_count} citations</Badge>
                  {card.elo_rating && (
                    <Badge size="xs" color="primary">
                      ELO: {card.elo_rating.toFixed(1)}
                    </Badge>
                  )}
                </Group>
                {card.paradigm_tags && card.paradigm_tags.length > 0 && (
                  <Group gap="xs">
                    {card.paradigm_tags.map((tag, i) => (
                      <Badge key={i} variant="outline" size="xs">
                        {tag}
                      </Badge>
                    ))}
                  </Group>
                )}
              </>
            ) : (
              <Text size="sm">Paper ID: {paperId}</Text>
            )}
            {link && (
              <Anchor
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                size="sm"
              >
                View on OpenAlex →
              </Anchor>
            )}
          </Stack>
        </Popover.Dropdown>
      </Popover>
    );
  };

  const formatCitations = (
    text: string,
    paperIds: string[],
    contextPrefix: string = "cite"
  ): JSX.Element[] => {
    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    // Find all citation markers - matches [W1234567890], [S2:abc123...], and other formats
    // Pattern matches: [ followed by alphanumeric, underscore, colon, or hyphen characters, then ]
    const citationRegex = /\[([A-Za-z0-9_:-]+)\]/g;
    let match;
    let key = 0;

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${contextPrefix}-${key++}`}>
            {text.substring(lastIndex, match.index)}
          </span>,
        );
      }

      // Add citation as a clickable badge/pill with popover
      // Use context prefix + position for unique key
      const paperId = match[1];
      const uniqueKey = `${contextPrefix}-${paperId}-${match.index}`;
      parts.push(renderCitation(paperId, uniqueKey));

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${contextPrefix}-${key++}`}>
          {text.substring(lastIndex)}
        </span>,
      );
    }

    return parts.length > 0 ? parts : [<span key={`text-${contextPrefix}`}>{text}</span>];
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
          <Text>{formatCitations(data.introduction, [], "intro")}</Text>
        </section>

        <section id="current-research">
          <Title order={3} mb="md">
            Current Research
          </Title>
          <Stack gap="md">
            {data.current_research.map((item, idx) => (
              <Stack key={idx} id={`current-research-${idx}`} gap="sm">
                <Title order={4}>{item.title}</Title>
                <Text>
                  {formatCitations(item.summary, item.paper_ids, `research-${idx}`)}
                </Text>
                {item.paper_ids.length > 0 && (
                  <Stack gap="xs" mt="sm">
                    <Text size="sm" fw={500}>
                      Referenced papers:
                    </Text>
                    <Group gap="xs" wrap="wrap">
                      {item.paper_ids.map((paperId, pidIdx) => {
                        const card = paperCardMap.get(paperId);
                        return (
                          <Group key={`${idx}-${paperId}-${pidIdx}`} gap="xs" align="center">
                            {renderCitation(paperId, `ref-${idx}-${paperId}-${pidIdx}`)}
                            {card && (
                              <Text size="sm" component="span">
                                {card.title}
                              </Text>
                            )}
                          </Group>
                        );
                      })}
                    </Group>
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
                    <Title
                      order={4}
                      c="warning"
                      style={{ wordBreak: "break-word", overflowWrap: "break-word" }}
                    >
                      {problem.title}
                    </Title>
                    <Text>
                      {formatCitations(problem.text, problem.paper_ids, `problem-${idx}`)}
                    </Text>
                    {problem.paper_ids.length > 0 && (
                      <Group gap="xs" mt="sm" wrap="wrap" align="center">
                        <Text size="sm" fw={500}>
                          Sources:
                        </Text>
                        {problem.paper_ids.map((id, pidIdx) =>
                          renderCitation(id, `source-${idx}-${id}-${pidIdx}`)
                        )}
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
          <Text>{formatCitations(data.conclusion, [], "conclusion")}</Text>
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
