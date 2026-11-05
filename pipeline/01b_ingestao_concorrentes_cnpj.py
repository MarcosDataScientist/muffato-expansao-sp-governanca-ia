#!/usr/bin/env python3
"""
Ingestão e Governança de Dados de Concorrentes (CNPJ / Receita Federal por CNAE)
Integra os estabelecimentos ativos de Hipermercados (4711-3/01), Supermercados (4711-3/02),
Atacadistas/Atacarejos (4691-5/00, 4639-7/01, 4639-7/02) e Minimercados (4712-1/00)
nas camadas Bronze e Silver (v3.0) do BigQuery e do repositório local.
"""

import json
import subprocess
from pathlib import Path
import pandas as pd

PROJECT_ID = "projeto-governanca"
LOCATION = "US"

AMBIENTE_DIR = Path(__file__).resolve().parents[1]

RAW_CNPJ_CSV = AMBIENTE_DIR / "reports" / "cnpj_concorrentes_sp_raw.csv"
SILVER_V2_CSV = AMBIENTE_DIR / "data" / "muffato_expansao_sp_governado_v2_ibge.csv"
SILVER_V3_CSV = AMBIENTE_DIR / "reports" / "municipios_sp_governado_v3_concorrentes.csv"
SCHEMA_JSON_PATH = AMBIENTE_DIR / "infra_gcp" / "schema_silver_bigquery.json"


def run_cnpj_ingestion_and_silver_v3():
    print("=== INICIANDO INGESTÃO E GOVERNANÇA DE CONCORRENTES (RECEITA FEDERAL CNPJ) ===")
    df_raw = pd.read_csv(RAW_CNPJ_CSV, dtype={"cd_municipio": str, "cnae_fiscal_principal": str})
    print(f"[1/4] Registros brutos por Município x CNAE carregados: {len(df_raw)} linhas.")

    # 1. Publicar tabela bruta na camada Bronze do BigQuery
    print("[2/4] Publicando tabela bruta na camada BRONZE (muffato_bronze.cnpj_concorrentes_sp_raw)...")
    subprocess.run(
        [
            "bq", f"--location={LOCATION}", "load",
            "--replace",
            "--autodetect",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            f"{PROJECT_ID}:muffato_bronze.cnpj_concorrentes_sp_raw",
            str(RAW_CNPJ_CSV),
        ],
        check=True,
    )

    # 2. Pivotar e agregar por município (645 municípios de SP)
    print("[3/4] Agregando CNAEs de concorrentes e calculando indicadores de saturação...")
    piv = (
        df_raw.pivot_table(
            index="cd_municipio",
            columns="cnae_fiscal_principal",
            values="qt_estabelecimentos_ativos",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    for cnae in ["4711301", "4711302", "4712100", "4691500", "4639701", "4639702"]:
        if cnae not in piv.columns:
            piv[cnae] = 0

    piv["qt_concorrentes_hipermercados"] = piv["4711301"].astype(int)
    piv["qt_concorrentes_supermercados"] = piv["4711302"].astype(int)
    piv["qt_concorrentes_atacadistas"] = (piv["4691500"] + piv["4639701"] + piv["4639702"]).astype(int)
    piv["qt_minimercados_mercearias"] = piv["4712100"].astype(int)
    piv["qt_concorrentes_diretos_total"] = (
        piv["qt_concorrentes_hipermercados"]
        + piv["qt_concorrentes_supermercados"]
        + piv["qt_concorrentes_atacadistas"]
    ).astype(int)

    cols_keep = [
        "cd_municipio",
        "qt_concorrentes_hipermercados",
        "qt_concorrentes_supermercados",
        "qt_concorrentes_atacadistas",
        "qt_minimercados_mercearias",
        "qt_concorrentes_diretos_total",
    ]
    df_cnae_mun = piv[cols_keep].copy()

    # Cruzar com a base Silver v2
    df_silver = pd.read_csv(
        SILVER_V2_CSV,
        dtype={
            "cd_municipio": str,
            "cd_microrregiao": str,
            "cd_mesorregiao": str,
            "cd_regiao_imediata": str,
            "cd_regiao_intermediaria": str,
        },
    )
    # Remover colunas de concorrência se já existirem
    for col in cols_keep[1:] + ["vl_concorrentes_por_10k_hab", "ds_saturacao_concorrencial"]:
        if col in df_silver.columns:
            df_silver.drop(columns=[col], inplace=True)

    df_v3 = df_silver.merge(df_cnae_mun, on="cd_municipio", how="left")
    for col in cols_keep[1:]:
        df_v3[col] = df_v3[col].fillna(0).astype(int)

    # Índice de Densidade Concorrencial (Lojas diretas de grande/médio porte por 10.000 habitantes)
    df_v3["vl_concorrentes_por_10k_hab"] = (
        (df_v3["qt_concorrentes_diretos_total"] / df_v3["qt_populacao_residente"].clip(lower=1)) * 10000.0
    ).round(2)

    q35 = df_v3["vl_concorrentes_por_10k_hab"].quantile(0.35)
    q75 = df_v3["vl_concorrentes_por_10k_hab"].quantile(0.75)

    def classificar_saturacao(v: float) -> str:
        if v <= q35:
            return "Baixa Saturacao (Oceano Azul)"
        elif v <= q75:
            return "Concorrencia Moderada"
        return "Alta Saturacao Concorrencial"

    df_v3["ds_saturacao_concorrencial"] = df_v3["vl_concorrentes_por_10k_hab"].apply(classificar_saturacao)

    df_v3.to_csv(SILVER_V3_CSV, index=False)
    print(f"[OK] Base Silver v3.0 gerada com {df_v3.shape[0]} municípios x {df_v3.shape[1]} variáveis governadas!")
    print(
        f"     Total Estadual SP -> Hipermercados: {df_v3['qt_concorrentes_hipermercados'].sum()} | "
        f"Supermercados: {df_v3['qt_concorrentes_supermercados'].sum()} | "
        f"Atacadistas: {df_v3['qt_concorrentes_atacadistas'].sum()} | "
        f"Minimercados B2B/Prox: {df_v3['qt_minimercados_mercearias'].sum()}"
    )

    # 3. Atualizar Schema JSON com descrições das 7 novas colunas de concorrência e subir para Silver no BigQuery
    print("[4/4] Atualizando Schema com Dicionário de Dados (39 colunas) na camada SILVER do BigQuery...")
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    existing_names = {col["name"] for col in schema}
    novas_colunas_schema = [
        {
            "name": "qt_concorrentes_hipermercados",
            "type": "INT64",
            "mode": "REQUIRED",
            "description": "Quantidade de hipermercados concorrentes ativos no municipio (Receita Federal CNAE 4711-3/01)",
        },
        {
            "name": "qt_concorrentes_supermercados",
            "type": "INT64",
            "mode": "REQUIRED",
            "description": "Quantidade de supermercados concorrentes ativos no municipio (Receita Federal CNAE 4711-3/02)",
        },
        {
            "name": "qt_concorrentes_atacadistas",
            "type": "INT64",
            "mode": "REQUIRED",
            "description": "Quantidade de atacadistas/atacarejos de alimentos e mercadorias ativos (CNAEs 4691-5/00, 4639-7/01, 4639-7/02)",
        },
        {
            "name": "qt_minimercados_mercearias",
            "type": "INT64",
            "mode": "REQUIRED",
            "description": "Quantidade de minimercados e mercearias ativas (CNAE 4712-1/00) - Clientes B2B do Atacarejo e concorrentes de proximidade",
        },
        {
            "name": "qt_concorrentes_diretos_total",
            "type": "INT64",
            "mode": "REQUIRED",
            "description": "Total de concorrentes diretos de medio e grande porte (Hipermercados + Supermercados + Atacadistas)",
        },
        {
            "name": "vl_concorrentes_por_10k_hab",
            "type": "FLOAT64",
            "mode": "REQUIRED",
            "description": "Indice de densidade concorrencial: Lojas de Hiper/Super/Atacadistas para cada 10.000 habitantes",
        },
        {
            "name": "ds_saturacao_concorrencial",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Classificacao do nivel de saturacao concorrencial da praca (Baixa Saturacao / Oceano Azul, Moderada, Alta Saturacao)",
        },
    ]

    for nc in novas_colunas_schema:
        if nc["name"] not in existing_names:
            schema.append(nc)

    with open(SCHEMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    subprocess.run(
        [
            "bq", f"--location={LOCATION}", "load",
            "--replace",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            f"{PROJECT_ID}:muffato_silver.municipios_sp_governado",
            str(SILVER_V3_CSV),
            str(SCHEMA_JSON_PATH),
        ],
        check=True,
    )
    print("[SUCESSO] Camada Silver v3.0 (39 variáveis com Concorrentes Receita Federal) publicada no BigQuery!")


if __name__ == "__main__":
    run_cnpj_ingestion_and_silver_v3()

