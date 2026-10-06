/**
 * PT: Os números da Tela 3 (#72), lidos dos três arquivos da previsão
 *     (#27, #98): `projecao_da_carteira.json`, `backtest_da_projecao.json` e
 *     `testes_da_projecao.json`.
 *
 *     O site não projeta nada: o script da previsão escolhe o campeão de
 *     cada série e grava a projeção, a faixa provável e o que cada modelo
 *     errou. Aqui só se separa a série escolhida, se recorta o período e se
 *     tiram médias dos testes recentes, que são os 4 últimos dos 16 testes
 *     do backtest, com previsões de fevereiro a julho de 2026.
 *
 * EN: Screen 3's numbers, read from the three forecast files. The site
 *     forecasts nothing: it picks the chosen series, cuts the period and
 *     averages the 4 recent backtest tests.
 */

/** @typedef {import("../../dados/carregar.js").ArquivoDeDados} ArquivoDeDados */
/** @typedef {import("../../dados/carregar.js").Ontologia} Ontologia */

/** @typedef {"pais" | "modalidade" | "uf"} TipoDeRecorte */

/** @typedef {"12-meses" | "desde-2024"} Periodo */

/**
 * @typedef {object} OpcaoDeSerie
 * @property {string} chave `tipo:recorte`, como `uf:SP` / `type:cut`
 * @property {TipoDeRecorte} tipo
 * @property {string} recorte `BR`, o código da modalidade ou a sigla da UF / cut code
 * @property {string} nome Como aparece na escolha / display name
 */

/**
 * @typedef {object} MesProjetado
 * @property {string} mes `aaaa-mm-dd`
 * @property {number} valor
 * @property {number} inferior Limite inferior da faixa provável / lower bound
 * @property {number} superior Limite superior da faixa provável / upper bound
 */

/**
 * @typedef {object} SerieDaProjecao
 * @property {string[]} meses Os meses realizados / actual months
 * @property {number[]} valores O realizado / actuals
 * @property {MesProjetado[]} projetados Os três meses projetados / projected months
 * @property {string} modelo O campeão da série, como no arquivo / the series' champion
 */

/**
 * @typedef {object} Teste
 * @property {string} data `aaaa-mm-dd`: o último mês que a projeção conhecia / last known month
 * @property {MesProjetado[]} projetados O que a projeção dizia / what the forecast said
 * @property {number[]} realizados O que aconteceu, na ordem dos meses / what happened
 */

/**
 * @typedef {object} ErroRecente
 * @property {string} modelo O campeão / champion
 * @property {number} erro Erro percentual médio do campeão nos testes recentes, em fração / champion's mean percentage error
 * @property {number} erroDeRepetir O mesmo erro de repetir o último mês / same error for the naive model
 * @property {number} acertos Casos em que o realizado caiu dentro da faixa / cases inside the band
 * @property {number} casos Testes recentes vezes horizontes / recent tests times horizons
 */

/** PT: a série que a tela abre / EN: the series the screen opens on */
export const SERIE_INICIAL = "pais:BR";

/** PT: o primeiro mês do recorte "Desde jan/2024" / EN: first month of the long period */
const INICIO_DA_SERIE = "2024-01-31";

/** PT: os meses do recorte "Últimos 12 meses" / EN: months in the short period */
const MESES_DO_RECORTE_CURTO = 12;

/** PT: o nome do modelo ingênuo no arquivo / EN: the naive model's file name */
export const REPETIR = "ingenuo";

/**
 * PT: As cinco séries em que o nível mudou dentro dos testes recentes, e o
 *     erro mede a mudança, e não o modelo (`docs/previsao.md`; #95).
 * EN: The five series whose level changed inside the recent tests.
 */
export const MUDARAM_DE_NIVEL = Object.freeze(
  new Set(["modalidade:07", "modalidade:10", "modalidade:11", "uf:AC", "uf:TO"]),
);

/**
 * PT: As séries fora da escolha. A modalidade 10 tem projeção e faixa
 *     negativas, e sai da tela até a previsão ser corrigida (decidido em
 *     2026-10-06; #101).
 * EN: Series left out of the choice until the forecast is fixed.
 */
export const FORA_DA_ESCOLHA = Object.freeze(new Set(["modalidade:10"]));

/** @type {readonly TipoDeRecorte[]} */
const ORDEM_DOS_TIPOS = Object.freeze(["pais", "modalidade", "uf"]);

/**
 * @template T
 * @param {ArquivoDeDados} arquivo
 * @param {string} nome
 * @returns {T[]}
 */
function coluna(arquivo, nome) {
  const valores = arquivo.colunas[nome];
  if (!valores) throw new Error(`Coluna fora do arquivo: ${arquivo.arquivo}, ${nome}`);
  return /** @type {T[]} */ (valores);
}

/**
 * PT: Os índices das linhas de uma série.
 * EN: Row indices of one series.
 *
 * @param {ArquivoDeDados} arquivo
 * @param {string} chave
 * @returns {number[]}
 */
function indicesDa(arquivo, chave) {
  const [tipo, recorte] = chave.split(":");
  const tipos = coluna(arquivo, "tipo_de_recorte");
  const recortes = coluna(arquivo, "recorte");
  return tipos.flatMap((t, i) => (t === tipo && recortes[i] === recorte ? [i] : []));
}

/**
 * PT: As séries que dá para escolher: o país, as modalidades, pelo código, e
 *     as 27 UFs, em ordem alfabética do nome, sem as que estão fora da
 *     escolha. Os nomes vêm da ontologia e da lista das UFs.
 * EN: The choosable series: country, modalities by code, states by name,
 *     minus the ones left out.
 *
 * @param {ArquivoDeDados} projecao
 * @param {(tipo: TipoDeRecorte, recorte: string) => string} nomear
 * @returns {OpcaoDeSerie[]}
 */
export function seriesDisponiveis(projecao, nomear) {
  const tipos = coluna(projecao, "tipo_de_recorte");
  const recortes = coluna(projecao, "recorte");
  /** @type {Map<string, OpcaoDeSerie>} */
  const unicas = new Map();
  tipos.forEach((tipo, i) => {
    const t = /** @type {TipoDeRecorte} */ (tipo);
    const recorte = String(recortes[i]);
    const chave = `${t}:${recorte}`;
    if (!unicas.has(chave))
      unicas.set(chave, { chave, tipo: t, recorte, nome: nomear(t, recorte) });
  });
  return [...unicas.values()]
    .filter((s) => !FORA_DA_ESCOLHA.has(s.chave))
    .sort(
      (a, b) =>
        ORDEM_DOS_TIPOS.indexOf(a.tipo) - ORDEM_DOS_TIPOS.indexOf(b.tipo) ||
        (a.tipo === "uf"
          ? a.nome.localeCompare(b.nome, "pt-BR")
          : a.recorte.localeCompare(b.recorte)),
    );
}

/**
 * PT: A série escolhida: o realizado, mês a mês, e os três meses projetados,
 *     com a faixa provável.
 * EN: The chosen series: actuals and the three projected months.
 *
 * @param {ArquivoDeDados} projecao
 * @param {string} chave
 * @returns {SerieDaProjecao}
 */
export function serieDaProjecao(projecao, chave) {
  const indices = indicesDa(projecao, chave);
  if (indices.length === 0) throw new Error(`Série fora do arquivo: ${chave}`);
  const datas = coluna(projecao, "data_base");
  const realizado = coluna(projecao, "realizado");
  const projetado = coluna(projecao, "projecao");
  const inferior = coluna(projecao, "limite_inferior");
  const superior = coluna(projecao, "limite_superior");
  const modelos = coluna(projecao, "modelo");
  const ordenados = [...indices].sort((a, b) => String(datas[a]).localeCompare(String(datas[b])));
  const passados = ordenados.filter((i) => realizado[i] !== null);
  const futuros = ordenados.filter((i) => projetado[i] !== null);
  return {
    meses: passados.map((i) => String(datas[i])),
    valores: passados.map((i) => Number(realizado[i])),
    projetados: futuros.map((i) => ({
      mes: String(datas[i]),
      valor: Number(projetado[i]),
      inferior: Number(inferior[i]),
      superior: Number(superior[i]),
    })),
    modelo: String(modelos[indices[0]]),
  };
}

/**
 * PT: O recorte do período: os últimos 12 meses realizados, ou todos, desde
 *     jan/2024. A projeção não muda.
 * EN: The period cut: last 12 actual months, or all since Jan 2024.
 *
 * @param {SerieDaProjecao} serie
 * @param {Periodo} periodo
 * @returns {SerieDaProjecao}
 */
export function recortar(serie, periodo) {
  const inicio =
    periodo === "12-meses"
      ? Math.max(0, serie.meses.length - MESES_DO_RECORTE_CURTO)
      : Math.max(0, serie.meses.indexOf(INICIO_DA_SERIE));
  return { ...serie, meses: serie.meses.slice(inicio), valores: serie.valores.slice(inicio) };
}

/**
 * PT: Os testes recentes da série, do mais antigo para o mais recente. Em
 *     cada um, o que o campeão previa para os três meses seguintes e o que
 *     aconteceu.
 * EN: The series' recent tests, oldest first: what the champion forecast
 *     for the next three months and what happened.
 *
 * @param {ArquivoDeDados} testes
 * @param {string} chave
 * @returns {Teste[]}
 */
export function testesDaSerie(testes, chave) {
  const datasDoTeste = coluna(testes, "data_do_teste");
  const horizontes = coluna(testes, "horizonte");
  const datas = coluna(testes, "data_base");
  const realizado = coluna(testes, "realizado");
  const projetado = coluna(testes, "projecao");
  const inferior = coluna(testes, "limite_inferior");
  const superior = coluna(testes, "limite_superior");
  /** @type {Map<string, number[]>} */
  const porTeste = new Map();
  for (const i of indicesDa(testes, chave)) {
    const data = String(datasDoTeste[i]);
    porTeste.set(data, [...(porTeste.get(data) ?? []), i]);
  }
  return [...porTeste.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([data, indices]) => {
      const ordenados = [...indices].sort((a, b) => Number(horizontes[a]) - Number(horizontes[b]));
      return {
        data,
        projetados: ordenados.map((i) => ({
          mes: String(datas[i]),
          valor: Number(projetado[i]),
          inferior: Number(inferior[i]),
          superior: Number(superior[i]),
        })),
        realizados: ordenados.map((i) => Number(realizado[i])),
      };
    });
}

/**
 * PT: O erro dos testes recentes. O do campeão e o de repetir o último mês
 *     são o erro percentual médio por horizonte, do backtest, na média dos
 *     três horizontes: cada caso pesa o mesmo, como no relatório. Os acertos
 *     da faixa contam os casos dos testes recentes.
 * EN: Recent-test error: the champion's and the naive model's mean
 *     percentage error averaged over horizons, and the band's hits.
 *
 * @param {ArquivoDeDados} backtest
 * @param {Teste[]} testes Os testes recentes da série / the series' recent tests
 * @param {string} chave
 * @returns {ErroRecente}
 */
export function erroRecente(backtest, testes, chave) {
  const modelos = coluna(backtest, "modelo");
  const escolhido = coluna(backtest, "escolhido");
  const mape = coluna(backtest, "mape");
  const indices = indicesDa(backtest, chave);
  const media = (/** @type {number[]} */ valores) =>
    valores.reduce((soma, v) => soma + v, 0) / valores.length;
  const doCampeao = indices.filter((i) => escolhido[i] === true);
  if (doCampeao.length === 0) throw new Error(`Série sem campeão no backtest: ${chave}`);
  const deRepetir = indices.filter((i) => modelos[i] === REPETIR);
  const casos = testes.flatMap((teste) =>
    teste.projetados.map((p, h) => ({ ...p, realizado: teste.realizados[h] })),
  );
  return {
    modelo: String(modelos[doCampeao[0]]),
    erro: media(doCampeao.map((i) => Number(mape[i]))),
    erroDeRepetir: media(deRepetir.map((i) => Number(mape[i]))),
    acertos: casos.filter((c) => c.inferior <= c.realizado && c.realizado <= c.superior).length,
    casos: casos.length,
  };
}

/**
 * PT: Os meses realizados que o gráfico do teste mostra: dois meses antes do
 *     primeiro teste até o último mês realizado. O eixo é o mesmo em todos
 *     os testes, e só a linha tracejada muda de lugar.
 * EN: Actual months shown in the backtest chart: two months before the
 *     first test through the last actual month, the same for every test.
 *
 * @param {SerieDaProjecao} serie
 * @param {Teste[]} testes
 * @returns {{ meses: string[], valores: number[] }}
 */
export function janelaDosTestes(serie, testes) {
  const primeiro = testes[0]?.data;
  const posicao = primeiro ? serie.meses.indexOf(primeiro) : -1;
  const inicio = Math.max(0, posicao - 2);
  return { meses: serie.meses.slice(inicio), valores: serie.valores.slice(inicio) };
}
