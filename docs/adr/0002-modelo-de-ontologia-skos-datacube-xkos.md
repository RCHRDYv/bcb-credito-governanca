# ADR 0002: Modelo de ontologia baseado em SKOS, RDF Data Cube e XKOS

**Status:** Aceito
**Data:** 2026-08-22

## Contexto

O projeto usa a palavra "ontologia" como elemento central da tese, mas até este ponto nenhum modelo formal havia sido fixado. Isso é um problema de duas naturezas.

**Problema de credibilidade:** um projeto que se propõe a demonstrar o efeito de ontologia sobre consumo de dado por IA precisa que o termo signifique algo verificável. Vocabulário informal em YAML, sem padrão por trás, é glossário. Chamar glossário de ontologia é exagero que um revisor técnico identifica.

**Problema técnico concreto:** o SCR tem uma quebra metodológica documentada entre a Versão 1 (descontinuada em junho de 2025) e a Versão 2. Expressar em prosa que "a modalidade X da V1 corresponde aproximadamente à Y da V2" não é consumível por máquina, e a pergunta mais difícil do experimento depende exatamente dessa correspondência.

O escopo real, levantado a partir do dado antes de qualquer leitura de normativo, é de 99 termos: 13 modalidades, 55 submodalidades, 13 portes, 8 segmentos, 6 indexadores, e 2 valores cada para cliente e origem.

## Decisão

Adotar três padrões complementares, cada um na camada onde tem encaixe direto.

### 1. SKOS como núcleo do vocabulário

O SKOS é o padrão W3C para tesauro, taxonomia e vocabulário controlado. O mapeamento com o SCR é direto:

| Conceito no SCR | Construto SKOS |
|---|---|
| Modalidade ou submodalidade | `skos:Concept` |
| O conjunto das modalidades | `skos:ConceptScheme` |
| Modalidade contém submodalidade | `skos:broader` e `skos:narrower` |
| Nome oficial como aparece no arquivo | `skos:prefLabel` |
| Definição extraída do normativo | `skos:definition` |
| O que entra e o que não entra na categoria | `skos:scopeNote` |
| Valor literal presente no dado | `skos:notation` |

### 2. RDF Data Cube para a estrutura multidimensional

O SCR é um cubo estatístico: dimensões (UF, modalidade, cliente, porte, tempo, segmento, origem, indexador) e medidas (carteira ativa, carteira vencida, inadimplência, ativo problemático, número de operações).

O vocabulário `qb:` do W3C existe para isso, e a própria especificação determina que `qb:codeList` aponte para um `skos:ConceptScheme`, o que faz as duas camadas se encaixarem sem adaptação.

Fator decisivo: **o RDF Data Cube é alinhado ao modelo de informação do SDMX**, o padrão internacional de intercâmbio de dado estatístico usado por bancos centrais e agências de estatística. Não é escolha exótica, é o caminho que o próprio domínio já trilha.

### 3. XKOS para correspondência entre versões da classificação

O XKOS é a extensão do SKOS para **classificações estatísticas**, e traz construtos para declarar correspondência entre versões diferentes de uma mesma classificação, com o tipo da correspondência (exata, aproximada, mais ampla, mais restrita).

É a resposta estrutural para a quebra V1 e V2. A pergunta sobre comparabilidade de série histórica deixa de depender de texto livre e passa a ser respondível a partir do modelo.

### 4. Autoria em YAML, emissão em RDF

A fonte da verdade é YAML versionado. Um passo do pipeline gera o RDF (Turtle) conforme os padrões acima.

O motivo é ergonômico e tem consequência prática na qualidade: escrever Turtle à mão para 99 conceitos é doloroso, e revisar Turtle em pull request é pior ainda. Se a revisão humana for penosa, ela não acontece, e a ontologia entra no ar sem verificação real.

Isso segue o mesmo princípio já adotado para `dim_modalidade`: uma fonte de verdade, todo o resto gerado.

## Alternativas descartadas

**OWL com inferência.** OWL serve para raciocínio automático sobre classes, propriedades e restrições. Esta taxonomia é hierárquica e finita, sem regra de inferência a derivar. Adotar OWL seria peso sem retorno, e reivindicar "ontologia OWL" sem usar as capacidades da linguagem seria exagero verificável.

**Glossário em prosa, sem padrão.** É o caminho de menor esforço e é o que a maioria dos projetos faz. Descartado porque não é consumível por máquina, não expressa hierarquia nem correspondência entre versões, e enfraquece a própria tese do projeto.

**Autoria direta em Turtle.** Descartado pelo motivo da seção anterior: torna a revisão humana inviável na prática, e revisão que não acontece é controle que não existe.

**Ontologia autoral, escrita a partir de conhecimento de domínio.** Descartado porque introduz circularidade: quem escreve a ontologia e o gabarito ao mesmo tempo não demonstrou nada. As definições são destiladas dos normativos oficiais do Banco Central, com citação da origem em cada uma.

## Consequências

**Positivas.** O termo "ontologia" passa a ter padrão W3C verificável por trás. A correspondência entre V1 e V2 vira dado estruturado em vez de nota de rodapé. O vocabulário fica interoperável com o ecossistema de dado estatístico ligado, incluindo SDMX. E a revisão humana continua viável, porque acontece sobre YAML.

**Negativas, e são reais.** Adiciona o trabalho do script de emissão e da validação do RDF. Exige mapear cada campo do YAML ao construto correto, o que é uma fonte de erro a mais. E ninguém no público-alvo imediato do projeto vai consumir o RDF na prática, então o retorno é de credibilidade e correção, não de uso.

**Aceitamos essas negativas** porque o custo é limitado e localizado num script, enquanto o ganho atinge a afirmação central do projeto.

## Nota sobre a origem do modelo

Este modelo **não foi extraído de um estudo sobre taxonomia de crédito**. Não há, até onde apuramos, trabalho publicado modelando a taxonomia do SCR. O modelo vem dos padrões do W3C e da prática estabelecida de publicação de dado estatístico ligado.

Registrar isso é deliberado: atribuir a decisão a uma referência inexistente seria pior do que assumir que ela é uma escolha de projeto fundamentada em padrão.
