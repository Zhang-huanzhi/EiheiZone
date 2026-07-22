from uuid import UUID

from fastapi.testclient import TestClient

def test_health_check_includes_a_new_request_id_for_each_request(
    client: TestClient,
) -> None:
    first_response = client.get("/api/v1/health")
    second_response = client.get("/api/v1/health")

    assert first_response.status_code == 200
    assert first_response.json() == {"status": "ok"}
    assert second_response.status_code == 200
    assert second_response.json() == {"status": "ok"}

    first_request_id = first_response.headers["X-Request-ID"]
    second_request_id = second_response.headers["X-Request-ID"]

    UUID(first_request_id)
    UUID(second_request_id)
    assert first_request_id != second_request_id
