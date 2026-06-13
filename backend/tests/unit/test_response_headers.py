from app.api.response_headers import content_disposition


def test_content_disposition_encodes_unicode_filename() -> None:
    value = content_disposition("诈骗聊天记录.png", fallback_filename="evidence.png")

    assert value == (
        'inline; filename="evidence.png"; '
        "filename*=UTF-8''%E8%AF%88%E9%AA%97%E8%81%8A%E5%A4%A9%E8%AE%B0%E5%BD%95.png"
    )
    assert value.isascii()


def test_content_disposition_removes_path_and_header_injection() -> None:
    value = content_disposition(
        "..\\截图\r\nX-Evil: yes.png",
        disposition="attachment",
        fallback_filename='report\r\n".png',
    )

    assert value.startswith("attachment; filename=\"report.png\"; filename*=UTF-8''")
    assert "%E6%88%AA%E5%9B%BEX-Evil%3A%20yes.png" in value
    assert "\r" not in value
    assert "\n" not in value
