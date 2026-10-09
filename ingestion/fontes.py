"""
PT: Configuração única da ingestão: quais arquivos buscar, onde guardar e
    para onde enviar. Todo módulo da ingestão lê daqui, para que mudar o
    recorte temporal ou o destino seja uma alteração em um lugar só.
EN: Single source of ingestion configuration: which files to fetch, where
    to store them and where to send them. Every ingestion module reads from
    here, so changing the time scope or the destination is a one-place edit.
"""

from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

# -----------------------------------------------------------------------------
# PT: Fontes oficiais
# EN: Official sources
# -----------------------------------------------------------------------------

URL_BASE = "https://www.bcb.gov.br/pda/desig"

# PT: Recorte do projeto: 2024 em diante (docs/cadeia-normativa.md, decisão 1.3).
# EN: Project scope: 2024 onwards (docs/cadeia-normativa.md, decision 1.3).
ANOS = (2024, 2025, 2026)


@dataclass(frozen=True)
class Fonte:
    """
    PT: Uma versão do SCR.data. A V2 é a fonte principal; a V1 é a fonte
        legada, mantida para reconciliação e para a conformação do ADR 0003.
    EN: One SCR.data version. V2 is the main source; V1 is the legacy
        source, kept for reconciliation and for the ADR 0003 conformance.
    """

    versao: str  # PT: "v1" ou "v2" / EN: "v1" or "v2"
    prefixo: str  # PT: prefixo do arquivo no portal / EN: file prefix on the portal
    colunas_esperadas: int  # PT: contrato mínimo de esquema / EN: minimal schema contract

    def nome_zip(self, ano: int) -> str:
        return f"{self.prefixo}_{ano}.zip"

    def url(self, ano: int) -> str:
        return f"{URL_BASE}/{self.nome_zip(ano)}"


FONTES = (
    Fonte(versao="v2", prefixo="scrdata", colunas_esperadas=24),
    Fonte(versao="v1", prefixo="planilha", colunas_esperadas=23),
)

# -----------------------------------------------------------------------------
# PT: Caminhos locais. data/ inteiro está no .gitignore.
# EN: Local paths. The whole data/ folder is gitignored.
# -----------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ / "data" / "raw"
DIR_LANDING = RAIZ / "data" / "landing"

# PT: O manifesto é versionado: não contém dado, só a identidade de cada
#     arquivo baixado. O histórico do git mostra quando o BCB republicou.
# EN: The manifest is versioned: it holds no data, only the identity of each
#     downloaded file. Git history shows when the BCB republished one.
MANIFESTO = RAIZ / "ingestion" / "manifesto.json"

# -----------------------------------------------------------------------------
# PT: Destino no Databricks. Nenhum identificador do workspace fica no código:
#     o perfil vem do ~/.databrickscfg e o warehouse é descoberto em tempo de
#     execução, ou informado por variável de ambiente.
# EN: Databricks destination. No workspace identifier lives in the code: the
#     profile comes from ~/.databrickscfg and the warehouse is discovered at
#     runtime, or given through an environment variable.
# -----------------------------------------------------------------------------

PERFIL = os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID")  # PT: opcional / EN: optional
CATALOGO = "workspace"
SCHEMA = "bcb_scr"
VOLUME = "raw"
CAMINHO_VOLUME = f"/Volumes/{CATALOGO}/{SCHEMA}/{VOLUME}"

# =============================================================================
# PT: Fontes externas por UF (issue #25). Ficam separadas do SCR porque têm
#     outra periodicidade, outro formato e outro servidor, e ganham manifesto
#     próprio dentro do mesmo arquivo (chaves "cnpj" e "ibge").
# EN: External sources by state (issue #25). Kept apart from the SCR because
#     they differ in periodicity, format and server, and get their own
#     sections in the same manifest file ("cnpj" and "ibge" keys).
# =============================================================================

# -----------------------------------------------------------------------------
# PT: CNPJ aberto da Receita Federal. O compartilhamento é público, e o
#     endereço abaixo é o link exatamente como a Receita o publica na página
#     de dados abertos, o mesmo registrado em ontology/fontes_externas.yml.
#     O WebDAV do servidor identifica o compartilhamento pelo último trecho
#     desse link, que por isso é extraído dele, e não escrito à parte: não é
#     credencial, e guardá-lo isolado o faria parecer uma.
#     A listagem por WebDAV dá nome, tamanho e data de cada arquivo sem
#     baixar nada.
# EN: Receita Federal's open CNPJ data. The share is public, and the address
#     below is the link exactly as Receita publishes it. The server's WebDAV
#     identifies the share by the link's last segment, which is therefore
#     derived from it rather than written separately: it is not a credential,
#     and storing it alone would make it look like one.
# -----------------------------------------------------------------------------

RECEITA_LINK_PUBLICO = "https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9"
RECEITA_COMPARTILHAMENTO = RECEITA_LINK_PUBLICO.rsplit("/", 1)[-1]
RECEITA_WEBDAV = "https://arquivos.receitafederal.gov.br/public.php/webdav"

# PT: Espelho usado para o download, decidido em 2026-09-24 (ADR
#     0009). O servidor da Receita entregava cerca de 4 MB/s com quedas e
#     depois saiu do ar; o espelho da Casa dos Dados entrega os mesmos
#     arquivos por CDN, sem login, a cerca de 100 MB/s. A Receita continua
#     sendo a fonte declarada: o espelho é só o meio de transporte, e 613 MB
#     baixados do servidor oficial antes da queda são idênticos byte a byte
#     aos do espelho. As pastas do espelho têm o nome do dia da extração
#     (2026-09-14), e não do mês.
# EN: Mirror used for downloading, decided on 2026-09-24. Receita's
#     server delivered about 4 MB/s with drops and then went offline; the
#     Casa dos Dados mirror serves the same files through a CDN, with no
#     login, at about 100 MB/s. Receita remains the declared source: the
#     mirror is only transport, and 613 MB downloaded from the official
#     server before it went down are byte-identical to the mirror's.
ESPELHO_CNPJ = "https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos"

# PT: O retrato mais recente alimenta o modelo: dele se reconstrói o estoque
#     de empresas ativas em cada fim de mês (ADR 0009). Os dois retratos
#     antigos existem só para medir o erro dessa reconstrução, e por isso
#     trazem apenas a tabela de estabelecimentos.
# EN: The latest snapshot feeds the model: the stock of active companies at
#     each month end is rebuilt from it (ADR 0009). The two older snapshots
#     exist only to measure that reconstruction's error, so they bring only
#     the establishments table.
RETRATO_DO_MODELO = "2026-09"
RETRATOS_DE_VALIDACAO = ("2024-06", "2025-06")

DIR_RAW_CNPJ = DIR_RAW / "cnpj"
DIR_LANDING_CNPJ = DIR_LANDING / "cnpj"


@dataclass(frozen=True)
class TabelaCnpj:
    """
    PT: Uma tabela do CNPJ aberto. Os arquivos não têm cabeçalho, então os
        nomes das colunas vêm do leiaute oficial da Receita
        (https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf), na
        ordem em que aparecem nele.
    EN: One table of the open CNPJ data. Files have no header, so column
        names come from Receita's official layout, in its order.
    """

    nome: str  # PT: nome da tabela bronze / EN: bronze table name
    prefixo: str  # PT: prefixo do ZIP no servidor / EN: ZIP prefix on the server
    colunas: tuple[str, ...]
    so_no_retrato_do_modelo: bool  # PT: fora dos retratos de validação / EN: not in validation snapshots

    def retratos(self) -> tuple[str, ...]:
        if self.so_no_retrato_do_modelo:
            return (RETRATO_DO_MODELO,)
        return (*RETRATOS_DE_VALIDACAO, RETRATO_DO_MODELO)

    def e_desta_tabela(self, arquivo: str) -> bool:
        """
        PT: "Estabelecimentos0.zip" é desta tabela; "Empresas0.zip" não. O
            prefixo precisa ser seguido de dígito ou de ".zip", porque
            "Socios" e "Simples" começam com a mesma letra.
        EN: The prefix must be followed by a digit or ".zip".
        """
        resto = arquivo.removeprefix(self.prefixo)
        return resto != arquivo and (resto == ".zip" or resto[:1].isdigit())


TABELAS_CNPJ = (
    TabelaCnpj(
        nome="estabelecimentos",
        prefixo="Estabelecimentos",
        colunas=(
            "cnpj_basico", "cnpj_ordem", "cnpj_dv", "identificador_matriz_filial",
            "nome_fantasia", "situacao_cadastral", "data_situacao_cadastral",
            "motivo_situacao_cadastral", "nome_cidade_exterior", "pais",
            "data_inicio_atividade", "cnae_fiscal_principal", "cnae_fiscal_secundaria",
            "tipo_logradouro", "logradouro", "numero", "complemento", "bairro", "cep",
            "uf", "municipio", "ddd_1", "telefone_1", "ddd_2", "telefone_2",
            "ddd_fax", "fax", "correio_eletronico", "situacao_especial",
            "data_situacao_especial",
        ),
        so_no_retrato_do_modelo=False,
    ),
    TabelaCnpj(
        nome="empresas",
        prefixo="Empresas",
        colunas=(
            "cnpj_basico", "razao_social", "natureza_juridica", "qualificacao_responsavel",
            "capital_social", "porte_empresa", "ente_federativo_responsavel",
        ),
        so_no_retrato_do_modelo=True,
    ),
    TabelaCnpj(
        nome="simples",
        prefixo="Simples",
        colunas=(
            "cnpj_basico", "opcao_simples", "data_opcao_simples", "data_exclusao_simples",
            "opcao_mei", "data_opcao_mei", "data_exclusao_mei",
        ),
        so_no_retrato_do_modelo=True,
    ),
    TabelaCnpj(
        nome="naturezas",
        prefixo="Naturezas",
        colunas=("codigo", "descricao"),
        so_no_retrato_do_modelo=True,
    ),
    TabelaCnpj(
        nome="cnaes",
        prefixo="Cnaes",
        colunas=("codigo", "descricao"),
        so_no_retrato_do_modelo=True,
    ),
)
# PT: Sócios não é ingerido: nenhuma pergunta usa, e é a tabela com nome e
#     CPF parcial de pessoas. Municípios, Países, Motivos e Qualificações
#     também ficam fora, porque nada no projeto os consulta.
# EN: Partners are not ingested: no question uses them, and it is the table
#     with people's names and partial CPFs. Municipalities, countries,
#     reasons and qualifications stay out too, since nothing queries them.

# -----------------------------------------------------------------------------
# PT: Tabelas do SIDRA, do IBGE, todas por UF (n3/all). Definições em
#     ontology/fontes_externas.yml.
#     - 6579: população residente estimada (issue #25), anual, com data de
#       referência em 1º de julho;
#     - 6472 e 6474: rendimento médio e massa de rendimento do trabalho da
#       PNAD Contínua (issue #38, ADR 0025), trimestrais. Só o valor nominal
#       e o coeficiente de variação. O valor real é deflacionado a preços do
#       último trimestre, e o IBGE refaz a série inteira a cada divulgação.
#
#     A PNAD começa no trimestre anterior ao primeiro mês do SCR: cada mês
#     usa o último trimestre encerrado até a data-base, e jan e fev do
#     primeiro ano usam o 4º trimestre do ano anterior. Março já usa o 1º,
#     que termina na própria data-base. O fim é o último trimestre
#     publicado. Histórico anterior não é baixado.
# EN: SIDRA tables from IBGE, all by state. 6579 is estimated population,
#     yearly; 6472 and 6474 are average and total labor income from the
#     quarterly PNAD Contínua, nominal value and coefficient of variation
#     only (the real value is re-deflated to the latest quarter on every
#     release). The PNAD starts one quarter before the first SCR month, since
#     each month uses the last quarter ended by its reference date; it ends at
#     the latest published quarter.
# -----------------------------------------------------------------------------

SIDRA_URL = "https://apisidra.ibge.gov.br/values/t/{tabela}/n3/all/v/{variaveis}/p/{periodos}"
SIDRA_PERIODOS = "https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos"
PRIMEIRO_TRIMESTRE_PNAD = f"{ANOS[0] - 1}04"
DIR_RAW_IBGE = DIR_RAW / "ibge"
DIR_LANDING_IBGE = DIR_LANDING / "ibge"


@dataclass(frozen=True)
class TabelaSidra:
    """
    PT: Uma tabela do SIDRA. O nome vira a pasta, o arquivo e o sufixo da
        tabela bronze (bronze_ibge_<nome>). O período é o rótulo da terceira
        dimensão no SIDRA: "Ano" ou "Trimestre".
    EN: One SIDRA table. The name becomes folder, file and bronze table
        suffix. The period is SIDRA's label for the third dimension.
    """

    nome: str
    tabela: int
    variaveis: tuple[str, ...]
    periodo: str

    @property
    def arquivo(self) -> str:
        return f"{self.nome}_{self.tabela}.json"


TABELAS_SIDRA = (
    TabelaSidra(nome="populacao", tabela=6579, variaveis=("9324",), periodo="Ano"),
    TabelaSidra(nome="rendimento", tabela=6472, variaveis=("5929", "5937"), periodo="Trimestre"),
    TabelaSidra(nome="massa", tabela=6474, variaveis=("6288", "6289"), periodo="Trimestre"),
)

# -----------------------------------------------------------------------------
# PT: Malha das UFs, pela API de malhas v3 do IBGE (issue #67). Só o site do
#     dashboard a usa, no mapa por UF, e ela não vai ao Databricks.
#     - qualidade=minima: a versão mais leve que o IBGE publica, já
#       generalizada por ele, com as fronteiras das vizinhas coincidindo;
#     - intrarregiao=UF: o país dividido nas 27 UFs, numa resposta só;
#     - periodo=2022: a malha territorial de 2022. Sem o parâmetro, a API
#       devolve exatamente a mesma resposta (sha256 conferido em
#       2026-10-01), mas o período escrito na URL não muda de sentido no dia
#       em que o IBGE publicar outra malha. Na mesma data, os períodos de
#       2023 a 2025 devolviam erro 500.
# EN: State mesh from IBGE's mesh API v3. Only the dashboard site uses it, and
#     it does not go to Databricks. Minimum quality, split by state, period
#     pinned to 2022, which is what the API serves by default (same sha256 on
#     2026-10-01); 2023 to 2025 returned HTTP 500 that day.
# -----------------------------------------------------------------------------

MALHA_UFS = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo%2Bjson&qualidade=minima&intrarregiao=UF&periodo=2022"
)

# -----------------------------------------------------------------------------
# PT: Séries do SGS, o Sistema Gerenciador de Séries Temporais do BCB (issue
#     #37). A API é pública, sem login, e devolve JSON. A consulta sempre
#     leva data final, a da extração: sem ela, séries como a meta da Selic
#     voltam com datas no futuro, porque o SGS repete a meta vigente até a
#     próxima reunião do Copom (medido em 2026-09-24: a série ia até
#     04/11/2026). Definições em ontology/fontes_externas.yml.
# EN: SGS series, the BCB time series system. Public API, no login, JSON.
#     Queries always carry an end date, the extraction date: without it,
#     series like the Selic target come back with future dates, because SGS
#     repeats the current target until the next Copom meeting.
# -----------------------------------------------------------------------------

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={inicio}&dataFinal={fim}"


@dataclass(frozen=True)
class SerieSgs:
    """
    PT: Uma série do SGS. O nome vira o nome do arquivo e da pasta; o código
        é o do próprio SGS.
    EN: One SGS series. The name becomes file and folder name; the code is
        SGS's own.
    """

    nome: str
    codigo: int
    descricao: str


# PT: A meta, e não a taxa efetiva: a Q25 registrada em inglês pede a "Selic
#     policy rate". Escolha registrada na issue #37 e no ADR 0010.
# EN: The target, not the effective rate: Q25 asks for the "Selic policy rate".
SERIES_SGS = (
    SerieSgs(nome="selic_meta", codigo=432, descricao="Meta da taxa Selic definida pelo Copom, % a.a., diária"),
)

# PT: Mesmo recorte do SCR (decisão 1.3 de docs/cadeia-normativa.md).
# EN: Same scope as the SCR.
SGS_DATA_INICIAL = f"01/01/{ANOS[0]}"
DIR_RAW_SGS = DIR_RAW / "sgs"
DIR_LANDING_SGS = DIR_LANDING / "sgs"

# -----------------------------------------------------------------------------
# PT: PIX por município, recurso TransacoesPixPorMunicipio do serviço OData
#     Pix_DadosAbertos do BCB (issue #36). Público, sem login. O parâmetro
#     DataBase é "a partir de", e não o mês exato, e o mês corrente vem
#     incompleto: a consulta pede do início do recorte até o último mês
#     fechado, por filtro, e pagina, porque passa de 100 mil linhas.
# EN: PIX by municipality, from BCB's Pix_DadosAbertos OData service. The
#     DataBase parameter means "from", not the exact month, and the current
#     month is partial: the query asks from the scope start to the last
#     closed month through a filter, and pages through the result.
# -----------------------------------------------------------------------------

PIX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/"
    "TransacoesPixPorMunicipio(DataBase=@DataBase)"
)
PIX_INICIO = f"{ANOS[0]}01"  # PT: AAAAMM / EN: YYYYMM
PIX_PAGINA = 10_000  # PT: limite por consulta, acima dos 5.572 municípios de um mês / EN: per-query limit
DIR_RAW_PIX = DIR_RAW / "pix"
DIR_LANDING_PIX = DIR_LANDING / "pix"

# -----------------------------------------------------------------------------
# PT: Corpus do RAG (issue #46, ADR 0028). São os documentos que a ontologia
#     cita, na lista congelada do pré-registro (evaluation/hipoteses.yml,
#     rag.corpus): metodologias V1 e V2 do SCR.data, leiaute e instruções do
#     documento 3040, os normativos de docs/leitura-normativos.md e
#     docs/cadeia-normativa.md, o leiaute do CNPJ e a documentação das APIs
#     do PIX e do SGS. Nada além disso entra sem errata no registro.
#
#     O tipo diz como o arquivo é lido em rag/extrair.py:
#     - pdf: texto página a página;
#     - xls: o leiaute do 3040, aba por aba;
#     - normativo: JSON da API de normativos do BCB, com o texto vigente em
#       HTML no campo Texto. As normas anteriores a 2020 têm o tipo
#       "Resolução", sem "CMN" (medido em 2026-10-07);
#     - olinda: página de documentação do Olinda, que traz a especificação
#       do serviço em JSON dentro do script da página;
#     - ckan: package_show do portal de dados abertos, com a descrição da
#       série e de cada recurso.
#
#     Os apelidos são as formas com que os campos fonte da ontologia citam o
#     documento. O gerador do gabarito de recuperação os usa para ligar cada
#     conceito ao seu documento.
#
# EN: RAG corpus (issue #46, ADR 0028): the documents the ontology cites, as
#     listed in the frozen pre-registration. The type says how each file is
#     read in rag/extrair.py. The aliases are how the ontology's fonte fields
#     cite each document; the retrieval answer-key generator uses them.
# -----------------------------------------------------------------------------

NORMATIVOS_URL = "https://www.bcb.gov.br/api/conteudo/app/normativos/exibenormativo?p1={tipo}&p2={numero}"
SCR_DOC3040_URL = "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040"


@dataclass(frozen=True)
class DocumentoDoCorpus:
    """
    PT: Um documento do corpus do RAG. O id vira o nome do arquivo bruto e o
        campo documento de cada trecho.
    EN: One RAG corpus document. The id becomes the raw file name and the
        document field of each chunk.
    """

    id: str
    titulo: str
    tipo: str  # PT: pdf, xls, normativo, olinda ou ckan / EN: pdf, xls, normativo, olinda or ckan
    url: str
    apelidos: tuple[str, ...] = ()

    @property
    def extensao(self) -> str:
        return {"pdf": ".pdf", "xls": ".xls", "olinda": ".html"}.get(self.tipo, ".json")

    @property
    def arquivo(self) -> str:
        return f"{self.id}{self.extensao}"


def _normativo(id_: str, tipo: str, numero: int, titulo: str, apelidos: tuple[str, ...]) -> DocumentoDoCorpus:
    """PT: normativo pela API do BCB / EN: regulation through the BCB API"""
    url = NORMATIVOS_URL.format(tipo=urllib.parse.quote(tipo), numero=numero)
    return DocumentoDoCorpus(id=id_, titulo=titulo, tipo="normativo", url=url, apelidos=apelidos)


DOCUMENTOS_DO_CORPUS = (
    DocumentoDoCorpus(
        id="metodologia_v1",
        titulo="Metodologia do SCR.data, Versão 1",
        tipo="pdf",
        url="https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf",
        apelidos=("Metodologia V1", "Metodologia do SCR.data, Versão 1"),
    ),
    DocumentoDoCorpus(
        id="metodologia_v2",
        titulo="Metodologia do SCR.data, Versão 2",
        tipo="pdf",
        url=f"{URL_BASE}/metodologia_versao2.pdf",
        apelidos=("Metodologia V2", "Metodologia do SCR.data, Versão 2"),
    ),
    DocumentoDoCorpus(
        id="instrucoes_3040",
        titulo="Instruções de Preenchimento do Documento 3040",
        tipo="pdf",
        url=f"{SCR_DOC3040_URL}/SCR_InstrucoesDePreenchimento_Doc3040.pdf",
        apelidos=("Instruções 3040", "Instruções"),
    ),
    DocumentoDoCorpus(
        id="leiaute_3040",
        titulo="Leiaute do Documento 3040",
        tipo="xls",
        url=f"{SCR_DOC3040_URL}/SCR3040_Leiaute.xls",
        apelidos=("Leiaute do Documento 3040", "Leiaute do documento 3040", "Anexo 3", "HistoricoAtualizacoes"),
    ),
    _normativo("res_4553", "Resolução", 4553, "Resolução nº 4.553, de 30/1/2017", ("Resolução nº 4.553/2017", "Res. 4.553")),
    _normativo("res_cmn_4966", "Resolução CMN", 4966, "Resolução CMN nº 4.966, de 25/11/2021", ("Resolução CMN 4.966",)),
    _normativo("res_cmn_5254", "Resolução CMN", 5254, "Resolução CMN nº 5.254", ("Resolução CMN 5.254", "CMN 5.254")),
    _normativo("res_cmn_5255", "Resolução CMN", 5255, "Resolução CMN nº 5.255", ("Resolução CMN 5.255",)),
    _normativo("res_bcb_512", "Resolução BCB", 512, "Resolução BCB nº 512", ("Resolução BCB 512",)),
    _normativo("in_bcb_414", "Instrução Normativa BCB", 414, "Instrução Normativa BCB nº 414", ("IN BCB 414",)),
    _normativo("in_bcb_531", "Instrução Normativa BCB", 531, "Instrução Normativa BCB nº 531", ("IN BCB 531",)),
    _normativo("in_bcb_627", "Instrução Normativa BCB", 627, "Instrução Normativa BCB nº 627", ("IN BCB 627",)),
    _normativo("in_bcb_659", "Instrução Normativa BCB", 659, "Instrução Normativa BCB nº 659", ("IN BCB 659",)),
    _normativo("carta_circular_3617", "Carta Circular", 3617, "Carta Circular nº 3.617", ("Carta Circular 3.617",)),
    _normativo("carta_circular_3773", "Carta Circular", 3773, "Carta Circular nº 3.773", ("Carta Circular 3.773",)),
    _normativo("carta_circular_3806", "Carta Circular", 3806, "Carta Circular nº 3.806", ("Carta Circular 3.806",)),
    _normativo("carta_circular_3817", "Carta Circular", 3817, "Carta Circular nº 3.817", ("Carta Circular 3.817",)),
    DocumentoDoCorpus(
        id="cnpj_leiaute",
        titulo="Metadados dos dados abertos do CNPJ (Receita Federal)",
        tipo="pdf",
        url="https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf",
        apelidos=("Leiaute dos dados abertos do CNPJ",),
    ),
    DocumentoDoCorpus(
        id="pix_api",
        titulo="Documentação do serviço Pix_DadosAbertos (Olinda)",
        tipo="olinda",
        url="https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/documentacao",
        apelidos=("Documentação da API Pix_DadosAbertos", "Documentação da API do PIX"),
    ),
    DocumentoDoCorpus(
        id="sgs_api",
        titulo="Taxa de juros - Meta Selic definida pelo Copom (portal de dados abertos, SGS 432)",
        tipo="ckan",
        url=(
            "https://dadosabertos.bcb.gov.br/api/3/action/package_show"
            "?id=432-taxa-de-juros---meta-selic-definida-pelo-copom"
        ),
        apelidos=("SGS do BCB", "API do SGS"),
    ),
)
DIR_RAW_DOCUMENTOS = DIR_RAW / "documentos"
