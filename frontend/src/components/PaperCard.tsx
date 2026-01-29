import type { PaperCard as PaperCardType } from "@/lib/types";

interface PaperCardProps {
  card: PaperCardType;
}

/**
 * Paper card component for displaying paper information.
 */
export function PaperCard({ card }: PaperCardProps) {
  const isOpenAlex = card.id.startsWith("W");
  const url = isOpenAlex
    ? `https://openalex.org/${card.id}`
    : `https://openalex.org/search?q=${encodeURIComponent(card.id)}`;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-gray-50 p-4 rounded-md border border-gray-200 no-underline text-inherit transition-all duration-200 hover:border-primary-400 hover:shadow-sm hover:no-underline"
    >
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-xs text-gray-500">[{card.id}]</span>
        {card.year && (
          <span className="badge-secondary inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-gray-100 text-gray-700">
            {card.year}
          </span>
        )}
      </div>

      <h4 className="text-base mb-2 text-gray-800">{card.title}</h4>

      <p className="text-sm text-gray-500 mb-2">{card.claim}</p>

      <div className="flex justify-between items-center">
        <span className="text-sm">{card.citation_count} citations</span>
        {card.elo_rating && (
          <span className="badge inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-primary-100 text-primary-700">
            ELO: {card.elo_rating.toFixed(0)}
          </span>
        )}
      </div>

      {card.paradigm_tags.length > 0 && (
        <div className="flex gap-1.5 flex-wrap mt-2">
          {card.paradigm_tags.map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 bg-gray-200 rounded text-gray-600"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}
