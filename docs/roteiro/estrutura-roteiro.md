# Estrutura do Roteiro + Checklist de QA

**Regra absoluta 1:** o roteiro entregue contém **somente o texto falado**. Não inclua sugestões de tempo, duração, ritmo, pausas, visual, câmera, cortes, cores, texto na tela, trilha sonora, efeitos ou notas de produção.

**Regra absoluta 2:** o roteiro é **criação original do roteirista**. Comentários são usados apenas para entender emoções — nunca são citados, colados, parafraseados ou mencionados. Proibido: nomes, @handles, curtidas, "alguém comentou", "vocês escreveram", "li os comentários", "fonte: X comentários". A emoção entra; a origem não.

## Modelo de arquivo final

```markdown
# <Título do vídeo>

- **Tema:** <tema fornecido>
- **Idioma:** <idioma informado explicitamente pelo usuário — nunca inferido>
- **Público:** <quem é>
- **CTA:** <ação principal>
- **Ângulo:** <a decisão criativa central>

## Sequência de blocos

1. <bloco> — <função> — <loop aberto/fechado>
2. <bloco> — <função> — <loop>
...

## Roteiro

<blocos no formato abaixo>

## Checklist final

<itens validados>
```

## Formato de cada bloco

```markdown
### GANCHO — Dor espelhada

**Fala:** "Você já sentiu que faz tudo certo e ainda assim parece que nada muda?"
```

Campos obrigatórios: **título do bloco** e **Fala**. Nenhum outro campo.

## Arquivo de narração pura (obrigatório)

Depois de salvar o `.md`, rode `python ferramentas/roteiro/extrair_falas.py <canal/slug>`. Ele gera o `.txt` só com as falas (um parágrafo por bloco, sem Markdown, sem aspas retas; « » internas preservadas), mede a duração e acusa menções a comentários, @handles, carimbos de tempo e colchetes.

## Regras do falado

1. Escreva como se estivesse conversando com **uma pessoa**, não com uma plateia. Você é o especialista que conduz — seguro, humano, sem soar como relatório.
2. Toda cena, exemplo, metáfora e estória é **sua**. Nunca reproduza um comentário, mesmo que pareça uma boa frase. Se reconhecer a origem, reescreva.
3. O espectador não deve perceber que houve uma análise de comentários por trás. Não faça metalinguagem ("eu li o que vocês disseram").
4. Frases curtas. Uma ideia por frase. Sujeito e verbo perto.
5. Use "você" e "a gente" — nunca "os espectadores" ou "o público".
6. Espelhe a emoção **antes** de explicar. Validação vem primeiro.
7. Uma pergunta por vez.
8. Números por extenso soam melhor no falado ("três erros", não "3 erros").
9. Evite advérbios de intenção ("obviamente", "claramente"). Mostre, não afirme.
10. Se uma frase soa como texto de artigo, reescreva mais curta.
11. Cada bloco termina com uma ponte para o próximo — nunca com um ponto final seco.
12. Honestidade acima de tudo: se algo tem limite ou exceção, diga.
13. Não escreva marcações entre colchetes, nem instruções de entrega, nem indicações de imagem ou som.

## Checklist final de QA

- [ ] Idioma do roteiro confirmado com o usuário antes de escrever (não inferido).
- [ ] Todas as falas e CTAs estão no idioma pedido.
- [ ] Roteiro estruturado `.md` salvo.
- [ ] Narração pura `.txt` gerada com `ferramentas/roteiro/extrair_falas.py` — sem rótulos, títulos, markdown ou aspas retas; guillemets francesas internas (`« ... »`) preservadas.
- [ ] **Nenhuma sugestão de tempo, duração, ritmo ou pausa.**
- [ ] **Nenhuma sugestão de visual, câmera, corte ou texto na tela.**
- [ ] **Nenhuma sugestão de trilha sonora, efeito ou volume.**
- [ ] Gancho no início, sem saudação.
- [ ] Promessa clara, específica e verificável.
- [ ] Critério de escolha: o espectador sabe por que ficar.
- [ ] Eventos de retenção distribuídos entre os blocos.
- [ ] Mapa emocional sentido em pelo menos 3 momentos do roteiro — sem nunca ser citado.
- [ ] Pelo menos 3 frases-espelho **originais**, criadas a partir do mapa (não são citações).
- [ ] Perguntas do público reformuladas com as suas palavras e usadas como blocos.
- [ ] Alternância entre momentos de tensão e momentos mais leves.
- [ ] Todos os loops (A, B, C...) foram fechados.
- [ ] Pelo menos uma estória com conflito real, escrita do zero.
- [ ] Dados concretos no lugar de generalizações.
- [ ] CTAs orgânicos, específicos e nos lugares certos (2–3 + final).
- [ ] Texto soa natural ao ser lido em voz alta e tem voz de especialista, não de relatório.
- [ ] **Nenhuma citação de comentário no roteiro** — nem real, nem inventada, nem parafraseada.
- [ ] **Nenhum nome, @handle, curtida, "alguém comentou", "vocês disseram" ou "li os comentários".**
- [ ] **Nenhuma menção a quantidade de comentários ou ao vídeo de referência.**
- [ ] Mapa emocional e citações ficaram apenas em `01_pesquisa/`, fora da entrega.
