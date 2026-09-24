# Arquitetura em diagramas

Três diagramas que complementam o fluxo medalhão do [README](../README.md#arquitetura-medalhão). Eles são escritos em Mermaid e ficam neste arquivo, e não em imagem exportada, para que a PR que muda um modelo mude também o desenho. As regras estão no [ADR 0008](adr/0008-diagramas-como-codigo-em-mermaid.md).

No diagrama da ontologia, a seta pontilhada liga uma verificação àquilo que ela confere.

## Esquema estrela

É o que a IA consulta nas duas condições do experimento ([ADR 0007](adr/0007-gold-estrela-para-perguntas-apresentacao-para-dashboard.md)). O fato tem só chaves e medidas. Rótulos, definições e avisos moram nas dimensões, e qualquer consulta que queira um nome precisa fazer a junção.

`fct_carteira` guarda o grão cheio da V2. `fct_carteira_v1` é o fato legado, agregado, e existe para que as perguntas de comparação entre versões tenham dado da V1. Ele se liga só ao tempo e à UF, porque a taxonomia da V1 não é a das dimensões.

```mermaid
erDiagram
    dim_tempo ||--o{ fct_carteira : data_base
    dim_uf ||--o{ fct_carteira : uf
    dim_segmento ||--o{ fct_carteira : segmento
    dim_modalidade ||--o{ fct_carteira : codigo_submodalidade
    dim_porte ||--o{ fct_carteira : porte_desambiguado
    dim_cnae_ocupacao ||--o{ fct_carteira : cnae_ocupacao_desambiguado
    dim_tempo ||--o{ fct_carteira_v1 : data_base
    dim_uf ||--o{ fct_carteira_v1 : uf

    fct_carteira {
        date data_base FK
        string uf FK
        string segmento FK
        string codigo_submodalidade FK
        string porte_desambiguado FK
        string cnae_ocupacao_desambiguado FK
        string cliente
        string origem
        string indexador
        bigint numero_de_operacoes "nulo quando o BCB suprime"
        boolean contagem_suprimida
        decimal carteira_a_vencer
        decimal carteira_vencida
        decimal carteira_ativa
        decimal carteira_inadimplencia
        decimal ativo_problematico
        string modalidade_v1_efetiva
        string origem_da_modalidade_v1 "oficial ou inferida_pelo_projeto"
    }

    fct_carteira_v1 {
        date data_base FK
        string uf FK
        string cliente
        string modalidade_v1
        string origem
        decimal carteira_ativa
        decimal carteira_inadimplida_arrastada "mesmo conceito, com o nome da V1"
        decimal ativo_problematico
    }

    dim_tempo {
        date data_base PK
        int ano
        int mes
        string ano_mes
        boolean eh_mes_mais_recente
        string criterio_ativo_problematico "vem da ontologia"
        boolean ativo_problematico_comparavel_com_mes_anterior
        string granularidade_da_publicacao "vem da ontologia"
        string divergencia_entre_versoes "vem da ontologia"
        string quebras_no_mes
    }

    dim_modalidade {
        string codigo_submodalidade PK
        string codigo_modalidade
        string modalidade "rótulo exato do dado"
        string submodalidade "rótulo exato do dado"
        string nome_oficial_submodalidade
        string definicao
        string confianca
        string fonte
    }

    dim_porte {
        string porte_desambiguado PK
        string cliente
        string porte "rótulo ambíguo, mantido de propósito"
        string taxonomia
        string aviso
    }

    dim_cnae_ocupacao {
        string cnae_ocupacao_desambiguado PK
        string cliente
        string cnae_ocupacao "rótulo ambíguo, mantido de propósito"
        string taxonomia
        string aviso
    }

    dim_uf {
        string uf PK
        string definicao_da_uf "domicílio ou sede, não o local da operação"
    }

    dim_segmento {
        string segmento PK
        string definicao_do_segmento
    }
```

## Ontologia virando modelo

As dimensões não são escritas à mão no dbt. Elas são geradas dos arquivos da ontologia, e duas verificações seguram a coerência: o CI regera os seeds e reprova se o resultado diferir do versionado, e os validadores conferem, contra o bronze, que a ontologia descreve exatamente o dado que existe.

A correspondência entre as versões segue o mesmo desenho, com uma diferença: a fonte é a planilha oficial do BCB, que é dado bruto e fica fora do repositório ([ADR 0001](adr/0001-credenciais-e-dado-bruto-fora-do-repositorio.md) e [ADR 0003](adr/0003-conformacao-de-taxonomia-entre-versoes.md)). O que se versiona é o seed gerado dela.

```mermaid
flowchart LR
    subgraph fonte["Fonte, versionada"]
        mod["ontology/modalidades.yml"]
        dim["ontology/dimensoes.yml"]
    end

    planilha["Planilha de equivalência do BCB<br/>fora do repositório"]

    subgraph geradores["Geradores"]
        g1["scripts/gerar_seeds_da_ontologia.py"]
        g2["scripts/gerar_seed_correspondencia.py"]
    end

    subgraph seeds["Seeds do dbt, versionados"]
        s_mod["ontologia_modalidade"]
        s_dim["ontologia_dimensao"]
        s_que["ontologia_quebra"]
        s_cor["correspondencia_modalidade_v2_v1"]
    end

    subgraph modelo["Modelos do dbt"]
        i_mod["int_dim_modalidade"]
        i_pc["int_dim_porte<br/>int_dim_cnae_ocupacao"]
        conf["int_scr_v2_conformado"]
        d_mod["dim_modalidade"]
        d_pc["dim_porte<br/>dim_cnae_ocupacao"]
        d_us["dim_uf<br/>dim_segmento"]
        d_tem["dim_tempo"]
    end

    mod --> g1
    dim --> g1
    g1 --> s_mod & s_dim & s_que
    planilha --> g2 --> s_cor

    s_mod --> i_mod --> d_mod
    i_mod --> conf
    s_dim --> i_pc --> d_pc
    s_dim --> d_us
    s_que --> d_tem
    s_cor --> conf

    ci{{"CI: regera os seeds<br/>e reprova diferença"}}
    val{{"Validadores contra o bronze:<br/>todo valor do dado tem conceito,<br/>todo conceito ocorre no dado"}}
    ci -.-> s_mod & s_dim & s_que
    val -.-> mod & dim
```

`ontology/metricas.yml` não aparece no diagrama porque nenhum gerador o lê ainda. As definições das medidas estão nele, e os modelos o citam nos comentários.

## Camadas de defesa

A `main` é protegida, e toda mudança passa por branch e PR. Três camadas conferem o trabalho, e cada uma pega o que a anterior não alcança. As duas primeiras não usam credencial nenhuma. A terceira precisa do dado, e por isso roda só na máquina de quem tem acesso ao Databricks, autenticada por OAuth, sem credencial guardada em segredo do GitHub.

```mermaid
flowchart TB
    subgraph local["1. Na máquina, antes do commit: pre-commit"]
        direction LR
        h_seg["gitleaks<br/>detect-private-key"]
        h_dado["bloqueia-dado-bruto<br/>check-added-large-files"]
        h_ramo["no-commit-to-branch"]
        h_form["check-yaml, check-json,<br/>fim de linha e espaços"]
    end

    subgraph ci["2. No servidor, em toda PR: CI"]
        direction LR
        c_seg["Qualidade e segurança:<br/>os mesmos hooks"]
        c_est["Estrutura da ontologia<br/>e do seed de correspondência"]
        c_seed["Seeds da ontologia em dia"]
        c_per["Pré-registro das perguntas"]
        c_cob["Cobertura da camada gold"]
        c_dbt["dbt parse, sem credencial"]
    end

    subgraph dados["3. Na máquina com acesso ao Databricks, por OAuth"]
        direction LR
        d_bro["ingestion.verificar_bronze:<br/>bronze igual ao publicado"]
        d_val["Validadores contra o bronze:<br/>ontologia e correspondência"]
        d_dbt["dbt build:<br/>modelos e testes"]
        d_qa["QA independente:<br/>scripts/analises/"]
    end

    local --> ci --> revisao["Revisão da PR"] --> main[("main")]
    dados --> revisao
```

A terceira camada não roda no CI por decisão, e não por falta de configuração. O projeto não guarda credencial do Databricks em segredo do GitHub ([ADR 0001](adr/0001-credenciais-e-dado-bruto-fora-do-repositorio.md)). A orquestração pelo Asset Bundle, publicada da máquina local, está na #22.
