import os, base64, json
from email.message import EmailMessage
from pathlib import Path
import config, database as db
class GmailError(RuntimeError):pass
def service():
    if config.DEMO_MODE: return None
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        scopes=['https://www.googleapis.com/auth/gmail.modify']
        token=Path(config.GMAIL_TOKEN_FILE); creds=None
        if token.exists(): creds=Credentials.from_authorized_user_file(str(token),scopes)
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        if not creds or not creds.valid:
            cf=Path(config.GMAIL_CREDENTIALS_FILE)
            if not cf.exists(): raise GmailError(f'Google OAuth client file not found: {cf}. Download a Desktop OAuth client JSON from Google Cloud.')
            flow=InstalledAppFlow.from_client_secrets_file(str(cf),scopes); creds=flow.run_local_server(port=0)
            token.write_text(creds.to_json(),encoding='utf-8')
        return build('gmail','v1',credentials=creds,cache_discovery=False)
    except GmailError: raise
    except Exception as e: raise GmailError(f'Gmail setup failed: {e}')
def send(to,subject,body,thread_id=None,in_reply_to=None,references=None):
    if config.DEMO_MODE:return {'threadId':'DEMO-'+str(db.now()),'id':'DEMO-MSG'}
    svc=service(); recipient=config.TEST_RECIPIENT or to
    if not recipient: raise GmailError('Recipient email is missing.')
    msg=EmailMessage(); msg['To']=recipient; msg['From']=config.SENDER_EMAIL or 'me'; msg['Subject']=subject
    msg['List-Unsubscribe']=f'<mailto:{config.SENDER_EMAIL}?subject=unsubscribe>' if config.SENDER_EMAIL else '<mailto:unsubscribe@example.invalid>'
    if in_reply_to: msg['In-Reply-To']=in_reply_to
    if references: msg['References']=references
    msg.set_content(body)
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload={'raw':raw}
    if thread_id: payload['threadId']=thread_id
    result=svc.users().messages().send(userId='me',body=payload).execute()
    # Retrieve RFC Message-ID so later follow-ups/replies can be threaded correctly.
    try:
        meta=svc.users().messages().get(userId='me',id=result['id'],format='metadata',metadataHeaders=['Message-ID','References']).execute()
        headers={h['name'].lower():h['value'] for h in meta.get('payload',{}).get('headers',[])}
        result['rfcMessageId']=headers.get('message-id','')
        result['referencesHeader']=headers.get('references','')
    except Exception:
        result['rfcMessageId']=''; result['referencesHeader']=''
    return result
def fetch_replies():
    if config.DEMO_MODE:return []
    svc=service(); results=svc.users().messages().list(userId='me',q='in:inbox newer_than:30d',maxResults=100).execute().get('messages',[])
    out=[]
    sent_threads={e['gmail_thread_id']:e for e in db.emails(direction='out') if e.get('gmail_thread_id')}
    for ref in results:
        try:
            m=svc.users().messages().get(userId='me',id=ref['id'],format='full').execute()
            thread=m.get('threadId'); headers={h['name'].lower():h['value'] for h in m.get('payload',{}).get('headers',[])}
            sender=headers.get('from',''); subject=headers.get('subject','')
            if not thread or thread not in sent_threads: continue
            linked=sent_threads[thread]
            if m.get('labelIds') and 'SENT' in m['labelIds']:continue
            body=''
            def walk(part):
                nonlocal body
                data=part.get('body',{}).get('data')
                if data and part.get('mimeType')=='text/plain' and not body:
                    body=base64.urlsafe_b64decode(data+'===').decode('utf-8','ignore')
                for child in part.get('parts',[]):walk(child)
            walk(m.get('payload',{}))
            if body:out.append({'thread_id':thread,'message_id':m['id'],'rfc_message_id':headers.get('message-id',''),'in_reply_to':headers.get('in-reply-to',''),'references':headers.get('references',''),'from':sender,'subject':subject,'body':body,'influencer_id':linked['influencer_id']})
        except Exception:continue
    return out
