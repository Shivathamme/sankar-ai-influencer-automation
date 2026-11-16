import re, requests
from urllib.parse import urlparse
import config
EMAIL_RE=re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I)
RESERVED={'p','reel','reels','explore','stories','accounts','about','directory','tags','locations','tv'}
def parse_followers(s):
    m=re.search(r'(\d+(?:[.,]\d+)?)\s*([KMB]?)\s*(?:followers|follower)',str(s),re.I)
    if not m:return 0
    return int(float(m.group(1).replace(',',''))*{'':1,'K':1e3,'M':1e6,'B':1e9}[m.group(2).upper()])
def _google_search(query, limit=10):
    r=requests.get('https://serpapi.com/search.json',params={'engine':'google','q':query,'api_key':config.SERPAPI_API_KEY,'num':min(10,limit)},timeout=35)
    r.raise_for_status()
    return r.json().get('organic_results',[])

def find_public_business_email(username, name=''):
    """Find an explicitly published contact from indexed public web snippets."""
    rows=_google_search(f'"{username}" {name} business email contact creator',6)
    for row in rows:
        title=row.get('title',''); snippet=row.get('snippet',''); blob=f'{title} {snippet}'
        if username.lower() not in blob.lower() and (not name or name.lower() not in blob.lower()):continue
        for email in EMAIL_RE.findall(blob):
            if not any(x in email.lower() for x in ('example.com','example.test','noreply','no-reply','donotreply')):
                return email.lower(), row.get('link','')
    return '', ''

def search(niche,location='',keywords='',minimum=0,maximum=100000000,limit=20,enrich_emails=False):
    if not config.SERPAPI_API_KEY: raise RuntimeError('SERPAPI_API_KEY missing. Configure SerpAPI for live public-web search, or load demo data.')
    terms=[x.strip() for x in keywords.split(',') if x.strip()][:4]
    queries=[f'site:instagram.com/ {niche} creator influencer {location}']+[f'site:instagram.com/ {t} creator {location}' for t in terms]
    found={}
    for q in queries:
        for row in _google_search(q,limit):
            link=row.get('link','')
            parsed=urlparse(link)
            if parsed.netloc.lower().removeprefix('www.') not in ('instagram.com','m.instagram.com'):continue
            parts=[x for x in parsed.path.split('/') if x]
            if not parts:continue
            user=parts[0].lower()
            if not re.fullmatch(r'[A-Za-z0-9._]{1,30}',user):continue
            if user in RESERVED:continue
            text=(row.get('title','')+' '+row.get('snippet','')).strip()
            em=next((e for e in EMAIL_RE.findall(text) if not any(z in e.lower() for z in ['example.com','noreply','no-reply'])), '')
            followers=parse_followers(text)
            if followers and not minimum<=followers<=maximum:continue
            found[user]={'username':user,'name':row.get('title','').split('(@')[0].strip() or user,'profile_url':f'https://www.instagram.com/{user}/','niche':niche,'followers':followers,'email':em,'email_source':'Search result snippet' if em else '', 'location':location,'bio':row.get('snippet',''),'source':'SerpAPI public web search'}
            if len(found)>=limit: break
        if len(found)>=limit: break
    results=list(found.values())
    if enrich_emails:
        for person in results:
            if not person.get('email'):
                email, source_url=find_public_business_email(person['username'],person.get('name',''))
                if email:
                    person['email']=email;person['email_source']=source_url or 'Public web search'
    return results
def demo_data():
    return [dict(username='sample_fit_creator',name='Sample Fitness Creator',niche='Fitness',followers=24500,email='creator1@example.test',location='Hyderabad, India',bio='Sample test record for fitness and healthy lifestyle content.',source='synthetic demo'),dict(username='sample_food_creator',name='Sample Food Creator',niche='Food',followers=52000,email='creator2@example.test',location='Bengaluru, India',bio='Sample test record for recipes and food reviews.',source='synthetic demo'),dict(username='sample_tech_creator',name='Sample Tech Creator',niche='Technology',followers=18000,email='',location='India',bio='Sample test record for technology explainers.',source='synthetic demo')]
