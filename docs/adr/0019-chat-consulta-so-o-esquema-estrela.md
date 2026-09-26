# ADR 0019: O chat do dashboard consulta só o esquema estrela, e não é o experimento

**Status:** Aceito
**Data:** 2026-09-25, com a decisão sobre os documentos em 2026-09-26

## Contexto

O ADR 0012 desenhou um assistente de dados só, que servia ao mesmo tempo ao experimento, em lote, e às pessoas de negócio, dentro do dashboard. Na v0.3, a caixa de pergunta usaria esse assistente na condição D do experimento, com ontologia e documentos.

Em 2026-09-25, no desenho do dashboard, isso foi separado. O dashboard não é onde o experimento acontece, e juntar os dois cria dois problemas:

- **Risco de viés.** Se o chat tiver acesso ao gabarito ou às perguntas pré-registradas, ele responde bem justamente às perguntas que o experimento usa para medir, e a medida deixa de valer.
- **Amarração desnecessária.** O modelo do experimento é escolhido para testar uma hipótese. O modelo do chat precisa caber na cota de GPU do visitante ([ADR 0016](0016-site-estatico-no-github-pages-e-chat-no-zerogpu.md)) e responder rápido. São critérios diferentes.

## Decisões

### 1. O chat consulta só o esquema estrela

O dado do chat são as tabelas `dim_*` e `fct_*`, lidas do dataset público do Hugging Face (#45). É a mesma regra que o [ADR 0007](0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md) fixou para a IA do experimento, agora estendida ao chat, pelo mesmo motivo: os marts de apresentação já trazem as taxas e a matriz calculadas, e o chat que os lesse estaria repetindo a resposta pronta em vez de consultar o dado.

### 2. O contexto é só a ontologia

O modelo recebe a ontologia como contexto: definições, avisos, armadilhas e a fonte de cada conceito.

A busca nos documentos do BCB (RAG) fica de fora, decidido em 2026-09-26. Três motivos:
- o Space fica mais simples, sem índice de busca nem modelo de embeddings para manter;
- cada pergunta gasta menos segundos de GPU, e o visitante sem login tem 2 minutos por dia;
- a ontologia já traz as definições com a seção do documento de onde vieram.

### 3. O chat não vê nada do experimento

O chat não tem acesso ao gabarito, às perguntas pré-registradas nem aos resultados do experimento. Ele também não usa o assistente da #49 nem as condições do [ADR 0013](0013-experimento-2x2-ontologia-contra-documentos.md).

A regra é garantida por teste, e não só por convenção: o empacotamento do Space reprova qualquer arquivo de `evaluation/` e as perguntas de seleção do modelo da #74.

### 4. Não há respostas pré-validadas nem selo

Toda resposta é gerada na hora, a partir do dado. O chat não tem um conjunto de respostas prontas marcadas como confiáveis.

### 5. O modelo é escolhido separadamente, e pode ser mais leve

A #74 escolhe o modelo por três medidas: acerto, tempo de resposta e segundos de GPU por pergunta, num conjunto de perguntas próprio do dashboard, escrito do ponto de vista do executivo e sem reaproveitar os enunciados do gabarito. O modelo pode ser mais leve que os do experimento.

### 6. Toda resposta mostra de onde veio o número

A resposta traz o SQL que o modelo escreveu, o número tirado do dado pela execução desse SQL, e as ressalvas que a ontologia associa aos conceitos usados. Quando o dado não permite responder, o chat diz isso e diz o que faltaria.

O SQL passa por quatro travas antes de rodar: um comando só, só as tabelas do esquema estrela, limite de linhas e limite de tempo.

### 7. A acurácia do experimento não vale para o chat

O chat tem outro modelo e outro contexto, então o resultado do experimento não diz nada sobre ele. A tela avisa que o chat é um modelo aberto leve que pode errar, e que por isso mostra sempre o SQL.

## Alternativas descartadas

**O chat usar o assistente do experimento na condição D,** como previa a #51. Misturaria produto e experimento, e abriria caminho para o gabarito influenciar o chat.

**O chat ler também os marts de apresentação.** Acertaria mais as perguntas sobre a decisão, mas estaria lendo a resposta calculada, e não consultando o dado.

**Respostas pré-validadas para as perguntas da decisão, com selo de confiança.** Foram consideradas em 2026-09-25 e descartadas: o chat consulta o dado, e as conclusões prontas já estão nas telas.

**Ontologia e busca nos documentos juntas.** Responderia também perguntas sobre o texto da norma, citando o trecho. Descartada em 2026-09-26 pelos motivos da decisão 2.

## Consequências

**Positivas.**
- O experimento fica protegido: nada do que ele mede passa pelo chat.
- O chat pode usar o modelo que melhor cabe na cota de GPU do visitante.
- O Space fica pequeno: o esquema estrela, a ontologia e o código do chat.

**Negativas, e são reais.**
- **O chat não tem a acurácia medida pelo experimento.** A única medida dele é a da #74, com menos perguntas e menos rigor que o pré-registro.
- **Perguntas sobre o texto da norma ficam sem resposta citada.** O chat explica o conceito pela ontologia, mas não mostra o trecho do documento.
- **As perguntas sobre a decisão dependem de o modelo refazer a conta.** A matriz do ADR 0014 está nas telas, e o chat precisa chegar ao mesmo número pelo esquema estrela. Quando não chegar, o SQL mostrado permite ver onde errou.
