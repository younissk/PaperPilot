import { AppShell } from "@mantine/core";
import { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { AppBar } from "./AppBar";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <AppShell header={{ height: 55 }} padding="md">
      <AppShell.Header withBorder={false}>
        <AppBar />
      </AppShell.Header>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}
