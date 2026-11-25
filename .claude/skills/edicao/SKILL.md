---
name: edicao
description: Monta e renderiza o vídeo no Remotion com o ofício já aprendido — enquadramento, moldura para arquivo, contraste de cartela, render em partes e as conferências que evitam perder horas. Use em /edicao, para renderizar um vídeo inteiro, refazer um trecho, trocar a mídia de uma cena e re-renderizar só o que mudou, ou ajustar o volume da trilha.
---

# /edicao `<canal>/<slug>`

Etapa 7 do estúdio, depois do `pesquisador-midia`. Chama o agente `editor-remotion`.

**Leia primeiro o guia de edição do canal**, se existir: `canais/<canal>/edicao.md`, além de
`visual.md` e `tema.json`. Esta skill traz o **ofício**, que vale para todo canal; o guia do
canal traz o **estilo**, que não vale para nenhum outro.

## Entradas

- `03_narracao/narracao_vNN.{wav,json}` — a versão mais alta, sempre. Narração regravada muda
  todos os tempos; a linha do tempo tem de ser reconstruída do zero, nunca reaproveitada.
- `04_visual/decupagem_vNN.json` e `04_visual/creditos.json`.
- `canais/<canal>/tema.json` → pacote de estilo em `estudio-remotion/src/estilos/<estilo>/`.

## Antes do render longo: as conferências baratas

Cada uma custa minutos; descobrir depois custa horas de render jogadas fora. Todas já pegaram
defeito real:

1. **Cartelas, uma a uma.** Renderize o quadro de cada e **olhe**. Contraste de título, texto
   cortado, quebra de linha estourando a margem.
2. **Colagens.** As camadas apontam para outras cenas. Se uma virou vídeo, a peça quebra —
   confirme que todas as camadas existem e são do tipo esperado.
3. **Cenas geradas.** Não podem ser dessaturadas: confira `pb: false` nelas.
4. **Amostra das cenas de arquivo** em moldura, para ver se o `conter` mostra a imagem inteira
   e a moldura não ficou pequena demais.
5. **Disco.** Um render de 20 min dá ~1,3 GB, e as partes mais outro tanto.

## Render

- **Renderize em partes de ~3,5 minutos** e junte com `ffmpeg -f concat -c:v copy`. O container
  reinicia sem aviso: numa passada única, uma queda aos 80% perde tudo; em partes, perde 21
  minutos. Isso já salvou um render de 20 minutos depois de duas perdas totais.
- **Monte o áudio à parte**, uma mixagem contínua (narração + trilha), e muxe no fim. Dois
  ganhos: nenhuma emenda na faixa sonora, e **mudar o volume da trilha vira um remux de um
  minuto** em vez de um render inteiro.
- Ritmo esperado em CPU, sem placa gráfica: ~4,8 quadros por segundo, ~21 min por parte.

## Depois do render: conferir

- **Fronteiras das partes**: sem quadro duplicado, preto ou salto no movimento de câmera.
- **Sincronia do áudio no FIM**, não só no começo — erro de concatenação só aparece lá.
  Correlação cruzada do áudio do vídeo contra o wav da narração no último minuto.
- `blackdetect` no filme inteiro.
- Duração final contra a da narração.

## Depois de conferir: assistir

Nenhum render se entrega sem ter sido visto. Procure, **por cena e com a frase na mão**:

- imagem que não diz o que a frase diz (o defeito mais comum e o mais caro);
- a mesma mídia repetida dentro de um minuto;
- marca de terceiro ou texto legível em idioma errado na tela;
- texto na tela fraco sobre imagem clara;
- trecho longo sem cartela, citação ou colagem.

Entregue a lista **com o tempo de cada cena**, para a pessoa marcar o que trocar.

## Pedidos pontuais

- «troca a imagem da cena c012» → `pesquisador-midia` só nela; depois remonte e **re-renderize
  só a parte afetada**.
- «a música está alta» → remux do áudio, sem render.
- «renderiza de 2:00 a 3:30» → `render.py <canal/slug> --previa --de 120 --ate 210`.
- «abre no Remotion Studio» → `render.py <canal/slug> --studio`.

## Regras do repositório

- **Nenhum design de canal em `estudio-remotion/src/base/`.** Motor genérico ali; cor, fonte e
  desenho no pacote `src/estilos/<estilo>/`. Capacidade nova (enquadramento, encaixe, peça de
  colagem que aceita vídeo) é motor e vai na base, lendo o fundo do estilo.
- Saída de vídeo só em `projetos/<canal>/<slug>/05_edicao/`.
- Decupagem nova sobe de versão; a anterior fica.
- Toda mudança de cena registra a razão em `nota_edicao`.
