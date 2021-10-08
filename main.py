from fastapi import FastAPI, Depends, Response, status
from core.schemas import schema
from core.utils.external_api import external_api_call
from core.utils.database_utils import get_db, create_car_record, create_rate_record, delete_car_record, get_popular, get_all_cars
from sqlalchemy.orm import Session
import requests

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/cars/")
async def get_cars_list(response: Response, db: Session = Depends(get_db)):
    status_code, resp = get_all_cars(db)
    response.status_code = status_code
    return resp


@app.post("/cars/")
async def create_car(car: schema.CarBase, response: Response, db: Session = Depends(get_db)):
    try:
        # We don't need a data from external api, but external api call is designed to return received data
        external_api_call(car.model, car.make)
        # Both exceptions point to error on external api side. I've used general 500 code, but it could be changed
        # to be more specific (500 for the first exception, and 503 for the second one ?)
    except (requests.exceptions.RequestException, ConnectionError) as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"external_api_error": f"{e}"}
    except AttributeError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"external_api_error": f"{e}"}
    except ValueError as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"external_api_error": f"{e}"}
    status_code, resp = create_car_record(car.make, car.model, db)
    response.status_code = status_code
    return resp


@app.post("/rate/")
async def create_rate(rate: schema.Rate, response: Response, db: Session = Depends(get_db)):
    status_code, resp = create_rate_record(rate.car_id, rate.rating, db)
    response.status_code = status_code
    return resp


@app.delete("/cars/{id}")
async def delete_car(pk: int, response: Response, db: Session = Depends(get_db)):
    status_code, resp = delete_car_record(pk, db)
    response.status_code = status_code
    return resp


@app.get("/popular/")
async def get_popular(response: Response, db: Session = Depends(get_db)):
    status_code, resp = get_popular(db)
    response.status_code = status_code
    return resp
