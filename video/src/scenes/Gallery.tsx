import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  Img,
  interpolate,
  Easing,
} from "remotion";
import { NAVY, GOLD, WHITE, hexToRgba } from "../lib/constants";

type GalleryProps = {
  fotosExtra: string[];
  bgColor?: string;
  accentColor?: string;
};

export const Gallery: React.FC<GalleryProps> = ({
  fotosExtra,
  bgColor = NAVY,
  accentColor = GOLD,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // If no extra photos, show a subtle message
  if (fotosExtra.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: bgColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            color: accentColor,
            fontSize: 38,
            fontFamily: "Georgia, serif",
            letterSpacing: 4,
          }}
        >
          PROPIEDAD EXCLUSIVA
        </div>
      </div>
    );
  }

  // Calculate timing per photo
  const photos = fotosExtra.slice(0, 6);
  const framesPerPhoto = Math.floor(durationInFrames / photos.length);
  const crossfadeDuration = 20;

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
      {photos.map((photo, i) => {
        const photoStart = i * framesPerPhoto;
        const photoEnd = photoStart + framesPerPhoto;

        // Opacity: fade in at start, fade out at end (except last photo)
        let opacity: number;
        if (i === 0) {
          // First photo: visible from start, fade out
          opacity = interpolate(
            frame,
            [photoEnd - crossfadeDuration, photoEnd],
            [1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
        } else if (i === photos.length - 1) {
          // Last photo: fade in, stay visible
          opacity = interpolate(
            frame,
            [photoStart, photoStart + crossfadeDuration],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
        } else {
          // Middle photos: fade in and out
          const fadeIn = interpolate(
            frame,
            [photoStart, photoStart + crossfadeDuration],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          const fadeOut = interpolate(
            frame,
            [photoEnd - crossfadeDuration, photoEnd],
            [1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          opacity = Math.min(fadeIn, fadeOut);
        }

        // Subtle Ken Burns per photo
        const photoProgress = interpolate(
          frame,
          [photoStart, photoEnd],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        const scale = 1.0 + photoProgress * 0.08;

        return (
          <Img
            key={i}
            src={photo}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity,
              transform: `scale(${scale})`,
              transformOrigin: i % 2 === 0 ? "center center" : "60% 40%",
            }}
          />
        );
      })}

      {/* Subtle vignette overlay */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            `radial-gradient(ellipse at center, transparent 50%, ${hexToRgba(bgColor, 0.4)} 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Gold corner accents */}
      <div
        style={{
          position: "absolute",
          top: 50,
          left: 50,
          width: 60,
          height: 60,
          borderTop: `3px solid ${accentColor}`,
          borderLeft: `3px solid ${accentColor}`,
          opacity: 0.6,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 50,
          right: 50,
          width: 60,
          height: 60,
          borderBottom: `3px solid ${accentColor}`,
          borderRight: `3px solid ${accentColor}`,
          opacity: 0.6,
        }}
      />
    </div>
  );
};
