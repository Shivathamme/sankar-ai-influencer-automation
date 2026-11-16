import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone
import config
STATUSES = ['New Lead','Email Available','Email Sent','Follow-up Due','Replied','Interested','Not Interested','Collaboration Confirmed','Opted Out']
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def conn():
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(config.DB_PATH, timeout=30); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS influencers(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, name TEXT, profile_url TEXT, niche TEXT, category TEXT, followers INTEGER DEFAULT 0, email TEXT, email_source TEXT, location TEXT, bio TEXT, source TEXT, score INTEGER, relevant INTEGER, summary TEXT, reason TEXT, status TEXT DEFAULT 'New Lead', created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS emails(id INTEGER PRIMARY KEY, influencer_id INTEGER NOT NULL REFERENCES influencers(id), direction TEXT, kind TEXT, status TEXT, subject TEXT, body TEXT, to_addr TEXT, from_addr TEXT, gmail_thread_id TEXT, gmail_message_id TEXT, parent_id INTEGER, classification TEXT, summary TEXT, next_action TEXT, due_at TEXT, sent_at TEXT, created_at TEXT, rfc_message_id TEXT, in_reply_to TEXT, references_header TEXT);
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, influencer_id INTEGER, event TEXT, detail TEXT, created_at TEXT);
        CREATE INDEX IF NOT EXISTS idx_email_due ON emails(status,due_at);
        ''')
        # Lightweight migration for databases created by earlier project versions.
        cols={row['name'] for row in c.execute('PRAGMA table_info(emails)')}
        for name in ('rfc_message_id','in_reply_to','references_header'):
            if name not in cols:c.execute(f'ALTER TABLE emails ADD COLUMN {name} TEXT')
def log(i,event,detail=''):
    with conn() as c: c.execute('INSERT INTO activity(influencer_id,event,detail,created_at) VALUES(?,?,?,?)',(i,event,detail,now()))
def upsert_person(p):
    username=(p.get('username') or '').strip().lstrip('@').lower()
    if not username: return None,False
    with conn() as c:
        old=c.execute('SELECT id FROM influencers WHERE username=?',(username,)).fetchone()
        vals=(username,p.get('name') or username,p.get('profile_url') or f'https://www.instagram.com/{username}/',p.get('niche',''),p.get('category',''),int(p.get('followers') or 0),p.get('email') or '',p.get('email_source',''),p.get('location',''),p.get('bio',''),p.get('source',''),p.get('score'),p.get('relevant'),p.get('summary',''),p.get('reason',''), 'Email Available' if p.get('email') else 'New Lead',now(),now())
        if old:
            c.execute('''UPDATE influencers SET name=?,profile_url=?,niche=?,followers=CASE WHEN ?>0 THEN ? ELSE followers END,email=CASE WHEN email='' THEN ? ELSE email END,email_source=CASE WHEN email='' THEN ? ELSE email_source END,location=CASE WHEN location='' THEN ? ELSE location END,bio=CASE WHEN bio='' THEN ? ELSE bio END,source=?,updated_at=? WHERE id=?''',(vals[1],vals[2],vals[3],vals[5],vals[5],vals[6],vals[7],vals[8],vals[9],vals[10],now(),old['id']))
            return old['id'],False
        cur=c.execute('''INSERT INTO influencers(username,name,profile_url,niche,category,followers,email,email_source,location,bio,source,score,relevant,summary,reason,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',vals)
        return cur.lastrowid,True
def people(status=None):
    with conn() as c:
        q='SELECT * FROM influencers'; args=()
        if status and status!='All': q+=' WHERE status=?'; args=(status,)
        q+=' ORDER BY COALESCE(score,0) DESC, id DESC'
        return [dict(x) for x in c.execute(q,args)]
def person(i):
    with conn() as c:
        r=c.execute('SELECT * FROM influencers WHERE id=?',(i,)).fetchone(); return dict(r) if r else None
def update_person(i, **kw):
    allowed={'category','score','relevant','summary','reason','status','email','email_source','followers','location','bio'}
    kw={k:v for k,v in kw.items() if k in allowed}
    if not kw:return
    kw['updated_at']=now(); sql=', '.join(f'{k}=?' for k in kw)
    with conn() as c:c.execute(f'UPDATE influencers SET {sql} WHERE id=?',(*kw.values(),i))
def add_email(i,direction,kind,status,subject,body,to_addr='',parent_id=None,due_at=None,classification='',summary='',next_action=''):
    with conn() as c:
        cur=c.execute('''INSERT INTO emails(influencer_id,direction,kind,status,subject,body,to_addr,parent_id,due_at,classification,summary,next_action,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(i,direction,kind,status,subject,body,to_addr,parent_id,due_at,classification,summary,next_action,now()))
        return cur.lastrowid
def update_email(i, **kw):
    allowed={'status','subject','body','gmail_thread_id','gmail_message_id','from_addr','sent_at','due_at','classification','summary','next_action','rfc_message_id','in_reply_to','references_header'}
    kw={k:v for k,v in kw.items() if k in allowed}
    if not kw:return
    with conn() as c:c.execute('UPDATE emails SET '+', '.join(f'{k}=?' for k in kw)+' WHERE id=?',(*kw.values(),i))
def emails(i=None,direction=None,kind=None,status=None):
    q='SELECT * FROM emails WHERE 1=1'; a=[]
    for k,v in [('influencer_id',i),('direction',direction),('kind',kind),('status',status)]:
        if v is not None:q+=f' AND {k}=?';a.append(v)
    q+=' ORDER BY id'
    with conn() as c:return [dict(x) for x in c.execute(q,a)]
def email(i):
    with conn() as c:
        r=c.execute('SELECT * FROM emails WHERE id=?',(i,)).fetchone();return dict(r) if r else None
def activity(limit=200):
    with conn() as c:return [dict(x) for x in c.execute('SELECT * FROM activity ORDER BY id DESC LIMIT ?',(limit,))]
def count_sent_today():
    day=datetime.now(timezone.utc).date().isoformat()
    with conn() as c:return c.execute("SELECT COUNT(*) FROM emails WHERE direction='out' AND status='sent' AND sent_at LIKE ?",(day+'%',)).fetchone()[0]
def set_reply_state(i, classification):
    status={'interested':'Interested','collaboration_request':'Interested','pricing_enquiry':'Interested','not_interested':'Not Interested','opt_out':'Opted Out','other':'Replied'}.get(classification,'Replied')
    update_person(i,status=status)
