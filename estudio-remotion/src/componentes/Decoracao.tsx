import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/** Número pseudoaleatório estável a partir de um texto (mesma cena = mesmo ângulo sempre). */
export const semente = (texto: string) => {
  let h = 2166136261;
  for (let i = 0; i < texto.length; i++) h = Math.imul(h ^ texto.charCodeAt(i), 16777619);
  return ((h >>> 0) % 10000) / 10000;
};

/** Raios de sol girando devagar (sunburst). */
export const Sunburst: React.FC<{ cor: string; corRaio: string; raios?: number; velocidade?: number }> = ({
  cor,
  corRaio,
  raios = 24,
  velocidade = 0.04,
}) => {
  const frame = useCurrentFrame();
  const passo = 360 / raios;
  const fatias = Array.from({ length: raios }, (_, i) => `${i % 2 ? "transparent" : corRaio} ${i * passo}deg ${(i + 1) * passo}deg`);
  return (
    <AbsoluteFill style={{ background: cor, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: "300%",
          height: "300%",
          transform: `translate(-50%, -50%) rotate(${frame * velocidade}deg)`,
          background: `conic-gradient(from 0deg, ${fatias.join(", ")})`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Textura de papel (ruído SVG estático, leve). */
export const Papel: React.FC<{ opacidade?: number }> = ({ opacidade = 0.18 }) => (
  <AbsoluteFill style={{ mixBlendMode: "multiply", opacity: opacidade, pointerEvents: "none" }}>
    <svg width="100%" height="100%">
      <filter id="papel">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="7" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#papel)" />
    </svg>
  </AbsoluteFill>
);

/** Grão de filme animado (muda a semente a cada 2 quadros). */
export const Grao: React.FC<{ intensidade: number }> = ({ intensidade }) => {
  const frame = useCurrentFrame();
  if (intensidade <= 0) return null;
  return (
    <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: intensidade, pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={`grao-${Math.floor(frame / 2) % 12}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed={Math.floor(frame / 2) % 12} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grao-${Math.floor(frame / 2) % 12})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vinheta: React.FC<{ intensidade: number }> = ({ intensidade }) =>
  intensidade > 0 ? (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: `radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,${intensidade}) 100%)`,
      }}
    />
  ) : null;

/** Três faixas coloridas que crescem da esquerda (assinatura sob palavras-chave). */
export const Faixas: React.FC<{ cores: string[]; largura: number; atraso?: number; altura?: number }> = ({
  cores,
  largura,
  atraso = 0,
  altura = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: altura * 0.5, width: largura }}>
      {cores.map((cor, i) => {
        const p = spring({ frame: frame - atraso - i * 4, fps, config: { damping: 200 } });
        return <div key={i} style={{ height: altura, width: `${p * 100}%`, background: cor, borderRadius: altura }} />;
      })}
    </div>
  );
};

/** Pedaço de fita adesiva com bordas serrilhadas. */
export const Fita: React.FC<{ cor: string; largura?: number; altura?: number; rotacao?: number; style?: React.CSSProperties; children?: React.ReactNode }> = ({
  cor,
  largura = 220,
  altura = 54,
  rotacao = -4,
  style,
  children,
}) => {
  const dentes = 9;
  const serra = Array.from({ length: dentes + 1 }, (_, i) => `${(i / dentes) * 100}% ${i % 2 ? 6 : 0}%`).join(", ");
  const serraB = Array.from({ length: dentes + 1 }, (_, i) => `${100 - (i / dentes) * 100}% ${i % 2 ? 94 : 100}%`).join(", ");
  return (
    <div
      style={{
        width: largura,
        minHeight: altura,
        background: cor,
        opacity: 0.94,
        transform: `rotate(${rotacao}deg)`,
        clipPath: `polygon(${serra}, ${serraB})`,
        boxShadow: "0 3px 8px rgba(0,0,0,0.25)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "6px 22px",
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
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
