import os, tempfile
os.environ['DB_PATH']=os.path.join(tempfile.gettempdir(),'sankar_test_crm.sqlite3')
os.environ['DEMO_MODE']='true'
import config, database as db, research

def setup_function():
    if os.path.exists(config.DB_PATH):os.remove(config.DB_PATH)
    db.init()
def test_upsert_deduplicates():
    p={'username':'Creator.One','name':'Creator','email':'a@example.test','followers':1200}
    a,created=db.upsert_person(p);b,created2=db.upsert_person(p)
    assert a==b and created and not created2 and len(db.people())==1
def test_parse_followers():
    assert research.parse_followers('12.5K followers')==12500
    assert research.parse_followers('1.2M followers')==1200000
    assert research.parse_followers('no count')==0
def test_email_records():
    i,_=db.upsert_person({'username':'creator','email':'a@example.test'})
    e=db.add_email(i,'out','initial','draft','Hi','Hello','a@example.test')
    assert db.email(e)['status']=='draft'
def test_opt_out_status_mapping():
    i,_=db.upsert_person({'username':'creator'});db.set_reply_state(i,'opt_out')
    assert db.person(i)['status']=='Opted Out'

def test_public_search_parses_canonical_trailing_slash(monkeypatch):
    import research
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'organic_results':[{
                'link':'https://www.instagram.com/creator.handle/',
                'title':'Creator Handle (@creator.handle)',
                'snippet':'Fitness creator in India · 25K followers'
            }]}
    monkeypatch.setattr(research.config,'SERPAPI_API_KEY','test-key')
    monkeypatch.setattr(research.requests,'get',lambda *a,**k:Response())
    found=research.search('fitness','India','',0,100000,5)
    assert len(found)==1
    assert found[0]['username']=='creator.handle'
    assert found[0]['followers']==25000
