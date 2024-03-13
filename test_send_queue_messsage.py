import os
import json
import logging
import pika
import traceback
import datetime  
import azure.functions as func

# This Azure Function is defined as a Blueprint.
# To find the main function definition, search for this variable in this file
function_send_queue_messsage = func.Blueprint()

def get_rabbitmq_channel(rabbitmq_connection, exchange_name, queue_name, routing_key):
    """
    Returns a RabbitMQ pika.channel.Channel
    """
    logging.info("In get_rabbitmq_channel().")

    channel = rabbitmq_connection.channel()

    channel.exchange_declare(exchange=exchange_name,
                             exchange_type="direct",
                             durable=True)

    channel.queue_declare(queue=queue_name,
                          durable=True,
                          arguments={"x-single-active-consumer": True})

    # Establish relationship between exchange and queue
    channel.queue_bind(exchange=exchange_name,
                       queue=queue_name,
                       routing_key=routing_key)

    return channel


def notify_nemo(payload):
    """
    Pushes the JSON payload to the RabbitMQ queue.
    This queues the NeMO submission for the next step in ingest.
    """
    logging.info("In notify_nemo().")

    payload_str = json.dumps(payload)
    logging.info("payload:\n{}".format(payload_str, indent=2))

    try:
        # Get RabbitMQ configuration from environment
        rabbitmq_host = os.getenv("RABBITMQ_HOST")
        rabbitmq_port = int(os.getenv("RABBITMQ_PORT"))
        rabbitmq_virtual_host = os.getenv("RABBITMQ_VIRTUAL_HOST")
        rabbitmq_username = os.getenv("RABBITMQ_USERNAME")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
        publisher_exchange_name = os.getenv("RABBITMQ_PUBLISHER_EXCHANGE_NAME")
        publisher_queue_name = os.getenv("RABBITMQ_PUBLISHER_QUEUE_NAME")
        publisher_routing_key = os.getenv("RABBITMQ_PUBLISHER_ROUTING_KEY")

        # RabbitMQ credentials for publisher
        rabbitmq_credentials = pika.PlainCredentials(
            username=rabbitmq_username,
            password=rabbitmq_password
        )

        # Parameters for RabbitMQ producer
        cxn_parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            virtual_host=rabbitmq_virtual_host,
            credentials=rabbitmq_credentials
        )

        # Get connection to RabbitMQ instance on GCP
        rabbitmq_connection = pika.BlockingConnection(
            parameters=cxn_parameters
        )

        # Get a connection channel.
        channel = get_rabbitmq_channel(
            rabbitmq_connection,
            publisher_exchange_name,
            publisher_queue_name,
            publisher_routing_key
        )

        # Publish message to the next step's queue.
        channel.basic_publish(
            exchange=publisher_exchange_name,
            routing_key=publisher_routing_key,
            body=payload_str,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

        rabbitmq_connection.close()
        return f"RabbitMQ message published to {publisher_queue_name} queue."
    except Exception:
        tb_message = traceback.format_exc()
        return f"An error occurred while publishing message to RabbitMQ: {tb_message}"


@function_send_queue_messsage.route(route='send_queue_messsage')
def send_queue_messsage(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function send_queue_messsage processed a request.')

    payload = {
        'message_text': 'This is test message',
        'timestamp': datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S')
    }

    try:
        result = notify_nemo(payload)
        if 'RabbitMQ message published' in result:
            return func.HttpResponse(result)
        else:
            return func.HttpResponse(result, status_code=400)

    except Exception as e:
        return func.HttpResponse(f"Failed to send queue message: \n{str(e)}", status_code=400)