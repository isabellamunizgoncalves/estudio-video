// Utilidades neutras, sem nenhum design de canal.
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Tema } from "../tipos";

/** Número pseudoaleatório estável a partir de um texto (mesma cena = mesmo valor sempre). */
export const semente = (texto: string) => {
  let h = 2166136261;
  for (let i = 0; i < texto.length; i++) h = Math.imul(h ^ texto.charCodeAt(i), 16777619);
  return ((h >>> 0) % 10000) / 10000;
};

/** Entrada com mola (0→1) a partir de `atraso` quadros. */
export const useEntrada = (atraso = 0, damping = 14) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - atraso, fps, config: { damping, mass: 0.7 } });
};

/** Saída suave nos últimos `quadros` de uma duração. */
export const saida = (frame: number, duracao: number, quadros = 10) =>
  interpolate(frame, [duracao - quadros, duracao], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

/** Lê uma opção do tema com valor padrão (cada estilo define as suas). */
export const opcao = <T,>(tema: Tema, chave: string, padrao: T): T => {
  const v = tema.opcoes?.[chave];
  return v === undefined || v === null ? padrao : (v as T);
};

/** Grão de filme animado. */
export const Grao: React.FC<{ intensidade: number }> = ({ intensidade }) => {
  const frame = useCurrentFrame();
  if (intensidade <= 0) return null;
  const s = Math.floor(frame / 2) % 12;
  return (
    <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: intensidade, pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={`grao-${s}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed={s} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grao-${s})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vinheta: React.FC<{ intensidade: number }> = ({ intensidade }) =>
  intensidade > 0 ? (
    <AbsoluteFill
      style={{ pointerEvents: "none", background: `radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,${intensidade}) 100%)` }}
    />
  ) : null;
