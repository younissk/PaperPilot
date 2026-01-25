import { createTheme } from "@mantine/core";

// Custom color definitions (10 shades from lightest to darkest)
const primaryColor = [
  "#fff4e6", // Lightest orange tint
  "#ffe0b8", // Very light orange
  "#ffcc8a", // Light orange
  "#ffb85c", // Medium-light orange
  "#ffa42e", // Medium orange
  "#FF8C42", // Main primary color (orangish)
  "#e67a2e", // Medium-dark orange
  "#cc6820", // Dark orange
  "#b35612", // Very dark orange
  "#994404", // Darkest orange
];

const accentColor = [
  "#e0faf8",
  "#b8f5f0",
  "#90f0e8",
  "#68ebe0",
  "#7CE1D7", // Main accent color
  "#5cc4b8",
  "#4aa799",
  "#388a7a",
  "#266d5b",
  "#14503c",
];

const errorColor = [
  "#fef0f0",
  "#fdd8d8",
  "#fcc0c0",
  "#fba8a8",
  "#fa9090",
  "#F3787A", // Main error color
  "#c25e60",
  "#914646",
  "#602e2c",
  "#2f1612",
];

const warningColor = [
  "#fef9e8",
  "#fdf1d1",
  "#fce9ba",
  "#fbe1a3",
  "#fad98c",
  "#F8D797", // Main warning color
  "#c6ac79",
  "#94815b",
  "#62563d",
  "#302b1f",
];

export const theme = createTheme({
  primaryColor: "primary",
  colors: {
    primary: primaryColor,
    accent: accentColor,
    error: errorColor,
    warning: warningColor,
  },
  defaultRadius: 0,
  fontFamily:
    'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
  headings: {
    fontFamily:
      'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif',
    fontWeight: "600",
  },
  white: "#FDFDFD",
  black: "#1a1a1a",
  defaultGradient: {
    from: "#FF8C42",
    to: "#7CE1D7",
    deg: 135,
  },
});
