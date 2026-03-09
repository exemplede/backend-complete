from rest_framework.authentication import TokenAuthentication, get_authorization_header


class BearerOrTokenAuthentication(TokenAuthentication):
    """
    Accept both:
    - Authorization: Token <key>
    - Authorization: Bearer <key>
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if len(auth) == 1:
            return None

        if len(auth) > 2:
            return None

        keyword = auth[0].lower()
        if keyword not in (b'token', b'bearer'):
            return None

        try:
            token = auth[1].decode()
        except UnicodeError:
            return None

        return self.authenticate_credentials(token)
