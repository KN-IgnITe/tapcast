from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Config(BaseSettings):
    s3_host: str = Field("localhost", validation_alias="S3_HOST")
    s3_port: int = Field(9000, validation_alias="S3_PORT")

    aws_access_key_id: str = Field(validation_alias="MINIO_ROOT_USER")
    aws_secret_access_key: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    region_name: str = Field("us-east-1", validation_alias="S3_REGION")

    # Defaults to MINIO_ROOT_USER if a bucket name env variable is not provided
    bucket_name: str = Field("bucket", validation_alias="MINIO_ROOT_USER")

    # This field will be computed dynamically via model_validator
    endpoint_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=False,  # Changed to False to allow post-init endpoint computing
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def compute_endpoint_url(self) -> "S3Config":
        """
        Dynamically builds the endpoint URL for MinIO using host and port.
        """
        self.endpoint_url = f"http://{self.s3_host}:{self.s3_port}"
        return self

    def get_client_config(self) -> dict:
        """
        Returns a dictionary with parameters required to initialize boto3.client.
        """
        return {
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.region_name,
        }
