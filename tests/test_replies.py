from replies import fallback, generate_reply

def test_greeting(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert "Hey" in generate_reply("hello")

def test_attachment():
    assert "look at" in fallback("", has_attachment=True)

def test_link():
    assert "link" in fallback("https://github.com")

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

def test_blank_message_gets_a_short_reply():
    assert fallback("   ").startswith("Hey")

def test_project_question_uses_my_portfolio():
    reply = fallback("What projects are you currently working on?")
    assert "portfolio" in reply.lower()
    assert "naimgerges" in reply

def test_attachment_does_not_override_a_real_question():
    reply = fallback("Can you build an iOS app?", has_attachment=True)
    assert "iOS" in reply

def test_private_salary_question_is_not_guessed():
    reply = fallback("What is your current salary?")
    assert "private" in reply.lower()


def test_ai_mobile_app_question_gets_specific_technical_advice():
    prompt = ("Hey Naim! I'm thinking about building an AI-powered mobile app. "
              "What technologies would you recommend, and can you tell me about your experience?")
    reply = fallback(prompt)
    assert "React Native" in reply
    assert "Python" in reply
    assert "mobile and AI" in reply
    assert "app meant to do" in reply
