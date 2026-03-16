import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  Img,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { StylePreset } from "../lib/types";
import { hexToRgba } from "../lib/constants";

type HeroPhotoProps = {
  fotoPortada: string;
  precioFormateado: string;
  ciudad: string;
  paisNombre: string;
  operacion: string;
  fraseGancho?: string;
  style: StylePreset;
};

export const HeroPhoto: React.FC<HeroPhotoProps> = ({
  fotoPortada,
  precioFormateado,
  ciudad,
  paisNombre,
  operacion,
  fraseGancho,
  style: s,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const speed = s.animSpeed;

  // Ken Burns: slow zoom from 1.0 to 1.12
  const scale = interpolate(frame, [0, 180], [1.0, 1.12], {
    extrapolateRight: "clamp",
  });

  // Badge slide in from left
  const badgeX = interpolate(frame, [Math.round(3 / speed), Math.round(18 / speed)], [-200, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const badgeOpacity = interpolate(frame, [Math.round(3 / speed), Math.round(12 / speed)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Hook phrase animation
  const hookDelay = Math.round(10 / speed);
  const hookOpacity = interpolate(frame, [hookDelay, hookDelay + 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const hookY = interpolate(frame, [hookDelay, hookDelay + 20], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Price animation
  const priceProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: Math.round(20 / speed),
  });
  const priceOpacity = interpolate(priceProgress, [0, 1], [0, 1]);
  const priceY = interpolate(priceProgress, [0, 1], [50, 0]);

  // Location fade in
  const locDelay = Math.round(30 / speed);
  const locationOpacity = interpolate(frame, [locDelay, locDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const locationX = interpolate(frame, [locDelay, locDelay + 15], [-20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Gold accent line
  const lineDelay = Math.round(35 / speed);
  const lineW = interpolate(frame, [lineDelay, lineDelay + 25], [0, 220], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const location = paisNombre ? `${ciudad}, ${paisNombre}` : ciudad;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        backgroundColor: s.bgColor,
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

      {/* Top gradient for badge area */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "25%",
          background: `linear-gradient(to bottom, ${hexToRgba(s.bgColor, 0.6)} 0%, transparent 100%)`,
        }}
      />

      {/* Bottom gradient overlay */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "65%",
          background: `linear-gradient(to top, ${hexToRgba(s.bgColor, 0.95)} 0%, ${hexToRgba(s.bgColor, 0.7)} 35%, transparent 100%)`,
        }}
      />

      {/* Operation badge — top left */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 60,
          opacity: badgeOpacity,
          transform: `translateX(${badgeX}px)`,
        }}
      >
        <div
          style={{
            backgroundColor: s.ctaColor,
            color: s.textColor,
            fontSize: 26,
            fontWeight: 700,
            fontFamily: s.fontBody,
            padding: "10px 28px",
            borderRadius: 2,
            letterSpacing: 5,
            boxShadow: `0 4px 20px ${hexToRgba(s.ctaColor, 0.5)}`,
          }}
        >
          {operacion.toUpperCase()}
        </div>
      </div>

      {/* Hook phrase — center overlay */}
      {fraseGancho && (
        <div
          style={{
            position: "absolute",
            top: "38%",
            left: 60,
            right: 60,
            opacity: hookOpacity,
            transform: `translateY(${hookY}px)`,
          }}
        >
          <div
            style={{
              color: s.textColor,
              fontSize: 44,
              fontWeight: 600,
              fontFamily: s.fontHeading,
              textAlign: "center",
              lineHeight: 1.3,
              textShadow: `0 4px 30px ${hexToRgba("#000000", 0.7)}`,
              padding: "0 20px",
            }}
          >
            &ldquo;{fraseGancho}&rdquo;
          </div>
        </div>
      )}

      {/* Price */}
      <div
        style={{
          position: "absolute",
          bottom: 240,
          left: 60,
          right: 60,
          opacity: priceOpacity,
          transform: `translateY(${priceY}px)`,
        }}
      >
        <div
          style={{
            color: s.accentColor,
            fontSize: 74,
            fontWeight: 700,
            fontFamily: s.fontHeading,
            textShadow: `0 4px 30px ${hexToRgba("#000000", 0.6)}`,
          }}
        >
          {precioFormateado}
        </div>
      </div>

      {/* Location */}
      <div
        style={{
          position: "absolute",
          bottom: 160,
          left: 60,
          right: 60,
          opacity: locationOpacity,
          transform: `translateX(${locationX}px)`,
        }}
      >
        <div
          style={{
            color: s.textColor,
            fontSize: 34,
            fontFamily: s.fontBody,
            fontWeight: 500,
            textShadow: `0 2px 15px ${hexToRgba("#000000", 0.5)}`,
            letterSpacing: 1,
          }}
        >
          {location}
        </div>
      </div>

      {/* Gold accent line */}
      <div
        style={{
          position: "absolute",
          bottom: 135,
          left: 60,
          width: lineW,
          height: 3,
          backgroundColor: s.accentColor,
          boxShadow: `0 0 15px ${hexToRgba(s.accentColor, 0.4)}`,
        }}
      />
    </div>
  );
};
