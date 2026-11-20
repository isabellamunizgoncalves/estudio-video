import type { EstiloVisual } from "./tipos";
import { padrao } from "./padrao";
import { retrovisage } from "./retrovisage";

// Pacotes de design disponíveis. O canal escolhe com "estilo": "<nome>" no seu tema.json.
// Novo design: crie src/estilos/<nome>/index.tsx (copie o padrao) e registre aqui.
export const ESTILOS: Record<string, EstiloVisual> = {
  padrao,
  retrovisage,
};

export const escolherEstilo = (nome?: string): EstiloVisual => {
  if (nome && !ESTILOS[nome]) console.warn(`Estilo "${nome}" não registrado em src/estilos/index.ts; usando "padrao".`);
  return (nome && ESTILOS[nome]) || padrao;
};
