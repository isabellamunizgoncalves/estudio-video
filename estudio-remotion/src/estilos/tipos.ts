import type React from "react";
import type { Cena, Tema, TextoTela } from "../tipos";

/**
 * Contrato de um PACOTE DE ESTILO (o design de um canal).
 *
 * A base (src/base) cuida do que é igual em todo canal: mídia em tela cheia com movimento
 * de câmera, transições, áudio, legendas. O pacote decide a cara: fundos, moldura das fotos,
 * cartelas de título, citações, textos na tela e acabamento (grão, vinheta, etc.).
 *
 * Novo design = nova pasta em src/estilos/<nome>/ exportando um EstiloVisual
 * e uma linha em src/estilos/index.ts. O canal escolhe com "estilo": "<nome>" no tema.json.
 */
export type EstiloVisual = {
  nome: string;
  /** fundo de cartelas, molduras e colagens */
  Fundo: React.FC<{ tema: Tema; cor?: string | null; idCena: string }>;
  /** envolve uma foto/vídeo no estilo "moldura" e cada peça de colagem */
  Moldura: React.FC<{ tema: Tema; idCena: string; entrada: number; children: React.ReactNode; compacta?: boolean }>;
  /** cartela de capítulo (tipo "titulo") */
  CenaTitulo: React.FC<{ cena: Cena; tema: Tema }>;
  /** citação / frase de impacto (tipo "citacao") */
  CenaCitacao: React.FC<{ cena: Cena; tema: Tema }>;
  /** textos sobre a cena: numero, destaque, data, lugar, rotulo */
  TextoNaTela: React.FC<{ texto: TextoTela; tema: Tema; duracaoCena: number; id: string }>;
  /** camada final sobre todo o vídeo (grão, vinheta, bordas…) */
  Acabamento: React.FC<{ tema: Tema }>;
};
