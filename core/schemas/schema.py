from pydantic import BaseModel, validator


class CarBase(BaseModel):
    make: str
    model: str

    @validator('make', 'model')
    def fields_must_be_stripped_title(cls, val):
        return val.strip().title()


class Car(CarBase):
    id: int
    avg_rating: float

    class Config:
        orm_mode = True


class Rate(BaseModel):
    car_id: int
    rating: int

    @validator('rating')
    def rating_must_be_in_range(cls, val):
        if val > 5 or val < 1:
            raise ValueError('Rating value should be between 1-5')
        return val
