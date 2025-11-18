import pika
import json
import os
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.host = os.getenv("RABBITMQ_HOST", "rabbitMQ")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.user = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")

    def connect(self):
        """Establish connection to RabbitMQ server"""
        if self.connection is None or self.connection.is_closed:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

    def close(self):
        """Close the connection"""
        if self.connection and self.connection.is_open:
            self.connection.close()

    def setup_exchange(self, exchange_name, exchange_type="topic"):
        """Setup the exchange if it doesn't exist"""
        self.connect()
        self.channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type, durable=True
        )

    def setup_queue(self, queue_name, exchange_name=None, routing_key=None):
        """Setup a queue and optionally bind it to an exchange"""
        self.connect()
        self.channel.queue_declare(queue=queue_name, durable=True)

        if exchange_name and routing_key:
            self.channel.queue_bind(
                queue=queue_name, exchange=exchange_name, routing_key=routing_key
            )

    def publish(self, exchange_name, routing_key, message, message_type=None):
        """Publish a message to the exchange"""
        self.connect()

        # Add message type as a property if provided
        properties = None
        if message_type:
            properties = pika.BasicProperties(
                content_type="application/json",
                type=message_type,
                delivery_mode=2,  # makes message persistent
            )

        # Convert message to JSON if it's a dict
        if isinstance(message, dict):
            message = json.dumps(message)

        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=message,
            properties=properties,
        )

    def consume(self, queue_name, callback):
        """Set up a consumer for a queue"""
        self.connect()

        @wraps(callback)
        def wrapped_callback(ch, method, properties, body):
            try:
                # Try to parse JSON
                if properties.content_type == "application/json":
                    message = json.loads(body)
                else:
                    message = body.decode()

                callback(message, properties.type)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=queue_name, on_message_callback=wrapped_callback
        )

    def start_consuming(self):
        """Start consuming messages"""
        self.channel.start_consuming()
