# Plano da #49: assistente de dados com resposta auditável

## Contexto
O ADR 0012 definiu o assistente: text-to-SQL sobre o esquema estrela, com a ontologia e os trechos de documentos como blocos de contexto que se ligam e desligam. É o mesmo componente para o experimento 2x2 do ADR 0013 (em lote, #48 e #50) e para o uso interativo local. O pré-registro (#47, `evaluation/hipoteses.yml` e `comparacao.yml`, congelados) já fixa:
- o conteúdo das condições (A esquema; B esquema e ontologia; C esquema e trechos; D exatamente B mais os trechos de C);
- o fluxo de duas chamadas (SQL ou abstenção, depois a resposta), sem nova tentativa;
- os cinco campos da resposta, a temperatura de 0,2 e as seeds de 1 a 5.

O prompt, o `num_ctx` e os limites do SQL são fixados pela #48 (`fixado_antes_da_execucao`). A #49 entrega o mecanismo parametrizado, com valores provisórios num arquivo que a #48 preenche e congela por errata.

O "pronto quando" da issue ("responde às perguntas da v0.1 nas quatro condições") exige modelo rodando, não se verifica no CI e rodaria o modelo no conjunto de teste antes da #48 (ADR 0026). Ele será reescrito, como está abaixo.

## Decisões do Yuri (2026-10-08)
1. **Ordem.** A #49 vem antes da #48 e traz o servidor local (Ollama), com modelo provisório só para fumaça. O "pronto quando" vira testes com modelo falso e validadores. O prompt não se afina nas 41 perguntas.
2. **Proveniência.** O código monta a proveniência. O modelo devolve só os 5 campos registrados. O assistente anexa:
   - o SQL executado e o resultado bruto (cortado);
   - os trechos recuperados;
   - os conceitos da ontologia resolvidos pelo código a partir do SQL, com confiança e fonte.
3. **Ontologia em B e D: itens inteiros.** São os 151 itens dos quatro YAML com todos os campos, menos o rótulo em inglês e os metadados de acesso à fonte (endereço, licença, leiaute, formato, transporte, publicador, periodicidade, documentação). Cerca de 29 mil tokens pela estimativa. O maior prompt de D fica perto de 36 mil, com `num_ctx` provisório de 40.960.
   - Revisto no mesmo dia. A versão compacta, de 12 mil tokens, perdia o texto de 16 dos 72 itens citados pelo gabarito e os códigos de filtro.
4. **Servidor.** API nativa `/api/chat` do Ollama, com `num_ctx`, `seed` e `temperature` por requisição e `format` com o esquema JSON da resposta (decodificação restrita).
5. **Interface.** Gradio local, num grupo de dependência próprio. Não é o chat do Space (ADR 0019).
6. **`valores`.** Tabela `{colunas, linhas}`, a mesma forma das respostas do gabarito.
7. **Limite de linhas.** O resultado é cortado e o modelo recebe "resultado cortado em N de M linhas". Valores provisórios: 100 linhas e 30 s.
8. **Vazamento em A.** As `dim_*` trazem definição, confiança, fonte e aviso, consultáveis por SQL em A. Isso é aceito e declarado no ADR como limite, na mesma direção do viés do ADR 0026.
9. **Fumaça.** Com `qwen3:8b` e perguntas inventadas, fora das 41. O Yuri instala o Ollama e baixa o modelo.

## Arquivos a criar
Pacote `assistente/`, com docstrings e comentários bilíngues no estilo de `rag/`:
- **`assistente/parametros.yml`:** servidor, modelo (`qwen3:8b`, `provisorio: true`), `num_ctx`, temperatura, seeds, limite de tokens da resposta, limites de linhas e de tempo, uso do esquema JSON e `think` (o modo de raciocínio do Qwen3 consome tokens e contexto). A #48 congela tudo isso junto.
- **`assistente/parametros.py`:** carrega esse arquivo e confere temperatura e seeds contra o `hipoteses.yml`, como em `rag/parametros.py::conferir_pre_registro`.
- **`assistente/modelo_de_prompt.md`:** rascunho do modelo de prompt, com as instruções comuns e um marcador por bloco (`{esquema}`, `{ontologia}`, `{trechos}`, `{pergunta}`) e o texto da segunda chamada (`{sql}`, `{resultado}`). A #48 revisa e congela.
- **`assistente/ontologia.py`:** carregador de todas as listas dos quatro YAML (conceitos, dimensoes, avisos_gerais, avisos, fontes e as quebras aninhadas), com id `arquivo.id`, o formato do gabarito. Também resolve os conceitos de um SQL:
  - colunas casadas com `metricas.notation`, `dimensoes.coluna` e `fontes_externas.notation`;
  - literais inteiros casados com `notation` e `rotulo_no_dado` das modalidades, nunca por pedaço de texto.

  Os avisos sem campo de vínculo ao dado não aparecem na proveniência montada pelo código. É consequência da decisão 2, a declarar no ADR.
- **`assistente/contexto.py`:** monta as mensagens por condição.
  - O bloco esquema vem só dos nomes e tipos do `evaluation/gabarito/esquema_estrela.json` (cru, sem descrição).
  - O bloco ontologia traz os itens inteiros, na regra da decisão 3, em ordem estável (arquivo, depois posição no YAML).
  - O bloco trechos vem de uma busca só, antes da geração, com o enunciado sem reescrita.
- **`assistente/sql.py`:** guarda e execução.
  - Um comando só, do tipo SELECT, conferido por `duckdb.extract_statements`.
  - Lista do que é permitido, não do que é proibido. A árvore do SQL vem de `json_serialize_sql()`, se ela expuser as referências de tabela (a confirmar no início da execução; senão, regex de `scripts/validar_gabarito.py` mais a recusa de qualquer função de tabela). Só passam tabelas base `dim_*` e `fct_*` (`TABELA_DO_ESQUEMA_ESTRELA`) e CTEs. Função de tabela (`read_*`, `query`, `glob` e afins) e `ATTACH` reprovam.
  - `lock_configuration` depois de criar as views.
  - Limite de tempo por `conexao.interrupt()` num `threading.Timer`.
  - Limite de linhas por fora do SQL: guarda N linhas, conta o total por `fetchmany` e marca o corte.
- **`assistente/cliente.py`:** cliente do Ollama nativo com `urllib.request` (sem dependência nova), mais um cliente falso de respostas gravadas para os testes.
  - Também detecta prompt maior que o `num_ctx`: estimativa antes do envio e `prompt_eval_count` depois. Nesse caso, a execução conta como erro.
- **`assistente/responder.py`:** `responder(pergunta, condicao, seed, *, cliente, banco, buscar) -> dict`.
  - Primeira chamada: `{interpretacao, sql, abstencao}`. O rascunho do prompt diz que vale um único comando com CTEs. Isso importa para a Q28 e a Q30, cujo gabarito usa várias consultas.
  - Se houver SQL, roda uma vez e faz a segunda chamada com os 5 campos.
  - Abstenção na primeira chamada: não há segunda chamada. A resposta final sai com `sql` vazio, `valores` vazio, `interpretacao` e `abstencao` da primeira chamada e `ressalva` vazia.
  - Falha (formato, tempo, SQL, contexto) vira `erro` com o tipo, sem nova tentativa.
  - Devolve o registro completo da execução: parâmetros, mensagens, trechos, SQL, resultado, resposta, proveniência e tempos.
- **`assistente/__main__.py`:** linha de comando `uv run python -m assistente "pergunta" --condicao B [--seed 1]`. Imprime a resposta com a proveniência e grava o registro em `data/assistente/execucoes/` (fora do git).
- **`assistente/interface.py`:** Gradio local, com pergunta, condição e seed, e painéis de resposta, SQL, tabela do resultado, conceitos e trechos. Roda com `uv run --group assistente --group rag python -m assistente.interface`.
- **`scripts/validar_assistente.py`:** no padrão dos `validar_*`, com `--autoteste`. Sem rede, sem modelo e sem dado: usa tabelas vazias a partir do `esquema_estrela.json`, como `checar_portabilidade`, um cliente falso e uma busca falsa. Confere:
  - A sem ontologia e sem trechos; instruções idênticas nas quatro condições; D igual a B mais o bloco de trechos de C; C e D com os mesmos trechos;
  - a guarda recusa escrita, dois comandos, tabela fora do esquema estrela, leitura de arquivo e `ATTACH`;
  - o tempo esgotado interrompe a consulta;
  - o corte avisa N de M;
  - a abstenção não executa SQL;
  - saída fora do formato e prompt grande demais viram erro sem nova tentativa;
  - a proveniência resolve conceitos com confiança e fonte;
  - nenhuma pergunta de fumaça coincide com as 41 do `questions_v3.yml`.

  O `--autoteste` estraga cópias e confere que cada uma reprova pelo motivo certo.
- **`scripts/analises/fumaca_assistente.py`:** roda duas ou três perguntas inventadas nas quatro condições com o Ollama local e grava o relatório em `data/assistente/`. O relatório traz o `prompt_eval_count` real de cada prompt, para a #48 dimensionar o `num_ctx` por um número medido e não pela estimativa. Fica fora do CI, porque depende do Ollama e do índice do RAG locais.
- **`.github/workflows/assistente.yml`:** workflow próprio com `uv sync --frozen`, `validar_assistente` e `--autoteste`. O `ci.yml` não muda.
- **`docs/adr/0029-assistente-local-com-ollama-e-proveniencia-pelo-codigo.md`:** as decisões 2 a 8; o vazamento em A como limite; os parâmetros provisórios que a #48 congela.

## Arquivos a mudar
- **`pyproject.toml` e `uv.lock`:** grupo `assistente = [gradio]`. O núcleo não ganha dependência.
- **`README.md`:** linha do assistente.
- **`CLAUDE.md`:** seção curta "Assistente (#49, ADR 0029)" com os comandos e o grupo.
- **`docs/adr/0012`:** status apontando o ADR 0029, como fez o 0028.

## O que se reaproveita
- `scripts/esquema_estrela_duckdb.py`: `conectar("local")` e `esquema_esperado()`.
- `scripts/validar_gabarito.py`: `COMANDO_DE_ESCRITA`, `TABELA_DO_ESQUEMA_ESTRELA`, `tipo_no_duckdb` e o padrão de tabelas vazias de `checar_portabilidade`.
- `rag/indice.py`: `buscar()`, e `carregar_indice()` para o título da seção. Importado sob demanda, para o CI não puxar o torch.
- `scripts/analises/qa_esquema_estrela.py`: `como_texto`, para serializar o resultado igual ao gabarito.
- O padrão `--autoteste` de `scripts/validar_recuperacao.py`.

## Passos
1. `git pull` na `main` (está 2 commits atrás, sem o merge da #46), depois a branch `feat/49-assistente-de-dados`.
2. Comentar na issue as decisões datadas e trocar o "pronto quando" pelo texto abaixo. As duas coisas ficam públicas no GitHub e estão cobertas pela aprovação deste plano.
3. Construir o pacote, o validador e o workflow. Rodar os validadores.
4. Quando o Yuri tiver instalado o Ollama e rodado `ollama pull qwen3:8b`, rodar a fumaça nas quatro condições e trazer o relatório.

## Pronto quando (o que vai para a issue)
- `uv run python -m scripts.validar_assistente` e `--autoteste` passam localmente e no workflow `assistente.yml`.
- Os validadores do `CLAUDE.md` passam, e o `validar_registro` confirma que nenhum arquivo congelado mudou.
- O ADR 0029 registra as decisões, e o `parametros.yml` marca como provisórios os valores que a #48 fixa.

## Verificação ponta a ponta
- Os dez validadores do `CLAUDE.md`, o `validar_assistente` e o `--autoteste`.
- `git diff --stat main -- evaluation/` vazio.
- Falha conhecida: o `validar_registro --autoteste` já falha só no Windows, por CRLF, na `main`. Não é regressão desta branch. O CI, em Linux, é a referência.
- Com o Ollama: `uv run --group rag python -m scripts.analises.fumaca_assistente` e uma pergunta pela interface, com captura nos dois temas do Gradio fora do repositório, em `../revisao-49`.

## Fora do escopo
- Escolha dos modelos, prompt definitivo, `num_ctx` e limites definitivos, e o congelamento por errata: #48.
- Execução em lote das 41 perguntas, correção e estatística: #50.
- Chat público no Space: #51.
- `questions_v3.yml` fora do `registro.yml`: proponho uma issue separada.
- Pontos que passam para a #48: o 14B em 4 bits com `num_ctx` perto de 40 mil aperta os 12 GB (cache KV em 8 bits ou parte na CPU); a Q28 e a Q30 num SQL único; o valor definitivo de `think`.
