import type { PaperCard as PaperCardType } from "@/lib/types";

// Brutalist shadow styles
const brutalShadow = { boxShadow: "3px 3px 0 #F3787A" };
const brutalShadowSmall = { boxShadow: "1px 1px 0 #F3787A" };

interface PaperCardProps {
  card: PaperCardType;
}

/**
 * Paper card component for displaying paper information - brutalist design.
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
      className="block bg-white p-4 border-2 border-black no-underline text-inherit transition-all duration-200 hover:no-underline"
      style={brutalShadow}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-xs text-gray-500">[{card.id}]</span>
        {card.year && (
          <span
            className="inline-flex items-center px-2 py-1 text-xs font-medium border border-black bg-white text-black"
            style={brutalShadowSmall}
          >
            {card.year}
          </span>
        )}
      </div>

      <h4 className="text-base mb-2 text-black font-semibold">{card.title}</h4>

      <p className="text-sm text-gray-600 mb-2">{card.claim}</p>

      <div className="flex justify-between items-center">
        <span className="text-sm lowercase">{card.citation_count} citations</span>
        {card.elo_rating && (
          <span
            className="inline-flex items-center px-2 py-1 text-xs font-bold border border-black bg-black text-white"
            style={brutalShadowSmall}
          >
            elo: {card.elo_rating.toFixed(0)}
          </span>
        )}
      </div>

      {card.paradigm_tags.length > 0 && (
        <div className="flex gap-1.5 flex-wrap mt-2">
          {card.paradigm_tags.map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 border border-black bg-white text-black lowercase"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}
