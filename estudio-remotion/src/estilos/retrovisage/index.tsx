// Estilo EXCLUSIVO do canal Rétrovisage: colagem editorial retrô.
// Raios de sol, papel, fita adesiva, três faixas, máquina de escrever.
// Não use em outros canais: crie um pacote próprio (veja src/estilos/tipos.ts).
import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { EstiloVisual } from "../tipos";
import type { Tema } from "../../tipos";
import { Grao, opcao, saida, semente, useEntrada, Vinheta } from "../../base/util";
import { pilha } from "../../fontes";

// ------------------------------------------------------------------ peças do estilo
const Sunburst: React.FC<{ cor: string; corRaio: string; raios?: number }> = ({ cor, corRaio, raios = 24 }) => {
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
          transform: `translate(-50%, -50%) rotate(${frame * 0.04}deg)`,
          background: `conic-gradient(from 0deg, ${fatias.join(", ")})`,
        }}
      />
    </AbsoluteFill>
  );
};

const Papel: React.FC<{ opacidade?: number }> = ({ opacidade = 0.18 }) => (
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

const Faixas: React.FC<{ cores: string[]; largura: number; atraso?: number; altura?: number }> = ({ cores, largura, atraso = 0, altura = 10 }) => {
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

const Fita: React.FC<{ cor: string; largura?: number; rotacao?: number; style?: React.CSSProperties; children?: React.ReactNode }> = ({
  cor,
  largura = 220,
  rotacao = -4,
  style,
  children,
}) => {
  const d = 9;
  const cima = Array.from({ length: d + 1 }, (_, i) => `${(i / d) * 100}% ${i % 2 ? 6 : 0}%`).join(", ");
  const baixo = Array.from({ length: d + 1 }, (_, i) => `${100 - (i / d) * 100}% ${i % 2 ? 94 : 100}%`).join(", ");
  return (
    <div
      style={{
        width: largura,
        minHeight: 54,
        background: cor,
        opacity: 0.94,
        transform: `rotate(${rotacao}deg)`,
        clipPath: `polygon(${cima}, ${baixo})`,
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

const faixasDo = (tema: Tema) => opcao<string[]>(tema, "faixas", [tema.cores.destaque, tema.cores.quente, tema.cores.detalhe]);

// Luminância relativa (WCAG) de "#rgb" / "#rrggbb"; null se não for hex.
const luminancia = (cor: string): number | null => {
  const h = cor.trim().replace("#", "");
  const hex = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  if (!/^[0-9a-fA-F]{6}$/.test(hex)) return null;
  const canais = [0, 2, 4].map((i) => {
    const v = parseInt(hex.slice(i, i + 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2];
};

/** Devolve `cor` se ela se destacar do fundo; senão a `alternativa`.
 *  Evita cartela com título laranja sobre fundo laranja (ou faixa invisível). */
const legivel = (cor: string, fundo: string, alternativa: string, minimo = 1.25) => {
  const a = luminancia(cor);
  const b = luminancia(fundo);
  if (a === null || b === null) return cor;
  const razao = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  return razao >= minimo ? cor : alternativa;
};

const contraste = (cor: string, fundo: string): number => {
  const a = luminancia(cor);
  const b = luminancia(fundo);
  if (a === null || b === null) return 0;
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
};

/** Para o TÍTULO da cartela: escolhe, entre as cores da paleta, a de maior contraste com o
 *  fundo — e não a primeira que passa de um limite. O limite binário errava em dois dos
 *  quatro fundos do canal: sobre a mostarda o laranja dava 1,70:1 e ficava, porque passava
 *  do mínimo de 1,25; o café dá 5,83:1. Sobre o café, o laranja dava 3,43:1 e o creme dá
 *  10,27:1. Fita e faixas continuam com `legivel`, que preserva a cor de identidade do
 *  canal: ali a cor importa mais que o contraste, no título é o contrário. */
const maisLegivel = (fundo: string, candidatas: string[]): string =>
  candidatas.reduce((a, b) => (contraste(b, fundo) > contraste(a, fundo) ? b : a));

// ------------------------------------------------------------------ contrato
const Fundo: EstiloVisual["Fundo"] = ({ tema, cor, idCena }) => {
  const base = cor || [tema.cores.fundo, tema.cores.quente, tema.cores.destaque, tema.cores.papel][Math.floor(semente(idCena) * 4)];
  const escuro = base === tema.cores.fundo;
  return (
    <>
      {opcao(tema, "sunburst", true) ? (
        <Sunburst cor={base} corRaio={escuro ? tema.cores.fundoAlt : "rgba(255,255,255,0.10)"} />
      ) : (
        <AbsoluteFill style={{ background: base }} />
      )}
      {opcao(tema, "papel", true) ? <Papel /> : null}
    </>
  );
};

const Moldura: EstiloVisual["Moldura"] = ({ tema, idCena, entrada, children, compacta }) => {
  const { width } = useVideoConfig();
  const rot = compacta ? 0 : (semente(idCena) - 0.5) * 5;
  return (
    <div
      style={{
        width: "100%",
        height: compacta ? undefined : "100%",
        background: "#fff",
        padding: width * (compacta ? 0.005 : 0.009),
        boxSizing: "border-box",
        boxShadow: "0 18px 40px rgba(0,0,0,0.45)",
        transform: `rotate(${rot}deg) translateY(${(1 - entrada) * 60}px) scale(${0.94 + 0.06 * entrada})`,
        opacity: entrada,
        position: "relative",
      }}
    >
      <div style={{ width: "100%", height: compacta ? undefined : "100%", overflow: "hidden" }}>{children}</div>
      {compacta ? null : (
        <>
          <Fita cor={tema.cores.quente} rotacao={-38} style={{ position: "absolute", left: -60, top: 10 }} />
          <Fita cor={tema.cores.quente} rotacao={-38} style={{ position: "absolute", right: -60, bottom: 10 }} />
        </>
      )}
    </div>
  );
};

const CenaTitulo: EstiloVisual["CenaTitulo"] = ({ cena, tema }) => {
  const e = useEntrada(3, 12);
  const e2 = useEntrada(14, 18);
  const { width } = useVideoConfig();
  const tamanho = width * ((cena.titulo ?? "").length > 28 ? 0.055 : 0.075);
  const fundoCartela = cena.fundo ?? tema.cores.fundo;
  const corTitulo = maisLegivel(fundoCartela, [tema.cores.destaque, tema.cores.papel, tema.cores.textoEscuro]);
  const corFita = legivel(tema.cores.quente, fundoCartela, tema.cores.papel);
  const cores = faixasDo(tema).map((c) => legivel(c, fundoCartela, tema.cores.papel));
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={fundoCartela} idCena={cena.id} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 8%" }}>
        {cena.subtitulo ? (
          <Fita cor={corFita} largura={width * 0.22} rotacao={-3} style={{ opacity: e2, marginBottom: 28 }}>
            <span style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.022, color: tema.cores.textoEscuro, letterSpacing: 2 }}>
              {cena.subtitulo}
            </span>
          </Fita>
        ) : null}
        <div
          style={{
            fontFamily: pilha(tema.fontes.titulo),
            fontSize: tamanho,
            color: corTitulo,
            // A sombra deslocada é do logo do canal, mas sombra café sob título café
            // (o que acontece sobre a mostarda) vira um borrão: ali ela vai de creme.
            textShadow: `5px 5px 0 ${corTitulo === tema.cores.textoEscuro ? tema.cores.papel : tema.cores.textoEscuro}`,
            textAlign: "center",
            lineHeight: 1.1,
            transform: `scale(${0.85 + 0.15 * e})`,
            opacity: e,
          }}
        >
          {cena.titulo}
        </div>
        <div style={{ marginTop: 30 }}>
          <Faixas cores={cores} largura={width * 0.28} atraso={10} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CenaCitacao: EstiloVisual["CenaCitacao"] = ({ cena, tema }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const texto = cena.titulo ?? "";
  // A datilografia nunca passa de ~60% da cena: nas citações longas ela terminava junto
  // com o corte e a frase inteira não chegava a ficar parada na tela para ser lida.
  const fimDigitacao = Math.max(14, Math.min(6 + texto.length * 1.6, cena.duracao * 0.6));
  const letras = Math.floor(interpolate(frame, [6, fimDigitacao], [0, texto.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
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

const TextoNaTela: EstiloVisual["TextoNaTela"] = ({ texto, tema, duracaoCena, id }) => {
  const frame = useCurrentFrame();
  const { width, fps } = useVideoConfig();
  const dur = Math.min(duracaoCena, texto.duracao ? Math.round(texto.duracao * fps) : texto.tipo === "numero" ? duracaoCena : 4 * fps);
  const e = useEntrada(6, 13);
  const e2 = useEntrada(14, 14);
  const o = saida(frame, dur, 12);
  if (frame > dur) return null;
  const faixas = faixasDo(tema);

  if (texto.tipo === "numero") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", padding: "0 0 9% 7%", opacity: o, background: "linear-gradient(to top, rgba(0,0,0,0.5), rgba(0,0,0,0) 45%)" }}>
        <Fita cor={tema.cores.quente} largura={width * 0.17} rotacao={-4} style={{ transform: `rotate(-4deg) translateX(${(1 - e) * -400}px)` }}>
          <span style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.026, color: tema.cores.textoEscuro, letterSpacing: 2 }}>{texto.texto}</span>
        </Fita>
        {texto.subtexto ? (
          <div style={{ marginTop: 18, fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.045, color: tema.cores.papel, textShadow: `4px 4px 0 ${tema.cores.textoEscuro}`, opacity: e2, maxWidth: "70%" }}>
            {texto.subtexto}
          </div>
        ) : null}
        <div style={{ marginTop: 14 }}>
          <Faixas cores={faixas} largura={width * 0.16} atraso={18} altura={8} />
        </div>
      </AbsoluteFill>
    );
  }

  if (texto.tipo === "destaque") {
    const al = texto.posicao === "esquerda" ? "flex-start" : texto.posicao === "direita" ? "flex-end" : "center";
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: al, padding: "0 7% 8%", opacity: o }}>
        <div style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.06, color: tema.cores.destaque, textShadow: `4px 4px 0 ${tema.cores.textoEscuro}`, transform: `scale(${0.8 + 0.2 * e})`, opacity: e, textAlign: "center" }}>
          {texto.texto}
        </div>
        <div style={{ marginTop: 12 }}>
          <Faixas cores={faixas} largura={width * 0.2} atraso={10} />
        </div>
      </AbsoluteFill>
    );
  }

  const rot = (semente(id) - 0.5) * 8;
  return (
    <AbsoluteFill style={{ padding: "6% 6%", alignItems: texto.posicao === "direita" ? "flex-end" : "flex-start", opacity: o }}>
      <Fita cor={texto.tipo === "data" ? tema.cores.papel : tema.cores.quente} largura={width * 0.2} rotacao={rot} style={{ transform: `rotate(${rot}deg) scale(${0.6 + 0.4 * e})`, opacity: e }}>
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

const Acabamento: EstiloVisual["Acabamento"] = ({ tema }) => (
  <>
    <Grao intensidade={opcao(tema, "grao", 0.12)} />
    <Vinheta intensidade={opcao(tema, "vinheta", 0.55)} />
  </>
);

export const retrovisage: EstiloVisual = { nome: "retrovisage", Fundo, Moldura, CenaTitulo, CenaCitacao, TextoNaTela, Acabamento };
