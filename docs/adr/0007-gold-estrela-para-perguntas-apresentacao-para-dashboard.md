# ADR 0007: A camada gold tem duas famílias, e a IA consulta só uma delas

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

A issue #15 mandava desenhar os marts a partir das perguntas pré-registradas. Em 2026-09-24 entrou uma segunda fonte de requisito: os marts também precisam servir ao dashboard da #17.

As duas necessidades puxam em direções opostas:

- **As perguntas** cruzam dimensões de formas que não dá para prever. A Q21 cruza segmento, modalidade e tempo; a Q33 cruza porte e cliente; a Q31 atravessa três modalidades. Elas pedem um fato no grão cheio, com as dimensões separadas.
- **O dashboard** é exportado como JSON estático, por decisão da especificação: credencial em JavaScript é pública, e dado mensal não precisa de tempo real. Ele pede tabelas pequenas, já agregadas no grão de cada tela, com as contas feitas.

E o experimento acrescenta uma terceira restrição, que é a mais importante: **aquilo que a IA consulta define o que o experimento mede.** Uma tabela que já traz a resposta pronta ajuda as duas condições por igual, e a diferença medida entre elas encolhe.

## Decisão

**A camada gold tem duas famílias, com papéis diferentes.**

| Família | Modelos | Serve | Quem consulta |
|---|---|---|---|
| Esquema estrela | `dim_tempo`, `dim_modalidade`, `dim_uf`, `dim_segmento`, `dim_porte`, `dim_cnae_ocupacao`, `fct_carteira`, `fct_carteira_v1` | As 41 perguntas | A IA, nas duas condições do experimento, e o gabarito |
| Apresentação | `mrt_carteira_mensal`, `mrt_reconciliacao_versoes`, `mrt_limites_do_dado` | As telas do dashboard | O dashboard e a camada de decisão |

### A IA consulta só o esquema estrela

Decidido com o Yuri em 2026-09-24. Os marts de apresentação trazem a taxa de inadimplência calculada, a distância entre as métricas de risco calculada e a diferença entre versões calculada. Se a IA os visse, várias armadilhas desapareceriam nas duas condições, e o experimento mediria a tabela, e não a documentação.

A matriz de cobertura (`evaluation/cobertura.yml`) sustenta a regra: pergunta só pode citar `dim_*` e `fct_*`, e o CI reprova o contrário.

### Linha de neutralidade nas dimensões

As dimensões trazem código, rótulo exato do dado, nome oficial, definição normativa e nível de confiança. **Não trazem coluna que responda uma pergunta específica.** Não existe marca de "é cartão de crédito", embora a ontologia saiba que o cartão está em cinco submodalidades de três modalidades: descobrir isso é o que a Q31 mede.

Pelo mesmo motivo, `dim_porte` e `dim_cnae_ocupacao` guardam o rótulo ambíguo como atributo, ao lado da chave desambiguada. Agrupar pelo rótulo reproduz a armadilha da coluna polimórfica, e ela precisa continuar possível.

### Os avisos vêm da ontologia, e ficam em coluna

A #15 pede que os avisos da ontologia apareçam no próprio mart, e não só na documentação. Duas formas:

- **`dim_tempo`** traz o regime de cada uma das três quebras datadas da série. As datas vêm de `ontology/dimensoes.yml`, pelo seed `ontologia_quebra`, e **nenhuma data de quebra está escrita no SQL**. O modelo sabe qual quebra procura pelo id, e a ontologia diz quando ela acontece.
- **`dim_uf`** traz a definição normativa da dimensão, que é onde está o aviso de que a UF é o domicílio da pessoa ou a sede da empresa, e não o local da operação.

A distinção entre aviso e resposta: aviso diz algo sobre a linha ou sobre o período, que o dado ou a norma afirmam. Resposta agrupa o dado do jeito que uma pergunta específica pede. O primeiro entra no mart; o segundo, não.

### O fato fica no grão cheio

`fct_carteira` tem as 9.687.811 linhas da V2, uma por recorte publicado. Qualquer agregação escolheria de antemão quais perguntas são fáceis. Ele leva só chaves e medidas; rótulos e avisos moram nas dimensões, e a consulta precisa fazer a junção, como num data warehouse de verdade.

### Um fato legado da V1, agregado

Encontrado na implementação. A Q39 pergunta se as duas versões fecham no total, e com a IA vendo só o esquema estrela ela não teria nenhum dado da V1. `fct_carteira_v1` resolve isso num grão agregado, mês, UF, modalidade da V1 e origem, com 18.344 linhas: a maior parte das 29,5 milhões de linhas da V1 vem de colunas que a V2 removeu e que nenhuma pergunta usa.

A medida de inadimplência mantém o nome da V1, `carteira_inadimplida_arrastada`. A definição é a mesma da V2, e a renomeação sem mudança de conceito é uma das armadilhas medidas.

### Taxa é razão de somas, calculada uma vez

Nos marts de apresentação, toda taxa é calculada uma vez, como razão das somas no grão. **Medido em jun/2026: a taxa de inadimplência de pessoa jurídica é 2,94%. A média das taxas dos recortes daria 7,68%, mais que o dobro.** Calcular no mart é o que impede o dashboard, e qualquer consulta derivada dele, de refazer a conta errada.

### Comparação no tempo é pela data

Uma combinação de cliente, UF e modalidade pode não ter linha em algum mês. Comparar com "seis linhas atrás" pularia meses sem avisar, então o mês de referência é encontrado pela data exata.

## Alternativas descartadas

**Uma família só, o esquema estrela, com o dashboard agregando na exportação.** A lógica de cada tela sairia do dbt e iria para o script de exportação, fora dos testes. O projeto passaria a ter duas verdades sem nada que as conferisse.

**Uma família só, agregada.** Quebraria as perguntas que cruzam dimensões, e o experimento perderia justamente as mais difíceis.

**A IA consultando toda a camada gold.** Mais parecido com o data warehouse de uma empresa, mas as duas condições acertariam mais pelo mesmo motivo, e a diferença medida encolheria. Descartada com o Yuri.

**Colunas de resposta nas dimensões**, como `eh_cartao_de_credito`. Desarmariam as armadilhas para as duas condições.

**Datas de quebra escritas no SQL.** Cada quebra nova, ou cada correção de data, exigiria editar modelo, e a ontologia deixaria de ser a fonte.

## Consequências

**Positivas.**
- O dashboard e a IA veem os mesmos números, e isso é provado por teste: `mrt_reconcilia_com_o_esquema_estrela` confere mês a mês cada total dos marts de apresentação contra os fatos.
- Todo número já publicado nos documentos do projeto é reproduzido pela camada gold.
- 30 das 41 perguntas já são respondíveis só com o SCR, e as outras 11 têm a issue que as bloqueia registrada.
- Os limites do dado deixam de ser texto fixo e viram medida mensal em `mrt_limites_do_dado`.

**Negativas, e são reais.**
- **Duas famílias para manter.** O teste de reconciliação entre elas é o que impede a divergência, e ele precisa acompanhar cada mart novo.
- **Armazenamento.** `fct_carteira` é tabela, e guarda uma segunda cópia do dado da V2 numa forma mais estreita.
- **A IA precisa fazer junção para chegar a qualquer rótulo.** É realista, e torna as perguntas mais difíceis nas duas condições. Faz parte do que se mede.
- **`fct_carteira_v1` depende de a V1 continuar publicada.** Se o BCB descontinuar a V1 de fato, as perguntas de comparação passam a ter só o histórico.
