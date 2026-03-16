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
import { TRANSITION_FRAMES, resolveStyle } from "./lib/constants";
import { Opening } from "./scenes/Opening";
import { HeroPhoto } from "./scenes/HeroPhoto";
import { Stats } from "./scenes/Stats";
import { Gallery } from "./scenes/Gallery";
import { ContactCTA } from "./scenes/ContactCTA";

// Base scene durations for 20s reel (600 frames)
const BASE_SCENES = {
  opening: 70,
  hero: 190,
  stats: 130,
  gallery: 190,
  cta: 80,
};
const BASE_TOTAL = 660; // sum before transition overlap

const BackgroundMusic: React.FC<{ src: string; maxVolume?: number }> = ({
  src,
  maxVolume = 0.35,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const volume = interpolate(
    frame,
    [0, 30, durationInFrames - 45, durationInFrames],
    [0, maxVolume, maxVolume, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return <Audio src={src} volume={volume} />;
};

const VoiceoverAudio: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Start voiceover quickly (frame 5), fade out at end
  const volume = interpolate(
    frame,
    [5, 15, durationInFrames - 30, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return <Audio src={src} volume={volume} startFrom={0} />;
};

/**
 * Calculate scene durations proportionally based on total available frames.
 * For voiceover/tour videos with longer duration, gallery gets more relative time
 * since it contains the scene-matched photos synced with narration.
 */
function calculateSceneDurations(totalFrames: number, hasVoiceover: boolean = false) {
  // Account for transitions: 4 transitions * TRANSITION_FRAMES each
  const transitionOverlap = 4 * TRANSITION_FRAMES;
  const availableFrames = totalFrames + transitionOverlap;

  if (hasVoiceover) {
    // Voiceover tours: gallery gets ~55% of time, reduce opening/stats
    const voiceoverScenes = {
      opening: 50,
      hero: 120,
      stats: 80,
      gallery: 350,
      cta: 60,
    };
    const voiceoverTotal = Object.values(voiceoverScenes).reduce((a, b) => a + b, 0);
    const scale = availableFrames / voiceoverTotal;
    return {
      opening: Math.round(voiceoverScenes.opening * scale),
      hero: Math.round(voiceoverScenes.hero * scale),
      stats: Math.round(voiceoverScenes.stats * scale),
      gallery: Math.round(voiceoverScenes.gallery * scale),
      cta: Math.round(voiceoverScenes.cta * scale),
    };
  }

  // Standard reel: scale proportionally from base
  const scale = availableFrames / BASE_TOTAL;
  return {
    opening: Math.round(BASE_SCENES.opening * scale),
    hero: Math.round(BASE_SCENES.hero * scale),
    stats: Math.round(BASE_SCENES.stats * scale),
    gallery: Math.round(BASE_SCENES.gallery * scale),
    cta: Math.round(BASE_SCENES.cta * scale),
  };
}

export const ListingReel: React.FC<ListingProps> = (props) => {
  const { durationInFrames } = useVideoConfig();

  const transitionTiming = linearTiming({
    durationInFrames: TRANSITION_FRAMES,
  });

  // Resolve style preset from props
  const style = resolveStyle(
    props.videoStyle,
    props.colorBackground,
    props.colorAccent,
    props.colorCta,
  );

  // Music volume: lower when voiceover is present
  const musicMaxVolume = props.voiceoverUrl ? (props.musicVolume ?? 0.15) : 0.35;

  const hasVoiceover = !!props.voiceoverUrl;

  // ─── Voiceover Tour Layout ───
  // Gallery takes ~93% with ALL photos (portada + extras) synced to voiceover.
  // No Opening/Hero/Stats — the narration IS the content.
  // Only a brief CTA at the end.
  if (hasVoiceover) {
    const ctaFrames = Math.min(75, Math.round(durationInFrames * 0.07));
    const galleryFrames = durationInFrames - ctaFrames + TRANSITION_FRAMES;
    const allPhotos = [props.fotoPortada, ...props.fotosExtra];

    return (
      <AbsoluteFill>
        {props.musicUrl && (
          <BackgroundMusic src={props.musicUrl} maxVolume={musicMaxVolume} />
        )}
        <VoiceoverAudio src={props.voiceoverUrl!} />

        <TransitionSeries>
          {/* Gallery with ALL photos synced to voiceover timestamps */}
          <TransitionSeries.Sequence durationInFrames={galleryFrames}>
            <Gallery
              fotosExtra={allPhotos}
              style={style}
              sceneWeights={props.sceneWeights}
              propertyData={{
                tipoPropiedad: props.tipoPropiedad,
                operacion: props.operacion,
                precioFormateado: props.precioFormateado,
                ciudad: props.ciudad,
                paisNombre: props.paisNombre,
                recamaras: props.recamaras,
                banos: props.banos,
                m2Construidos: props.m2Construidos,
                estacionamientos: props.estacionamientos,
                fraseGancho: props.fraseGancho,
                logoUrl: props.logoUrl,
              }}
            />
          </TransitionSeries.Sequence>

          <TransitionSeries.Transition
            presentation={fade()}
            timing={transitionTiming}
          />

          {/* Brief CTA at the end */}
          <TransitionSeries.Sequence durationInFrames={ctaFrames}>
            <ContactCTA
              agenteNombre={props.agenteNombre}
              agenteTelefono={props.agenteTelefono}
              agenciaNombre={props.agenciaNombre}
              logoUrl={props.logoUrl}
              agentPhotoUrl={props.agentPhotoUrl}
              qrUrl={props.qrUrl}
              bgPhotoUrl={props.fotoPortada}
              style={style}
            />
          </TransitionSeries.Sequence>
        </TransitionSeries>
      </AbsoluteFill>
    );
  }

  // ─── Standard Reel Layout (no voiceover) ───
  // Classic 5-scene structure: Opening → Hero → Stats → Gallery → CTA
  const S = calculateSceneDurations(durationInFrames, false);

  return (
    <AbsoluteFill>
      {props.musicUrl && (
        <BackgroundMusic src={props.musicUrl} maxVolume={musicMaxVolume} />
      )}

      <TransitionSeries>
        {/* Scene 1: Opening */}
        <TransitionSeries.Sequence durationInFrames={S.opening}>
          <Opening
            operacion={props.operacion}
            tipoPropiedad={props.tipoPropiedad}
            logoUrl={props.logoUrl}
            bgPhotoUrl={props.fotoPortada}
            style={style}
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
            fraseGancho={props.fraseGancho}
            style={style}
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
            bgPhotoUrl={props.fotosExtra[0] || props.fotoPortada}
            style={style}
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
            style={style}
            sceneWeights={props.sceneWeights}
            propertyData={{
              tipoPropiedad: props.tipoPropiedad,
              operacion: props.operacion,
              precioFormateado: props.precioFormateado,
              ciudad: props.ciudad,
              paisNombre: props.paisNombre,
              recamaras: props.recamaras,
              banos: props.banos,
              m2Construidos: props.m2Construidos,
              estacionamientos: props.estacionamientos,
              fraseGancho: props.fraseGancho,
              logoUrl: props.logoUrl,
            }}
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
            logoUrl={props.logoUrl}
            agentPhotoUrl={props.agentPhotoUrl}
            qrUrl={props.qrUrl}
            bgPhotoUrl={props.fotoPortada}
            style={style}
          />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
