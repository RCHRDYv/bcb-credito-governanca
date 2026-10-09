# ADR 0028: O corpus do RAG é a lista congelada, o índice se refaz por um comando, e o modelo de embeddings sai do gabarito de recuperação

**Status:** Aceito
**Data:** 2026-10-08

## Contexto

As condições C e D do experimento recebem trechos dos documentos do BCB recuperados por busca ([ADR 0013](0013-experimento-2x2-ontologia-contra-documentos.md)). O [ADR 0012](0012-assistente-de-dados-com-modelo-aberto-e-aplicacao-de-custo-zero.md) decidiu que o corpus são os documentos que a ontologia cita, e que a citação da ontologia dá o gabarito da recuperação. O pré-registro da #47 (`evaluation/hipoteses.yml`, bloco `rag`) fixou quase todo o resto:
- a lista do corpus;
- o trecho: até 512 tokens no tokenizador do modelo, 64 de sobreposição, sem cruzar seção, com documento, seção e página;
- a busca: densa por cosseno, com o enunciado sem reescrita, 5 trechos, uma chamada antes da geração e os mesmos trechos em C e D;
- o modelo de embeddings: multilíngue, "o de maior acerto no gabarito de recuperação da #46, escolhido e versionado antes de qualquer execução de C ou D".

Faltava montar o corpus, o índice e o gabarito de recuperação, e escolher o modelo. Quatro fatos medidos em 2026-10-07 e 2026-10-08 pesaram:
- `docs/referencias.md`, de onde o ADR 0012 dizia sair a lista final, só cita literatura. A lista saiu do bloco congelado, de `docs/leitura-normativos.md`, de `docs/cadeia-normativa.md` e dos campos de fonte da ontologia.
- A API de normativos do BCB (`api/conteudo/app/normativos/exibenormativo`) devolve o texto vigente de cada norma em HTML, com o texto revogado riscado. As normas anteriores a 2020 têm o tipo "Resolução", sem "CMN".
- A página de documentação do PIX no Olinda traz a especificação do serviço em JSON dentro do script. A do SGS é um portal CKAN, com a descrição da série pela API `package_show`.
- O Qwen3-Embedding carrega em bfloat16, o tipo do config dele. Na CPU, a normalização sai com erro na terceira casa (normas de 0,998 a 1,004), e o produto interno deixa de ser o cosseno. O QA pegou a diferença ao recalcular o ranking no DuckDB.

## Decisões

Decidi em 2026-10-07, antes do código (comentário na #46). As decisões 6 a 8 são convenções de implementação que seguem delas, e estão aqui para serem revistas.

1. **Candidatos a modelo de embeddings:** `BAAI/bge-m3`, `intfloat/multilingual-e5-large` e `Qwen/Qwen3-Embedding-0.6B`, cada um fixado por revisão do Hugging Face em `rag/parametros.py`. Os três têm licença MIT ou Apache, aceitam 512 tokens de entrada ou mais e rodam sem código remoto. Os prefixos do e5 (`query: ` e `passage: `) e o prompt de consulta do Qwen3 são o formato de entrada que o próprio modelo pede, e não reescrita da pergunta.
2. **Consulta do gabarito de recuperação:** "O que é <prefLabel_pt>?" para cada conceito. O texto da definição não serve, porque metade dos conceitos é verbatim e a consulta copiaria o trecho.
3. **Métrica de escolha:** acerto@5, a parcela dos conceitos em que um dos 5 trechos trazidos cai na página ou na seção citada. Empate se resolve pela menor memória, como no [ADR 0026](0026-modelos-do-experimento-escolhidos-pela-condicao-a.md). Como tudo roda na CPU, a medida é o tamanho dos pesos carregados. MRR, acerto por documento e acerto nas perguntas do experimento saem só como diagnóstico, para não escolher o modelo pelo conjunto de teste.
4. **O índice é local e se refaz por um comando.** Documentos, seções, trechos e embeddings ficam em `data/` (ignorado pelo git). `rag.construir` confere o sha256 de cada documento contra o manifesto da ingestão, extrai, corta, calcula os embeddings e grava `rag/manifesto.json`. A busca é exata: produto interno entre vetores normalizados em float32, com empate pela ordem do trecho no corpus. Nada é publicado no Hugging Face.
5. **Corpus:** a lista congelada ao pé da letra, com 20 documentos (`ingestion/fontes.py`):
   - metodologias V1 e V2 do SCR.data;
   - instruções e leiaute do documento 3040;
   - os 13 normativos de `docs/leitura-normativos.md` e `docs/cadeia-normativa.md`;
   - o leiaute do CNPJ;
   - a documentação do PIX e do SGS.

   Ficam fora:
   - a planilha de Equivalência de Modalidades;
   - IBGE e SIDRA;
   - o tutorial do SCR.data;
   - as normas que só a ontologia cita (Res. 4.676, numa nota histórica, o Cosif e o Decreto 6.306), por decisão de 2026-10-08;
   - os `.md` do projeto, que levariam conhecimento curado para a condição C.

   Documento novo só entra por errata no registro.
6. **Seção é a divisão que o próprio documento declara:**
   - nas metodologias, os títulos numerados e as alíneas ("2.d"), que é como a ontologia os cita;
   - nas instruções do 3040, as entradas do sumário da página 2 (A a I e os itens numerados), achadas no corpo na página que o sumário indica;
   - no leiaute, cada anexo da aba Anexo, cada bloco da aba Doc3040 e as outras abas inteiras;
   - no CNPJ, cada tabela;
   - nos normativos, o nível mais fino que a norma declara (capítulo, seção ou subseção), inclusive os rótulos entre aspas que uma norma transcreve ao alterar outra ("CAPÍTULO III-A, na CMN 5.255), e a norma inteira quando não tem nenhum;
   - no PIX, a descrição do serviço e cada recurso;
   - no SGS, a descrição da série e cada recurso do portal.

   Incisos e alíneas do texto corrido não abrem seção.
7. **Página:**
   - nos PDFs, a do arquivo, que nas instruções do 3040 é a impressa ("Página 20");
   - na planilha, o nome da aba;
   - no HTML e no JSON, página nula.

   Os normativos vêm todos com texto na API, então o PDF anexo não é usado. O texto riscado é redação revogada e fica de fora.
8. **O limite de 512 tokens conta a entrada inteira do modelo,** com o prefixo e os tokens especiais, para nada ser truncado em silêncio. Os três modelos carregam em float32, para rodarem na mesma precisão e a normalização ser exata.
9. **O gabarito de recuperação é gerado da ontologia** por `scripts/gerar_gabarito_de_recuperacao.py`, chaveado por documento e página ou seção, e nunca por id de trecho, porque cada candidato corta os trechos com o seu tokenizador. Ficam fora do denominador, com o motivo escrito, as lacunas, as medições no dado, o método do projeto e as fontes fora do corpus.
10. **O gabarito de recuperação e o manifesto do RAG entram no `evaluation/registro.yml` por errata datada.** Reconstruir o índice ou regerar o gabarito de um jeito que mude um deles pede errata nova.

## Resultado medido

Medido em 2026-10-08, na CPU, sobre o gabarito de recuperação de 95 conceitos. Dos 105 conceitos da ontologia, ficaram fora 5 lacunas, 4 com fonte no IBGE ou na CONCLA e 1 com fonte no método do projeto.

| Candidato | Trechos | Acerto@5 | MRR | Instruções 3040 (74) | Metodologia V2 (16) | CNPJ (3) | PIX e SGS (2) | Perguntas, diagnóstico (33) |
|---|---|---|---|---|---|---|---|---|
| `Qwen/Qwen3-Embedding-0.6B` | 525 | **87,4%** (83) | 0,727 | 64 | 16 | 1 | 2 | 69,7% (23) |
| `BAAI/bge-m3` | 454 | 80,0% (76) | 0,611 | 57 | 16 | 1 | 2 | 54,5% (18) |
| `intfloat/multilingual-e5-large` | 456 | 71,6% (68) | 0,480 | 49 | 16 | 1 | 2 | 48,5% (16) |

**O modelo do experimento é o `Qwen/Qwen3-Embedding-0.6B`, na revisão `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`,** escolhido pelo acerto@5, sem empate. Os outros números confirmam a ordem, sem decidir: ele também lidera o MRR e o diagnóstico nas perguntas.

O Qwen3 erra 12 conceitos:
- 10 são das instruções do 3040. Sete deles têm rótulo genérico ou repetido: "outros empréstimos", "outros financiamentos", "outros com característica de crédito", "Financiamentos", "comercialização" e "recebíveis adquiridos", que é o rótulo de duas submodalidades (0250 e 0450), com duas consultas idênticas. Os outros três são cheque especial, conta garantida e antecipação de fatura de cartão de crédito.
- 2 são do leiaute do CNPJ: "Empresa ativa" e "Microempreendedor individual", que o documento descreve pelos códigos dos campos. O diagnóstico nas perguntas cobre as 33 perguntas cujo gabarito cita um conceito com alvo. Ele fica bem abaixo do acerto no gabarito, porque o enunciado de uma pergunta de negócio é mais distante do texto normativo do que "O que é X?".

## Alternativas descartadas

**Publicar trechos e embeddings no Hugging Face, como o esquema estrela.** Republicaria texto do BCB e acrescentaria uma etapa de publicação. O índice se refaz em minutos a partir dos documentos públicos, e o manifesto fixa o resultado.

**Embeddings na GPU.** Exigiria o torch com CUDA 12.8 fixado no `uv.lock` por índice próprio. O corpus tem cerca de 500 trechos. Na CPU, duas reconstruções do zero na mesma máquina deram os mesmos sha256 de trechos e embeddings (medido em 2026-10-08). Em outra máquina, outra biblioteca de álgebra linear pode mudar os embeddings na última casa, e a reconstrução avisa pelo sha256.

**Índice aproximado (FAISS, HNSW).** Com 500 trechos, a busca exata é instantânea e não tem aproximação para explicar.

**PyMuPDF para ler os PDFs.** É AGPL, num repositório MIT. O `pypdf` é BSD e dá o texto por página.

**Seção pelos incisos do texto ("IV. No campo...").** Exigiria regex frágil num documento de 138 páginas. O sumário é a divisão que o próprio documento declara, e o acerto nas instruções se mede por página.

**Consulta pelo texto da definição.** Descartada pela decisão 2.

## Consequências

**Positivas.**
- A #49 recebe uma busca pronta, `rag.indice.buscar(pergunta)`, que lê o modelo escolhido no manifesto.
- O gabarito de recuperação se regera da ontologia, e o CI reprova se ele ficar para trás.
- O QA confere a extração contra as definições verbatim da ontologia, sem embeddings, e recalcula o ranking por outro caminho.

**Negativas, e são reais.**
- **A taxa geral pesa as instruções do 3040,** com 74 dos 95 alvos. Por isso o relatório sai por documento.
- **O gabarito mede a busca pela definição, e o experimento busca pelo enunciado da pergunta.** O diagnóstico nas perguntas mostra o tamanho dessa diferença, sem entrar na escolha.
- **Três definições marcadas como verbatim na ontologia resolvem uma referência da fonte** (carteira a vencer, carteira vencida e carteira ativa: a Metodologia V2 diz "Somatório dos itens s e v"). O QA as lista à parte.
- **A extração depende da forma dos documentos.** Uma republicação do BCB muda o sha256, obriga a reconstruir e pode exigir ajuste nas regras de seção. O `rag.construir` para quando um título do sumário não aparece no corpo.
