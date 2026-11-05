# Relatório Técnico Final — Etapa 4: Governança da Solução de IA e MLOps
**Projeto:** Inteligência e Governança de Expansão no Varejo com Base em Dados Públicos Municipais  
**Estudo de Caso:** Expansão Estratégica do Grupo Muffato no Estado de São Paulo (645 Municípios)  
**Disciplina:** Governança de TI e de Dados — Universidade Estadual de Londrina (UEL) — 6º Semestre  
**Docente:** Prof. Dr. André Menolli  
**Equipe:** Guilherme Terziotti, Lucas Silva e Marcos Beregula  

---

## 1. Visão Geral: Da Modelagem ao Ciclo de Vida Governado (MLOps)

A **Etapa 4** consolida a governança ponta a ponta da solução de Inteligência Artificial desenvolvida para a expansão do **Grupo Muffato** em São Paulo. Mais do que treinar modelos isolados, a arquitetura implementada em `projeto/ambiente_final/` demonstra o gerenciamento completo do ciclo de vida do modelo sob os frameworks **DAMA-DMBOK2**, **COBIT 2019 (APO14, BAI03, MEA01)**, **ISO/IEC 38500**, **Código IBGC (6ª ed.)** e **LGPD (Artigo 20)**.

---

## 2. Os 4 Pilares de MLOps Implementados

### 2.1 Versionamento Integral (Código, Dados, Modelos e Configurações)
* **Código:** Scripts modulares em Python versionados em `ambiente_final/pipeline/` (`01` a `05`).
* **Dados (Hash SHA-256 + Arquitetura Medalhão no BigQuery):**
  * `v2.0-ibge-2022-silver`: 645 municípios $\times$ 32 atributos (exclusivamente IBGE);
  * `v3.0-ibge-cnpj-concorrentes`: 645 municípios $\times$ 39 atributos (integrando `muffato_bronze.cnpj_concorrentes_sp_raw` da Receita Federal `gov.br`).
* **Modelos (MLflow Model Registry via Docker):**
  * `Muffato_KMeans_Segmentacao_SP`: **Version 1** (`v2.0`) ➔ **Version 2** (`v3.0` com concorrentes);
  * `Muffato_RandomForest_Recomendador_Formatos`: **Version 1** (`v2.0`) ➔ **Version 2** (`v3.0` com concorrentes).
* **Configurações:** Centralizadas em [`config/settings.yaml`](../../ambiente_final/config/settings.yaml) com `random_state: 42`, thresholds de PSI/KS e pesos do IAV.

### 2.2 Experiment Tracking em Container Docker (`http://localhost:5050`)
O servidor **MLflow 3.18** executando no container `muffato-mlflow-governance` registra 28 runs auditáveis nos dois experimentos oficiais (`Muffato_SP_Etapa3_Clusterizacao_Municipios` e `Muffato_SP_Etapa3_4_Recomendador_Formatos_Loja`), armazenando parâmetros, métricas, assinaturas de schema (`infer_signature`) e artefatos visuais.

### 2.3 Explicabilidade Algorítmica e Conformidade com o Artigo 20 da LGPD
A tabela `projeto-governanca:muffato_gold.mlops_explainability_lgpd` audita a contribuição global e por permutação de cada uma das 12 variáveis na decisão do formato de loja:

| Variável | Importância Gini | Importância por Permutação | Papel na Decisão Auditável (Art. 20 LGPD) |
| :--- | :---: | :---: | :--- |
| `vl_pib_total_mil_reais` | 0,2080 | 0,0255 | Alto impacto na distinção de escala e formato |
| `qt_populacao_residente` | 0,1732 | 0,0511 | Alto impacto na distinção de escala e formato |
| `vl_densidade_demografica_hab_km2` | 0,1344 | 0,0338 | Alto impacto na distinção de escala e formato |
| `pc_agropecuaria_economia` | 0,1139 | 0,0107 | Alto impacto na distinção de escala e formato |
| `qt_minimercados_mercearias` *(CNPJ)* | **0,0928** | **0,0133** | **Impacto direto na viabilidade B2B do Max Atacadista** |
| `vl_massa_salarial_per_capita_reais` | 0,0814 | 0,0426 | Impacto complementar de poder de compra familiar |
| `vl_densidade_empresarial_por_mil_hab` | 0,0490 | 0,0025 | Impacto complementar de dinamismo empresarial |
| `vl_concorrentes_por_10k_hab` *(CNPJ)* | **0,0458** | **0,0139** | **Filtro de saturação competitiva (bloqueio de praças saturadas)** |

### 2.4 Monitoramento Contínuo de Produção (*Data Drift*, *Model Drift*, Negócio e Governança)
O pipeline [`03_etapa4_mlops_monitoramento.py`](../../ambiente_final/pipeline/03_etapa4_mlops_monitoramento.py) calcula o **Population Stability Index (PSI)** e o teste **Kolmogorov-Smirnov (KS)** sobre todas as 12 features, detectando automaticamente:
* **Estabilidade demográfica e setorial** ($\text{PSI} < 0,01$ — `ESTAVEL`);
* **Alerta de expansão concorrencial** em `vl_concorrentes_por_10k_hab` ($\text{PSI} = 0,0993$, $p < 0,05$ — `ALERTA - Recalibrar Scaler`);
* **Drift crítico inflacionário** em `vl_salario_medio_mensal_reais` ($\text{PSI} = 0,5355 \ge 0,25$ — `CRITICO - Retreinar Modelo`).

---

## 3. Índice das 7 Entregas do Pacote de Governança de IA

1. **Repositório da Solução:** [`projeto/ambiente_final/`](../../ambiente_final/) (`Dockerfile`, `docker-compose.yml`, `pipeline/01` a `05`).
2. **Dataset Documentado (`v3.0`):** [`municipios_sp_governado_v3_concorrentes.csv`](../../ambiente_final/reports/municipios_sp_governado_v3_concorrentes.csv) + [`docs/dicionario_dados.md`](../docs/dicionario_dados.md) (39 variáveis).
3. **Registro dos Experimentos:** [`mlops_experiments_log.csv`](../../ambiente_final/reports/mlops_experiments_log.csv) + MLflow Docker (`http://localhost:5050`).
4. **Model Card Oficial:** [`docs/model_card.md`](../docs/model_card.md).
5. **Plano de Monitoramento:** [`docs/plano_monitoramento.md`](../docs/plano_monitoramento.md).
6. **Matriz de Riscos Integrada:** [`docs/matriz_riscos.md`](../docs/matriz_riscos.md).
7. **Relatório Executivo & Painel Looker Studio:** Este documento + Views `vw_painel_executivo_expansao` e `vw_mapa_candidatos_expansao` no BigQuery (`projeto-governanca`).

