import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { Tema, TextoTela, Timeline } from "../tipos";
import { Faixas, Fita, saida, semente, useEntrada } from "../componentes/Decoracao";
import { pilha } from "../fontes";

/** Texto sobre a cena: "Numéro 3", palavra-chave, data, lugar, rótulo. */
export const TextoNaTela: React.FC<{ texto: TextoTela; tema: Tema; duracaoCena: number; id: string }> = ({
  texto,
  tema,
  duracaoCena,
  id,
}) => {
  const frame = useCurrentFrame();
  const { width, fps } = useVideoConfig();
  const dur = Math.min(duracaoCena, texto.duracao ? Math.round(texto.duracao * fps) : texto.tipo === "numero" ? duracaoCena : 4 * fps);
  const e = useEntrada(6, 13);
  const e2 = useEntrada(14, 14);
  const o = saida(frame, dur, 12);
  if (frame > dur) return null;

  if (texto.tipo === "numero") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", padding: "0 0 9% 7%", opacity: o,
        background: "linear-gradient(to top, rgba(0,0,0,0.5), rgba(0,0,0,0) 45%)" }}>
        <Fita cor={tema.cores.quente} largura={width * 0.17} rotacao={-4} style={{ transform: `rotate(-4deg) translateX(${(1 - e) * -400}px)` }}>
          <span style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.026, color: tema.cores.textoEscuro, letterSpacing: 2 }}>
            {texto.texto}
          </span>
        </Fita>
        {texto.subtexto ? (
          <div
            style={{
              marginTop: 18,
              fontFamily: pilha(tema.fontes.titulo),
              fontSize: width * 0.045,
              color: tema.cores.papel,
              textShadow: `4px 4px 0 ${tema.cores.textoEscuro}`,
              opacity: e2,
              maxWidth: "70%",
            }}
          >
            {texto.subtexto}
          </div>
        ) : null}
        <div style={{ marginTop: 14 }}>
          <Faixas cores={tema.efeitos.faixas} largura={width * 0.16} atraso={18} altura={8} />
        </div>
      </AbsoluteFill>
    );
  }

  if (texto.tipo === "destaque") {
    const alinhamento = texto.posicao === "esquerda" ? "flex-start" : texto.posicao === "direita" ? "flex-end" : "center";
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: alinhamento, padding: "0 7% 8%", opacity: o }}>
        <div
          style={{
            fontFamily: pilha(tema.fontes.titulo),
            fontSize: width * 0.06,
            color: tema.cores.destaque,
            textShadow: `4px 4px 0 ${tema.cores.textoEscuro}`,
            transform: `scale(${0.8 + 0.2 * e})`,
            opacity: e,
            textAlign: "center",
          }}
        >
          {texto.texto}
        </div>
        <div style={{ marginTop: 12 }}>
          <Faixas cores={tema.efeitos.faixas} largura={width * 0.2} atraso={10} />
        </div>
      </AbsoluteFill>
    );
  }

  // data, lugar, rótulo: fita no canto superior
  const rot = (semente(id) - 0.5) * 8;
  return (
    <AbsoluteFill style={{ padding: "6% 6%", alignItems: texto.posicao === "direita" ? "flex-end" : "flex-start", opacity: o }}>
      <Fita cor={texto.tipo === "data" ? tema.cores.papel : tema.cores.quente} largura={width * 0.2} rotacao={rot}
        style={{ transform: `rotate(${rot}deg) scale(${0.6 + 0.4 * e})`, opacity: e }}>
        <span style={{ fontFamily: pilha(texto.tipo === "data" ? tema.fontes.documento : tema.fontes.rotulo), fontSize: width * 0.024, color: tema.cores.textoEscuro, letterSpacing: 1.5 }}>
          {texto.texto}
        </span>
      </Fita>
      {texto.subtexto ? (
        <div style={{ marginTop: 10, fontFamily: pilha(tema.fontes.corpo), fontSize: width * 0.016, color: tema.cores.papel, textShadow: "0 2px 6px rgba(0,0,0,.7)", opacity: e }}>
          {texto.subtexto}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** Legendas (só quando o canal usa). */
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
