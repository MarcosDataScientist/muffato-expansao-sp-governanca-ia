#!/usr/bin/env python3
"""
ETAPAS 3 & 4 — MLflow Experiment Tracking Local, Model Registry e Artefatos Visuais
Atende integralmente ao requisito de ProjetoFinal_Etapas3_4.pdf:
  "Experimento -> Parâmetros -> Métricas -> Modelo -> Artefatos
   De forma a mostrar a diferença entre simplesmente treinar um modelo e gerenciar o
   ciclo de vida de um modelo."
"""

import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    calinski_harabasz_score,
    confusion_matrix,
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

RANDOM_STATE = 42
DATA_VERSION = "v3.0-ibge-cnpj-concorrentes"

AMBIENTE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = AMBIENTE_DIR.parent
ETAPA3_DIR = BASE_DIR / "etapa_3"
ETAPA4_DIR = BASE_DIR / "etapa_4"

SILVER_CSV = AMBIENTE_DIR / "reports" / "municipios_sp_governado_v3_concorrentes.csv"
GOLD_CSV = AMBIENTE_DIR / "reports" / "gold_expansao_recomendacoes_iav.csv"
XAI_CSV = AMBIENTE_DIR / "reports" / "mlops_explainability_lgpd.csv"
DRIFT_CSV = AMBIENTE_DIR / "reports" / "mlops_monitoring_drift.csv"

FIG_DIR = AMBIENTE_DIR / "reports" / "fig"
FIG_DIR.mkdir(parents=True, exist_ok=True)

MLFLOW_DIR = AMBIENTE_DIR / "mlflow_tracking"
MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = MLFLOW_DIR / "mlflow.db"
ARTIFACTS_DIR = MLFLOW_DIR / "mlartifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

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


def compute_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()[:16]


def generate_diagnostic_plots(df_gold: pd.DataFrame, df_xai: pd.DataFrame, df_drift: pd.DataFrame,
                              sil_results: dict, y_test, y_pred, labels_order):
    """Gera os 5 gráficos executivos de diagnóstico e salva em reports/fig/."""
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#cbd5e1"

    # 1. Curva Silhouette (K-Means vs Ward)
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=200)
    ks = sorted(list(sil_results["K-Means"].keys()))
    ax.plot(ks, [sil_results["K-Means"][k] for k in ks], marker="o", linewidth=2.5, color="#0b2958", label="K-Means (k-means++)")
    ax.plot(ks, [sil_results["Ward"][k] for k in ks], marker="s", linewidth=2.5, linestyle="--", color="#c8102e", label="Agglomerative Ward")
    ax.axvline(4, color="#16a34a", linestyle=":", linewidth=1.8, label="k=4 Selecionado (Equilíbrio Negócio/Coesão)")
    ax.set_title("Avaliação de Clusterização — Silhouette Score por Número de Clusters (k)", fontsize=12, fontweight="bold", color="#0b2958")
    ax.set_xlabel("Número de Clusters (k)", fontsize=10)
    ax.set_ylabel("Silhouette Score", fontsize=10)
    ax.set_xticks(ks)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(frameon=True, fontsize=9)
    fig.tight_layout()
    p1 = FIG_DIR / "01_curva_silhouette_clusters.png"
    fig.savefig(p1)
    plt.close(fig)

    # 2. Projeção PCA 2D dos 645 Municípios
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=200)
    palette = ["#0b2958", "#2563eb", "#d97706", "#64748b"]
    for idx, cl_name in enumerate(sorted(df_gold["ds_cluster_socioeconomico"].unique())):
        sub = df_gold[df_gold["ds_cluster_socioeconomico"] == cl_name]
        ax.scatter(sub["vl_pca_1"], sub["vl_pca_2"], s=36, alpha=0.78, color=palette[idx % len(palette)], label=f"{cl_name} (n={len(sub)})")
    ax.set_title("Projeção PCA (2D) — Segmentação dos 645 Municípios de São Paulo", fontsize=12, fontweight="bold", color="#0b2958")
    ax.set_xlabel("Componente Principal 1 (Escala Econômica & Demográfica)", fontsize=10)
    ax.set_ylabel("Componente Principal 2 (Vocação Setorial & Densidade)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best", fontsize=8.5, frameon=True)
    fig.tight_layout()
    p2 = FIG_DIR / "02_pca_clusters_sp.png"
    fig.savefig(p2)
    plt.close(fig)

    # 3. Matriz de Confusão do Classificador Campeão (Random Forest)
    fig, ax = plt.subplots(figsize=(7.5, 5.8), dpi=200)
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[l.split(" (")[0].split(" /")[0] for l in labels_order])
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Matriz de Confusão — Motor Recomendador de Formatos (Conjunto de Teste)", fontsize=11, fontweight="bold", color="#0b2958")
    plt.xticks(rotation=20, ha="right", fontsize=9)
    plt.yticks(fontsize=9)
    fig.tight_layout()
    p3 = FIG_DIR / "03_matriz_confusao_formatos.png"
    fig.savefig(p3)
    plt.close(fig)

    # 4. Explicabilidade Algorítmica (Art. 20 LGPD)
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    df_xai_sorted = df_xai.sort_values("vl_importancia_gini", ascending=True)
    y_pos = np.arange(len(df_xai_sorted))
    ax.barh(y_pos - 0.18, df_xai_sorted["vl_importancia_gini"], height=0.35, color="#0b2958", label="Importância Gini (Impureza)")
    ax.barh(y_pos + 0.18, df_xai_sorted["vl_importancia_permutacao_media"], height=0.35, color="#1a73e8", label="Importância por Permutação (Teste)")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_xai_sorted["nm_variavel"], fontsize=9)
    ax.set_xlabel("Importância Relativa na Decisão do Formato", fontsize=10)
    ax.set_title("Explicabilidade Algorítmica (Art. 20 LGPD) — Contribuição das Variáveis", fontsize=11.5, fontweight="bold", color="#0b2958")
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    p4 = FIG_DIR / "04_explicabilidade_lgpd_art20.png"
    fig.savefig(p4)
    plt.close(fig)

    # 5. Monitoramento de Data Drift (PSI)
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    df_psi = df_drift[df_drift["metrica_utilizada"].str.contains("PSI")].copy()
    df_psi["var_short"] = df_psi["indicador"].str.replace("Estabilidade de Distribuicao: ", "", regex=False)
    df_psi = df_psi.sort_values("valor_atual_producao", ascending=True)
    colors_psi = [
        "#dc2626" if v >= 0.25 else ("#d97706" if v >= 0.10 else "#16a34a")
        for v in df_psi["valor_atual_producao"]
    ]
    ax.barh(df_psi["var_short"], df_psi["valor_atual_producao"], color=colors_psi, height=0.55)
    ax.axvline(0.10, color="#d97706", linestyle="--", linewidth=1.5, label="Limite de Alerta (PSI = 0.10)")
    ax.axvline(0.25, color="#dc2626", linestyle="--", linewidth=1.8, label="Limite Crítico / Retreino (PSI = 0.25)")
    ax.set_title("Monitoramento MLOps de Data Drift — Population Stability Index (PSI)", fontsize=11.5, fontweight="bold", color="#0b2958")
    ax.set_xlabel("Valor do PSI (Lote de Produção Simulado vs. Base de Treino)", fontsize=10)
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    p5 = FIG_DIR / "05_monitoramento_data_drift_psi.png"
    fig.savefig(p5)
    plt.close(fig)

    return [p1, p2, p3, p4, p5]


def run_mlflow_tracking():
    import urllib.request
    docker_uri = "http://127.0.0.1:5050"
    try:
        urllib.request.urlopen(f"{docker_uri}/health", timeout=2)
        tracking_uri = docker_uri
        use_remote_artifacts = True
    except Exception:
        tracking_uri = f"sqlite:///{DB_PATH}"
        use_remote_artifacts = False

    mlflow.set_tracking_uri(tracking_uri)
    print(f"[MLflow] Tracking URI configurado em: {tracking_uri}")

    df_gold = pd.read_csv(GOLD_CSV)
    df_xai = pd.read_csv(XAI_CSV)
    df_drift = pd.read_csv(DRIFT_CSV)
    data_hash = compute_file_sha256(SILVER_CSV)

    # Preparação para Clusterização
    X_clust_raw = df_gold[FEATURES_CLUSTER].copy()
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

    # Preparação Supervisionada (Split ANTES do Scaling)
    X_sup = df_gold[FEATURES_CLUSTER].copy()
    y_sup = df_gold["ds_formato_recomendado"].copy()
    labels_order = sorted(y_sup.unique())

    X_train, X_test, y_train, y_test = train_test_split(
        X_sup, y_sup, test_size=0.25, stratify=y_sup, random_state=RANDOM_STATE
    )

    sil_results = {"K-Means": {}, "Ward": {}}
    for k in [3, 4, 5, 6]:
        km_tmp = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE).fit(X_clust_scaled)
        sil_results["K-Means"][k] = float(silhouette_score(X_clust_scaled, km_tmp.labels_))
        ward_tmp = AgglomerativeClustering(n_clusters=k, linkage="ward").fit(X_clust_scaled)
        sil_results["Ward"][k] = float(silhouette_score(X_clust_scaled, ward_tmp.labels_))

    rf_champ = Pipeline([
        ("scaler", RobustScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=RANDOM_STATE)),
    ])
    rf_champ.fit(X_train, y_train)
    y_pred_champ = rf_champ.predict(X_test)

    plot_paths = generate_diagnostic_plots(df_gold, df_xai, df_drift, sil_results, y_test, y_pred_champ, labels_order)
    print(f"[OK] {len(plot_paths)} gráficos de diagnóstico gerados em {FIG_DIR}")

    # Copiar figuras também para etapa_3/reports e etapa_4/reports
    for p in plot_paths:
        (ETAPA3_DIR / "reports" / p.name).write_bytes(p.read_bytes())
        (ETAPA4_DIR / "reports" / p.name).write_bytes(p.read_bytes())

    # =========================================================================
    # EXPERIMENTO 1: CLUSTERIZAÇÃO DE PRAÇAS (ETAPA 3)
    # =========================================================================
    exp1_name = "Muffato_SP_Etapa3_Clusterizacao_Municipios"
    if mlflow.get_experiment_by_name(exp1_name) is None:
        if use_remote_artifacts:
            mlflow.create_experiment(exp1_name)
        else:
            mlflow.create_experiment(exp1_name, artifact_location=ARTIFACTS_DIR.as_uri())
    mlflow.set_experiment(exp1_name)

    print(f"\n[MLflow] Registrando execuções no Experimento 1: {exp1_name}...")
    for k in [3, 4, 5, 6]:
        with mlflow.start_run(run_name=f"KMeans_k{k}_v3_Concorrentes"):
            km = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE)
            labels = km.fit_predict(X_clust_scaled)
            sil = float(silhouette_score(X_clust_scaled, labels))
            db = float(davies_bouldin_score(X_clust_scaled, labels))
            ch = float(calinski_harabasz_score(X_clust_scaled, labels))

            mlflow.set_tags({
                "etapa": "Etapa 3 e 4",
                "dataset_version": DATA_VERSION,
                "dataset_sha256": data_hash,
                "gcp_table": "projeto-governanca:muffato_silver.municipios_sp_governado",
                "concorrentes_cnpj": "True (Receita Federal CNAEs 4711301/4711302/4691500)",
                "responsavel": "Guilherme Terziotti, Lucas Silva, Marcos Beregula",
            })
            mlflow.log_params({
                "algoritmo": "K-Means",
                "n_clusters": k,
                "n_init": 50,
                "random_state": RANDOM_STATE,
                "n_features": len(FEATURES_CLUSTER),
                "scaler": "Log10 + RobustScaler (Winsorized [-3.5, 3.5])",
            })
            mlflow.log_metrics({
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(db, 4),
                "calinski_harabasz_index": round(ch, 2),
                "inertia_wcss": round(float(km.inertia_), 2),
            })
            mlflow.log_artifact(str(FIG_DIR / "01_curva_silhouette_clusters.png"), artifact_path="plots")
            mlflow.log_artifact(str(FIG_DIR / "02_pca_clusters_sp.png"), artifact_path="plots")

            if k == 4:
                sig = infer_signature(X_clust_scaled, labels)
                mlflow.sklearn.log_model(
                    km,
                    name="model_kmeans",
                    signature=sig,
                    serialization_format="cloudpickle",
                    registered_model_name="Muffato_KMeans_Segmentacao_SP",
                )

        with mlflow.start_run(run_name=f"Agglomerative_Ward_k{k}_v3_Concorrentes"):
            ward = AgglomerativeClustering(n_clusters=k, linkage="ward")
            labels_w = ward.fit_predict(X_clust_scaled)
            sil_w = float(silhouette_score(X_clust_scaled, labels_w))
            db_w = float(davies_bouldin_score(X_clust_scaled, labels_w))
            ch_w = float(calinski_harabasz_score(X_clust_scaled, labels_w))

            mlflow.set_tags({
                "etapa": "Etapa 3 e 4",
                "dataset_version": DATA_VERSION,
                "dataset_sha256": data_hash,
                "gcp_table": "projeto-governanca:muffato_silver.municipios_sp_governado",
                "concorrentes_cnpj": "True (Receita Federal CNAEs 4711301/4711302/4691500)",
            })
            mlflow.log_params({
                "algoritmo": "AgglomerativeClustering",
                "n_clusters": k,
                "linkage": "ward",
                "n_features": len(FEATURES_CLUSTER),
                "scaler": "Log10 + RobustScaler (Winsorized [-3.5, 3.5])",
            })
            mlflow.log_metrics({
                "silhouette_score": round(sil_w, 4),
                "davies_bouldin_index": round(db_w, 4),
                "calinski_harabasz_index": round(ch_w, 2),
            })

    # =========================================================================
    # EXPERIMENTO 2: CLASSIFICAÇÃO DE FORMATO DE LOJA & GOVERNANÇA (ETAPA 3 & 4)
    # =========================================================================
    exp2_name = "Muffato_SP_Etapa3_4_Recomendador_Formatos_Loja"
    if mlflow.get_experiment_by_name(exp2_name) is None:
        if use_remote_artifacts:
            mlflow.create_experiment(exp2_name)
        else:
            mlflow.create_experiment(exp2_name, artifact_location=ARTIFACTS_DIR.as_uri())
    mlflow.set_experiment(exp2_name)

    print(f"[MLflow] Registrando execuções e artefatos no Experimento 2: {exp2_name}...")
    sup_models = [
        (
            "01_Baseline_Dummy_Prior_v3_Concorrentes",
            {"algoritmo": "DummyClassifier", "strategy": "prior", "scaler": "StandardScaler", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", StandardScaler()), ("clf", DummyClassifier(strategy="prior", random_state=RANDOM_STATE))]),
            False,
        ),
        (
            "02_Logistic_Regression_Multinomial_v3_Concorrentes",
            {"algoritmo": "LogisticRegression", "C": 1.0, "max_iter": 1000, "scaler": "RobustScaler", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", RobustScaler()), ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_STATE))]),
            False,
        ),
        (
            "03_Decision_Tree_Gini_v3_Concorrentes",
            {"algoritmo": "DecisionTreeClassifier", "max_depth": 5, "min_samples_leaf": 5, "scaler": "RobustScaler", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", RobustScaler()), ("clf", DecisionTreeClassifier(max_depth=5, min_samples_leaf=5, random_state=RANDOM_STATE))]),
            False,
        ),
        (
            "04_Random_Forest_n100_CAMPEAO_v3_Concorrentes",
            {"algoritmo": "RandomForestClassifier", "n_estimators": 100, "max_depth": 8, "scaler": "RobustScaler", "featurization_order": "split_before_scale", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", RobustScaler()), ("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=RANDOM_STATE))]),
            True,
        ),
        (
            "05_Random_Forest_n200_Balanced_v3_Concorrentes",
            {"algoritmo": "RandomForestClassifier", "n_estimators": 200, "max_depth": 10, "class_weight": "balanced", "scaler": "RobustScaler", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", RobustScaler()), ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, class_weight="balanced", random_state=RANDOM_STATE))]),
            False,
        ),
        (
            "06_Gradient_Boosting_v3_Concorrentes",
            {"algoritmo": "GradientBoostingClassifier", "n_estimators": 100, "learning_rate": 0.1, "max_depth": 4, "scaler": "RobustScaler", "n_features": len(FEATURES_CLUSTER)},
            Pipeline([("scaler", RobustScaler()), ("clf", GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=RANDOM_STATE))]),
            False,
        ),
    ]

    for run_name, params, pipe, is_champion in sup_models:
        with mlflow.start_run(run_name=run_name):
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            y_prob = pipe.predict_proba(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
            rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
            try:
                auc = float(roc_auc_score(y_test, y_prob, multi_class="ovr", average="macro"))
            except Exception:
                auc = 0.5

            mlflow.set_tags({
                "etapa": "Etapa 3 e 4 (MLOps)",
                "dataset_version": DATA_VERSION,
                "dataset_sha256": data_hash,
                "gcp_project": "projeto-governanca",
                "gcp_gold_table": "muffato_gold.expansao_recomendacoes_iav",
                "lgpd_art20_compliant": "True",
                "status_modelo": "PRODUCTION_CHAMPION" if is_champion else "CANDIDATE_EXPERIMENT",
            })
            mlflow.log_params(params)
            mlflow.log_metrics({
                "accuracy": round(acc, 4),
                "f1_macro": round(f1, 4),
                "precision_macro": round(prec, 4),
                "recall_macro": round(rec, 4),
                "roc_auc_ovr": round(auc, 4),
            })

            sig = infer_signature(X_train, y_pred)
            if is_champion:
                # Logar todos os artefatos de Governança e gráficos na run campeã
                for fig_file in plot_paths:
                    mlflow.log_artifact(str(fig_file), artifact_path="plots_diagnostico")
                for gov_doc in [
                    AMBIENTE_DIR / "governanca" / "model_card.md",
                    AMBIENTE_DIR / "governanca" / "plano_monitoramento.md",
                    AMBIENTE_DIR / "governanca" / "matriz_riscos.md",
                    AMBIENTE_DIR / "governanca" / "dicionario_dados.md",
                    AMBIENTE_DIR / "config" / "settings.yaml",
                ]:
                    mlflow.log_artifact(str(gov_doc), artifact_path="pacote_governanca")

                mlflow.sklearn.log_model(
                    pipe,
                    name="model_recomendador_formatos",
                    signature=sig,
                    serialization_format="cloudpickle",
                    registered_model_name="Muffato_RandomForest_Recomendador_Formatos",
                )
            else:
                mlflow.sklearn.log_model(
                    pipe,
                    name="model_candidate",
                    signature=sig,
                    serialization_format="cloudpickle",
                )

    print("\n[SUCESSO] Todos os 14 experimentos, métricas, gráficos, Model Card e Modelos registrados no MLflow Local!")


if __name__ == "__main__":
    run_mlflow_tracking()
