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

type ContactCTAProps = {
  agenteNombre: string;
  agenteTelefono: string;
  agenciaNombre: string;
  logoUrl?: string;
  agentPhotoUrl?: string;
  qrUrl?: string;
  bgPhotoUrl?: string;
  style: StylePreset;
};

export const ContactCTA: React.FC<ContactCTAProps> = ({
  agenteNombre,
  agenteTelefono,
  agenciaNombre,
  logoUrl,
  agentPhotoUrl,
  qrUrl,
  bgPhotoUrl,
  style: s,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const speed = s.animSpeed;

  // Agent photo animation
  const photoProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: Math.round(2 / speed),
  });
  const photoOpacity = interpolate(photoProgress, [0, 1], [0, 1]);
  const photoScale = interpolate(photoProgress, [0, 1], [0.7, 1]);

  // CTA text animation
  const ctaDelay = Math.round(5 / speed);
  const ctaProgress = spring({
    frame,
    fps,
    config: { damping: 200 },
    delay: ctaDelay,
  });
  const ctaOpacity = interpolate(ctaProgress, [0, 1], [0, 1]);
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.85, 1]);

  // Gold line
  const lineDelay = Math.round(10 / speed);
  const lineWidth = interpolate(frame, [lineDelay, lineDelay + 22], [0, 400], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Contact info
  const contactDelay = Math.round(15 / speed);
  const contactOpacity = interpolate(frame, [contactDelay, contactDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const contactY = interpolate(frame, [contactDelay, contactDelay + 15], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });

  // Phone pill
  const pillDelay = Math.round(25 / speed);
  const pillProgress = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120 },
    delay: pillDelay,
  });
  const pillScale = interpolate(pillProgress, [0, 1], [0.5, 1]);
  const pillOpacity = interpolate(pillProgress, [0, 1], [0, 1]);

  // QR code animation
  const qrDelay = Math.round(30 / speed);
  const qrOpacity = interpolate(frame, [qrDelay, qrDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Logo animation
  const logoDelay = Math.round(35 / speed);
  const logoOpacity = interpolate(frame, [logoDelay, logoDelay + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Watermark
  const watermarkDelay = Math.round(40 / speed);
  const watermarkOpacity = interpolate(frame, [watermarkDelay, watermarkDelay + 15], [0, 0.4], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Ken Burns for background photo
  const bgScale = interpolate(frame, [0, 80], [1.0, 1.08], {
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
              transformOrigin: "40% 60%",
              filter: "blur(4px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: hexToRgba(s.bgColor, 0.78),
              pointerEvents: "none",
            }}
          />
        </>
      )}

      {/* Subtle background radial */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `radial-gradient(ellipse at center, ${hexToRgba(s.accentColor, 0.05)} 0%, transparent 70%)`,
          pointerEvents: "none",
        }}
      />

      {/* Agent photo */}
      {agentPhotoUrl && (
        <div
          style={{
            width: 130,
            height: 130,
            borderRadius: "50%",
            overflow: "hidden",
            marginBottom: 30,
            opacity: photoOpacity,
            transform: `scale(${photoScale})`,
            border: `3px solid ${hexToRgba(s.accentColor, 0.6)}`,
            boxShadow: `0 4px 20px ${hexToRgba("#000000", 0.3)}`,
          }}
        >
          <Img
            src={agentPhotoUrl}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </div>
      )}

      {/* CTA Text */}
      <div
        style={{
          color: s.textColor,
          fontSize: 52,
          fontWeight: 700,
          fontFamily: s.fontHeading,
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
          backgroundColor: s.accentColor,
          marginBottom: 40,
          boxShadow: `0 0 10px ${hexToRgba(s.accentColor, 0.3)}`,
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
          gap: 10,
        }}
      >
        <div
          style={{
            color: s.textColor,
            fontSize: 38,
            fontWeight: 700,
            fontFamily: s.fontBody,
          }}
        >
          {agenteNombre}
        </div>
        {agenciaNombre && (
          <div
            style={{
              color: s.textLight,
              fontSize: 26,
              fontFamily: s.fontBody,
              letterSpacing: 1,
            }}
          >
            {agenciaNombre}
          </div>
        )}
      </div>

      {/* Phone pill */}
      <div
        style={{
          marginTop: 40,
          backgroundColor: s.ctaColor,
          borderRadius: 50,
          padding: "18px 50px",
          opacity: pillOpacity,
          transform: `scale(${pillScale})`,
          boxShadow: `0 6px 25px ${hexToRgba(s.ctaColor, 0.4)}`,
        }}
      >
        <div
          style={{
            color: s.textColor,
            fontSize: 34,
            fontWeight: 700,
            fontFamily: s.fontBody,
            letterSpacing: 2,
          }}
        >
          {agenteTelefono}
        </div>
      </div>

      {/* QR Code */}
      {qrUrl && (
        <div
          style={{
            marginTop: 35,
            opacity: qrOpacity,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Img
            src={qrUrl}
            style={{
              width: 120,
              height: 120,
              borderRadius: 8,
              border: `2px solid ${hexToRgba(s.accentColor, 0.3)}`,
            }}
          />
          <div
            style={{
              color: s.textLight,
              fontSize: 18,
              fontFamily: s.fontBody,
              letterSpacing: 2,
            }}
          >
            ESCANEA PARA MÁS INFO
          </div>
        </div>
      )}

      {/* Logo at bottom */}
      {logoUrl && (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            opacity: logoOpacity,
          }}
        >
          <Img
            src={logoUrl}
            style={{
              maxWidth: 140,
              maxHeight: 70,
              objectFit: "contain",
            }}
          />
        </div>
      )}

      {/* Watermark */}
      <div
        style={{
          position: "absolute",
          bottom: 35,
          opacity: watermarkOpacity,
          color: s.textLight,
          fontSize: 18,
          fontFamily: s.fontBody,
          letterSpacing: 5,
        }}
      >
        LISTAPRO
      </div>
    </div>
  );
};
