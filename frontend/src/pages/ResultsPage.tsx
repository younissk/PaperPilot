import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Container,
  Title,
  Button,
  Stack,
  Modal,
  Paper as MantinePaper,
  Text,
  Box,
  useMantineTheme,
} from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import { ReportForm } from "../components/ReportForm";
import { ReportProgressView } from "../components/ReportProgressView";
import { ReportView, buildReportSections } from "../components/ReportView";
import { ReportTableOfContents } from "../components/ReportTableOfContents";
import { useReportStatus } from "../hooks/queries/useReport";
import { getAllResults } from "../services/api";
import type { Paper } from "../services/api";

export function ResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const theme = useMantineTheme();
  const isMobile = useMediaQuery(`(max-width: ${theme.breakpoints.md}px)`);
  const queryFromUrl = searchParams.get("q");
  const decodedQuery = queryFromUrl ? decodeURIComponent(queryFromUrl) : null;

  const [papers, setPapers] = useState<Paper[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string | null>(decodedQuery);

  // Modal states
  const [showReportForm, setShowReportForm] = useState(false);

  // Job IDs for polling
  const [reportJobId, setReportJobId] = useState<string | null>(null);

  // Result data
  const [reportData, setReportData] = useState<Record<string, unknown> | null>(
    null,
  );

  // Result existence flags
  const [hasReport, setHasReport] = useState(false);
  const [loadingResults, setLoadingResults] = useState(true);

  // Update query from URL on mount or when URL changes
  useEffect(() => {
    if (decodedQuery && decodedQuery !== currentQuery) {
      setCurrentQuery(decodedQuery);
    } else if (!decodedQuery && currentQuery) {
      // Update URL if we have a query but no URL param
      setSearchParams({ q: encodeURIComponent(currentQuery) });
    }
  }, [decodedQuery]);

  // Polling hooks - always poll when jobId is set
  const { data: reportResponse } = useReportStatus(
    reportJobId,
    reportJobId !== null,
  );

  // Load existing results on mount using bulk endpoint
  useEffect(() => {
    if (currentQuery) {
      setLoadingResults(true);

      const loadResults = async () => {
        try {
          const allResults = await getAllResults(currentQuery);

          // Set papers from snowball results
          if (allResults.snowball?.papers) {
            setPapers(allResults.snowball.papers);
          }

          // Set result data and existence flags
          if (allResults.report) {
            setReportData(allResults.report);
            setHasReport(true);
          }
        } catch (error) {
          console.error("Failed to load results:", error);
        } finally {
          setLoadingResults(false);
        }
      };

      loadResults();
    } else {
      setLoadingResults(false);
    }
  }, [currentQuery]);

  // Update data from polling
  useEffect(() => {
    if (reportResponse?.report_data) {
      setReportData(reportResponse.report_data);
    }
    if (reportResponse?.status === "completed") {
      setHasReport(true);
      setShowReportForm(false);
    }
  }, [reportResponse]);

  if (!loadingResults && papers.length === 0 && !currentQuery) {
    return (
      <Container size="lg" py="xl">
        <Title order={1} mb="xl">
          Results
        </Title>
        <Text>No results to display. Start a search to see papers here.</Text>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <Title order={1}>
          {currentQuery ? `Results: ${currentQuery}` : "Search Results"}
        </Title>

        <Box
          style={{
            display: "grid",
            gridTemplateColumns:
              hasReport && reportData && !isMobile ? "220px 1fr" : "1fr",
            gap: "var(--mantine-spacing-xl)",
            alignItems: "start",
          }}
        >
          {/* Sticky TOC Sidebar - only show when report exists */}
          {hasReport && reportData && (
            <Box
              style={{
                position: isMobile ? "static" : "sticky",
                top: isMobile ? "auto" : 90,
                marginBottom: isMobile ? "var(--mantine-spacing-md)" : 0,
              }}
            >
              <MantinePaper p="md" radius={0}>
                <ReportTableOfContents
                  sections={buildReportSections(reportData)}
                />
              </MantinePaper>
            </Box>
          )}

          {/* Main Content Area */}
          <Stack gap="xl">
            {loadingResults ? (
              <Text c="dimmed">Checking for existing report...</Text>
            ) : reportJobId &&
              (reportResponse?.status === "running" ||
                reportResponse?.status === "queued") ? (
              <ReportProgressView
                currentStep={reportResponse?.current_step || 0}
                stepName={reportResponse?.step_name || ""}
                currentProgress={reportResponse?.current_progress || 0}
                totalProgress={reportResponse?.total_progress || 0}
                progressMessage={reportResponse?.progress_message || ""}
                query={currentQuery || ""}
              />
            ) : hasReport && reportData ? (
              <ReportView
                query={currentQuery || ""}
                reportData={reportData}
                isLoading={false}
                papers={papers}
              />
            ) : (
              <Button
                variant="gradient"
                gradient={{ from: "primary", to: "accent", deg: 135 }}
                onClick={() => setShowReportForm(true)}
                radius={0}
              >
                Generate Report
              </Button>
            )}
          </Stack>
        </Box>

        {/* Modals */}
        <Modal
          opened={showReportForm}
          onClose={() => setShowReportForm(false)}
          title="Generate Report"
          size="lg"
          radius={0}
        >
          <ReportForm
            query={currentQuery || ""}
            onReportStart={(jobId) => {
              setReportJobId(jobId);
              setShowReportForm(false);
            }}
            onReportComplete={() => {}}
            onCancel={() => setShowReportForm(false)}
          />
        </Modal>
      </Stack>
    </Container>
  );
}
