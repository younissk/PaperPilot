import { Loader, Text, Stack } from "@mantine/core";
import { ReportDisplay } from "./ReportDisplay";
import type { Paper } from "../services/api";

export interface TocSection {
  id: string;
  title: string;
  children?: TocSection[];
}

interface ReportViewProps {
  query: string;
  reportData: Record<string, unknown> | null;
  isLoading?: boolean;
  papers?: Paper[];
}

export function buildReportSections(
  reportData: Record<string, unknown> | null,
): TocSection[] {
  const baseSections: TocSection[] = [
    { id: "introduction", title: "Introduction" },
    {
      id: "current-research",
      title: "Current Research",
      children:
        reportData && Array.isArray((reportData as any).current_research)
          ? (reportData as any).current_research.map(
              (item: any, idx: number) => ({
                id: `current-research-${idx}`,
                title: item.title || `Research Item ${idx + 1}`,
              }),
            )
          : undefined,
    },
    { id: "open-problems", title: "Open Problems" },
    { id: "conclusion", title: "Conclusion" },
    { id: "sources", title: "Sources" },
  ];

  return baseSections;
}

export function ReportView({
  query,
  reportData,
  isLoading,
  papers = [],
}: ReportViewProps) {
  if (isLoading || !reportData) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader size="lg" />
        <Text>Generating report...</Text>
      </Stack>
    );
  }

  return (
    <ReportDisplay data={reportData as any} papers={papers} query={query} />
  );
}
