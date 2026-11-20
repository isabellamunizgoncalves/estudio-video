import { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import type { Tema } from "./tipos";

// Catálogo de fontes do Google disponíveis para os temas dos canais.
// Para usar outra: acrescente uma linha (o nome do módulo é o nome da fonte sem espaços).
type ModuloFonte = {
  getInfo: () => unknown;
  loadFont: (estilo: "normal", opcoes: { weights: string[]; subsets: string[]; ignoreTooManyRequestsWarning?: boolean }) => {
    waitUntilDone: () => Promise<unknown>;
  };
};
const CATALOGO: Record<string, () => Promise<unknown>> = {
  "Anton": () => import("@remotion/google-fonts/Anton"),
  "Fascinate": () => import("@remotion/google-fonts/Fascinate"),
  "Special Elite": () => import("@remotion/google-fonts/SpecialElite"),
  "Josefin Sans": () => import("@remotion/google-fonts/JosefinSans"),
  "Shrikhand": () => import("@remotion/google-fonts/Shrikhand"),
  "Bebas Neue": () => import("@remotion/google-fonts/BebasNeue"),
  "Oswald": () => import("@remotion/google-fonts/Oswald"),
  "Inter": () => import("@remotion/google-fonts/Inter"),
  "IBM Plex Mono": () => import("@remotion/google-fonts/IBMPlexMono"),
  "Montserrat": () => import("@remotion/google-fonts/Montserrat"),
  "Playfair Display": () => import("@remotion/google-fonts/PlayfairDisplay"),
  "Lora": () => import("@remotion/google-fonts/Lora"),
  "Merriweather": () => import("@remotion/google-fonts/Merriweather"),
  "Poppins": () => import("@remotion/google-fonts/Poppins"),
  "Roboto": () => import("@remotion/google-fonts/Roboto"),
  "Roboto Condensed": () => import("@remotion/google-fonts/RobotoCondensed"),
  "Abril Fatface": () => import("@remotion/google-fonts/AbrilFatface"),
  "Righteous": () => import("@remotion/google-fonts/Righteous"),
  "Lobster": () => import("@remotion/google-fonts/Lobster"),
  "Permanent Marker": () => import("@remotion/google-fonts/PermanentMarker"),
  "Caveat": () => import("@remotion/google-fonts/Caveat"),
  "Cormorant Garamond": () => import("@remotion/google-fonts/CormorantGaramond"),
  "DM Serif Display": () => import("@remotion/google-fonts/DMSerifDisplay"),
  "Libre Baskerville": () => import("@remotion/google-fonts/LibreBaskerville"),
  "Archivo Black": () => import("@remotion/google-fonts/ArchivoBlack"),
  "Raleway": () => import("@remotion/google-fonts/Raleway"),
  "Nunito": () => import("@remotion/google-fonts/Nunito"),
  "Open Sans": () => import("@remotion/google-fonts/OpenSans"),
};

const carregadas = new Set<string>();

async function carregar(familia: string) {
  if (!familia || carregadas.has(familia)) return;
  const carregar = CATALOGO[familia];
  if (!carregar) {
    console.warn(`Fonte "${familia}" não está no CATALOGO de estudio-remotion/src/fontes.ts; usando a padrão.`);
    return;
  }
  const mod = (await carregar()) as ModuloFonte;
  const info = mod.getInfo() as { fonts: Record<string, Record<string, unknown>>; subsets: string[] };
  const pesos = Object.keys(info.fonts.normal ?? {});
  const escolhidos = ["400", "700"].filter((p) => pesos.includes(p));
  const subsets = info.subsets.filter((s) => s === "latin" || s === "latin-ext");
  const { waitUntilDone } = mod.loadFont("normal", {
    weights: escolhidos.length ? escolhidos : pesos.slice(0, 1),
    subsets: subsets.length ? subsets : info.subsets.slice(0, 1),
    ignoreTooManyRequestsWarning: true,
  });
  await waitUntilDone();
  carregadas.add(familia);
}

/** Carrega as fontes do tema antes de renderizar o primeiro quadro. */
export function useFontesDoTema(tema: Tema) {
  const [handle] = useState(() => delayRender("Carregando fontes do tema"));
  useEffect(() => {
    const familias = Array.from(new Set([...Object.values(tema.fontes), tema.legendas?.fonte].filter(Boolean)));
    Promise.all(familias.map((f) => carregar(f as string).catch((e) => console.warn(e))))
      .finally(() => continueRender(handle));
  }, [handle, tema]);
}

export const pilha = (familia: string) => `"${familia}", "Helvetica Neue", Arial, sans-serif`;
