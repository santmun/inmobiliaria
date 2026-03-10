import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  Img,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { NAVY, GOLD, WHITE, RED, hexToRgba } from "../lib/constants";

type HeroPhotoProps = {
  fotoPortada: string;
  precioFormateado: string;
  ciudad: string;
  paisNombre: string;
  operacion: string;
  bgColor?: string;
  accentColor?: string;
  ctaColor?: string;
};

export const HeroPhoto: React.FC<HeroPhotoProps> = ({
  fotoPortada,
  precioFormateado,
  ciudad,
  paisNombre,
  operacion,
  bgColor = NAVY,
  accentColor = GOLD,
  ctaColor = RED,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns: slow zoom from 1.0 to 1.15 over full duration
  const scale = interpolate(frame, [0, 180], [1.0, 1.15], {
    extrapolateRight: "clamp",
  });

  // Price animation
  const priceProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: 15,
  });
  const priceOpacity = interpolate(priceProgress, [0, 1], [0, 1]);
  const priceY = interpolate(priceProgress, [0, 1], [40, 0]);

  // Location fade in
  const locationOpacity = interpolate(frame, [25, 45], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Badge
  const badgeOpacity = interpolate(frame, [5, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const location = paisNombre ? `${ciudad}, ${paisNombre}` : ciudad;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        backgroundColor: bgColor,
      }}
    >
      {/* Hero image with Ken Burns */}
      <Img
        src={fotoPortada}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      />

      {/* Gradient overlay */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "60%",
          background:
            `linear-gradient(to top, ${hexToRgba(bgColor, 0.95)} 0%, ${hexToRgba(bgColor, 0.6)} 40%, transparent 100%)`,
        }}
      />

      {/* Operation badge */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 60,
          backgroundColor: ctaColor,
          color: WHITE,
          fontSize: 28,
          fontWeight: "bold",
          fontFamily: "sans-serif",
          padding: "10px 30px",
          borderRadius: 4,
          letterSpacing: 4,
          opacity: badgeOpacity,
        }}
      >
        {operacion.toUpperCase()}
      </div>

      {/* Price */}
      <div
        style={{
          position: "absolute",
          bottom: 220,
          left: 60,
          right: 60,
          opacity: priceOpacity,
          transform: `translateY(${priceY}px)`,
        }}
      >
        <div
          style={{
            color: accentColor,
            fontSize: 72,
            fontWeight: "bold",
            fontFamily: "Georgia, serif",
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
          }}
        >
          {precioFormateado}
        </div>
      </div>

      {/* Location */}
      <div
        style={{
          position: "absolute",
          bottom: 140,
          left: 60,
          right: 60,
          opacity: locationOpacity,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontSize: 36,
            fontFamily: "sans-serif",
            textShadow: "0 2px 10px rgba(0,0,0,0.5)",
          }}
        >
          {location}
        </div>
      </div>

      {/* Gold accent line */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 60,
          width: interpolate(frame, [30, 60], [0, 200], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          height: 3,
          backgroundColor: accentColor,
        }}
      />
    </div>
  );
};
