import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { NAVY, GOLD, WHITE, RED } from "../lib/constants";

type OpeningProps = {
  operacion: string;
  tipoPropiedad: string;
  bgColor?: string;
  accentColor?: string;
  ctaColor?: string;
};

export const Opening: React.FC<OpeningProps> = ({
  operacion,
  tipoPropiedad,
  bgColor = NAVY,
  accentColor = GOLD,
  ctaColor = RED,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Badge fade + scale in
  const badgeProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: 5,
  });

  const badgeScale = interpolate(badgeProgress, [0, 1], [0.5, 1]);
  const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1]);

  // Gold line expand
  const lineWidth = interpolate(frame, [15, 45], [0, 600], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Property type fade in
  const typeOpacity = interpolate(frame, [30, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const typeY = interpolate(frame, [30, 50], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

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
      }}
    >
      {/* Operation badge */}
      <div
        style={{
          backgroundColor: ctaColor,
          color: WHITE,
          fontSize: 48,
          fontWeight: "bold",
          fontFamily: "Georgia, serif",
          letterSpacing: 12,
          padding: "18px 60px",
          borderRadius: 4,
          opacity: badgeOpacity,
          transform: `scale(${badgeScale})`,
        }}
      >
        {operacion.toUpperCase()}
      </div>

      {/* Gold line */}
      <div
        style={{
          width: lineWidth,
          height: 3,
          backgroundColor: accentColor,
          marginTop: 40,
          marginBottom: 40,
        }}
      />

      {/* Property type */}
      <div
        style={{
          color: accentColor,
          fontSize: 38,
          fontFamily: "Georgia, serif",
          letterSpacing: 6,
          opacity: typeOpacity,
          transform: `translateY(${typeY}px)`,
        }}
      >
        {tipoPropiedad.toUpperCase()}
      </div>
    </div>
  );
};
