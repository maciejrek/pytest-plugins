from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from core.models import models
from core.models.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_record(record, db):
    db.add(record)
    db.commit()
    db.refresh(record)


def create_car_record(make: str, model: str, db: Session):
    if db.query(models.Car).filter_by(make=make, model=model).first():
        return status.HTTP_400_BAD_REQUEST, {"error": "Record exists."}
    try:
        db_car = models.Car(make=make, model=model)
        add_record(db_car, db)
    except SQLAlchemyError as e:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)}

    return status.HTTP_200_OK, {'message': "Car record created."}


def create_rate_record(car_id: int, rating: int, db: Session):
    if not db.query(models.Car).filter_by(id=car_id).first():
        return status.HTTP_400_BAD_REQUEST, {"error": "Car record doesn't exists."}
    try:
        db_rate = models.Rate(car_id=car_id, rating=rating)
        add_record(db_rate, db)
        avg = db.query(func.avg(models.Rate.rating).label('avg')).filter_by(car_id=car_id).first()
        car = db.query(models.Car).filter_by(id=car_id).first()
        car.avg_rating = avg[0]
        db.commit()
        db.refresh(car)
    except SQLAlchemyError as e:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)}

    return status.HTTP_200_OK, {'message': "Rate record created."}


def delete_car_record(car_id: int, db: Session):
    try:
        if db.query(models.Car).filter_by(id=car_id).delete():
            msg = 'Record Deleted'
            status_code = status.HTTP_200_OK
        else:
            msg = 'Record does not exist.'
            status_code = status.HTTP_404_NOT_FOUND
        db.commit()
    except SQLAlchemyError as e:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)}
    return status_code, msg


def get_popular(db: Session):
    try:
        cars = db.query(models.Car, func.count(models.Rate.id)).filter(models.Car.id == models.Rate.car_id).group_by(
            models.Rate.car_id).all()
        resp = {car.id: {f'{car.make} {car.model}': count} for car, count in cars}
    except SQLAlchemyError as e:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)}

    return status.HTTP_200_OK, resp


def get_all_cars(db: Session):
    try:
        resp = db.query(models.Car).all()
    except SQLAlchemyError as e:
        return status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)}
    return status.HTTP_200_OK, {car.id: car for car in resp}
