-- ==============================================================================
-- DATAFORM / BIGQUERY SQL ASSERTIONS & VIEWS — GOVERNANÇA ATIVA (DAMA-DMBOK)
-- Projeto GCP: projeto-governanca
-- Datasets: muffato_bronze, muffato_silver, muffato_gold
-- ==============================================================================

-- 1. ASSERTION DE UNICIDADE E COMPLETUDE (645 Municípios Oficiais de SP)
SELECT
  COUNT(*) AS total_registros,
  COUNT(DISTINCT cd_municipio) AS chaves_unicas,
  SUM(CASE WHEN qt_populacao_residente IS NULL OR vl_pib_total_mil_reais IS NULL THEN 1 ELSE 0 END) AS total_nulos
FROM `projeto-governanca.muffato_silver.municipios_sp_governado`
HAVING total_registros != 645 OR chaves_unicas != 645 OR total_nulos > 0;

-- 2. ASSERTION DE VALIDADE E CONSISTÊNCIA MACROECONÔMICA
SELECT
  cd_municipio,
  nm_municipio,
  qt_populacao_residente,
  vl_salario_medio_mensal_reais,
  vl_score_iav
FROM `projeto-governanca.muffato_gold.expansao_recomendacoes_iav`
WHERE qt_populacao_residente <= 0
   OR vl_salario_medio_mensal_reais <= 0
   OR vl_score_iav < 0
   OR vl_score_iav > 100;

-- 3. VIEW EXECUTIVA PARA O LOOKER STUDIO (COMITÊ DE EXPANSÃO GRUPO MUFFATO)
CREATE OR REPLACE VIEW `projeto-governanca.muffato_gold.vw_painel_executivo_expansao` AS
SELECT
  nr_ranking_iav,
  cd_municipio,
  nm_municipio,
  nm_regiao_intermediaria,
  ds_porte_populacional,
  ds_vocacao_economica,
  qt_populacao_residente,
  vl_densidade_demografica_hab_km2,
  vl_massa_salarial_per_capita_reais,
  vl_salario_medio_mensal_reais,
  vl_pib_per_capita_reais,
  vl_pib_total_mil_reais,
  vl_score_pilar_demografico,
  vl_score_pilar_renda,
  vl_score_pilar_economia,
  vl_score_pilar_empresarial,
  vl_score_iav,
  ds_cluster_socioeconomico,
  ds_formato_recomendado,
  vl_confianca_recomendacao,
  CASE
    WHEN ds_formato_recomendado = 'Max Atacadista (Cash & Carry)' THEN 'R$ 40M - R$ 60M'
    WHEN ds_formato_recomendado = 'Super Muffato / Gourmet' THEN 'R$ 25M - R$ 40M'
    WHEN ds_formato_recomendado = 'Muffato Go / Proximidade' THEN 'R$ 5M - R$ 15M'
    ELSE 'Monitoramento Estrategico'
  END AS fx_capex_estimado
FROM `projeto-governanca.muffato_gold.expansao_recomendacoes_iav`
ORDER BY nr_ranking_iav ASC;

