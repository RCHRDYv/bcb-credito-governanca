# ADR 0013: O experimento vira 2x2, ontologia contra documentos, e passa a buscar uma descoberta

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

O experimento registrado compara duas condições: **A**, o modelo só com o esquema, e **B**, o esquema com a ontologia. O projeto se apresentava como **demonstração, e não descoberta**, porque o efeito de metadado sobre acerto de text-to-SQL já está na literatura (`docs/referencias.md`): no BIRD, por exemplo, 34,88% sem evidência de conhecimento externo contra 54,89% com ela.

O ADR 0012 separou o contexto em duas camadas independentes, a ontologia e os documentos do BCB recuperados por RAG. Em 2026-09-24, o Yuri decidiu duas coisas:

- os documentos entram como **novo teste**, e não como troca da condição B;
- o projeto passa a **buscar uma descoberta**, e não só replicar um efeito conhecido.

## Decisão

### Quatro condições, em desenho 2x2

| | Sem documentos | Com documentos (RAG) |
|---|---|---|
| **Sem ontologia** | **A:** só o esquema | **C:** só os documentos |
| **Com ontologia** | **B:** só a ontologia | **D:** ontologia e documentos |

**A e B não mudam.** Continuam exatamente como estão registradas. **C e D são extensão,** registrada com data anterior a qualquer execução do experimento.

### A pergunta que torna isto uma descoberta

Que metadado ajuda text-to-SQL já é sabido, e a comparação entre A e B continua sendo replicação. A pergunta nova é outra:

> **Vale o trabalho de curar uma ontologia, se os mesmos documentos de onde ela foi destilada podem ser recuperados em texto bruto?**

O corpus do RAG são exatamente os documentos que a ontologia cita (ADR 0012). Então B e C têm acesso ao mesmo conhecimento, e só a forma muda: curado e estruturado, ou cru e recuperado por busca. A resposta serve a qualquer empresa que decide entre montar uma camada semântica e jogar documentos num RAG.

O projeto não afirma que a pergunta é inédita na literatura. Afirma que é a pergunta que decide entre duas arquiteturas reais, e que aqui ela é medida com pré-registro, em dado regulatório brasileiro e em português.

### Hipóteses, com direção

Registradas nesta data, e formalizadas em `evaluation/hipoteses.yml` antes de qualquer execução (issue própria, na v0.2):

- **H1:** B acerta mais que A. A ontologia ajuda. É o que já estava registrado.
- **H2:** C acerta mais que A. Os documentos ajudam.
- **H3:** B acerta mais que C nas perguntas de tipo `valor`. Conhecimento estruturado vence texto bruto quando a resposta é SQL.
- **H4:** D acerta pelo menos tanto quanto o melhor entre B e C. As duas camadas se somam, ou pelo menos não atrapalham.
- **H5:** a vantagem da ontologia sobre os documentos é maior nas perguntas de `valor_com_ressalva` e `abstencao` do que nas de `valor`. Saber o que o dado não permite é onde a curadoria mais pesa.

Cada hipótese pode ser refutada, e um resultado contra ela é publicado do mesmo jeito.

### Estatística

- **Teste Q de Cochran** para as quatro condições pareadas, por pergunta.
- **McNemar entre pares de condições,** com correção de Holm para as comparações múltiplas.
- **Tamanho de efeito sempre,** com intervalo.
- **Análise separada por tipo de acerto:** valor, valor com ressalva e abstenção.
- **Dois modelos de níveis diferentes,** como a especificação já exige.
- **Cada pergunta roda várias vezes por condição,** e a variância é reportada.

### O limite, declarado junto

A v0.1 tem 38 perguntas respondíveis. É pouco para uma descoberta forte. A conclusão vale para este domínio e para este conjunto, com tamanho de efeito, e não como lei geral. Isso é dito junto do resultado, e não escondido.

## Alternativas descartadas

**Manter só A e B, como demonstração.** Replicaria um efeito conhecido e deixaria de fora a pergunta que tem valor de decisão.

**Trocar a condição B pela combinação de ontologia e documentos.** Mudaria uma condição já registrada, o que fere o pré-registro, e misturaria os dois efeitos.

**Três condições, sem a D.** Deixaria sem resposta se as duas camadas se somam ou atrapalham, que é a pergunta prática de quem vai montar a ferramenta.

## Consequências

**Positivas.**
- O projeto passa a ter uma pergunta de pesquisa, com hipóteses de direção declarada.
- O 2x2 separa o efeito da ontologia, o efeito dos documentos e a interação entre os dois.

**Negativas, e são reais.**
- **O dobro de condições,** e portanto o dobro de execuções e de custo de avaliação.
- **Mais comparações pedem correção,** e isso reduz o poder de cada teste, com uma amostra que já é pequena.
- **O RAG precisa de corpus e de índice próprios** (ADR 0012), que ainda não existem.
- **`docs/referencias.md` e o README mudam de posicionamento:** a parte de replicação continua explicada, e a pergunta nova passa a vir primeiro.
