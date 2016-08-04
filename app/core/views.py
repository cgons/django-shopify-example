import os
import hmac
import requests

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden

from . import models
from .models import ShopifyShop


# ESDK Views
# -----------------------------------------------------------------------------
def esdk_home(request):
    # TODO:
    # 1. verify request is authentic with hmac (decorator func.)
    # 2. verify that shop exists in our records

    return render(request, 'core/esdk/home.jinja2')


# Shopify App Views
# -----------------------------------------------------------------------------
def app_install(request):
    install_url = ShopifyShop.get_intall_url(request, 'shopifygreen')
    return render(request, 'core/app/home.jinja2', dict(
        install_url=install_url
    ))


def app_auth(request):
    # We stored a nonce in the session that we'll now use as an additional
    # measure to verify this app installation request.
    # Let's grab the nonce from the session, save it in a local variable and
    # then remove it from the session to keep our session clean.

    # TODO: Remove nonce from session

    if not models.validate_shopify_hmac(request):
        return HttpResponseForbidden()

    # Once verified, send a request to Shopify asking for an access token
    resp = ShopifyShop.send_auth_request(request)

    # On success, create a record in our DB for the shop and its access token
    ShopifyShop.create(resp, request)

    return HttpResponse("OKAY")


# Utils and Other methods
# -----------------------------------------------------------------------------
def validate_esdk_request():
    pass
