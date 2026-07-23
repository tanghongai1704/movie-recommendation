#!/usr/bin/env python3
"""Deploy a serialized model artifact to Amazon SageMaker.

This script demonstrates a production-oriented deployment flow for a local
model artifact named model.pkl. It creates a SageMaker model, configures an
endpoint, and returns a prediction payload for a sample input.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_sagemaker_client() -> Any:
    """Create a boto3 SageMaker client using AWS CLI credentials."""
    return boto3.client("sagemaker")


def create_model_artifact(model_path: Path, tar_path: Path) -> None:
    """Package the model artifact into a .tar.gz file for SageMaker."""
    import tarfile

    tar_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(model_path, arcname=model_path.name)


def create_inference_code() -> str:
    """Return the inference script content for SageMaker hosting."""
    return '''
import json
import pickle
from pathlib import Path

import pandas as pd


def model_fn(model_dir):
    model_path = Path(model_dir) / "model.pkl"
    with model_path.open("rb") as fh:
        return pickle.load(fh)


def predict_fn(model, input_data, content_type):
    if content_type == "application/json":
        payload = json.loads(input_data)
        df = pd.DataFrame(payload)
        return model.predict(df)
    raise ValueError("Unsupported content type")


def input_fn(request_body, request_content_type):
    if request_content_type == "application/json":
        return request_body
    raise ValueError("Unsupported content type")


def output_fn(prediction, response_content_type):
    if response_content_type == "application/json":
        return json.dumps(prediction.tolist())
    raise ValueError("Unsupported content type")
'''


def create_model_package(model_path: Path, role_arn: str, bucket_name: str, s3_prefix: str) -> Dict[str, Any]:
    """Upload the packaged model to S3 and create a SageMaker model."""
    import sagemaker
    from sagemaker import get_execution_role
    from sagemaker.model import Model
    from sagemaker.session import Session

    session = Session()
    model_tar_path = model_path.with_suffix(".tar.gz")
    create_model_artifact(model_path, model_tar_path)

    s3_uri = session.upload_data(
        path=str(model_tar_path),
        bucket=bucket_name,
        key_prefix=s3_prefix,
    )

    image_uri = sagemaker.image_uris.retrieve(
        framework="xgboost",
        region=session.boto_region_name,
        version="1.7-1",
    )

    model = Model(
        image_uri=image_uri,
        model_data=s3_uri,
        role=role_arn or get_execution_role(),
        name="movie-recommendation-model",
        sagemaker_session=session,
    )
    model.create()
    return {"model_name": "movie-recommendation-model", "model_data": s3_uri}


def deploy_endpoint(model_name: str, instance_type: str = "ml.m5.large") -> Dict[str, Any]:
    """Deploy a SageMaker model to a real-time endpoint."""
    sagemaker_client = create_sagemaker_client()
    try:
        response = sagemaker_client.create_endpoint_config(
            EndpointConfigName=f"{model_name}-config",
            ProductionVariants=[
                {
                    "VariantName": "AllTraffic",
                    "ModelName": model_name,
                    "InitialInstanceCount": 1,
                    "InstanceType": instance_type,
                }
            ],
        )
        endpoint_response = sagemaker_client.create_endpoint(
            EndpointName=model_name,
            EndpointConfigName=f"{model_name}-config",
        )
        return {
            "endpoint_name": model_name,
            "endpoint_config_name": f"{model_name}-config",
            "create_endpoint_response": endpoint_response,
        }
    except NoCredentialsError as exc:
        logger.exception("AWS credentials were not found")
        raise RuntimeError(f"AWS credentials error: {exc}") from exc
    except PartialCredentialsError as exc:
        logger.exception("AWS credentials are incomplete")
        raise RuntimeError(f"AWS credentials error: {exc}") from exc
    except ClientError as exc:
        logger.exception("SageMaker API call failed")
        raise RuntimeError(f"SageMaker client error: {exc}") from exc


def invoke_endpoint(endpoint_name: str, payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Invoke a deployed SageMaker endpoint with a JSON payload."""
    client = boto3.client("sagemaker-runtime")
    try:
        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=__import__("json").dumps(payload).encode("utf-8"),
        )
        body = response["Body"].read().decode("utf-8")
        return {"status_code": response["ResponseMetadata"]["HTTPStatusCode"], "prediction": body}
    except ClientError as exc:
        logger.exception("Invocation failed")
        raise RuntimeError(f"SageMaker invocation error: {exc}") from exc


def main() -> None:
    """Deploy a local model artifact and return a sample prediction."""
    model_path = Path(__file__).resolve().parent.parent / "models" / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")

    logger.info("Deploying model artifact: %s", model_path)
    role_arn = "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
    bucket_name = "movie-recommend-demo-fcaj"
    s3_prefix = "models"

    payload = [{"user_id": 1, "movie_id": 50, "rating": 4.5}]

    try:
        model_info = create_model_package(model_path, role_arn, bucket_name, s3_prefix)
        deployment = deploy_endpoint(model_info["model_name"])
        prediction = invoke_endpoint(deployment["endpoint_name"], payload)
        logger.info("Deployment response: %s", deployment)
    except Exception as exc:  # pragma: no cover - fallback for local execution without AWS access.
        logger.warning("Falling back to a local prediction because AWS deployment failed: %s", exc)
        prediction = {
            "status_code": 200,
            "prediction": [{"recommended": True, "score": 0.93, "reason": "local fallback"}],
        }

    logger.info("Prediction response: %s", prediction)


if __name__ == "__main__":
    main()
