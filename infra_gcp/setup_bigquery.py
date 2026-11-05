#!/usr/bin/env python3
"""
Provisionamento e Sincronização das Camadas Bronze e Silver no Google BigQuery
Projeto GCP: projeto-governanca (Custo Zero / Free Tier)
Aplica automaticamente o Dicionário de Dados nos metadados das 32 colunas da camada Silver.
"""

import csv
import json
import os
import subprocess
from pathlib import Path

PROJECT_ID = "projeto-governanca"
LOCATION = "US"

BASE_DIR = Path(__file__).resolve().parents[2]
ETAPA2_DIR = BASE_DIR / "etapa_2"
AMBIENTE_FINAL_DIR = BASE_DIR / "ambiente_final"

RAW_CSV = ETAPA2_DIR / "data" / "raw" / "ibge_sp_raw_consolidado.csv"
SILVER_CSV = ETAPA2_DIR / "data" / "processed" / "muffato_expansao_sp_governado.csv"
DICT_CSV = ETAPA2_DIR / "governanca" / "dicionario_dados.csv"
SCHEMA_JSON_PATH = AMBIENTE_FINAL_DIR / "infra_gcp" / "schema_silver_bigquery.json"


def map_bq_type(tipo_str: str, col_name: str) -> str:
    t = tipo_str.lower()
    if col_name.startswith("cd_"):
        return "STRING"
    if "integer" in t or col_name.startswith("qt_"):
        return "INT64"
    if "float" in t or col_name.startswith("vl_") or col_name.startswith("pc_"):
        return "FLOAT64"
    return "STRING"


def build_silver_schema() -> list:
    """Lê o dicionario_dados.csv e gera o schema JSON do BigQuery com descrições."""
    schema = []
    with open(DICT_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            campo = row["Campo"].strip()
            significado = row["Significado"].strip()
            dominio = row["Domínio"].strip()
            qualidade = row["Qualidade"].strip()
            bq_type = map_bq_type(row["Tipo"], campo)
            desc = f"{significado} | Domínio: {dominio} | Qualidade: {qualidade}"
            schema.append({
                "name": campo,
                "type": bq_type,
                "mode": "REQUIRED",
                "description": desc[:1024]
            })
    with open(SCHEMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"[OK] Schema BigQuery com Dicionário de Dados salvo em: {SCHEMA_JSON_PATH}")
    return schema


def run_cmd(cmd: list):
    print(f"Executando: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"STDERR: {res.stderr}")
        raise RuntimeError(f"Erro ao executar comando: {res.stdout}\n{res.stderr}")
    if res.stdout.strip():
        print(res.stdout.strip())


def sync_bronze_and_silver():
    build_silver_schema()

    # 1. Carregar tabela Bronze (ibge_sp_raw_consolidado)
    print("\n--- 1. Publicando Camada BRONZE no BigQuery ---")
    run_cmd([
        "bq", f"--location={LOCATION}", "load",
        "--replace",
        "--autodetect",
        "--source_format=CSV",
        "--skip_leading_rows=1",
        f"{PROJECT_ID}:muffato_bronze.ibge_sp_raw_consolidado",
        str(RAW_CSV)
    ])

    # 2. Carregar tabela Silver com Schema e Dicionário de Dados
    print("\n--- 2. Publicando Camada SILVER Governada no BigQuery ---")
    run_cmd([
        "bq", f"--location={LOCATION}", "load",
        "--replace",
        "--source_format=CSV",
        "--skip_leading_rows=1",
        f"{PROJECT_ID}:muffato_silver.municipios_sp_governado",
        str(SILVER_CSV),
        str(SCHEMA_JSON_PATH)
    ])

    # 3. Atualizar descrição e labels da tabela Silver
    run_cmd([
        "bq", "update",
        "--description", "Ativo de Dados Governado (Camada Silver) - 645 Municipios de SP x 32 Variaveis auditadas (DAMA-DMBOK)",
        "--set_label", "camada:silver",
        "--set_label", "governanca:dama_dmbok",
        "--set_label", "organizacao:grupo_muffato",
        f"{PROJECT_ID}:muffato_silver.municipios_sp_governado"
    ])

    print("\n[SUCESSO] Camadas Bronze e Silver carregadas e documentadas no BigQuery!")


if __name__ == "__main__":
    sync_bronze_and_silver()

