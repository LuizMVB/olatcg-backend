"""
Django command to wait for the database to be available.
"""
import os
import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

import pika

class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Creating blastn exchange and queue...')
        exchange_up = False
        while exchange_up is False:
            try:
                connection_parameters = pika.ConnectionParameters(
                    host='rabbitmq',
                    port=5672,
                    credentials=pika.PlainCredentials(
                        username=os.environ.get('RABBITMQ_DEFAULT_USER'),
                        password=os.environ.get('RABBITMQ_DEFAULT_PASS')
                    )
                )
                connection = pika.BlockingConnection(connection_parameters)
                channel = connection.channel()

                # Declare the exchange
                channel.exchange_declare(
                    exchange=os.environ.get('RABBITMQ_BLASTN_EXCHANGE_NAME'),
                    exchange_type=os.environ.get('RABBITMQ_BLASTN_EXCHANGE_TYPE'),
                    durable=bool(os.environ.get('RABBITMQ_BLASTN_EXCHANGE_DURABLE'))
                )

                # Declare the queue
                channel.queue_declare(
                    queue=os.environ.get('RABBITMQ_BLASTN_QUEUE_NAME'),
                    durable=True
                )

                # Bind the queue to the exchange
                channel.queue_bind(
                    exchange=os.environ.get('RABBITMQ_BLASTN_EXCHANGE_NAME'),
                    queue=os.environ.get('RABBITMQ_BLASTN_QUEUE_NAME'),
                    routing_key=os.environ.get('RABBITMQ_BLASTN_ROUTING_KEY')
                )

                connection.close()
                exchange_up = True
            except (Psycopg2OpError, OperationalError, pika.exceptions.AMQPConnectionError):
                self.stdout.write('RabbitMQ unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('RabbitMQ exchange and queue are available!'))
