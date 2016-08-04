import os
from collections import OrderedDict
import hmac
from time import time
import requests
from django.db import models


# Provided via .env.secret file
# ---
# SHOPIFY_API_KEY
# SHOPIFY_SECRET
# ---
SHOPIFY_SCOPES = 'read_script_tags,write_script_tags'
SHOPIFY_AUTH_URL = "https://{shop_name}.myshopify.com/admin/oauth/authorize?"\
                   "client_id={api_key}"\
                   "&scope={scopes}"\
                   "&redirect_uri={redirect_uri}"\
                   "&state={nonce}"


class ShopifyShop(models.Model):
    access_token = models.CharField(max_length=128)
    shop_name = models.CharField(max_length=255)
    scopes = models.TextField()

    @staticmethod
    def get_intall_url(request, shop_name):
        """Returns a shopify install url with generated nonce."""

        # Create our nonce and save it to the session so we can verify the
        # authenticity of the response received from Shopify (among other checks)
        nonce = int(time())
        request.session[nonce] = True

        # Create the url based on nonce and shop name
        install_url = SHOPIFY_AUTH_URL.format(
            shop_name=shop_name,
            api_key=os.environ.get('SHOPIFY_API_KEY'),
            scopes=SHOPIFY_SCOPES,
            redirect_uri='https://' + request.get_host() + '/auth',
            nonce=nonce,
        )
        return install_url

    @staticmethod
    def send_auth_request(request):
        resp = requests.post(
            'https://shopifygreen.myshopify.com/admin/oauth/access_token',
            data=dict(
                client_id=os.environ.get('SHOPIFY_API_KEY'),
                client_secret=os.environ.get('SHOPIFY_SECRET'),
                code=request.GET.get('code')
            )
        )
        return resp

    @classmethod
    def create(cls, resp, request):
        json_resp = resp.json()

        # TODO: check to ensure the scopes returned match what we need
        if resp.status_code == 200 and 'access_token' in json_resp:
            cls.objects.create(
                access_token=json_resp.get('access_token'),
                shop_name=request.GET.get('shop'),
                scopes=json_resp.get('scope'),
            )

# -----------------------------------------------------------------------------

def compose_hmac_message(dict_params):
    if 'hmac' in dict_params:
        dict_params.pop('hmac')

    dict_params = OrderedDict(sorted(dict_params.items()))

    message = ''
    for k, v in dict_params.items():
        message += k + '=' + v + '&'
    message = message.strip('&')
    return message


def validate_shopify_hmac(request):
    """Responses from Shopify include a series of GET parameters.
    In order to verify the authenticity of this response, Shopify also provides a
    hmac parameter that is computed based on all the GET parameters (lexical order).
    (Note: The computed hmac does not include the hmac GET parameter itself).
    """
    if 'hmac' not in request.GET:
        return False

    composed_message = compose_hmac_message(request.GET.copy())
    computed_hmac = hmac.new(
        os.environ.get('SHOPIFY_SECRET').encode(),
        composed_message.encode(),
        'sha256'
    )

    if computed_hmac.hexdigest() == request.GET['hmac']:
        return True
    else:
        return False
