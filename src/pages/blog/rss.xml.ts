import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import config from "@/config/config.json";

const escape = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export const GET: APIRoute = async () => {
  const site = config.site.base_url.replace(/\/$/, "");
  const posts = (await getCollection("posts"))
    .filter((p) => !p.data.draft)
    .sort((a, b) => {
      const ad = a.data.date ? new Date(a.data.date).getTime() : 0;
      const bd = b.data.date ? new Date(b.data.date).getTime() : 0;
      return bd - ad;
    });

  const items = posts
    .map((p) => {
      const url = `${site}/blog/${p.id.replace(/\.mdx?$/, "")}/`;
      const pubDate = p.data.date ? new Date(p.data.date).toUTCString() : new Date().toUTCString();
      const desc = p.data.description || "";
      return `    <item>
      <title>${escape(p.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${pubDate}</pubDate>
      <description>${escape(desc)}</description>
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escape(config.site.title)}</title>
    <link>${site}</link>
    <atom:link href="${site}/blog/rss.xml" rel="self" type="application/rss+xml" />
    <description>${escape(config.metadata.meta_description || "")}</description>
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
${items}
  </channel>
</rss>`;

  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
};
