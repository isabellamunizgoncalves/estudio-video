---
name: narracao
description: Só a etapa de narração do estúdio — Gemini TTS (vozes do Google AI Studio) em blocos de ~1 minuto, cada bloco verificado palavra a palavra com Whisper e refeito se alucinar. Use em /narracao, para narrar um roteiro pronto, refazer blocos ("refaz o bloco 7") ou testar vozes.
---

# /narracao

- Projeto: `canal/slug` (se não disser, use `ferramentas/projeto.py listar` e pergunte). Precisa de `02_roteiro/roteiro_narracao_vNN.txt` (senão rode o `humanizador` antes) e `GEMINI_API_KEY` no `.env`.
- Narrar tudo ou refazer blocos: chame o agente `narrador` com o pedido.
- **Texto avulso** (Isabella colou um texto sem projeto): crie um projeto (`projeto.py novo <canal> "<tema>"`), salve o texto como `02_roteiro/roteiro_narracao_v01.txt` e chame o `narrador`.
- **Testar vozes:** `.venv/bin/python ferramentas/narracao/testar_vozes.py --canal <canal> [--vozes A,B,C]`.
- **Trocar voz/modelo só desta vez:** `narrar.py <canal/slug> --voz Gacrux --modelo <modelo>`; para sempre, edite `canais/<canal>/canal.yaml`.
- Entregue: duração, blocos reprovados (se houver) e o caminho do `.wav` para ouvir.
