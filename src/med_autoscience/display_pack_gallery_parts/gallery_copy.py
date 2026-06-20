from __future__ import annotations

from dataclasses import dataclass

from med_autoscience.display_pack_gallery_catalog import TemplateRecord


@dataclass(frozen=True)
class CompositionCopy:
    title: str
    use_case: str
    central_message: str
    panel_plan: tuple[str, ...]
    evidence_note: str


@dataclass(frozen=True)
class EvidenceCopy:
    purpose: str
    data_requirement: str
    use_when: str


@dataclass(frozen=True)
class DesignCopy:
    purpose: str
    input_requirement: str
    use_when: str
    evidence_boundary: str


GALLERY_TITLE = "MAS 医学论文配图 Gallery"
GALLERY_SUBTITLE = (
    "这份画册展示 MAS 内置医学论文配图体系的默认工作方式：先用页面级图页方案组织论文论点，"
    "再分别选择非数据设计图起点和 R/ggplot2 数据证据图起点。"
)
GALLERY_SCOPE = (
    "所有示例均使用合成数据或示意性图页方案，用于评估模板覆盖、版式组织、统一风格和调用入口。"
    "真实论文使用时，MAS 根据论文问题、数据引用、统计定义和期刊要求继续调整布局、标签、配色和面板结构。"
)
GALLERY_WORKFLOW_STEPS = (
    ("1", "锁定论文论点", "明确本图要支撑的主要结论、目标人群、数据来源和统计量。"),
    ("2", "选择图页方案", "从页面级图页方案中选择最接近的叙事结构，确定主面板和辅助证据。"),
    ("3", "选择图件起点", "非数据设计图可走 SVG/Python/imagegen 辅助；数据证据图默认走 R/ggplot2，保证统计含义可追踪。"),
    ("4", "论文级打磨", "MAS 可重排面板、统一图例、调整配色和标签，并在最终稿前执行视觉与证据审查。"),
)


COMPOSITION_COPY: dict[str, CompositionCopy] = {
    "clinical_triptych_prediction": CompositionCopy(
        title="临床预测模型主图",
        use_case="适用于诊断、预后或风险预测模型的主结果图。",
        central_message="同时回答模型能否区分风险、概率是否校准、阈值使用是否具有临床净获益。",
        panel_plan=(
            "主面板呈现模型总体判别性能。",
            "辅助面板展示校准曲线、决策曲线和关键风险分层。",
            "统一图例、阈值和队列标注，避免 ROC、校准和临床效用之间语义割裂。",
        ),
        evidence_note="所有数据证据面板由程序化统计结果驱动，R/ggplot2 是默认起点。",
    ),
    "model_validation_dashboard": CompositionCopy(
        title="模型验证与泛化能力图页",
        use_case="适用于多队列验证、亚组稳定性、时间窗性能和模型复杂度说明。",
        central_message="集中说明模型在不同队列、亚组和评估口径下是否稳定可靠。",
        panel_plan=(
            "主面板展示内部与外部验证的核心性能摘要。",
            "辅助面板展示亚组森林图、校准或时间依赖性能。",
            "以共享图例和一致坐标减少重复解释，突出泛化能力而非堆叠指标。",
        ),
        evidence_note="保留队列、亚组、时间窗和统计量的来源引用，使验证摘要服务于泛化能力判断。",
    ),
    "schematic_led_composite": CompositionCopy(
        title="机制或流程引导图页",
        use_case="适用于研究设计、分析流程、机制假说或模型工作流与数据证据并置的图页。",
        central_message="先用清晰 schematic 建立读者理解框架，再用小型程序化证据面板支撑关键环节。",
        panel_plan=(
            "主面板展示机制、流程或系统结构。",
            "辅助面板放置定量验证、示例结果或关键分布。",
            "schematic 可以使用 SVG 或图像生成辅助，但不得替代统计证据。",
        ),
        evidence_note="设计面板强调表达力；数据分析面板由程序化结果生成并保留数据引用。",
    ),
    "image_plate_plus_quantification": CompositionCopy(
        title="图像板与定量证据图页",
        use_case="适用于病理、影像、空间组学或显微图像与定量比较并置。",
        central_message="将代表性图像、区域标注和定量结果放在同一叙事层级，避免只展示好看的图像。",
        panel_plan=(
            "主面板展示代表性图像或图像板。",
            "辅助面板展示定量分布、组间比较和模型输出。",
            "图像比例尺、ROI、分组颜色和统计图例保持一致。",
        ),
        evidence_note="图像面板采用表现力优先的版式，定量面板由程序化数据结果生成。",
    ),
    "asymmetric_genomics_figure": CompositionCopy(
        title="组学景观与功能后果图页",
        use_case="适用于突变、CNV、表达、通路富集或多组学主结果图。",
        central_message="用一个强主面板呈现分子模式，再用后果、通路和临床关联面板解释其意义。",
        panel_plan=(
            "主面板承载分子景观或矩阵模式。",
            "辅助面板展示富集、后果、效应估计或临床相关性。",
            "热图、点图和森林图共享调色逻辑，减少多组学图页的视觉漂移。",
        ),
        evidence_note="矩阵和热图类面板使用统一连续/发散色板，并在论文级审图时检查图例密度。",
    ),
    "single_cell_atlas_storyboard": CompositionCopy(
        title="单细胞或空间图谱图页",
        use_case="适用于细胞状态、空间区域、marker 表达和轨迹/组成变化的综合展示。",
        central_message="先说明细胞或空间结构，再展示 marker、组成和功能信号如何支持生物学解释。",
        panel_plan=(
            "主面板展示 UMAP/t-SNE/空间坐标等图谱结构。",
            "辅助面板展示 marker dotplot、signature heatmap 或组成变化。",
            "颜色、细胞类型命名和图例顺序在全图内保持一致。",
        ),
        evidence_note="降维图由原始特征矩阵或已审计 embedding workflow 生成，完整保留计算语义。",
    ),
}


EVIDENCE_CATEGORY_COPY: dict[str, tuple[str, str]] = {
    "Prediction Performance": (
        "预测性能",
        "用于呈现判别、校准、精确率-召回率和阈值相关性能。",
    ),
    "Clinical Utility": (
        "临床效用",
        "用于呈现不同阈值下的净获益、临床影响和决策价值。",
    ),
    "Time-to-Event": (
        "生存与时间事件",
        "用于呈现随访时间、风险分层、累积发生和时间依赖性能。",
    ),
    "Effect Estimate": (
        "效应估计",
        "用于呈现回归效应、亚组交互、变量路径和不确定性区间。",
    ),
    "Generalizability": (
        "外部验证与泛化",
        "用于呈现跨队列、亚组、中心或时间窗的稳定性。",
    ),
    "Data Geometry": (
        "数据结构与降维",
        "用于呈现样本分布、降维结构、差异特征和高维数据几何。",
    ),
    "Matrix Pattern": (
        "矩阵、热图与组学模式",
        "用于呈现表达、突变、CNV、marker、通路或细胞类型矩阵。",
    ),
    "Model Explanation": (
        "模型解释",
        "用于呈现全局与局部解释、特征贡献和个体预测依据。",
    ),
    "Model Audit": (
        "模型审计",
        "用于呈现模型复杂度、稳健性、特征治理和过拟合风险。",
    ),
}


DESIGN_COPY: dict[str, DesignCopy] = {
    "cohort_flow_figure": DesignCopy(
        "展示研究对象筛选、排除、纳入分析和结局分流的流程结构。",
        "需要 cohort source、纳排标准、每一步人数、排除原因、分析集和结局定义。",
        "用于 Figure 1、研究设计图、队列构建说明或补充流程图。",
        "人数和节点关系必须来自可追踪 source；该 shell 只负责流程表达，不承担模型性能或统计推断证据。",
    ),
    "submission_graphical_abstract": DesignCopy(
        "用简洁的图形摘要概括研究对象、核心终点、主要发现和提交材料中的视觉主线。",
        "需要论文核心结论、主要 cohort、关键 endpoint、最重要的结果数字和目标期刊图形摘要要求。",
        "用于 graphical abstract、submission companion、TOC-style overview 或编辑部要求的视觉摘要。",
        "可使用 SVG/Python composition 或 imagegen-assisted art direction 提升表现力，但真实结果数字必须来自已审计证据引用。",
    ),
}


EVIDENCE_COPY: dict[str, EvidenceCopy] = {
    "roc_curve_binary": EvidenceCopy(
        "展示二分类模型的判别能力和 AUC。",
        "需要真实标签、预测分数和队列/分组信息。",
        "用于诊断、预后或筛查模型的主要性能面板。",
    ),
    "pr_curve_binary": EvidenceCopy(
        "展示阳性事件较少场景下的 precision-recall 性能。",
        "需要真实标签、预测分数和阳性类别定义。",
        "用于类别不平衡或临床关注阳性检出的任务。",
    ),
    "calibration_curve_binary": EvidenceCopy(
        "展示预测概率与观察风险的一致性。",
        "需要预测概率、真实结局和校准分箱或平滑策略。",
        "用于说明模型输出是否可作为风险概率解释。",
    ),
    "decision_curve_binary": EvidenceCopy(
        "展示不同阈值下的临床净获益。",
        "需要真实结局、预测概率和阈值范围。",
        "用于把模型性能转化为临床决策价值。",
    ),
    "kaplan_meier_grouped": EvidenceCopy(
        "展示不同组别的生存曲线和风险表。",
        "需要随访时间、事件状态和分组变量。",
        "用于风险分层、治疗组或分子分型的生存差异。",
    ),
    "cumulative_incidence_grouped": EvidenceCopy(
        "展示随时间累积发生风险。",
        "需要时间、事件状态、分组变量和竞争风险口径。",
        "用于复发、死亡或不良事件累积风险展示。",
    ),
    "time_dependent_roc_horizon": EvidenceCopy(
        "展示指定时间窗下的时间依赖判别性能。",
        "需要随访资料、事件状态、预测分数和评估时间窗。",
        "用于预后模型在不同随访时间的性能说明。",
    ),
    "time_to_event_multihorizon_calibration_panel": EvidenceCopy(
        "展示多个时间窗下的预后概率校准。",
        "需要时间窗风险预测、观察风险估计和队列信息。",
        "用于说明预后模型概率输出在不同时间点的可靠性。",
    ),
    "time_to_event_decision_curve": EvidenceCopy(
        "展示预后模型在时间窗下的净获益。",
        "需要时间窗预测风险、随访结局和阈值范围。",
        "用于连接时间事件模型和临床阈值决策。",
    ),
    "risk_layering_monotonic_bars": EvidenceCopy(
        "展示风险层级与事件率或结局负担的单调关系。",
        "需要风险分层、事件率或结局统计和置信区间。",
        "用于说明模型分层具有可解释的临床梯度。",
    ),
    "forest_effect_main": EvidenceCopy(
        "展示主要效应估计及置信区间。",
        "需要估计值、置信区间、变量标签和模型口径。",
        "用于回归模型、危险因素和亚组效应的核心结果。",
    ),
    "coefficient_path_panel": EvidenceCopy(
        "展示正则化或特征选择过程中的系数路径。",
        "需要惩罚参数、变量系数和模型选择节点。",
        "用于说明模型构建过程和特征稳定性。",
    ),
    "generalizability_subgroup_composite_panel": EvidenceCopy(
        "展示跨队列和亚组的性能或效应稳定性。",
        "需要队列、亚组、指标估计和不确定性区间。",
        "用于外部验证、泛化能力和公平性初筛。",
    ),
    "pca_scatter_grouped": EvidenceCopy(
        "从特征矩阵计算 PCA 并展示样本结构。",
        "需要样本特征矩阵、分组标签和预处理口径。",
        "用于高维数据整体分布和批次/分组结构检查。",
    ),
    "tsne_scatter_grouped": EvidenceCopy(
        "从特征矩阵计算 t-SNE 并展示局部邻域结构。",
        "需要样本特征矩阵、分组标签和 t-SNE 参数。",
        "用于非线性局部结构和细胞/样本簇展示。",
    ),
    "umap_scatter_grouped": EvidenceCopy(
        "从特征矩阵计算 UMAP 并展示全局-局部折中结构。",
        "需要样本特征矩阵、分组标签和 UMAP 参数。",
        "用于单细胞、空间或多组学嵌入展示。",
    ),
    "omics_volcano_panel": EvidenceCopy(
        "展示差异分析效应量和显著性。",
        "需要 log fold change、显著性统计和特征注释。",
        "用于转录组、蛋白组或代谢组差异特征筛选。",
    ),
    "heatmap_group_comparison": EvidenceCopy(
        "展示分组间的矩阵模式和样本聚类。",
        "需要矩阵数据、行列注释和统一热图色板。",
        "用于表达谱、signature 或临床特征矩阵展示。",
    ),
    "confusion_matrix_heatmap_binary": EvidenceCopy(
        "展示二分类预测的混淆矩阵。",
        "需要真实标签、预测标签和阈值定义。",
        "用于阈值固定后的分类错误结构说明。",
    ),
    "celltype_marker_dotplot_panel": EvidenceCopy(
        "展示细胞类型 marker 的表达比例与强度。",
        "需要细胞类型、marker、表达比例和平均表达。",
        "用于单细胞注释、细胞状态和 marker 证据汇总。",
    ),
    "genomic_alteration_landscape_panel": EvidenceCopy(
        "展示样本层面的基因改变景观。",
        "需要样本-基因改变矩阵、临床注释和改变类型。",
        "用于突变、CNV 或多组学主景观面板。",
    ),
    "genomic_alteration_consequence_panel": EvidenceCopy(
        "展示分子改变与功能或临床后果的关系。",
        "需要改变类别、后果指标和统计比较结果。",
        "用于解释分子景观的生物学和临床意义。",
    ),
    "cnv_recurrence_summary_panel": EvidenceCopy(
        "展示 CNV 复发区域和频率模式。",
        "需要基因组位置、拷贝数状态和样本频率。",
        "用于拷贝数改变主结果或补充证据。",
    ),
    "pathway_enrichment_dotplot_panel": EvidenceCopy(
        "展示通路富集强度、显著性和基因集大小。",
        "需要通路名、富集分数、显著性和命中数量。",
        "用于解释差异基因、signature 或分子亚型。",
    ),
    "shap_summary_beeswarm": EvidenceCopy(
        "展示全局特征贡献分布。",
        "需要 SHAP 值、特征值和样本分组信息。",
        "用于模型解释主面板和特征重要性排序。",
    ),
    "shap_dependence_panel": EvidenceCopy(
        "展示单个特征取值与模型贡献的关系。",
        "需要 SHAP 值、原始特征值和交互或分组变量。",
        "用于解释关键变量的非线性影响。",
    ),
    "shap_waterfall_local_explanation_panel": EvidenceCopy(
        "展示单个样本预测的局部贡献。",
        "需要个体 SHAP 分解、基线值和预测输出。",
        "用于病例级解释或代表性样本说明。",
    ),
    "model_complexity_audit_panel": EvidenceCopy(
        "展示模型复杂度、特征数量和验证性能之间的关系。",
        "需要模型版本、特征数量、性能指标和验证结果。",
        "用于说明模型选择、简洁性和过拟合风险控制。",
    ),
}


def composition_copy(recipe_id: str, fallback_title: str) -> CompositionCopy:
    return COMPOSITION_COPY.get(
        recipe_id,
        CompositionCopy(
            title=fallback_title,
            use_case="适用于需要多面板组织的医学论文图页。",
            central_message="围绕一个核心论点组织主面板和辅助证据。",
            panel_plan=(
                "主面板承载最重要的结论。",
                "辅助面板补充统计证据、机制解释或稳健性检查。",
            ),
            evidence_note="涉及数据分析的面板均应使用程序化结果生成并保留审计引用。",
        ),
    )


def evidence_category_copy(category: str) -> tuple[str, str]:
    return EVIDENCE_CATEGORY_COPY.get(category, (category, "用于医学论文中对应类别的数据证据展示。"))


def evidence_copy(record: TemplateRecord) -> EvidenceCopy:
    return EVIDENCE_COPY.get(
        record.template_id,
        EvidenceCopy(
            purpose=f"展示{record.canonical_family_title}相关数据证据。",
            data_requirement="需要已审计的数据摘要、统计量和来源引用。",
            use_when="用于论文中与该图型对应的证据面板。",
        ),
    )


def design_copy(record: TemplateRecord) -> DesignCopy:
    return DESIGN_COPY.get(
        record.template_id,
        DesignCopy(
            purpose=f"展示{record.canonical_family_title}相关非数据设计图。",
            input_requirement="需要论文级叙事 brief、来源引用、节点/面板关系和目标期刊图形要求。",
            use_when="用于研究流程、设计说明、图形摘要或机制性示意图。",
            evidence_boundary="设计图可追求表达力，但不得替代程序化数据证据图或统计结果来源。",
        ),
    )
