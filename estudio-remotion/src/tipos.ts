// Formato do timeline.json gerado por ferramentas/edicao/montar_timeline.py.
// Todos os tempos em QUADROS; caminhos relativos à pasta do projeto (--public-dir).

export type Tema = {
  /** pacote de design em src/estilos/<estilo>/ (padrão: "padrao") */
  estilo?: string;
  cores: {
    fundo: string;
    fundoAlt: string;
    destaque: string;
    quente: string;
    papel: string;
    detalhe: string;
    texto: string;
    textoEscuro: string;
  };
  fontes: { titulo: string; rotulo: string; documento: string; corpo: string };
  movimento: { zoomPorPlano: number; transicao: Transicao; duracaoTransicaoQuadros: number };
  /** opções livres lidas só pelo pacote de estilo do canal */
  opcoes?: Record<string, unknown>;
  legendas: { ativas: boolean; fonte: string; tamanho: number; cor: string; contorno: string };
  logo?: string;
};

export type Transicao = "fade" | "slide" | "wipe" | "zoom" | "corte";
export type Movimento = "zoom-in" | "zoom-out" | "pan-esquerda" | "pan-direita" | "parado";

/** Recorte fixo da mídia dentro do quadro, aplicado antes do movimento de câmera.
 *  `zoom` amplia (1 = nada); `x`/`y` (0–1) dizem que ponto da mídia fica no centro. */
export type Enquadramento = { zoom?: number; x?: number; y?: number };

export type TextoTela = {
  tipo: "numero" | "destaque" | "data" | "lugar" | "rotulo";
  texto: string;
  subtexto?: string;
  /** segundos na tela (padrão: cena inteira para "numero", 4 s para os outros) */
  duracao?: number;
  posicao?: "esquerda" | "centro" | "direita";
};

export type Camada = {
  src: string;
  x: number; // 0–1, centro da camada
  y: number;
  largura: number; // 0–1 da largura do quadro
  rotacao?: number;
  atraso?: number; // quadros
};

export type Cena = {
  id: string;
  inicio: number;
  duracao: number;
  tipo: "midia" | "titulo" | "citacao" | "cartela" | "colagem";
  estilo?: "tela-cheia" | "moldura";
  /** "cobrir" (padrão) preenche o quadro e corta; "conter" mostra a mídia inteira sobre o fundo do estilo */
  encaixe?: "cobrir" | "conter";
  enquadramento?: Enquadramento | null;
  movimento?: Movimento;
  transicao?: Transicao;
  pb?: boolean;
  fundo?: string | null;
  src?: string;
  midiaTipo?: "video" | "imagem";
  midiaDuracao?: number;
  textoTela?: TextoTela | null;
  titulo?: string | null;
  subtitulo?: string | null;
  camadas?: Camada[] | null;
  /** cena sem mídia ainda (rascunho) */
  falta?: boolean;
};

export type Musica = {
  src: string;
  inicio: number;
  duracao: number;
  volume: number;
  inicioNoArquivo?: number;
  loop?: boolean;
};

export type Timeline = {
  canal: string;
  slug: string;
  titulo: string;
  fps: number;
  largura: number;
  altura: number;
  duracaoQuadros: number;
  tema: Tema;
  logo?: string;
  audio: {
    narracao: string;
    musica: Musica[];
    sfx: { src: string; inicio: number; volume?: number }[];
  };
  cenas: Cena[];
  legendas: { inicio: number; fim: number; texto: string }[];
};
