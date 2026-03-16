import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
  Img,
  staticFile,
} from "remotion";
import { StylePreset } from "../lib/types";
import { hexToRgba } from "../lib/constants";

type StatsProps = {
  recamaras: string;
  banos: string;
  m2Construidos: string;
  estacionamientos: string;
  bgPhotoUrl?: string;
  style: StylePreset;
};

type StatItem = {
  icon: string;
  value: string;
  label: string;
};

export const Stats: React.FC<StatsProps> = ({
  recamaras,
  banos,
  m2Construidos,
  estacionamientos,
  bgPhotoUrl,
  style: s,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const speed = s.animSpeed;

  // Build stats array from available data
  const stats: StatItem[] = [];
  if (recamaras && recamaras !== "0") {
    stats.push({ icon: staticFile("icons/bed.png"), value: recamaras, label: "Recámaras" });
  }
  if (banos && banos !== "0") {
    stats.push({ icon: staticFile("icons/bathroom.png"), value: banos, label: "Baños" });
  }
  if (m2Construidos) {
    stats.push({ icon: staticFile("icons/area.png"), value: `${m2Construidos} m²`, label: "Construidos" });
  }
  if (estacionamientos && estacionamientos !== "0") {
    stats.push({ icon: staticFile("icons/parking.png"), value: estacionamientos, label: "Estac." });
  }

  // Title animation
  const titleDelay = Math.round(2 / speed);
  const titleOpacity = interpolate(frame, [titleDelay, titleDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [titleDelay, titleDelay + 15], [-20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Top decorative line
  const lineDelay = Math.round(5 / speed);
  const lineW = interpolate(frame, [lineDelay, lineDelay + 25], [0, 200], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Ken Burns for background photo
  const bgScale = interpolate(frame, [0, 130], [1.1, 1.0], {
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
        padding: 60,
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
              transformOrigin: "60% 40%",
              filter: "blur(3px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: hexToRgba(s.bgColor, 0.72),
              pointerEvents: "none",
            }}
          />
        </>
      )}

      {/* Subtle background pattern */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `radial-gradient(circle at 20% 80%, ${hexToRgba(s.accentColor, 0.05)} 0%, transparent 50%),
                       radial-gradient(circle at 80% 20%, ${hexToRgba(s.accentColor, 0.05)} 0%, transparent 50%)`,
          pointerEvents: "none",
        }}
      />

      {/* Title */}
      <div
        style={{
          color: s.accentColor,
          fontSize: 38,
          fontFamily: s.fontHeading,
          letterSpacing: 8,
          marginBottom: 20,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        CARACTERÍSTICAS
      </div>

      {/* Decorative line under title */}
      <div
        style={{
          width: lineW,
          height: 2,
          backgroundColor: s.accentColor,
          marginBottom: 70,
        }}
      />

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
          const delay = Math.round((12 + i * 8) / speed);
          const cardProgress = spring({
            frame,
            fps,
            config: { damping: 14, stiffness: 100 },
            delay,
          });

          const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1]);
          const cardScale = interpolate(cardProgress, [0, 1], [0.8, 1]);

          // Icon bounce-in slightly after card
          const iconDelay = delay + Math.round(5 / speed);
          const iconProgress = spring({
            frame,
            fps,
            config: { damping: 10, stiffness: 150 },
            delay: iconDelay,
          });
          const iconScale = interpolate(iconProgress, [0, 1], [0.3, 1]);

          return (
            <div
              key={i}
              style={{
                width: 420,
                backgroundColor: s.bgSecondary,
                borderRadius: 16,
                padding: "44px 30px 36px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                opacity: cardOpacity,
                transform: `scale(${cardScale})`,
                border: `1px solid ${hexToRgba(s.accentColor, 0.15)}`,
                boxShadow: `0 8px 32px ${hexToRgba("#000000", 0.15)}`,
              }}
            >
              {/* Icon */}
              <div
                style={{
                  width: 72,
                  height: 72,
                  marginBottom: 20,
                  transform: `scale(${iconScale})`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Img
                  src={stat.icon}
                  style={{
                    width: 64,
                    height: 64,
                    objectFit: "contain",
                  }}
                />
              </div>

              {/* Value */}
              <div
                style={{
                  color: s.textColor,
                  fontSize: 52,
                  fontWeight: 700,
                  fontFamily: s.fontHeading,
                  marginBottom: 8,
                }}
              >
                {stat.value}
              </div>

              {/* Label */}
              <div
                style={{
                  color: s.textLight,
                  fontSize: 24,
                  fontFamily: s.fontBody,
                  letterSpacing: 3,
                  textTransform: "uppercase",
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
