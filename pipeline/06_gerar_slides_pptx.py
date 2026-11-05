#!/usr/bin/env python3
"""
Geração automatizada das apresentações executivas em PowerPoint (.pptx)
para a Etapa 3 (Modelagem & IAV v3.0 com Concorrentes CNPJ) e
Etapa 4 (Governança de IA, MLOps Docker MLflow & Monitoramento de Drift).
Segue o mesmo padrão visual corporativo da Etapa 2 (Muffato Navy & Red).
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

COLOR_NAVY = RGBColor(11, 41, 88)       # #0B2958 - Muffato Navy
COLOR_RED = RGBColor(200, 16, 46)       # #C8102E - Muffato Red
COLOR_CARD_BG = RGBColor(250, 251, 253) # #FAFBFD - Card Background
COLOR_CARD_BORDER = RGBColor(218, 224, 233)
COLOR_TEXT_DARK = RGBColor(30, 41, 59)
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUBTITLE = RGBColor(215, 228, 248)

BASE_DIR = Path(__file__).resolve().parents[2]
FIG_DIR = BASE_DIR / "ambiente_final" / "reports" / "fig"
ETAPA3_PPTX = BASE_DIR / "etapa_3" / "slides" / "apresentacao_etapa3.pptx"
ETAPA4_PPTX = BASE_DIR / "etapa_4" / "slides" / "apresentacao_etapa4.pptx"


def add_header(slide, title_text: str, subtitle_text: str):
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.10))
    header.fill.solid()
    header.fill.fore_color.rgb = COLOR_NAVY
    header.line.color.rgb = COLOR_NAVY

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.10), Inches(13.333), Inches(0.045))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_RED
    line.line.color.rgb = COLOR_RED

    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.12), Inches(12.1), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Arial"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE

    p2 = tf.add_paragraph()
    p2.text = subtitle_text
    p2.font.name = "Arial"
    p2.font.size = Pt(11)
    p2.font.color.rgb = COLOR_SUBTITLE


def add_footer(slide, section_name: str, slide_num: int, total_slides: int):
    footer_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.05), Inches(13.333), Inches(0.45))
    footer_bg.fill.solid()
    footer_bg.fill.fore_color.rgb = RGBColor(241, 245, 249)
    footer_bg.line.color.rgb = RGBColor(226, 232, 240)

    tb_l = slide.shapes.add_textbox(Inches(0.6), Inches(7.12), Inches(6.5), Inches(0.32))
    p_l = tb_l.text_frame.paragraphs[0]
    p_l.text = "UEL | Governança de TI e de Dados · Grupo Muffato (645 Municípios SP)"
    p_l.font.name = "Arial"
    p_l.font.size = Pt(9)
    p_l.font.bold = True
    p_l.font.color.rgb = COLOR_TEXT_MUTED

    tb_r = slide.shapes.add_textbox(Inches(7.2), Inches(7.12), Inches(5.5), Inches(0.32))
    p_r = tb_r.text_frame.paragraphs[0]
    p_r.alignment = PP_ALIGN.RIGHT
    p_r.text = f"{section_name}  |  {slide_num}/{total_slides}"
    p_r.font.name = "Arial"
    p_r.font.size = Pt(9.5)
    p_r.font.bold = True
    p_r.font.color.rgb = COLOR_NAVY


def add_card(slide, left: float, top: float, width: float, height: float, title: str, bullets: list[str]):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_CARD_BG
    box.line.color.rgb = COLOR_CARD_BORDER

    tb = slide.shapes.add_textbox(Inches(left + 0.18), Inches(top + 0.14), Inches(width - 0.36), Inches(height - 0.28))
    tf = tb.text_frame
    tf.word_wrap = True

    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = "Arial"
    p_title.font.size = Pt(13)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_NAVY

    for item in bullets:
        p = tf.add_paragraph()
        p.text = f"• {item}"
        p.font.name = "Arial"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(5)


def build_etapa3_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    total = 6

    # Slide 1: Capa
    s1 = prs.slides.add_slide(blank)
    add_header(s1, "Etapa 3 — Desenvolvimento da Solução Analítica & Machine Learning",
               "Expansão Estratégica do Grupo Muffato em SP (645 Municípios) · IBGE + Concorrentes Receita Federal (gov.br)")
    add_card(s1, 0.6, 1.5, 12.1, 2.2, "Contexto e Evolução do Ativo Governado (Silver v3.0)", [
        "Organização Beneficiária: Grupo Muffato (Alocação de CAPEX de R$ 5M a R$ 60M por loja no Estado de São Paulo).",
        "Atendendo à recomendação do Prof. Dr. André Menolli, integramos os Dados Abertos de CNPJ da Receita Federal (gov.br) na camada Silver v3.0.",
        "Total mapeado em SP: 1.570 Hipermercados, 11.062 Supermercados, 7.917 Atacadistas/Atacarejos e 82.606 Minimercados/Mercearias (demanda B2B).",
        "Equipe: Guilherme Terziotti, Lucas Silva e Marcos Beregula | Docente: Prof. Dr. André Menolli (UEL).",
    ])
    add_card(s1, 0.6, 4.0, 5.9, 2.7, "Pipeline Estruturado sem Data Leakage", [
        "1. Dados: 645 municípios x 39 atributos governados (BigQuery Silver).",
        "2. Validação: 0% nulos, chaves IBGE únicas e contadores CNPJ íntegros.",
        "3. Preparação: train_test_split (75%/25%) ANTES do fit do RobustScaler.",
        "4. Modelos: K-Means / Ward (Clusterização) + Random Forest (Formatos).",
    ])
    add_card(s1, 6.8, 4.0, 5.9, 2.7, "Os 3 Produtos Analíticos da Etapa 3", [
        "1. Segmentação Socioeconômica e Concorrencial (k=4 clusters).",
        "2. Índice de Atratividade Varejista (IAV v3.0 de 0 a 100 pontos).",
        "3. Recomendador de Bandeira: Max Atacadista, Super Muffato ou Muffato Go.",
        "4. Filtragem automática de praças saturadas (> 8,5 concorrentes/10k hab).",
    ])
    add_footer(s1, "Etapa 3 · Visão Geral & Concorrentes CNPJ", 1, total)

    # Slide 2: Clusterização e Silhouette
    s2 = prs.slides.add_slide(blank)
    add_header(s2, "1. Segmentação Não Supervisionada de Praças (K-Means vs. Ward)",
               "Avaliação sistemática de k in [3, 4, 5, 6] sobre 12 variáveis socioeconômicas e concorrenciais")
    s2.shapes.add_picture(str(FIG_DIR / "01_curva_silhouette_clusters.png"), Inches(0.6), Inches(1.45), width=Inches(6.0))
    s2.shapes.add_picture(str(FIG_DIR / "02_pca_clusters_sp.png"), Inches(6.8), Inches(1.45), width=Inches(5.9))
    add_card(s2, 0.6, 5.35, 12.1, 1.5, "Interpretação Executiva dos 4 Clusters Selecionados (k=4)", [
        "C1 (Polos Dinâmicos & Industriais) | C2 (Centros Regionais de Serviços) | C3 (Mercados Intermediários em Expansão) | C4 (Pequeno Porte / Agro).",
        "Transformação Log10 + RobustScaler protege os centróides contra distorções extremas (ex: capital São Paulo e enclave petroquímico de Paulínia).",
    ])
    add_footer(s2, "Etapa 3 · Clusterização Não Supervisionada", 2, total)

    # Slide 3: Formulação do IAV v3.0
    s3 = prs.slides.add_slide(blank)
    add_header(s3, "2. Índice de Atratividade Varejista (IAV v3.0) com Pressão Competitiva",
               "Combinação multicritério ponderada [0 a 100] premiando demanda B2B e penalizando saturação de concorrentes")
    add_card(s3, 0.6, 1.5, 5.9, 2.5, "Pilar 1: Demografia (30%) & Pilar 2: Poder de Compra (30%)", [
        "Pilar Demográfico (30%): 70% Log10(População) + 30% Log10(Densidade hab/km²).",
        "Pilar Poder de Compra (30%): 65% Massa Salarial Formal per capita + 35% Salário Médio Mensal.",
        "Corrige a distorção de enclaves de PIB (mede renda que efetivamente circula no varejo).",
    ])
    add_card(s3, 6.8, 1.5, 5.9, 2.5, "Pilar 3: Economia (25%) & Pilar 4: Oportunidade CNPJ (15%)", [
        "Pilar Econômico (25%): 45% Log10(PIB Total) + 25% PIB per capita + 30% VAB Serviços.",
        "Pilar Empresarial & Concorrência (15%): Combina densidade de empresas + Minimercados B2B (CNAE 4712-1/00) + Oportunidade de Oceano Azul (1 - Saturação Concorrencial).",
    ])
    add_card(s3, 0.6, 4.25, 12.1, 2.5, "Regras de Alocação de Formato de Loja Calibradas pela Concorrência (Receita Federal)", [
        "• Muffato Go / Proximidade: Densidade > 2.200 hab/km², IAV >= 48 e saturação <= 8,5 concorrentes/10k hab.",
        "• Super Muffato / Gourmet: População >= 40k, Salário >= R$ 2.900, Serviços >= 45% e saturação <= 6,5 concorrentes/10k hab (ou <= 3 hipermercados).",
        "• Max Atacadista (Cash & Carry): População >= 70k ou Massa Salarial >= R$ 800M, com forte base de minimercados B2B (>= 60 mercearias) ou baixa presença de atacarejos.",
    ])
    add_footer(s3, "Etapa 3 · Scoring IAV v3.0 & Regras de Negócio", 3, total)

    # Slide 4: Classificação Supervisionada & Matriz de Confusão
    s4 = prs.slides.add_slide(blank)
    add_header(s4, "3. Classificador Supervisionado de Formatos & Evolução de Experimentos",
               "Comparação empírica entre algoritmos e versões de dados (v2.0 IBGE vs. v3.0 IBGE + Concorrentes CNPJ)")
    s4.shapes.add_picture(str(FIG_DIR / "03_matriz_confusao_formatos.png"), Inches(0.6), Inches(1.45), width=Inches(5.6))
    add_card(s4, 6.4, 1.45, 6.3, 5.3, "Rastreabilidade de Runs (BigQuery & MLflow)", [
        "• RUN-09 (v2.0 Baseline Majority): Accuracy = 77,16% | F1-Macro = 0,2178",
        "• RUN-12 (v2.0 Random Forest n=100): Accuracy = 97,53% | F1-Macro = 0,9454 | AUC = 0,9951",
        "• RUN-16 (v3.0 Logistic Regression + CNPJ): Accuracy = 89,51% | F1-Macro = 0,6757 | AUC = 0,9706",
        "• RUN-17 (v3.0 Decision Tree + CNPJ): Accuracy = 92,59% | F1-Macro = 0,7582 | AUC = 0,9240",
        "• RUN-18 (v3.0 Random Forest n=100 + CNPJ): Accuracy = 93,83% | F1-Macro = 0,8490 | AUC = 0,9812",
        "• RUN-19 (v3.0 Random Forest n=200 + CNPJ): Accuracy = 95,06% | F1-Macro = 0,8480 | AUC = 0,9830",
        "• RUN-20 (v3.0 Gradient Boosting + CNPJ): Accuracy = 93,21% | F1-Macro = 0,7640 | AUC = 0,9784",
        "Justificativa: F1-Macro avalia o equilíbrio nas classes minoritárias de alta relevância financeira (CAPEX de R$ 40M a R$ 60M).",
    ])
    add_footer(s4, "Etapa 3 · Avaliação Supervisionada", 4, total)

    # Slide 5: Mapa de Candidatos
    s5 = prs.slides.add_slide(blank)
    add_header(s5, "4. Mapa Macro-Locacional dos 139 Municípios Candidatos em SP",
               "Integração nativa com Google BigQuery (ST_GEOGPOINT) e Looker Studio")
    s5.shapes.add_picture(str(FIG_DIR / "06_mapa_candidatos_expansao_sp.png"), Inches(0.6), Inches(1.35), width=Inches(7.3))
    add_card(s5, 8.1, 1.45, 4.6, 5.3, "Top Candidatos Prioritários (IAV v3.0)", [
        "#1 São Paulo (IAV 100,0) — Muffato Go",
        "#2 Barueri (IAV 82,9) — Muffato Go",
        "#3 Osasco (IAV 80,7) — Muffato Go",
        "#4 Campinas (IAV 78,2 | 4,46 conc/10k) — Super Muffato",
        "#5 Jundiaí (IAV 74,5 | 4,04 conc/10k) — Super Muffato",
        "#6 Paulínia (IAV 73,5 | 3,44 conc/10k) — Max Atacadista",
        "#7 São Bernardo do Campo (IAV 72,4) — Super Muffato",
        "#11 Santos (IAV 67,7 | 3,39 conc/10k) — Super Muffato",
        "#14 São José dos Campos (IAV 65,6) — Super Muffato",
    ])
    add_footer(s5, "Etapa 3 · Mapa Geoespacial de Expansão", 5, total)

    # Slide 6: Conclusão Etapa 3
    s6 = prs.slides.add_slide(blank)
    add_header(s6, "Conclusão da Etapa 3 & Transição para Governança MLOps (Etapa 4)",
               "Alinhamento Estratégico entre Negócio, Engenharia de Dados e Ciência de Dados")
    add_card(s6, 0.6, 1.5, 12.1, 5.1, "Síntese das Entregas da Etapa 3", [
        "1. Pipeline Fim a Fim Executado: Ingestão Receita Federal CNPJ (Bronze) -> Ativo Governado v3.0 (Silver, 39 colunas) -> Recomendações IAV (Gold).",
        "2. Modelos Serializados e Reprodutíveis: K-Means (k=4) e Random Forest (95,06% Accuracy / 0,9830 ROC-AUC) salvos em .joblib e no MLflow.",
        "3. Decisão Executiva Acionável: Identificação de 139 praças prioritárias em SP com filtro explícito contra saturação concorrencial.",
        "4. Ponte para a Etapa 4: Versionamento no MLflow Docker (localhost:5050), Explicabilidade Art. 20 LGPD e Monitoramento Contínuo de Data Drift (PSI).",
    ])
    add_footer(s6, "Etapa 3 · Conclusão", 6, total)

    ETAPA3_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(ETAPA3_PPTX))
    print(f"[OK] Apresentação Etapa 3 gerada em: {ETAPA3_PPTX}")


def build_etapa4_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    total = 6

    # Slide 1: Capa Etapa 4
    s1 = prs.slides.add_slide(blank)
    add_header(s1, "Etapa 4 — Governança da Solução de IA, MLOps & Monitoramento",
               "Ciclo de Vida do Modelo (MLflow Docker + Google BigQuery + Looker Studio) · Grupo Muffato SP")
    add_card(s1, 0.6, 1.5, 12.1, 2.3, "Objetivo da Etapa 4: Gerenciar o Ciclo de Vida da Solução de IA", [
        "Demonstrar na prática a diferença entre apenas treinar um algoritmo e governar seu ciclo de vida completo em produção.",
        "Arquitetura Híbrida Custo Zero: Google Cloud BigQuery (projeto-governanca: Bronze, Silver v3.0, Gold) + Servidor MLflow 3.18 em Docker (localhost:5050).",
        "Evolução Rastreada: Transição auditável da Versão 1 (v2.0 só IBGE) para a Versão 2 (v3.0 IBGE + Concorrentes Receita Federal CNPJ).",
        "Equipe: Guilherme Terziotti, Lucas Silva e Marcos Beregula | Docente: Prof. Dr. André Menolli (UEL).",
    ])
    add_card(s1, 0.6, 4.05, 5.9, 2.7, "Os 4 Pilares de MLOps Implementados", [
        "1. Versionamento: Git + SHA-256 + BigQuery + MLflow Model Registry.",
        "2. Experiment Tracking: 28 execuções comparando v2.0 vs. v3.0 no Docker.",
        "3. Explicabilidade (Art. 20 LGPD): Importância Gini e Permutação.",
        "4. Monitoramento de Drift: PSI e Teste KS automatizados no BigQuery.",
    ])
    add_card(s1, 6.8, 4.05, 5.9, 2.7, "As 7 Entregas do Pacote de Governança", [
        "1. Repositório Integrado (ambiente_final/) | 2. Dataset v3.0 (39 variáveis)",
        "3. Log de Experimentos (MLflow + BQ) | 4. Model Card Oficial (10 seções)",
        "5. Plano de Monitoramento (PSI/KS) | 6. Matriz Integrada de Riscos",
        "7. Relatório Executivo Final & Mapa Interativo no Looker Studio.",
    ])
    add_footer(s1, "Etapa 4 · Governança de IA & MLOps", 1, total)

    # Slide 2: Versionamento & MLflow Tracking (v2.0 vs v3.0)
    s2 = prs.slides.add_slide(blank)
    add_header(s2, "1. Versionamento e Experiment Tracking no MLflow Docker (localhost:5050)",
               "Rastreabilidade ponta a ponta: Experimento -> Parâmetros -> Métricas -> Modelo -> Artefatos")
    add_card(s2, 0.6, 1.5, 5.9, 5.2, "Controle de Versão em 4 Níveis", [
        "• Código: Pipelines numerados (01 a 05) + Dockerfile + docker-compose.yml.",
        "• Dados (SHA-256): Evolução documentada de v2.0-ibge-2022-silver (32 colunas) para v3.0-ibge-cnpj-concorrentes (39 colunas com Receita Federal).",
        "• Modelos (MLflow Registry):",
        "   - Muffato_KMeans_Segmentacao_SP (Version 1 -> Version 2)",
        "   - Muffato_RandomForest_Recomendador_Formatos (Version 1 -> Version 2)",
        "• Configurações: Parametrização centralizada em config/settings.yaml.",
    ])
    add_card(s2, 6.8, 1.5, 5.9, 5.2, "Artefatos Anexados à Run Campeã no MLflow", [
        "• Gráficos de Diagnóstico (Curva Silhouette, PCA 2D, Matriz de Confusão).",
        "• Gráfico de Explicabilidade Algorítmica (Art. 20 LGPD).",
        "• Gráfico de Monitoramento de Data Drift (PSI).",
        "• Mapa Geoespacial dos 139 Candidatos de Expansão em SP.",
        "• Pacote Completo de Governança (model_card.md, plano_monitoramento.md, matriz_riscos.md, dicionario_dados.md, settings.yaml).",
        "• Schema de Assinatura (infer_signature) validando entradas e saídas.",
    ])
    add_footer(s2, "Etapa 4 · Versionamento & MLflow Registry", 2, total)

    # Slide 3: Explicabilidade Art. 20 LGPD
    s3 = prs.slides.add_slide(blank)
    add_header(s3, "2. Explicabilidade Algorítmica e Conformidade com o Artigo 20 da LGPD",
               "Auditoria quantitativa da influência de cada variável socioeconômica e concorrencial na decisão")
    s3.shapes.add_picture(str(FIG_DIR / "04_explicabilidade_lgpd_art20.png"), Inches(0.6), Inches(1.45), width=Inches(7.0))
    add_card(s3, 7.8, 1.45, 4.9, 5.3, "Transparência Perante o Conselho (IBGC)", [
        "• Art. 20 LGPD: Direito à revisão e explicação de decisões automatizadas.",
        "• Top Variáveis de Escala: PIB Total (20,8%), População (17,3%) e Densidade Demográfica (13,4%).",
        "• Impacto das Novas Variáveis CNPJ Receita Federal:",
        "   - qt_minimercados_mercearias (9,28% Gini): Define a viabilidade B2B do formato Max Atacadista.",
        "   - vl_concorrentes_por_10k_hab (4,58% Gini): Atua como freio contra alocação de CAPEX em praças saturadas.",
    ])
    add_footer(s3, "Etapa 4 · Explicabilidade & LGPD Art. 20", 3, total)

    # Slide 4: Monitoramento de Drift (PSI & KS)
    s4 = prs.slides.add_slide(blank)
    add_header(s4, "3. Monitoramento Contínuo de Produção (Data Drift, Model Drift & Negócio)",
               "Detecção proativa de desvios de distribuição via Population Stability Index (PSI) e Teste KS")
    s4.shapes.add_picture(str(FIG_DIR / "05_monitoramento_data_drift_psi.png"), Inches(0.6), Inches(1.45), width=Inches(7.0))
    add_card(s4, 7.8, 1.45, 4.9, 5.3, "Regras de Alerta e Gatilhos de Retreino", [
        "• PSI < 0,10 (Verde): Distribuição estável (Demografia e PIB Total).",
        "• 0,10 <= PSI < 0,25 ou p-KS < 0,05 (Amarelo — Alerta):",
        "   - Detectado em vl_concorrentes_por_10k_hab (PSI = 0,0993 / p < 0,05) devido à abertura de novas lojas rivais na Receita Federal.",
        "   - Ação: Atualizar ingestão Bronze CNPJ e recalibrar RobustScaler.",
        "• PSI >= 0,25 (Vermelho — Crítico):",
        "   - Detectado em vl_salario_medio_mensal_reais (PSI = 0,5355) por inflação nominal.",
        "   - Ação: Gatilho imediato de retreinamento do modelo.",
    ])
    add_footer(s4, "Etapa 4 · Monitoramento Contínuo & Drift", 4, total)

    # Slide 5: Matriz de Riscos e Mapa Looker Studio
    s5 = prs.slides.add_slide(blank)
    add_header(s5, "4. Matriz de Riscos Integrada & Painel Geoespacial no Looker Studio",
               "Conectando BigQuery (muffato_gold.vw_mapa_candidatos_expansao) à tomada de decisão executiva")
    s5.shapes.add_picture(str(FIG_DIR / "06_mapa_candidatos_expansao_sp.png"), Inches(0.6), Inches(1.4), width=Inches(6.5))
    add_card(s5, 7.3, 1.45, 5.4, 5.3, "Mitigação de Riscos (Dados, Modelo, Ética e Negócio)", [
        "• Risco de Enclave Industrial (Paulínia): Mitigado pelo peso de 30% da Massa Salarial per capita e RobustScaler.",
        "• Risco de Cegueira Concorrencial: Mitigado pela ingestão de 20.549 concorrentes diretos da Receita Federal (gov.br).",
        "• Risco de Data Leakage: Mitigado pela ordenação estrita (split antes do scaling em Pipeline).",
        "• Risco Ético / Exclusão Territorial: Estratégia multiformato atende desde centros densos (Muffato Go) até cidades médias/B2B (Max Atacadista).",
        "• Princípio Human-in-the-Loop: Recomendação consultiva auditável para deliberação final do Comitê de Expansão.",
    ])
    add_footer(s5, "Etapa 4 · Riscos & Painel Looker Studio", 5, total)

    # Slide 6: Fechamento
    s6 = prs.slides.add_slide(blank)
    add_header(s6, "Conclusão Geral — Governança de TI, Dados e IA na Prática",
               "Alinhamento integral aos frameworks IBGC, SAM, COBIT 2019, DAMA-DMBOK2, ISO 38500 e LGPD")
    add_card(s6, 0.6, 1.5, 12.1, 5.1, "Destaques Finais da Solução Entregue", [
        "1. Arquitetura Lakehouse Operacional no GCP (projeto-governanca): Camadas Bronze, Silver v3.0 e Gold com custo zero (Free Tier).",
        "2. Integração Real de Concorrentes (gov.br / Receita Federal): Mapeamento completo por CNAE em todos os 645 municípios paulistas.",
        "3. MLOps em Container Docker (http://localhost:5050): Comparação transparente entre v2.0 e v3.0 no MLflow Model Registry.",
        "4. Visualização Geoespacial Executiva: Views nativas com ST_GEOGPOINT prontas para filtro interativo de saturação e CAPEX no Looker Studio.",
    ])
    add_footer(s6, "Etapa 4 · Encerramento", 6, total)

    ETAPA4_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(ETAPA4_PPTX))
    print(f"[OK] Apresentação Etapa 4 gerada em: {ETAPA4_PPTX}")


if __name__ == "__main__":
    build_etapa3_pptx()
    build_etapa4_pptx()

