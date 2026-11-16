import json, re, requests
import config
class AIError(RuntimeError): pass
def ask_model(prompt, max_tokens=900):
    """Call the configured provider. Groq is the default; Claude is selectable."""
    provider = config.AI_PROVIDER
    if provider == 'groq':
        if not config.GROQ_API_KEY:
            raise AIError('GROQ_API_KEY is missing. Create one at https://console.groq.com/keys and add it to .env.')
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {config.GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': config.GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.2, 'max_tokens': max_tokens, 'response_format': {'type': 'json_object'}},
            timeout=90,
        )
        if r.status_code >= 400:
            raise AIError(f'Groq API error {r.status_code}: {r.text[:500]}')
        return r.json()['choices'][0]['message']['content'].strip()
    if provider == 'claude':
        if not config.ANTHROPIC_API_KEY:
            raise AIError('ANTHROPIC_API_KEY is missing. Add it to .env to use Claude.')
        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={'x-api-key': config.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
            json={'model': config.CLAUDE_MODEL, 'max_tokens': max_tokens, 'messages': [{'role': 'user', 'content': prompt}]},
            timeout=90,
        )
        if r.status_code >= 400:
            raise AIError(f'Claude API error {r.status_code}: {r.text[:500]}')
        return ''.join(x.get('text', '') for x in r.json().get('content', []) if x.get('type') == 'text').strip()
    raise AIError(f'Unsupported AI_PROVIDER={provider!r}. Choose groq or claude.')

def json_result(prompt, max_tokens=900):
    raw=ask_model(prompt,max_tokens); raw=re.sub(r'^```(?:json)?|```$','',raw.strip(),flags=re.I|re.M).strip()
    m=re.search(r'\{.*\}',raw,re.S)
    if not m: raise AIError('The configured AI provider did not return a JSON object.')
    try:return json.loads(m.group())
    except json.JSONDecodeError as e: raise AIError(f'Invalid JSON from Claude: {e}')
def analyse(p,camp):
    prompt=f'''You are an influencer marketing analyst. Use only supplied facts; never invent details. Return JSON: relevant (boolean), category (string), summary (max 35 words), score (integer 0-100), reason (one sentence). Score niche fit, location fit, audience/follower fit, keyword fit.\nCAMPAIGN: {json.dumps(camp)}\nPUBLIC PROFILE: {json.dumps(p)}'''
    x=json_result(prompt); x['score']=max(0,min(100,int(x.get('score',0)))); return x
def write_email(p,camp,kind='initial',previous=''):
    prompt=f'''Write a personalised {kind} outreach email. Return JSON with subject and body. Use only known facts; no false claims about viewing content. Brand: {camp}. Influencer: {p}. Previous email: {previous}. Keep initial email 90-130 words; follow-ups 45-80 words. Include one clear CTA. For follow-up 2 politely say this is the final note. Do not invent offer details.'''
    x=json_result(prompt); return str(x.get('subject','Collaboration opportunity')),str(x.get('body',''))
def classify_reply(p,camp,history,inbound):
    prompt=f'''Classify this influencer email reply. Return JSON with classification exactly one of interested, not_interested, pricing_enquiry, collaboration_request, opt_out, other; summary; suggested_next_action; draft_reply. If opt_out, draft_reply must be empty. Never promise price or contract. Context: {camp}; influencer: {p}; history: {history}; incoming reply: {inbound}'''
    x=json_result(prompt)
    if x.get('classification') not in {'interested','not_interested','pricing_enquiry','collaboration_request','opt_out','other'}: x['classification']='other'
    if x['classification']=='opt_out':x['draft_reply']=''
    return x
# Explicitly labelled deterministic demo responses; never used in live mode.
def _demo_json(prompt):
    low=prompt.lower()
    if 'classify this influencer email reply' in low:
        inbound=low.split('incoming reply:',1)[-1]
        if any(x in inbound for x in ['unsubscribe','stop emailing','remove me','do not contact']):return {'classification':'opt_out','summary':'Asked to stop receiving emails.','suggested_next_action':'Suppress contact immediately.','draft_reply':''}
        if any(x in inbound for x in ['not interested','no thanks']):return {'classification':'not_interested','summary':'Declined the collaboration.','suggested_next_action':'Mark not interested and stop follow-ups.','draft_reply':'Thank you for letting us know. We will not follow up further.'}
        if any(x in inbound for x in ['rate','price','budget','how much']):return {'classification':'pricing_enquiry','summary':'Asked about pricing or budget.','suggested_next_action':'Have the partnerships team confirm the budget and deliverables.','draft_reply':'Thanks for your reply. Our team will confirm the proposed budget and deliverables shortly.'}
        return {'classification':'interested','summary':'Expressed interest in discussing a collaboration.','suggested_next_action':'Review the opportunity and share campaign details.','draft_reply':'Thanks for your interest. We would be happy to share more details about the campaign.'}
    if 'write a personalised initial' in low or 'write a personalised initial' in prompt.lower():return {'subject':'Potential creator collaboration','body':'Hello,\n\nWe are reaching out from the campaign team to explore a possible partnership. Your publicly listed creator profile appears relevant to our campaign focus. We would be glad to share the proposed collaboration details and understand whether this opportunity is of interest.\n\nWould you be open to learning more?'}
    if 'follow-up' in low:return {'subject':'Re: Potential creator collaboration','body':'Hello,\n\nI wanted to gently follow up on my earlier note about a possible creator partnership. If this opportunity is relevant, we would be happy to share further details. If not, no action is needed and we will not keep following up.\n\nWould you be interested in receiving the details?'}
    return {'relevant':True,'category':'General','summary':'Synthetic demo analysis; configure a live AI provider for real profile assessment.','score':65,'reason':'Demo score only; real AI analysis requires an API key.'}
# Safe offline demo: deterministic responses are clearly labelled as simulated.
_real_ask_model = ask_model
def ask_model(prompt, max_tokens=900):
    if config.DEMO_MODE and ((config.AI_PROVIDER == 'groq' and not config.GROQ_API_KEY) or (config.AI_PROVIDER == 'claude' and not config.ANTHROPIC_API_KEY)):
        return json.dumps(_demo_json(prompt))
    return _real_ask_model(prompt, max_tokens)
