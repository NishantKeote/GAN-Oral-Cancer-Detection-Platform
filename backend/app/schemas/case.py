"""Patient and case metadata schemas."""

from pydantic import BaseModel, Field


class PatientContext(BaseModel):
    """Normalized clinical metadata associated with an analyzed case."""

    age: str = Field(default="Not provided", description="Patient age")
    sex: str = Field(default="Not provided", description="Biological sex")
    tobacco: str = Field(default="Not provided", description="Tobacco consumption history")
    alcohol: str = Field(default="Not provided", description="Alcohol consumption history")
    lesion_site: str = Field(default="Not provided", description="Anatomical location of the oral lesion")
    magnification: str = Field(default="Not provided", description="Histopathology image magnification")
