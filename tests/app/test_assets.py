def test_static_404s_return(client_request):
    client_request.get_response_from_url(
        '/static/images/some-image-that-doesnt-exist.png',
        _expected_status=404,
    )
