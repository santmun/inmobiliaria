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

type PropertyOverlayData = {
  tipoPropiedad?: string;
  operacion?: string;
  precioFormateado?: string;
  ciudad?: string;
  paisNombre?: string;
  recamaras?: string;
  banos?: string;
  m2Construidos?: string;
  estacionamientos?: string;
  fraseGancho?: string;
  logoUrl?: string;
};

type GalleryProps = {
  fotosExtra: string[];
  style: StylePreset;
  sceneWeights?: number[];
  propertyData?: PropertyOverlayData;
};

export const Gallery: React.FC<GalleryProps> = ({
  fotosExtra,
  style: s,
  sceneWeights,
  propertyData: pd,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // If no extra photos, show a styled placeholder
  if (fotosExtra.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          backgroundColor: s.bgColor,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            color: s.accentColor,
            fontSize: 38,
            fontFamily: s.fontHeading,
            letterSpacing: 6,
          }}
        >
          PROPIEDAD EXCLUSIVA
        </div>
      </div>
    );
  }

  // Allow up to 10 photos for voiceover tours (portada + extras), 6 for standard
  const maxPhotos = sceneWeights ? 10 : 6;
  const photos = fotosExtra.slice(0, maxPhotos);
  const crossfadeDuration = 20;

  // Build per-photo start/end frames based on weights or equal distribution
  const photoStarts: number[] = [];
  const photoEnds: number[] = [];

  if (sceneWeights && sceneWeights.length >= photos.length) {
    // Use scene weights for proportional timing
    // Normalize weights to sum to 1.0 (in case they don't already)
    const relevantWeights = sceneWeights.slice(0, photos.length);
    const weightSum = relevantWeights.reduce((a, b) => a + b, 0);
    const normalizedWeights = weightSum > 0
      ? relevantWeights.map((w) => w / weightSum)
      : relevantWeights.map(() => 1 / photos.length);

    let cursor = 0;
    for (let i = 0; i < photos.length; i++) {
      const segmentFrames = Math.round(normalizedWeights[i] * durationInFrames);
      photoStarts.push(cursor);
      cursor += segmentFrames;
      photoEnds.push(cursor);
    }
    // Ensure last photo extends to exact end
    photoEnds[photoEnds.length - 1] = durationInFrames;
  } else {
    // Equal distribution (original behavior)
    const framesPerPhoto = Math.floor(durationInFrames / photos.length);
    for (let i = 0; i < photos.length; i++) {
      photoStarts.push(i * framesPerPhoto);
      photoEnds.push((i + 1) * framesPerPhoto);
    }
    photoEnds[photoEnds.length - 1] = durationInFrames;
  }

  // Current photo index based on frame position
  let currentPhotoIndex = photos.length - 1;
  for (let i = 0; i < photos.length; i++) {
    if (frame < photoEnds[i]) {
      currentPhotoIndex = i;
      break;
    }
  }

  // Counter fade in
  const counterOpacity = interpolate(frame, [5, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

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
      {photos.map((photo, i) => {
        const photoStart = photoStarts[i];
        const photoEnd = photoEnds[i];

        // Opacity: fade in at start, fade out at end
        let opacity: number;
        if (i === 0) {
          opacity = interpolate(
            frame,
            [photoEnd - crossfadeDuration, photoEnd],
            [1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
        } else if (i === photos.length - 1) {
          opacity = interpolate(
            frame,
            [photoStart, photoStart + crossfadeDuration],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
        } else {
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

        // Alternating Ken Burns directions
        const photoProgress = interpolate(
          frame,
          [photoStart, photoEnd],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );
        const scale = 1.0 + photoProgress * 0.08;
        const origins = ["center center", "60% 40%", "40% 60%", "center top"];
        const origin = origins[i % origins.length];

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
              transformOrigin: origin,
            }}
          />
        );
      })}

      {/* Vignette overlay */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `radial-gradient(ellipse at center, transparent 40%, ${hexToRgba(s.bgColor, 0.55)} 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Top gradient for title area */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "30%",
          background: `linear-gradient(to bottom, ${hexToRgba("#000000", 0.65)} 0%, transparent 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Bottom gradient for info strip */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "40%",
          background: `linear-gradient(to top, ${hexToRgba("#000000", 0.75)} 0%, ${hexToRgba("#000000", 0.3)} 60%, transparent 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Corner accents */}
      <div style={{ position: "absolute", top: 50, left: 50, width: 60, height: 60, borderTop: `2px solid ${hexToRgba(s.accentColor, 0.5)}`, borderLeft: `2px solid ${hexToRgba(s.accentColor, 0.5)}` }} />
      <div style={{ position: "absolute", bottom: 50, right: 50, width: 60, height: 60, borderBottom: `2px solid ${hexToRgba(s.accentColor, 0.5)}`, borderRight: `2px solid ${hexToRgba(s.accentColor, 0.5)}` }} />

      {/* ─── PROPERTY INFO OVERLAYS ─── */}
      {pd && (() => {
        // Local frame within current photo segment
        const segStart = photoStarts[currentPhotoIndex];
        const localFrame = frame - segStart;

        // Shared animation helpers
        const slideUp = (delay: number, distance = 40) =>
          interpolate(localFrame, [delay, delay + 15], [distance, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
        const fadeIn = (delay: number, dur = 12) =>
          interpolate(localFrame, [delay, delay + dur], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

        // Build stats pills
        const stats: { icon: string; value: string; label: string }[] = [];
        if (pd.recamaras && pd.recamaras !== "0")
          stats.push({ icon: "🛏", value: pd.recamaras, label: "Rec." });
        if (pd.banos && pd.banos !== "0")
          stats.push({ icon: "🚿", value: pd.banos, label: "Baños" });
        if (pd.m2Construidos && pd.m2Construidos !== "0")
          stats.push({ icon: "📐", value: pd.m2Construidos, label: "m²" });
        if (pd.estacionamientos && pd.estacionamientos !== "0")
          stats.push({ icon: "🚗", value: pd.estacionamientos, label: "Est." });

        return (
          <>
            {/* ── Top: Operation badge (always visible) ── */}
            {pd.operacion && pd.tipoPropiedad && (
              <div
                style={{
                  position: "absolute",
                  top: 55,
                  left: 55,
                  opacity: fadeIn(3),
                  transform: `translateX(${interpolate(localFrame, [3, 18], [-80, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) })}px)`,
                }}
              >
                <div
                  style={{
                    backgroundColor: s.ctaColor,
                    padding: "10px 24px",
                    borderRadius: 6,
                    boxShadow: `0 4px 20px ${hexToRgba(s.ctaColor, 0.4)}`,
                  }}
                >
                  <span
                    style={{
                      color: "#ffffff",
                      fontSize: 24,
                      fontFamily: s.fontBody,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: 2,
                    }}
                  >
                    {pd.tipoPropiedad} en {pd.operacion}
                  </span>
                </div>
              </div>
            )}

            {/* ── Top-right: Logo ── */}
            {pd.logoUrl && (
              <div
                style={{
                  position: "absolute",
                  top: 55,
                  right: 55,
                  opacity: fadeIn(5),
                }}
              >
                <Img
                  src={pd.logoUrl}
                  style={{
                    height: 50,
                    objectFit: "contain",
                    filter: "brightness(0) invert(1)",
                    opacity: 0.8,
                  }}
                />
              </div>
            )}

            {/* ── First photo: Hero intro with price & location ── */}
            {currentPhotoIndex === 0 && (
              <>
                {/* Hook phrase */}
                {pd.fraseGancho && (
                  <div
                    style={{
                      position: "absolute",
                      top: "38%",
                      left: 0,
                      right: 0,
                      textAlign: "center",
                      opacity: fadeIn(8, 18),
                      transform: `translateY(${slideUp(8, 30)}px)`,
                    }}
                  >
                    <span
                      style={{
                        color: "#ffffff",
                        fontSize: 42,
                        fontFamily: s.fontHeading,
                        fontStyle: "italic",
                        lineHeight: 1.3,
                        textShadow: `0 3px 20px ${hexToRgba("#000000", 0.7)}`,
                        padding: "0 60px",
                        display: "inline-block",
                      }}
                    >
                      &ldquo;{pd.fraseGancho}&rdquo;
                    </span>
                  </div>
                )}

                {/* Price */}
                {pd.precioFormateado && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: 260,
                      left: 0,
                      right: 0,
                      textAlign: "center",
                      opacity: fadeIn(15, 15),
                      transform: `translateY(${slideUp(15, 50)}px)`,
                    }}
                  >
                    <span
                      style={{
                        color: s.accentColor,
                        fontSize: 72,
                        fontFamily: s.fontHeading,
                        fontWeight: 700,
                        textShadow: `0 3px 25px ${hexToRgba("#000000", 0.6)}, 0 0 40px ${hexToRgba(s.accentColor, 0.3)}`,
                      }}
                    >
                      {pd.precioFormateado}
                    </span>
                  </div>
                )}

                {/* Location */}
                {pd.ciudad && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: 210,
                      left: 0,
                      right: 0,
                      textAlign: "center",
                      opacity: fadeIn(22),
                      transform: `translateX(${interpolate(localFrame, [22, 37], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)`,
                    }}
                  >
                    <span
                      style={{
                        color: s.textColor,
                        fontSize: 34,
                        fontFamily: s.fontBody,
                        fontWeight: 500,
                        textShadow: `0 2px 12px ${hexToRgba("#000000", 0.5)}`,
                      }}
                    >
                      📍 {pd.ciudad}{pd.paisNombre ? `, ${pd.paisNombre}` : ""}
                    </span>
                  </div>
                )}

                {/* Gold accent line */}
                <div
                  style={{
                    position: "absolute",
                    bottom: 195,
                    left: "50%",
                    transform: "translateX(-50%)",
                    height: 2,
                    width: interpolate(localFrame, [28, 50], [0, 200], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                      easing: Easing.out(Easing.cubic),
                    }),
                    backgroundColor: s.accentColor,
                    boxShadow: `0 0 15px ${hexToRgba(s.accentColor, 0.5)}`,
                  }}
                />
              </>
            )}

            {/* ── Stats strip (visible on photos 2+) ── */}
            {currentPhotoIndex > 0 && stats.length > 0 && (
              <div
                style={{
                  position: "absolute",
                  bottom: 130,
                  left: 0,
                  right: 0,
                  display: "flex",
                  justifyContent: "center",
                  gap: 16,
                  opacity: fadeIn(5),
                  transform: `translateY(${slideUp(5, 25)}px)`,
                }}
              >
                {stats.map((stat, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: hexToRgba(s.bgColor, 0.65),
                      backdropFilter: "blur(10px)",
                      borderRadius: 14,
                      padding: "14px 22px",
                      border: `1px solid ${hexToRgba(s.accentColor, 0.25)}`,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: 4,
                      opacity: fadeIn(5 + idx * 4),
                      transform: `translateY(${slideUp(5 + idx * 4, 20)}px)`,
                    }}
                  >
                    <span style={{ fontSize: 26 }}>{stat.icon}</span>
                    <span
                      style={{
                        color: s.accentColor,
                        fontSize: 28,
                        fontFamily: s.fontHeading,
                        fontWeight: 700,
                      }}
                    >
                      {stat.value}
                    </span>
                    <span
                      style={{
                        color: s.textLight,
                        fontSize: 16,
                        fontFamily: s.fontBody,
                        fontWeight: 500,
                        textTransform: "uppercase",
                        letterSpacing: 1,
                      }}
                    >
                      {stat.label}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* ── Price reminder (on photos 2+, smaller) ── */}
            {currentPhotoIndex > 0 && pd.precioFormateado && (
              <div
                style={{
                  position: "absolute",
                  bottom: 60,
                  left: 0,
                  right: 0,
                  textAlign: "center",
                  opacity: fadeIn(8) * 0.9,
                }}
              >
                <span
                  style={{
                    color: s.accentColor,
                    fontSize: 36,
                    fontFamily: s.fontHeading,
                    fontWeight: 600,
                    textShadow: `0 2px 15px ${hexToRgba("#000000", 0.5)}`,
                  }}
                >
                  {pd.precioFormateado}
                </span>
              </div>
            )}
          </>
        );
      })()}

      {/* Photo counter */}
      <div
        style={{
          position: "absolute",
          top: pd?.operacion ? 120 : 55,
          left: 55,
          opacity: counterOpacity,
        }}
      >
        <div
          style={{
            backgroundColor: hexToRgba(s.bgColor, 0.5),
            borderRadius: 30,
            padding: "6px 18px",
            border: `1px solid ${hexToRgba(s.accentColor, 0.25)}`,
          }}
        >
          <span style={{ color: s.accentColor, fontSize: 20, fontFamily: s.fontBody, fontWeight: 600 }}>
            {currentPhotoIndex + 1}
          </span>
          <span style={{ color: s.textLight, fontSize: 20, fontFamily: s.fontBody }}>
            {" / "}{photos.length}
          </span>
        </div>
      </div>
    </div>
  );
};
