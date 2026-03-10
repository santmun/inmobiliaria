import React from "react";
import { Composition } from "remotion";
import { ListingReel } from "./ListingReel";
import { ListingProps } from "./lib/types";
import { FPS, WIDTH, HEIGHT } from "./lib/constants";

// Total duration: sum of scene durations - (4 transitions * 15 frames)
// 70 + 190 + 130 + 190 + 80 - (4 * 15) = 660 - 60 = 600 frames = 20s
const TOTAL_DURATION = 600;

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
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ListingReel"
      component={ListingReel}
      durationInFrames={TOTAL_DURATION}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={defaultProps}
    />
  );
};
