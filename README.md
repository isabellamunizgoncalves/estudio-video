# Estúdio de Vídeo

Estúdio de produção de vídeos para YouTube com **agentes do Claude Code**, feito para **vários canais**.
Você manda **tema + link de um vídeo de referência + idioma**; o estúdio lê as emoções dos comentários, escreve o roteiro, narra com as vozes do Google AI Studio e monta o vídeo com imagens e vídeos de bancos livres e motion graphics no Remotion.

```
/estudio retrovisage "20 souvenirs des enfants des années 60" https://youtu.be/XXXX fr-FR
```

O roteiro é escrito pelo estúdio. Se você já tiver um roteiro pronto, é só colar no `/estudio`: ele pula a escrita e segue para revisão (opcional), humanização e narração.

```
comentários ─► mapa emocional ─► roteiro ⇄ revisão ─► humanização ─► narração Gemini (blocos de 1 min, verificados)
                                                                              │
         publicação ◄─ render 1080p ◄─ Remotion (motion graphics) ◄─ mídia livre ◄─ decupagem cena a cena
```

## Agentes

| Agente | Modelo | O que faz |
|---|---|---|
| `analista-emocional` | sonnet | Coleta os comentários e mapeia emoções, dores, desejos, memórias e o que "faltou" |
| `roteirista` | opus | Escreve o roteiro original com engenharia de retenção e conexão emocional |
| `revisor-roteiro` | opus | Critica como espectador exigente: notas, mapa de abandono, veredito |
| `humanizador` | opus | Pontuação e pausas para a voz (sem mudar palavras) + emoção por trecho |
| `narrador` | sonnet | Gemini TTS em blocos de ~1 min, cada bloco verificado com Whisper e refeito se alucinar |
| `diretor-visual` | opus | Decupagem: imagem, estilo, movimento e texto de cada frase da narração |
| `pesquisador-midia` | sonnet | Busca e escolhe mídia em Internet Archive, Wikimedia, Openverse, Pexels e Pixabay, com licença |
| `editor-remotion` | opus | Monta no Remotion, revisa as prévias quadro a quadro, render final |
| `publicador` | sonnet | Títulos, descrição com capítulos e créditos, tags, conceito de miniatura |

Comandos: `/estudio` (tudo), `/roteiro`, `/narracao`, `/video`, `/novo-canal`.

## Canais

Cada canal é só uma pasta de configuração em `canais/<canal>/` — **nenhum código muda** para abrir outro canal.

| Canal | Idioma | Voz |
|---|---|---|
| [`retrovisage`](canais/retrovisage/) — Rétrovisage, nostalgia da França do séc. XX | fr-FR | Gemini `Charon` |

Novo canal: `/novo-canal` ou `./scripts/novo-canal.sh meu-canal "Meu Canal"`.

**Cada canal tem o seu design.** O visual retrô (raios de sol, fita adesiva, três faixas) é um pacote **exclusivo do Rétrovisage** (`estudio-remotion/src/estilos/retrovisage/`). Canais novos começam no estilo `padrao` (documentário moderno) com as próprias cores e fontes, ou ganham um pacote de design próprio em `estudio-remotion/src/estilos/<canal>/`.

## Instalação

Precisa de Python 3.10+, Node.js 18+, ffmpeg e o Claude Code.

```bash
./scripts/instalar.sh          # .venv, dependências, Remotion e .env
# preencha o .env: GEMINI_API_KEY (obrigatória), PEXELS_API_KEY / PIXABAY_API_KEY / YOUTUBE_API_KEY (opcionais)
.venv/bin/python testes/teste_ponta_a_ponta.py   # teste completo sem gastar API
```

Chaves gratuitas: [Google AI Studio](https://aistudio.google.com/apikey) · [Pexels](https://www.pexels.com/api/) · [Pixabay](https://pixabay.com/api/docs/) · [YouTube Data API](https://console.cloud.google.com/apis/library/youtube.googleapis.com).

## Estrutura

```
.claude/agents/        9 agentes (papel, modelo, contrato)
.claude/skills/        /estudio, /roteiro, /narracao, /video, /novo-canal
canais/                um canal por pasta (+ _modelo/ para copiar)
ferramentas/           Python: comentarios/, roteiro/, narracao/, midia/, edicao/, publicacao/, comum/
estudio-remotion/      Remotion: src/base/ (motor comum) + src/estilos/<estilo>/ (design de cada canal)
projetos/              um vídeo por pasta: projetos/<canal>/<slug>/ (fora do git)
docs/                  ARQUITETURA.md, FLUXO.md (contrato entre etapas), roteiro/ (retenção, estrutura, comentários)
scripts/               instalar, novo-video, novo-canal, status
testes/                teste ponta a ponta com APIs simuladas
```

Detalhes: [docs/ARQUITETURA.md](docs/ARQUITETURA.md) · [docs/FLUXO.md](docs/FLUXO.md)

## Uso manual (sem agentes)

```bash
./scripts/novo-video.sh retrovisage "Tema" https://youtu.be/XXXX fr-FR
P=retrovisage/tema
.venv/bin/python ferramentas/comentarios/coletar.py $P
# … roteiro em 02_roteiro/roteiro_v01.md …
.venv/bin/python ferramentas/roteiro/extrair_falas.py $P
.venv/bin/python ferramentas/narracao/narrar.py $P --plano
.venv/bin/python ferramentas/narracao/narrar.py $P
# … decupagem em 04_visual/decupagem_v01.json …
.venv/bin/python ferramentas/midia/buscar.py $P --todas
.venv/bin/python ferramentas/midia/baixar.py $P --cena c001 --escolha 0
.venv/bin/python ferramentas/edicao/montar_timeline.py $P
.venv/bin/python ferramentas/edicao/render.py $P --previa --de 0 --ate 60
.venv/bin/python ferramentas/edicao/render.py $P
```
