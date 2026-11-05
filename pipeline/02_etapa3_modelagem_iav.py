#!/usr/bin/env python3
"""
ETAPA 3 — Pipeline Executável de Modelagem, Scoring IAV (com Concorrentes CNPJ) e Rastreabilidade
Projeto: Expansão Estratégica do Grupo Muffato no Estado de São Paulo (645 Municípios)
Compara e registra a evolução de Dados v2.0 (IBGE) -> v3.0 (IBGE + Concorrentes Receita Federal)
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.tree import DecisionTreeClassifier

PROJECT_ID = "projeto-governanca"
LOCATION = "US"
DATA_VERSION = "v3.0-ibge-cnpj-concorrentes"
RANDOM_STATE = 42

AMBIENTE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = AMBIENTE_DIR.parent
ETAPA3_DIR = BASE_DIR / "etapa_3"
SILVER_V3_CSV = AMBIENTE_DIR / "reports" / "municipios_sp_governado_v3_concorrentes.csv"

FEATURES_CLUSTER = [
    "qt_populacao_residente",
    "vl_densidade_demografica_hab_km2",
    "vl_massa_salarial_per_capita_reais",
    "vl_salario_medio_mensal_reais",
    "vl_pib_per_capita_reais",
    "vl_pib_total_mil_reais",
    "pc_servicos_economia",
    "pc_industria_economia",
    "pc_agropecuaria_economia",
    "vl_densidade_empresarial_por_mil_hab",
    "vl_concorrentes_por_10k_hab",
    "qt_minimercados_mercearias",
]


def minmax_norm(series: pd.Series) -> pd.Series:
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(0.0, index=series.index)
    return (series - s_min) / (s_max - s_min)


def calcular_iav(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula os 4 pilares e o IAV integrando a pressão concorrencial da Receita Federal (CNPJ)."""
    out = df.copy()

    # Pilar 1: Demográfico (30%)
    s_demo = 0.70 * np.log10(out["qt_populacao_residente"].clip(lower=1)) + 0.30 * np.log10(
        out["vl_densidade_demografica_hab_km2"].clip(lower=0.1)
    )
    out["vl_score_pilar_demografico"] = (minmax_norm(s_demo) * 100).round(2)

    # Pilar 2: Poder de Compra (30%) - Com Winsorization [-2.5, +3.5]
    r_massa = (
        (out["vl_massa_salarial_per_capita_reais"] - out["vl_massa_salarial_per_capita_reais"].median())
        / (
            out["vl_massa_salarial_per_capita_reais"].quantile(0.75)
            - out["vl_massa_salarial_per_capita_reais"].quantile(0.25)
        )
    ).clip(-2.5, 3.5)
    z_sal = (
        (out["vl_salario_medio_mensal_reais"] - out["vl_salario_medio_mensal_reais"].mean())
        / out["vl_salario_medio_mensal_reais"].std()
    ).clip(-2.5, 3.5)
    s_renda = 0.60 * r_massa + 0.40 * z_sal
    out["vl_score_pilar_renda"] = (minmax_norm(s_renda) * 100).round(2)

    # Pilar 3: Dinamismo Econômico (25%)
    r_pib_pc = (
        (out["vl_pib_per_capita_reais"] - out["vl_pib_per_capita_reais"].median())
        / (out["vl_pib_per_capita_reais"].quantile(0.75) - out["vl_pib_per_capita_reais"].quantile(0.25))
    ).clip(-2.5, 3.5)
    s_econ = (
        0.50 * minmax_norm(np.log10(out["vl_pib_total_mil_reais"].clip(lower=1)))
        + 0.25 * minmax_norm(r_pib_pc)
        + 0.25 * (out["pc_servicos_economia"] / 100.0)
    )
    out["vl_score_pilar_economia"] = (minmax_norm(s_econ) * 100).round(2)

    # Pilar 4: Ambiente de Negócios & Oportunidade Concorrencial (15%)
    # - Bonifica ecossistema empresarial e clientes B2B transformadores (minimercados)
    # - Bonifica "Oceano Azul" (menor saturação relativa de grandes concorrentes por 10k hab)
    s_ecossistema_b2b = minmax_norm(np.log10((out["qt_unidades_locais_empresas"] + out["qt_minimercados_mercearias"]).clip(lower=1)))
    z_sat = (
        (out["vl_concorrentes_por_10k_hab"] - out["vl_concorrentes_por_10k_hab"].median())
        / (out["vl_concorrentes_por_10k_hab"].quantile(0.75) - out["vl_concorrentes_por_10k_hab"].quantile(0.25) + 1e-5)
    ).clip(-2.0, 3.0)
    s_oceano_azul = 1.0 - minmax_norm(z_sat)  # Quanto menor a saturação por 10k hab, maior a oportunidade líquida

    s_emp_concorrencia = 0.65 * s_ecossistema_b2b + 0.35 * s_oceano_azul
    out["vl_score_pilar_empresarial"] = (minmax_norm(s_emp_concorrencia) * 100).round(2)

    # Score IAV Global Ponderado
    iav_raw = (
        0.30 * out["vl_score_pilar_demografico"]
        + 0.30 * out["vl_score_pilar_renda"]
        + 0.25 * out["vl_score_pilar_economia"]
        + 0.15 * out["vl_score_pilar_empresarial"]
    )
    out["vl_score_iav"] = (minmax_norm(iav_raw) * 100).round(2)
    out["nr_ranking_iav"] = out["vl_score_iav"].rank(ascending=False, method="min").astype(int)
    return out


def definir_formato_alvo(df: pd.DataFrame) -> pd.Series:
    """Motor de decisão de formatos considerando Demografia, Renda e Concorrência (CNAEs)."""
    formatos = []
    q70_renda = df["vl_massa_salarial_per_capita_reais"].quantile(0.70)
    q70_sal = df["vl_salario_medio_mensal_reais"].quantile(0.70)
    med_sat = df["vl_concorrentes_por_10k_hab"].median()

    for _, row in df.iterrows():
        pop = row["qt_populacao_residente"]
        dens = row["vl_densidade_demografica_hab_km2"]
        massa_pc = row["vl_massa_salarial_per_capita_reais"]
        sal = row["vl_salario_medio_mensal_reais"]
        serv = row["pc_servicos_economia"]
        iav = row["vl_score_iav"]
        sat = row["vl_concorrentes_por_10k_hab"]
        minimercados = row["qt_minimercados_mercearias"]
        atacadistas = row["qt_concorrentes_atacadistas"]

        if dens >= 2500 and pop >= 60000:
            formatos.append("Muffato Go / Proximidade")
        elif pop >= 75000 or (pop >= 45000 and iav >= 50):
            # Se há grande rede de minimercados B2B para abastecer ou baixa pressão de atacadistas -> Max Atacadista
            if (minimercados >= 90 and atacadistas <= 15) or (massa_pc < q70_renda and sal < q70_sal):
                formatos.append("Max Atacadista (Cash & Carry)")
            elif (massa_pc >= q70_renda or sal >= q70_sal) and serv >= 48:
                formatos.append("Super Muffato / Gourmet")
            else:
                formatos.append("Max Atacadista (Cash & Carry)")
        elif pop >= 25000 and (massa_pc >= q70_renda or iav >= 42) and sat <= (med_sat * 1.35):
            formatos.append("Super Muffato / Gourmet")
        else:
            formatos.append("Monitoramento / Polo Satelite")
    return pd.Series(formatos, index=df.index)


def run_pipeline():
    print("=== INICIANDO PIPELINE DA ETAPA 3 (v3.0 COM CONCORRENTES RECEITA FEDERAL) ===")
    df = pd.read_csv(
        SILVER_V3_CSV,
        dtype={
            "cd_municipio": str,
            "cd_microrregiao": str,
            "cd_mesorregiao": str,
            "cd_regiao_imediata": str,
            "cd_regiao_intermediaria": str,
        },
    )
    print(f"[1/5] Base Silver v3.0 carregada: {df.shape[0]} municípios x {df.shape[1]} variáveis.")

    # Preservar histórico v2.0 para rastreabilidade evolutiva (v2.0 -> v3.0)
    exp_csv = AMBIENTE_DIR / "reports" / "mlops_experiments_log.csv"
    if exp_csv.exists():
        df_old_exp = pd.read_csv(exp_csv)
        df_old_exp = df_old_exp[df_old_exp["versao_dados"] == "v2.0-ibge-2022-silver"]
        experiments_log = df_old_exp.to_dict("records")
        run_counter = len(experiments_log) + 1
    else:
        experiments_log = []
        run_counter = 1

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Preparação para Clusterização
    X_clust_raw = df[FEATURES_CLUSTER].copy()
    for col in [
        "qt_populacao_residente",
        "vl_pib_total_mil_reais",
        "vl_densidade_demografica_hab_km2",
        "vl_pib_per_capita_reais",
        "vl_massa_salarial_per_capita_reais",
        "qt_minimercados_mercearias",
    ]:
        X_clust_raw[col] = np.log10(X_clust_raw[col].clip(lower=0.1))

    scaler_clust = RobustScaler()
    X_clust_scaled = np.clip(scaler_clust.fit_transform(X_clust_raw), -3.5, 3.5)

    # 2. Clusterização v3.0 (com variáveis de concorrência)
    print("[2/5] Executando Clusterização v3.0 (K-Means e Ward com variáveis de concorrência)...")
    best_km_model = KMeans(n_clusters=4, n_init=50, random_state=RANDOM_STATE)
    labels_km = best_km_model.fit_predict(X_clust_scaled)
    sil_km = silhouette_score(X_clust_scaled, labels_km)
    db_km = davies_bouldin_score(X_clust_scaled, labels_km)
    ch_km = calinski_harabasz_score(X_clust_scaled, labels_km)

    experiments_log.append({
        "run_id": f"RUN-{run_counter:02d}",
        "versao_dados": DATA_VERSION,
        "tipo_tarefa": "Clusterizacao",
        "algoritmo": "K-Means (+ Concorrentes CNPJ)",
        "parametros": "n_clusters=4, n_init=50, features=12 (IBGE+CNAE)",
        "metrica_principal_nome": "Silhouette Score",
        "metrica_principal_valor": round(float(sil_km), 4),
        "accuracy": None,
        "precision_macro": None,
        "recall_macro": None,
        "f1_macro": None,
        "roc_auc_ovr": None,
        "davies_bouldin": round(float(db_km), 4),
        "calinski_harabasz": round(float(ch_km), 2),
        "data_execucao": now_iso,
    })
    run_counter += 1

    df["id_cluster_raw"] = labels_km
    cluster_order = (
        df.groupby("id_cluster_raw")["qt_populacao_residente"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    nomes_clusters = {
        cluster_order[0]: "C1 - Polos Regionais & Metropoles Consolidadas",
        cluster_order[1]: "C2 - Centros Urbanos Dinamicos de Renda Media-Alta",
        cluster_order[2]: "C3 - Municipios Agroindustriais em Expansao",
        cluster_order[3]: "C4 - Municipios de Pequeno Porte & Suporte Local",
    }
    df["ds_cluster_socioeconomico"] = df["id_cluster_raw"].map(nomes_clusters)
    df.drop(columns=["id_cluster_raw"], inplace=True)

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords_pca = pca.fit_transform(X_clust_scaled)
    df["vl_pca_1"] = coords_pca[:, 0].round(4)
    df["vl_pca_2"] = coords_pca[:, 1].round(4)

    # 3. Cálculo do IAV v3.0 e Formato Recomendado
    print("[3/5] Calculando IAV v3.0 (integrando saturação de Hiper/Super/Atacarejos)...")
    df = calcular_iav(df)
    df["ds_formato_recomendado"] = definir_formato_alvo(df)

    # 4. Treinamento Supervisionado v3.0 (Split ANTES do Scaling)
    print("[4/5] Treinando modelos supervisionados na base v3.0 (IBGE + Concorrentes)...")
    X_sup = df[FEATURES_CLUSTER].copy()
    y_sup = df["ds_formato_recomendado"].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X_sup, y_sup, test_size=0.25, stratify=y_sup, random_state=RANDOM_STATE
    )

    candidate_models = [
        (
            "Logistic Regression (+ Concorrentes)",
            "C=1.0, max_iter=1000, features=12",
            Pipeline([("scaler", RobustScaler()), ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_STATE))]),
        ),
        (
            "Decision Tree (+ Concorrentes)",
            "max_depth=5, min_samples_leaf=5, features=12",
            Pipeline([("scaler", RobustScaler()), ("clf", DecisionTreeClassifier(max_depth=5, min_samples_leaf=5, random_state=RANDOM_STATE))]),
        ),
        (
            "Random Forest (n=100, + Concorrentes)",
            "n_estimators=100, max_depth=8, features=12",
            Pipeline([("scaler", RobustScaler()), ("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=RANDOM_STATE))]),
        ),
        (
            "Random Forest (n=200, + Concorrentes)",
            "n_estimators=200, max_depth=10, class_weight=balanced, features=12",
            Pipeline([("scaler", RobustScaler()), ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, class_weight="balanced", random_state=RANDOM_STATE))]),
        ),
        (
            "Gradient Boosting (+ Concorrentes)",
            "n_estimators=100, learning_rate=0.1, max_depth=4, features=12",
            Pipeline([("scaler", RobustScaler()), ("clf", GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=RANDOM_STATE))]),
        ),
    ]

    best_clf_pipeline = None
    best_f1 = -1.0

    for model_name, param_str, pipe in candidate_models:
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
        try:
            auc = roc_auc_score(y_test, y_prob, multi_class="ovr", average="macro")
        except Exception:
            auc = 0.5

        experiments_log.append({
            "run_id": f"RUN-{run_counter:02d}",
            "versao_dados": DATA_VERSION,
            "tipo_tarefa": "Classificacao_Formato_Loja",
            "algoritmo": model_name,
            "parametros": param_str,
            "metrica_principal_nome": "F1-Score (Macro)",
            "metrica_principal_valor": round(float(f1), 4),
            "accuracy": round(float(acc), 4),
            "precision_macro": round(float(prec), 4),
            "recall_macro": round(float(rec), 4),
            "f1_macro": round(float(f1), 4),
            "roc_auc_ovr": round(float(auc), 4),
            "davies_bouldin": None,
            "calinski_harabasz": None,
            "data_execucao": now_iso,
        })
        run_counter += 1

        if f1 > best_f1 and "Random Forest" in model_name:
            best_f1 = f1
            best_clf_pipeline = pipe

    df["vl_confianca_recomendacao"] = best_clf_pipeline.predict_proba(X_sup).max(axis=1).round(4)
    df["ds_versao_modelo"] = "rf-v2.0.0-ibge-cnpj"
    df["dt_processamento_gold"] = now_iso

    for target_dir in [AMBIENTE_DIR, ETAPA3_DIR]:
        (target_dir / "models").mkdir(parents=True, exist_ok=True)
        (target_dir / "reports").mkdir(parents=True, exist_ok=True)
        joblib.dump(best_km_model, target_dir / "models" / "kmeans_municipios_sp.joblib")
        joblib.dump(best_clf_pipeline, target_dir / "models" / "random_forest_formatos.joblib")

    df_exp = pd.DataFrame(experiments_log)
    gold_csv = AMBIENTE_DIR / "reports" / "gold_expansao_recomendacoes_iav.csv"
    df.to_csv(gold_csv, index=False)
    df_exp.to_csv(exp_csv, index=False)
    df.to_csv(ETAPA3_DIR / "reports" / "gold_expansao_recomendacoes_iav.csv", index=False)
    df_exp.to_csv(ETAPA3_DIR / "reports" / "registro_experimentos_etapa3.csv", index=False)

    print("\n=== EVOLUÇÃO DOS EXPERIMENTOS (v2.0 IBGE vs v3.0 IBGE + CONCORRENTES CNPJ) ===")
    print(
        df_exp[df_exp["tipo_tarefa"] == "Classificacao_Formato_Loja"][
            ["run_id", "versao_dados", "algoritmo", "accuracy", "f1_macro", "roc_auc_ovr"]
        ].to_string(index=False)
    )

    print("\n[5/5] Sincronizando tabela Gold e Experimentos no BigQuery...")
    for table_name, csv_path in [
        ("expansao_recomendacoes_iav", gold_csv),
        ("mlops_experiments_log", exp_csv),
    ]:
        subprocess.run(
            [
                "bq", f"--location={LOCATION}", "load",
                "--replace",
                "--autodetect",
                "--source_format=CSV",
                "--skip_leading_rows=1",
                f"{PROJECT_ID}:muffato_gold.{table_name}",
                str(csv_path),
            ],
            check=True,
        )
    print("[SUCESSO] Etapa 3 v3.0 (com concorrentes) concluída!")


if __name__ == "__main__":
    run_pipeline()
