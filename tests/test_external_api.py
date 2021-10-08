import pytest
from fastapi import status

from core.utils.external_api import external_api_call
from tests.utils.pytest_utils import MockResponse, add_marks


@add_marks('aux', 'external_api', 'negative_case')
def test_external_api_call_bad_request_raises_connection_error_on_400_negative_case(mocker):
    mocker.patch(
        "core.utils.external_api.requests.get", return_value=MockResponse(json_data={}, status_code=status.HTTP_400_BAD_REQUEST)
    )
    with pytest.raises(ConnectionError, match='External api error or API unavailable'):
        external_api_call('', '')


@add_marks('aux', 'external_api', 'negative_case')
def test_external_api_call_bad_request_raises_connection_error_on_404_negative_case(mocker):
    mocker.patch(
        "core.utils.external_api.requests.get", return_value=MockResponse(json_data={
            'message': 'No HTTP resource was found that matches the request URI '},
            # In this case there's no need to add this msg, cause we don't use it, so it's kinda redundant
            status_code=status.HTTP_404_NOT_FOUND)
    )
    with pytest.raises(ConnectionError, match='External api error or API unavailable'):
        external_api_call('', '')


@add_marks('aux', 'external_api', 'negative_case')
def test_external_api_call_no_matching_result_negative_case(mocker):
    mocked_response_data = {
        "Count": 1,
        "Message": "Response returned successfully",
        "SearchCriteria": "Make:honda",
        "Results": [
            {"Make_ID": 474, "Make_Name": 'HONDA', "Model_ID": 1861, "Model_Name": "Accord"},
        ]
    }
    mocker.patch(
        "core.utils.external_api.requests.get",
        return_value=MockResponse(
            json_data=mocked_response_data,
            status_code=status.HTTP_200_OK
        )
    )
    with pytest.raises(ValueError, match='No matching result in external api for Honda Civic'):
        external_api_call(car_make="Honda", car_model="Civic")


@add_marks('aux', 'external_api', 'positive')
def test_external_api_call_positive_case(mocker):
    mocked_response_data = {
        "Count": 1,
        "Message": "Response returned successfully",
        "SearchCriteria": "Make:honda",
        "Results": [
            {"Make_ID": 474, "Make_Name": 'HONDA', "Model_ID": 1861, "Model_Name": "Accord"},
        ]
    }
    mocker.patch(
        "core.utils.external_api.requests.get",
        return_value=MockResponse(
            json_data=mocked_response_data,
            status_code=status.HTTP_200_OK
        )
    )
    resp = external_api_call(car_make="Honda", car_model="Accord")
    assert resp == [
        {"Make_ID": 474, "Make_Name": 'HONDA', "Model_ID": 1861, "Model_Name": "Accord"},
    ]
