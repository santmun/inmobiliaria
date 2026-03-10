import React from "react";
import {
  Audio,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { ListingProps } from "./lib/types";
import { TRANSITION_FRAMES, NAVY, GOLD, RED, adjustBrightness } from "./lib/constants";
import { Opening } from "./scenes/Opening";
import { HeroPhoto } from "./scenes/HeroPhoto";
import { Stats } from "./scenes/Stats";
import { Gallery } from "./scenes/Gallery";
import { ContactCTA } from "./scenes/ContactCTA";

// Scene durations (before transition overlap subtraction)
const OPENING_DURATION = 75;
const HERO_DURATION = 195;
const STATS_DURATION = 135;
const GALLERY_DURATION = 195;
const CTA_DURATION = 75;

// Total = 75+195+135+195+75 - 4*15 = 675-60 = 615 ≈ 600 frames (20s)
// Adjusted to hit exactly 600:
// 70+190+130+190+80 - 4*15 = 660-60 = 600

const S = {
  opening: 70,
  hero: 190,
  stats: 130,
  gallery: 190,
  cta: 80,
};

const BackgroundMusic: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Fade in first 30 frames, fade out last 45 frames
  const volume = interpolate(
    frame,
    [0, 30, durationInFrames - 45, durationInFrames],
    [0, 0.35, 0.35, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return <Audio src={src} volume={volume} />;
};

export const ListingReel: React.FC<ListingProps> = (props) => {
  const transitionTiming = linearTiming({
    durationInFrames: TRANSITION_FRAMES,
  });

  // Resolve colors from props with fallback to constants
  const bgColor = props.colorBackground || NAVY;
  const accentColor = props.colorAccent || GOLD;
  const ctaColor = props.colorCta || RED;
  const lightBg = adjustBrightness(bgColor, 20);

  return (
    <AbsoluteFill>
      {props.musicUrl && <BackgroundMusic src={props.musicUrl} />}
    <TransitionSeries>
      {/* Scene 1: Opening */}
      <TransitionSeries.Sequence durationInFrames={S.opening}>
        <Opening
          operacion={props.operacion}
          tipoPropiedad={props.tipoPropiedad}
          bgColor={bgColor}
          accentColor={accentColor}
          ctaColor={ctaColor}
        />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={transitionTiming}
      />

      {/* Scene 2: Hero Photo */}
      <TransitionSeries.Sequence durationInFrames={S.hero}>
        <HeroPhoto
          fotoPortada={props.fotoPortada}
          precioFormateado={props.precioFormateado}
          ciudad={props.ciudad}
          paisNombre={props.paisNombre}
          operacion={props.operacion}
          bgColor={bgColor}
          accentColor={accentColor}
          ctaColor={ctaColor}
        />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={slide({ direction: "from-bottom" })}
        timing={transitionTiming}
      />

      {/* Scene 3: Stats */}
      <TransitionSeries.Sequence durationInFrames={S.stats}>
        <Stats
          recamaras={props.recamaras}
          banos={props.banos}
          m2Construidos={props.m2Construidos}
          estacionamientos={props.estacionamientos}
          bgColor={bgColor}
          accentColor={accentColor}
          lightBgColor={lightBg}
        />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={transitionTiming}
      />

      {/* Scene 4: Gallery */}
      <TransitionSeries.Sequence durationInFrames={S.gallery}>
        <Gallery
          fotosExtra={props.fotosExtra}
          bgColor={bgColor}
          accentColor={accentColor}
        />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={slide({ direction: "from-right" })}
        timing={transitionTiming}
      />

      {/* Scene 5: Contact CTA */}
      <TransitionSeries.Sequence durationInFrames={S.cta}>
        <ContactCTA
          agenteNombre={props.agenteNombre}
          agenteTelefono={props.agenteTelefono}
          agenciaNombre={props.agenciaNombre}
          bgColor={bgColor}
          accentColor={accentColor}
          ctaColor={ctaColor}
        />
      </TransitionSeries.Sequence>
    </TransitionSeries>
    </AbsoluteFill>
  );
};
