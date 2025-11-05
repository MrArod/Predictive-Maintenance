"""FastAPI service exposing turbine predictive maintenance insights.

The service pulls model outputs from a SQL database when available, with a
fallback to static JSON sample data for local development. It provides three
endpoints:

- ``/health`` for liveness checks.
- ``/predict`` returning Remaining Useful Life (RUL), failure probabilities and
  alerts per engine.
- ``/metrics`` serving KPI aggregates and trend series for dashboarding.

Authentication is handled through an ``X-API-Key`` header whose expected value is
configured via the ``PREDICTIVE_API_KEY`` environment variable (defaults to a
local development key).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EnginePrediction(BaseModel):
    engine_id: str = Field(..., description="Unique identifier for the engine")
    cycle: int = Field(..., ge=0, description="Latest observed operating cycle")
    rul: float = Field(..., ge=0, description="Remaining Useful Life estimate in cycles")
    failure_probability: float = Field(
        ..., ge=0, le=1, description="Probability of failure in the next prediction window"
    )
    alert_level: str = Field(..., description="Alert level derived from probability thresholds")
    timestamp: datetime = Field(
        ..., description="Timestamp when the prediction was generated or observed"
    )


class EngineTrend(BaseModel):
    engine_id: str
    timestamp: datetime
    rul: float
    failure_probability: float


class KPIAggregates(BaseModel):
    production_efficiency: float = Field(..., description="Overall production efficiency percentage")
    failure_rate: float = Field(..., description="Fleet failure rate percentage")
    mean_time_to_failure: float = Field(..., description="Mean cycles until failure")
    average_rul: float = Field(..., description="Average RUL across the fleet")
    downtime_cost: float = Field(..., description="Estimated downtime cost in USD per hour")


class KPITrend(BaseModel):
    metric: str
    timestamp: datetime
    value: float


class PredictResponse(BaseModel):
    generated_at: datetime
    engines: List[EnginePrediction]


class MetricsResponse(BaseModel):
    generated_at: datetime
    aggregates: KPIAggregates
    kpi_trends: List[KPITrend]
    engine_trends: List[EngineTrend]


class DataRepository:
    """Interface to load predictive maintenance outputs.

    The repository first attempts to pull data from a SQL database defined by the
    ``DATABASE_URL`` environment variable. When unavailable it falls back to a
    JSON file bundled with the project to provide sample responses that power the
    API and UI during local development.
    """

    def __init__(self, sample_path: Path, database_url: Optional[str] = None) -> None:
        self.sample_path = sample_path
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._data = {}
        self._load_data()

    def _load_data(self) -> None:
        if self.database_url and self._load_from_database():
            logger.info("Loaded predictive outputs from database at %s", self.database_url)
            return

        self._load_from_sample()
        logger.info("Loaded predictive outputs from sample dataset at %s", self.sample_path)

    def _load_from_database(self) -> bool:
        """Attempt to load data from a SQL database.

        The method expects two tables:
            - ``engine_predictions`` with columns ``engine_id``, ``cycle``, ``rul``,
              ``failure_probability``, ``alert_level`` and ``timestamp``.
            - ``kpi_trends`` with columns ``metric``, ``timestamp`` and ``value``.

        It should also expose a ``kpi_aggregates`` view/table with one row containing
        aggregate KPI columns. When the schema is missing or the driver is not
        installed the method returns ``False`` which triggers the JSON fallback.
        """

        try:
            from sqlalchemy import create_engine, text
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("SQLAlchemy not available, falling back to sample data: %s", exc)
            return False

        engine = create_engine(self.database_url, future=True)

        try:
            with engine.connect() as connection:
                prediction_rows = connection.execute(
                    text(
                        """
                        SELECT engine_id, cycle, rul, failure_probability, alert_level, timestamp
                        FROM engine_predictions
                        ORDER BY timestamp DESC
                        """
                    )
                ).mappings()
                kpi_trend_rows = connection.execute(
                    text(
                        """
                        SELECT metric, timestamp, value
                        FROM kpi_trends
                        ORDER BY timestamp
                        """
                    )
                ).mappings()
                aggregates_row = connection.execute(
                    text("SELECT * FROM kpi_aggregates LIMIT 1")
                ).mappings().first()
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("Database unavailable or schema missing, using sample data: %s", exc)
            return False

        if aggregates_row is None:
            logger.warning("kpi_aggregates table is empty; reverting to sample dataset")
            return False

        generated_at = datetime.utcnow()
        self._data = {
            "generated_at": generated_at.isoformat(),
            "engines": list(prediction_rows),
            "engine_trends": list(prediction_rows),
            "kpi_trends": list(kpi_trend_rows),
            "kpi_aggregates": dict(aggregates_row),
        }
        return True

    def _load_from_sample(self) -> None:
        with self.sample_path.open("r", encoding="utf-8") as handle:
            self._data = json.load(handle)

    def reload(self) -> None:
        """Force a reload which picks up DB changes or refreshed sample data."""

        self._load_data()

    def _iter_engines(self, engine_id: Optional[str] = None) -> Iterable[Dict[str, object]]:
        engines: List[Dict[str, object]] = self._data.get("engines", [])
        for engine in engines:
            if engine_id and engine.get("engine_id") != engine_id:
                continue
            yield engine

    def get_predictions(self, engine_id: Optional[str] = None) -> List[EnginePrediction]:
        predictions: List[EnginePrediction] = []
        for engine in self._iter_engines(engine_id):
            timestamp = engine.get("timestamp") or self._data.get("generated_at")
            predictions.append(
                EnginePrediction(
                    engine_id=str(engine["engine_id"]),
                    cycle=int(engine.get("cycle", 0)),
                    rul=float(engine.get("rul", 0)),
                    failure_probability=float(engine.get("failure_probability", 0)),
                    alert_level=str(engine.get("alert_level", "normal")),
                    timestamp=_parse_datetime(timestamp),
                )
            )
        return predictions

    def get_engine_trends(self, engine_id: Optional[str] = None) -> List[EngineTrend]:
        trend_items: List[Dict[str, object]] = self._data.get("engine_trends", [])
        results: List[EngineTrend] = []
        for item in trend_items:
            if engine_id and item.get("engine_id") != engine_id:
                continue
            results.append(
                EngineTrend(
                    engine_id=str(item["engine_id"]),
                    timestamp=_parse_datetime(item["timestamp"]),
                    rul=float(item.get("rul", 0)),
                    failure_probability=float(item.get("failure_probability", 0)),
                )
            )
        return results

    def get_metrics(self) -> KPIAggregates:
        aggregates = self._data.get("kpi_aggregates", {})
        return KPIAggregates(
            production_efficiency=float(aggregates.get("production_efficiency", 0)),
            failure_rate=float(aggregates.get("failure_rate", 0)),
            mean_time_to_failure=float(aggregates.get("mean_time_to_failure", 0)),
            average_rul=float(aggregates.get("average_rul", 0)),
            downtime_cost=float(aggregates.get("downtime_cost", 0)),
        )

    def get_kpi_trends(self) -> List[KPITrend]:
        return [
            KPITrend(
                metric=str(item["metric"]),
                timestamp=_parse_datetime(item["timestamp"]),
                value=float(item.get("value", 0)),
            )
            for item in self._data.get("kpi_trends", [])
        ]

    def generated_at(self) -> datetime:
        return _parse_datetime(self._data.get("generated_at", datetime.utcnow().isoformat()))


def _parse_datetime(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("Unable to parse datetime %s; falling back to utcnow", value)
    return datetime.utcnow()


def get_repository() -> DataRepository:
    sample_path = Path(__file__).resolve().parent / "sample_data.json"
    return DataRepository(sample_path=sample_path)


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    expected_key = os.getenv("PREDICTIVE_API_KEY", "dev-secret")
    if not expected_key:
        logger.warning("API key expected but not configured; rejecting request")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API key not configured")
    if x_api_key != expected_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


app = FastAPI(title="Predictive Maintenance Service", version="1.0.0")


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Simple health endpoint used for readiness checks."""

    return {"status": "ok"}


@app.get("/predict", response_model=PredictResponse)
def get_predictions(
    engine_id: Optional[str] = None,
    repo: DataRepository = Depends(get_repository),
    _: None = Depends(verify_api_key),
) -> PredictResponse:
    """Return the latest predictions for each engine, optionally filtered."""

    predictions = repo.get_predictions(engine_id=engine_id)
    if engine_id and not predictions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engine not found")
    return PredictResponse(generated_at=repo.generated_at(), engines=predictions)


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    engine_id: Optional[str] = None,
    repo: DataRepository = Depends(get_repository),
    _: None = Depends(verify_api_key),
) -> MetricsResponse:
    """Return aggregated KPIs and trend data used by dashboards."""

    aggregates = repo.get_metrics()
    engine_trends = repo.get_engine_trends(engine_id=engine_id)
    kpi_trends = repo.get_kpi_trends()
    return MetricsResponse(
        generated_at=repo.generated_at(),
        aggregates=aggregates,
        kpi_trends=kpi_trends,
        engine_trends=engine_trends,
    )


@app.post("/reload", status_code=status.HTTP_204_NO_CONTENT)
def reload_data(repo: DataRepository = Depends(get_repository), _: None = Depends(verify_api_key)) -> None:
    """Hot-reload the backing datastore.

    Useful for development when the SQL source or JSON fixture has changed.
    """

    repo.reload()
