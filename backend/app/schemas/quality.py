from pydantic import BaseModel


class QualityMetricOut(BaseModel):
    metric_key: str
    metric_value: float
    threshold: float | None
    exceeded: bool

    class Config:
        from_attributes = True
