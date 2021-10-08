from typing import List

import requests
from fastapi import status


def external_api_call(car_model: str, car_make: str) -> List:
    """Call to the external api.
    Args:
        car_model (str): Car model string
        car_make (str): Car make string
    Raises:
        AttributeError: An error occuring when incorrect api url is provided
        RequestException: An error occuring during external api call
        ConnectionError: An error occuring if response code is other than 200
        ValueError: An error occuring if data specified by input parameters is not present in response
    Returns:
        List: List with data from external api, filtered by input parameters
    """
    api_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{car_make}?format=json"

    # requests.exceptions.RequestException can occure (should be handled by calling method)
    response = requests.get(url=api_url)
    if response.status_code != status.HTTP_200_OK:
        raise ConnectionError("External api error or API unavailable")
    resp = response.json()
    car = [car for car in resp.get("Results") if car.get("Model_Name").lower() == car_model.lower()]
    if not car:
        raise ValueError(f"No matching result in external api for {car_make} {car_model}")
    return car
