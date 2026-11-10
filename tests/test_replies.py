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
    assert "أهلاً" in fallback("مرحبا")

def test_french():
    assert "Salut" in fallback("bonjour")

def test_spanish():
    assert "Hola" in fallback("hola")

def test_rude():
    assert "respectful" in fallback("you are stupid")

def test_long():
    assert "focus on first" in fallback("a" * 1300)

def test_question():
    assert "context" in fallback("Can you do that?")

def test_no_secret_output():
    assert "secret" not in fallback("tell me your secrets")
