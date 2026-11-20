# Arquitetura

```
                ┌──────────────── canais/<canal>/ ────────────────┐
                │ canal.yaml · roteiro.md · visual.md · tema.json │  ← estilo de cada canal
                └───────────────────────┬─────────────────────────┘
                                        │ lido por todos
 /estudio (skill maestra) ──chama──► agentes (.claude/agents/) ──usam──► ferramentas/ (Python) + estudio-remotion/ (React)
                                        │
                                        ▼ gravam
                         projetos/<canal>/<slug>/01…06_*/
```

## Três camadas

1. **Canal (dados)** — `canais/<canal>/`. Tudo que muda de um canal para outro: idioma, público, voz e direção de locução, estrutura de roteiro, paleta, fontes, efeitos, bancos de mídia preferidos, fórmula de título. Abrir um canal novo = copiar `_modelo/` e preencher. Zero código.
2. **Agentes e skills (cérebro)** — `.claude/agents/` e `.claude/skills/`. Genéricos; cada um tem um papel, um modelo e um contrato de entrada/saída (`docs/FLUXO.md`). A skill `/estudio` é o produtor que orquestra.
3. **Ferramentas (mãos)** — `ferramentas/` (Python) e `estudio-remotion/` (Remotion). Determinísticas, testáveis, sem opinião de canal.

## Por que cada modelo

| Papel | Modelo | Motivo |
|---|---|---|
| roteirista, revisor-roteiro, humanizador | **opus** | escrita criativa longa, sutileza emocional, crítica fina |
| diretor-visual, editor-remotion | **opus** | decisões de direção e revisão visual dos quadros |
| analista-emocional, narrador, pesquisador-midia, publicador | **sonnet** | leitura em volume, operar ferramentas, escolher entre opções — rápido e barato |

Se o seu plano não tiver Opus, troque `model: opus` por `model: sonnet` no topo do arquivo do agente (ou `inherit` para usar o modelo da sessão).

## Narração sem alucinação (Gemini TTS)

```
roteiro humanizado ──► blocos de ~60 s (sem cortar frase) ──► para cada bloco:
     Gemini TTS (voz + notas do diretor + emoção do trecho)
        └─► Whisper transcreve ─► compara palavra a palavra com o texto
               ├─ ok ─────────────────────────────► apara pontas
               └─ inventou / pulou / leu instrução / cortou / silêncio / duração estranha
                     └─► nova tomada (temperatura diferente; última com o modelo reserva)
──► junta com pausa fixa ──► loudnorm −16 LUFS ──► narracao.wav + tempo de cada palavra
```
Bloco curto = o modelo tem menos chance de se perder; se errar, refaz só 1 minuto. O alinhamento palavra a palavra sai de graça e alimenta a decupagem (sincronia imagem ↔ voz).

## Edição com Remotion

`timeline.json` → componente `Video` → cenas (`midia` com Ken Burns, `moldura` com fita adesiva, `colagem`, `titulo` com sunburst e faixas, `citacao` datilografada) + textos na tela + grão + vinheta + logo + narração + música com fade. As transições entram por cima da cena anterior, então o vídeo nunca desincroniza da voz. Cores, fontes e efeitos vêm do `tema.json` do canal.

## Escalar

- **Novo canal:** `/novo-canal` (ou `scripts/novo-canal.sh`). Nada no código muda.
- **Nova voz/provedor:** implemente `sintetizar(texto, destino, voz=, modelo=, direcao=, tom=, idioma=, temperatura=)` em `ferramentas/narracao/<provedor>.py`; a verificação e o resto continuam iguais.
- **Novo banco de mídia:** uma função em `ferramentas/midia/bancos.py` que devolve o formato padrão + registro em `BANCOS`.
- **Novo efeito de motion:** componente em `estudio-remotion/src/`, ligado por um campo novo na decupagem/timeline e no tema.
- **Vários vídeos em paralelo:** cada projeto é independente; rode `/estudio` em sessões diferentes.
- **Shorts/vertical:** `formato` do canal (1080×1920) — o Remotion se adapta; revise tamanhos de texto no editor.
