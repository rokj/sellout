from omnibus.api import publish
from omnibus.factories import websocket_connection_factory









def test_connection_factory(auth_class, pubsub):
    class GeneratedConnection(websocket_connection_factory(auth_class, pubsub)):

        def close_connection(self):
            print 'closed connection'
            return super(GeneratedConnection, self).close_connection()


        def open_connection(self):
            # Initializing a zmq subscriber socket to handle messages from other
            # connection or from python-api calls.
            print 'opened connection'
            return super(GeneratedConnection, self).open_connection()

        def on_message(self, msg):
            print msg
            return super(GeneratedConnection, self).on_message(msg)

    return GeneratedConnection


def publish_to_channel(message):
    return publish(
        'channel', # the name of the channel
        'message', # the `type` of the message/event, clients use this name
        # to register event handlers
        message, # payload of the event, needs to be
        # a dict which is JSON dumpable.
        sender='server'  # sender id of the event, can be None.
    )