from pydantic import BaseModel, ConfigDict


class QualityMetricOut(BaseModel):
    metric_key: str
    metric_value: float
    threshold: float | None
    exceeded: bool

    model_config = ConfigDict(from_attributes=True)
