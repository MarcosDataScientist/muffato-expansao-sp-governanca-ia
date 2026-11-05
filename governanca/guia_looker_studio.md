# 📊 Guia de Conexão Direta e Painel Executivo no Looker Studio
**Projeto GCP:** `projeto-governanca` | **Dataset:** `muffato_gold`  
**Organização Beneficiária:** Grupo Muffato (Expansão no Estado de São Paulo — 645 Municípios)

---

## 🔗 Links de Criação Rápida (1 Clique via Linking API do Looker Studio)

Clique nos links abaixo logado na conta `beregula.marcos@gmail.com` para abrir o **Looker Studio** já conectado diretamente às tabelas da camada **Gold** do seu BigQuery:

1. 🎯 **[Abrir Mapa Direto dos 139 Candidatos de Expansão (`vw_mapa_candidatos_expansao`)](https://lookerstudio.google.com/reporting/create?c.reportName=Muffato_SP_Mapa_Candidatos_e_Formatos_Loja&ds.connector=bigQuery&ds.projectId=projeto-governanca&ds.type=TABLE&ds.datasetId=muffato_gold&ds.tableId=vw_mapa_candidatos_expansao)** *(Contém apenas os 139 municípios candidatos prioritários calibrados pela concorrência da Receita Federal, com geometria nativa `geo_ponto_municipio`!)*
2. 🗺️ **[Abrir Painel Completo dos 645 Municípios & IAV (`vw_painel_executivo_expansao`)](https://lookerstudio.google.com/reporting/create?c.reportName=Muffato_SP_Painel_Executivo_Expansao_IAV&ds.connector=bigQuery&ds.projectId=projeto-governanca&ds.type=TABLE&ds.datasetId=muffato_gold&ds.tableId=vw_painel_executivo_expansao)**
3. 🧪 **[Conectar Tabela de Experimentos MLOps (`mlops_experiments_log`)](https://lookerstudio.google.com/reporting/create?c.reportName=Muffato_MLOps_Experiment_Tracking&ds.connector=bigQuery&ds.projectId=projeto-governanca&ds.type=TABLE&ds.datasetId=muffato_gold&ds.tableId=mlops_experiments_log)**
4. 🛡️ **[Conectar Monitoramento de Drift & Governança (`mlops_monitoring_drift`)](https://lookerstudio.google.com/reporting/create?c.reportName=Muffato_MLOps_Monitoramento_Drift&ds.connector=bigQuery&ds.projectId=projeto-governanca&ds.type=TABLE&ds.datasetId=muffato_gold&ds.tableId=mlops_monitoring_drift)**

---

## 🎨 Estrutura Recomendada das 2 Páginas do Dashboard

### Página 1: Visão Executiva de Expansão & Alocação de CAPEX (Etapa 3)
Fonte de Dados: `projeto-governanca.muffato_gold.vw_painel_executivo_expansao`

* **Filtros de Controle (Topo):**
  * `ds_formato_recomendado` (*Max Atacadista*, *Super Muffato / Gourmet*, *Muffato Go / Proximidade*)
  * `ds_saturacao_concorrencial` (*Oceano Azul*, *Baixa Saturação*, *Concorrência Moderada*, *Alta Saturação*)
  * `ds_cluster_socioeconomico` (*C1 a C4*)
  * `nm_regiao_intermediaria` (*São Paulo, Campinas, Sorocaba, Ribeirão Preto, etc.*)
* **4 Cartões de KPI (Visão Geral):**
  1. **Municípios Mapeados:** `COUNT(cd_municipio)` (645 municípios)
  2. **Praças Prioritárias (Expansão Imediata):** Filtro `ds_formato_recomendado != 'Monitoramento / Polo Satelite'` (139 praças)
  3. **Score IAV Médio das Praças Alvo:** `AVG(vl_score_iav)`
  4. **Concorrentes Diretos Mapeados (CNPJ):** `SUM(qt_concorrentes_diretos_total)` (20.549 lojas concorrentes em SP)
* **Mapa Geográfico Interativo (Google Maps — Mapa de Bolhas):**
  * **Location (Localização):** `nm_municipio` (ou `ds_localizacao_mapa`)
  * **Geospatial field (Campo Geoespacial):** `geo_ponto_municipio` (tipo `GEOGRAPHY` nativo com `ST_GEOGPOINT`)
  * **Tooltip (Dica de Ferramenta):** `ds_rotulo_mapa` (exibe `#Ranking Cidade | IAV | Concorrentes (Saturação) | Formato`)
  * **Size (Tamanho da Bolha):** `vl_score_iav` (ou `qt_populacao_residente`)
  * **Color dimension (Cor da Bolha):** `ds_formato_recomendado`
* **Tabela Executiva de Decisão de CAPEX & Concorrência:**
  * Colunas: `nr_ranking_iav`, `nm_municipio`, `qt_concorrentes_diretos_total`, `vl_concorrentes_por_10k_hab`, `ds_saturacao_concorrencial`, `vl_score_iav`, `ds_formato_recomendado`, `fx_capex_estimado`, `vl_confianca_recomendacao`.

---

### Página 2: Governança de IA, Explicabilidade (Art. 20 LGPD) e MLOps (Etapa 4)
Fontes de Dados: `mlops_experiments_log`, `mlops_explainability_lgpd` e `mlops_monitoring_drift`

* **Gráfico de Barras Horizontais (Explicabilidade Art. 20 LGPD):**
  * Dimensão: `nm_variavel` | Métrica: `vl_importancia_gini` e `vl_importancia_permutacao_media`
* **Tabela de Rastreabilidade de Experimentos (Etapa 3):**
  * Colunas: `run_id`, `versao_dados`, `algoritmo`, `parametros`, `metrica_principal_nome`, `metrica_principal_valor`, `accuracy`, `f1_macro`
* **Painel Semafórico de Monitoramento Contínuo (Data Drift & Model Drift):**
  * Colunas: `dimensao_monitoramento`, `indicador`, `metrica_utilizada`, `valor_atual_producao`, `limite_tolerancia`, `status_alerta`, `acao_recomendada`.

