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

# PT: Espelho usado para o download, decidido com o Yuri em 2026-09-24 (ADR
#     0009). O servidor da Receita entregava cerca de 4 MB/s com quedas e
#     depois saiu do ar; o espelho da Casa dos Dados entrega os mesmos
#     arquivos por CDN, sem login, a cerca de 100 MB/s. A Receita continua
#     sendo a fonte declarada: o espelho é só o meio de transporte, e 613 MB
#     baixados do servidor oficial antes da queda são idênticos byte a byte
#     aos do espelho. As pastas do espelho têm o nome do dia da extração
#     (2026-09-14), e não do mês.
# EN: Mirror used for downloading, decided with Yuri on 2026-09-24. Receita's
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
# PT: População residente estimada por UF, IBGE, tabela 6579 do SIDRA. A
#     estimativa tem data de referência em 1º de julho de cada ano.
#     n3/all = todas as UFs; v/9324 = população residente estimada.
# EN: Estimated resident population by state, IBGE, SIDRA table 6579.
#     Reference date is July 1st of each year.
# -----------------------------------------------------------------------------

SIDRA_POPULACAO = "https://apisidra.ibge.gov.br/values/t/6579/n3/all/v/9324/p/{anos}"
ANOS_POPULACAO = ANOS
DIR_RAW_IBGE = DIR_RAW / "ibge"
DIR_LANDING_IBGE = DIR_LANDING / "ibge"

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
