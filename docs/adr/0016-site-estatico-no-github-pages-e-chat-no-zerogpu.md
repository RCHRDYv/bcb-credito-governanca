# ADR 0016: O site do dashboard é estático no GitHub Pages, e o chat roda num Space ZeroGPU

**Status:** Aceito
**Data:** 2026-09-25

## Contexto

O ADR 0012 colocou o dashboard, o esquema estrela e a caixa de pergunta numa aplicação só, no plano gratuito de CPU do Hugging Face Spaces. Em 2026-09-25, ao começar o desenho do dashboard, a documentação do Hugging Face dizia outra coisa:

> "Static Spaces are free for everyone. Gradio and Docker Spaces run on compute and require a paid plan to create: PRO for personal accounts, Team or Enterprise for organizations. Free personal accounts in good standing can still host up to 2 Gradio Spaces running on ZeroGPU."
> ([Spaces Overview](https://huggingface.co/docs/hub/spaces-overview), acessado em 2026-09-25)

Ou seja, o Space de CPU grátis em que a decisão 5 do ADR 0012 se apoiava deixou de existir para contas novas. Continuam valendo as duas restrições do projeto: **custo zero** e **nenhuma credencial exposta**.

Na mesma data o dashboard passou a ser tratado como projeto próprio, com quadro separado no GitHub, e o desenho da aplicação pública foi refeito do zero.

## Decisões

### 1. O site é estático, no GitHub Pages

O dashboard é um site de HTML, CSS e JavaScript, sem servidor próprio, publicado no GitHub Pages por um workflow do Actions.

- **Por que o Pages:** é grátis, não dorme quando ninguém acessa, e o link sai direto do README, no mesmo lugar onde está o código.
- **Limites do plano,** conferidos na [documentação do Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) em 2026-09-25: site publicado de até 1 GB e banda flexível de 100 GB por mês. Cada arquivo do repositório tem ainda o limite geral do GitHub, de 100 MiB. Os marts de apresentação exportados ficam muito abaixo disso.
- **Uso permitido:** o Pages não pode servir negócio comercial nem SaaS. Um portfólio público não se enquadra nisso.
- **CSP por `<meta>`:** o Pages não deixa configurar cabeçalho HTTP próprio, então a política de segurança de conteúdo vai no HTML.

### 2. O chat roda num Space ZeroGPU, com Gradio

O ZeroGPU é a única forma de Space com computação que continua grátis para conta pessoal. As regras, conferidas na [documentação do ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) em 2026-09-25:

| Item | Regra |
|---|---|
| Quem pode hospedar | Conta grátis com e-mail verificado e mais de 30 dias, até 2 Spaces |
| GPU | Metade de uma NVIDIA RTX Pro 6000 Blackwell, com 48 GB de VRAM |
| Cota diária de GPU | 2 minutos para visitante sem login, 5 minutos para conta grátis |
| De quem é a cota | De quem faz a pergunta, e não do dono do Space |
| O que roda | Só Gradio, com PyTorch |

Duas consequências práticas:
- **A cota é do visitante.** Um visitante que faz muitas perguntas gasta a cota dele, e não esgota o dia para os outros.
- **O modelo roda com `transformers`.** llama.cpp e Ollama, previstos no ADR 0012 para o experimento local, não rodam no ZeroGPU.

### 3. O SQL roda no Space, sobre o esquema estrela publicado num dataset

O Space executa o SQL gerado pelo modelo com DuckDB em Python, sobre o esquema estrela em Parquet publicado num dataset público do Hugging Face (#45).

O navegador não carrega o DuckDB-WASM, que tem 33,5 MB, e a consulta roda longe da página. O que o chat consulta, e o que ele não pode ver, está no [ADR 0019](0019-chat-consulta-so-o-esquema-estrela.md).

### 4. As telas não dependem do chat

Com o Space dormindo, com a cota do visitante esgotada ou com erro, o dashboard continua inteiro, porque as telas leem arquivos que estão no próprio site. O chat mostra em que estado está, em vez de falhar calado.

### 5. Nenhuma credencial pessoal, de nenhum serviço, fica exposta

Decidido em 2026-09-25. Amplia o [ADR 0001](0001-credenciais-e-dado-bruto-fora-do-repositorio.md), que tratava das credenciais do Databricks: a regra passa a valer para qualquer serviço, inclusive GitHub e Hugging Face.

| Peça | Como publica | Segredo guardado |
|---|---|---|
| Site no Pages | Workflow do Actions, com o token efêmero que o GitHub gera para cada execução | Nenhum. O token do workflow não é credencial pessoal e expira sozinho |
| Dataset e Space no Hugging Face | Da máquina local, com token de escopo fino, restrito a esses dois repositórios | Nenhum no repositório, no CI ou no Space. O token fica só na máquina local |
| Página publicada | Não chama nenhum serviço que exija chave | Nenhum |
| Space do chat | Lê um dataset público | Nenhum |

### 6. O esquema estrela vai para o Hugging Face antes do previsto

A publicação do esquema estrela num dataset do Hugging Face estava na #52, na v0.4. Como o chat depende dela, ela sobe para a #45, na v0.2. A #52 fica só com os resultados do experimento.

## Alternativas descartadas

**Space de CPU no Hugging Face,** como previa o ADR 0012. Passou a exigir plano pago.

**Worker da Cloudflare chamando o Workers AI.** Rodaria modelos abertos maiores sem nenhuma chave guardada, com cota grátis de 10 mil "neurônios" por dia ([preços do Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/), acessado em 2026-09-25). Descartado em 2026-09-26 por dois motivos: com o ZeroGPU, o dataset e o chat ficam na mesma plataforma, sem abrir conta num serviço novo, e o Space e o dataset aparecem juntos no perfil do Hugging Face, que serve de vitrine do projeto.

**Modelo rodando no navegador do visitante,** com WebLLM. Não precisa de conta nenhuma, mas o visitante baixaria de 1,6 a 2,5 GB de modelo, só funciona em computador com WebGPU, e um modelo desse tamanho acerta bem menos SQL.

**Cloudflare Pages, Vercel ou Netlify para o site.** Todos servem site estático e aceitam cabeçalho HTTP próprio, mas tiram o link do ecossistema do GitHub. O plano grátis da Vercel, além disso, é só para uso não comercial ([limites da Vercel](https://vercel.com/docs/limits), acessado em 2026-09-25).

**API paga de modelo.** Fere o custo zero.

## Consequências

**Positivas.**
- Custo zero, e nenhuma credencial pessoal em lugar nenhum.
- O site nunca dorme, e o link está no mesmo lugar que o código.
- A GPU do ZeroGPU permite um modelo melhor que o de CPU previsto no ADR 0012.
- Um visitante não esgota o chat para os outros.

**Negativas, e são reais.**
- **O Space dorme sem uso,** e a primeira pergunta depois disso espera o modelo carregar.
- **A cota do visitante limita quantas perguntas ele faz por dia.** Quanto mais leve o modelo, mais perguntas cabem, e isso pesa na escolha da #74.
- **O Hugging Face já mudou a regra uma vez em 2026, e pode mudar de novo.** É por isso que as telas não dependem do chat.
- **A CSP por `<meta>` não cobre tudo:** a diretiva `frame-ancestors`, que impede outro site de embutir a página, só funciona por cabeçalho.
- **O site e o chat ficam em plataformas diferentes,** e a página precisa chamar o Space por outra origem.
