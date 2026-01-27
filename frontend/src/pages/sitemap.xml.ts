/**
 * Runtime sitemap.xml generation for SEO.
 * Lists all report URLs that have completed reports, with accurate lastmod dates.
 */

import type { APIRoute } from "astro";
import { listQueries, getQueryMetadata, slugifyQuery } from "../lib/api";

export const GET: APIRoute = async ({ url }) => {
  const siteUrl = url.origin;

  // Fetch all queries
  let queries: string[] = [];
  try {
    const response = await listQueries();
    queries = response.queries || [];
  } catch (e) {
    console.error("Failed to fetch queries for sitemap:", e);
  }

  // Build sitemap entries for queries with reports
  const reportEntries: string[] = [];

  for (const query of queries) {
    try {
      const { metadata } = await getQueryMetadata(query);

      // Only include queries that have a report file
      if (metadata?.report_file) {
        const slug = slugifyQuery(query);
        const reportUrl = `${siteUrl}/report/${slug}`;

        // Use last_updated or report_generated_at for lastmod
        const lastmod = metadata.last_updated || metadata.report_generated_at;
        const lastmodDate = lastmod
          ? new Date(lastmod).toISOString().split("T")[0]
          : undefined;

        reportEntries.push(`
    <url>
      <loc>${reportUrl}</loc>${
        lastmodDate
          ? `
      <lastmod>${lastmodDate}</lastmod>`
          : ""
      }
      <changefreq>monthly</changefreq>
      <priority>0.8</priority>
    </url>`);
      }
    } catch {
      // Skip queries where metadata fetch fails
    }
  }

  // Build complete sitemap XML
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
      <loc>${siteUrl}/</loc>
      <changefreq>weekly</changefreq>
      <priority>1.0</priority>
    </url>
    <url>
      <loc>${siteUrl}/queries</loc>
      <changefreq>daily</changefreq>
      <priority>0.6</priority>
    </url>
    <url>
      <loc>${siteUrl}/about</loc>
      <changefreq>monthly</changefreq>
      <priority>0.5</priority>
    </url>${reportEntries.join("")}
</urlset>`;

  return new Response(sitemap.trim(), {
    headers: {
      "Content-Type": "application/xml",
      "Cache-Control": "public, max-age=3600", // Cache for 1 hour
    },
  });
};
