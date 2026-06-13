from app.api.response_headers import CORS_EXPOSE_HEADERS


def test_cors_exposes_download_filename_header() -> None:
    exposed = [header.lower() for header in CORS_EXPOSE_HEADERS]
    assert "content-disposition" in exposed
