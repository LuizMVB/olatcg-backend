import os
from typing import Dict
import pika
import json

class RabbitmqPublisher:
    def __init__(self, exchange, routing_key) -> None:
        self.__host = "rabbitmq"
        self.__port = 5672
        self.__username = os.environ.get("RABBITMQ_DEFAULT_USER")
        self.__password = os.environ.get("RABBITMQ_DEFAULT_PASS")
        self.__exchange = exchange
        self.__routing_key = routing_key
        self.__channel = self.__create_channel()

    def __create_channel(self):
        connection_parameters = pika.ConnectionParameters(
            host=self.__host,
            port=self.__port,
            credentials=pika.PlainCredentials(
                username=self.__username,
                password=self.__password
            )
        )

        channel = pika.BlockingConnection(connection_parameters).channel()
        return channel

    def send_message(self, body: Dict):
        self.__channel.basic_publish(
            exchange=self.__exchange,
            routing_key=self.__routing_key,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )