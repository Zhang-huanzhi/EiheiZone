from app.core.errors import AppError, ErrorDetail, ErrorResponse, FieldError


def test_error_response_uses_the_expected_json_structure() -> None:
    response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request fields are invalid",
            field_errors=[
                FieldError(
                    field="query.limit",
                    message="Input should be less than or equal to 100",
                    type="less_than_equal",
                )
            ],
            request_id="14c58976-8643-4318-a54c-aae6f6d98422",
        )
    )

    assert response.model_dump(mode="json") == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request fields are invalid",
            "field_errors": [
                {
                    "field": "query.limit",
                    "message": "Input should be less than or equal to 100",
                    "type": "less_than_equal",
                }
            ],
            "request_id": "14c58976-8643-4318-a54c-aae6f6d98422",
        }
    }


def test_error_detail_creates_an_independent_empty_field_error_list() -> None:
    first_error = ErrorDetail(
        code="NOT_FOUND",
        message="Resource was not found",
        request_id="first-request",
    )
    second_error = ErrorDetail(
        code="NOT_FOUND",
        message="Resource was not found",
        request_id="second-request",
    )

    first_error.field_errors.append(
        FieldError(field="path.post_id", message="Not found", type="missing")
    )

    assert second_error.field_errors == []


def test_app_error_keeps_client_safe_error_information() -> None:
    field_error = FieldError(
        field="body.title",
        message="Field is required",
        type="missing",
    )
    error = AppError(
        status_code=409,
        code="POST_CONFLICT",
        message="The post cannot be changed in its current state",
        field_errors=[field_error],
    )

    assert str(error) == "The post cannot be changed in its current state"
    assert error.status_code == 409
    assert error.code == "POST_CONFLICT"
    assert error.message == "The post cannot be changed in its current state"
    assert error.field_errors == [field_error]
