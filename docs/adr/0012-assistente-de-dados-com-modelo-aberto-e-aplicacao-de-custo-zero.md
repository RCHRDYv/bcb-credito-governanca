# ADR 0012: A camada de IA é um assistente de dados com modelo aberto, e a aplicação pública roda a custo zero

**Status:** Aceito. Em 2026-09-25, o que este ADR decide sobre a aplicação pública (a decisão 5 e a parte das decisões 1 e 4 que trata dela) foi substituído pelos ADRs [0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md) e [0019](0019-chat-consulta-so-o-esquema-estrela.md). O que ele decide sobre o experimento continua valendo.
**Data:** 2026-09-24

## Contexto

A especificação previa uma camada de IA na v0.3, rodando no Hugging Face Spaces, e um dashboard estático, sem consulta ao banco, porque credencial em JavaScript é pública. Em 2026-09-24 o Yuri trouxe três ideias que mudam o desenho:

1. O que se constrói é uma **ferramenta de texto para pessoas de negócio** consultarem os dados. A ontologia é o pilar, e os documentos do BCB podem ser outra fonte de consulta.
2. O modelo deve ser **aberto e rodar localmente,** na máquina dele: RTX 5070 com 12 GB de VRAM, Ryzen 7 5700X e 32 GB de RAM.
3. O dashboard deve ter uma **caixa de pergunta aberta,** respondida pelo modelo.

E duas restrições continuam valendo: nenhuma credencial do Databricks sai da máquina do Yuri (ADR 0001), e a solução pública precisa ter **custo zero**.

## Decisões

### 1. É um assistente de dados com duas camadas de contexto, e não só um RAG

O núcleo é **text-to-SQL**: o modelo escreve a consulta sobre o esquema estrela, e o número vem do dado, e não do texto do modelo. Por cima vêm duas camadas de contexto independentes, que se ligam e desligam:

- **Ontologia:** conhecimento curado e estruturado, com definição, confiança, fonte e armadilhas;
- **Documentos (RAG):** trechos recuperados dos documentos do BCB, em texto bruto.

```
pergunta ──> assistente
               ├─ SQL sobre o esquema estrela (só SELECT, limite de linhas e de tempo)
               ├─ contexto 1: ontologia            (liga ou desliga)
               └─ contexto 2: busca nos documentos (liga ou desliga)
            <── número + SQL + conceitos usados + ressalva + trechos citados
```

A independência das duas camadas é o que permite o experimento 2x2 do ADR 0013.

### 2. Toda resposta vem com proveniência

A resposta mostra o número, o SQL que o produziu, os conceitos da ontologia usados, com confiança e fonte, a ressalva que o torna interpretável e os trechos de documento citados. Quando o dado não permite responder, o assistente diz isso e diz o que faltaria. É o `valor_com_ressalva` e a `abstencao` do experimento virando comportamento do produto.

### 3. O corpus do RAG são os documentos que a ontologia cita

Metodologias V1 e V2 do SCR.data, leiaute e instruções do documento 3040, os normativos de `docs/leitura-normativos.md` e `docs/cadeia-normativa.md`, o leiaute do CNPJ e a documentação das APIs do PIX e do SGS. A lista final sai de `docs/referencias.md`.

Dois motivos. É onde está a resposta. E, como a ontologia cita a seção de onde tirou cada definição, isso dá o gabarito da recuperação: para cada pergunta, sabe-se que trecho deveria vir, e dá para medir se veio.

Os documentos seguem o padrão de ingestão do projeto: download com manifesto e sha256, e os PDFs fora do repositório, como todo dado bruto.

### 4. Modelo aberto e local no experimento, modelo pequeno na aplicação pública

- **Experimento:** dois modelos abertos de níveis diferentes, como a especificação já exige, dentro de 12 GB de VRAM. Um da classe de ~14B parâmetros em 4 bits, e outro da classe de ~7 a 8B. Rodam localmente, com Ollama ou llama.cpp.
- **Aplicação pública:** um modelo pequeno, da classe de ~1,5 a 3B em 4 bits, que roda em CPU. Não precisa ser o do experimento.
- **Busca nos documentos:** embeddings multilíngues, que rodam em GPU e em CPU.

Os nomes se escolhem no momento da execução, porque modelos abertos mudam rápido, e a escolha sai do próprio gabarito do projeto: dois ou três candidatos, as perguntas da v0.1, e fica o que acertar mais. Não há ajuste fino: a tese é contexto, e não treino.

### 5. O dado vai dentro da aplicação, e a aplicação roda no Hugging Face a custo zero

O dashboard, o esquema estrela e a caixa de pergunta formam **uma aplicação só,** no plano gratuito de CPU do Hugging Face Spaces:

- o esquema estrela da gold é exportado em Parquet para dentro do próprio repositório do Space, e consultado por DuckDB. Não há banco, conexão nem credencial;
- os fatos exportados são agregados e públicos. O bronze do CNPJ, com dado pessoal, nunca sai da máquina do Yuri;
- é o mesmo princípio da exportação estática que a especificação já adotava: o dado sai da gold uma vez, e a aplicação não consulta o Databricks.

A #17, o dashboard da v0.1, é construída já como essa aplicação, lendo os arquivos exportados. A caixa de pergunta entra na v0.3. Assim não se constrói um dashboard estático para depois refazê-lo.

## Alternativas descartadas

**Caixa de pergunta ligada ao modelo local.** A demonstração só funcionaria com a máquina do Yuri ligada.

**Hardware com GPU no Hugging Face, ou API paga de modelo.** Tem custo, e a decisão é custo zero.

**Aplicação consultando o Databricks.** Exigiria credencial fora da máquina do Yuri, e o Databricks Free Edition não serve aplicação pública.

**RAG sobre todos os documentos do BCB.** Mais texto não é mais resposta. O corpus citado pela ontologia tem fonte conferida e dá gabarito de recuperação.

**Ajuste fino do modelo.** Contradiz a tese, que é medir o efeito do contexto.

## Consequências

**Positivas.**
- A ferramenta para negócio e o experimento usam os mesmos componentes.
- Custo zero e nenhuma credencial em lugar nenhum.
- A resposta auditável é o diferencial frente a um chatbot comum, e é o que o experimento mede.

**Negativas, e são reais.**
- **O modelo da aplicação pública acerta menos que os do experimento.** A tela declara isso e mostra sempre o SQL e o número tirado do dado, para quem lê conferir.
- **A resposta pública é lenta,** em segundos, porque roda em CPU.
- **O Space gratuito dorme sem uso,** e a primeira pergunta depois disso demora mais. As condições do plano gratuito, como memória e tempo até dormir, se confirmam no momento da execução.
- **O dado da aplicação é uma cópia.** Ele se atualiza quando a exportação roda de novo, e não sozinho.
