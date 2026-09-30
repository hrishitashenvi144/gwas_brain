import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="NeuroAtlas",
    page_icon="🧠",
    layout="wide",
)


st.markdown(
    """
    <style>
    .stApp {
        background: #050807;
        color: #F5F8F5;
        overflow: visible;
    }

    .block-container ,
[data-testid="stMainBlockContainer"] {
        padding-top: 7rem !important;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
        max-width: 1500px;
        overflow: visible;
    }

    .app-title {
        font-size: clamp(2.2rem, 2.7vw, 4rem);
        letter-spacing: -0.055em;
        font-weight: 700;
        color: #F5F8F5;
        line-height: 1.25;
        margin: 0 0 0.35rem 0;
        position:relative;
        top:0px;
        # margin-bottom:60px;
        padding-top: 0.5rem;
        max-width: min(100%, 1100px);
        display: block;
        white-space: normal;
        overflow: visible !important;
        visibility: visible !important;
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    }

    .subtitle {
        font-size: 0.92rem;
        color: #A4B4AB;
        margin-bottom: 1.2rem;
    }

    .panel-title {
        color: #8F9D96;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .summary-value {
        color: #F5F8F5;
        font-size: 1.05rem;
        font-weight: 600;
    }

    .summary-key {
        color: #9BAAA1;
        font-size: 0.7rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
    }

    .note {
        color: #C0CFC7;
        font-size: 0.87rem;
        line-height: 1.6;
    }

    .selection-box {
        border: 1px solid rgba(124, 255, 138, 0.28);
        background: rgba(9, 15, 12, 0.9);
        border-radius: 12px;
        padding: 0.9rem 0.95rem;
    }

    .thin-divider {
        height: 1px;
        background: rgba(151, 166, 159, 0.18);
        margin: 1rem 0;
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(124, 255, 138, 0.24);
        background: rgba(10, 18, 14, 0.75);
        color: #F5F8F5;
        min-height: 3.3rem;
        box-shadow: none;
    }

    .stButton > button:hover {
        border-color: rgba(124, 255, 138, 0.45);
        background: rgba(10, 18, 14, 0.9);
    }

    .stButton > button:focus {
        box-shadow: none;
    }

    .stButton > button[kind="primary"] {
        background: rgba(124, 255, 138, 0.06);
        border-color: rgba(124, 255, 138, 0.8);
        color: #E9FBEA;
    }

    [data-testid="stSelectbox"] > div {
        border-radius: 10px;
        border: 1px solid rgba(124, 255, 138, 0.24);
        background: rgba(9, 15, 12, 0.8);
    }

    .stExpander {
        border: 1px solid rgba(150, 170, 160, 0.18);
        border-radius: 10px;
        background: rgba(7, 12, 10, 0.2);
    }

    .stExpander summary {
        color: #F5F8F5;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    base_dir = Path(__file__).parent
    data_dir = base_dir / "app_data"

    with open(data_dir / "region_data.json", "r", encoding="utf-8") as fh:
        region_df = pd.DataFrame(json.load(fh))

    with open(data_dir / "disease_config.json", "r", encoding="utf-8") as fh:
        disease_config = json.load(fh)

    mesh = np.load(data_dir / "brain_mesh.npz")
    return region_df, disease_config, mesh["vertices"], mesh["faces"]


def disease_map():
    return {
        "Parkinson's": "parkinsons",
        "Alzheimer's": "alzheimers",
        "Huntington's": "huntingtons",
    }


def disease_description(disease_name: str) -> str:
    descriptions = {
        "Parkinson's": "Explore how Parkinson's-associated genes are expressed across the brain.",
        "Alzheimer's": "Explore how Alzheimer's-associated genes are expressed across the brain.",
        "Huntington's": "Explore the regional expression pattern of the Huntington's-associated gene set.",
    }
    if disease_name == "Huntington's":
        return descriptions[disease_name] + " This analysis uses a single associated gene (HTT), so its regional pattern should be interpreted cautiously."
    return descriptions[disease_name]


def get_region_detail_text(disease_name: str, is_significant: bool) -> str:
    if is_significant:
        return (
            f"This region shows a relatively elevated {disease_name.lower()}-associated gene expression signal. "
            "The result passes the FDR threshold used in this analysis."
        )
    return (
        f"This region shows a relatively strong {disease_name.lower()}-associated regional signal, "
        "but it does not pass the FDR significance threshold in this analysis."
    )


def default_region_for_disease(region_df: pd.DataFrame, disease_name: str) -> str:
    fdr_col = f"{disease_name}_fdr"
    score_col = f"{disease_name}_score"
    significant = region_df[fdr_col] < 0.05
    if significant.any():
        return region_df.loc[significant, ["region_name", fdr_col]].sort_values(fdr_col).iloc[0]["region_name"]
    return region_df.loc[region_df[score_col].idxmax(), "region_name"]


def build_brain_figure(region_df: pd.DataFrame, disease_name: str, selected_region_name: str | None, vertices: np.ndarray, faces: np.ndarray):
    score_col = f"{disease_name}_score"
    fdr_col = f"{disease_name}_fdr"
    effect_col = f"{disease_name}_effect"

    region_names = region_df["region_name"].to_numpy()
    x = region_df["mni_x"].to_numpy()
    y = region_df["mni_y"].to_numpy()
    z = region_df["mni_z"].to_numpy()
    scores = region_df[score_col].to_numpy(dtype=float)
    fdr_values = region_df[fdr_col].to_numpy(dtype=float)
    effect_sizes = region_df[effect_col].to_numpy(dtype=float)

    score_min = float(np.min(scores))
    score_max = float(np.max(scores))
    if score_max > score_min:
        normalized = (scores - score_min) / (score_max - score_min)
    else:
        normalized = np.zeros_like(scores)

    fig = go.Figure()

    fig.add_trace(
        go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            color="#97AD9D",
            opacity=0.22,
            flatshading=False,
            lighting=dict(ambient=0.7, diffuse=0.8, specular=0.2, roughness=0.6),
            hoverinfo="skip",
            name="Brain surface",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=4 + normalized * 7,
                color=normalized,
                colorscale=[[0.0, "#4d5a55"], [0.5, "#7e9d89"], [1.0, "#7CFF8A"]],
                cmin=0,
                cmax=1,
                opacity=0.65,
                line=dict(width=0),
            ),
            text=region_names,
            customdata=np.column_stack([scores, fdr_values, effect_sizes]),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Regional score: %{customdata[0]:.3f}<br>"
                "FDR: %{customdata[1]:.4f}<br>"
                "Effect size: %{customdata[2]:.2f}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    top_indices = np.argsort(scores)[-5:][::-1]
    fig.add_trace(
        go.Scatter3d(
            x=x[top_indices],
            y=y[top_indices],
            z=z[top_indices],
            mode="markers",
            marker=dict(
                size=9,
                color="#7CFF8A",
                opacity=0.95,
                line=dict(color="#DFFFE8", width=1),
            ),
            text=region_names[top_indices],
            customdata=np.column_stack([scores[top_indices], fdr_values[top_indices], effect_sizes[top_indices]]),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Strong regional signal<br>"
                "Regional score: %{customdata[0]:.3f}<br>"
                "FDR: %{customdata[1]:.4f}<br>"
                "Effect size: %{customdata[2]:.2f}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    sig_indices = np.where(fdr_values < 0.05)[0]
    if sig_indices.size:
        fig.add_trace(
            go.Scatter3d(
                x=x[sig_indices],
                y=y[sig_indices],
                z=z[sig_indices],
                mode="markers",
                marker=dict(
                    size=12,
                    symbol="diamond",
                    color="#7CFF8A",
                    opacity=1,
                    line=dict(color="#FFFFFF", width=2),
                ),
                text=region_names[sig_indices],
                customdata=np.column_stack([scores[sig_indices], fdr_values[sig_indices], effect_sizes[sig_indices]]),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Statistically significant<br>"
                    "Regional score: %{customdata[0]:.3f}<br>"
                    "FDR: %{customdata[1]:.4f}<br>"
                    "Effect size: %{customdata[2]:.2f}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    if selected_region_name is not None and selected_region_name in region_names:
        selected_idx = np.where(region_names == selected_region_name)[0][0]
        fig.add_trace(
            go.Scatter3d(
                x=[x[selected_idx]],
                y=[y[selected_idx]],
                z=[z[selected_idx]],
                mode="markers",
                marker=dict(
                    size=18,
                    color="#EBFFF0",
                    opacity=1,
                    line=dict(color="#7CFF8A", width=2),
                ),
                text=[region_names[selected_idx]],
                hovertemplate="<b>%{text}</b><extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        height=760,
        paper_bgcolor="#050807",
        plot_bgcolor="#050807",
        margin=dict(l=0, r=0, t=4, b=0),
        scene=dict(
            bgcolor="#050807",
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False),
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.15)),
        ),
        dragmode="turntable",
        showlegend=False,
    )
    return fig


region_df, disease_config, verts, faces = load_data()
if "selected_disease" not in st.session_state:
    st.session_state.selected_disease = "Parkinson's"
selected_disease = st.session_state.get("selected_disease", "Parkinson's")

if "selected_region_name" not in st.session_state:
    st.session_state.selected_region_name = default_region_for_disease(region_df, selected_disease)

if st.session_state.get("last_disease") != selected_disease:
    st.session_state.selected_region_name = default_region_for_disease(region_df, selected_disease)
    st.session_state["last_disease"] = selected_disease

st.markdown(
    '<div style="height: 0px;"></div>'
    '<div class="app-title">NeuroAtlas-Brain GWAS Enrichment</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Interactive brain-wide enrichment analysis of neurodegenerative disease-associated genes.</div>',
    unsafe_allow_html=True,
)

brain_col, side_col = st.columns([2.15, 0.85])

with brain_col:
    selected_region_name = st.session_state.selected_region_name
    fig = build_brain_figure(region_df, selected_disease, selected_region_name, verts, faces)
    brain_chart = st.plotly_chart(
        fig,
        width="stretch",
        key="brain_plot",
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": False, "scrollZoom": True, "doubleClick": "reset"},
    )

    if brain_chart is not None:
        selection = getattr(brain_chart, "selection", {}) or {}
        point_indices = selection.get("point_indices") or []
        if point_indices:
            selected_idx = int(point_indices[0])
            st.session_state.selected_region_name = region_df.iloc[selected_idx]["region_name"]
            selected_region_name = st.session_state.selected_region_name

with side_col:
    st.markdown('<div class="panel-title">Disease</div>', unsafe_allow_html=True)
    for disease_name, disease_key in disease_map().items():
        is_selected = disease_name == selected_disease
        if st.button(
            disease_name,
            key=f"disease_{disease_key}",
            type="primary" if is_selected else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_disease = disease_name
            st.session_state.selected_region_name = default_region_for_disease(region_df, disease_name)
            st.rerun()

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.caption(disease_description(selected_disease), unsafe_allow_html=False)

    st.markdown('<div class="panel-title">Results</div>', unsafe_allow_html=True)
    score_col = f"{selected_disease}_score"
    fdr_col = f"{selected_disease}_fdr"
    effect_col = f"{selected_disease}_effect"
    disease_scores = region_df[score_col].to_numpy(dtype=float)
    disease_fdr = region_df[fdr_col].to_numpy(dtype=float)
    strongest_index = int(np.argmax(disease_scores))
    strongest_region = region_df.iloc[strongest_index]["region_name"]
    significant_regions = int(np.sum(disease_fdr < 0.05))
    gene_count = disease_config[disease_map()[selected_disease]]["gene_count"]

    summary_pairs = [
        ("Associated genes", str(gene_count)),
        ("Brain regions analyzed", "158"),
        ("Strongest regional signal", strongest_region),
        ("FDR-significant regions", str(significant_regions)),
    ]

    for label, value in summary_pairs:
        st.markdown(
            f"<div style='margin-bottom: 0.65rem;'><div class='summary-key'>{label}</div><div class='summary-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )

    if significant_regions == 1:
        st.caption(
            "One region showed statistically significant enrichment after FDR correction. This is distinct from a strong regional expression signal, which can be present even without FDR significance."
        )
    elif significant_regions == 0:
        st.caption(
            "No brain region passed the FDR significance threshold in this analysis. The strongest regional signals remain informative for exploration, but they are not considered statistically significant after correction."
        )

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel-title">Region</div>', unsafe_allow_html=True)
    region_options = region_df["region_name"].tolist()
    current_region_name = st.session_state.selected_region_name
    if current_region_name not in region_options:
        current_region_name = region_df.iloc[strongest_index]["region_name"]
        st.session_state.selected_region_name = current_region_name

    region_selection = st.selectbox(
        "Select region",
        options=region_options,
        index=region_options.index(current_region_name),
        label_visibility="collapsed",
    )
    st.session_state.selected_region_name = region_selection

    selected_row = region_df[region_df["region_name"] == region_selection].iloc[0]
    region_score = float(selected_row[score_col])
    region_fdr = float(selected_row[fdr_col])
    region_effect = float(selected_row[effect_col])

    st.markdown(
        """
        <div class="selection-box">
            <div class="summary-key">Region</div>
            <div class="summary-value" style="margin-top:0.2rem; margin-bottom:0.55rem;">%s</div>
            <div class="summary-key">Disease</div>
            <div class="summary-value" style="margin-top:0.2rem; margin-bottom:0.55rem;">%s</div>
            <div class="summary-key">Regional score</div>
            <div class="summary-value" style="margin-top:0.2rem; margin-bottom:0.55rem;">%.3f</div>
            <div class="summary-key">FDR</div>
            <div class="summary-value" style="margin-top:0.2rem; margin-bottom:0.55rem;">%.4f</div>
            <div class="summary-key">Effect size</div>
            <div class="summary-value" style="margin-top:0.2rem; margin-bottom:0.55rem;">%.2f</div>
        </div>
        """
        % (
            region_selection.upper(),
            selected_disease,
            region_score,
            region_fdr,
            region_effect,
        ),
        unsafe_allow_html=True,
    )

    st.write(get_region_detail_text(selected_disease, region_fdr < 0.05))
    st.caption("Statistical significance does not establish causality or disease vulnerability.")

    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Learning</div>', unsafe_allow_html=True)

    with st.expander("What is this?", expanded=True):
        st.write(
            "Some genes are associated with neurological diseases. Those genes are not necessarily expressed equally throughout the brain. This project asks whether disease-associated genes show unusually strong regional expression patterns across the brain."
        )

    with st.expander("Key concepts"):
        st.markdown(
            "- Gene: a unit of biological information that can influence how cells function.\n"
            "- Gene expression: how actively a gene is being expressed in a tissue.\n"
            "- Brain region: an anatomical subdivision with distinct cellular and functional characteristics.\n"
            "- Regional score: summarizes how strongly the selected disease-associated genes are expressed relative to their patterns across the brain.\n"
            "- FDR: false discovery rate correction controls the expected proportion of false discoveries when many regions are tested.\n"
            "- Effect size: how far the observed regional score is from the expected score under the expression-matched null model."
        )

    with st.expander("How the analysis works"):
        st.markdown(
            "Disease-associated genes\n"
            "->\n"
            "Allen Human Brain Atlas expression data\n"
            "->\n"
            "Probe ? gene aggregation\n"
            "->\n"
            "Gene-wise regional normalization\n"
            "->\n"
            "Disease regional score\n"
            "->\n"
            "Expression-matched permutation test\n"
            "->\n"
            "FDR correction\n"
            "->\n"
            "Brain-region visualization"
        )

    with st.expander("Understanding the results"):
        st.write(
            "A brighter or larger point means a relatively stronger regional signal. It does not automatically mean statistically significant. A region is statistically significant only when it passes the FDR threshold."
        )
        st.write("FDR < 0.05 indicates that the observed regional signal is unusually strong relative to the expression-matched null model, after accounting for the many regions tested.")
        st.write(
            "A non-significant result is still a valid result. For Alzheimer's and Huntington's, the absence of FDR-significant regions should be interpreted neutrally rather than as 'no signal at all.'"
        )

    with st.expander("Limitations"):
        st.markdown(
            "- Disease gene sets are small.\n"
            "- Huntington's uses only one gene.\n"
            "- The analysis is based on gene expression data, not direct disease diagnosis.\n"
            "- Regional expression association does not establish causality.\n"
            "- The brain surface is an anatomical reference visualization.\n"
            "- AHBA sampling is not uniformly distributed across every brain region.\n"
            "- Gene-expression measurements do not directly measure disease pathology.\n"
            "- Multiple testing correction reduces false positives but does not prove biological causality.\n"
            "- The current disease gene lists are curated inputs rather than direct GWAS summary-statistic analysis."
        )
