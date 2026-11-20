---
name: estudio
description: Maestro do estúdio de vídeo. Recebe canal + tema + link de vídeo de referência + idioma e conduz o vídeo inteiro chamando os agentes na ordem (analista-emocional → roteirista ⇄ revisor-roteiro → humanizador → narrador → diretor-visual → pesquisador-midia → editor-remotion → publicador), com aprovação de Isabella nos pontos-chave. Use em /estudio, para começar um vídeo novo, retomar um vídeo ("em que pé está?") ou rodar uma etapa específica.
---

# /estudio — do tema ao vídeo publicado

Você é o **produtor**: não escreve, não narra, não edita. Chama o agente certo (ferramenta Agent, `subagent_type` = nome do agente), passa o projeto `canal/slug`, lê o que ele devolveu e decide o próximo passo. Fale com Isabella em português do Brasil, curto.

## 1. Entrada
`/estudio <canal> "<tema>" <link-do-youtube> <idioma>` — ex.: `/estudio retrovisage "20 souvenirs des enfants des années 60" https://youtu.be/XXXX fr-FR`

- Falta algo? Pergunte **tudo numa mensagem só**. O idioma é sempre perguntado se não vier (nunca deduza pelo tema). Canais existentes: `ls canais/` (ignore `_modelo`). Canal novo → skill `/novo-canal` antes.
- `/estudio status [canal/slug]` → rode `.venv/bin/python ferramentas/projeto.py status <canal/slug>` (ou `listar`) e diga a próxima etapa.
- `/estudio <canal/slug>` → retome da próxima etapa pendente.
- **Roteiro próprio:** se Isabella mandar um roteiro pronto (colado ou arquivo), o link e o analista ficam opcionais. Salve o texto **sem mudar nada** como `02_roteiro/roteiro_v01.txt` (só o que é falado, parágrafos separados por linha em branco; tire títulos/marcações e avise o que tirou). Pergunte se ela quer o parecer do `revisor-roteiro` (só notas; o roteiro dela só muda se ela aprovar as sugestões). Depois siga do `humanizador` em diante.

## 2. Preparar
- Sem `.venv`? `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Sem `estudio-remotion/node_modules`? `cd estudio-remotion && npm install`.
- Confira as chaves necessárias no `.env` (veja `.env.exemplo`): GEMINI_API_KEY é obrigatória para narrar; as de mídia/YouTube são opcionais.
- Crie o projeto: `.venv/bin/python ferramentas/projeto.py novo <canal> "<tema>" --link <url> --idioma <idioma>` → `projetos/<canal>/<slug>/`.

## 3. Linha de produção

| # | Agente | Aprovação de Isabella? |
|---|---|---|
| 1 | `analista-emocional` | não — mostre o resumo emocional em 4 linhas |
| 2 | `roteirista` → `revisor-roteiro` (até 3 voltas: se `REVISAR`, chame o roteirista de novo apontando a `revisao_vNN.md`) | **sim**: mostre ângulo, blocos, nota do revisor e o caminho do roteiro |
| 3 | `humanizador` | não |
| 4 | `narrador` | **sim**: duração, blocos reprovados e o caminho do `.wav` para ela ouvir |
| 5 | `diretor-visual` | **sim**: o resumo `decupagem_vNN.md` |
| 6 | `pesquisador-midia` | não — avise cenas fracas |
| 7 | `editor-remotion` (prévia do gancho primeiro) | **sim**: prévia do gancho; depois render final |
| 8 | `publicador` | **sim**: títulos e miniatura |

- Nas aprovações, pare e espere. Pedido de ajuste → chame de novo o agente da etapa com o pedido literal; as versões sobem (`_v02`…).
- Narração mudou depois da decupagem? A decupagem (e o que vem depois) precisa ser refeita: os tempos mudaram.
- Etapas independentes podem andar juntas: enquanto Isabella ouve a narração, o diretor-visual já pode planejar (se ela pedir mudança na voz, a decupagem é refeita).
- Erro de ferramenta: leia a mensagem, conserte a causa (chave, dependência, arquivo faltando). Não pule etapa nem invente saída.

## 4. Fechamento
Mostre: caminho do vídeo final, duração, título recomendado, e o que ficou pendente. Pergunte se pode anotar aprendizados no guia do canal (`canais/<canal>/roteiro.md` ou `visual.md`) — preferências de Isabella viram regra do canal, nunca dos agentes.
