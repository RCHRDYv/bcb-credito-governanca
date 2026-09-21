# Desenvolvimento com assistência de IA

PT: Este projeto trata de habilitar IA a trabalhar sobre dado corporativo. Seria incoerente construí-lo com IA e não declarar isso. Esta página registra o que a IA acelerou, o que exigiu julgamento humano, e onde ela errou e foi corrigida.

EN: This project is about enabling AI to work over enterprise data. It would be incoherent to build it with AI and not disclose that. This page records what AI accelerated, what required human judgement, and where it was wrong and got corrected.

A parte mais útil é a terceira. Documentação de uso de IA que só lista benefícios não informa nada.

## O que a assistência de IA acelerou

- Descoberta e configuração de ferramental (CLI, autenticação, adaptadores)
- Primeira versão de arquivos de configuração e de scripts utilitários
- Estruturação de documentação e de decisões de arquitetura
- Leitura e sumarização de esquema de dado e de metadado de portal público

## O que exigiu julgamento humano, e continua exigindo

- **Interpretar os normativos do Banco Central** e decidir o que cada modalidade significa quando duas fontes divergem. Este é o núcleo do projeto e não é automatizável com confiança
- **Decidir a direção do fluxo da ontologia.** A proposta inicial da IA era escrever a ontologia primeiro e gerar a documentação a partir dela. A correção humana foi apontar que, no mundo real, o fluxo é o inverso: parte-se da documentação de negócio existente e destila-se a ontologia dali. O projeto adotou o fluxo real
- **Rejeitar dado sintético.** A IA propôs gerar dado bagunçado para depois demonstrar que a governança o resolve. A correção humana foi que isso torna a avaliação circular: quem planta a bagunça e depois a resolve não provou nada. O projeto usa dado público real, cuja bagunça ninguém planejou
- **Definir o que é honesto reivindicar.** Escopo, limitações declaradas e nível de confiança de cada afirmação

## Erros da IA neste projeto, e como foram pegos

### 1. Procedência de dado, o mais grave

A IA recomendou combinar o dataset Home Credit Default Risk com dados macroeconômicos do Banco Central do Brasil. O Home Credit Group é uma financeira de origem tcheca que opera no Leste Europeu e na Ásia. Não há relação possível entre a carteira dela e a taxa de juros brasileira, e qualquer junção seria fabricada.

**Pego por:** revisão humana, com a pergunta direta "essa base é americana ou brasileira?".

**Por que importa:** num projeto sobre governança e procedência de dado, publicar essa junção teria provado o oposto da tese.

### 2. Afirmação sobre volume sem verificar

A IA afirmou com convicção que o dado do SCR era pequeno e que usar Databricks seria sobredimensionamento.

**Pego por:** baixar o arquivo real. Cada CSV mensal tem cerca de 97 MB, e o conjunto multianual chega a vários gigabytes.

**Correção:** o uso de Databricks passou a ter justificativa técnica, e não apenas de aprendizado.

### 3. Suposição sobre a interface da fonte

A especificação inicial assumia que todas as fontes do Banco Central eram API OData. O SCR.data não é: são arquivos ZIP anuais para download. A API OData existe, mas para as estatísticas do PIX.

**Pego por:** consultar os metadados do portal antes de escrever o cliente, em vez de assumir o padrão de URL.

### 4. Guarda-corpo local vazando para o CI

A IA configurou o hook `no-commit-to-branch`, que impede commit direto na branch principal. Correto para desenvolvimento local, mas quebra no CI, porque após o merge o runner faz checkout justamente da branch principal.

**Pego por:** a própria terceira camada de defesa. Os hooks locais passavam e o PR passava; só a execução no servidor expôs a inconsistência.

**Registro:** a falha e a correção estão nos PRs #1 e #2 deste repositório.

### 5. Regressão de segurança introduzida por conveniência

Para configurar uma integração, a IA gravou um token de acesso amplo numa variável de ambiente de usuário, em texto puro. Antes disso, o token vivia apenas num cofre criptografado.

**Pego por:** auditoria a pedido do desenvolvedor, com a pergunta "existe algum risco de segurança aqui?".

**Correção:** variável removida, token de volta ao cofre, e a integração passou a ser opcional em vez de exigir credencial ampla.

### 6. Encoding afirmado sem teste

A IA afirmou, e registrou na especificação, que os arquivos do SCR usavam codificação **latin-1**. Estão em **UTF-8 com BOM**.

A afirmação parecia confirmada porque ler em latin-1 **não gera erro**: latin-1 mapeia qualquer byte para algum caractere, então o arquivo abre normalmente e apenas os acentos ficam corrompidos. A verificação inicial olhou "abriu sem erro" em vez de "o conteúdo está correto".

**Pego por:** um artefato visual no cabeçalho (`ï»¿data_base`), que é a assinatura de um BOM UTF-8 lido como latin-1, seguido de teste explícito decodificando os mesmos bytes em quatro codificações e comparando o resultado.

**Por que importa:** é o pior tipo de falha, porque é silenciosa. Toda a ingestão teria rodado sem erro, produzindo dado com acento corrompido em toda dimensão textual, e a ontologia teria sido construída sobre rótulos errados.

**Correção adotada:** `utf-8-sig`, e a regra de que verificar encoding significa comparar conteúdo decodificado, nunca ausência de exceção.

### 7. Afirmação sobre o conteúdo do dado sem consulta

Ao investigar um rótulo duplo na planilha oficial de equivalência, a IA afirmou que as duas modalidades do rótulo, "PJ - Capital de giro rotativo" e "PJ - Cheque especial e conta garantida", apareciam separadamente no dado de 2025, e usou isso como objeção à hipótese de renomeação.

**Pego por:** o desenvolvedor pediu para conferir a ressalva antes de seguir. A consulta nos 12 meses de 2025 mostrou só o nome novo. A IA provavelmente confundiu com "PJ - Capital de giro", modalidade diferente e a maior da carteira PJ.

**Por que importa:** o erro não gerou afirmação falsa publicada, mas quase derrubou uma conclusão correta. Dúvida sem verificação também é afirmação, e também precisa de fonte.

**Correção:** hipótese de renomeação confirmada pela nota de rodapé da própria planilha e pelo dado. Ver `docs/cadeia-normativa.md`, seção 4.

### 8. Premissas de plano escritas como fato

No plano da ingestão, a IA fez três afirmações sem verificar:
- que o hook de dado bruto só bloqueava `.csv` e `.zip`, deduzido do nome exibido do hook;
- que o Parquet reduziria o envio em cerca de dez vezes;
- os números de linhas e de volume da especificação, escritos de memória.

**Pego por:**
- **O hook:** abrir o arquivo antes de editar. Ele já bloqueava `.parquet` e `.xlsx`, e só o nome exibido estava desatualizado.
- **O Parquet:** medir. Ele é dez vezes menor que o CSV, mas praticamente do tamanho do ZIP, então a redução de envio não existia. A justificativa certa, dispensar a descompactação no servidor, está no ADR 0004.
- **Os números:** conferir contra o manifesto antes do commit. Dois estavam arredondados errado.

**Por que importa:** plano aprovado tende a ser tratado como verdade na execução. Aqui, cada premissa foi conferida no momento de agir sobre ela, e não no momento de escrevê-la.

### 9. Inferência "forte" que o dado derrubou

Na leitura dos normativos, a IA concluiu "por inferência forte" que o `-1` de `numero_de_operacoes` na V2 era o rótulo `<= 15` da V1 com outro nome. A conclusão foi marcada como `inferido`, e não como fato, o que foi certo. Mas a palavra "forte" fez a hipótese parecer mais segura do que era.

**Pego por:** a decisão do desenvolvedor de testar empiricamente em vez de publicar a inferência (`docs/triagem-ontologia.md`, item 1.1). A V2 divulga contagens de 1 a 15, então o `-1` não pode ser o `<= 15`. Ver `docs/sentinela-numero-de-operacoes.md`.

**Por que importa:** é o caso mais próximo do tema do projeto. Uma definição coerente, com fonte citada e redação convincente, estava errada. Só a marcação de confiança e o teste impediram que ela virasse regra de staging.

## O padrão que emerge

Os nove erros têm a mesma forma: **a IA foi rápida e confiante em afirmações que não tinha verificado.** Nenhum deles foi erro de sintaxe ou de implementação, que é onde a assistência é mais forte. Todos foram erros de fato, de procedência ou de contexto.

O sexto acrescenta uma variação relevante: **ausência de erro não é evidência de correção.** Três dos nove casos passaram despercebidos justamente porque nada quebrou. O sétimo mostra o caminho inverso: uma objeção sem verificação quase descartou uma conclusão certa.

A prática adotada no projeto a partir daí: **nenhuma afirmação sobre fonte de dado, volume ou endpoint entra em código ou documentação sem verificação direta na origem.** Onde a verificação não foi possível, o documento declara isso explicitamente.

## Por que publicar isso

Porque a alternativa é fingir. Um projeto sobre habilitação de IA construído com IA, com contabilidade transparente do processo, é mais convincente que o mesmo projeto sem essa seção, e substancialmente mais útil para quem quiser reproduzir o método.
