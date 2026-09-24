# ADR 0008: Os diagramas de arquitetura são código, escritos em Mermaid

**Status:** Aceito
**Data:** 2026-09-24

## Contexto

Até a camada gold, a arquitetura do projeto era explicada só em texto e tabela. O fluxo das camadas, o esquema estrela e o caminho da ontologia até o modelo já pediam desenho: são relações entre muitas peças, e um diagrama as mostra de uma vez.

A escolha da ferramenta não é neutra neste projeto. A tese dele é que documentação separada do que ela descreve deriva sem ninguém notar, e é por isso que as dimensões são geradas da ontologia e o CI reprova divergência. Um diagrama pode repetir exatamente esse erro: desenhado numa ferramenta visual e exportado como imagem, ele fica desatualizado no primeiro modelo novo, e nada avisa.

## Decisão

**Os diagramas de arquitetura são escritos em Mermaid, dentro dos próprios arquivos markdown do repositório.** O GitHub desenha os blocos ` ```mermaid ` sozinho, sem imagem exportada, sem conta em ferramenta externa e sem entidade fora do repositório.

| Diagrama | Onde mora |
|---|---|
| Fluxo medalhão, das fontes aos consumidores | `README.md`, seção "Arquitetura medalhão" |
| Esquema estrela | `docs/arquitetura.md` |
| Ontologia virando modelo | `docs/arquitetura.md` |
| Camadas de defesa | `docs/arquitetura.md` |

### Regras para os diagramas

- **Cita só o que existe.** Todo modelo, arquivo e verificação que aparece no diagrama existe no repositório. O que ainda é plano aparece tracejado e com o número da issue.
- **Mostra estrutura, e não números.** Contagem de linhas, de verificações e de conceitos muda a cada build ou a cada revisão da ontologia. Esses números moram no texto e nos testes, onde alguém os confere.
- **Anda junto com a mudança.** A PR que acrescenta, renomeia ou remove um modelo, um seed ou um passo do CI atualiza o diagrama que o mostra. A revisão da PR confere os dois, porque estão no mesmo diff.
- **Cada diagrama mora num lugar só.** Outros documentos apontam para ele por link, em vez de copiá-lo.

### O que fica fora

- **Linhagem modelo a modelo.** É papel do `dbt docs`, na v0.2. O grafo gerado é mais completo e não precisa de manutenção. Os diagramas mostram o que o `dbt docs` não mostra: a ingestão, a ontologia, o CI e quem consome cada camada.
- **Imagem de capa.** Uma peça visual para o README ou para divulgação pode ser feita em ferramenta visual, porque o acabamento vale mais que a manutenção, e ela quase não muda. Ela não substitui nenhum dos diagramas acima.

## Alternativas descartadas

**Figma, Excalidraw ou draw.io exportados como imagem.** Acabamento melhor, mas o arquivo-fonte fica fora do repositório ou vira binário, e a imagem deriva do código sem que a revisão da PR perceba. Repetiria o problema que o projeto existe para evitar.

**draw.io com o XML versionado.** Resolve o versionamento, mas o diff é ilegível, e na prática ninguém revisa a mudança do diagrama junto com a do modelo.

**PlantUML.** Também é texto, mas o GitHub não o desenha sozinho, e ele exigiria uma etapa de geração de imagem.

**Só o `dbt docs`.** Não mostra nada fora do dbt, e fica para a v0.2.

## Consequências

**Positivas.**
- O diagrama é revisado na mesma PR que muda o que ele mostra.
- Quem lê o repositório no GitHub vê o desenho sem instalar nada e sem sair da página.
- Nenhuma conta ou ferramenta externa entra no projeto.

**Negativas, e são reais.**
- **Pouco controle de layout.** O Mermaid posiciona os nós sozinho, e um diagrama grande fica ilegível. Por isso são quatro diagramas focados, e não um só.
- **Nada verifica o diagrama automaticamente.** Um nome errado dentro dele não quebra o CI. A garantia é a regra da PR, e não um teste.
- **O GitHub desenha com a versão do Mermaid que ele escolher.** Recurso muito novo da sintaxe pode não aparecer. Os diagramas usam só `flowchart` e `erDiagram`, que são estáveis.
