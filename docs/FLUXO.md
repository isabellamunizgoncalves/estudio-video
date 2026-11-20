# Fluxo — contrato entre as etapas

Cada etapa lê o que a anterior gravou e grava só na própria pasta do projeto `projetos/<canal>/<slug>/`.
Para trocar a ferramenta de uma etapa (outra voz, outro banco de imagens), basta manter o mesmo arquivo de saída.

| # | Etapa | Agente (modelo) | Ferramenta | Lê | Grava |
|---|---|---|---|---|---|
| 1 | Pesquisa emocional | `analista-emocional` (sonnet) | `comentarios/coletar.py` | link do `projeto.json` | `01_pesquisa/comentarios.json`, `contexto.md`, `mapa-emocional.md` |
| 2 | Roteiro | `roteirista` (opus) | `roteiro/extrair_falas.py` | mapa, `canais/<c>/roteiro.md`, `docs/roteiro/` | `02_roteiro/roteiro_vNN.md` + `.txt` |
| 2b | Revisão | `revisor-roteiro` (opus) | — | roteiro, mapa, guia do canal | `02_roteiro/revisao_vNN.md` (APROVADO/REVISAR) |
| 3 | Humanização | `humanizador` (opus) | `roteiro/comparar_palavras.py` | `roteiro_vNN.txt` | `roteiro_narracao_vNN.txt`, `direcao_vNN.json` |
| 4 | Narração | `narrador` (sonnet) | `narracao/narrar.py` (Gemini TTS + Whisper) | humanizado, direção, `canal.yaml › narracao` | `03_narracao/narracao_vNN.wav` + `.json` (palavras e frases com tempo) + `qa_vNN.md` |
| 5 | Decupagem | `diretor-visual` (opus) | — | manifesto da narração, `visual.md`, `tema.json` | `04_visual/decupagem_vNN.json` + `.md` |
| 6 | Mídia | `pesquisador-midia` (sonnet) | `midia/buscar.py`, `midia/baixar.py` | decupagem | `04_visual/candidatos/`, `midia/`, `creditos.json` |
| 7 | Edição | `editor-remotion` (opus) | `edicao/montar_timeline.py`, `edicao/render.py` | narração, decupagem, créditos, música, tema | `05_edicao/timeline_vNN.json`, `renders/previa_*.mp4`, `renders/video_vNN.mp4` |
| 8 | Publicação | `publicador` (sonnet) | `publicacao/creditos.py` | timeline, créditos, roteiro, mapa | `06_publicacao/publicacao_vNN.md`, `capitulos.txt`, `creditos.txt` |

A skill `/estudio` chama os agentes nessa ordem e para nas aprovações (roteiro, narração, decupagem, prévia, títulos).

## Regras do contrato
- **Dono de cada pasta:** só a etapa dona grava nela. `projeto.json` é atualizado pelas ferramentas (`Projeto.marcar`), nunca à mão.
- **Versões só sobem:** `_v01`, `_v02`… A anterior fica. As ferramentas sempre pegam a versão mais recente.
- **A narração manda no tempo:** decupagem e timeline usam os tempos do `narracao_vNN.json`. Narração nova ⇒ decupagem e timeline novas.
- **Sem licença, sem uso:** mídia só entra no timeline se estiver em `creditos.json`.
- **Canal só em `canais/`:** nenhuma regra de canal dentro de agente, skill, ferramenta ou componente.

## Formato do manifesto da narração (`narracao_vNN.json`)
```json
{
  "audio": "03_narracao/narracao_v01.wav", "duracao": 1234.5, "voz": "Charon", "modelo": "...",
  "blocos":   [{"indice": 1, "inicio": 0.0, "fim": 58.2, "texto": "...", "tomadas": 2, "similaridade": 0.97, "aprovado": true}],
  "palavras": [{"texto": "Fermez", "inicio": 0.12, "fim": 0.48, "bloco": 1}],
  "frases":   [{"indice": 0, "texto": "Fermez les yeux une seconde…", "inicio": 0.12, "fim": 2.3, "bloco": 1, "paragrafo": 0}]
}
```

## Formato do timeline (`timeline_vNN.json`)
Gerado por `montar_timeline.py`; tipos em `estudio-remotion/src/tipos.ts`. Tempos em quadros, caminhos relativos ao projeto (o Remotion roda com `--public-dir` = pasta do projeto).
