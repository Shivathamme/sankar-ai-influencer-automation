from datetime import datetime,timedelta,timezone
import config,database as db
import time
from campaign_store import load_campaign
from ai_service import analyse,write_email,classify_reply
from gmail_service import send,fetch_replies
from gmail_service import GmailError
from email.utils import parseaddr


def with_sender_footer(body):
    footer = f"\n\n{config.SENDER_NAME}\n{config.SENDER_TITLE}"
    if config.POSTAL_ADDRESS:
        footer += f"\n{config.POSTAL_ADDRESS}"
    if config.SENDER_EMAIL:
        footer += f"\n{config.SENDER_EMAIL}"
    return body.rstrip() + footer + '\n\nIf you prefer not to receive further collaboration emails, reply with "unsubscribe".'

def campaign():
    return load_campaign()

def run_analysis():
    done=failed=qualified=0; camp=campaign()
    for p in db.people():
        if p.get('score') is not None:continue
        try:
            a=analyse(p,camp);db.update_person(p['id'],category=a.get('category',''),score=a['score'],relevant=int(bool(a['relevant'])),summary=a.get('summary',''),reason=a.get('reason',''))
            if a['relevant'] and a['score']>=config.MIN_SCORE:qualified+=1
            db.log(p['id'],f'{config.AI_PROVIDER}_analysis',f"score={a['score']}");done+=1
        except Exception as e:db.log(p['id'],'analysis_error',str(e)[:300]);failed+=1
    return {'analysed':done,'qualified':qualified,'failed':failed}
def create_initial_drafts():
    made=0
    for p in db.people():
        if not p.get('email') or not p.get('relevant') or (p.get('score') or 0)<config.MIN_SCORE or p['status']!='Email Available':continue
        if db.emails(i=p['id'],kind='initial'):continue
        sub,body=write_email(p,campaign(),'initial')
        if config.POSTAL_ADDRESS:body+=f"\n\n{config.SENDER_NAME}\n{config.SENDER_TITLE}\n{config.POSTAL_ADDRESS}"
        if config.SENDER_EMAIL:body+=f"\n{config.SENDER_EMAIL}"
        body+='\n\nIf you prefer not to receive further collaboration emails, reply with “unsubscribe”.'
        db.add_email(p['id'],'out','initial','draft',sub,body,p['email']);db.log(p['id'],'initial_draft_created',sub);made+=1
    return made
def approve_and_send(email_id):
    e=db.email(email_id);p=db.person(e['influencer_id']) if e else None
    if not e or not p:raise RuntimeError('Email or influencer not found')
    if e['status'] not in ('draft','approved'):raise RuntimeError('Email is not awaiting approval')
    if p['status']=='Opted Out' or (e['kind']!='initial' and p['status'] in ('Replied','Interested','Not Interested','Collaboration Confirmed','Opted Out')):raise RuntimeError('Send blocked by reply/opt-out stop rule')
    if db.count_sent_today()>=config.DAILY_SEND_LIMIT:raise RuntimeError('Daily send limit reached')
    if config.DEMO_MODE is False and not config.SENDER_EMAIL:raise RuntimeError('Set SENDER_EMAIL before live sending')
    # Thread replies/follow-ups using RFC 5322 headers as well as Gmail's thread ID.
    in_reply_to=e.get('in_reply_to') or ''
    references=e.get('references_header') or ''
    if e.get('kind')=='reply' and e.get('parent_id'):
        parent=db.email(e['parent_id'])
        if parent:
            in_reply_to=parent.get('rfc_message_id') or in_reply_to
            references=' '.join(x for x in [parent.get('references_header',''), parent.get('rfc_message_id','')] if x).strip()
    elif e.get('kind') in ('followup1','followup2'):
        prior=[x for x in db.emails(i=p['id'],direction='out') if x['status']=='sent' and x['kind'] in ('initial','followup1','followup2')]
        if prior:
            last=prior[-1]
            in_reply_to=last.get('rfc_message_id') or in_reply_to
            references=' '.join(x for x in [last.get('references_header',''), last.get('rfc_message_id','')] if x).strip()
    result=send(e['to_addr'] or p['email'],e['subject'],e['body'],e.get('gmail_thread_id'),in_reply_to or None,references or None)
    db.update_email(email_id,status='sent',sent_at=db.now(),gmail_thread_id=result.get('threadId'),gmail_message_id=result.get('id'),rfc_message_id=result.get('rfcMessageId',''),in_reply_to=in_reply_to,references_header=result.get('referencesHeader','') or references)
    if e['kind'] in ('initial','followup1','followup2'):db.update_person(p['id'],status='Email Sent')
    db.log(p['id'],'email_sent',f"{e['kind']} {'(demo)' if config.DEMO_MODE else ''}")
    return 'Simulated send complete (DEMO_MODE=true).' if config.DEMO_MODE else f"Sent to {config.TEST_RECIPIENT or e['to_addr']}"
def process_incoming():
    if config.DEMO_MODE:return {'processed':0,'message':'Demo mode: use the reply simulator in the app.'}
    msgs=fetch_replies(); processed=0
    for m in msgs:
        p=db.person(m['influencer_id']);
        if not p:continue
        # Prevent duplicate processing by Gmail message id.
        if any(x.get('gmail_message_id')==m['message_id'] for x in db.emails(i=p['id'],direction='in')):continue
        eid=db.add_email(p['id'],'in','inbound','received',m['subject'],m['body'],parent_id=None)
        db.update_email(eid,gmail_thread_id=m['thread_id'],gmail_message_id=m['message_id'],rfc_message_id=m.get('rfc_message_id',''),in_reply_to=m.get('in_reply_to',''),references_header=m.get('references',''),from_addr=m['from'])
        txt=m['body'].lower()
        if any(w in txt for w in ['unsubscribe','stop emailing','do not contact','remove me']):
            a={'classification':'opt_out','summary':'Recipient requested no further emails.','suggested_next_action':'Suppress this contact immediately.','draft_reply':''}
        else:a=classify_reply(p,campaign(),db.emails(i=p['id']),m['body'])
        db.update_email(eid,classification=a['classification'],summary=a.get('summary',''),next_action=a.get('suggested_next_action',''))
        db.set_reply_state(p['id'],a['classification'])
        # Only create a reply draft when the classification calls for one.
        # Keep the Gmail thread ID so an approved response stays in the conversation.
        if a.get('draft_reply') and a['classification']!='opt_out':
            rid=db.add_email(p['id'],'out','reply','draft','Re: '+m['subject'],with_sender_footer(a['draft_reply']),p['email'],parent_id=eid)
            db.update_email(rid,gmail_thread_id=m['thread_id'])
        db.log(p['id'],'reply_processed',a['classification']);processed+=1
    return {'processed':processed}
def run_followups():
    # Fail closed: never schedule/send follow-ups if inbox check fails.
    if not config.DEMO_MODE:
        process_incoming()
    now=datetime.now(timezone.utc);created=sent=0
    for p in db.people():
        if p['status'] not in ('Email Sent','Follow-up Due'):continue
        outs=[e for e in db.emails(i=p['id'],direction='out') if e['kind'] in ('initial','followup1','followup2') and e['status']=='sent']
        if not any(e['kind']=='initial' for e in outs):continue
        stage=1+sum(e['kind']!='initial' for e in outs)
        if stage>2:continue
        last=max(outs,key=lambda e:e.get('sent_at') or '')
        days=config.FOLLOWUP1_DAYS if stage==1 else config.FOLLOWUP2_DAYS
        try:last_at=datetime.fromisoformat(last['sent_at'])
        except Exception:continue
        if now-last_at<timedelta(days=days):continue
        if any(e['kind']==f'followup{stage}' for e in db.emails(i=p['id'])):continue
        sub,body=write_email(p,campaign(),f'follow-up {stage}',last['body'])
        footer=f"\n\n{config.SENDER_NAME}\n{config.SENDER_TITLE}"
        if config.POSTAL_ADDRESS: footer+=f"\n{config.POSTAL_ADDRESS}"
        if config.SENDER_EMAIL: footer+=f"\n{config.SENDER_EMAIL}"
        body+=footer+'\n\nIf you prefer not to receive further collaboration emails, reply with "unsubscribe".'
        due=now.isoformat(timespec='seconds')
        eid=db.add_email(p['id'],'out',f'followup{stage}','approved' if config.AUTO_SEND_FOLLOWUPS else 'draft',sub,body,p['email'],due_at=due)
        db.update_email(eid,gmail_thread_id=last.get('gmail_thread_id'))
        created+=1;db.update_person(p['id'],status='Follow-up Due')
        if config.AUTO_SEND_FOLLOWUPS:
            if sent: time.sleep(config.MIN_SEND_INTERVAL_SECONDS)
            approve_and_send(eid);sent+=1
    return {'created':created,'sent':sent}
def simulate_reply(influencer_id,text):
    p=db.person(influencer_id);eid=db.add_email(influencer_id,'in','inbound','received','Re: Collaboration',text)
    low=text.lower()
    if any(x in low for x in ['unsubscribe','stop emailing','remove me','do not contact']):a={'classification':'opt_out','summary':'Asked to stop emails.','suggested_next_action':'Suppress contact.','draft_reply':''}
    else:a=classify_reply(p,campaign(),db.emails(i=influencer_id),text)
    db.update_email(eid,classification=a['classification'],summary=a.get('summary',''),next_action=a.get('suggested_next_action',''))
    db.set_reply_state(influencer_id,a['classification'])
    if a.get('draft_reply') and a['classification']!='opt_out':rid=db.add_email(influencer_id,'out','reply','draft','Re: Collaboration',with_sender_footer(a['draft_reply']),p['email'],parent_id=eid)
    return a
