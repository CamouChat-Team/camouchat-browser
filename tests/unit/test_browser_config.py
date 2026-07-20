import pytest
from camouchat_core import Platform
from camouchat_browser.browser_config import BrowserConfig

def test_browser_config_from_dict_minimal():
    data = {"platform": Platform.WHATSAPP}
    config = BrowserConfig.from_dict(data)
    assert config.platform == Platform.WHATSAPP
    assert config.locale == "en-US"
    assert config.enable_cache is False
    assert config.headless is False
    assert config.geoip is False
    assert config.proxy is None
    assert config.prefs == {}
    assert config.addons == []

def test_browser_config_from_dict_full():
    data = {
        "platform": Platform.WHATSAPP,
        "locale": "fr-FR",
        "enable_cache": True,
        "headless": True,
        "geoip": True,
        "proxy": {
            "server": "http://localhost:8080",
            "username": "user",
            "password": "pass"
        },
        "prefs": {"js.enabled": False},
        "addons": ["/path/to/addon"],
        "fingerprint": {"some": "data"}
    }
    config = BrowserConfig.from_dict(data)
    assert config.platform == Platform.WHATSAPP
    assert config.locale == "fr-FR"
    assert config.enable_cache is True
    assert config.headless is True
    assert config.geoip is True
    assert config.proxy["server"] == "http://localhost:8080"
    assert config.prefs == {"js.enabled": False}
    assert config.addons == ["/path/to/addon"]
    assert config.fingerprint == {"some": "data"}

def test_browser_config_from_dict_errors():
    with pytest.raises(ValueError, match="'data : dict' is required"):
        BrowserConfig.from_dict({})

    with pytest.raises(ValueError, match="'platform' is required"):
        BrowserConfig.from_dict({"locale": "en-US"})

    with pytest.raises(ValueError, match="'platform' must be an instance of Platform"):
        BrowserConfig.from_dict({"platform": "WHATSAPP"})

    with pytest.raises(ValueError, match="proxy must be a dict"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "proxy": "not-a-dict"})

    with pytest.raises(ValueError, match=r"proxy\['server'\] is required"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "proxy": {"username": "u"}})

    with pytest.raises(ValueError, match="proxy username/password must be provided together"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "proxy": {"server": "s", "username": "u"}})

    with pytest.raises(ValueError, match=r"proxy\['username'\] must be string"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "proxy": {"server": "s", "username": 1, "password": "p"}})

    with pytest.raises(ValueError, match=r"proxy\['password'\] must be string"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "proxy": {"server": "s", "username": "u", "password": 1}})

    with pytest.raises(ValueError, match="prefs must be a dict"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "prefs": []})

    with pytest.raises(ValueError, match="addons must be a list"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "addons": {}})

    with pytest.raises(ValueError, match="all addons must be strings"):
        BrowserConfig.from_dict({"platform": Platform.WHATSAPP, "addons": [1]})

def test_browser_config_to_dict():
    config = BrowserConfig(
        platform=Platform.WHATSAPP,
        locale="en-US",
        enable_cache=True,
        headless=False,
        prefs={"a": True},
        addons=["b"],
        geoip=True,
        proxy={"server": "s"}
    )
    d = config.to_dict()
    assert d["platform"] == Platform.WHATSAPP
    assert d["locale"] == "en-US"
    assert d["enable_cache"] is True
    assert d["headless"] is False
    assert d["geoip"] is True
    assert d["proxy"] == {"server": "s"}
    assert d["prefs"] == {"a": True}
    assert d["addons"] == ["b"]
    assert d["fingerprint"] == {"provider": "browserforge"}

def test_browser_config_str_repr():
    config = BrowserConfig(
        platform=Platform.WHATSAPP,
        locale="en-US",
        enable_cache=True,
        headless=False
    )
    assert "Platform: WhatsApp" in str(config)
    assert "BrowserConfig(platform=WhatsApp" in repr(config)
