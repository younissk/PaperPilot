import { useState } from "react";
import {
  Title,
  Stack,
  Group,
  Select,
  Button,
  Card,
  Badge,
  Text,
  ActionIcon,
  Modal,
} from "@mantine/core";
import type { Paper } from "../services/api";

interface PaperListProps {
  papers: Paper[];
  title?: string;
}

export function PaperList({ papers, title = "Papers" }: PaperListProps) {
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [sortBy, setSortBy] = useState<
    "year" | "citations" | "confidence" | "depth"
  >("citations");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const sortedPapers = [...papers].sort((a, b) => {
    let aVal: number;
    let bVal: number;

    switch (sortBy) {
      case "year":
        aVal = a.year ?? 0;
        bVal = b.year ?? 0;
        break;
      case "citations":
        aVal = a.citation_count;
        bVal = b.citation_count;
        break;
      case "confidence":
        aVal = a.judge_confidence;
        bVal = b.judge_confidence;
        break;
      case "depth":
        aVal = a.depth;
        bVal = b.depth;
        break;
      default:
        return 0;
    }

    if (sortOrder === "asc") {
      return aVal - bVal;
    } else {
      return bVal - aVal;
    }
  });

  if (papers.length === 0) {
    return (
      <Stack gap="md">
        <Title order={2}>{title}</Title>
        <Text c="dimmed">No papers to display.</Text>
      </Stack>
    );
  }

  return (
    <Stack gap="md">
      <Group justify="space-between" align="center">
        <Title order={2}>
          {title} ({papers.length})
        </Title>
        <Group gap="xs">
          <Select
            value={sortBy}
            onChange={(value) => setSortBy(value as typeof sortBy)}
            data={[
              { value: "citations", label: "Citations" },
              { value: "year", label: "Year" },
              { value: "confidence", label: "Confidence" },
              { value: "depth", label: "Depth" },
            ]}
            w={150}
          />
          <ActionIcon
            variant="light"
            onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
            title={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
          >
            {sortOrder === "asc" ? "↑" : "↓"}
          </ActionIcon>
        </Group>
      </Group>

      <Stack gap="md">
        {sortedPapers.map((paper) => {
          return (
            <Card
              key={paper.paper_id}
              shadow="sm"
              padding="lg"
              radius={0}
              withBorder
              style={{ cursor: "pointer" }}
              onClick={() => setSelectedPaper(paper)}
            >
              <Stack gap="sm">
                <Group gap="xs" align="center" wrap="wrap">
                  <Title order={4} style={{ margin: 0 }}>
                    {paper.title}
                  </Title>
                  {paper.year && (
                    <Badge color="accent" radius={0}>
                      {paper.year}
                    </Badge>
                  )}
                  <Badge color="primary" radius={0}>
                    {paper.citation_count} citations
                  </Badge>
                </Group>
              </Stack>
            </Card>
          );
        })}
      </Stack>

      <Modal
        opened={selectedPaper !== null}
        onClose={() => setSelectedPaper(null)}
        title={selectedPaper?.title}
        size="lg"
        radius={0}
      >
        {selectedPaper && (
          <Stack gap="md">
            <Group gap="xs">
              {selectedPaper.year && (
                <Badge color="accent" radius={0}>
                  {selectedPaper.year}
                </Badge>
              )}
              <Badge color="primary" radius={0}>
                {selectedPaper.citation_count} citations
              </Badge>
              <Badge variant="outline" radius={0}>
                Depth: {selectedPaper.depth}
              </Badge>
            </Group>

            <Text size="sm" fw={500}>
              Abstract:
            </Text>
            <Text size="sm" c="dimmed">
              {selectedPaper.abstract || "No abstract available"}
            </Text>

            <Group gap="xs">
              <Text size="sm" fw={500}>
                Edge type:
              </Text>
              <Text size="sm" c="primary">
                {selectedPaper.edge_type}
              </Text>
              {selectedPaper.discovered_from && (
                <>
                  <Text size="sm" fw={500}>
                    From:
                  </Text>
                  <Text size="sm" c="primary">
                    {selectedPaper.discovered_from}
                  </Text>
                </>
              )}
            </Group>

            <Text size="sm" c="dimmed" fs="italic">
              <strong>Reason:</strong> {selectedPaper.judge_reason}
            </Text>
          </Stack>
        )}
      </Modal>
    </Stack>
  );
}
