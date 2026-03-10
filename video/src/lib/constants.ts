export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// Colors
export const NAVY = "#0f2137";
export const GOLD = "#c9a84c";
export const RED = "#c8102e";
export const WHITE = "#ffffff";
export const LIGHT_NAVY = "#1a365d";
export const TEXT_LIGHT = "rgba(255,255,255,0.7)";

// Scene durations in frames
export const TRANSITION_FRAMES = 15;

export const SCENES = {
  opening: { start: 0, duration: 60 },       // 0-2s
  hero: { start: 60, duration: 180 },         // 2-8s
  stats: { start: 240, duration: 120 },       // 8-12s
  gallery: { start: 360, duration: 180 },     // 12-18s
  cta: { start: 540, duration: 60 },          // 18-20s
} as const;

/**
 * Lighten or darken a hex color by a given amount.
 * Positive amount = lighter, negative = darker.
 */
export function adjustBrightness(hex: string, amount: number): string {
  const h = hex.replace("#", "");
  const r = Math.max(0, Math.min(255, parseInt(h.substring(0, 2), 16) + amount));
  const g = Math.max(0, Math.min(255, parseInt(h.substring(2, 4), 16) + amount));
  const b = Math.max(0, Math.min(255, parseInt(h.substring(4, 6), 16) + amount));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

/**
 * Convert hex color to rgba string.
 */
export function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// Total = sum of durations - (4 transitions * 15 frames)
// 60 + 180 + 120 + 180 + 60 - (4 * 15) = 600 - 60 = 540
// But we want 600 total, so we add the overlap back
export const TOTAL_DURATION = 600;
