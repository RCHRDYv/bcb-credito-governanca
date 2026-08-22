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

## O padrão que emerge

Os cinco erros têm a mesma forma: **a IA foi rápida e confiante em afirmações que não tinha verificado.** Nenhum deles foi erro de sintaxe ou de implementação, que é onde a assistência é mais forte. Todos foram erros de fato, de procedência ou de contexto.

A prática adotada no projeto a partir daí: **nenhuma afirmação sobre fonte de dado, volume ou endpoint entra em código ou documentação sem verificação direta na origem.** Onde a verificação não foi possível, o documento declara isso explicitamente.

## Por que publicar isso

Porque a alternativa é fingir. Um projeto sobre habilitação de IA construído com IA, com contabilidade transparente do processo, é mais convincente que o mesmo projeto sem essa seção, e substancialmente mais útil para quem quiser reproduzir o método.
