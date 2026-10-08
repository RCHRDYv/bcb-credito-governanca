<!--
PT: Rascunho do Projeto de Pesquisa (4ª etapa do TCC), no formato da Tabela 1 do
    Manual de TCC da POLI USP PRO (docs/tcc/referencia/manual-tcc.md, item 6.1)
    e do template docs/tcc/referencia/template-projeto-de-pesquisa.md. Os trechos
    marcados com [CONFIRMAR] dependem do Yuri, do orientador ou da coordenação.
    Na entrega, o texto vai para o .docx do template (Arial 11, espaçamento 1,5,
    recuo de 1,25 cm), sem estes comentários, junto com o resultado do FDE.
EN: Draft of the research project (4th TCC stage), following the POLI USP PRO
    manual. Items marked [CONFIRMAR] depend on Yuri, the advisor or the course.
-->

**Aluno(a):** Yuri Vida

**Orientador(a):** [CONFIRMAR: nome do(a) orientador(a) designado(a)]

**Curso:** MBA em Data Science & Analytics para Operações

**Ontologia curada ou documentos recuperados como contexto de LLMs em consultas de crédito**

<!-- 13 palavras. Título provisório; alternativa mais curta: "Ontologia contra RAG na geração de SQL sobre dados públicos de crédito" (12 palavras). -->

**Introdução**

Modelos de linguagem de grande escala [LLMs] passaram a ser usados para traduzir perguntas em linguagem natural para consultas em linguagem SQL, tarefa conhecida como text-to-SQL, o que promete dar a gestores acesso direto aos dados das organizações sem a intermediação de um analista. Em bases de laboratório, como o Spider, os modelos atingem acurácias elevadas, mas o desempenho cai de forma acentuada em bases reais, com valores sujos, nomes de colunas pouco descritivos e regras de negócio que não estão escritas no esquema (Yu et al., 2018; Li et al., 2023). No benchmark BIRD, construído justamente sobre bases desse tipo, a acurácia de execução de um modelo de fronteira passou de cerca de 35% para cerca de 55% quando cada pergunta veio acompanhada de uma frase de conhecimento externo explicando o significado dos campos (Li et al., 2023). Resultado semelhante foi observado em protocolo pareado com uma camada semântica descrevendo medidas e convenções de uma base analítica (Autor, 2026). Esses achados indicam que o erro desses modelos decorre, em boa parte, da falta de contexto sobre o significado do dado, e não apenas da falta de capacidade de gerar SQL.

O mercado respondeu a esse problema por dois caminhos. O primeiro é a curadoria de uma camada semântica, como uma ontologia ou um modelo de métricas, que declara de forma estruturada o que cada medida significa, como ela é calculada e quais são seus limites; o vocabulário SKOS é um padrão aberto para representar esse tipo de conhecimento (World Wide Web Consortium [W3C], 2009). O segundo é a geração aumentada por recuperação [RAG], em que trechos dos documentos originais são buscados por similaridade e inseridos no contexto do modelo no momento da pergunta (Lewis et al., 2020). A curadoria exige trabalho especializado e manutenção contínua, enquanto o RAG aproveita documentos que já existem. Para uma organização que decide onde investir, a pergunta prática é se o trabalho de curar uma ontologia se paga quando os mesmos documentos de onde ela seria destilada podem ser recuperados em texto bruto. Na literatura consultada, o efeito do metadado já está bem estabelecido, mas a comparação direta entre as duas formas de entregar o mesmo conhecimento, com pré-registro e em domínio regulatório de língua portuguesa, ainda é pouco explorada.

O Sistema de Informações de Crédito [SCR] do Banco Central do Brasil [BCB] oferece um caso adequado para essa comparação. O conjunto SCR.data publica mensalmente a carteira de crédito do sistema financeiro nacional, agregada por unidade da federação, modalidade, porte, setor econômico e tipo de cliente (Banco Central do Brasil [BCB], 2024). Os dados apresentam dificuldades reais e documentadas: valores sentinela sem explicação, métricas com nomes parecidos e definições regulatórias distintas, como carteira inadimplida e ativo problemático, e uma quebra metodológica entre a primeira e a segunda versão da taxonomia, descrita em documentos oficiais. Assim, o conhecimento necessário para responder corretamente às perguntas está disponível em documentos públicos, o que permite construir tanto a ontologia quanto o corpus do RAG a partir das mesmas fontes, isolando o efeito da forma de apresentação do conhecimento.

Além da acurácia, importa a confiabilidade da resposta. Modelos tendem a responder com segurança mesmo quando o dado não permite uma resposta, em parte porque as avaliações usuais recompensam o palpite e não a abstenção (Kalai et al., 2025). O TrustSQL propôs avaliar sistemas de text-to-SQL também pela capacidade de se abster diante de perguntas não respondíveis (Lee et al., 2024). Em contexto de crédito, uma resposta numérica sem a ressalva que a torna interpretável pode levar a decisões equivocadas de exposição ao risco. Por isso, este trabalho considerará três tipos de acerto: o valor correto, o valor acompanhado da ressalva obrigatória e a abstenção justificada.

A pesquisa se justifica, do ponto de vista aplicado, por orientar a escolha entre duas arquiteturas usadas por empresas que desejam colocar LLMs sobre seus dados, com estimativa do ganho de cada uma e do custo de errar. Do ponto de vista científico, contribui com uma replicação do efeito de metadado em domínio novo e com uma medida pré-registrada da comparação entre conhecimento curado e conhecimento recuperado, abrindo caminho para estudos posteriores com mais perguntas, mais domínios e outras formas de representação do conhecimento.

**Objetivo**

Medir, em pontos percentuais e com intervalo de confiança de 95%, a diferença de acurácia de LLMs abertos ao responder 41 perguntas sobre dados de crédito a pessoas jurídicas do SCR.data em quatro condições de contexto: somente o esquema dos dados; esquema e ontologia curada; esquema e trechos dos documentos oficiais recuperados por RAG; e esquema, ontologia e trechos recuperados, verificando se a ontologia supera os documentos de onde foi destilada e se essa vantagem é maior nas perguntas que exigem ressalva ou abstenção.

**Material e Métodos**

A pesquisa terá natureza aplicada, abordagem quantitativa e caráter explicativo, com delineamento de pesquisa experimental em desenho fatorial 2×2 com medidas repetidas. Como técnicas de coleta, serão empregados o levantamento de dados secundários, com os dados públicos de crédito, e a pesquisa documental, com os normativos e metodologias do BCB que fundamentam a ontologia e o corpus do RAG.

*Dados e infraestrutura.* Os dados de crédito virão do SCR.data (BCB, 2024), complementados por séries do Instituto Brasileiro de Geografia e Estatística [IBGE] e do Sistema Gerenciador de Séries Temporais do BCB. A ingestão será feita na plataforma Databricks, e a modelagem em camadas (bronze, staging, intermediate e marts) será implementada com a ferramenta dbt, resultando em um esquema estrela. Um retrato desse esquema, com mês de referência declarado, será exportado em formato Parquet e consultado pelo banco DuckDB durante o experimento, de modo que todas as condições usem os mesmos dados. Todo o código está em repositório público, o que permite a auditoria e a reprodução do trabalho.

*Fatores experimentais.* O primeiro fator é a presença da ontologia, escrita em SKOS e destilada dos documentos oficiais do BCB, em que cada conceito cita o documento de origem. O segundo fator é a presença de trechos recuperados por RAG de um corpus formado exatamente pelos documentos que a ontologia cita, como as metodologias das versões 1 e 2 do SCR.data e o leiaute do documento 3040. Os documentos serão divididos em trechos de até 512 tokens, e para cada pergunta serão recuperados os cinco trechos mais similares por busca densa com um modelo de embeddings multilíngue, escolhido previamente por um gabarito de recuperação. As quatro condições resultantes serão: A, somente o esquema; B, esquema e ontologia; C, esquema e trechos; D, esquema, ontologia e trechos. O enunciado, as instruções e o formato da resposta serão idênticos entre as condições, variando apenas os blocos de contexto.

*Unidades experimentais e gabarito.* Serão utilizadas 41 perguntas de negócio sobre o crédito a pessoas jurídicas, registradas antes de qualquer execução, classificadas pelo tipo de acerto esperado: valor, valor com ressalva ou abstenção. Para cada pergunta, o gabarito é calculado por consultas SQL portáteis sobre o mesmo esquema estrela, admitindo mais de uma leitura aceita quando a pergunta é ambígua, e conferido por um segundo caminho de cálculo independente.

*Modelos e execução.* Serão usados dois modelos abertos de classes diferentes, um de cerca de 14 bilhões e outro de cerca de 7 a 8 bilhões de parâmetros, quantizados em 4 bits e executados localmente. Os modelos serão selecionados entre candidatos pelo desempenho na condição A, escolha conservadora em relação às hipóteses a favor do contexto. Cada pergunta será executada cinco vezes por condição e por modelo, com temperatura de 0,2 e sementes fixas. Em cada execução, o modelo escreverá uma consulta SQL ou se absterá; a consulta será executada em modo somente leitura e o resultado retornará ao modelo, que redigirá a resposta final em formato estruturado. Uma pergunta será considerada correta em uma condição quando pelo menos três das cinco execuções acertarem, segundo regras de comparação também registradas previamente. Falhas de formato, erros de SQL e estouro de tempo ou de contexto contarão como erro.

*Hipóteses e análise estatística.* As hipóteses foram registradas com direção antes da execução: H1, a condição B acerta mais que a A; H2, a C acerta mais que a A; H3, a B acerta mais que a C nas perguntas de valor; H4, a D não é inferior à melhor entre B e C, com margem de cinco pontos percentuais; e H5, exploratória, a vantagem de B sobre C é maior nas perguntas de ressalva e abstenção do que nas de valor. As comparações pareadas usarão o teste de McNemar exato unilateral (McNemar, 1947), com correção de Holm para a família de hipóteses confirmatórias (Holm, 1979), e o teste Q de Cochran como análise descritiva das quatro condições (Cochran, 1950). O tamanho de efeito será sempre reportado como diferença pareada de proporções com intervalo de Newcombe (Newcombe, 1998). A H4 será avaliada por teste de não inferioridade e a H5 por teste de permutação, com intervalo por bootstrap. Os resultados serão reportados por modelo e por tipo de acerto, junto com a variância entre execuções. O protocolo completo, as hipóteses, o gabarito e as regras de comparação estão congelados por resumos criptográficos verificados em integração contínua, e qualquer alteração posterior será registrada como errata datada e declarada junto ao resultado.

*Limitações previstas.* O número de perguntas é pequeno para efeitos modestos, e o grupo de ressalva e abstenção tem 12 perguntas, razão pela qual a H5 é tratada como exploratória. As conclusões valerão para este domínio, este conjunto de perguntas e estes modelos, apresentadas com tamanho de efeito e não como generalização.

*Aspectos éticos.* A pesquisa não envolve participantes humanos nem dados pessoais identificáveis. Os dados utilizados são de acesso e domínio públicos e agregados, sem possibilidade de identificação individual, o que enquadra o estudo nas hipóteses de dispensa de apreciação pelo Comitê de Ética em Pesquisa previstas nos incisos II, III e V do parágrafo único do art. 1º da Resolução nº 510 (Brasil, 2016). O Formulário de Direcionamento Ético será preenchido e entregue com este projeto. [CONFIRMAR: decisão com o(a) orientador(a) após o FDE.]

**Resultados Esperados**

Espera-se obter a estimativa do ganho de acurácia proporcionado por cada forma de contexto em relação ao esquema puro, com intervalo de confiança, para dois modelos de portes diferentes. Com base na literatura, espera-se que tanto a ontologia quanto os documentos melhorem o desempenho em relação ao esquema puro, confirmando as hipóteses H1 e H2 em domínio brasileiro e em português. Espera-se também que a ontologia supere os documentos recuperados nas perguntas de valor e que essa vantagem seja maior nas perguntas que exigem ressalva ou abstenção, nas quais o conhecimento sobre os limites do dado é decisivo. Caso alguma hipótese seja refutada, o resultado será igualmente relevante: se os documentos recuperados igualarem a ontologia, a evidência favorecerá o RAG como alternativa de menor custo de curadoria. Como produtos, a pesquisa entregará uma recomendação fundamentada para a escolha entre camada semântica e RAG, um conjunto de dados, perguntas e gabarito públicos e reprodutíveis, e um protocolo pré-registrado que poderá ser estendido em estudos de pós-graduação stricto sensu.

**Cronograma de Atividades**

<!-- [CONFIRMAR] Ajustar meses e prazos às datas das etapas definidas pela coordenação (Resultados Preliminares, Depósito e Defesa). -->

| Atividades planejadas | Out/26 | Nov/26 | Dez/26 | Jan/27 | Fev/27 | Mar/27 | Abr/27 | Mai/27 | Jun/27 |
|---|---|---|---|---|---|---|---|---|---|
| Revisão bibliográfica | X | X | X | X | | | | | |
| Entrega do Projeto de Pesquisa e do FDE | X | | | | | | | | |
| Finalização do corpus, índice do RAG e gabarito de recuperação | X | X | | | | | | | |
| Seleção dos modelos na condição A | | X | | | | | | | |
| Execução do experimento (condições A, B, C e D) | | X | X | | | | | | |
| Análise estatística e controle de qualidade | | | X | X | | | | | |
| Redação e entrega dos Resultados Preliminares | | | | X | X | | | | |
| Redação do TCC | | | | | X | X | X | | |
| Depósito do TCC | | | | | | | X | | |
| Preparação da apresentação e defesa | | | | | | | | X | |
| Entrega da versão revisada | | | | | | | | | X |

**Referências**

<!-- [CONFIRMAR] Conferir na fonte cada referência antes da entrega. A de arXiv 2604.25149 está sem autores: completar a partir do artigo. -->

Autor. 2026. [CONFIRMAR: autores e título do artigo arXiv:2604.25149 sobre camada semântica em protocolo pareado]. Disponível em: <https://arxiv.org/abs/2604.25149>. Acesso em: [data].

Banco Central do Brasil [BCB]. 2024. SCR.data: painel de operações de crédito. Disponível em: <https://dadosabertos.bcb.gov.br/dataset/scr_data>. Acesso em: [CONFIRMAR: data].

Brasil. 2016. Resolução nº 510, de 7 de abril de 2016. Dispõe sobre as normas aplicáveis a pesquisas em Ciências Humanas e Sociais. Diário Oficial da União, Brasília, 24 maio 2016. Seção 1, p. 44-46.

Cochran, W.G. 1950. The comparison of percentages in matched samples. Biometrika 37(3-4): 256-266.

Holm, S. 1979. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6(2): 65-70.

Kalai, A.T.; Nachum, O.; Vempala, S.S.; Zhang, E. 2025. Why language models hallucinate. Disponível em: <https://arxiv.org/abs/2509.04664>. Acesso em: [data].

Lee, G.; Chay, W.; Cho, S.; Choi, E. 2024. TrustSQL: benchmarking text-to-SQL reliability with penalty-based scoring. Disponível em: <https://arxiv.org/abs/2403.15879>. Acesso em: [data].

Lewis, P.; Perez, E.; Piktus, A.; Petroni, F.; Karpukhin, V.; Goyal, N.; Küttler, H.; Lewis, M.; Yih, W.; Rocktäschel, T.; Riedel, S.; Kiela, D. 2020. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: Conference on Neural Information Processing Systems, 2020, Vancouver, BC, Canada. Anais... p. 9459-9474.

Li, J.; Hui, B.; Qu, G.; Yang, J.; Li, B.; Li, B.; Wang, B.; Qin, B.; Geng, R.; Huo, N.; Zhou, X.; Ma, C.; Li, G.; Chang, K.C.C.; Huang, F.; Cheng, R.; Li, Y. 2023. Can LLM already serve as a database interface? A big bench for large-scale database grounded text-to-SQLs. In: Conference on Neural Information Processing Systems, 2023, New Orleans, LA, USA. Anais...

McNemar, Q. 1947. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12(2): 153-157.

Newcombe, R.G. 1998. Improved confidence intervals for the difference between binomial proportions based on paired data. Statistics in Medicine 17(22): 2635-2650.

World Wide Web Consortium [W3C]. 2009. SKOS simple knowledge organization system reference. Disponível em: <https://www.w3.org/TR/skos-reference/>. Acesso em: [data].

Yu, T.; Zhang, R.; Yang, K.; Yasunaga, M.; Wang, D.; Li, Z.; Ma, J.; Li, I.; Yao, Q.; Roman, S.; Zhang, Z.; Radev, D. 2018. Spider: a large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. In: Conference on Empirical Methods in Natural Language Processing, 2018, Brussels, Belgium. Anais... p. 3911-3921.
