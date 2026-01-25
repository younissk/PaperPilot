import { Container, Title } from "@mantine/core";
import { SearchForm } from "../components/SearchForm";
import { useNavigate } from "react-router-dom";
import { showError, showSuccess } from "../utils/notifications";
import type { Paper } from "../services/api";

export function SearchPage() {
  const navigate = useNavigate();

  const handleSearchComplete = (jobId: string, papers: Paper[]) => {
    showSuccess(`Search completed! Found ${papers.length} papers.`);
    const query = papers[0]?.title || "Search Results";
    navigate(`/results?q=${encodeURIComponent(query)}`);
  };

  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="xl">
        Start New Search
      </Title>
      <SearchForm onSearchComplete={handleSearchComplete} />
    </Container>
  );
}
