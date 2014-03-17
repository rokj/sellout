from pos.views.util import JSON_error, JSON_response

from rest_framework import parsers, renderers
from rest_framework.authentication import OAuth2Authentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.views import APIView

__author__ = 'tomaz'


def get_user_credentials(user):
    credentials = {}

    #credentials['last_group_slug'] = GroupUserRole.objects.get(user=user, group=group).group_slug
    credentials['user_id'] = user.id
    credentials['user_email'] = user.email
    credentials['other_groups'] = None
    return credentials

class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    authentication_classes = (OAuth2Authentication,)
    model = Token

    def post(self, request, backend):
        if backend == 'auth':
            serializer = self.serializer_class(data=request.DATA)
            if serializer.is_valid():
                user = serializer.object['user']
            else:
                return JSON_error(status="error", message="wrong credentials")


        else:
            return JSON_error("error", "wrong login")

        token, created = Token.objects.get_or_create(user=user)
        if user:
            user_credentials = get_user_credentials(user)
            group = "fak" # TODO
            if not group:
                group = user.homegroup

        else:
            return JSON_error("error", "this should not happen")

        return JSON_response({'token': token.key,
                         'user': user_credentials,
                         'last_group': group,
                         'status': "ok"})

        #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

obtain_auth_token = ObtainAuthToken.as_view()
