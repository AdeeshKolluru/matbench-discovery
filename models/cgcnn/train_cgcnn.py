# %%
import os

import pandas as pd
from aviary.cgcnn.data import CrystalGraphData, collate_batch
from aviary.cgcnn.model import CrystalGraphConvNet
from aviary.core import TaskType
from aviary.train import df_train_test_split, train_model
from pymatgen.core import Structure
from torch.utils.data import DataLoader
from tqdm import tqdm

from matbench_discovery import DEBUG, ROOT, timestamp, today
from matbench_discovery.slurm import slurm_submit

"""
Train a CGCNN ensemble on target_col of data_path.
"""

__author__ = "Janosh Riebesell"
__date__ = "2022-06-13"


# %%
epochs = 300
target_col = "formation_energy_per_atom"
job_name = f"train-cgcnn-robust-{target_col}{'-debug' if DEBUG else ''}"
print(f"{job_name=}")
robust = "robust" in job_name.lower()
ensemble_size = 10
module_dir = os.path.dirname(__file__)
out_dir = os.environ.get("SBATCH_OUTPUT", f"{module_dir}/{today}-{job_name}")

slurm_vars = slurm_submit(
    job_name=job_name,
    partition="ampere",
    account="LEE-SL3-GPU",
    time="8:0:0",
    array=f"1-{ensemble_size}",
    out_dir=out_dir,
    slurm_flags="--nodes 1 --gpus-per-node 1",
)


# %%
optimizer = "AdamW"
learning_rate = 3e-4
batch_size = 128
swa_start = None
slurm_array_task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
task_type: TaskType = "regression"


# %%
data_path = f"{ROOT}/data/mp/2022-08-13-mp-energies.json.gz"
# data_path = f"{ROOT}/data/mp/2022-08-13-mp-energies-1k-samples.json.gz"
print(f"{data_path=}")
df = pd.read_json(data_path).set_index("material_id", drop=False)
df["structure"] = [Structure.from_dict(s) for s in tqdm(df.structure, disable=None)]
assert target_col in df

train_df, test_df = df_train_test_split(df, test_size=0.05)

print(f"{train_df.shape=}")
train_data = CrystalGraphData(train_df, task_dict={target_col: task_type})
train_loader = DataLoader(
    train_data, batch_size=batch_size, shuffle=True, collate_fn=collate_batch
)

print(f"{test_df.shape=}")
test_data = CrystalGraphData(test_df, task_dict={target_col: task_type})
test_loader = DataLoader(
    test_data, batch_size=batch_size, shuffle=False, collate_fn=collate_batch
)

# 1 for regression, n_classes for classification
n_targets = [1 if task_type == "regression" else df[target_col].max() + 1]

model_params = dict(
    n_targets=n_targets,
    elem_emb_len=train_data.elem_emb_len,
    nbr_fea_len=train_data.nbr_fea_dim,
    task_dict={target_col: task_type},  # e.g. {'exfoliation_en': 'regression'}
    robust=robust,
)
model = CrystalGraphConvNet(**model_params)

run_params = dict(
    data_path=data_path,
    batch_size=batch_size,
    train_df=dict(shape=str(train_data.df.shape), columns=", ".join(train_df)),
    test_df=dict(shape=str(test_data.df.shape), columns=", ".join(test_df)),
    slurm_vars=slurm_vars,
)


# %%
print(f"\nJob started running {timestamp}")

train_model(
    checkpoint="wandb",  # None | 'local' | 'wandb',
    epochs=epochs,
    learning_rate=learning_rate,
    model_params=model_params,
    model=model,
    optimizer=optimizer,
    run_name=f"{job_name}-{slurm_array_task_id}",
    swa_start=swa_start,
    target_col=target_col,
    task_type=task_type,
    test_loader=test_loader,
    timestamp=timestamp,
    train_loader=train_loader,
    wandb_path="janosh/matbench-discovery",
    run_params=run_params,
)