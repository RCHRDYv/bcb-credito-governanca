# ADR 0004: Ingestão em camada bronze: ZIP local, Parquet só texto, volume do Unity Catalog

**Status:** Aceito
**Data:** 2026-09-21

## Contexto

O SCR.data é publicado em um ZIP por ano e por versão, com um CSV por mês. No recorte do projeto, de janeiro de 2024 a julho de 2026, são 62 CSVs mensais: 31 da V2, de cerca de 100 MB cada, e 31 da V1, de cerca de 300 MB. Somam 12,7 GB descompactados e 39,2 milhões de linhas.

O formato tem armadilhas conhecidas (`docs/especificacao.md`):
- UTF-8 com BOM;
- `;` como separador, inclusive dentro de campos entre aspas;
- vírgula decimal;
- valores com espaços à direita na V1;
- o sentinela `-1` na contagem de operações.

O destino é o Databricks Free Edition, que só oferece computação serverless.

Três fatos apareceram ao verificar as fontes antes de escrever o pipeline. Eles moldaram a decisão:
1. **A V2 existe também para 2023 e 2024, e a V1 continua publicada em 2026**, ao contrário do que diz o portal.
2. **O BCB republica arquivos antigos sem aviso.** Os ZIPs de 2024 foram regravados em 2026-09-15. Os de 2026 foram regravados em 2026-09-19, e isso mudou o ativo problemático de junho de 2026 de R$ 627,5 bi para R$ 627,0 bi.
3. **Os totais das duas versões não reconciliam:** a V2 fica de 3,95% a 5,94% acima da V1 (`docs/analise-v1-v2.md`, seção 6).

## Decisão

**Pipeline em cinco etapas, cada uma um módulo em `ingestion/`, todas idempotentes:**

| Etapa | Módulo | O que faz |
|---|---|---|
| 1 | `baixar` | Baixa os ZIPs e registra no manifesto a data de publicação informada pelo servidor, o tamanho e o sha256 |
| 2 | `converter_parquet` | Converte cada CSV mensal em um Parquet com **todas as colunas como texto**, e valida colunas, linhas e data-base contra o CSV |
| 3 | `enviar_volume` | Cria schema e volume se faltarem e envia os Parquets para `/Volumes/workspace/bcb_scr/raw/` |
| 4 | `criar_bronze` | `CREATE OR REPLACE TABLE` de uma tabela bronze por versão, a partir de `read_files` |
| 5 | `verificar_bronze` | Prova que o bronze é o dado publicado: linhas por arquivo contra o manifesto e totais mensais contra o cálculo local |

**Escopo:** a V2 é a fonte principal. A V1 entra como fonte legada, para a reconciliação e para a conformação do ADR 0003.

### Por que tudo como texto no bronze

Inferência de tipo erra em silêncio neste arquivo:
- vírgula decimal vira texto ou nulo, conforme o leitor;
- o `-1` vira um número legítimo;
- o espaço à direita da V1 quebra comparações.

Esse é o mesmo tipo de falha do erro 6 de `docs/desenvolvimento-com-ia.md`: nada quebra, e o dado fica errado. O bronze guarda o que foi publicado. A tipagem acontece no staging do dbt, de forma explícita e testada. A única alteração no bronze é remover o BOM do nome da primeira coluna, que de outro modo viraria `﻿data_base`.

### Por que existe o manifesto

O manifesto (`ingestion/manifesto.json`) é versionado e não contém dado. Ele cumpre dois papéis:
- **Detectar republicação:** quando o BCB regrava um arquivo, o sha256 muda e o diff aparece no git.
- **Servir de gabarito da etapa 5:** as contagens de linha por mês foram conferidas contra o CSV original na conversão, e o bronze precisa reproduzi-las.

## Alternativas descartadas

**Enviar os ZIPs e descompactar no Databricks.**
- **Não reduz o envio:** os ZIPs somam 1,51 GB, e os Parquets, quase o mesmo tanto. A premissa inicial deste ADR era que o Parquet seria dez vezes menor. É, mas em relação ao CSV, não ao ZIP.
- **Acrescenta peças:** descompactar exigiria um job Python serverless escrevendo no volume, só para chegar ao mesmo ponto.

**Enviar os CSVs.** Seriam 12,7 GB, oito vezes mais envio. E o parse de BOM, separador e encoding passaria a acontecer no servidor, longe da validação local.

**Baixar direto do BCB dentro do Databricks.**
- Depende de acesso de saída à internet a partir do serverless do Free Edition, o que não foi verificado.
- Separaria o download da máquina onde o manifesto e a validação acontecem.

**Tipar no bronze** e **Auto Loader ou pipeline declarativo.** O primeiro foi descartado pelo motivo acima. O segundo é desproporcional para dois arquivos por mês e fica para quando houver agendamento.

## Consequências

**Positivas.**
- O bronze é auditável: cada linha carrega `arquivo_origem` e `sha256_zip`.
- Republicação é detectável.
- A igualdade entre o bronze e a fonte é provada por teste, e não presumida.
- Nenhum identificador do workspace fica no código: perfil e warehouse vêm da configuração local.

**Negativas, e são reais.**
- **O envio depende da conexão de quem roda.** Medido em 2026-09-21: cerca de 0,45 MB/s por conexão. O envio usa 6 conexões simultâneas e chegou a cerca de 1,6 MB/s.
- **O pipeline roda da máquina do desenvolvedor**, não de forma agendada.
- **A V1 dobra o armazenamento** para uso legado.
- **Custo de armazenamento no Free Edition:** o volume guarda os Parquets e as tabelas Delta guardam uma segunda cópia.

**Fora do escopo desta decisão:** staging, tratamento do sentinela e conformação de modalidades. Eles dependem do teste empírico do `-1` e de `ontology/modalidades.yml`.
