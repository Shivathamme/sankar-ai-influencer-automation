import config
import ai_service

class FakeResponse:
    status_code = 200
    text = ''
    def raise_for_status(self): pass
    def json(self):
        return {'choices': [{'message': {'content': '{"ok": true}'}}]}

def test_groq_provider_uses_openai_compatible_endpoint(monkeypatch):
    seen = {}
    monkeypatch.setattr(config, 'AI_PROVIDER', 'groq')
    monkeypatch.setattr(config, 'GROQ_API_KEY', 'test-groq-key')
    monkeypatch.setattr(config, 'GROQ_MODEL', 'openai/gpt-oss-120b')
    def fake_post(url, **kwargs):
        seen['url'] = url; seen.update(kwargs); return FakeResponse()
    monkeypatch.setattr(ai_service.requests, 'post', fake_post)
    assert ai_service.ask_model('Return JSON') == '{"ok": true}'
    assert seen['url'] == 'https://api.groq.com/openai/v1/chat/completions'
    assert seen['headers']['Authorization'] == 'Bearer test-groq-key'
    assert seen['json']['model'] == 'openai/gpt-oss-120b'

def test_claude_provider_remains_available(monkeypatch):
    monkeypatch.setattr(config, 'AI_PROVIDER', 'claude')
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'test-claude-key')
    seen = {}
    class ClaudeResponse:
        status_code = 200
        text = ''
        def json(self): return {'content': [{'type': 'text', 'text': '{"ok": true}'}]}
    def fake_post(url, **kwargs): seen['url'] = url; seen.update(kwargs); return ClaudeResponse()
    monkeypatch.setattr(ai_service.requests, 'post', fake_post)
    assert ai_service.ask_model('Return JSON') == '{"ok": true}'
    assert seen['url'] == 'https://api.anthropic.com/v1/messages'
    assert seen['headers']['x-api-key'] == 'test-claude-key'
