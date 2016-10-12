
from tornado.testing import (
    AsyncHTTPTestCase, AsyncHTTPSTestCase, AsyncTestCase, ExpectLog, gen_test
)
from tornado.httpclient import HTTPRequest
import sfm.app


class AuthTest(AsyncHTTPSTestCase):

    def get_app(self):
        return sfm.app.make_app()

    def test_auth_response(self):
        response = self.fetch('/auth')
        self.assertEqual(response.code, 200)

    def test_auth_positive(self):
        response = self.fetch(
            '/auth', method='POST', body="login=admin&passwd=admin"
        )
        self.assertEqual(response.code, 200)

    def test_auth_negative(self):
        response = self.fetch(
            '/auth', method='POST', body="login=admin&passwd=admuin"
        )
        self.assertIn('Wrong login or password', str(response.body))