import hashlib
import hmac
from django.contrib.auth.models import User
from omnibus.api import publish
from omnibus.factories import websocket_connection_factory

import settings


def user_socket_token(user_id):
    # 
    return hmac.new(settings.SECRET_KEY, str(user_id), hashlib.sha1).hexdigest()


def connection_factory(auth_class, pubsub):
    class GeneratedConnection(websocket_connection_factory(auth_class, pubsub)):
        # see docs/SOCKETS for info on messages and 'POS' protocol
        #
        #def close_connection(self):
        #    print 'closed connection'
        #    return super(GeneratedConnection, self).close_connection()
        #
        #def open_connection(self):
        #    print 'opened connection'
        #    return super(GeneratedConnection, self).open_connection()



        def on_message(self, msg):
            print msg

            # drop command messages (beginning with '!')
            if msg[0] != '!':
                handle_socket_message(msg)

            return super(GeneratedConnection, self).on_message(msg)

    return GeneratedConnection


def authentication_factory(*args, **kwargs):
    print args
    print kwargs
    class GeneratedUserAuthenticator(object):
        @classmethod
        def authenticate(cls, args):
            # First of all, check if we found a auth_token (assuming the connection
            # is logged in.
            print args
            if ':' in args:
                # auth token available, try to validate.
                try:
                    identifier, user_id, token = args.split(':')
                except ValueError:
                    return None

                if not cls.validate_auth_token(user_id, token):
                    return None

                # We validated the auth_token, fetch user from db for further use.
                try:
                    user = User.objects.get(pk=int(user_id), is_active=True)
                except (ValueError, User.DoesNotExist):
                    return None
            else:
                # No auth_token, assume anonymous connection.
                identifier = args
                user = None

            return cls(identifier, user)

        @classmethod
        def get_auth_token(cls, user_id):
            # Generate an auth token for the user id of a connection.
            #return hmac.new(settings.SECRET_KEY, str(user_id), hashlib.sha1).hexdigest()
            return user_socket_token(user_id)


        @classmethod
        def validate_auth_token(cls, user_id, token):
            # Compare generated auth token with received auth token.
            print cls.get_auth_token(user_id)
            return cls.get_auth_token(user_id) == token

        def __init__(self, identifier, user):
            self.identifier = identifier
            self.user = user

        def get_identifier(self):
            return self.identifier

        def can_subscribe(self, channel):
            # If a user is authenticated, subscription is allowed.
            return self.user is not None

        def can_unsubscribe(self, channel):
            # If a user is authenticated, un-subscription is allowed.
            return self.user is not None

        def can_publish(self, channel):
            # If a user is authenticated and is staff member, publishing is allowed.
            return self.user is not None and self.user.is_staff is True

    return GeneratedUserAuthenticator



def publish_to_channel(message):
    return publish(
        'channel', # the name of the channel
        'message', # the `type` of the message/event, clients use this name
        # to register event handlers
        message, # payload of the event, needs to be
        # a dict which is JSON dumpable.
        sender='server'  # sender id of the event, can be None.
    )





def handle_socket_message(msg):
    print msg
    pass