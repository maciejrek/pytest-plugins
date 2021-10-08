import tempfile
from typing import Iterator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_postgresql import factories
from requests.exceptions import RequestException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from core.models.database import Base
from core.utils.database_utils import get_db
from main import app
from tests.utils.pytest_utils import add_marks

# Using pytest-postgresql doesn't mean that we don't need to install
# postgres on machine. It's required to make everything work
socket_dir = tempfile.TemporaryDirectory()
postgresql_my_proc = factories.postgresql_proc(port=None, unixsocketdir=socket_dir.name)
postgresql_my = factories.postgresql("postgresql_my_proc")


@pytest.fixture
def app_client(postgresql_my, caplog) -> Iterator[Session]:
    """
    I know this one look kinda ugly, but it prepare TestClient as a fixture.
    Typically in fastapi (following docs) we'd just do it once at the beginning of the file,
    but this way we have empty db for each test, and we can separate them from each other.
    (See the diff between this file and test_db_utils)
    """

    # caplog.set_level(logging.INFO)
    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    Base.metadata.create_all(engine)
    SQLa_session = sessionmaker(bind=engine)

    def override_get_db():
        try:
            db = SQLa_session()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client


def mock_external_api_call_raise_request_exception(*args):
    raise RequestException('Custom mocked error msg')


def mock_external_api_call_raise_connection_error(*args):
    raise ConnectionError('Custom mocked error msg')


def mock_external_api_call_raise_attribute_error(*args):
    raise AttributeError('Custom mocked error msg')


def mock_external_api_call_raise_value_error(*args):
    raise ValueError('Custom mocked error msg')


def test_dummy_test(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


@add_marks('negative_case', 'api', 'car', 'post')
def test_post_cars_endpoint_external_api_raises_request_exception_negative_case(mocker, app_client):
    mocker.patch('main.external_api_call', new=mock_external_api_call_raise_request_exception)
    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'external_api_error': 'Custom mocked error msg'}


@add_marks('negative_case', 'api', 'car', 'post')
def test_post_cars_endpoint_external_api_raises_connection_error_negative_case(mocker, app_client):
    mocker.patch('main.external_api_call', new=mock_external_api_call_raise_connection_error)
    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'external_api_error': 'Custom mocked error msg'}


@add_marks('negative_case', 'api', 'car', 'post')
def test_post_cars_endpoint_external_api_raises_attribute_error_negative_case(mocker, app_client):
    mocker.patch('main.external_api_call', new=mock_external_api_call_raise_attribute_error)
    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'external_api_error': 'Custom mocked error msg'}


@add_marks('negative_case', 'api', 'car', 'post')
def test_post_cars_endpoint_external_api_raises_value_error_negative_case(mocker, app_client):
    mocker.patch('main.external_api_call', new=mock_external_api_call_raise_value_error)
    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'external_api_error': 'Custom mocked error msg'}


@add_marks('positive_case', 'api', 'car', 'post')
def test_post_cars_endpoint_positive_case(mocker, app_client):
    mocker.patch('main.external_api_call', return_value={})
    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'Car record created.'}


@add_marks('positive_case', 'api', 'car', 'get')
def test_get_cars_endpoint_positive_case(app_client):
    response = app_client.get("/cars/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}


@add_marks('positive_case', 'api', 'car', 'get', 'post')
def test_get_cars_endpoint_return_dict_of_cars(mocker, app_client):
    mocker.patch('main.external_api_call', return_value={})
    response = app_client.get("/cars/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}

    response = app_client.post("/cars/", json={'make': 'aa', 'model': 'bb'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'Car record created.'}

    response = app_client.post("/cars/", json={'make': 'cc', 'model': 'dd'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message': 'Car record created.'}

    response = app_client.get("/cars/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'1': {'avg_rating': 0.0, 'id': 1, 'make': 'Aa', 'model': 'Bb'},
                               '2': {'avg_rating': 0.0, 'id': 2, 'make': 'Cc', 'model': 'Dd'}}
