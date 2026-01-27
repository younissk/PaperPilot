/**
 * Runtime robots.txt generation.
 * References sitemap and allows crawling of all public pages.
 */

import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ url }) => {
  const siteUrl = url.origin;

  const robotsTxt = `# PaperPilot robots.txt
User-agent: *
Allow: /
Allow: /report/
Allow: /queries
Allow: /about

# Sitemap location
Sitemap: ${siteUrl}/sitemap.xml
`;

  return new Response(robotsTxt, {
    headers: {
      "Content-Type": "text/plain",
      "Cache-Control": "public, max-age=86400", // Cache for 24 hours
    },
  });
};
