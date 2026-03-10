import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { NAVY, GOLD, WHITE, LIGHT_NAVY, TEXT_LIGHT } from "../lib/constants";

type StatsProps = {
  recamaras: string;
  banos: string;
  m2Construidos: string;
  estacionamientos: string;
  bgColor?: string;
  accentColor?: string;
  lightBgColor?: string;
};

type StatItem = {
  emoji: string;
  value: string;
  label: string;
};

export const Stats: React.FC<StatsProps> = ({
  recamaras,
  banos,
  m2Construidos,
  estacionamientos,
  bgColor = NAVY,
  accentColor = GOLD,
  lightBgColor = LIGHT_NAVY,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Build stats array from available data
  const stats: StatItem[] = [];
  if (recamaras && recamaras !== "0") {
    stats.push({ emoji: "🛏️", value: recamaras, label: "Recámaras" });
  }
  if (banos && banos !== "0") {
    stats.push({ emoji: "🚿", value: banos, label: "Baños" });
  }
  if (m2Construidos) {
    stats.push({ emoji: "📐", value: `${m2Construidos} m²`, label: "Construidos" });
  }
  if (estacionamientos && estacionamientos !== "0") {
    stats.push({ emoji: "🚗", value: estacionamientos, label: "Estac." });
  }

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: bgColor,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 60,
      }}
    >
      {/* Title */}
      <div
        style={{
          color: accentColor,
          fontSize: 38,
          fontFamily: "Georgia, serif",
          letterSpacing: 6,
          marginBottom: 80,
          opacity: interpolate(frame, [0, 15], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        CARACTERÍSTICAS
      </div>

      {/* Stats grid - 2 columns */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 30,
          width: "100%",
          maxWidth: 900,
        }}
      >
        {stats.map((stat, i) => {
          const delay = 10 + i * 8;
          const cardProgress = spring({
            frame,
            fps,
            config: { damping: 15, stiffness: 120 },
            delay,
          });

          const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1]);
          const cardY = interpolate(cardProgress, [0, 1], [60, 0]);

          return (
            <div
              key={i}
              style={{
                width: 420,
                backgroundColor: lightBgColor,
                borderRadius: 20,
                padding: "40px 30px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                opacity: cardOpacity,
                transform: `translateY(${cardY}px)`,
                border: `1px solid ${accentColor}33`,
              }}
            >
              <div style={{ fontSize: 60, marginBottom: 16 }}>{stat.emoji}</div>
              <div
                style={{
                  color: WHITE,
                  fontSize: 52,
                  fontWeight: "bold",
                  fontFamily: "sans-serif",
                  marginBottom: 8,
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  color: TEXT_LIGHT,
                  fontSize: 26,
                  fontFamily: "sans-serif",
                  letterSpacing: 2,
                }}
              >
                {stat.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
