import tema from "../../canais/retrovisage/tema.json";
import type { Timeline } from "./tipos";

// Demonstração para o Remotion Studio: só motion graphics, sem mídia nem narração.
export const timelineExemplo: Timeline = {
  canal: "retrovisage",
  slug: "exemplo",
  titulo: "Exemplo",
  fps: 30,
  largura: 1920,
  altura: 1080,
  duracaoQuadros: 450,
  tema: tema as Timeline["tema"],
  audio: { narracao: "", musica: [], sfx: [] },
  legendas: [],
  cenas: [
    { id: "c001", inicio: 0, duracao: 120, tipo: "titulo", titulo: "La France d'autrefois", subtitulo: "ANNÉES 60" },
    { id: "c002", inicio: 120, duracao: 120, tipo: "cartela", fundo: "#E8A33D", textoTela: { tipo: "numero", texto: "NUMÉRO 1", subtexto: "L'odeur de l'encre violette" } },
    { id: "c003", inicio: 240, duracao: 90, tipo: "cartela", fundo: "#D9622B", transicao: "slide", textoTela: { tipo: "data", texto: "1962", subtexto: "Paris" } },
    { id: "c004", inicio: 330, duracao: 120, tipo: "citacao", transicao: "wipe", titulo: "C'était presque rien.\nEt c'était tout.", subtitulo: "RÉTROVISAGE" },
  ],
};
