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
   - `visual.md` e `tema.json`: paleta (8 cores do tema), fontes do catálogo de `estudio-remotion/src/fontes.ts` (acrescente lá se precisar de outra do Google Fonts), legendas, logo em `identidade-visual/`.
4. **Design do canal (cada canal tem o seu):** o estilo `retrovisage` é exclusivo do Rétrovisage — nunca o use em outro canal. Pergunte a Isabella:
   - **Partir do `padrao`** (documentário moderno e limpo) só com cores, fontes e `opcoes` próprias: `"estilo": "padrao"`. Rápido; bom para começar.
   - **Design próprio** (recomendado quando o canal tem identidade forte): chame o agente `editor-remotion` para criar `estudio-remotion/src/estilos/<id>/` copiando o `padrao` e redesenhando fundos, moldura, cartela de título, citação, textos na tela e acabamento a partir das referências que ela mandar; registre em `src/estilos/index.ts` e use `"estilo": "<id>"`.
   - Acrescente o tema em `TEMAS_EXEMPLO` de `estudio-remotion/src/exemplo.ts` e renderize `npx remotion render src/index.ts Exemplo-<id> out/<id>.mp4 --scale 0.5` para Isabella ver.
5. **Voz — Isabella escolhe de ouvido, e isso é uma parada obrigatória.** Nenhum canal nasce com voz definida por você.
   - Pergunte primeiro o **perfil**: voz masculina ou feminina, e que tipo de pessoa narra (idade, temperamento). Nunca deduza pelo tema do canal.
   - Gere as amostras: `.venv/bin/python ferramentas/narracao/testar_vozes.py --canal <id> --perfil masculina` (ou `feminina`). São 8 vozes do gênero pedido, a mesma frase em cada, no idioma do canal. `--todas` abre as 16 masculinas ou 14 femininas; `--vozes A,B,C` escolhe na mão.
   - **Mande os `.wav` para Isabella na conversa** (não basta dizer onde salvou: ela precisa ouvir). Diga o nome da voz em cada arquivo.
   - **Pare e espere a escolha dela.** Só então grave `narracao.voz` no `canal.yaml`. Se nenhuma servir, gere outra rodada com `--todas` ou com outra frase.
   - O Google não publica o timbre de cada voz, só o gênero — então não descreva voz que você não ouviu nem recomende uma por nome. Quem decide é o ouvido dela.
   - **Trocar a voz depois invalida narração já gravada:** os blocos em `03_narracao/` são daquela voz. Avise isso antes de qualquer troca.
6. Mostre o resumo do canal e sugira o primeiro `/estudio <id> ...`.
