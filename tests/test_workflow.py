import os,tempfile
import config,database as db,research,workflow

def setup_function():
    config.DB_PATH=tempfile.mktemp(suffix='.sqlite3');config.DEMO_MODE=True;db.init()

def test_demo_pipeline_and_reply_stop():
    for p in research.demo_data():db.upsert_person(p)
    result=workflow.run_analysis();assert result['analysed']==3
    assert workflow.create_initial_drafts()==2
    draft=db.emails(direction='out',kind='initial',status='draft')[0]
    assert 'unsubscribe' in draft['body'].lower()
    workflow.approve_and_send(draft['id'])
    assert db.email(draft['id'])['status']=='sent'
    result=workflow.simulate_reply(draft['influencer_id'],'Please unsubscribe me from future emails.')
    assert result['classification']=='opt_out'
    assert db.person(draft['influencer_id'])['status']=='Opted Out'

def test_live_reply_optout_is_recorded_without_creating_reply_draft(monkeypatch):
    # Exercise the live inbox-processing branch without making a Gmail network call.
    import workflow as wf
    p=research.demo_data()[0]
    pid,_=db.upsert_person(p)
    sent_id=db.add_email(pid,'out','initial','sent','Hello','Initial outreach',p['email'])
    db.update_email(sent_id,gmail_thread_id='thread-test',gmail_message_id='sent-msg')
    config.DEMO_MODE=False
    monkeypatch.setattr(wf,'fetch_replies',lambda:[{
        'thread_id':'thread-test','message_id':'reply-msg','from':p['email'],
        'subject':'Re: Hello','body':'Please unsubscribe me from all future emails.',
        'influencer_id':pid
    }])
    result=wf.process_incoming()
    assert result['processed']==1
    assert db.person(pid)['status']=='Opted Out'
    assert not db.emails(i=pid,direction='out',kind='reply')

def test_scheduler_creates_due_followup_and_stops_after_reply(monkeypatch):
    from datetime import datetime,timedelta,timezone
    p=research.demo_data()[0]
    pid,_=db.upsert_person(p)
    db.update_person(pid,status='Email Sent')
    sent_id=db.add_email(pid,'out','initial','sent','Initial','Initial body',p['email'])
    old=(datetime.now(timezone.utc)-timedelta(days=config.FOLLOWUP1_DAYS+1)).isoformat(timespec='seconds')
    db.update_email(sent_id,status='sent',sent_at=old)
    result=workflow.run_followups()
    assert result['created']==1
    assert len(db.emails(i=pid,direction='out',kind='followup1'))==1
    # A reply changes the CRM state and the next scheduler pass must not create stage 2.
    db.set_reply_state(pid,'interested')
    result=workflow.run_followups()
    assert result['created']==0
    assert len(db.emails(i=pid,direction='out',kind='followup2'))==0
