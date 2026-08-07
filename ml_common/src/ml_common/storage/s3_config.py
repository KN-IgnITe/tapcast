from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Config(BaseSettings):
    """Configuration required to connect to S3-compatible storage."""

    s3_host: str = Field("localhost", validation_alias="S3_HOST")
    s3_port: int = Field(9000, validation_alias="S3_PORT")

    aws_access_key_id: str = Field(validation_alias="MINIO_ROOT_USER")
    aws_secret_access_key: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    region_name: str = Field("us-east-1", validation_alias="S3_REGION")

    bucket_name: str = Field("tapcast-models", validation_alias="S3_BUCKET_NAME")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    @property
    def endpoint_url(self) -> str:
        """Build the S3-compatible endpoint URL from host and port."""

        return f"http://{self.s3_host}:{self.s3_port}"

    def get_client_config(self) -> dict[str, str]:
        """Return parameters required to initialize boto3 S3 client."""

        return {
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.region_name,
        }
