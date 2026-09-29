# Brain GWAS Enrichment

Interactive brain-wide enrichment analysis of neurodegenerative disease-associated genes.

This project renders precomputed gene-expression results across 158 anatomically defined brain regions from the Allen Human Brain Atlas, using curated disease-associated gene sets for Parkinson's disease, Alzheimer's disease, and Huntington's disease.

## Features

- Disease selector for Parkinson's, Alzheimer's, and Huntington's
- 3D brain visualization over the validated anatomical surface mesh
- All 158 regional scores shown for every disease
- Strongest regional signals and FDR-significant regions highlighted separately
- Region-level details including score, FDR, and effect size
- Educational explanation panels covering analysis goals, terminology, and limitations

## Scientific note

This frontend consumes validated, precomputed results and does not recalculate the underlying scientific analysis. The implemented procedure is based on the already validated expression-matched regional enrichment workflow.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app expects the following files in `app_data/`:

- `region_data.json`
- `disease_config.json`
- `brain_mesh.npz`

## Data and method

The app visualizes validated regional enrichment scores derived from disease-associated genes across the human brain. The aim is to help users understand how gene-expression patterns are distributed across brain regions and to distinguish strong regional signals from statistically significant FDR-corrected results.

## License

This project is provided for research and educational use as part of the project repository.
