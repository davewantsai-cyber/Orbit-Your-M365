from orbit import config


def test_identity():
    assert config.AUTHOR == "Reece Gabriel Dickson"
    assert config.VERSION == "1.2.0"
