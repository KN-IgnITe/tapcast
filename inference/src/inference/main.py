import logging
import os
from concurrent import futures
from pathlib import Path

import grpc

from inference.artifacts.model_bundle_loader import download_model_bundle_from_s3
from inference.pb.ping.v1 import ping_pb2, ping_pb2_grpc

MODEL_BUNDLE_DIR = Path("artifacts/production")


def prepare_model_bundle() -> Path:
    """Download model bundle before starting inference service."""

    download_model_bundle_from_s3(MODEL_BUNDLE_DIR)

    return MODEL_BUNDLE_DIR


class PingServiceServicer(ping_pb2_grpc.PingServiceServicer):
    def Ping(
        self, request: ping_pb2.PingRequest, context: grpc.ServicerContext
    ) -> ping_pb2.PingResponse:
        logging.info(f"Received ping with message: {request.message}")
        return ping_pb2.PingResponse(message=f"pong from python: {request.message}")


def serve() -> None:
    inference_port = os.getenv("INFERENCE_PORT")

    if not inference_port:
        logging.error("INFERENCE_PORT environment variable must be set")
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ping_pb2_grpc.add_PingServiceServicer_to_server(PingServiceServicer(), server)
    server.add_insecure_port(f"[::]:{inference_port}")
    server.start()
    logging.info(f"Server started on port {inference_port}")
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prepare_model_bundle()
    serve()
