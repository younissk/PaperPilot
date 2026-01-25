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

  const renderSection = (section: TocSection) => {
    return (
      <div key={section.id}>
        <NavLink
          href={`#${section.id}`}
          label={section.title}
          onClick={(e) => handleClick(e, section.id)}
          style={{
            textDecoration: "none",
          }}
        />
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
