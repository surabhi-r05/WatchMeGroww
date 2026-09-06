def test_imports():
    from app.main import app
    assert app.title == "Watch Me Groww API"
