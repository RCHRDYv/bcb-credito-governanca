---
name: nova-fonte-externa
description: Caminho para trazer uma fonte externa nova ao bcb-credito-governanca (IBGE, SGS, OData do BCB e afins), da ingestão até a ontologia e o gabarito, no padrão da #25 e da #38. Use ao planejar ou construir uma fonte nova.
---

# Fonte externa nova

Referências: a #25 (população, CNPJ), a #37 (Selic), a #36 (PIX) e a #38 (renda da PNAD), com os ADRs 0009, 0010, 0011 e 0025.

## Antes de codar (plano, com decisões do Yuri)
- Confirme na API da fonte: tabela, variáveis, unidade, periodicidade, nível territorial e último período publicado. Para o IBGE, use `https://servicodados.ibge.gov.br/api/v3/agregados/<tabela>/metadados` e `/periodos`.
- Leve ao Yuri as escolhas que mudam a resposta:
  - o conceito exato da variável;
  - nominal ou real;
  - como alinhar o período da fonte ao mês do SCR;
  - a janela, que parte dos dados que o projeto já tem, sem histórico desnecessário.
- Registre as decisões num comentário da issue antes do código.

## Ingestão
1. **Constantes** em `ingestion/fontes.py`. Uma tabela do SIDRA é uma linha em `TABELAS_SIDRA`.
2. **Download e Parquet só texto** com colunas de linhagem (`arquivo_origem`, `sha256_arquivo`):
   - para o SIDRA, use `ingestion/baixar_ibge.py`;
   - para outra fonte, faça um `ingestion/baixar_<fonte>.py` no mesmo molde.
   - A validação reprova estrutura diferente, linha faltando e valor sem número.
3. **Manifesto:** a seção da fonte em `ingestion/manifesto.json`, com `tabela`, `url`, `bytes`, `sha256`, `linhas` e os períodos. Uma nova rodada sem mudança não pode alterar o manifesto.
4. **Bronze:** o bloco em `ingestion/bronze.sql`, com `CREATE OR REPLACE TABLE ... read_files` e um COMMENT descritivo.
5. **Verificação:** confira se `checar_fontes_externas` em `ingestion/verificar_bronze.py` lê a tabela nova.
6. Rode `enviar_volume`, `criar_bronze` e `verificar_bronze`.

## dbt
- Declare a fonte no source `externas` de `dbt/models/staging/_fontes.yml`.
- `stg_*` fica 1:1 com o bronze, só com nomes e tipos, com `accepted_values` no código da variável.
- O fato `fct_*` fica no grão da fonte, com a UF pelo `codigo_ibge` da seed `ontologia_dimensao`. Documente em `_marts.yml`, com relationships para `dim_uf`.
- Escreva um teste singular de completude em `dbt/tests/`: todas as UFs, períodos contíguos e todo mês do SCR com valor.

## Ontologia e documentação
- Em `ontology/fontes_externas.yml`, registre:
  - a fonte, com publicador, endereço, periodicidade e data de referência;
  - o conceito, com notation, definição, scopeNote e armadilha;
  - os avisos.
- Rode `validar_fontes_externas` e regere as seeds.
- Escreva um ADR com as decisões, atualize `docs/especificacao.md`, `docs/arquitetura.md` (diagrama do esquema estrela) e o `README.md`.

## Gabarito, se a fonte destrava perguntas
- Escreva os SQL em `evaluation/gabarito/` no padrão do ADR 0015, expondo o período do denominador numa coluna.
- `gabarito.yml` e `cobertura.yml` mudam juntos. Depois, rode `gerar_gabarito` e os validadores.

## QA independente
- Confira a soma das UFs contra o total do Brasil quando a medida é aditiva.
- Num script em `scripts/analises/`, refaça o fato e as respostas por outro caminho.
