import { Box, Stack } from "@mantine/core";
import { SearchForm } from "../components/SearchForm";
import { useNavigate } from "react-router-dom";
import { showSuccess } from "../utils/notifications";
import type { Paper as PaperType } from "../services/api";

export function SearchPage() {
  const navigate = useNavigate();

  const handleSearchComplete = (jobId: string, papers: PaperType[]) => {
    showSuccess(`Search completed! Found ${papers.length} papers.`);
    const query = papers[0]?.title || "Search Results";
    navigate(`/results?q=${encodeURIComponent(query)}`);
  };

  return (
    <Box
      style={{
        minHeight: "100%",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Stack
        gap="xl"
        align="center"
        style={{
          width: "100%",
          maxWidth: 800,
          padding: "var(--mantine-spacing-xl)",
        }}
      >
        <SearchForm onSearchComplete={handleSearchComplete} />
      </Stack>
    </Box>
  );
}
