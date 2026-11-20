// Cenas da base: só o que é igual em todo canal. O visual vem do pacote de estilo.
import React from "react";
import { AbsoluteFill, Img, interpolate, Loop, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Camada, Cena, Movimento, Tema } from "../tipos";
import type { EstiloVisual } from "../estilos/tipos";
import { useEntrada } from "./util";
import { pilha } from "../fontes";

/** Movimento lento de câmera (Ken Burns). */
export const useCamera = (movimento: Movimento = "zoom-in", duracao: number, zoom: number) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, Math.max(1, duracao)], [0, 1], { extrapolateRight: "clamp" });
  const z = zoom || 0.06;
  switch (movimento) {
    case "zoom-out":
      return `scale(${1 + z - z * t})`;
    case "pan-esquerda":
      return `scale(${1 + z}) translateX(${(z / 2) * 100 - t * z * 100}%)`;
    case "pan-direita":
      return `scale(${1 + z}) translateX(${-(z / 2) * 100 + t * z * 100}%)`;
    case "parado":
      return "scale(1)";
    default:
      return `scale(${1 + z * t})`;
  }
};

export const Midia: React.FC<{ cena: Cena; style?: React.CSSProperties }> = ({ cena, style }) => {
  const css: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    filter: cena.pb ? "grayscale(1) contrast(1.08)" : undefined,
    ...style,
  };
  if (!cena.src) return null;
  if (cena.midiaTipo === "video") {
    const video = <OffthreadVideo src={staticFile(cena.src)} muted style={css} />;
    return cena.midiaDuracao && cena.midiaDuracao < cena.duracao ? <Loop durationInFrames={cena.midiaDuracao}>{video}</Loop> : video;
  }
  return <Img src={staticFile(cena.src)} style={css} />;
};

export const CenaMidia: React.FC<{ cena: Cena; tema: Tema; estilo: EstiloVisual }> = ({ cena, tema, estilo }) => {
  const transform = useCamera(cena.movimento, cena.duracao, tema.movimento.zoomPorPlano);
  const entrada = useEntrada(4, 16);
  if (cena.estilo === "moldura") {
    const { Fundo, Moldura } = estilo;
    return (
      <AbsoluteFill>
        <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform }}>
          <div style={{ width: "74%", aspectRatio: "16 / 10" }}>
            <Moldura tema={tema} idCena={cena.id} entrada={entrada}>
              <Midia cena={cena} />
            </Moldura>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform }}>
        <Midia cena={cena} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const PecaColagem: React.FC<{ camada: Camada; indice: number; tema: Tema; estilo: EstiloVisual; idCena: string }> = ({
  camada,
  indice,
  tema,
  estilo,
  idCena,
}) => {
  const { width, height } = useVideoConfig();
  const e = useEntrada(camada.atraso ?? indice * 8, 13);
  const w = camada.largura * width;
  const { Moldura } = estilo;
  return (
    <div
      style={{
        position: "absolute",
        left: camada.x * width - w / 2,
        top: camada.y * height,
        width: w,
        transform: `translateY(-50%) rotate(${camada.rotacao ?? 0}deg)`,
      }}
    >
      <Moldura tema={tema} idCena={`${idCena}-${indice}`} entrada={e} compacta>
        <Img src={staticFile(camada.src)} style={{ width: "100%", display: "block" }} />
      </Moldura>
    </div>
  );
};

export const CenaColagem: React.FC<{ cena: Cena; tema: Tema; estilo: EstiloVisual }> = ({ cena, tema, estilo }) => {
  const transform = useCamera("zoom-in", cena.duracao, tema.movimento.zoomPorPlano * 0.6);
  const { Fundo } = estilo;
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ transform }}>
        {(cena.camadas ?? []).map((c, i) => (
          <PecaColagem key={i} camada={c} indice={i} tema={tema} estilo={estilo} idCena={cena.id} />
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Cartela lisa; com `falta`, avisa que a cena ainda não tem mídia (rascunho). */
export const CenaCartela: React.FC<{ cena: Cena; tema: Tema; estilo: EstiloVisual }> = ({ cena, tema, estilo }) => {
  const { width } = useVideoConfig();
  const { Fundo } = estilo;
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      {cena.falta ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.025, color: tema.cores.texto, opacity: 0.55, letterSpacing: 3 }}>
            {cena.id.toUpperCase()} · SEM MÍDIA
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
