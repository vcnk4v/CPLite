import os
import time
import logging
import threading

from utils.messaging import RabbitMQClient
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class NotificationConsumer:
    def __init__(self):
        self.client = RabbitMQClient()
        self.service = NotificationService()
        self.exchange_name = "task_events"
        self.queue_name = "notification_queue"
        self.shutdown_event = threading.Event()

    def setup(self):
        """Set up exchanges and queues"""
        try:
            # Setup task events exchange
            self.client.setup_exchange(self.exchange_name)

            # Setup task queue with bindings
            self.client.setup_queue(
                self.queue_name,
                exchange_name=self.exchange_name,
                routing_key="task.batch_created",  # Subscribe to all task.created events
            )

            # Setup contest notifications exchange
            contest_exchange = "codeforces_notifications"
            self.client.setup_exchange(contest_exchange)

            # Setup contest queue with bindings
            contest_queue = "contest_notification_queue"
            self.client.setup_queue(
                contest_queue,
                exchange_name=contest_exchange,
                routing_key="notifications.contest.upcoming",  # Subscribe to all contest notifications
            )

            # Set up consuming from the contest queue
            self.client.consume(contest_queue, self.callback)

            logger.info("Notification consumer setup complete")
        except Exception as e:
            logger.error(f"Error setting up consumer: {e}")
            raise

    def callback(self, message, message_type):
        """Process incoming messages"""
        try:
            logger.info(f"Received message of type {message_type}")
            self.service.process_message(message, message_type)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def start(self):
        """Start consuming messages"""
        try:
            logger.info("Starting notification consumer...")
            self.setup()
            self.client.consume(self.queue_name, self.callback)

            # This will block until we call stop()
            while not self.shutdown_event.is_set():
                try:
                    self.client.start_consuming()
                except Exception as e:
                    logger.error(f"Consumer error: {e}")
                    time.sleep(5)  # Wait before reconnecting
                    self.client.connect()  # Reconnect

        except KeyboardInterrupt:
            logger.info("Stopping consumer due to keyboard interrupt")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error in consumer: {e}")
            self.stop()

    def stop(self):
        """Stop the consumer"""
        self.shutdown_event.set()
        if self.client:
            try:
                # Stop consuming and close connection
                if self.client.channel and self.client.channel.is_open:
                    self.client.channel.stop_consuming()
                self.client.close()
            except Exception as e:
                logger.error(f"Error closing client: {e}")
