import os
import hmac
from unittest.mock import MagicMock, patch
from django.test import TestCase

from . import models
from . import views
from .models import ShopifyShop


class ShopifyShopModelTestCase(TestCase):
    def test_get_install_url_adds_nonce_to_session(self):
        request = MagicMock()
        request.session = {}

        ShopifyShop.get_intall_url(request, 'test_shop')
        self.assertEqual(len(request.session.keys()), 1)

    def test_create_method_noops_with_invalid_response(self):
        request = MagicMock()
        request.GET = dict(shop='testshop')

        test_resp = MagicMock()
        test_resp.json.return_value = {}

        ShopifyShop.create(test_resp, request)

        self.assertEqual(ShopifyShop.objects.count(), 0)


    def test_create_method_creates_record_with_valid_response(self):
        request = MagicMock()
        request.GET = dict(shop='testshop')

        test_resp = MagicMock()
        test_resp.json.return_value = {
            'access_token': '123faketoken',
            'scope': 'read_scope, write_scope'
        }
        test_resp.status_code = 200

        ShopifyShop.create(test_resp, request)

        self.assertEqual(ShopifyShop.objects.count(), 1)


class ModelUtilsTestCase(TestCase):
    def test_message_composed_correctly(self):
        """Ensure the message is composed correctly - with proper delimiters
        and in the correct order."""
        test_message_params = dict(foo='bar', acme='biz', baz='qux')
        test_message = 'acme=biz&baz=qux&foo=bar'

        message = models.compose_hmac_message(test_message_params)

        split_message = message.split('&')
        self.assertEqual(split_message[0], 'acme=biz')
        self.assertEqual(split_message[1], 'baz=qux')
        self.assertEqual(split_message[2], 'foo=bar')
        self.assertEqual(test_message, message)

    def test_validate_shopify_hmac_returns_false_without_hmac_key(self):
        request = MagicMock()
        request.GET = {}
        self.assertEqual(False, models.validate_shopify_hmac(request))

    def test_validate_shopify_hmac_returns_true_with_valid_hmac(self):
        """Ensure that it matches a test/reference hmac we prepare."""
        ref_hmac = get_ref_hmac()

        request = MagicMock()
        request.GET = dict(hmac=ref_hmac, foo='bar', biz='baz')

        self.assertEqual(True, models.validate_shopify_hmac(request))


class ViewsTestCase(TestCase):
    def test_app_auth_returns_forbidden_with_invalid_get_params(self):
        resp = views.app_auth(MagicMock())
        self.assertEqual(resp.status_code, 403)

    @patch('core.views.ShopifyShop')
    def test_app_auth_calls_shopify_with_valid_get_params(self, MockShopifyShop):
        ref_hmac = get_ref_hmac()

        request = MagicMock()
        request.GET = dict(hmac=ref_hmac, biz='baz', foo='bar')

        views.app_auth(request)

        self.assertEqual(MockShopifyShop.send_auth_request.called, True)


 # Utils and Helpers
 # -----------------------------------------------------------------------------------
def get_ref_hmac():
    h = hmac.new(
        os.environ['SHOPIFY_SECRET'].encode(),
        'biz=baz&foo=bar'.encode(),
        'sha256'
    )
    return h.hexdigest()
