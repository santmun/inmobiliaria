import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { NAVY, GOLD, WHITE, RED, TEXT_LIGHT } from "../lib/constants";

type ContactCTAProps = {
  agenteNombre: string;
  agenteTelefono: string;
  agenciaNombre: string;
  bgColor?: string;
  accentColor?: string;
  ctaColor?: string;
};

export const ContactCTA: React.FC<ContactCTAProps> = ({
  agenteNombre,
  agenteTelefono,
  agenciaNombre,
  bgColor = NAVY,
  accentColor = GOLD,
  ctaColor = RED,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // CTA text animation
  const ctaProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: 3,
  });
  const ctaOpacity = interpolate(ctaProgress, [0, 1], [0, 1]);
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.8, 1]);

  // Gold line
  const lineWidth = interpolate(frame, [8, 30], [0, 400], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Contact info
  const contactOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const contactY = interpolate(frame, [15, 30], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Phone pill
  const pillProgress = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 120 },
    delay: 25,
  });
  const pillScale = interpolate(pillProgress, [0, 1], [0.5, 1]);
  const pillOpacity = interpolate(pillProgress, [0, 1], [0, 1]);

  // Watermark
  const watermarkOpacity = interpolate(frame, [35, 50], [0, 0.5], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
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
        padding: 60,
      }}
    >
      {/* CTA Text */}
      <div
        style={{
          color: WHITE,
          fontSize: 56,
          fontWeight: "bold",
          fontFamily: "Georgia, serif",
          textAlign: "center",
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
          marginBottom: 20,
        }}
      >
        Agenda tu visita
      </div>

      {/* Gold line */}
      <div
        style={{
          width: lineWidth,
          height: 3,
          backgroundColor: accentColor,
          marginBottom: 50,
        }}
      />

      {/* Agent info */}
      <div
        style={{
          opacity: contactOpacity,
          transform: `translateY(${contactY}px)`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontSize: 40,
            fontWeight: "bold",
            fontFamily: "sans-serif",
          }}
        >
          {agenteNombre}
        </div>
        {agenciaNombre && (
          <div
            style={{
              color: TEXT_LIGHT,
              fontSize: 28,
              fontFamily: "sans-serif",
            }}
          >
            {agenciaNombre}
          </div>
        )}
      </div>

      {/* Phone pill */}
      <div
        style={{
          marginTop: 50,
          backgroundColor: ctaColor,
          borderRadius: 50,
          padding: "20px 50px",
          opacity: pillOpacity,
          transform: `scale(${pillScale})`,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontSize: 36,
            fontWeight: "bold",
            fontFamily: "sans-serif",
            letterSpacing: 2,
          }}
        >
          📞 {agenteTelefono}
        </div>
      </div>

      {/* Watermark */}
      <div
        style={{
          position: "absolute",
          bottom: 40,
          opacity: watermarkOpacity,
          color: TEXT_LIGHT,
          fontSize: 20,
          fontFamily: "sans-serif",
          letterSpacing: 4,
        }}
      >
        LISTAPRO
      </div>
    </div>
  );
};
