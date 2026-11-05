# 📋 Model Card Oficial — Sistema de Inteligência Macro-Locacional & Expansão Varejista
**Organização Beneficiária:** Grupo Muffato (Expansão no Estado de São Paulo)  
**Projeto GCP:** `projeto-governanca` (`muffato_bronze` ➔ `muffato_silver` ➔ `muffato_gold`)  
**Disciplina:** Governança de TI e de Dados — UEL (6º Semestre)  
**Versão do Modelo:** `rf-v1.0.0-etapa3` / `kmeans-v1.0.0-etapa3`  

---

## 1. Objetivo do Modelo
Apoiar o **Comitê Executivo de Expansão** e o **Conselho de Administração** do Grupo Muffato na alocação eficiente de capital intensivo (*CAPEX* de R$ 15M a R$ 60M por loja) no Estado de São Paulo, por meio de:
1. **Segmentação Socioeconômica Não Supervisionada (`K-Means` / `Ward`):** Agrupamento dos 645 municípios paulistas em 4 perfis estruturais homogêneos;
2. **Scoring Multicritério (`IAV` $\in [0, 100]$):** Ranqueamento objetivo de atratividade varejista combinando Demografia (30%), Poder de Compra (30%), Dinamismo Econômico (25%) e Ambiente Empresarial (15%);
3. **Classificação de Formato de Loja (`Random Forest`):** Recomendação automatizada e auditável da bandeira ideal para cada praça:
   * *Max Atacadista (Cash & Carry)*;
   * *Super Muffato / Muffato Gourmet*;
   * *Muffato Go (Proximidade / Autoatendimento)*;
   * *Monitoramento / Polo Satélite*.

---

## 2. Dados Utilizados
* **Fonte Primária:** Dados Públicos Oficiais do **IBGE** (Censo Demográfico 2022, PIB dos Municípios / Contas Regionais e CEMPRE — Cadastro Central de Empresas).
* **Ativo Governado (Camada Silver):** Tabela `projeto-governanca:muffato_silver.municipios_sp_governado` (`muffato_expansao_sp_governado.parquet`), contendo **645 registros e 32 atributos** auditados sob as 6 dimensões do *DAMA-DMBOK* (100% de completude, unicidade estrita de chaves IBGE).
* **Vetor Preditivo ($X$):** 10 variáveis socioeconômicas (`qt_populacao_residente`, `vl_densidade_demografica_hab_km2`, `vl_massa_salarial_per_capita_reais`, `vl_salario_medio_mensal_reais`, `vl_pib_per_capita_reais`, `vl_pib_total_mil_reais`, `pc_servicos_economia`, `pc_industria_economia`, `pc_agropecuaria_economia`, `vl_densidade_empresarial_por_mil_hab`).

---

## 3. População e Contexto de Aplicação
* **Cobertura Geográfica:** Totalidade dos **645 municípios do Estado de São Paulo** (de Borá, com 807 habitantes, à capital São Paulo, com 11,45 milhões de habitantes).
* **Granularidade:** Municipal (análise macro-locacional para triagem estratégica de praças).

---

## 4. Métricas de Desempenho (Validação Empírica)
* **Prevenção de Data Leakage:** Particionamento estratificado (*75% treino / 25% teste*, `random_state=42`) executado **estritamente antes** do ajuste do `RobustScaler`.
* **Clusterização (`K-Means`, $k=4$):**
  * *Silhouette Score:* **0,3312** | *Davies-Bouldin Index:* **1,0984** | *Calinski-Harabasz:* **287,45**.
* **Classificação de Formato de Loja (`Random Forest`, $n=100$):**
  * *Accuracy (Teste):* **97,53%**
  * *F1-Score (Macro):* **0,9454**
  * *Precision (Macro):* **0,9612**
  * *Recall (Macro):* **0,9348**
  * *ROC-AUC (OvR Macro):* **0,9965**

---

## 5. Limitações Conhecidas
1. **Granularidade Macro-Locacional:** Os dados do IBGE operam em nível municipal agregado; o modelo indica **qual cidade** e **qual formato** priorizar, mas não substitui o estudo geomercadológico de microlocalização (escolha do terreno, tráfego da avenida ou zoneamento urbano).
2. **Defasagem Temporal de Pesquisas Estruturais:** O Censo Demográfico é decenal e as Contas Regionais do IBGE possuem ciclo de publicação anual/bienal.
3. **Economia Informal:** As métricas do CEMPRE capturam exclusivamente vínculos empresariais e salariais formais.

---

## 6. Usos Recomendados
* Triagem executiva e priorização de municípios paulistas para o plano diretor de expansão física (horizonte de 1 a 5 anos);
* Alocação preliminar de orçamento de *CAPEX* por formato de bandeira varejista;
* Subsídio quantitativo para reuniões do Comitê de Expansão e prestação de contas ao Conselho de Administração (*IBGC*).

---

## 7. Usos Não Recomendados
* Assinatura de contratos de compra/locação imobiliária sem vistoria presencial de engenharia e análise concorrencial de raio (isócronas de deslocamento);
* Extrapolação direta do modelo treinado em São Paulo para outros estados sem recalibração do `RobustScaler` regional;
* Utilização para concessão de crédito individual a pessoas físicas.

---

## 8. Riscos Mapeados
* **Risco de Enclave Industrial:** Municípios pequenos com refinarias ou polos químicos (ex: Paulínia) apresentam PIB *per capita* artificialmente inflado. *Mitigação implementada:* Inclusão da variável **Massa Salarial Formal per capita** com peso de 30% no IAV e uso de `RobustScaler`.
* **Risco de Data Drift Inflacionário:** Deslocamento nominal dos salários e do PIB ao longo dos anos. *Mitigação:* Monitoramento via *PSI (Population Stability Index)* na camada Gold do BigQuery.

---

## 9. Aspectos Éticos, Fairness e Conformidade com a LGPD
* **Isenção de Dados Pessoais (LGPD - Lei nº 13.709/2018):** O modelo consome exclusivamente estatísticas públicas agregadas em nível municipal, garantindo **risco zero de violação de privacidade individual**.
* **Explicabilidade Algorítmica (Artigo 20 da LGPD):** Todas as predições são auditadas por importância de permutação e decomposição de pilares na tabela `muffato_gold.mlops_explainability_lgpd`, permitindo explicar exatamente o peso de cada atributo na recomendação.
* **Mitigação de Viés Territorial (*Fairness*):** O modelo evita penalizar cidades populosas periféricas com menor PIB *per capita* ao equilibrar escala demográfica com massa salarial agregada.
* **Princípio *Human-in-the-Loop*:** O sistema atua como motor consultivo de apoio à decisão; a deliberação final de investimento pertence aos órgãos de governança humana.

---

## 10. Responsáveis pelo Modelo (Data & AI Stewards)
* **Equipe de Ciência de Dados e Governança (UEL):** Guilherme Terziotti, Lucas Silva e Marcos Beregula.
* **Docente Orientador:** Prof. Dr. André Menolli (*Disciplina de Governança de TI e de Dados*).

