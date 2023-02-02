# %%
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import requests
import wandb
import wandb.apis.public
from pymatviz.utils import save_fig
from tqdm import tqdm

from matbench_discovery import FIGS, MODELS, WANDB_PATH, today
from matbench_discovery.data import PRED_FILENAMES, load_df_wbm_preds
from matbench_discovery.energy import stable_metrics
from matbench_discovery.plots import px

__author__ = "Janosh Riebesell"
__date__ = "2022-11-28"


# %%
models: dict[str, dict[str, Any]] = {
    "CGCNN": dict(
        n_runs=10,
        filters=dict(
            created_at={"$gt": "2022-11-21", "$lt": "2022-11-23"},
            display_name={"$regex": "cgcnn-robust-formation_energy_per_atom"},
        ),
    ),
    "Voronoi Random Forest": dict(
        n_runs=68,
        filters=dict(
            created_at={"$gt": "2022-11-17", "$lt": "2022-11-28"},
            display_name={"$regex": "voronoi-features"},
        ),
    ),
    "Wrenformer": dict(
        n_runs=10,
        filters=dict(
            created_at={"$gt": "2022-11-14", "$lt": "2022-11-16"},
            display_name={"$regex": "wrenformer-robust-mp-formation_energy"},
        ),
    ),
    "MEGNet": dict(
        n_runs=1,
        filters=dict(
            created_at={"$gt": "2022-11-17", "$lt": "2022-11-19"},
            display_name={"$regex": "megnet-wbm-IS2RE"},
        ),
    ),
    "M3GNet": dict(
        n_runs=99,
        filters=dict(
            created_at={"$gt": "2022-10-31", "$lt": "2022-11-01"},
            display_name={"$regex": "m3gnet-wbm-IS2RE"},
        ),
    ),
    "BOWSR MEGNet": dict(
        n_runs=500,
        filters=dict(
            created_at={"$gt": "2023-01-20", "$lt": "2023-01-22"},
            display_name={"$regex": "bowsr-megnet"},
        ),
    ),
}

assert set(models) == set(PRED_FILENAMES), f"{set(models)=} != {set(PRED_FILENAMES)=}"


model_stats: dict[str, dict[str, str | int | float]] = {}


# %% calculate total model run times from wandb logs
# NOTE these model run times are pretty meaningless since some models were run on GPU
# (Wrenformer and CGCNN), others on CPU. Also BOWSR MEGNet, M3GNet and MEGNet weren't
# trained from scratch. Their run times only indicate the time needed to predict the
# test set.

for model in (pbar := tqdm(models)):
    n_runs, filters = (models[model].get(x) for x in ("n_runs", "filters"))
    if n_runs == 0 or model in model_stats:
        continue
    pbar.set_description(model)
    if "runs" in models[model]:
        runs: wandb.apis.public.Runs = models[model]["runs"]
    else:
        models[model]["runs"] = runs = wandb.Api().runs(WANDB_PATH, filters=filters)

    assert len(runs) == n_runs, f"found {len(runs)=} for {model}, expected {n_runs}"

    each_run_time = [run.summary.get("_wandb", {}).get("runtime", 0) for run in runs]

    run_time_total = sum(each_run_time)
    # NOTE we assume all jobs have the same metadata here
    metadata = requests.get(runs[0].file("wandb-metadata.json").url).json()

    n_gpu, n_cpu = metadata.get("gpu_count", 0), metadata.get("cpu_count", 0)
    model_stats[model] = {
        (time_col := "Run Time (h)"): run_time_total / 3600,
        "GPU": n_gpu,
        "CPU": n_cpu,
        "Slurm Jobs": n_runs,
    }


ax = (pd.Series(each_run_time) / 3600).hist(bins=100)
ax.set(
    title=f"Run time distribution for {model}", xlabel="Run time [h]", ylabel="Count"
)

df_metrics = pd.DataFrame(model_stats).T
df_metrics.index.name = "Model"
# on 2022-11-28:
# run_times = {'Voronoi Random Forest': 739608,
#  'Wrenformer': 208399,
#  'MEGNet': 12396,
#  'M3GNet': 301138,
#  'BOWSR MEGNet': 9105237}


# %%
df_wbm = load_df_wbm_preds(list(models))
e_form_col = "e_form_per_atom_mp2020_corrected"
each_true_col = "e_above_hull_mp2020_corrected_ppd_mp"


# %%
for model in models:
    each_pred = df_wbm[each_true_col] + df_wbm[model] - df_wbm[e_form_col]

    metrics = stable_metrics(df_wbm[each_true_col], each_pred)

    df_metrics.loc[model, list(metrics)] = metrics.values()


# %%
df_styled = (
    df_metrics.reset_index()
    .drop(columns=["GPU", "CPU", "Slurm Jobs"])
    .style.format(precision=2)
    .background_gradient(
        cmap="viridis_r",  # lower is better so reverse color map
        subset=["MAE", "RMSE", "FNR", "FPR"],
    )
    .background_gradient(
        cmap="viridis_r",
        subset=[time_col],
        gmap=np.log10(df_metrics[time_col].to_numpy()),  # for log scaled color map
    )
    .background_gradient(
        cmap="viridis",  # higher is better
        subset=["DAF", "R2", "Precision", "Recall", "F1", "Accuracy", "TPR", "TNR"],
    )
    .hide(axis="index")
)
df_styled


# %% export model metrics as styled HTML table
styles = {
    "": "font-family: sans-serif; border-collapse: collapse;",
    "td, th": "border: 1px solid #ddd; text-align: left; padding: 8px; white-space: nowrap;",
}
df_styled.set_table_styles([dict(selector=sel, props=styles[sel]) for sel in styles])

html_path = f"{FIGS}/{today}-metrics-table.svelte"
df_styled.to_html(html_path)


# %% write model metrics to json for use by the website
df_metrics["missing_preds"] = df_wbm[list(models)].isna().sum()
df_metrics["missing_percent"] = [
    f"{x / len(df_wbm):.2%}" for x in df_metrics.missing_preds
]

df_metrics.attrs["Total Run Time"] = df_metrics[time_col].sum()

df_metrics.round(2).to_json(f"{MODELS}/{today}-model-stats.json", orient="index")


# %% plot model run times as pie chart
fig = px.pie(
    df_metrics, values=time_col, names=df_metrics.index, hole=0.5
).update_traces(
    textinfo="percent+label",
    textfont_size=14,
    marker=dict(line=dict(color="#000000", width=2)),
    hoverinfo="label+percent+name",
    texttemplate="%{label}<br>%{percent:.1%}",
    hovertemplate="%{label} %{percent:.1%} (%{value:.1f} h)",
    rotation=90,
    showlegend=False,
)
fig.add_annotation(
    # add title in the middle saying "Total CPU+GPU time used"
    text=f"Total CPU+GPU<br>time used:<br>{df_metrics[time_col].sum():.1f} h",
    font=dict(size=18),
    x=0.5,
    y=0.5,
    showarrow=False,
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))


# %%
save_fig(fig, f"{FIGS}/{today}-model-run-times-pie.svelte")