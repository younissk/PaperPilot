import { useState, useEffect, useCallback } from "react";
import {
  Grid,
  Button,
  Text,
  Stack,
  Group,
  Paper,
  Title,
  Badge,
} from "@mantine/core";

interface Card {
  id: number;
  emoji: string;
  isFlipped: boolean;
  isMatched: boolean;
}

const EMOJI_PAIRS = ["🎯", "🚀", "📚", "🔬", "💡", "⚡", "🎨", "🌟"];

function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

function initializeCards(): Card[] {
  const emojis = [...EMOJI_PAIRS, ...EMOJI_PAIRS];
  const shuffled = shuffleArray(emojis);
  return shuffled.map((emoji, index) => ({
    id: index,
    emoji,
    isFlipped: false,
    isMatched: false,
  }));
}

export function MemoryGame() {
  const [cards, setCards] = useState<Card[]>(initializeCards());
  const [flippedCards, setFlippedCards] = useState<number[]>([]);
  const [moves, setMoves] = useState(0);
  const [time, setTime] = useState(0);
  const [isGameWon, setIsGameWon] = useState(false);
  const [isGameActive, setIsGameActive] = useState(true);

  // Timer effect
  useEffect(() => {
    if (!isGameActive || isGameWon) return;

    const interval = setInterval(() => {
      setTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isGameActive, isGameWon]);

  // Check for matches
  useEffect(() => {
    if (flippedCards.length === 2) {
      const [firstId, secondId] = flippedCards;
      const firstCard = cards[firstId];
      const secondCard = cards[secondId];

      if (firstCard.emoji === secondCard.emoji) {
        // Match found
        setCards((prevCards) =>
          prevCards.map((card) =>
            card.id === firstId || card.id === secondId
              ? { ...card, isMatched: true, isFlipped: true }
              : card,
          ),
        );
        setFlippedCards([]);
        setMoves((prev) => prev + 1);

        // Check if all cards are matched
        setTimeout(() => {
          setCards((prevCards) => {
            const allMatched = prevCards.every((card) => card.isMatched);
            if (allMatched) {
              setIsGameWon(true);
              setIsGameActive(false);
            }
            return prevCards;
          });
        }, 500);
      } else {
        // No match - flip back after a delay
        setTimeout(() => {
          setCards((prevCards) =>
            prevCards.map((card) =>
              card.id === firstId || card.id === secondId
                ? { ...card, isFlipped: false }
                : card,
            ),
          );
          setFlippedCards([]);
          setMoves((prev) => prev + 1);
        }, 1000);
      }
    }
  }, [flippedCards, cards]);

  const handleCardClick = useCallback(
    (cardId: number) => {
      const card = cards[cardId];

      // Don't allow clicking if:
      // - Card is already flipped or matched
      // - Two cards are already flipped
      // - Game is won
      if (
        card.isFlipped ||
        card.isMatched ||
        flippedCards.length >= 2 ||
        isGameWon
      ) {
        return;
      }

      // Flip the card
      setCards((prevCards) =>
        prevCards.map((c) => (c.id === cardId ? { ...c, isFlipped: true } : c)),
      );
      setFlippedCards((prev) => [...prev, cardId]);
    },
    [cards, flippedCards.length, isGameWon],
  );

  const handleReset = () => {
    setCards(initializeCards());
    setFlippedCards([]);
    setMoves(0);
    setTime(0);
    setIsGameWon(false);
    setIsGameActive(true);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <Stack gap="sm">
      <Group justify="center" align="center">
        <Group gap="md">
          <Badge size="md" variant="light" color="primary">
            Moves: {moves}
          </Badge>
          <Badge size="md" variant="light" color="accent">
            Time: {formatTime(time)}
          </Badge>
        </Group>
      </Group>

      {isGameWon && (
        <Paper
          p="sm"
          style={{ backgroundColor: "var(--mantine-color-primary-0)" }}
        >
          <Stack gap="xs" align="center">
            <Text size="lg" fw={700} c="primary">
              🎉 Congratulations! 🎉
            </Text>
            <Text size="xs" c="dimmed">
              You completed the game in {moves} moves and {formatTime(time)}!
            </Text>
          </Stack>
        </Paper>
      )}

      <Grid gutter="xs">
        {cards.map((card) => (
          <Grid.Col key={card.id} span={3}>
            <Paper
              p="sm"
              style={{
                aspectRatio: "1",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor:
                  card.isMatched || card.isFlipped || flippedCards.length >= 2
                    ? "default"
                    : "pointer",
                backgroundColor: card.isMatched
                  ? "var(--mantine-color-primary-1)"
                  : card.isFlipped
                    ? "var(--mantine-color-body)"
                    : "var(--mantine-color-gray-8)",
                border: `2px solid ${
                  card.isMatched
                    ? "var(--mantine-color-primary-6)"
                    : "var(--mantine-color-gray-6)"
                }`,
                transition: "all 0.3s ease",
                transform: card.isFlipped ? "scale(1.05)" : "scale(1)",
                opacity: card.isMatched ? 0.7 : 1,
              }}
              onClick={() => handleCardClick(card.id)}
            >
              <Text size="1.75rem" style={{ userSelect: "none" }}>
                {card.isFlipped || card.isMatched ? card.emoji : "❓"}
              </Text>
            </Paper>
          </Grid.Col>
        ))}
      </Grid>

      <Group justify="center" mt="xs">
        <Button onClick={handleReset} variant="outline" size="sm">
          Reset Game
        </Button>
      </Group>
    </Stack>
  );
}
