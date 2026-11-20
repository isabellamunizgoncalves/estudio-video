import React from "react";
import { AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Musica, Tema, Timeline, Transicao } from "./tipos";
import { CenaCartela, CenaCitacao, CenaColagem, CenaMidia, CenaTitulo } from "./cenas/Cenas";
import { Legendas, TextoNaTela } from "./overlays/Textos";
import { Grao, Vinheta } from "./componentes/Decoracao";
import { useFontesDoTema } from "./fontes";

const ConteudoCena: React.FC<{ cena: Cena; tema: Tema }> = ({ cena, tema }) => {
  switch (cena.tipo) {
    case "titulo":
      return <CenaTitulo cena={cena} tema={tema} />;
    case "citacao":
      return <CenaCitacao cena={cena} tema={tema} />;
    case "colagem":
      return <CenaColagem cena={cena} tema={tema} />;
    case "cartela":
      return <CenaCartela cena={cena} tema={tema} />;
    default:
      return <CenaMidia cena={cena} tema={tema} />;
  }
};

/** Envolve a cena com a transição de ENTRADA. A cena anterior continua por baixo,
 *  então a voz nunca sai de sincronia (as cenas não encurtam o vídeo). */
const ComTransicao: React.FC<{ tipo: Transicao; quadros: number; children: React.ReactNode }> = ({ tipo, quadros, children }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const p = quadros > 0 ? interpolate(frame, [0, quadros], [0, 1], { extrapolateRight: "clamp" }) : 1;
  const suave = 1 - Math.pow(1 - p, 3);
  let style: React.CSSProperties = {};
  if (tipo === "fade") style = { opacity: p };
  if (tipo === "slide") style = { transform: `translateX(${(1 - suave) * width}px)` };
  if (tipo === "wipe") style = { clipPath: `inset(0 ${(1 - suave) * 100}% 0 0)` };
  if (tipo === "zoom") style = { opacity: p, transform: `scale(${1.15 - 0.15 * suave})` };
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

const TrilhaMusical: React.FC<{ m: Musica; fps: number }> = ({ m, fps }) => {
  const fade = Math.min(2 * fps, Math.floor(m.duracao / 4));
  return (
    <Sequence from={m.inicio} durationInFrames={m.duracao} layout="none">
      <Audio
        src={staticFile(m.src)}
        loop={m.loop}
        trimBefore={m.inicioNoArquivo || undefined}
        volume={(f) =>
          m.volume *
          interpolate(f, [0, fade, m.duracao - fade, m.duracao], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })
        }
      />
    </Sequence>
  );
};

export const Video: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  const { tema, cenas } = timeline;
  useFontesDoTema(tema);
  const T = tema.movimento.duracaoTransicaoQuadros;

  return (
    <AbsoluteFill style={{ background: tema.cores.fundo }}>
      {cenas.map((cena, i) => {
        const tipo: Transicao = i === 0 ? "corte" : cena.transicao ?? tema.movimento.transicao;
        const t = tipo === "corte" ? 0 : Math.min(T, Math.floor(cena.duracao / 2));
        const from = Math.max(0, cena.inicio - t);
        return (
          <Sequence key={cena.id} from={from} durationInFrames={cena.duracao + (cena.inicio - from)} name={`${cena.id} · ${cena.tipo}`}>
            <ComTransicao tipo={tipo} quadros={cena.inicio - from}>
              <ConteudoCena cena={cena} tema={tema} />
            </ComTransicao>
            {cena.textoTela ? (
              <Sequence from={cena.inicio - from} layout="absolute-fill">
                <TextoNaTela texto={cena.textoTela} tema={tema} duracaoCena={cena.duracao} id={cena.id} />
              </Sequence>
            ) : null}
          </Sequence>
        );
      })}

      <Grao intensidade={tema.efeitos.grao} />
      <Vinheta intensidade={tema.efeitos.vinheta} />
      {timeline.legendas.length ? <Legendas timeline={timeline} /> : null}
      {timeline.logo ? (
        <Img src={staticFile(timeline.logo)} style={{ position: "absolute", right: 36, bottom: 30, width: 86, opacity: 0.55 }} />
      ) : null}

      {timeline.audio.narracao ? <Audio src={staticFile(timeline.audio.narracao)} /> : null}
      {timeline.audio.musica.map((m, i) => (
        <TrilhaMusical key={i} m={m} fps={timeline.fps} />
      ))}
      {timeline.audio.sfx.map((s, i) => (
        <Sequence key={`sfx${i}`} from={s.inicio} layout="none">
          <Audio src={staticFile(s.src)} volume={s.volume ?? 0.5} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
