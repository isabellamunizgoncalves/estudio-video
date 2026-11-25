# Guia de edição — Rétrovisage

Complementa `visual.md`, que define a identidade. Aqui ficam as decisões de **montagem**:
o que o editor faz com a mídia depois que ela existe. Tudo aprendido editando
`25-plats-annees-60`, o primeiro vídeo do canal.

## A regra que decide quase tudo

**A imagem tem de dizer o que a frase diz.** É o defeito mais caro e o mais fácil de deixar
passar, porque cada plano isolado parece bom. No primeiro vídeo entraram um hambúrguer numa
chapa sob «carne selada na cocotte», lasanha sob «endives au jambon», macarrão sob «pão no
caldo» e lombadas de livros sob «o rosto sério de uma mulher». Nenhum é feio; todos estão
errados.

Ao revisar, leia a frase e olhe o plano **ao mesmo tempo**. Plano bonito que ilustra outra
coisa sai.

## Arquivo histórico

- **Foto quase quadrada** (o acervo Van de Poll sai ~1920×1890): em `tela-cheia` o corte 16:9
  come 21% e decepa pés e cabeças. Use `encaixe: "conter"` sobre o fundo do estilo, e troque
  o movimento para `zoom-in` — em pillarbox o `pan` desliza a foto sobre o fundo, o que é feio.
- **Clipe de filme 4:3** (640×480 nos filmes do Prelinger): `estilo: "moldura"` com
  `encaixe: "conter"`. É a combinação que menos amplia (1,85× contra 3× em tela cheia) e a
  única que não corta. E a moldura com fita **justifica** a imagem menor: em pillarbox puro o
  espectador lê «vídeo esticado», dentro da moldura lê «material de arquivo».
- **Não emende molduras.** Três seguidas já achatam o ritmo; quatro, nunca. Alterne com foto
  em tela cheia e com os vídeos de resolução alta.
- **Nunca colorir nem desbotar arquivo.** Está em `visual.md` e vale como lei: foto de época é
  documento. `pb: true` só onde o original já é P&B.

## Imagem gerada

- **Sempre em cor**, com a paleta de filme da época (ver `canal.yaml › visual.geracao.estilo`).
  A regra «não colorir» vale para arquivo, que tem um original a respeitar; imagem gerada não
  tem. E o canal é colagem colorida.
- **`pb: false` na cena gerada**, senão a edição dessatura o que acabou de nascer em cor.
- **O prompt vai em inglês e diz o tamanho do plano.** A `descricao` da decupagem é escrita em
  português para o diretor e o pesquisador; mandá-la ao modelo produz cena errada («osso do
  peito» virou três meninos de terno numa sala). Use o campo `prompt_geracao`.
- **Diga o que NÃO deve aparecer.** «Osso seco, limpo, sem carne nem molho» funcionou onde
  descrever só o que deveria estar falhou.
- Imagem gerada **ilustra, não documenta**. Arquivo real sempre ganha. Use só em cena encenada
  que o acervo livre não tem: gesto doméstico, família à mesa, retrato.

## Cartelas e texto na tela

- O título escolhe **a cor de maior contraste** com o fundo da cartela, entre as três da
  paleta — não a primeira que passa de um limite. Com limite binário o laranja ficava sobre a
  mostarda a 1,70:1, praticamente invisível, porque «passava».
- A **sombra deslocada** vira creme quando o título fica café, senão vira borrão.
- Fita e três faixas **não** seguem essa regra: ali a cor de identidade vale mais que o
  contraste. No título é o contrário.
- **Datilografia nunca passa de 60% da cena.** A última letra caindo junto com o corte faz a
  frase nunca ficar parada para ser lida.
- Texto `destaque` sobre imagem clara some. Se a cena for clara, põe véu atrás ou troca a cena.

## Ritmo

- Plano médio de ~5 s, 10 a 15 cortes por minuto.
- **Nenhum trecho acima de dois minutos sem cartela, citação ou colagem.** No primeiro vídeo
  houve 2,6 minutos de prato atrás de prato (2:28–5:01) e é o pedaço que cansa.
- **Rosto humano cedo no gancho.** Nos primeiros 34 s, o primeiro rosto aparecia aos 24 s; com
  a avó oferecendo a colher aos 7 s o gancho mudou de patamar.
- **Não repita a mesma mídia dentro de um minuto.** Duas tortas iguais com 7 s de intervalo o
  espectador vê. Longe uma da outra, passa.

## Cenas modernas de propósito

O roteiro contrapõe o antes e o hoje: prateleira de supermercado, bandeja de isopor, balcão de
açougue atual, etiqueta de preço. Essas são modernas **de propósito** e não devem ser
envelhecidas nem trocadas por arquivo. Estão marcadas em `nota_edicao`.

## Nunca

- **Marca de terceiro legível na tela** (um sachê com código de barras entrou no primeiro
  vídeo). Logotipo, embalagem com marca, cartela de texto em outro idioma.
- Texto legível em idioma errado: um livro de cozinha **alemão** com letra gótica entrou sob a
  frase «dans aucun livre». Se o objeto tem letreiro, ou é francês ou é ilegível.
- Mídia marcada «ai generated» no banco. As imagens geradas do estúdio são declaradas em
  `creditos.json` com `gerado: true`; as do banco entram sem aviso e sem controle.
