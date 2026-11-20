// Estilo PADRÃO: documentário moderno e limpo. Ponto de partida para canais novos.
// Cores e fontes vêm do tema.json do canal; para um design próprio, copie esta pasta
// para src/estilos/<seu-canal>/ e redesenhe (veja src/estilos/tipos.ts).
//
// Opções (tema.json › opcoes): grao (0–1, padrão 0.04), vinheta (0–1, padrão 0.35),
// raio (px dos cantos, padrão 18), gradiente (true/false, padrão true).
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { EstiloVisual } from "../tipos";
import { Grao, opcao, saida, useEntrada, Vinheta } from "../../base/util";
import { pilha } from "../../fontes";

/** Revela o texto de baixo para cima, palavra por palavra (tipografia cinética). */
const TextoCinetico: React.FC<{ texto: string; atraso?: number; style: React.CSSProperties }> = ({ texto, atraso = 0, style }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ ...style, display: "flex", flexWrap: "wrap", justifyContent: style.textAlign === "left" ? "flex-start" : "center", columnGap: "0.28em" }}>
      {texto.split(/\s+/).map((p, i) => {
        const t = interpolate(frame - atraso - i * 3, [0, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const s = 1 - Math.pow(1 - t, 3);
        return (
          <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: "0.08em" }}>
            <span style={{ display: "inline-block", transform: `translateY(${(1 - s) * 105}%)` }}>{p}</span>
          </span>
        );
      })}
    </div>
  );
};

const Barra: React.FC<{ cor: string; largura: number; atraso?: number; altura?: number }> = ({ cor, largura, atraso = 0, altura = 8 }) => {
  const e = useEntrada(atraso, 200);
  return <div style={{ width: largura * e, height: altura, background: cor, borderRadius: altura }} />;
};

const Fundo: EstiloVisual["Fundo"] = ({ tema, cor }) => {
  const frame = useCurrentFrame();
  const base = cor || tema.cores.fundo;
  if (!opcao(tema, "gradiente", true)) return <AbsoluteFill style={{ background: base }} />;
  const x = 30 + Math.sin(frame / 90) * 10;
  const y = 40 + Math.cos(frame / 110) * 10;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${x}% ${y}%, ${tema.cores.fundoAlt} 0%, ${base} 55%),
                     radial-gradient(circle at ${100 - x}% ${100 - y}%, ${tema.cores.destaque}22 0%, transparent 40%)`,
        backgroundBlendMode: "screen",
      }}
    />
  );
};

const Moldura: EstiloVisual["Moldura"] = ({ tema, entrada, children, compacta }) => {
  const raio = opcao(tema, "raio", 18);
  return (
    <div
      style={{
        width: "100%",
        height: compacta ? undefined : "100%",
        borderRadius: raio,
        overflow: "hidden",
        boxShadow: "0 30px 60px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.08)",
        transform: `translateY(${(1 - entrada) * 40}px) scale(${0.96 + 0.04 * entrada})`,
        opacity: entrada,
      }}
    >
      {children}
    </div>
  );
};

const CenaTitulo: EstiloVisual["CenaTitulo"] = ({ cena, tema }) => {
  const { width } = useVideoConfig();
  const e = useEntrada(0, 200);
  const longo = (cena.titulo ?? "").length > 28;
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 10%" }}>
        {cena.subtitulo ? (
          <div style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.018, color: tema.cores.destaque, letterSpacing: 6, textTransform: "uppercase", opacity: e, marginBottom: 18 }}>
            {cena.subtitulo}
          </div>
        ) : null}
        <TextoCinetico
          texto={cena.titulo ?? ""}
          atraso={4}
          style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * (longo ? 0.058 : 0.085), color: tema.cores.texto, lineHeight: 1.02, textTransform: "uppercase", textAlign: "left" }}
        />
        <div style={{ marginTop: 28 }}>
          <Barra cor={tema.cores.destaque} largura={width * 0.12} atraso={12} altura={10} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CenaCitacao: EstiloVisual["CenaCitacao"] = ({ cena, tema }) => {
  const { width } = useVideoConfig();
  const e = useEntrada(0, 18);
  const eAutor = useEntrada(30, 200);
  return (
    <AbsoluteFill>
      <Fundo tema={tema} cor={cena.fundo} idCena={cena.id} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 14%" }}>
        <div style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.16, lineHeight: 0.6, color: tema.cores.destaque, opacity: e, transform: `scale(${0.6 + 0.4 * e})` }}>“</div>
        <TextoCinetico
          texto={cena.titulo ?? ""}
          atraso={8}
          style={{ fontFamily: pilha(tema.fontes.corpo), fontWeight: 700, fontSize: width * 0.042, color: tema.cores.texto, lineHeight: 1.25, textAlign: "center" }}
        />
        {cena.subtitulo ? (
          <div style={{ marginTop: 34, fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.016, letterSpacing: 4, color: tema.cores.destaque, textTransform: "uppercase", opacity: eAutor }}>
            — {cena.subtitulo}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const TextoNaTela: EstiloVisual["TextoNaTela"] = ({ texto, tema, duracaoCena }) => {
  const frame = useCurrentFrame();
  const { width, fps } = useVideoConfig();
  const dur = Math.min(duracaoCena, texto.duracao ? Math.round(texto.duracao * fps) : texto.tipo === "numero" ? duracaoCena : 4 * fps);
  const e = useEntrada(6, 200);
  const e2 = useEntrada(12, 200);
  const o = saida(frame, dur, 10);
  if (frame > dur) return null;
  const sombra = "0 4px 18px rgba(0,0,0,0.55)";

  if (texto.tipo === "numero") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", padding: "0 0 8% 7%", opacity: o, background: "linear-gradient(to top, rgba(0,0,0,0.6), transparent 50%)" }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 28 }}>
          <div style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.11, lineHeight: 0.85, color: "transparent", WebkitTextStroke: `3px ${tema.cores.destaque}`, opacity: e, transform: `translateX(${(1 - e) * -60}px)` }}>
            {texto.texto.replace(/\D+/g, "") || texto.texto}
          </div>
          <div style={{ paddingBottom: 10 }}>
            <div style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.016, letterSpacing: 5, color: tema.cores.destaque, textTransform: "uppercase", opacity: e }}>{texto.texto}</div>
            {texto.subtexto ? (
              <div style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.042, color: tema.cores.texto, textShadow: sombra, opacity: e2, maxWidth: width * 0.6 }}>{texto.subtexto}</div>
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  if (texto.tipo === "destaque") {
    return (
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", padding: "0 8% 9%", opacity: o }}>
        <TextoCinetico
          texto={texto.texto}
          atraso={4}
          style={{ fontFamily: pilha(tema.fontes.titulo), fontSize: width * 0.062, color: tema.cores.texto, textTransform: "uppercase", textShadow: sombra, textAlign: "center" }}
        />
        <div style={{ marginTop: 14 }}>
          <Barra cor={tema.cores.destaque} largura={width * 0.08} atraso={12} />
        </div>
      </AbsoluteFill>
    );
  }

  // data, lugar, rótulo: lower third com bloco de cor
  const direita = texto.posicao === "direita";
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: direita ? "flex-end" : "flex-start", padding: "0 6% 7%", opacity: o }}>
      <div style={{ display: "flex", alignItems: "stretch", overflow: "hidden", borderRadius: 6, transform: `translateX(${(1 - e) * (direita ? 80 : -80)}px)`, opacity: e }}>
        <div style={{ width: 10, background: tema.cores.destaque }} />
        <div style={{ background: "rgba(0,0,0,0.62)", padding: "14px 26px" }}>
          <div style={{ fontFamily: pilha(tema.fontes.rotulo), fontSize: width * 0.022, color: tema.cores.texto, letterSpacing: 2, textTransform: "uppercase" }}>{texto.texto}</div>
          {texto.subtexto ? (
            <div style={{ fontFamily: pilha(tema.fontes.corpo), fontSize: width * 0.015, color: tema.cores.texto, opacity: 0.8 * e2, marginTop: 4 }}>{texto.subtexto}</div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Acabamento: EstiloVisual["Acabamento"] = ({ tema }) => (
  <>
    <Grao intensidade={opcao(tema, "grao", 0.04)} />
    <Vinheta intensidade={opcao(tema, "vinheta", 0.35)} />
  </>
);

export const padrao: EstiloVisual = { nome: "padrao", Fundo, Moldura, CenaTitulo, CenaCitacao, TextoNaTela, Acabamento };
