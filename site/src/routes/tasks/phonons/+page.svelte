<script lang="ts">
  import { MetricScatter, MetricsTable, MODELS, type ModelData } from '$lib'
  import { DEFAULT_CPS_CONFIG } from '$lib/combined_perf_score'
  import { ALL_METRICS, METADATA_COLS, PHONON_METRICS } from '$lib/metrics'

  // Default column visibility
  let visible_cols: Record<string, boolean> = $state({
    // Hide other metrics
    ...Object.fromEntries([...ALL_METRICS].map((col) => [col.label, false])),
    // Show all metadata
    ...Object.fromEntries([...METADATA_COLS].map((col) => [col.label, true])),
    // Show phonon metrics
    ...Object.fromEntries([...PHONON_METRICS].map((col) => [col.label, true])),
  })

  const model_has_kappa_103 = (model: ModelData) =>
    typeof model?.metrics?.phonons?.kappa_103?.κ_SRME === `number`
</script>

<h1>MLFF Phonon Modeling Metrics</h1>

<figure>
  <MetricsTable
    col_filter={(col) => visible_cols[col.label] ?? true}
    model_filter={model_has_kappa_103}
    sort_hint=""
    style="width: 100%;"
  />

  <h3>κ<sub>SRME</sub> for 103 PhononDB structures over time</h3>
  <p>
    κ<sub>SRME</sub> ranges from 0 to 2, the lower the better. This metric was introduced
    in
    <a href="https://arxiv.org/abs/2408.00755v4">arXiv:2408.00755v4</a>. This modeling
    task would not have been possible without the
    <a href="https://github.com/materialsproject/PhononDB">PhononDB</a>
    and the help of Atsushi Togo who kindly shared the
    <a
      href="https://github.com/atztogo/phonondb/blob/main/README.md#url-links-to-phono3py-finite-displacement-method-inputs-of-103-compounds-on-mdr-at-nims-pbe"
      >PBE reference data for the 103 MP structures</a
    > that form the test set for this task.
  </p>

  <MetricScatter
    models={MODELS}
    model_filter={model_has_kappa_103}
    metric="phonons.kappa_103.κ_SRME"
    x_property="model_params"
    y_label="{DEFAULT_CPS_CONFIG.parts.kappa_SRME.svg_label} (lower better)"
    style="margin: 2em 0;"
  />

  <h3 style="margin: 3em auto -1em;">κ<sub>SRME</sub> Progress Over Time</h3>
  <MetricScatter
    models={MODELS}
    model_filter={model_has_kappa_103}
    metric="phonons.kappa_103.κ_SRME"
    x_property="date_added"
    date_range={[new Date(2024, 9, 1), null]}
    y_label="{DEFAULT_CPS_CONFIG.parts.kappa_SRME.svg_label} (lower better)"
    style="margin: 2em 0;"
  />
</figure>

<style>
  h3 {
    text-align: center;
  }
  figure {
    margin: 0;
    display: grid;
    gap: 1ex;
  }
</style>
