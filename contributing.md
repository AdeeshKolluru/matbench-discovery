# How to submit new models to Matbench Discovery

## 🔨 &thinsp; Installation

Clone the repo and install `matbench_discovery` into your Python environment:

```zsh
git clone https://github.com/janosh/matbench-discovery --depth 1
pip install -e ./matbench-discovery
```

There's also a [PyPI package](https://pypi.org/project/matbench-discovery) for faster installation if you don't need the latest code changes (unlikely if you're planning to submit a model since the benchmark is under active development).

## 📙 &thinsp; Usage

When you access an attribute of the `DataFiles` class, it automatically downloads and caches the corresponding data file. For example:

```py
from matbench_discovery.data import DataFiles, load

# available data files
assert sorted(DataFiles) == [
    "mp_computed_structure_entries",
    "mp_elemental_ref_entries",
    "mp_energies",
    "mp_patched_phase_diagram",
    "wbm_computed_structure_entries",
    "wbm_cses_plus_init_structs",
    "wbm_initial_structures",
    "wbm_summary",
]

# 1st arg can be any DataFiles key
# version defaults to latest, set a specific version like 1.0.0 to avoid breaking changes
df_wbm = load("wbm_summary", version="1.0.0")

# test set size
assert df_wbm.shape == (256_963, 15)

# available columns in WBM summary data
assert tuple(df_wbm) == [
    "formula",
    "n_sites",
    "volume",
    "uncorrected_energy",
    "e_form_per_atom_wbm",
    "e_above_hull_wbm",
    "bandgap_pbe",
    "wyckoff_spglib",
    "wyckoff_spglib_initial_structure",
    "uncorrected_energy_from_cse",
    "e_correction_per_atom_mp2020",
    "e_correction_per_atom_mp_legacy",
    "e_form_per_atom_uncorrected",
    "e_form_per_atom_mp2020_corrected",
    "e_above_hull_mp2020_corrected_ppd_mp",
    "site_stats_fingerprint_init_final_norm_diff",
]
```

`"wbm-summary"` columns:

1. **`formula`**: A compound's unreduced alphabetical formula
1. **`n_sites`**: Number of sites in the structure's unit cell
1. **`volume`**: Relaxed structure volume in cubic Angstrom
1. **`uncorrected_energy`**: Raw VASP-computed energy
1. **`e_form_per_atom_wbm`**: Original formation energy per atom from [WBM paper]
1. **`e_above_hull_wbm`**: Original energy above the convex hull in (eV/atom) from [WBM paper]
1. **`wyckoff_spglib`**: Aflow label strings built from spacegroup and Wyckoff positions of the DFT-relaxed structure as computed by [spglib](https://spglib.readthedocs.io/en/stable/api/python-api/spglib/spglib.html#spglib.get_symmetry_dataset).
1. **`wyckoff_spglib_initial_structure`**: Same as `wyckoff_spglib` but computed from the initial structure.
1. **`bandgap_pbe`**: PBE-level DFT band gap from [WBM paper]
1. **`uncorrected_energy_from_cse`**: Uncorrected DFT energy stored in `ComputedStructureEntries`. Should be the same as `uncorrected_energy`. There are 2 cases where the absolute difference reported in the summary file and in the computed structure entries exceeds 0.1 eV (`wbm-2-3218`, `wbm-1-56320`) which we attribute to rounding errors.
1. **`e_form_per_atom_uncorrected`**: Uncorrected DFT formation energy per atom in eV/atom.
1. **`e_form_per_atom_mp2020_corrected`**: Matbench Discovery takes these as ground truth for the formation energy. The result of applying the [MP2020 energy corrections][`MaterialsProject2020Compatibility`] (latest correction scheme at time of release) to `e_form_per_atom_uncorrected`.
1. **`e_correction_per_atom_mp2020`**: [`MaterialsProject2020Compatibility`] energy corrections in eV/atom.
1. **`e_correction_per_atom_mp_legacy`**: Legacy [`MaterialsProjectCompatibility`] energy corrections in eV/atom. Having both old and new corrections allows updating predictions from older models like MEGNet that were trained on MP formation energies treated with the old correction scheme.
1. **`e_above_hull_mp2020_corrected_ppd_mp`**: Energy above hull distances in eV/atom after applying the MP2020 correction scheme. The convex hull in question is the one spanned by all ~145k Materials Project `ComputedStructureEntries`. Matbench Discovery takes these as ground truth for material stability. Any value above 0 is assumed to be an unstable/metastable material.
1. **`site_stats_fingerprint_init_final_norm_diff`**: The norm of the difference between the initial and final site fingerprints. This is a volume-independent measure of how much the structure changed during DFT relaxation. Uses the `matminer` [`SiteStatsFingerprint`](https://github.com/hackingmaterials/matminer/blob/33bf112009b67b108f1008b8cc7398061b3e6db2/matminer/featurizers/structure/sites.py#L21-L33) (v0.8.0).

[`MaterialsProject2020Compatibility`]: https://github.com/materialsproject/pymatgen/blob/02a4ca8aa0277b5f6db11f4de4fdbba129de70a5/pymatgen/entries/compatibility.py#L823
[`MaterialsProjectCompatibility`]: https://github.com/materialsproject/pymatgen/blob/02a4ca8aa0277b5f6db11f4de4fdbba129de70a5/pymatgen/entries/compatibility.py#L766

## 📥 &thinsp; Direct Download

You can download all Matbench Discovery data files from [this Figshare article](https://figshare.com/articles/dataset/23713842).

<slot name="data-files" />

To train an interatomic potential, we recommend the [**MPtrj dataset**](https://figshare.com/articles/dataset/23713842) which was created to train [CHGNet](https://www.nature.com/articles/s42256-023-00716-3). With thanks to [Bowen Deng](https://scholar.google.com/citations?user=PRPXA0QAAAAJ) for cleaning and releasing this dataset. It was created from the [2021.11.10](https://docs.materialsproject.org/changes/database-versions#v2021.11.10) release of Materials Project and therefore constitutes a slightly smaller but valid subset of the allowed [2022.10.28](https://docs.materialsproject.org/changes/database-versions#v2022.10.28) MP release that is our training set.

[wbm paper]: https://nature.com/articles/s41524-020-00481-6

## ✨ &thinsp; How to submit a new model

To submit a new model to this benchmark and add it to our leaderboard, please create a pull request to the [`main` branch][repo] that includes at least these 3 required files:

1. `<yyyy-mm-dd>-<model_name>-preds.(json|csv).gz`: Your model's energy predictions for all ~250k WBM compounds as compressed JSON or CSV. The recommended way to create this file is with `pandas.DataFrame.to_{json|csv}('<yyyy-mm-dd>-<model_name>-preds.(json|csv).gz')`. JSON is preferred over CSV if your model not only predicts energies (floats) but also objects like relaxed structures. See e.g. [M3GNet](https://github.com/janosh/matbench-discovery/blob/-/models/m3gnet/test_m3gnet.py) and [CHGNet](https://github.com/janosh/matbench-discovery/blob/-/models/chgnet/test_chgnet.py) test scripts.
   For machine learning force field (MLFF) submissions, you additionally upload the relaxed structures and forces from your model's geometry optimization to Figshare or a similar platform and include the download link in your PR description and the YAML metadata file. This file should include:

   - The final relaxed structures (as ASE `Atoms` or pymatgen `Structures`)
   - Energies (eV), forces (eV/Å), stress (eV/Å³) and volume (Å³) at each relaxation step

   Recording the model-relaxed structures enables additional analysis of root mean squared displacement (RMSD) and symmetry breaking with respect to DFT relaxed structures. Having the forces and stresses at each step also allows analyzing any pathological behavior for structures were relaxation failed or went haywire.

   Example of how to record these quantities for a single structure with ASE:

   ```python
   from collections import defaultdict
   import pandas as pd
   from ase.atoms import Atoms
   from ase.optimize import FIRE
   from mace.calculators import mace_mp
   trajectory = defaultdict(list)
   batio3 = Atoms(
       "BaTiO3",
       scaled_positions=[
           (0, 0, 0),
           (0.5, 0.5, 0.5),
           (0.5, 0, 0.5),
           (0, 0.5, 0.5),
           (0.5, 0.5, 0),
       ],
       cell=[4] * 3,
   )
   batio3.calc = mace_mp(model_name="medium", default_dtype="float64")
   def callback() -> None:
       """Record energy, forces, stress and volume at each step."""
       trajectory["energy"] += [batio3.get_potential_energy()]
       trajectory["forces"] += [batio3.get_forces()]
       trajectory["stress"] += [batio3.get_stress()]
       trajectory["volume"] += [batio3.get_volume()]
       # Optionally save structure at each step
       trajectory["atoms"] += [batio3.copy()]
   opt = FIRE(batio3)
   opt.attach(callback) # register callback
   opt.run(fmax=0.01, steps=500)  # optimize geometry
   # Save final structure and trajectory data
   df_traj = pd.DataFrame(trajectory)
   df_traj.index.name = "step"
   df_traj.to_csv("trajectory.csv.gz")
   ```

1. `test_<model_name>.(py|ipynb)`: The Python script or Jupyter notebook that generated the energy predictions. Ideally, this file should have comments explaining at a high level what the code is doing and how the model works so others can understand and reproduce your results. If the model deployed on this benchmark was trained specifically for this purpose (i.e. if you wrote any training/fine-tuning code while preparing your PR), please also include it as `train_<model_name>.(py|ipynb)`.
1. `<model_name.yml>`: A file to record all relevant metadata of your algorithm like model name and version, authors, package requirements, links to publications, notes, etc. Here's a template:

   ```yml
   model_name: My new model # required (this must match the model's label which is the 3rd arg in the matbench_discovery.preds.Model enum)
   model_key: my-new-model # this should match the name of the YAML file and determines the URL /models/<model_key> on which details of the model are displayed on the website
   model_version: 1.0.0 # required
   matbench_discovery_version: 1.0 # required
   date_added: "2023-01-01" # required
   authors: # required (only name, other keys are optional)
     - name: John Doe
       affiliation: Some University, Some National Lab
       email: john-doe@uni.edu
       orcid: https://orcid.org/0000-xxxx-yyyy-zzzz
       url: lab.gov/john-doe
       corresponding: true
       role: Model & PR
     - name: Jane Doe
       affiliation: Some National Lab
       email: jane-doe@lab.gov
       url: uni.edu/jane-doe
       orcid: https://orcid.org/0000-xxxx-yyyy-zzzz
       role: Model
   repo: https://github.com/<user>/<repo> # required
   url: https://<model-docs-or-similar>.org
   doi: https://doi.org/10.5281/zenodo.0000000
   preprint: https://arxiv.org/abs/xxxx.xxxxx

   requirements: # strongly recommended
     torch: 1.13.0
     torch-geometric: 2.0.9
     ...

   training_set: [MPtrj] # list of keys from data/training-sets.yml

   notes: # notes can have any key, be multiline and support markdown.
     description: This is how my model works...
     steps: |
      Optional *free-form* [markdown](example.com) notes.

   metrics:
     discovery:
        pred_file: /models/<model_dir>/<yyyy-mm-dd>-<model_name>-wbm-IS2RE.csv.gz # should contain the models energy predictions for the WBM test set
        pred_col: e_form_per_atom_<model_name>
     geo_opt: # only applicable if the model performed structure relaxation
        pred_file: /models/<model_dir>/<yyyy-mm-dd>-<model_name>-wbm-IS2RE.json.gz # should contain the models relaxed structures as ASE Atoms or pymatgen Structures, and forces/stresses at each relaxation step
        pred_col: e_form_per_atom_<model_name>
   ```

   Arbitrary other keys can be added as needed. The above keys will be schema-validated with `pre-commit` (if installed) with errors for missing keys.

Please see any of the subdirectories in [`models/`](https://github.com/janosh/matbench-discovery/bob/-/models) for example submissions. More detailed step-by-step instructions below.

### Step 1: Clone the repo

```sh
git clone https://github.com/janosh/matbench-discovery --depth 1
cd matbench-discovery
git checkout -b model-name-you-want-to-add
```

Tip: `--depth 1` only clones the latest commit, not the full `git history` which is faster if a repo contains large data files that changed over time.

### Step 2: Commit model predictions, train/test scripts and metadata

Create a new folder

```sh
mkdir models/<model_name>
```

and place the above-listed files there. The file structure should look like this:

```txt
matbench-discovery-root
└── models
    └── <model_name>
        ├── <model_name>.yml
        ├── <yyyy-mm-dd>-<model_name>-preds.(json|csv).gz
        ├── test_<model_name>.py
        ├── readme.md  # optional
        └── train_<model_name>.py  # optional
```

You can include arbitrary other supporting files like metadata and model features (below 10MB total to keep `git clone` time low) if they are needed to run the model or help others reproduce your results. For larger files, please upload to [Figshare](https://figshare.com) or similar and share the link in your PR description.

### Step 3: Open a PR to the [Matbench Discovery repo][repo]

Commit your files to the repo on a branch called `<model_name>` and create a pull request (PR) to the Matbench repository.

```sh
git add -a models/<model_name>
git commit -m 'add <model_name> to Matbench Discovery leaderboard'
```

And you're done! Once tests pass and the PR is merged, your model will be added to the leaderboard! 🎉

### Step 4 (optional): Copy WandB runs into our project

[Weights and Biases](https://wandb.ai) is a tool for logging training and test runs of ML models. It's free, (partly) [open source](https://github.com/wandb/wandb) and offers a [special plan for academics](https://wandb.ai/site/research). It auto-collects metadata like

- what hardware the model is running on
- and for how long,
- what the CPU, GPU and network utilization was over that period,
- the exact code in the script that launched the run, and
- which versions of dependencies were installed in the environment your model ran in.

This information can be useful for others looking to reproduce your results or compare their model to yours i.t.o. computational cost. We therefore strongly recommend tracking all runs that went into a model submission with WandB so that the runs can be copied over to our WandB project at <https://wandb.ai/janosh/matbench-discovery> for everyone to inspect. This also allows us to include your model in more detailed analysis (see [SI](https://matbench-discovery.materialsproject.org/preprint#supplementary-information)).

## 😵‍💫 &thinsp; Troubleshooting

Having problems? Please [open an issue on GitHub](https://github.com/janosh/matbench-discovery/issues). We're happy to help! 😊

[repo]: https://github.com/janosh/matbench-discovery