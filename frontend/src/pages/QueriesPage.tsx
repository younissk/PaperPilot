import { Container, Title } from "@mantine/core";
import { QueryList } from "../components/QueryList";
import { useNavigate } from "react-router-dom";
import type { Paper } from "../services/api";

export function QueriesPage() {
  const navigate = useNavigate();

  const handleSelectQuery = (query: string, papers: Paper[]) => {
    navigate(`/results?q=${encodeURIComponent(query)}`);
  };

  return (
    <Container size="lg" py="xl">
      <Title order={1} mb="xl">
        Previous Queries
      </Title>
      <QueryList onSelectQuery={handleSelectQuery} />
    </Container>
  );
}
