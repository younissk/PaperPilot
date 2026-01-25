import { NavLink, Stack, ScrollArea } from "@mantine/core";
import type { TocSection } from "./ReportView";

interface ReportTableOfContentsProps {
  sections: Array<TocSection>;
}

export function ReportTableOfContents({
  sections,
}: ReportTableOfContentsProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const renderSection = (section: TocSection, level: number = 0) => {
    return (
      <div key={section.id}>
        <NavLink
          href={`#${section.id}`}
          label={section.title}
          onClick={(e) => handleClick(e, section.id)}
          style={{
            textDecoration: "none",
            paddingLeft: level > 0 ? `${16 + level * 16}px` : undefined,
            fontSize: level > 0 ? "0.875rem" : undefined,
          }}
        />
        {section.children && section.children.length > 0 && (
          <Stack gap={0} style={{ marginLeft: "8px" }}>
            {section.children.map((child) => renderSection(child, level + 1))}
          </Stack>
        )}
      </div>
    );
  };

  return (
    <ScrollArea h="calc(100vh - 250px)">
      <Stack gap="xs">
        {sections.map((section) => renderSection(section))}
      </Stack>
    </ScrollArea>
  );
}
