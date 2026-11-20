---
name: novo-canal
description: Cria um canal novo no estúdio (pasta canais/<id>/ com canal.yaml, guia de roteiro, guia visual e tema do Remotion) por entrevista curta e análise de canais de referência. Use em /novo-canal ou quando Isabella disser que vai abrir outro canal.
---

# /novo-canal

1. **Entrevista (uma mensagem só):** nome do canal; nicho e subnicho; idioma; público (idade, o que sente, por que assiste); 1–3 canais ou vídeos de referência; tom do narrador (ex.: avô contando histórias, investigador, amiga íntima); duração típica; usa legenda?; identidade visual existente (logo, cores, fontes) ou "criar".
2. **Criar a pasta:** `./scripts/novo-canal.sh <id> "<Nome>"` (copia `canais/_modelo/`). `id` em minúsculas, sem espaço.
3. **Preencher** tudo que estiver `__ASSIM__`:
   - `canal.yaml`: idioma, público, `roteiro.*` (palavras/min: 140 calmo, 150 padrão, 165 enérgico), CTA, despedida; `narracao.voz` e `narracao.direcao` (escreva a direção como para um ator, no idioma do canal); `visual.*` (bancos na ordem de preferência; arquivo histórico → archive/wikimedia primeiro); música; fórmula de título.
   - `roteiro.md`: voz, estrutura (fixa do canal ou a padrão de retenção), interação, checklist. Se houver referências, analise títulos/estrutura delas (pode usar o agente analista-emocional nos comentários de uma referência).
   - `visual.md` e `tema.json`: paleta (8 cores do tema), fontes do catálogo de `estudio-remotion/src/fontes.ts` (acrescente lá se precisar de outra do Google Fonts), efeitos (grão, vinheta, papel, sunburst), legendas, logo em `identidade-visual/`.
4. **Voz:** `.venv/bin/python ferramentas/narracao/testar_vozes.py --canal <id>` gera amostras em `canais/<id>/amostras-voz/`; Isabella ouve e escolhe; atualize `narracao.voz`.
5. **Visual:** renderize o exemplo com o tema novo (troque o import em `estudio-remotion/src/exemplo.ts` temporariamente ou crie um projeto de teste) e mostre um quadro.
6. Mostre o resumo do canal e sugira o primeiro `/estudio <id> ...`.
