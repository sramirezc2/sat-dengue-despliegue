"""Extensión del backend MLflow local: lifecycle padre e hijos por horizonte."""

import math
import time
from pathlib import Path
from typing import Any

from sat_dengue_pipeline.tracking.local import LocalTracker, TrackingConfig

EXPERIMENT_TAGS = {
    "mlflow.runName",
    "mlflow.parentRunId",
    "experiment_id",
    "hypothesis_id",
    "protocol_sha256",
    "configuration_sha256",
    "dataset_sha256",
    "code_sha256",
    "execution_id",
    "execution_signature",
    "status",
    "candidate",
    "horizon",
    "evidence",
    "experiment_type",
    "evaluation_label",
    "contract_sha256",
    "contract_status",
}


class ExperimentTracker(LocalTracker):
    """Reutilizar SQLite/SDK/privacidad existentes; no API fluida ni backend remoto."""

    def __init__(self, workspace: Path, enabled: bool) -> None:
        """Seleccionar un store local ignorado y conservar la opción de desactivarlo."""
        super().__init__(
            workspace, TrackingConfig(enabled, ".tracking/experiments", "satd-experiments")
        )

    def start(self, tags: dict[str, str], parent: str | None = None) -> str | None:
        """Abrir una corrida operacional antes de calcular, con tags cerrados."""
        if not set(tags) <= EXPERIMENT_TAGS:
            raise ValueError("Tag desconocido")
        if not self.config.enabled:
            return None
        if self.store is None:
            self._open()
        from mlflow.entities import RunTag

        tags = {**tags, "status": "RUNNING"}
        if parent:
            tags["mlflow.parentRunId"] = parent
        run = self.store.create_run(
            self.experiment_id,
            user_id="",
            start_time=int(time.time() * 1000),
            tags=[RunTag(k, v) for k, v in tags.items()],
            run_name=tags["execution_id"],
        )
        return run.info.run_id

    def finish(
        self,
        run_id: str | None,
        status: str,
        tags: dict[str, str],
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Registrar solo números agregados y cerrar explícitamente cada corrida creada."""
        if not set(tags) <= EXPERIMENT_TAGS:
            raise ValueError("Tag desconocido")
        if run_id is None:
            return
        from mlflow.entities import Metric, RunStatus, RunTag
        from mlflow.utils.validation import MAX_ENTITIES_PER_BATCH, MAX_METRICS_PER_BATCH

        numeric = []
        for reference, records in (metrics or {}).items():
            for record in records:
                value = record["value"]
                if value is not None and math.isfinite(value):
                    numeric.append(
                        Metric(
                            reference + "." + record["metric"],
                            float(value),
                            int(time.time() * 1000),
                            0,
                        )
                    )
        logged_tags = [RunTag(k, v) for k, v in {**tags, "status": status}.items()]
        batch_size = min(MAX_METRICS_PER_BATCH, MAX_ENTITIES_PER_BATCH - len(logged_tags))
        try:
            for start in range(0, max(len(numeric), 1), batch_size):
                self.store.log_batch(
                    run_id,
                    metrics=numeric[start : start + batch_size],
                    params=[],
                    tags=logged_tags,
                )
        except BaseException:
            self.store.update_run_info(run_id, RunStatus.FAILED, int(time.time() * 1000), None)
            raise
        native = {
            "COMPLETED": RunStatus.FINISHED,
            "BLOCKED": RunStatus.FAILED,
            "FAILED": RunStatus.FAILED,
            "KILLED": RunStatus.KILLED,
        }[status]
        self.store.update_run_info(run_id, native, int(time.time() * 1000), None)
