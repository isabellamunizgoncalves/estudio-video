# projetos/

Um vídeo por pasta: `projetos/<canal>/<slug>/`. Criada por `./scripts/novo-video.sh` (ou pela skill `/estudio`).
Os **textos** (projeto, mapa emocional, roteiros, revisões, decupagem, timeline, publicação) vão para o git, para qualquer sessão retomar o vídeo. A **mídia pesada** (áudio, vídeo, imagens, prévias) e os **comentários brutos** ficam fora: guarde os renders no Drive/HD.

```
projeto.json        canal, tema, link, idioma e estado das etapas
01_pesquisa/        comentarios.json, contexto.md, mapa-emocional.md
02_roteiro/         roteiro_vNN.md/.txt, revisao_vNN.md, roteiro_narracao_vNN.txt, direcao_vNN.json
03_narracao/        narracao_vNN.wav, narracao_vNN.json (tempos), qa_vNN.md, blocos_vNN/
04_visual/          decupagem_vNN.json/.md, candidatos/, midia/, musica/, creditos.json
05_edicao/          timeline_vNN.json, assets/, renders/
06_publicacao/      publicacao_vNN.md, capitulos.txt, creditos.txt
```
