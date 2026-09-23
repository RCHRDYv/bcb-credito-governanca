# ADR 0006: O staging corrige a forma e preserva o conteúdo

**Status:** Aceito
**Data:** 2026-09-23

## Contexto

O bronze guarda o SCR.data como publicado, com todas as colunas como texto (ADR 0004). Assim ele é auditável e inútil: nenhuma soma funciona, nenhuma comparação de data funciona, e a contagem de operações traz dois sentinelas diferentes conforme a versão.

Entre o bronze e os marts existe uma decisão que não é técnica: **o que o staging tem direito de mudar.** Ela precisa ser explícita porque o projeto inteiro depende dela. O experimento compara respostas de uma IA sobre esta base, e a camada semântica é o objeto de estudo. Se o staging corrigir o dado por conta própria, o experimento passa a medir as correções do autor, não a qualidade da documentação. Se não corrigir nada, a pergunta mais simples já sai errada.

O formato foi medido antes desta decisão, sobre as 9.687.811 linhas da V2 e as 29.471.540 da V1, em 2026-09-23:

| Fato medido | V2 | V1 |
|---|---|---|
| Separador de milhar nas medidas | nenhum | nenhum |
| Casas decimais | 2 | 2 |
| Maior número de dígitos inteiros | 12 | 12 |
| Valores não numéricos nas medidas | nenhum | nenhum |
| Espaço à direita | `submodalidade`, 720.339 linhas | `porte`, todas as linhas |
| Sentinela em `numero_de_operacoes` | `-1`, 2.590.482 linhas | `<= 15`, 22.120.146 linhas |
| Marcador `-` de ausência | nenhum | 4 colunas, 46,5 milhões de ocorrências |
| Grão declarado é único | sim | sim |

## Decisão

**Um modelo por versão, `stg_scr_v2` e `stg_scr_v1`, materializado como view, com relação um para um com o bronze.** O staging corrige a forma e preserva o conteúdo.

### O que o staging muda

1. **Trim nos rótulos.** Não é cosmético: é o que torna o valor igual ao `rotulo_no_dado` da ontologia, que é a chave de junção.
2. **Vírgula decimal para `decimal(18,2)`.** Decimal, e não ponto flutuante, porque são valores contábeis e os testes de identidade comparam somas por igualdade exata.
3. **Data-base para data.**
4. **Sentinela de contagem para nulo,** com a supressão preservada em coluna própria.
5. **Marcador `-` da V1 para nulo,** nas quatro colunas em que ele significa ausência.

### O que o staging não muda

Nenhum agregado é calculado, nenhuma linha é filtrada, nenhum rótulo é traduzido e nenhuma taxonomia é conformada. A conformação entre V1 e V2 é da camada intermediária, com o seed de correspondência e o ADR 0003. O staging preserva até a imperfeição do rótulo, porque é ela que casa com o dado.

### O tratamento do sentinela é assimétrico de propósito

As duas versões suprimem a contagem de operações, e só uma diz como:

- **V1:** a regra está publicada. "Casos em que o número de operações seja inferior ou igual a 15, a informação divulgada será '<= 15'" (Metodologia V1, item 4.l). Por isso o modelo da V1 carrega `contagem_min` e `contagem_max`, que valem 1 e 15 nas linhas suprimidas e o próprio valor nas demais.
- **V2:** não existe regra publicada, e está medido que o critério **não** é o número de operações: a V2 divulga contagens de 1 a 15 abertamente, e um mesmo recorte alterna entre `-1` e contagens de até 514.490 operações (`docs/sentinela-numero-de-operacoes.md`). Por isso o modelo da V2 não tem intervalo nenhum. Inventar um limite superior para ficar simétrico seria transformar lacuna em número.

A consequência atravessa as camadas de cima: somar `numero_de_operacoes` em um grupo com linhas suprimidas dá **limite inferior, não total**, e isso vale para 26,7% das linhas e 6,71% da carteira da V2.

### Um marcador, dois significados

Na V1, `cnae_subclasse` usa o mesmo `-` para duas coisas: nas 4.244.485 linhas de pessoa física a coluna não se aplica, e em 989.730 linhas de pessoa jurídica a subclasse foi suprimida pela regra documentada dos 5 CNPJs. Converter os dois para nulo perderia a distinção, então o modelo da V1 registra `subclasse_suprimida`, que separa os casos usando `cliente`. É o inverso do caso da V2: aqui a supressão tem critério publicado e merece ser nomeada.

### A exceção do arquivo aparece como aviso, não como filtro

A identidade `carteira_ativa = carteira_a_vencer + carteira_vencida` é a definição da própria métrica. Ela falha em **uma** linha das 9.687.811 da V2, e falha na origem: o arquivo publica, em dez/2024, uma carteira a vencer maior que a carteira ativa.

O teste `stg_scr_v2_carteira_ativa` avisa com uma linha e falha o build com duas. A alternativa era excluir a exceção por chave, e ela foi descartada: a exclusão esconderia a mudança exatamente no dia em que ela acontecesse. Um aviso que aparece em toda execução é desconfortável de propósito.

## Alternativas descartadas

**Tipar no bronze.** Descartada no ADR 0004: inferência de tipo erra em silêncio neste arquivo.

**Tratar o `-1` como zero ou como 15.** Zero afirma que não há operação, e 15 afirma um limite que está medido como falso. As duas trocam lacuna por número plausível, que é o erro que este projeto existe para expor.

**Guardar o sentinela como está e deixar o tratamento para quem consulta.** É o estado atual de quem usa o SCR.data sem documentação, e o próprio motivo do projeto.

**Conformar V1 e V2 no staging.** Juntaria duas decisões de natureza diferente no mesmo lugar: converter tipo é mecânico e verificável, mapear taxonomia é interpretação com ambiguidade declarada (ADR 0003). Separadas, dá para testar cada uma.

**Materializar como tabela.** Duplicaria 12,7 GB no Free Edition sem ganho: o staging não tem agregação, e o custo real de varredura fica nos marts, que são tabelas.

## Consequências

**Positivas.**
- Todo número já publicado nos documentos do projeto foi reproduzido pelo staging: jun/2026 com carteira ativa de R$ 7.637,1 bi, inadimplência de 4,63% e ativo problemático de 8,21%; jan/2025 da V1 com R$ 6.395,6 bi, R$ 214,4 bi e R$ 452,6 bi; "Outros créditos" com 10,42% da carteira e a submodalidade 1304 com R$ 594,7 bi.
- A igualdade com o bronze é testada, não presumida: linhas, meses, linhas suprimidas por dois caminhos independentes e a soma das medidas de carteira.
- As armadilhas viraram coluna: `contagem_suprimida`, `contagem_min`, `contagem_max` e `subclasse_suprimida` são legíveis por quem consulta e por uma IA, em vez de ficarem só em prosa.
- Custo de armazenamento zero, porque são views.

**Negativas, e são reais.**
- **View recalcula a cada consulta.** Aceitável enquanto o staging não tem agregação, e é o que torna os marts materializados obrigatórios.
- **`decimal(18,2)` é escolha fixa.** Folgada para 12 dígitos inteiros, mas se o BCB mudar a escala publicada, o cast falha. Falhar é o comportamento desejado.
- **O build termina com um aviso permanente,** enquanto o BCB não corrigir a linha de dez/2024.
- **O staging da V1 não é comparável com o da V2.** Por decisão: quem precisar comparar passa pela camada intermediária.
