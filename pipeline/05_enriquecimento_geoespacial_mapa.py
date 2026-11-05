#!/usr/bin/env python3
"""
Ingestão Geoespacial Oficial (BigQuery `basedosdados.br_bd_diretorios_brasil.municipio` +
API Oficial de Malhas Geográficas do IBGE `servicodados.ibge.gov.br/api/v3/malhas/estados/35`).

Substitui qualquer arquivo estático externo por:
1. Tabela Bronze auditável: `projeto-governanca:muffato_bronze.ibge_diretorio_geoespacial_sp_raw`
   (contendo `cd_municipio`, `id_municipio_rf` da Receita Federal, `ddd`, `nm_regiao_metropolitana`,
    `vl_latitude` e `vl_longitude` oficiais do centroide geodésico IBGE);
2. Malha Poligonal Oficial do Estado de SP (645 municípios via API `servicodados.ibge.gov.br`)
   para renderização cartográfica real do mapa executivo;
3. Enriquecimento das camadas Silver (`muffato_silver.municipios_sp_governado`) e Gold
   (`muffato_gold.expansao_recomendacoes_iav`, `vw_painel_executivo_expansao` e `vw_mapa_candidatos_expansao`).
"""

import gzip
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import mlflow
import pandas as pd

PROJECT_ID = "projeto-governanca"
LOCATION = "US"

AMBIENTE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = AMBIENTE_DIR.parent
ETAPA3_DIR = BASE_DIR / "etapa_3"
ETAPA4_DIR = BASE_DIR / "etapa_4"

BRONZE_GEO_CSV = AMBIENTE_DIR / "reports" / "ibge_diretorio_geoespacial_sp_raw.csv"
IBGE_MALHA_GEOJSON = AMBIENTE_DIR / "reports" / "ibge_malha_municipios_sp.geojson"
SILVER_CSV = AMBIENTE_DIR / "reports" / "municipios_sp_governado_v3_concorrentes.csv"
GOLD_CSV = AMBIENTE_DIR / "reports" / "gold_expansao_recomendacoes_iav.csv"
FIG_DIR = AMBIENTE_DIR / "reports" / "fig"


def extract_official_ibge_geospatial() -> pd.DataFrame:
    """
    Extrai os centroides oficiais do IBGE, código SIAFI/Receita Federal (id_municipio_rf),
    DDD e Região Metropolitana diretamente do diretório oficial no BigQuery
    (`basedosdados.br_bd_diretorios_brasil.municipio`) e publica na camada Bronze.
    """
    print("[1/5] Extraindo coordenadas oficiais IBGE e códigos Receita Federal via BigQuery...")
    sql = """
    SELECT
      CAST(id_municipio AS STRING) AS cd_municipio,
      CAST(id_municipio_rf AS STRING) AS cd_municipio_receita_federal,
      CAST(ddd AS STRING) AS nr_ddd,
      COALESCE(nome_regiao_metropolitana, 'Interior / Fora de RM') AS nm_regiao_metropolitana,
      ROUND(ST_Y(centroide), 6) AS vl_latitude,
      ROUND(ST_X(centroide), 6) AS vl_longitude,
      'IBGE Geociencias / Diretorio Oficial Base dos Dados (centroide ST_GEOGPOINT)' AS ds_fonte_geoespacial
    FROM `basedosdados.br_bd_diretorios_brasil.municipio`
    WHERE sigla_uf = 'SP'
    ORDER BY id_municipio
    """
    res = subprocess.run(
        ["bq", "query", f"--project_id={PROJECT_ID}", "--use_legacy_sql=false", "--format=csv", "--max_rows=1000", sql],
        capture_output=True,
        text=True,
        check=True,
    )
    BRONZE_GEO_CSV.write_text(res.stdout, encoding="utf-8")
    df_geo = pd.read_csv(BRONZE_GEO_CSV, dtype={"cd_municipio": str, "cd_municipio_receita_federal": str, "nr_ddd": str})
    df_geo["dt_ingestao_bronze"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    df_geo.to_csv(BRONZE_GEO_CSV, index=False)

    assert len(df_geo) == 645, f"Esperados 645 municípios, obtidos {len(df_geo)}"
    assert df_geo["vl_latitude"].isnull().sum() == 0, "Nulos detectados em vl_latitude!"

    # Carregar na camada Bronze do BigQuery para rastreabilidade completa
    subprocess.run(
        [
            "bq", f"--location={LOCATION}", "load",
            "--replace",
            "--autodetect",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            f"{PROJECT_ID}:muffato_bronze.ibge_diretorio_geoespacial_sp_raw",
            str(BRONZE_GEO_CSV),
        ],
        check=True,
    )
    print(f"[OK] Tabela Bronze publicada: {PROJECT_ID}:muffato_bronze.ibge_diretorio_geoespacial_sp_raw (645 municípios)")
    return df_geo


def fetch_ibge_official_polygons() -> dict:
    """
    Baixa a malha cartográfica oficial dos 645 municípios de SP diretamente da
    API de Serviços de Dados do IBGE (servicodados.ibge.gov.br/api/v3/malhas/estados/35).
    """
    print("[2/5] Consultando API Oficial de Malhas Geográficas do IBGE (servicodados.ibge.gov.br)...")
    if not IBGE_MALHA_GEOJSON.exists():
        url = (
            "https://servicodados.ibge.gov.br/api/v3/malhas/estados/35"
            "?intrarregiao=municipio&formato=application/vnd.geo+json&qualidade=minima"
        )
        raw = urllib.request.urlopen(url, timeout=20).read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        IBGE_MALHA_GEOJSON.write_bytes(raw)
    geojson = json.loads(IBGE_MALHA_GEOJSON.read_text(encoding="utf-8"))
    print(f"[OK] Malha poligonal oficial do IBGE carregada: {len(geojson.get('features', []))} polígonos municipais.")
    return geojson


def enrich_geospatial_and_sync():
    df_geo = extract_official_ibge_geospatial()
    geojson_sp = fetch_ibge_official_polygons()

    # Atualizar também a camada Silver para incluir as coordenadas oficiais do IBGE e código RF
    df_silver = pd.read_csv(SILVER_CSV, dtype={"cd_municipio": str})
    cols_geo_drop = [
        "cd_municipio_receita_federal", "nr_ddd", "nm_regiao_metropolitana",
        "vl_latitude", "vl_longitude", "ds_fonte_geoespacial", "dt_ingestao_bronze",
    ]
    df_silver.drop(columns=[c for c in cols_geo_drop if c in df_silver.columns], inplace=True)
    df_silver = df_silver.merge(
        df_geo[["cd_municipio", "cd_municipio_receita_federal", "nr_ddd", "nm_regiao_metropolitana", "vl_latitude", "vl_longitude"]],
        on="cd_municipio",
        how="left",
    )
    df_silver.to_csv(SILVER_CSV, index=False)
    subprocess.run(
        [
            "bq", f"--location={LOCATION}", "load",
            "--replace",
            "--autodetect",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            f"{PROJECT_ID}:muffato_silver.municipios_sp_governado",
            str(SILVER_CSV),
        ],
        check=True,
    )
    print(f"[OK] Camada Silver atualizada com coordenadas oficiais IBGE e Código RF ({df_silver.shape[1]} colunas).")

    # Atualizar camada Gold
    df_gold = pd.read_csv(GOLD_CSV, dtype={"cd_municipio": str})
    for c in [
        "cd_municipio_receita_federal", "nr_ddd", "nm_regiao_metropolitana",
        "vl_latitude", "vl_longitude", "ds_lat_long", "ds_status_candidato",
        "ds_rotulo_mapa", "fx_capex_estimado",
    ]:
        if c in df_gold.columns:
            df_gold.drop(columns=[c], inplace=True)

    df_gold = df_gold.merge(
        df_geo[["cd_municipio", "cd_municipio_receita_federal", "nr_ddd", "nm_regiao_metropolitana", "vl_latitude", "vl_longitude"]],
        on="cd_municipio",
        how="left",
    )
    assert df_gold["vl_latitude"].isnull().sum() == 0, "Falha ao cruzar coordenadas oficiais dos 645 municípios!"

    df_gold["ds_lat_long"] = (
        df_gold["vl_latitude"].round(5).astype(str) + "," + df_gold["vl_longitude"].round(5).astype(str)
    )
    df_gold["ds_status_candidato"] = df_gold["ds_formato_recomendado"].apply(
        lambda f: "1. Candidato Prioritario (Expansao)"
        if f != "Monitoramento / Polo Satelite"
        else "2. Monitoramento / Polo Satelite"
    )
    capex_map = {
        "Max Atacadista (Cash & Carry)": "R$ 40M - R$ 60M",
        "Super Muffato / Gourmet": "R$ 25M - R$ 40M",
        "Muffato Go / Proximidade": "R$ 5M - R$ 15M",
        "Monitoramento / Polo Satelite": "Sem Aporte Imediato",
    }
    df_gold["fx_capex_estimado"] = df_gold["ds_formato_recomendado"].map(capex_map)
    df_gold["ds_rotulo_mapa"] = (
        "#" + df_gold["nr_ranking_iav"].astype(str)
        + " " + df_gold["nm_municipio"]
        + " | IAV: " + df_gold["vl_score_iav"].astype(str)
        + " | Concorrentes: " + df_gold["qt_concorrentes_diretos_total"].astype(str)
        + " (" + df_gold["ds_saturacao_concorrencial"] + ")"
        + " | " + df_gold["ds_formato_recomendado"]
    )

    df_gold.to_csv(GOLD_CSV, index=False)
    df_gold.to_csv(ETAPA3_DIR / "reports" / "gold_expansao_recomendacoes_iav.csv", index=False)

    # 3. Gerar Mapa Executivo em Alta Resolução com a Malha Poligonal Oficial do IBGE
    print("[3/5] Renderizando mapa espacial sobre a malha cartográfica oficial do IBGE (645 polígonos)...")
    fig, ax = plt.subplots(figsize=(10.8, 7.4), dpi=220)

    patches = []
    for feat in geojson_sp.get("features", []):
        geom = feat.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        if gtype == "Polygon":
            for ring in coords:
                patches.append(MplPolygon(ring, closed=True))
        elif gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    patches.append(MplPolygon(ring, closed=True))

    if patches:
        pc = PatchCollection(
            patches,
            facecolor="#f1f5f9",
            edgecolor="#cbd5e1",
            linewidth=0.35,
            zorder=1,
        )
        ax.add_collection(pc)

    sub_mon = df_gold[df_gold["ds_formato_recomendado"] == "Monitoramento / Polo Satelite"]
    ax.scatter(
        sub_mon["vl_longitude"],
        sub_mon["vl_latitude"],
        s=12,
        color="#94a3b8",
        alpha=0.45,
        label=f"Monitoramento / Polo Satélite (n={len(sub_mon)})",
        zorder=2,
    )

    format_styles = [
        ("Max Atacadista (Cash & Carry)", "#c8102e", "s", 65),
        ("Super Muffato / Gourmet", "#0b2958", "o", 55),
        ("Muffato Go / Proximidade", "#16a34a", "^", 85),
    ]
    for fmt_name, color, marker, base_size in format_styles:
        sub = df_gold[df_gold["ds_formato_recomendado"] == fmt_name]
        sizes = base_size + (sub["vl_score_iav"] ** 1.35) * 0.65
        ax.scatter(
            sub["vl_longitude"],
            sub["vl_latitude"],
            s=sizes,
            color=color,
            marker=marker,
            alpha=0.88,
            edgecolors="white",
            linewidth=0.7,
            label=f"{fmt_name} (n={len(sub)})",
            zorder=4,
        )

    top_cities = df_gold.sort_values("nr_ranking_iav").head(12)
    for _, row in top_cities.iterrows():
        ax.annotate(
            f"#{row['nr_ranking_iav']} {row['nm_municipio']} ({row['vl_score_iav']:.0f})",
            xy=(row["vl_longitude"], row["vl_latitude"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7.5,
            fontweight="bold",
            color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.18", fc="#ffffff", ec="#94a3b8", alpha=0.88, lw=0.5),
            zorder=6,
        )

    ax.set_title(
        "Mapa Oficial de Expansão (Malha IBGE + CNPJ Receita Federal) — Candidatos e Formatos em SP",
        fontsize=12.0,
        fontweight="bold",
        color="#0b2958",
        pad=12,
    )
    ax.set_xlabel("Longitude Geodésica Oficial IBGE (°O)", fontsize=10)
    ax.set_ylabel("Latitude Geodésica Oficial IBGE (°S)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(
        loc="lower left",
        frameon=True,
        fontsize=9,
        title="Formato Recomendado (Malha Oficial IBGE servicodados.ibge.gov.br)",
        title_fontsize=9.0,
    )
    fig.tight_layout()

    map_png = FIG_DIR / "06_mapa_candidatos_expansao_sp.png"
    fig.savefig(map_png)
    plt.close(fig)
    (ETAPA3_DIR / "reports" / map_png.name).write_bytes(map_png.read_bytes())
    (ETAPA4_DIR / "reports" / map_png.name).write_bytes(map_png.read_bytes())
    print(f"[OK] Mapa cartográfico oficial salvo em: {map_png}")

    # 4. Atualizar tabela Gold e criar Views Geoespaciais no BigQuery
    print("[4/5] Atualizando tabela Gold e Views com tipo nativo GEOGRAPHY no BigQuery...")
    subprocess.run(
        [
            "bq", f"--location={LOCATION}", "load",
            "--replace",
            "--autodetect",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            f"{PROJECT_ID}:muffato_gold.expansao_recomendacoes_iav",
            str(GOLD_CSV),
        ],
        check=True,
    )

    sql_views = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.muffato_gold.vw_painel_executivo_expansao` AS
    SELECT
      nr_ranking_iav,
      cd_municipio,
      cd_municipio_receita_federal,
      nm_municipio,
      nr_ddd,
      nm_regiao_metropolitana,
      CONCAT(nm_municipio, ', São Paulo, Brasil') AS ds_localizacao_mapa,
      vl_latitude,
      vl_longitude,
      ds_lat_long,
      ST_GEOGPOINT(vl_longitude, vl_latitude) AS geo_ponto_municipio,
      ds_rotulo_mapa,
      ds_status_candidato,
      nm_regiao_intermediaria,
      nm_mesorregiao,
      ds_porte_populacional,
      ds_vocacao_economica,
      qt_populacao_residente,
      vl_densidade_demografica_hab_km2,
      vl_massa_salarial_anual_mil_reais,
      vl_massa_salarial_per_capita_reais,
      vl_salario_medio_mensal_reais,
      vl_pib_per_capita_reais,
      vl_pib_total_mil_reais,
      qt_concorrentes_hipermercados,
      qt_concorrentes_supermercados,
      qt_concorrentes_atacadistas,
      qt_minimercados_mercearias,
      qt_concorrentes_diretos_total,
      vl_concorrentes_por_10k_hab,
      ds_saturacao_concorrencial,
      vl_score_pilar_demografico,
      vl_score_pilar_renda,
      vl_score_pilar_economia,
      vl_score_pilar_empresarial,
      vl_score_iav,
      ds_cluster_socioeconomico,
      ds_formato_recomendado,
      fx_capex_estimado,
      vl_confianca_recomendacao
    FROM `{PROJECT_ID}.muffato_gold.expansao_recomendacoes_iav`
    ORDER BY nr_ranking_iav ASC;

    CREATE OR REPLACE VIEW `{PROJECT_ID}.muffato_gold.vw_mapa_candidatos_expansao` AS
    SELECT *
    FROM `{PROJECT_ID}.muffato_gold.vw_painel_executivo_expansao`
    WHERE ds_formato_recomendado != 'Monitoramento / Polo Satelite'
    ORDER BY nr_ranking_iav ASC;
    """
    subprocess.run(
        ["bq", "query", f"--project_id={PROJECT_ID}", "--use_legacy_sql=false", sql_views],
        check=True,
    )
    print("[OK] Views 'vw_painel_executivo_expansao' e 'vw_mapa_candidatos_expansao' atualizadas com coordenadas oficiais IBGE!")

    # 5. Logar o novo mapa também no MLflow Docker
    print("[5/5] Anexando mapa oficial IBGE aos artefatos do MLflow Docker (http://127.0.0.1:5050)...")
    try:
        mlflow.set_tracking_uri("http://127.0.0.1:5050")
        exp = mlflow.get_experiment_by_name("Muffato_SP_Etapa3_4_Recomendador_Formatos_Loja")
        if exp:
            runs = mlflow.search_runs(experiment_ids=[exp.experiment_id], filter_string="tags.status_modelo = 'PRODUCTION_CHAMPION'")
            if not runs.empty:
                champ_run_id = runs.iloc[0]["run_id"]
                with mlflow.start_run(run_id=champ_run_id):
                    mlflow.log_artifact(str(map_png), artifact_path="plots_diagnostico")
                print(f"[OK] Mapa oficial anexado à run campeã ({champ_run_id}) no MLflow!")
    except Exception as e:
        print(f"[Aviso] Não foi possível anexar ao MLflow: {e}")


if __name__ == "__main__":
    enrich_geospatial_and_sync()
