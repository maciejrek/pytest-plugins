import tempfile
from typing import Iterator

import pytest
from fastapi import status
from pytest_mock import MockerFixture
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from core.models import models
from core.models.database import Base
from core.utils.database_utils import create_car_record, create_rate_record
from tests.utils.pytest_utils import add_marks

# Using pytest-postgresql doesn't mean that we don't need to install
# postgres on machine. It's required to make everything work
socket_dir = tempfile.TemporaryDirectory()
postgresql_my_proc = factories.postgresql_proc(port=None, unixsocketdir=socket_dir.name)
postgresql_my = factories.postgresql("postgresql_my_proc")


@pytest.fixture
def base_session(postgresql_my, caplog) -> Iterator[Session]:
    """
    Basic pytest fixture, will mock empty session in postgres
    """

    # caplog.set_level(logging.INFO)
    def dbcreator():
        return postgresql_my.cursor().connection

    engine = create_engine("postgresql+psycopg2://", creator=dbcreator)
    Base.metadata.create_all(engine)
    SQLa_session = sessionmaker(bind=engine)
    session = SQLa_session()
    yield session
    session.close()


@pytest.fixture
def session_with_single_car(base_session: Session):
    """
    Extended session fixture. Yields session with single car record in db.
    """
    session = base_session
    car = models.Car(make='Honda', model='Civic')
    session.add(car)
    session.commit()
    yield session


def mock_add_record_raise_sqlalchemy_error(*args):
    """
    Used to mock 'add_record' method from database_utils.
    Can be used with *args or exact same args of method [(record, db) in this case]
    """
    raise SQLAlchemyError('Custom mocked error msg')


@add_marks('negative_case', 'model', 'car')
def test_create_car_record_car_already_exist_negative_case(session_with_single_car: Session):
    assert len(session_with_single_car.query(models.Car).all()) == 1
    status_code, resp = create_car_record('Honda', 'Civic', session_with_single_car)
    assert status_code == status.HTTP_400_BAD_REQUEST
    assert resp == {"error": "Record exists."}
    assert len(session_with_single_car.query(models.Car).all()) == 1


@add_marks('negative_case', 'model', 'car')
def test_create_car_record_db_exception_negative_case(base_session: Session, mocker: MockerFixture):
    mocker.patch('core.utils.database_utils.add_record', new=mock_add_record_raise_sqlalchemy_error)
    status_code, resp = create_car_record('Honda', 'Civic', base_session)
    assert status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert resp == {'error': "Custom mocked error msg"}
    assert len(base_session.query(models.Car).all()) == 0


@add_marks('positive_case', 'model', 'car')
def test_create_car_record_positive_case(base_session: Session):
    status_code, resp = create_car_record('Honda', 'Civic', base_session)
    assert status_code == status.HTTP_200_OK
    assert resp == {'message': "Car record created."}
    assert len(base_session.query(models.Car).all()) == 1


@add_marks('negative_case', 'model', 'rate')
def test_create_rate_record_car_record_doesnt_exist_negative_case(base_session: Session):
    status_code, resp = create_rate_record(1, 5, base_session)
    assert status_code == status.HTTP_400_BAD_REQUEST
    assert resp == {"error": "Car record doesn't exists."}
    assert len(base_session.query(models.Rate).all()) == 0


@add_marks('negative_case', 'model', 'rate')
def test_create_rate_record_db_exception_negative_case(session_with_single_car: Session, mocker: MockerFixture):
    mocker.patch('core.utils.database_utils.add_record', new=mock_add_record_raise_sqlalchemy_error)
    status_code, resp = create_rate_record(1, 5, session_with_single_car)
    assert status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert resp == {'error': "Custom mocked error msg"}
    assert len(session_with_single_car.query(models.Rate).all()) == 0


@add_marks('positive_case', 'model', 'rate')
def test_create_rate_record_positive_case(session_with_single_car: Session):
    """
    In Rate tests we need car record to make it work.
    Another place where we can use session with single car, without any additional steps.
    """
    status_code, resp = create_rate_record(1, 5, session_with_single_car)
    assert status_code == status.HTTP_200_OK
    assert resp == {'message': "Rate record created."}
    assert len(session_with_single_car.query(models.Rate).all()) == 1


@add_marks('positive_case', 'model', 'rate', 'car')
def test_create_rade_modify_avg_in_car_ugly(session_with_single_car: Session):
    car_list = session_with_single_car.query(models.Car).all()
    assert len(car_list) == 1
    assert car_list[0].avg_rating == 0.0
    assert len(session_with_single_car.query(models.Rate).all()) == 0

    create_rate_record(1, 5, session_with_single_car)
    assert len(session_with_single_car.query(models.Rate).all()) == 1

    assert session_with_single_car.query(models.Car).all()[0].avg_rating == 5

    create_rate_record(1, 4, session_with_single_car)
    assert len(session_with_single_car.query(models.Rate).all()) == 2

    assert session_with_single_car.query(models.Car).all()[0].avg_rating == 4.5

    create_rate_record(1, 3, session_with_single_car)
    assert len(session_with_single_car.query(models.Rate).all()) == 3

    assert session_with_single_car.query(models.Car).all()[0].avg_rating == 4.0

    create_rate_record(1, 3, session_with_single_car)
    assert len(session_with_single_car.query(models.Rate).all()) == 4

    assert session_with_single_car.query(models.Car).all()[0].avg_rating == 3.75


@pytest.mark.parametrize(
    'rates,expected_value',
    [
        ([5], 5),
        ([5, 4], 4.5),
        ([5, 4, 3], 4),
        ([5, 4, 3, 3], 3.75),  # Change something here to show test results
        ([5, 4, 3, 3, 2], 3.4)

    ]
)
@add_marks('positive_case', 'model', 'rate', 'car')
def test_create_rade_modify_avg_in_car_sexy(session_with_single_car: Session, rates, expected_value):
    car_list = session_with_single_car.query(models.Car).all()
    assert len(car_list) == 1
    assert car_list[0].avg_rating == 0.0
    assert len(session_with_single_car.query(models.Rate).all()) == 0

    for rate in rates:
        create_rate_record(1, rate, session_with_single_car)

    assert len(session_with_single_car.query(models.Rate).all()) == len(rates)
    assert session_with_single_car.query(models.Car).all()[0].avg_rating == expected_value


"""
That's all in this part, there's no need to cover 100% :D
"""
