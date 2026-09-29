def test_python_works():
    assert 1 + 1 == 2


def test_app_imports():
    from app import create_app
    app = create_app()
    assert app is not None