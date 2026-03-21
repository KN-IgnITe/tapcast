import logging
from concurrent import futures
import os

import grpc

from inference.pb.ping.v1 import ping_pb2, ping_pb2_grpc

class PingServiceServicer(ping_pb2_grpc.PingServiceServicer):
    def Ping(self, request, context):
        logging.info(f"Received ping with message: {request.message}")
        return ping_pb2.PingResponse(message=f"pong from python: {request.message}")

def serve():
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()

