import { Group, Text, Button, Stack, Box } from "@mantine/core";
import { Link, useLocation } from "react-router-dom";
import { useHealthCheck } from "../hooks/queries/useHealthCheck";

export function AppBar() {
  const location = useLocation();
  const { data: healthData, isError } = useHealthCheck();

  return (
    <Box
      h="100%"
      style={{
        backgroundColor: "var(--mantine-color-primary-6)",
        display: "flex",
        alignItems: "center",
      }}
    >
      <Group
        justify="space-between"
        h="100%"
        style={{ flex: 1, width: "100%" }}
      >
        <Group style={{ paddingLeft: "var(--mantine-spacing-md)" }}>
          <Text
            component={Link}
            to="/"
            fw={700}
            size="xl"
            c="white"
            style={{ textDecoration: "none" }}
          >
            PaperPilot
          </Text>
          <Stack gap={4}>
            <Group gap="xs">
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: isError
                    ? "#F3787A"
                    : healthData
                      ? "#7CE1D7"
                      : "#F8D797",
                  animation:
                    !healthData && !isError
                      ? "pulse 1.5s ease-in-out infinite"
                      : "none",
                }}
              />
              <Text size="xs" c="white" style={{ opacity: 0.9 }}>
                {isError
                  ? "API Offline"
                  : healthData
                    ? "API Online"
                    : "Checking..."}
              </Text>
            </Group>
          </Stack>
        </Group>
        <Group gap={0} h="100%" style={{ marginLeft: "auto" }}>
          <Button
            component={Link}
            to="/queries"
            h="100%"
            variant="subtle"
            style={{
              borderRadius: 0,
              backgroundColor: "white",
              color: "var(--mantine-color-primary-6)",
            }}
          >
            Searches
          </Button>
          <Button
            component={Link}
            to="/about"
            h="100%"
            variant="subtle"
            style={{
              borderRadius: 0,
              backgroundColor: "white",
              color: "var(--mantine-color-primary-6)",
            }}
          >
            About
          </Button>
        </Group>
      </Group>
    </Box>
  );
}
