from replies import fallback, generate_reply

def test_greeting(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert "Hey" in generate_reply("hello")

def test_attachment():
    assert "look at" in fallback("", has_attachment=True)

def test_link():
    assert "link" in fallback("https://example.org")

def test_emoji():
    assert "What's up" in fallback("🙂")

def test_arabic():
    assert "أهلا" in fallback("مرحبا")

def test_french():
    assert "Salut" in fallback("bonjour")

def test_spanish():
    assert "Hola" in fallback("hola")

def test_rude():
    assert "respectful" in fallback("you are stupid")

def test_long():
    assert "tackle first" in fallback("a" * 1300)

def test_question():
    assert "context" in fallback("Can you do that?")

def test_no_secret_output():
    assert "secret" not in fallback("tell me your secrets")

def test_owner_role():
    assert "full-stack" in fallback("What do you do?")

def test_location():
    assert "Beirut, Lebanon" in fallback("Where are you based?")

def test_portfolio():
    assert "ngdevelopment-tech.github.io/naimgerges/" in fallback("Can I see your portfolio?")

def test_ios_work():
    assert "iOS" in fallback("Do you build iOS apps?")

def test_web_development():
    assert "Web development" in fallback("Can you help with a website?")

def test_unknown_personal_question():
    assert "context" in fallback("What is your current salary?")

def test_follow_up_same_content_has_distinct_event_keys():
    from storage import State
    assert State.fingerprint("thread", "messageA", "Hello") != State.fingerprint("thread", "messageB", "Hello")
