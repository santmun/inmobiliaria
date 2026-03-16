import React from "react";
import { Composition } from "remotion";
import { getAudioDurationInSeconds } from "@remotion/media-utils";
import { ListingReel } from "./ListingReel";
import { ListingProps } from "./lib/types";
import { FPS, WIDTH, HEIGHT } from "./lib/constants";

// Base duration: 600 frames = 20s (for reel without voiceover)
const BASE_DURATION = 600;

const defaultProps: ListingProps = {
  tipoPropiedad: "Casa",
  operacion: "Venta",
  ciudad: "Polanco, CDMX",
  paisNombre: "México",
  precioFormateado: "$8,500,000 MXN",
  recamaras: "4",
  banos: "3.5",
  m2Construidos: "320",
  estacionamientos: "2",
  fotoPortada: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1080&q=80",
  fotosExtra: [
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1080&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1080&q=80",
  ],
  agenteNombre: "María García",
  agenteTelefono: "+52 55 1234 5678",
  agenciaNombre: "Inmobiliaria Premium",
  videoStyle: "elegante",
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ListingReel"
      component={ListingReel}
      durationInFrames={BASE_DURATION}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={defaultProps}
      calculateMetadata={async ({ props }) => {
        // If voiceover audio exists, calculate duration from the audio length
        if (props.voiceoverUrl) {
          try {
            const audioDuration = await getAudioDurationInSeconds(props.voiceoverUrl);
            // Add 3 seconds padding (intro + outro)
            const totalSeconds = audioDuration + 3;
            const frames = Math.ceil(totalSeconds * FPS);
            return {
              durationInFrames: Math.max(frames, BASE_DURATION),
            };
          } catch (e) {
            console.error("Could not get voiceover duration:", e);
          }
        }
        // Default: 20s reel
        return { durationInFrames: BASE_DURATION };
      }}
    />
  );
};
