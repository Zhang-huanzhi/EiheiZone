from app.main import app


OPERATION_METHODS = {"get", "post", "put", "patch", "delete"}
EXPECTED_OPERATIONS = {
    ("get", "/api/v1/health"),
    ("get", "/api/v1/auth/csrf"),
    ("post", "/api/v1/auth/login"),
    ("get", "/api/v1/auth/me"),
    ("post", "/api/v1/auth/logout"),
    ("get", "/api/v1/public/posts"),
    ("get", "/api/v1/public/posts/{post_id}"),
    ("get", "/api/v1/posts"),
    ("get", "/api/v1/posts/{post_id}"),
    ("post", "/api/v1/posts"),
    ("patch", "/api/v1/posts/{post_id}"),
    ("delete", "/api/v1/posts/{post_id}"),
    ("get", "/api/v1/qas"),
    ("get", "/api/v1/qas/{qa_id}"),
    ("post", "/api/v1/qas"),
    ("put", "/api/v1/qas/{qa_id}/answer"),
    ("get", "/api/v1/expenditures"),
    ("get", "/api/v1/expenditures/{expenditure_id}"),
    ("post", "/api/v1/expenditures"),
    ("patch", "/api/v1/expenditures/{expenditure_id}"),
    ("delete", "/api/v1/expenditures/{expenditure_id}"),
    ("get", "/api/v1/dashboard"),
}


def test_openapi_operations_match_v1_contract() -> None:
    schema = app.openapi()
    operations = {
        (method, path)
        for path, path_item in schema["paths"].items()
        for method in path_item
        if method in OPERATION_METHODS
    }

    assert operations == EXPECTED_OPERATIONS


def test_openapi_has_no_out_of_scope_public_or_user_management_api() -> None:
    paths = set(app.openapi()["paths"])

    assert "/api/v1/public/qas" not in paths
    assert "/api/v1/public/expenditures" not in paths
    assert "/api/v1/public/dashboard" not in paths
    assert "/api/v1/users" not in paths
    assert "/api/v1/auth/register" not in paths
