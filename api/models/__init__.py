# Import all model classes to make them available when importing api.models
from .models_definitions import (
    DemandData,
    WeatherData,
    GenerationData,
    DataQualityMetrics,
    SummaryData
)

from .frontend_compatibility import (
    FrontendDemandData,
    FrontendWeatherData,
    FrontendGenerationData,
    FrontendDataQualityMetrics,
    FrontendSummaryData,
)
