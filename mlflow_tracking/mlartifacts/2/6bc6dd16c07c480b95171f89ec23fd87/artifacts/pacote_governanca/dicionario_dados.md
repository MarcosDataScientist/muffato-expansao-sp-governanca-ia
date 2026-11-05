# Dicionário de Dados — Ativo Governado para Expansão Varejista (SP)

**Organização Beneficiária:** Grupo Muffato (Expansão no Estado de São Paulo)  
**Fonte Oficial:** IBGE (Censo 2022, Contas Regionais 2022, CEMPRE 2022)  
**Dimensões:** 645 municípios x 32 atributos governados  

| Campo | Significado | Tipo | Domínio | Qualidade |
| :--- | :--- | :--- | :--- | :--- |
| `cd_municipio` | Código oficial do município no padrão IBGE de 7 dígitos | String (7) | 3500105 a 3557303 | 100% preenchido, unicidade absoluta (chave primária) |
| `nm_municipio` | Nome oficial do município paulista | String | 645 municípios oficiais do Estado de SP | 100% íntegro, sem caracteres inválidos ou duplicatas |
| `sg_uf` | Sigla da Unidade da Federação | String (2) | SP | 100% consistente (restringe o escopo ao Estado de SP) |
| `cd_microrregiao` | Código identificador da microrregião geográfica IBGE | String (5) | Classificação político-geográfica IBGE | 100% completo e padronizado |
| `nm_microrregiao` | Nome da microrregião geográfica | String | 63 microrregiões paulistas | 100% padronizado |
| `cd_mesorregiao` | Código identificador da mesorregião geográfica IBGE | String (4) | Classificação político-geográfica IBGE | 100% completo e padronizado |
| `nm_mesorregiao` | Nome da mesorregião geográfica | String | 15 mesorregiões paulistas (ex: Macro Metropolitana, Campinas) | 100% padronizado |
| `cd_regiao_imediata` | Código da Região Geográfica Imediata (divisão regional moderna IBGE) | String (6) | Classificação IBGE 2017+ | 100% completo |
| `nm_regiao_imediata` | Nome da Região Geográfica Imediata de referência | String | Regiões imediatas de centros urbanos de SP | 100% íntegro |
| `cd_regiao_intermediaria` | Código da Região Geográfica Intermediária | String (4) | Classificação IBGE 2017+ | 100% completo |
| `nm_regiao_intermediaria` | Nome da Região Geográfica Intermediária | String | Regiões intermediárias de SP (ex: São Paulo, Campinas, Sorocaba) | 100% íntegro |
| `qt_populacao_residente` | População total residente apurada pelo Censo Demográfico 2022 | Integer | 807 (Borá) a 11.451.245 (São Paulo) | 100% validado; Censo oficial do IBGE |
| `vl_area_territorial_km2` | Área territorial oficial da unidade municipal em km² | Float | 3,565 a 1.977,961 km² | 100% consistente; georreferenciamento IBGE |
| `vl_densidade_demografica_hab_km2` | Densidade demográfica (habitantes por quilômetro quadrado) | Float | 4,49 a 13.060,94 hab/km² | 100% calculado e consistente com população/área |
| `qt_unidades_locais_empresas` | Quantidade de unidades locais de empresas ativas (CEMPRE 2022) | Integer | 34 a 582.417 empresas ativas | 100% preenchido |
| `qt_pessoal_ocupado_total` | Total de pessoas ocupadas no município (CEMPRE 2022) | Integer | 64 a 6.012.389 pessoas | 100% consistente (maior ou igual ao pessoal assalariado) |
| `qt_pessoal_ocupado_assalariado` | Total de pessoas ocupadas assalariadas com vínculo formal | Integer | 48 a 5.214.908 pessoas | 100% completo |
| `vl_massa_salarial_anual_mil_reais` | Massa salarial anual e remunerações pagas pelo setor formal (Mil R$) | Float | R$ 1.482,00 a R$ 342.150.840,00 mil | 100% preenchido e tipado |
| `vl_salario_medio_mensal_reais` | Salário médio mensal pago aos trabalhadores formais em Reais | Float | R$ 1.942,50 a R$ 6.840,10 | 100% consistente (acima do salário mínimo 2022) |
| `vl_massa_salarial_per_capita_reais` | Massa salarial anual por habitante (Poder de compra direto) | Float | R$ 1.250,00 a R$ 42.180,00 | Métrica derivada governada; 100% calculada |
| `vl_pib_total_mil_reais` | Produto Interno Bruto municipal a preços correntes (Mil R$ - 2022) | Float | R$ 29.840,00 a R$ 828.980.608,00 mil | 100% apurado pelo IBGE Contas Regionais |
| `vl_pib_per_capita_reais` | PIB per capita municipal a preços correntes em Reais (2022) | Float | R$ 12.349,27 a R$ 713.159,13 | 100% consistente; auditado contra distorções atípicas |
| `vl_vab_servicos_projetado_mil_reais` | VAB do setor de Serviços (exclusive administração pública) projetado (Mil R$) | Float | Valores não negativos | Imputação fundamentada pela matriz setorial de 2021 |
| `vl_vab_industria_projetado_mil_reais` | VAB do setor Industrial projetado para 2022 (Mil R$) | Float | Valores não negativos | Imputação fundamentada pela matriz setorial de 2021 |
| `vl_vab_agropecuaria_projetado_mil_reais` | VAB da Agropecuária projetado para 2022 (Mil R$) | Float | Valores não negativos | Imputação fundamentada pela matriz setorial de 2021 |
| `vl_vab_adm_publica_projetado_mil_reais` | VAB da Administração Pública projetado para 2022 (Mil R$) | Float | Valores não negativos | Imputação fundamentada pela matriz setorial de 2021 |
| `pc_servicos_economia` | Participação percentual do setor de serviços no VAB total (%) | Float | 0.0 a 100.0% | 100% calculado |
| `pc_industria_economia` | Participação percentual da indústria no VAB total (%) | Float | 0.0 a 100.0% | 100% calculado |
| `pc_agropecuaria_economia` | Participação percentual da agropecuária no VAB total (%) | Float | 0.0 a 100.0% | 100% calculado |
| `ds_porte_populacional` | Classificação da praça por porte populacional para alocação de formatos de loja | String (Categoria) | Pequeno I, Pequeno II, Médio Porte, Grande Porte, Metrópole | 100% categorizado |
| `vl_densidade_empresarial_por_mil_hab` | Número de empresas locais ativas para cada 1.000 habitantes | Float | 5.0 a 85.0 empresas/mil hab | 100% calculado |
| `ds_vocacao_economica` | Setor econômico predominante no município para adequação do sortimento | String (Categoria) | Serviços e Comércio, Industrial, Agropecuário | 100% categorizado |
