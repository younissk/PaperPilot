import { useState, FormEvent, useEffect } from "react";
import {
  TextInput,
  NumberInput,
  Button,
  Stack,
  Alert,
  Badge,
  Group,
  Text,
  Title,
  Modal,
  Collapse,
  Switch,
  Select,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useSearchMutation, useSearchStatus } from "../hooks/queries/useSearch";
import { DEFAULT_SEARCH_PARAMS, DEFAULT_PIPELINE_PARAMS } from "../config";
import { showError, showSuccess } from "../utils/notifications";
import { SearchProgressView } from "./SearchProgressView";
import { DetailedPipelineProgressView } from "./DetailedPipelineProgressView";
import { usePipeline } from "../hooks/usePipeline";
import type { Paper as PaperType } from "../services/api";

interface SearchFormProps {
  onSearchComplete?: (jobId: string, papers: PaperType[]) => void;
}

export function SearchForm({ onSearchComplete }: SearchFormProps) {
  const [query, setQuery] = useState("");
  const [enablePipeline, setEnablePipeline] = useState(true); // Default to pipeline mode
  const [numResults, setNumResults] = useState(
    DEFAULT_PIPELINE_PARAMS.num_results,
  );
  const [maxIterations, setMaxIterations] = useState(
    DEFAULT_PIPELINE_PARAMS.max_iterations,
  );
  const [maxAccepted, setMaxAccepted] = useState(
    DEFAULT_PIPELINE_PARAMS.max_accepted,
  );
  const [topN, setTopN] = useState(DEFAULT_PIPELINE_PARAMS.top_n);
  // ELO params
  const [kFactor, setKFactor] = useState(DEFAULT_PIPELINE_PARAMS.k_factor);
  const [pairing, setPairing] = useState<"swiss" | "random">(
    DEFAULT_PIPELINE_PARAMS.pairing,
  );
  const [earlyStop, setEarlyStop] = useState(
    DEFAULT_PIPELINE_PARAMS.early_stop,
  );
  const [eloConcurrency, setEloConcurrency] = useState(
    DEFAULT_PIPELINE_PARAMS.elo_concurrency,
  );
  // Report params
  const [reportTopK, setReportTopK] = useState(
    DEFAULT_PIPELINE_PARAMS.report_top_k,
  );
  const [jobId, setJobId] = useState<string | null>(null);
  const [opened, { toggle }] = useDisclosure(false);

  const searchMutation = useSearchMutation();
  const { data: searchData, error: pollingError } = useSearchStatus(
    jobId,
    jobId !== null && !enablePipeline,
  );

  // Pipeline hook
  const pipeline = usePipeline();

  // Handle search completion (non-pipeline mode)
  useEffect(() => {
    if (
      !enablePipeline &&
      searchData?.status === "completed" &&
      searchData.papers &&
      onSearchComplete
    ) {
      onSearchComplete(searchData.job_id, searchData.papers);
      showSuccess(
        `Search completed! Found ${searchData.papers.length} papers.`,
      );
      setJobId(null);
    }
  }, [searchData, enablePipeline, onSearchComplete]);

  // Handle search errors (non-pipeline mode)
  useEffect(() => {
    if (!enablePipeline && searchData?.status === "failed") {
      showError("Search failed. Please try again.");
      setJobId(null);
    }
  }, [searchData, enablePipeline]);

  useEffect(() => {
    if (!enablePipeline && pollingError) {
      showError(pollingError.message);
    }
  }, [pollingError, enablePipeline]);

  // Handle pipeline completion
  useEffect(() => {
    if (
      enablePipeline &&
      pipeline.isCompleted &&
      pipeline.papers.length > 0 &&
      onSearchComplete
    ) {
      onSearchComplete(pipeline.jobId || "", pipeline.papers);
      showSuccess(
        `Pipeline completed! Found ${pipeline.papers.length} papers and generated report.`,
      );
    }
  }, [
    pipeline.isCompleted,
    pipeline.papers,
    pipeline.jobId,
    enablePipeline,
    onSearchComplete,
  ]);

  // Handle pipeline errors
  useEffect(() => {
    if (enablePipeline && pipeline.isFailed && pipeline.error) {
      showError(`Pipeline failed: ${pipeline.error}`);
    }
  }, [pipeline.isFailed, pipeline.error, enablePipeline]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      showError("Please enter a search query");
      return;
    }

    try {
      if (enablePipeline) {
        // Use pipeline mode
        await pipeline.start({
          query: query.trim(),
          num_results: numResults,
          max_iterations: maxIterations,
          max_accepted: maxAccepted,
          top_n: topN,
          k_factor: kFactor,
          pairing: pairing,
          early_stop: earlyStop,
          elo_concurrency: eloConcurrency,
          report_top_k: reportTopK,
        });
        showSuccess("Pipeline started successfully!");
      } else {
        // Use regular search mode
        const response = await searchMutation.mutateAsync({
          query: query.trim(),
          num_results: numResults,
          max_iterations: maxIterations,
          max_accepted: maxAccepted,
          top_n: topN,
        });
        setJobId(response.job_id);
        showSuccess("Search started successfully!");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to start search";
      showError(errorMessage);
    }
  };

  const handleReset = () => {
    setQuery("");
    setNumResults(DEFAULT_PIPELINE_PARAMS.num_results);
    setMaxIterations(DEFAULT_PIPELINE_PARAMS.max_iterations);
    setMaxAccepted(DEFAULT_PIPELINE_PARAMS.max_accepted);
    setTopN(DEFAULT_PIPELINE_PARAMS.top_n);
    setKFactor(DEFAULT_PIPELINE_PARAMS.k_factor);
    setPairing(DEFAULT_PIPELINE_PARAMS.pairing);
    setEarlyStop(DEFAULT_PIPELINE_PARAMS.early_stop);
    setEloConcurrency(DEFAULT_PIPELINE_PARAMS.elo_concurrency);
    setReportTopK(DEFAULT_PIPELINE_PARAMS.report_top_k);
    setJobId(null);
    if (enablePipeline) {
      pipeline.reset();
    }
  };

  const currentStatus = enablePipeline
    ? pipeline.status
    : searchData?.status || (searchMutation.isPending ? "queued" : null);
  const totalAccepted = enablePipeline
    ? pipeline.papers.length
    : (searchData?.total_accepted ?? 0);
  const isProcessing = enablePipeline
    ? pipeline.isRunning
    : currentStatus === "running" ||
      currentStatus === "queued" ||
      searchMutation.isPending;

  return (
    <Stack gap="xl" style={{ width: "100%" }}>
      <Stack gap="md" align="center" style={{ textAlign: "center" }}>
        <Title
          order={1}
          size="3.5rem"
          fw={700}
          c="primary"
          style={{ lineHeight: 1.2 }}
        >
          Discover Research Papers
        </Title>
        <Text size="lg" c="dimmed" maw={600}>
          Use our intelligent snowball search to find and explore relevant
          academic papers. Enter your research query to get started.
        </Text>
      </Stack>

      <form onSubmit={handleSubmit} style={{ width: "100%" }}>
        <Stack gap="lg">
          <Group gap="md" align="flex-end" style={{ width: "100%" }}>
            <TextInput
              placeholder="e.g., LLM Based Recommendation Systems"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isProcessing}
              required
              size="lg"
              style={{ flex: 1 }}
            />
            <Button
              type="submit"
              disabled={isProcessing}
              loading={isProcessing}
              variant="filled"
              color="primary"
              size="lg"
            >
              {isProcessing
                ? enablePipeline
                  ? "Running Pipeline..."
                  : "Searching..."
                : "Search"}
            </Button>
          </Group>

          <Group justify="space-between" align="center">
            <Switch
              label="Full Pipeline (Search + Rank + Report)"
              description="Automatically rank papers and generate report"
              checked={enablePipeline}
              onChange={(e) => setEnablePipeline(e.currentTarget.checked)}
              disabled={isProcessing}
            />
            <Button variant="subtle" onClick={toggle} size="sm">
              {opened ? "Hide" : "Show"} Advanced Options
            </Button>
          </Group>

          <Collapse in={opened}>
            <Stack
              gap="md"
              p="md"
              style={{
                border: "1px solid var(--mantine-color-gray-6)",
                borderRadius: "4px",
              }}
            >
              <Text size="sm" fw={500} c="dimmed">
                Query Configuration
              </Text>
              <Group grow>
                <NumberInput
                  label="Results per Query"
                  description="Number of papers to retrieve per iteration"
                  value={numResults}
                  onChange={(value) =>
                    setNumResults(
                      typeof value === "number"
                        ? value
                        : DEFAULT_SEARCH_PARAMS.num_results,
                    )
                  }
                  min={1}
                  max={100}
                  disabled={isProcessing}
                />
                <NumberInput
                  label="Max Iterations"
                  description="Maximum number of search iterations"
                  value={maxIterations}
                  onChange={(value) =>
                    setMaxIterations(
                      typeof value === "number"
                        ? value
                        : DEFAULT_SEARCH_PARAMS.max_iterations,
                    )
                  }
                  min={1}
                  max={20}
                  disabled={isProcessing}
                />
              </Group>

              <Text size="sm" fw={500} c="dimmed" mt="md">
                Filtering & Ranking
              </Text>
              <Group grow>
                <NumberInput
                  label="Max Accepted Papers"
                  description="Maximum total papers to accept"
                  value={maxAccepted}
                  onChange={(value) =>
                    setMaxAccepted(
                      typeof value === "number"
                        ? value
                        : DEFAULT_PIPELINE_PARAMS.max_accepted,
                    )
                  }
                  min={10}
                  disabled={isProcessing}
                />
                <NumberInput
                  label="Top N Candidates"
                  description="Top candidates to consider per iteration"
                  value={topN}
                  onChange={(value) =>
                    setTopN(
                      typeof value === "number"
                        ? value
                        : DEFAULT_PIPELINE_PARAMS.top_n,
                    )
                  }
                  min={5}
                  disabled={isProcessing}
                />
              </Group>

              {enablePipeline && (
                <>
                  <Text size="sm" fw={500} c="dimmed" mt="md">
                    ELO Ranking Configuration
                  </Text>
                  <Group grow>
                    <NumberInput
                      label="K-Factor"
                      description="ELO update sensitivity (1-100)"
                      value={kFactor}
                      onChange={(value) =>
                        setKFactor(
                          typeof value === "number"
                            ? value
                            : DEFAULT_PIPELINE_PARAMS.k_factor,
                        )
                      }
                      min={1}
                      max={100}
                      step={1}
                      disabled={isProcessing}
                    />
                    <Select
                      label="Pairing Strategy"
                      description="How papers are matched"
                      value={pairing}
                      onChange={(value) =>
                        setPairing(
                          (value as "swiss" | "random") ||
                            DEFAULT_PIPELINE_PARAMS.pairing,
                        )
                      }
                      data={[
                        { value: "swiss", label: "Swiss (Recommended)" },
                        { value: "random", label: "Random" },
                      ]}
                      disabled={isProcessing}
                    />
                  </Group>
                  <Group grow>
                    <NumberInput
                      label="ELO Concurrency"
                      description="Parallel comparisons (1-20)"
                      value={eloConcurrency}
                      onChange={(value) =>
                        setEloConcurrency(
                          typeof value === "number"
                            ? value
                            : DEFAULT_PIPELINE_PARAMS.elo_concurrency,
                        )
                      }
                      min={1}
                      max={20}
                      disabled={isProcessing}
                    />
                    <Switch
                      label="Early Stop"
                      description="Stop when rankings stabilize"
                      checked={earlyStop}
                      onChange={(e) => setEarlyStop(e.currentTarget.checked)}
                      disabled={isProcessing}
                      mt="xl"
                    />
                  </Group>

                  <Text size="sm" fw={500} c="dimmed" mt="md">
                    Report Generation
                  </Text>
                  <Group grow>
                    <NumberInput
                      label="Top K Papers for Report"
                      description="Number of top papers to include"
                      value={reportTopK}
                      onChange={(value) =>
                        setReportTopK(
                          typeof value === "number"
                            ? value
                            : DEFAULT_PIPELINE_PARAMS.report_top_k,
                        )
                      }
                      min={1}
                      disabled={isProcessing}
                    />
                  </Group>
                </>
              )}
            </Stack>
          </Collapse>

          {enablePipeline ? (
            // Pipeline progress view
            pipeline.isRunning || pipeline.status === "queued" ? (
              <DetailedPipelineProgressView
                query={query}
                phase={pipeline.phase}
                // Search phase props
                searchStep={
                  pipeline.phase === "search" ? pipeline.phaseStep : 0
                }
                searchStepName={
                  pipeline.phase === "search" ? pipeline.phaseStepName : ""
                }
                searchProgress={
                  pipeline.phase === "search" ? pipeline.phaseProgress : 0
                }
                searchTotal={
                  pipeline.phase === "search" ? pipeline.phaseTotal : 0
                }
                searchMessage={
                  pipeline.phase === "search" ? pipeline.progressMessage : ""
                }
                searchIteration={pipeline.currentIteration}
                searchTotalIterations={pipeline.totalIterations}
                searchTotalAccepted={pipeline.totalAccepted}
                queryProfile={pipeline.queryProfile}
                // Ranking phase props
                rankingPapers={
                  pipeline.phase === "ranking" ? pipeline.papers : []
                }
                matchStats={pipeline.matchStats}
                currentMatch={pipeline.currentMatch}
                lastMatch={pipeline.lastMatch}
                rankingProgress={
                  pipeline.phase === "ranking" ? pipeline.phaseProgress : 0
                }
                rankingTotal={
                  pipeline.phase === "ranking" ? pipeline.phaseTotal : 0
                }
                rankingMessage={
                  pipeline.phase === "ranking" ? pipeline.progressMessage : ""
                }
                // Report phase props
                reportStep={
                  pipeline.phase === "report" ? pipeline.phaseStep : 0
                }
                reportStepName={
                  pipeline.phase === "report" ? pipeline.phaseStepName : ""
                }
                reportProgress={
                  pipeline.phase === "report" ? pipeline.phaseProgress : 0
                }
                reportTotal={
                  pipeline.phase === "report" ? pipeline.phaseTotal : 0
                }
                reportMessage={
                  pipeline.phase === "report" ? pipeline.progressMessage : ""
                }
              />
            ) : pipeline.isCompleted ? (
              <Alert color="primary" title="COMPLETED">
                Pipeline completed! Found {pipeline.papers.length} papers and
                generated report.
              </Alert>
            ) : pipeline.isFailed ? (
              <Alert color="error" title="FAILED">
                Pipeline failed: {pipeline.error || "Unknown error"}
              </Alert>
            ) : null
          ) : // Regular search progress view
          currentStatus &&
            (currentStatus === "running" || currentStatus === "queued") &&
            searchData ? (
            <SearchProgressView
              currentStep={searchData.current_step || 0}
              stepName={searchData.step_name || ""}
              currentProgress={searchData.current_progress || 0}
              totalProgress={searchData.total_progress || 0}
              progressMessage={searchData.progress_message || ""}
              currentIteration={searchData.current_iteration || 0}
              totalIterations={searchData.total_iterations || 0}
              totalAccepted={searchData.total_accepted || 0}
              query={query}
            />
          ) : currentStatus === "completed" ? (
            <Alert color="primary" title="COMPLETED">
              Search completed! Found {totalAccepted} papers.
            </Alert>
          ) : currentStatus === "failed" ? (
            <Alert color="error" title="FAILED">
              Search failed. Please try again.
            </Alert>
          ) : null}

          <Group justify="center">
            {((!enablePipeline &&
              (currentStatus === "completed" || currentStatus === "failed")) ||
              (enablePipeline &&
                (pipeline.isCompleted || pipeline.isFailed))) && (
              <Button variant="outline" onClick={handleReset}>
                New Search
              </Button>
            )}
          </Group>
        </Stack>
      </form>
    </Stack>
  );
}
