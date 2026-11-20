---
name: video
description: Só a etapa visual do estúdio — decupagem cena a cena sobre a narração, busca de imagens e vídeos nos bancos livres, montagem e motion graphics no Remotion, prévias e render final. Use em /video quando a narração já existe, ou para pedidos como "troca a imagem da cena 12", "renderiza o gancho".
---

# /video

- Projeto `canal/slug` com `03_narracao/narracao_vNN.json` pronto.
- Fluxo: `diretor-visual` (aprovação do resumo) → `pesquisador-midia` → `editor-remotion` (prévia do gancho para aprovação → render final).
- Pedidos pontuais:
  - "troca a imagem da cena c012" → `pesquisador-midia` só para essa cena; depois `editor-remotion` remonta e renderiza o trecho.
  - "muda o texto / o movimento / a cor da cena" → `editor-remotion` (nova versão da decupagem).
  - "renderiza de 2:00 a 3:30" → `render.py <canal/slug> --previa --de 120 --ate 210`.
  - "abre no Remotion Studio" → `render.py <canal/slug> --studio` (só no computador de Isabella).
- Música: arquivos em `04_visual/musica/` (Isabella escolhe; YouTube Audio Library e Pixabay Music são livres).
