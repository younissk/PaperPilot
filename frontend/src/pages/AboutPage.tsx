import { Container, Title, Text, Stack, Paper } from '@mantine/core';

export function AboutPage() {
  return (
    <Container size="lg" py="xl">
      <Stack gap="xl">
        <Title order={1}>About PaperPilot</Title>
        <Paper p="md" withBorder>
          <Stack gap="md">
            <Text size="lg" fw={500}>AI-powered academic literature discovery</Text>
            <Text>
              PaperPilot helps researchers discover and analyze academic papers through intelligent
              search, ranking, visualization, and automated report generation.
            </Text>
            <Text>
              Features include:
            </Text>
            <ul>
              <li>Semantic search with snowball sampling</li>
              <li>ELO-based paper ranking</li>
              <li>Citation graph visualization</li>
              <li>Timeline analysis</li>
              <li>Paper clustering</li>
              <li>Automated research report generation</li>
            </ul>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}
