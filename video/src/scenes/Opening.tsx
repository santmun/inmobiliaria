import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
  Img,
} from "remotion";
import { StylePreset } from "../lib/types";
import { hexToRgba } from "../lib/constants";

type OpeningProps = {
  operacion: string;
  tipoPropiedad: string;
  logoUrl?: string;
  bgPhotoUrl?: string;
  style: StylePreset;
};

export const Opening: React.FC<OpeningProps> = ({
  operacion,
  tipoPropiedad,
  logoUrl,
  bgPhotoUrl,
  style: s,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const speed = s.animSpeed;

  // Shimmer sweep across background
  const shimmerX = interpolate(frame, [0, 70], [-400, 1500], {
    extrapolateRight: "clamp",
  });

  // Logo fade + scale
  const logoProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: Math.round(2 / speed),
  });
  const logoOpacity = interpolate(logoProgress, [0, 1], [0, 1]);
  const logoScale = interpolate(logoProgress, [0, 1], [0.7, 1]);

  // Top decorative line
  const topLineWidth = interpolate(frame, [Math.round(5 / speed), Math.round(35 / speed)], [0, 300], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Badge fade + scale in
  const badgeProgress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 100 },
    delay: Math.round(10 / speed),
  });
  const badgeScale = interpolate(badgeProgress, [0, 1], [0.3, 1]);
  const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1]);

  // Gold line expand
  const lineWidth = interpolate(
    frame,
    [Math.round(20 / speed), Math.round(50 / speed)],
    [0, 600],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  // Property type stagger in (letter by letter feel via translateY)
  const typeDelay = Math.round(35 / speed);
  const typeOpacity = interpolate(frame, [typeDelay, typeDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const typeY = interpolate(frame, [typeDelay, typeDelay + 15], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const typeLetterSpacing = interpolate(frame, [typeDelay, typeDelay + 20], [20, 8], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Bottom decorative line
  const bottomLineWidth = interpolate(frame, [Math.round(45 / speed), Math.round(65 / speed)], [0, 200], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Ken Burns for background photo
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.15], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: s.bgColor,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background photo with dark overlay */}
      {bgPhotoUrl && (
        <>
          <Img
            src={bgPhotoUrl}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${bgScale})`,
              transformOrigin: "center center",
              filter: "blur(2px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: hexToRgba(s.bgColor, 0.75),
              pointerEvents: "none",
            }}
          />
        </>
      )}

      {/* Subtle shimmer sweep */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: shimmerX,
          width: 300,
          height: "100%",
          background: `linear-gradient(90deg, transparent, ${hexToRgba(s.accentColor, 0.06)}, transparent)`,
          transform: "skewX(-15deg)",
          pointerEvents: "none",
        }}
      />

      {/* Corner decorations */}
      <div style={{ position: "absolute", top: 60, left: 60, width: 80, height: 80, borderTop: `2px solid ${hexToRgba(s.accentColor, 0.3)}`, borderLeft: `2px solid ${hexToRgba(s.accentColor, 0.3)}` }} />
      <div style={{ position: "absolute", bottom: 60, right: 60, width: 80, height: 80, borderBottom: `2px solid ${hexToRgba(s.accentColor, 0.3)}`, borderRight: `2px solid ${hexToRgba(s.accentColor, 0.3)}` }} />

      {/* Logo */}
      {logoUrl && (
        <div
          style={{
            opacity: logoOpacity,
            transform: `scale(${logoScale})`,
            marginBottom: 50,
          }}
        >
          <Img
            src={logoUrl}
            style={{
              maxWidth: 180,
              maxHeight: 100,
              objectFit: "contain",
            }}
          />
        </div>
      )}

      {/* Top decorative accent line */}
      <div
        style={{
          width: topLineWidth,
          height: 1,
          backgroundColor: hexToRgba(s.accentColor, 0.4),
          marginBottom: 40,
        }}
      />

      {/* Operation badge */}
      <div
        style={{
          backgroundColor: s.ctaColor,
          color: s.textColor,
          fontSize: 52,
          fontWeight: 700,
          fontFamily: s.fontHeading,
          letterSpacing: 14,
          padding: "20px 70px",
          borderRadius: 2,
          opacity: badgeOpacity,
          transform: `scale(${badgeScale})`,
          boxShadow: `0 8px 40px ${hexToRgba(s.ctaColor, 0.4)}`,
        }}
      >
        {operacion.toUpperCase()}
      </div>

      {/* Gold line */}
      <div
        style={{
          width: lineWidth,
          height: 2,
          backgroundColor: s.accentColor,
          marginTop: 45,
          marginBottom: 45,
        }}
      />

      {/* Property type */}
      <div
        style={{
          color: s.accentColor,
          fontSize: 40,
          fontFamily: s.fontHeading,
          letterSpacing: typeLetterSpacing,
          opacity: typeOpacity,
          transform: `translateY(${typeY}px)`,
        }}
      >
        {tipoPropiedad.toUpperCase()}
      </div>

      {/* Bottom decorative accent line */}
      <div
        style={{
          width: bottomLineWidth,
          height: 1,
          backgroundColor: hexToRgba(s.accentColor, 0.3),
          marginTop: 40,
        }}
      />
    </div>
  );
};
