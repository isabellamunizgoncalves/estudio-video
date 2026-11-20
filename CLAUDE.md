# CLAUDE.md

Responda sempre em português do Brasil.

Este repositório é um **estúdio de vídeo para YouTube com vários canais**. O fluxo é:
pesquisa emocional → roteiro → humanização → narração → direção visual → mídia → edição (Remotion) → publicação.
Visão geral em `README.md`, arquitetura em `docs/ARQUITETURA.md`, contrato de arquivos em `docs/FLUXO.md`.

## Regras de organização

- **Canal ≠ ferramenta.** Tudo que é estilo de um canal (voz, idioma, tom, paleta, fontes, CTA, estrutura de roteiro) vive em `canais/<canal>/`. Agentes, skills, ferramentas e o Remotion são genéricos e leem o canal. Nunca escreva "Rétrovisage" ou outra regra de canal dentro de um agente, ferramenta ou de `estudio-remotion/src/base/` (o único lugar de código com design de canal é o pacote `src/estilos/<estilo>/`).
- **Design é do canal:** cada canal tem seu pacote visual em `estudio-remotion/src/estilos/<estilo>/`, escolhido no `tema.json`. O estilo `retrovisage` é exclusivo do Rétrovisage; canais novos partem do `padrao` ou ganham um estilo próprio. `estudio-remotion/src/base/` não tem design de canal nenhum.
- **Um vídeo = uma pasta:** `projetos/<canal>/<slug>/`, criada por `scripts/novo-video.sh`. Cada etapa grava só na sua subpasta (`01_pesquisa/` … `06_publicacao/`), conforme `docs/FLUXO.md`. Nunca grave saída de vídeo em `canais/`, `ferramentas/`, `estudio-remotion/` ou `.claude/`.
- **Versões só sobem:** gerar de novo cria `_v02`, `_v03`… A versão anterior fica.
- **Agentes** ficam em `.claude/agents/`, **skills** (comandos `/…`) em `.claude/skills/`. A skill `/estudio` é a maestra que chama os agentes na ordem.
- **Narração:** Gemini TTS do Google AI Studio (`ferramentas/narracao/narrar.py`), sempre em blocos de ~1 min com verificação por transcrição (Whisper). Bloco que não bate com o texto é regenerado; nunca aceite um bloco reprovado sem avisar.
- **Mídia:** só de bancos com licença registrada (`ferramentas/midia/`). Toda mídia baixada entra em `04_visual/creditos.json`. Sem fonte e licença = não entra no vídeo.
- **Comentários do público** são radar emocional interno: nunca são citados, parafraseados ou mencionados no roteiro.
- Chaves de API vão em `.env` (nunca no git). Modelo em `.env.exemplo`.
