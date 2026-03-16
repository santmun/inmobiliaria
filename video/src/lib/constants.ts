import { VideoStyle, StylePreset } from "./types";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// Scene durations in frames
export const TRANSITION_FRAMES = 15;

export const SCENES = {
  opening: { start: 0, duration: 60 },
  hero: { start: 60, duration: 180 },
  stats: { start: 240, duration: 120 },
  gallery: { start: 360, duration: 180 },
  cta: { start: 540, duration: 60 },
} as const;

export const TOTAL_DURATION = 600;

// ─── Style Presets ───────────────────────────────────────────────
export const STYLE_PRESETS: Record<VideoStyle, StylePreset> = {
  elegante: {
    bgColor: "#0f2137",
    bgSecondary: "#1a365d",
    accentColor: "#c9a84c",
    ctaColor: "#c8102e",
    textColor: "#ffffff",
    textLight: "rgba(255,255,255,0.7)",
    fontHeading: "'Playfair Display', Georgia, serif",
    fontBody: "'DM Sans', 'Helvetica Neue', sans-serif",
    animSpeed: 1,
  },
  moderno: {
    bgColor: "#111111",
    bgSecondary: "#1e1e1e",
    accentColor: "#00d4ff",
    ctaColor: "#ff3366",
    textColor: "#ffffff",
    textLight: "rgba(255,255,255,0.65)",
    fontHeading: "'DM Sans', 'Helvetica Neue', sans-serif",
    fontBody: "'DM Sans', 'Helvetica Neue', sans-serif",
    animSpeed: 1.3,
  },
  minimalista: {
    bgColor: "#faf8f5",
    bgSecondary: "#f0ece6",
    accentColor: "#2c2420",
    ctaColor: "#c9a84c",
    textColor: "#2c2420",
    textLight: "rgba(44,36,32,0.55)",
    fontHeading: "'Playfair Display', Georgia, serif",
    fontBody: "'DM Sans', 'Helvetica Neue', sans-serif",
    animSpeed: 0.85,
  },
};

// ─── Helper functions ────────────────────────────────────────────

export function adjustBrightness(hex: string, amount: number): string {
  const h = hex.replace("#", "");
  const r = Math.max(0, Math.min(255, parseInt(h.substring(0, 2), 16) + amount));
  const g = Math.max(0, Math.min(255, parseInt(h.substring(2, 4), 16) + amount));
  const b = Math.max(0, Math.min(255, parseInt(h.substring(4, 6), 16) + amount));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

export function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/**
 * Resolve final style from props: explicit colors override preset.
 */
export function resolveStyle(
  videoStyle?: VideoStyle,
  colorBackground?: string,
  colorAccent?: string,
  colorCta?: string,
): StylePreset {
  const base = STYLE_PRESETS[videoStyle || "elegante"];
  return {
    ...base,
    bgColor: colorBackground || base.bgColor,
    accentColor: colorAccent || base.accentColor,
    ctaColor: colorCta || base.ctaColor,
  };
}
