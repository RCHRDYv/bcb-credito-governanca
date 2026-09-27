/**
 * PT: Todos os textos da interface, em português do Brasil.
 *
 *     Nenhum componente escreve texto fixo: ele pede o texto pela chave, com a
 *     função `t()` de `./index.js`. Quando o inglês entrar, ele vira um arquivo
 *     irmão deste, com as mesmas chaves, sem mexer em componente nenhum
 *     (ADR 0017, decisão 6; requisito RNF-13).
 *
 *     As chaves são planas e agrupadas pelo prefixo: `produto.`, `pagina.` e
 *     `inicio.`. "Crédito PJ" é o nome provisório do produto, até a decisão
 *     registrada em `dashboard/PRODUCT.md`.
 *
 * EN: Every interface text, in Brazilian Portuguese. Components never hold
 *     fixed text; they ask for it by key through `t()`. English will be a
 *     sibling file with the same keys. "Crédito PJ" is a provisional name.
 */

export const ptBR = Object.freeze({
  "produto.nome": "Crédito PJ",
  "pagina.titulo": "Crédito PJ: onde crescer em crédito para empresas",
  "pagina.pular-para-o-conteudo": "Pular para o conteúdo",
  "inicio.titulo": "Onde crescer em crédito para empresas, e onde o risco está piorando",
  "inicio.em-construcao": "As visões do dashboard estão em construção.",
});
