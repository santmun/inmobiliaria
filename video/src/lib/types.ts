export type VideoStyle = "elegante" | "moderno" | "minimalista";

export type ListingProps = {
  tipoPropiedad: string;
  operacion: string;
  ciudad: string;
  paisNombre: string;
  precioFormateado: string;
  recamaras: string;
  banos: string;
  m2Construidos: string;
  estacionamientos: string;
  fotoPortada: string;
  fotosExtra: string[];
  agenteNombre: string;
  agenteTelefono: string;
  agenciaNombre: string;
  musicUrl?: string;
  musicVolume?: number;
  // Branding
  logoUrl?: string;
  agentPhotoUrl?: string;
  // Content
  fraseGancho?: string;
  qrUrl?: string;
  // Video type & voiceover
  videoType?: "reel" | "tour";
  voiceoverUrl?: string;
  // Style
  videoStyle?: VideoStyle;
  colorBackground?: string;
  colorAccent?: string;
  colorCta?: string;
  // Scene sync (voiceover tours): relative duration weight per photo
  // e.g. [0.15, 0.2, 0.18, 0.12, 0.15, 0.2] — must sum to ~1.0
  sceneWeights?: number[];
};

export type StylePreset = {
  bgColor: string;
  bgSecondary: string;
  accentColor: string;
  ctaColor: string;
  textColor: string;
  textLight: string;
  fontHeading: string;
  fontBody: string;
  animSpeed: number; // multiplier: 1 = normal
};
