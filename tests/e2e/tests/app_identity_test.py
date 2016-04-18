from google.appengine.api import app_identity


def test_get_service_account_name():
    assert app_identity.get_service_account_name()


def test_get_application_id():
    assert app_identity.get_application_id()


def test_get_default_version_hostname():
    app_id = app_identity.get_application_id()
    hostname = app_identity.get_default_version_hostname()
    assert hostname
    assert app_id in hostname


def test_get_access_token():
    token = app_identity.get_access_token(
        ['https://www.googleapis.com/auth/userinfo.email'])
    assert token
    # TODO: Verify token with tokeninfo endpoint.


def test_get_default_gcs_bucket_name():
    assert app_identity.get_default_version_hostname()


def test_sign_blob():
    cleartext = 'Curiouser and curiouser!'
    key_name, signature = app_identity.sign_blob(cleartext)
    assert key_name
    assert signature
