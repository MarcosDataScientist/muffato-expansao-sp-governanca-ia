# 📈 Plano de Monitoramento Contínuo — Produção & MLOps (Etapa 4)
**Projeto GCP:** `projeto-governanca` | **Tabela de Monitoramento:** `muffato_gold.mlops_monitoring_drift`  
**Organização Beneficiária:** Grupo Muffato (Expansão no Estado de São Paulo)  
**Disciplina:** Governança de TI e de Dados — UEL (6º Semestre)

---

## 🎯 Questão Orientadora de Governança
> *"Depois que o modelo entra em produção, como sabemos que ele continua funcionando adequadamente?"*

Este plano define os indicadores quantitativos, limites de tolerância (*thresholds*) e ações corretivas automatizadas nas **4 dimensões obrigatórias** (Dados, Modelo, Negócio e Governança), cujos resultados são persistidos na tabela `projeto-governanca:muffato_gold.mlops_monitoring_drift`.

---

## 📊 Matriz de Monitoramento (O que monitorar, Indicador, Limite e Ação)

| Dimensão | O que Monitorar | Indicador / Métrica | Limite de Tolerância (*Threshold*) | Status Simulado (Lote Atual) | Ação Governada Quando Ultrapassado |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **1. Dados** | Completude da ingestão IBGE/CEMPRE | Taxa de *Missing Values* (%) | `0,0%` (Zero nulos admitidos na Silver/Gold) | `0,0%` (🟢 Estável) | Bloquear atualização da camada Gold via *Assertion* e acionar fallback da última versão íntegra. |
| **1. Dados** | *Data Drift* Demográfico (`qt_populacao_residente`, `vl_densidade`) | *PSI (Population Stability Index)* e Teste KS ($p$-valor) | $\text{PSI} < 0,10$ e $p \ge 0,05$ | $\text{PSI} = 0,0018$ (🟢 Estável) | Manter versão corrente do modelo. |
| **1. Dados** | *Data Drift* de Renda (`vl_salario_medio`, `vl_massa_salarial_pc`) | *PSI (Population Stability Index)* e Teste KS ($p$-valor) | Alerta: $\text{PSI} \in [0,10; 0,25)$<br/>Crítico: $\text{PSI} \ge 0,25$ | $\text{PSI}_{\text{sal}} = 0,5355$ (🔴 Crítico — Inflação salarial) | **Gatilho de Retreinamento:** Recalibrar o `RobustScaler` com a nova distribuição nominal e reexecutar o pipeline `02_etapa3_modelagem_iav.py`. |
| **2. Modelo** | Desempenho preditivo do recomendador de formatos | *F1-Score (Macro)* e *Accuracy* em validação | $\text{F1}_{\text{macro}} \ge 0,85$ | $\text{F1} = 0,9180$ (🟢 Estável) | Se $\text{F1} < 0,85$, reverter para a versão anterior no *Model Registry* (`rf-v1.0.0-etapa3`) e auditar hiperparâmetros. |
| **2. Modelo** | Coesão geométrica dos clusters socioeconômicos | *Silhouette Score* ($k=4$) | $\text{Silhouette} \ge 0,28$ | $\text{Silhouette} = 0,3346$ (🟢 Estável) | Reavaliar número ótimo de clusters $k \in [3, 6]$ caso ocorra fragmentação estrutural. |
| **3. Negócio** | Aderência e utilização pelo Comitê de Expansão | Taxa de concordância executiva nas praças Top-20 do IAV | $\ge 80\%$ de aprovação na triagem macro | `90,0%` (🟢 Estável) | Revisar os pesos $w_k$ dos 4 pilares do IAV junto à Diretoria de Expansão. |
| **3. Negócio** | Retorno sobre Capital Investido (*ROIC*) das lojas inauguradas | Atingimento da curva de *break-even* projetada | Desvio máximo de $\pm 15\%$ no faturamento do 1º ano | `Em conformidade` (🟢 Estável) | Incluir variáveis concorrenciais locais adicionais (CNPJ Receita Federal) na calibragem do pilar empresarial. |
| **4. Governança** | *Fairness* Territorial e Mitigação de Vieses | Discrepância entre ranking por PIB *per capita* vs. Massa Salarial | 0 cidades penalizadas exclusivamente por ausência de enclave industrial | `100% Auditado` (🟢 Conforme) | Auditar pesos de renda familiar e submeter revisão ao Comitê de Governança de Dados. |
| **4. Governança** | Conformidade com o **Artigo 20 da LGPD** | Cobertura de explicabilidade (*Permutation / Gini Importance*) | `100%` das recomendações com justificativa auditável | `100%` (🟢 Conforme) | Disponibilizar tabela `mlops_explainability_lgpd` nos relatórios do Comitê Executivo. |

