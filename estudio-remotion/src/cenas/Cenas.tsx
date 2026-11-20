import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  Loop,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Camada, Cena, Movimento, Tema } from "../tipos";
import { Faixas, Fita, Papel, semente, Sunburst, useEntrada } from "../componentes/Decoracao";
import { pilha } from "../fontes";

// ---------------------------------------------------------------- movimento de câmera
const useCamera = (movimento: Movimento = "zoom-in", duracao: number, zoom: number) => {
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

// ---------------------------------------------------------------- mídia (foto ou vídeo)
const Midia: React.FC<{ cena: Cena; style?: React.CSSProperties }> = ({ cena, style }) => {
  const filtro = cena.pb ? "grayscale(1) contrast(1.08)" : undefined;
  const css: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover", filter: filtro, ...style };
  if (!cena.src) return null;
  if (cena.midiaTipo === "video") {
    const video = <OffthreadVideo src={staticFile(cena.src)} muted style={css} />;
    return cena.midiaDuracao && cena.midiaDuracao < cena.duracao ? (
      <Loop durationInFrames={cena.midiaDuracao}>{video}</Loop>
    ) : (
      video
    );
  }
  return <Img src={staticFile(cena.src)} style={css} />;
};

const Fundo: React.FC<{ tema: Tema; cor?: string | null; idCena: string }> = ({ tema, cor, idCena }) => {
  const base = cor || [tema.cores.fundo, tema.cores.quente, tema.cores.destaque, tema.cores.papel][Math.floor(semente(idCena) * 4)];
  const escuro = base === tema.cores.fundo;
  return (
    <>
      {tema.efeitos.sunburst ? (
        <Sunburst cor={base} corRaio={escuro ? tema.cores.fundoAlt : "rgba(255,255,255,0.10)"} />
      ) : (
        <AbsoluteFill style={{ background: base }} />
      )}
      {tema.efeitos.papel ? <Papel /> : null}
    </>
  );
};

export const CenaMidia: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const transform = useCamera(cena.movimento, cena.duracao, tema.movimento.zoomPorPlano);
  const entrada = useEntrada(4, 16);
  const { width } = useVideoConfig();

  if (cena.estilo === "moldura") {
    const rot = (semente(cena.id) - 0.5) * 5;
    return (
      <AbsoluteFill>
        <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform }}>
          <div
            style={{
              width: "74%",
              aspectRatio: "16 / 10",
              background: "#fff",
              padding: width * 0.009,
              boxShadow: "0 18px 40px rgba(0,0,0,0.45)",
              transform: `rotate(${rot}deg) translateY(${(1 - entrada) * 60}px) scale(${0.94 + 0.06 * entrada})`,
              opacity: entrada,
              position: "relative",
            }}
          >
            <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
              <Midia cena={cena} />
            </div>
            <Fita cor={tema.cores.quente} rotacao={-38} style={{ position: "absolute", left: -60, top: 10 }} />
            <Fita cor={tema.cores.quente} rotacao={-38} style={{ position: "absolute", right: -60, bottom: 10 }} />
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

// ---------------------------------------------------------------- colagem (várias fotos)
const PecaColagem: React.FC<{ camada: Camada; indice: number }> = ({ camada, indice }) => {
  const { width, height } = useVideoConfig();
  const e = useEntrada(camada.atraso ?? indice * 8, 13);
  const w = camada.largura * width;
  return (
    <div
      style={{
        position: "absolute",
        left: camada.x * width - w / 2,
        top: camada.y * height,
        width: w,
        transform: `translateY(-50%) rotate(${camada.rotacao ?? 0}deg) scale(${0.7 + 0.3 * e})`,
        opacity: e,
        background: "#fff",
        padding: 10,
        boxShadow: "0 6px 12px rgba(0,0,0,0.35)",
      }}
    >
      <Img src={staticFile(camada.src)} style={{ width: "100%", display: "block" }} />
    </div>
  );
};

export const CenaColagem: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const transform = useCamera("zoom-in", cena.duracao, tema.movimento.zoomPorPlano * 0.6);
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ transform }}>
        {(cena.camadas ?? []).map((c, i) => (
          <PecaColagem key={i} camada={c} indice={i} />
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cartela de título (capítulo)
export const CenaTitulo: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const e = useEntrada(3, 12);
  const e2 = useEntrada(14, 18);
  const { width } = useVideoConfig();
  const tamanho = width * ((cena.titulo ?? "").length > 28 ? 0.055 : 0.075);
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo ?? tema.cores.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 8%" }}>
        {cena.subtitulo ? (
          <Fita cor={tema.cores.quente} largura={width * 0.22} rotacao={-3} style={{ opacity: e2, marginBottom: 28 }}>
            <span style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.022, color: tema.cores.textoEscuro, letterSpacing: 2 }}>
              {cena.subtitulo}
            </span>
          </Fita>
        ) : null}
        <div
          style={{
            fontFamily: pilha(tema.fontes.titulo),
            fontSize: tamanho,
            color: tema.cores.destaque,
            textShadow: `5px 5px 0 ${tema.cores.textoEscuro}`,
            textAlign: "center",
            lineHeight: 1.1,
            transform: `scale(${0.85 + 0.15 * e})`,
            opacity: e,
          }}
        >
          {cena.titulo}
        </div>
        <div style={{ marginTop: 30 }}>
          <Faixas cores={tema.efeitos.faixas} largura={width * 0.28} atraso={10} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- citação / documento datilografado
export const CenaCitacao: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const texto = cena.titulo ?? "";
  const letras = Math.floor(interpolate(frame, [6, 6 + texto.length * 1.6], [0, texto.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo ?? tema.cores.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "66%",
            background: tema.cores.papel,
            padding: "70px 80px",
            boxShadow: "0 16px 36px rgba(0,0,0,0.45)",
            transform: `rotate(${(semente(cena.id) - 0.5) * 3}deg)`,
            position: "relative",
          }}
        >
          <Papel opacidade={0.25} />
          <div style={{ fontFamily: pilha(tema.fontes.documento), fontSize: width * 0.03, color: tema.cores.textoEscuro, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>
            {texto.slice(0, letras)}
            <span style={{ opacity: frame % 20 < 10 ? 1 : 0 }}>▍</span>
          </div>
          {cena.subtitulo ? (
            <div style={{ marginTop: 26, fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.018, color: tema.cores.destaque, letterSpacing: 2 }}>
              {cena.subtitulo}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cartela (rascunho / cena sem mídia)
export const CenaCartela: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      {!cena.falta ? null : (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.025, color: tema.cores.texto, opacity: 0.55, letterSpacing: 3 }}>
            {cena.id.toUpperCase()} · SEM MÍDIA
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
