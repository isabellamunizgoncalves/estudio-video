import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { Timeline } from "../tipos";
import { pilha } from "../fontes";

/** Legendas (só quando o canal usa). Cores e fonte vêm do tema. */
export const Legendas: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const l = timeline.tema.legendas;
  const atual = timeline.legendas.find((s) => frame >= s.inicio && frame < s.fim);
  if (!atual) return null;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "6%" }}>
      <div
        style={{
          maxWidth: "80%",
          textAlign: "center",
          fontFamily: pilha(l.fonte),
          fontSize: l.tamanho * (width / 1920),
          color: l.cor,
          fontWeight: 700,
          WebkitTextStroke: `${Math.max(2, l.tamanho / 14)}px ${l.contorno}`,
          paintOrder: "stroke fill",
          lineHeight: 1.25,
        }}
      >
        {atual.texto}
      </div>
    </AbsoluteFill>
  );
};
