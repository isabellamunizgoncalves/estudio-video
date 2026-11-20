import type { Tema, Timeline } from "./tipos";
import retrovisage from "../../canais/retrovisage/tema.json";
import modelo from "../../canais/_modelo/tema.json";

// Temas que aparecem como "Exemplo-<canal>" no Remotion Studio, para ver o design de cada
// canal sem mídia nem voz. Canal novo: acrescente uma linha (o /novo-canal faz isso).
export const TEMAS_EXEMPLO: Record<string, Tema> = {
  retrovisage: retrovisage as Tema,
  modelo: modelo as Tema,
};

export const timelineExemplo = (tema: Tema, nome = "exemplo"): Timeline => ({
  canal: nome,
  slug: "exemplo",
  titulo: "Exemplo",
  fps: 30,
  largura: 1920,
  altura: 1080,
  duracaoQuadros: 450,
  tema,
  audio: { narracao: "", musica: [], sfx: [] },
  legendas: [],
  cenas: [
    { id: "c001", inicio: 0, duracao: 120, tipo: "titulo", titulo: "Título do capítulo", subtitulo: "Capítulo 1" },
    { id: "c002", inicio: 120, duracao: 120, tipo: "cartela", fundo: tema.cores.fundoAlt, textoTela: { tipo: "numero", texto: "Nº 1", subtexto: "Um destaque na tela" } },
    { id: "c003", inicio: 240, duracao: 90, tipo: "cartela", transicao: "slide", textoTela: { tipo: "lugar", texto: "Paris, 1962", subtexto: "rótulo de lugar e data" } },
    { id: "c004", inicio: 330, duracao: 120, tipo: "citacao", transicao: "wipe", titulo: "Uma frase de impacto, dita devagar.", subtitulo: "Citação" },
  ],
});
