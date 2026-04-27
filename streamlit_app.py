import json, base64, secrets, textwrap, time as time_module
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_local_storage import LocalStorage

# ═══════════════════════════════════════════════════════════
# APP CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="Kundli AI", page_icon="🪐", layout="wide",
                   initial_sidebar_state="collapsed")
try: swe.set_ephe_path("ephe")
except: pass
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ═══════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
PLANETS = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,
           "Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
DIGNITIES = {"Sun":(0,6),"Moon":(1,7),"Mars":(9,3),"Mercury":(5,11),
             "Jupiter":(3,9),"Venus":(11,5),"Saturn":(6,0)}
OWN_SIGNS = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
             "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
SIGN_LORDS_MAP = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",
                  6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}
COMBUST_DEGREES = {"Mercury":14,"Venus":10,"Mars":17,"Jupiter":11,"Saturn":15}
NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
              "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
              "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
              "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
              "Uttara Bhadrapada","Revati"]
NAKSHATRA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]*3
NAK_NATURES = {
    "Fixed (Dhruva)":  ["Rohini","Uttara Phalguni","Uttara Ashadha","Uttara Bhadrapada"],
    "Movable (Chara)": ["Punarvasu","Swati","Shravana","Dhanishta","Shatabhisha"],
    "Fierce (Ugra)":   ["Bharani","Magha","Purva Phalguni","Purva Ashadha","Purva Bhadrapada"],
    "Mixed (Mishra)":  ["Krittika","Vishakha"],
    "Swift (Kshipra)": ["Ashwini","Pushya","Hasta"],
    "Tender (Mridu)":  ["Mrigashira","Chitra","Anuradha","Revati"],
    "Sharp (Tikshna)": ["Ardra","Ashlesha","Jyeshtha","Mula"],
}
NAK_ADVICE = {
    "Fixed (Dhruva)":  "Best for long-term commitments, buying property, and starting permanent things.",
    "Movable (Chara)": "Great for travel, change, buying vehicles, or beginning new chapters.",
    "Fierce (Ugra)":   "Intense energy — good for assertive action, cutting through obstacles.",
    "Mixed (Mishra)":  "Average day — stick to routine tasks and pending work.",
    "Swift (Kshipra)": "High-pace energy — ideal for quick tasks, trading, and fast decisions.",
    "Tender (Mridu)":  "Soft, creative day — perfect for romance, arts, and new friendships.",
    "Sharp (Tikshna)": "Focused energy — excellent for research, analysis, and ending bad habits.",
}
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
               "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
YOGA_NAMES = ["Vishkambha","Priti","Ayushman","Saubhagya","Sobhana","Atiganda","Sukarma",
              "Dhriti","Soola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
              "Siddhi","Vyatipata","Variyan","Parigha","Siva","Siddha","Sadhya","Subha",
              "Sukla","Brahma","Indra","Vaidhriti"]
YEAR_DAYS=365.2425; MOVABLE_SIGNS={0,3,6,9}; FIXED_SIGNS={1,4,7,10}
DEB_SIGN_LORDS={"Sun":"Venus","Moon":"Mars","Mars":"Moon","Mercury":"Jupiter",
                "Jupiter":"Saturn","Venus":"Mercury","Saturn":"Mars"}
EXALT_LORD_IN_DEB_SIGN={"Sun":"Saturn","Moon":None,"Mars":"Jupiter","Mercury":"Venus",
                         "Jupiter":"Mars","Venus":"Mercury","Saturn":"Sun"}
PYTH_MAP={'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':1,'k':2,'l':3,
          'm':4,'n':5,'o':6,'p':7,'q':8,'r':9,'s':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8}
CHALDEAN_MAP={'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,'k':2,'l':3,
              'm':4,'n':5,'o':7,'p':8,'q':1,'r':2,'s':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}
FULL_TAROT_DECK = ["The Fool","The Magician","The High Priestess","The Empress","The Emperor",
    "The Hierophant","The Lovers","The Chariot","The Strength","The Hermit",
    "Wheel of Fortune","Justice","The Hanged Man","Death","Temperance","The Devil",
    "The Tower","The Star","The Moon","The Sun","Judgement","The World"]
for suit in ["Wands","Cups","Swords","Pentacles"]:
    for rank in ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten",
                 "Page","Knight","Queen","King"]:
        FULL_TAROT_DECK.append(f"{rank} of {suit}")
COMPARISON_CRITERIA = ["Wealth Potential — Who builds the most wealth?",
    "Relationship Quality — Who has the best marriage/love life?",
    "Career Success — Who reaches the highest professional position?",
    "Life Struggles — Who faces the most karmic obstacles?",
    "Health & Longevity — Who has the strongest constitution?",
    "Happiness & Contentment — Who lives the most fulfilled life?",
    "Luck & Fortune — Who is the most naturally fortunate?",
    "Spiritual Depth — Who is the most spiritually evolved?",
    "Hidden Pitfalls — Who faces the most unexpected structural problems?"]
PERSONAL_YEAR_MEANINGS = {1:"New beginnings, independence, leadership.",
    2:"Partnership, patience, diplomacy.", 3:"Creativity, expression, social energy.",
    4:"Hard work, foundations, discipline.", 5:"Freedom, change, adventure.",
    6:"Home, family, responsibility.", 7:"Reflection, spirituality, inner growth.",
    8:"Power, ambition, material success.", 9:"Completion, release, transformation.",
    11:"Intuition, spiritual awakening, inspiration (Master Number).",
    22:"Mastery, large-scale building, legacy (Master Number).",
    33:"Compassion, teaching, healing (Master Number)."}
CELTIC_CROSS_POSITIONS = [
    "1. The Present — Core issue or central energy",
    "2. The Challenge — What crosses or complicates",
    "3. The Foundation — Unconscious influences, deep roots",
    "4. The Past — What is passing or recently passed",
    "5. The Crown — Potential outcome or conscious goal",
    "6. The Near Future — What approaches in coming weeks",
    "7. The Self — Your attitude, how you show up",
    "8. External Influences — Others or environment",
    "9. Hopes & Fears — Inner tension",
    "10. The Outcome — Most likely resolution"]
PDF_BASE="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/"
PDF_HTRH1=f"{PDF_BASE}htrh1.pdf"; PDF_HTRH2=f"{PDF_BASE}htrh2.pdf"
PDF_TGUIDE=f"{PDF_BASE}tguide.pdf"
PDF_NUMEW1=f"{PDF_BASE}numeguide1.pdf"; PDF_NUMEW2=f"{PDF_BASE}numeguide2.pdf"
PDF_NUMEV=f"{PDF_BASE}vedicnume.pdf"
TAROT_BASE="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/tarot/"
NAV_PAGES=["Dashboard","The Oracle","Mystic Tarot","Horoscopes","Numerology","Saved Profiles"]

# ═══════════════════════════════════════════════════════════
# SESSION STATE & QUERY PARAMS (navigation)
# ═══════════════════════════════════════════════════════════
localS = LocalStorage()

# Read query param for bottom-nav navigation FIRST
_qp = st.query_params.get("p","")
if _qp in NAV_PAGES:
    if 'nav_page' not in st.session_state or st.session_state.nav_page != _qp:
        st.session_state.nav_page = _qp

if 'db' not in st.session_state: st.session_state.db=[]
if 'db_loaded' not in st.session_state:
    saved=localS.getItem("kundli_vault")
    if saved is not None:
        if isinstance(saved,str) and saved.strip():
            try: st.session_state.db=json.loads(saved)
            except: pass
        elif isinstance(saved,list): st.session_state.db=saved
    st.session_state.db_loaded=True
if 'default_profile_idx' not in st.session_state:
    di=localS.getItem("kundli_default")
    try: st.session_state.default_profile_idx=int(di) if di is not None and str(di).strip().isdigit() else None
    except: st.session_state.default_profile_idx=None
if 'needs_sync'       not in st.session_state: st.session_state.needs_sync=False
if 'custom_criteria'  not in st.session_state: st.session_state.custom_criteria=[]
if 'editing_idx'      not in st.session_state: st.session_state.editing_idx=None
if 'comp_slots'       not in st.session_state: st.session_state.comp_slots=2
if 'nav_page'         not in st.session_state: st.session_state.nav_page="Dashboard"
if 'active_mission'   not in st.session_state: st.session_state.active_mission="Deep Personal Analysis"
if 'tarot_tab'        not in st.session_state: st.session_state.tarot_tab="three"
if 'tarot3_drawn'     not in st.session_state: st.session_state.tarot3_drawn=False
if 'tarot3_cards'     not in st.session_state: st.session_state.tarot3_cards=[]
if 'tarot3_states'    not in st.session_state: st.session_state.tarot3_states=[]
if 'tarot3_mode'      not in st.session_state: st.session_state.tarot3_mode="General Guidance"
if 'yn_drawn'         not in st.session_state: st.session_state.yn_drawn=False
if 'yn_card'          not in st.session_state: st.session_state.yn_card=None
if 'yn_state'         not in st.session_state: st.session_state.yn_state=None
if 'cc_drawn'         not in st.session_state: st.session_state.cc_drawn=False
if 'cc_cards'         not in st.session_state: st.session_state.cc_cards=[]
if 'cc_states'        not in st.session_state: st.session_state.cc_states=[]
if 'bc_revealed'      not in st.session_state: st.session_state.bc_revealed=False
if 'bc_dob'           not in st.session_state: st.session_state.bc_dob=None
if 'dash_tarot_card'  not in st.session_state: st.session_state.dash_tarot_card=None
if 'dash_tarot_state' not in st.session_state: st.session_state.dash_tarot_state=None
if 'dash_tarot_date'  not in st.session_state: st.session_state.dash_tarot_date=None
if 'show_add_profile' not in st.session_state: st.session_state.show_add_profile=False
if 'select_all_cb'    not in st.session_state: st.session_state.select_all_cb=False
for i in range(len(COMPARISON_CRITERIA)):
    if f"chk_{i}" not in st.session_state: st.session_state[f"chk_{i}"]=False

def sync_db(): st.session_state.needs_sync=True
def is_duplicate_in_db(p): return any(x['name']==p['name'] and x['date']==p['date'] for x in st.session_state.db)
def format_date_ui(s): return datetime.fromisoformat(s).strftime('%d %b %Y')
def get_filename(n): return n.lower().replace(' ','')+'.jpg'
def toggle_all_criteria():
    v=st.session_state.select_all_cb
    for i in range(len(COMPARISON_CRITERIA)): st.session_state[f"chk_{i}"]=v
    for i in range(len(st.session_state.custom_criteria)): st.session_state[f"cc_{i}"]=v
def get_default_profile():
    idx=st.session_state.default_profile_idx
    if idx is not None and 0<=idx<len(st.session_state.db): return st.session_state.db[idx],idx
    return None,None
def set_default_profile(idx):
    st.session_state.default_profile_idx=idx
    localS.setItem("kundli_default",str(idx))
def clear_default_profile():
    st.session_state.default_profile_idx=None
    localS.setItem("kundli_default","")
def get_local_today(tz_string="Asia/Kolkata"):
    """FIX: Use user timezone, not server UTC, for date-based features."""
    try: return datetime.now(ZoneInfo(tz_string)).date()
    except: return datetime.now(ZoneInfo("Asia/Kolkata")).date()
def sorted_profile_options():
    if not st.session_state.db: return []
    def_idx=st.session_state.default_profile_idx
    result=[(i,p) for i,p in enumerate(st.session_state.db)]
    if def_idx is not None and 0<=def_idx<len(st.session_state.db):
        result.sort(key=lambda x: 0 if x[0]==def_idx else 1)
    return result

# ═══════════════════════════════════════════════════════════
# BASIC HELPERS
# ═══════════════════════════════════════════════════════════
def sign_name(i): return SIGNS[i%12]
def sign_index_from_lon(lon): return int(lon//30)%12
def format_dms(angle):
    angle%=360; d=int(angle); mf=(angle-d)*60; m=int(mf); s=int(round((mf-m)*60))
    if s==60: s,m=0,m+1
    if m==60: m,d=0,d+1
    return f"{d:02d}°{m:02d}'"
def nakshatra_info(lon):
    ns=360/27; idx=min(int((lon%360)//ns),26)
    return NAKSHATRAS[idx],NAKSHATRA_LORDS[idx],int(((lon%360%ns)//(ns/4)))+1
def get_baladi_avastha(lon):
    si=int(lon//30)%12; states=["Infant","Youth","Adult","Old","Dead"]
    if si%2!=0: states=states[::-1]
    return states[int((lon%30)//6)]
def get_panchanga(sun_lon,moon_lon,dt_local):
    tv=(moon_lon-sun_lon)%360; tn=int(tv/12)+1
    paksha="Shukla (Waxing)" if tv<180 else "Krishna (Waning)"; td=tn if tn<=15 else tn-15
    yn=min(int(((moon_lon+sun_lon)%360)/(360/27)),26); ki=int(tv/6)
    if ki==0: kn="Kintughna (Fixed)"
    elif 1<=ki<=56: kn=f"{['Bava','Balava','Kaulava','Taitila','Gara','Vanija','Vishti'][(ki-1)%7]} (Movable)"
    elif ki==57: kn="Sakuni (Fixed)"
    elif ki==58: kn="Chatushpada (Fixed)"
    else: kn="Naga (Fixed)"
    return {"tithi":f"{td} {paksha}","yoga":YOGA_NAMES[yn],"karana":kn,
            "weekday":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][dt_local.weekday()]}
def whole_sign_house(ls,ps): return ((ps-ls)%12)+1
def get_western_sign(month,day):
    cusps=[(1,19,"Capricorn"),(2,18,"Aquarius"),(3,20,"Pisces"),(4,19,"Aries"),(5,20,"Taurus"),
           (6,20,"Gemini"),(7,22,"Cancer"),(8,22,"Leo"),(9,22,"Virgo"),(10,22,"Libra"),
           (11,21,"Scorpio"),(12,21,"Sagittarius")]
    for em,ed,sign in cusps:
        if month<em or (month==em and day<=ed): return sign
    return "Capricorn"

@st.cache_data(show_spinner=False)
def geocode_place(pt):
    try: loc=Nominatim(user_agent="kundli_ai_suite").geocode(pt,exactly_one=True,timeout=10); return (loc.latitude,loc.longitude,loc.address) if loc else None
    except: return None
@st.cache_data(show_spinner=False)
def timezone_for_latlon(lat,lon): return TimezoneFinder().timezone_at(lat=lat,lng=lon)
def local_to_julian_day(d,t,tz_name):
    lz=ZoneInfo(tz_name); dtl=datetime.combine(d,t).replace(tzinfo=lz)
    dtu=dtl.astimezone(ZoneInfo("UTC"))
    return swe.julday(dtu.year,dtu.month,dtu.day,dtu.hour+dtu.minute/60+dtu.second/3600),dtl,dtu
def get_lagna_and_cusps(jd,lat,lon):
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL; cusps,ascmc=swe.houses_ex(jd,lat,lon,b"O",f); return float(ascmc[0])%360,cusps
def get_planet_longitude_and_speed(jd,pid):
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED; res,_=swe.calc_ut(jd,pid,f); return float(res[0])%360,float(res[3])
def get_planet_lon_lat(jd,pid):
    """Return (lon, lat, speed) — needed for Graha Yuddha latitude comparison."""
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED; res,_=swe.calc_ut(jd,pid,f)
    return float(res[0])%360,float(res[1]),float(res[3])
def get_rahu_longitude(jd):
    res,_=swe.calc_ut(jd,swe.MEAN_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL); return float(res[0])%360
def get_placidus_cusps(jd,lat,lon):
    cusps,_=swe.houses_ex(jd,lat,lon,b"P",swe.FLG_SWIEPH|swe.FLG_SIDEREAL); return cusps

@st.cache_data(ttl=3600,show_spinner=False)
def get_live_cosmic_weather():
    dt_now=datetime.now(ZoneInfo("UTC"))  # FIX: no longer utcnow()
    jd=swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    moon_lon,_=swe.calc_ut(jd,swe.MOON,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    sun_lon,_=swe.calc_ut(jd,swe.SUN,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    moon_sidx=sign_index_from_lon(moon_lon[0]); sun_sidx=sign_index_from_lon(sun_lon[0])
    nak,_,_=nakshatra_info(moon_lon[0]); panch=get_panchanga(sun_lon[0],moon_lon[0],dt_now)
    retrogrades=[]
    for pname in ["Mars","Mercury","Jupiter","Venus","Saturn"]:
        _,spd=get_planet_longitude_and_speed(jd,PLANETS[pname])
        if spd<0: retrogrades.append(pname)
    nature_type="Mixed (Mishra)"; advice=NAK_ADVICE["Mixed (Mishra)"]
    for nt,naks in NAK_NATURES.items():
        if nak in naks: nature_type=nt; advice=NAK_ADVICE[nt]; break
    all_pos={}
    for pname,pid in PLANETS.items():
        lon,_=get_planet_longitude_and_speed(jd,pid); all_pos[pname]=sign_name(sign_index_from_lon(lon))
    r_lon,_=swe.calc_ut(jd,swe.MEAN_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    all_pos["Rahu"]=sign_name(sign_index_from_lon(float(r_lon[0])%360))
    all_pos["Ketu"]=sign_name(sign_index_from_lon((float(r_lon[0])+180)%360))
    return {"moon_sign":sign_name(moon_sidx),"sun_sign":sign_name(sun_sidx),"nakshatra":nak,
            "tithi":panch["tithi"],"yoga":panch["yoga"],"retrogrades":retrogrades,
            "nature":nature_type,"advice":advice,"all_pos":all_pos}

def generate_horoscope_text(sign,mode,date_val):
    import random; rng=random.Random(f"{sign}_{mode}_{date_val}")
    g=["The cosmos aligns in your favor today. Clarity arrives where confusion once lived.",
       "Patience is your greatest ally right now. Let situations unfold at their own pace.",
       "You radiate a magnetic, positive energy. Others will naturally gravitate toward you.",
       "A period of quiet introspection is needed. Your inner voice holds the key.",
       "Unexpected news or a shift in perspective is on its way. Stay adaptable.",
       "Your creative energy is at a powerful peak. Channel it into something meaningful.",
       "Your mind needs rest more than stimulation. Avoid overcommitting to others.",
       "This is a powerful time to set intentions. The universe backs your ambitions."]
    l=["Communication with loved ones flows with unusual ease and warmth today.",
       "A slight misunderstanding may surface. Approach it with empathy, not ego.",
       "Romantic energy swirls around you. Plan something meaningful for someone special.",
       "Today calls for deep self-love. Treat yourself with the same kindness you show others.",
       "A connection from your past may resurface. Proceed with an open yet discerning heart."]
    c=["Your diligent work is finally catching the right kind of attention. Stay the course.",
       "A professional challenge tests your composure. Think strategically, not reactively.",
       "Collaboration unlocks a door that individual effort cannot. Reach out.",
       "A breakthrough idea arrives — write it down immediately. The timing is perfect.",
       "Avoid impulsive financial moves today. Thorough research will protect your interests."]
    return f"**General:** {rng.choice(g)}\n\n**Love & Relationships:** {rng.choice(l)}\n\n**Career & Finance:** {rng.choice(c)}"

# ═══════════════════════════════════════════════════════════
# ADVANCED ASTRO ENGINES
# ═══════════════════════════════════════════════════════════
def get_kp_sub_lord(lon):
    ns=360/27; idx=int((lon%360)//ns); nak_lord=NAKSHATRA_LORDS[idx]
    deg=lon%360-idx*ns; si=DASHA_ORDER.index(nak_lord); seq=DASHA_ORDER[si:]+DASHA_ORDER[:si]
    acc=0.0
    for sl in seq:
        acc+=(DASHA_YEARS[sl]/120.0)*ns
        if deg<=acc+1e-9: return sl
    return seq[-1]
def get_planet_lon_helper(pname,planet_data,r_lon,k_lon):
    if pname in planet_data: return planet_data[pname][0]
    if pname=="Rahu": return r_lon
    if pname=="Ketu": return k_lon
def get_planet_house(pname,ls,planet_data,r_lon,k_lon):
    lon=get_planet_lon_helper(pname,planet_data,r_lon,k_lon)
    return whole_sign_house(ls,sign_index_from_lon(lon)) if lon is not None else None
def get_lagna_lord_chain(ls,planet_data,r_lon,k_lon):
    ll=SIGN_LORDS_MAP[ls]; ll_lon=get_planet_lon_helper(ll,planet_data,r_lon,k_lon)
    ll_sidx=sign_index_from_lon(ll_lon); ll_house=whole_sign_house(ls,ll_sidx)
    tags=[]
    if ll in DIGNITIES:
        if ll_sidx==DIGNITIES[ll][0]: tags.append("Exalted")
        elif ll_sidx==DIGNITIES[ll][1]: tags.append("Debilitated")
    if ll in OWN_SIGNS and ll_sidx in OWN_SIGNS[ll]: tags.append("Own Sign")
    if ll in planet_data and planet_data[ll][1]<0: tags.append("Retrograde")
    tag_str=f" [{', '.join(tags)}]" if tags else ""
    disp=SIGN_LORDS_MAP[ll_sidx]; disp_h=get_planet_house(disp,ls,planet_data,r_lon,k_lon)
    return f"{ll} → H{ll_house} ({sign_name(ll_sidx)}{tag_str}) → dispositor {disp} in H{disp_h}"
def get_conjunctions(ls,planet_data,r_lon,k_lon):
    all_p={}
    for pn,(plon,_) in planet_data.items(): h=whole_sign_house(ls,sign_index_from_lon(plon)); all_p.setdefault(h,[]).append(pn)
    for pn,plon in [("Rahu",r_lon),("Ketu",k_lon)]: h=whole_sign_house(ls,sign_index_from_lon(plon)); all_p.setdefault(h,[]).append(pn)
    return [f"{' + '.join(plist)} conjunct in H{h} ({sign_name((ls+h-1)%12)})" for h,plist in all_p.items() if len(plist)>=2]
def get_mutual_aspects(ls,planet_data,r_lon,k_lon):
    spec={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[5,7,9],"Ketu":[5,7,9]}
    def asp(pn,h): return {((h+j-2)%12)+1 for j in spec.get(pn,[7])}
    houses={pn:whole_sign_house(ls,sign_index_from_lon(planet_data[pn][0])) for pn in planet_data}
    houses["Rahu"]=whole_sign_house(ls,sign_index_from_lon(r_lon))
    houses["Ketu"]=whole_sign_house(ls,sign_index_from_lon(k_lon))
    plist=list(houses.keys()); mutual=[]
    for i,p1 in enumerate(plist):
        for p2 in plist[i+1:]:
            h1,h2=houses[p1],houses[p2]
            if h1!=h2 and h2 in asp(p1,h1) and h1 in asp(p2,h2): mutual.append(f"{p1}(H{h1}) ↔ {p2}(H{h2})")
    return mutual
def detect_graha_yuddha(jd_ut, planet_data):
    """FIX: Use ecliptic latitude (res[1]) to determine winner, not longitude."""
    eligible=["Mars","Mercury","Jupiter","Venus","Saturn"]
    plist=list(eligible); wars=[]
    for i,p1 in enumerate(plist):
        for p2 in plist[i+1:]:
            l1=planet_data[p1][0]; l2=planet_data[p2][0]
            diff=abs(l1-l2); diff=min(diff,360-diff)
            if diff<=1.0:
                # Fetch ecliptic latitude for winner determination
                try:
                    res1,_=swe.calc_ut(jd_ut,PLANETS[p1],swe.FLG_SWIEPH|swe.FLG_SIDEREAL); lat1=float(res1[1])
                    res2,_=swe.calc_ut(jd_ut,PLANETS[p2],swe.FLG_SWIEPH|swe.FLG_SIDEREAL); lat2=float(res2[1])
                    winner=p1 if lat1>lat2 else p2; loser=p2 if lat1>lat2 else p1
                except: winner=p1 if l1>l2 else p2; loser=p2 if l1>l2 else p1
                wars.append((winner,loser,round(diff,3)))
    return wars
def get_functional_planets(ls):
    trikona={1,5,9}; kendra={1,4,7,10}; trika={6,8,12}
    house_lords={}
    for h in range(1,13): lord=SIGN_LORDS_MAP[(ls+h-1)%12]; house_lords.setdefault(lord,[]).append(h)
    yks=[]; bens=[]; mals=[]; neu=[]
    for planet,houses in house_lords.items():
        has_tri=any(h in trikona for h in houses); has_ken=any(h in kendra and h!=1 for h in houses)
        has_trika=any(h in trika for h in houses)
        if has_tri and has_ken: yks.append(planet)
        elif has_tri: bens.append(planet)
        elif has_trika and not has_tri: mals.append(planet)
        else: neu.append(planet)
    return bens,mals,yks,neu
def get_house_strength_summary(ls,planet_data,r_lon,k_lon,placidus_cusps):
    key_houses={7:("Marriage & Spouse",{2,7,11}),10:("Career & Status",{1,6,10,11}),
                2:("Wealth & Family",{2,11}),5:("Intelligence & Children",{5,11}),
                4:("Home & Mother",{4,12}),11:("Gains & Desires",{3,6,11})}
    summaries=[]
    for h,(theme,ev_houses) in key_houses.items():
        h_sidx=(ls+h-1)%12; h_lord=SIGN_LORDS_MAP[h_sidx]
        lord_house=get_planet_house(h_lord,ls,planet_data,r_lon,k_lon)
        lord_sidx=sign_index_from_lon(get_planet_lon_helper(h_lord,planet_data,r_lon,k_lon))
        flags=[]
        if h_lord in DIGNITIES:
            if lord_sidx==DIGNITIES[h_lord][0]: flags.append("Lord Exalted")
            elif lord_sidx==DIGNITIES[h_lord][1]: flags.append("Lord Debilitated")
        if h_lord in OWN_SIGNS and lord_sidx in OWN_SIGNS[h_lord]: flags.append("Lord Own Sign")
        if lord_house in {6,8,12}: flags.append(f"Lord in dusthana H{lord_house}")
        elif lord_house in {1,4,7,10}: flags.append(f"Lord in Kendra H{lord_house}")
        kp_sl=get_kp_sub_lord(placidus_cusps[h-1])
        sigs=get_planet_house_significations(kp_sl,ls,planet_data,r_lon,k_lon)
        matched=sigs&ev_houses
        verdict="STRONGLY PROMISED" if len(matched)>=2 or (max(ev_houses) in matched) else ("WEAKLY PROMISED" if len(matched)==1 else "NOT CLEARLY PROMISED")
        flag_str=" | ".join(flags) if flags else "Neutral"
        summaries.append(f"H{h} ({theme}): Lord={h_lord}(H{lord_house}) [{flag_str}] | KP SL={kp_sl}: {verdict}")
    return summaries
def check_neecha_bhanga(pname,ls,moon_sidx,planet_data,r_lon,k_lon):
    if pname not in DIGNITIES: return None
    p_sidx=sign_index_from_lon(planet_data[pname][0])
    if p_sidx!=DIGNITIES[pname][1]: return None
    kendra={1,4,7,10}
    def hf(ref,pn):
        lon=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(ref,sign_index_from_lon(lon)) if lon else None
    conds=[]
    dsl=DEB_SIGN_LORDS.get(pname)
    if dsl:
        h=hf(ls,dsl)
        if h in kendra: conds.append(f"dispositor ({dsl}) in Kendra H{h} from Lagna")
        h=hf(moon_sidx,dsl)
        if h in kendra: conds.append(f"dispositor ({dsl}) in Kendra H{h} from Moon")
    exl=EXALT_LORD_IN_DEB_SIGN.get(pname)
    if exl:
        h=hf(ls,exl)
        if h in kendra: conds.append(f"exaltation-sign lord ({exl}) in Kendra H{h} from Lagna")
    hfm=whole_sign_house(moon_sidx,p_sidx)
    if hfm in kendra: conds.append(f"debilitated planet in Kendra H{hfm} from Moon")
    return conds if conds else None
def get_chara_karakas(planet_data):
    deg={pn:planet_data[pn][0]%30 for pn in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]}
    ranked=sorted(deg,key=deg.get,reverse=True)
    return ranked[0],deg[ranked[0]],ranked[1],deg[ranked[1]]
def detect_yogas(ls,moon_sidx,planet_data,r_lon,k_lon):
    def ho(pn):
        lon=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(ls,sign_index_from_lon(lon)) if lon else None
    def ink(h1,h2): return (h2-h1)%12 in {0,3,6,9}
    yogas=[]; absent=[]
    mh,jh=ho("Moon"),ho("Jupiter")
    if mh and jh and ink(mh,jh): yogas.append(("Gajakesari Yoga",f"Moon(H{mh})+Jupiter(H{jh}) mutual Kendra — intelligence, fame, stability"))
    else: absent.append("Gajakesari Yoga — Moon+Jupiter not in mutual Kendra")
    for planet,(yname,ex_sidx) in {"Mars":("Ruchaka",9),"Mercury":("Bhadra",5),"Jupiter":("Hamsa",3),"Venus":("Malavya",11),"Saturn":("Shasha",6)}.items():
        psidx=sign_index_from_lon(planet_data[planet][0]); ph=whole_sign_house(ls,psidx)
        own=planet in OWN_SIGNS and psidx in OWN_SIGNS[planet]
        if (own or psidx==ex_sidx) and ph in {1,4,7,10}:
            yogas.append((f"{yname} Yoga",f"{planet} in {'own' if own else 'exaltation'} in Kendra H{ph} — Pancha Mahapurusha"))
        else: absent.append(f"{yname} Yoga — {planet} not in own/exalt+Kendra")
    if ho("Sun")==ho("Mercury"): yogas.append(("Budha-Aditya Yoga",f"Sun+Mercury conjunct H{ho('Sun')} — intellect, communication, reputation"))
    else: absent.append("Budha-Aditya Yoga — Sun+Mercury not conjunct")
    if ho("Moon")==ho("Mars"): yogas.append(("Chandra-Mangala Yoga",f"Moon+Mars conjunct H{ho('Moon')} — entrepreneurial drive"))
    else: absent.append("Chandra-Mangala Yoga — Moon+Mars not conjunct")
    mh2=ho("Moon")
    if mh2:
        t6=((mh2-1+5)%12)+1; t7=((mh2-1+6)%12)+1; t8=((mh2-1+7)%12)+1
        ben=[b for b in ["Mercury","Jupiter","Venus"] if ho(b) in {t6,t7,t8}]
        if len(ben)>=2: yogas.append(("Adhi Yoga",f"{', '.join(ben)} in 6/7/8 from Moon — leadership, longevity"))
        else: absent.append("Adhi Yoga — <2 benefics in 6/7/8 from Moon")
    tri_lords={SIGN_LORDS_MAP[(ls+h-1)%12] for h in [1,5,9]}
    ken_lords={SIGN_LORDS_MAP[(ls+h-1)%12] for h in [1,4,7,10]}
    rj=[]
    for tl in tri_lords:
        for kl in ken_lords:
            if tl!=kl:
                th,kh=ho(tl),ho(kl)
                if th and kh and th==kh: rj.append(f"{tl}+{kl} in H{th}")
    if rj: yogas.append(("Raja Yoga",f"Trikona+Kendra lords conjunct: {'; '.join(rj[:2])} — power, high status"))
    else: absent.append("Raja Yoga — no Trikona+Kendra lord conjunction")
    dust_lords=[SIGN_LORDS_MAP[(ls+h-1)%12] for h in [6,8,12]]
    dust_in=[dl for dl in dust_lords if ho(dl) in {6,8,12}]
    if len(dust_in)>=2: yogas.append(("Viparita Raja Yoga",f"Dusthana lords ({', '.join(dust_in)}) in dusthana — rise after adversity"))
    else: absent.append("Viparita Raja Yoga — insufficient dusthana lords in dusthana")
    if mh2:
        h2m=((mh2-1+1)%12)+1; h12m=((mh2-1-1)%12)+1
        all_h={pn:ho(pn) for pn in list(planet_data.keys())+["Rahu","Ketu"] if pn!="Moon"}
        flanking=[pn for pn,h in all_h.items() if h in {h2m,h12m} and pn not in {"Rahu","Ketu"}]
        if not flanking: yogas.append(("Kemadruma Yoga (Negative)",f"No planets flanking Moon in H{h2m}/H{h12m} — emotional isolation tendency"))
    return yogas,absent
def calculate_sade_sati(natal_moon_sidx):
    utc=datetime.now(ZoneInfo("UTC"))
    jd=swe.julday(utc.year,utc.month,utc.day,utc.hour+utc.minute/60.0)
    res,_=swe.calc_ut(jd,swe.SATURN,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    sat_sidx=sign_index_from_lon(float(res[0])%360); diff=(sat_sidx-natal_moon_sidx)%12
    phases={11:"ACTIVE — Phase 1 (Rising)",0:"ACTIVE — Phase 2 (Peak — most intense)",1:"ACTIVE — Phase 3 (Setting)"}
    if diff in phases: return f"{phases[diff]}: Saturn in {sign_name(sat_sidx)}, natal Moon in {sign_name(natal_moon_sidx)}."
    return f"NOT ACTIVE (Saturn is {diff} signs from natal Moon in {sign_name(natal_moon_sidx)})."
def check_manglik_dosha(ls,moon_sidx,mars_sidx):
    mh_l=whole_sign_house(ls,mars_sidx); mh_m=whole_sign_house(moon_sidx,mars_sidx)
    il=mh_l in [1,4,7,8,12]; im=mh_m in [1,4,7,8,12]
    if il and im: return "HIGH MANGLIK — Mars in Manglik house from both Ascendant and Moon"
    elif il: return "MILD MANGLIK — Mars in Manglik house from Ascendant only"
    elif im: return "MILD MANGLIK — Mars in Manglik house from Moon only"
    return "NOT MANGLIK — No Kuja Dosha"
def get_manglik_cancellation_verdict(ma,mb):
    m1="NOT MANGLIK" not in ma; m2="NOT MANGLIK" not in mb
    if m1 and m2: return "MANGLIK DOSHA CANCELLED — Both partners are Manglik (classical cancellation). No remedy required."
    elif not m1 and not m2: return "No Manglik Dosha in either chart."
    who="Person 1 is Manglik" if m1 else "Person 2 is Manglik"
    return f"MANGLIK IMBALANCE — {who}, the other is not. Carefully chosen Muhurta and remedies advisable."
def calculate_ashta_koota(ma,mb):
    s1=sign_index_from_lon(ma); s2=sign_index_from_lon(mb)
    n1=min(int((ma%360)//(360/27)),26); n2=min(int((mb%360)//(360/27)),26)
    vm=[1,2,3,0,1,2,3,0,1,2,3,0]; v=1 if vm[s1]<=vm[s2] else 0
    va=[0,0,1,2,3,1,1,4,0,2,1,2]; va1,va2=va[s1],va[s2]
    if va1==va2: vap=2
    elif {va1,va2} in [{1,3},{1,4},{2,3}]: vap=0
    else: vap=1
    t1=((n2-n1)%27)%9; t2=((n1-n2)%27)%9
    ta=(0 if t1 in [2,4,6] else 1.5)+(0 if t2 in [2,4,6] else 1.5)
    ym=[0,1,2,3,3,4,5,2,5,6,6,7,8,9,8,9,10,10,4,11,12,11,13,0,13,7,1]
    y1,y2=ym[n1],ym[n2]; enemies=[{0,8},{1,13},{2,11},{3,12},{4,10},{5,6},{7,9}]
    yo=4 if y1==y2 else (0 if {y1,y2} in enemies else 2)
    lm=[0,1,2,3,4,2,1,0,5,6,6,5]; l1,l2=lm[s1],lm[s2]
    f_map={0:[3,4,5],1:[2,6],2:[1,4],3:[2,4],4:[0,3,5],5:[0,3,4],6:[1,2]}
    e_map={0:[2],1:[3,4],2:[3],3:[],4:[1,6],5:[1,2],6:[0,3,4]}
    def rel(a,b): return 2 if b in f_map.get(a,[]) else (0 if b in e_map.get(a,[]) else 1)
    ms={(2,2):5,(2,1):4,(1,2):4,(1,1):3,(2,0):1,(0,2):1,(1,0):.5,(0,1):.5,(0,0):0}
    m=ms.get((rel(l1,l2),rel(l2,l1)),0)
    gm={0:0,1:1,2:2,3:1,4:0,5:1,6:0,7:0,8:2,9:2,10:1,11:1,12:0,13:2,14:0,15:2,16:0,17:2,18:2,19:1,20:1,21:0,22:2,23:2,24:1,25:1,26:0}
    g1,g2=gm[n1],gm[n2]
    if g1==g2: g=6
    elif g1==0 and g2==1: g=6
    elif g1==1 and g2==0: g=5
    elif g1==0 and g2==2: g=1
    else: g=0
    dist=(s2-s1)%12; bh=7 if dist in [0,2,3,6,8,9,10] else 0
    nb=[0,1,2]*9; nd1,nd2=nb[n1],nb[n2]; nn=""; np=0
    if nd1==nd2:
        if n1==n2: nn="NADI DOSHA EXCEPTION: Same Nakshatra — Dosha CANCELLED."
        elif SIGN_LORDS_MAP[s1]!=SIGN_LORDS_MAP[s2]: nn="NADI DOSHA PARTIAL EXCEPTION: Different Moon sign lords — severity reduced."
    else: np=8
    total=v+vap+ta+yo+m+g+bh+np
    res=(f"TOTAL ASHTA KOOTA SCORE: {total}/36\n"
         f"  Varna(1):{v} | Vashya(2):{vap} | Tara(3):{ta} | Yoni(4):{yo}\n"
         f"  GrahaMaitri(5):{m} | Gana(6):{g} | Bhakoot(7):{bh} | Nadi(8):{np}")
    if nn: res+=f"\n  NOTE: {nn}"
    res+=f"\n  QUALITY: {'Excellent (31-36)' if total>=31 else 'Good (18-30)' if total>=18 else f'Challenging ({total}/36)'}"
    return res
def get_planet_house_significations(pname,ls,planet_data,r_lon,k_lon):
    lon=get_planet_lon_helper(pname,planet_data,r_lon,k_lon)
    if lon is None: return set()
    sigs=set(); psidx=sign_index_from_lon(lon); sigs.add(whole_sign_house(ls,psidx))
    for sidx,lord in SIGN_LORDS_MAP.items():
        if lord==pname: sigs.add(whole_sign_house(ls,sidx))
    _,sl,_=nakshatra_info(lon)
    if sl!=pname:
        sl_lon=get_planet_lon_helper(sl,planet_data,r_lon,k_lon)
        if sl_lon:
            sigs.add(whole_sign_house(ls,sign_index_from_lon(sl_lon)))
            for sidx,lord in SIGN_LORDS_MAP.items():
                if lord==sl: sigs.add(whole_sign_house(ls,sidx))
    return sigs
def build_vimshottari_timeline(dt_birth,moon_lon,dt_now):
    ns=360/27; idx=int((moon_lon%360)//ns); lord=NAKSHATRA_LORDS[idx]
    bal=DASHA_YEARS[lord]*(1-((moon_lon%360%ns)/ns))
    si=DASHA_ORDER.index(lord); seq=DASHA_ORDER[si:]+DASHA_ORDER[:si]
    dc=dt_birth; mdl=[(seq[0],bal)]+[(l,DASHA_YEARS[l]) for l in seq[1:]]
    for ml,my in mdl:
        nmd=dc+timedelta(days=my*YEAR_DAYS)
        if dt_now<nmd:
            ac=dc; aseq=DASHA_ORDER[DASHA_ORDER.index(ml):]+DASHA_ORDER[:DASHA_ORDER.index(ml)]
            for al in aseq:
                ay=(my*DASHA_YEARS[al])/120.0; nad=ac+timedelta(days=ay*YEAR_DAYS)
                if dt_now<nad:
                    pc=ac; pseq=DASHA_ORDER[DASHA_ORDER.index(al):]+DASHA_ORDER[:DASHA_ORDER.index(al)]
                    for pl in pseq:
                        py=(ay*DASHA_YEARS[pl])/120.0; npd=pc+timedelta(days=py*YEAR_DAYS)
                        if dt_now<npd:
                            return {"birth_nakshatra":NAKSHATRAS[idx],"start_lord":lord,"balance_years":bal,
                                    "current_md":ml,"current_ad":al,"current_pd":pl,"md_total_years":my,
                                    "md_start":dc,"md_end":nmd,"ad_start":ac,"ad_end":nad,"pd_start":pc,"pd_end":npd}
                        pc=npd
                ac=nad
        dc=nmd
    n=datetime.now()
    return {"birth_nakshatra":"Unknown","start_lord":"Unknown","balance_years":0,"current_md":"Unknown",
            "current_ad":"Unknown","current_pd":"Unknown","md_total_years":0,
            "md_start":n,"md_end":n,"ad_start":n,"ad_end":n,"pd_start":n,"pd_end":n}
def get_antardasha_table(di):
    ml=di['current_md']; my=di['md_total_years']
    if ml=="Unknown" or my==0: return []
    mi=DASHA_ORDER.index(ml); aseq=DASHA_ORDER[mi:]+DASHA_ORDER[:mi]
    cursor=di['md_start']; lines=[]; cur_al=di['current_ad']
    for al in aseq:
        ay=(my*DASHA_YEARS[al])/120.0; ad_end=cursor+timedelta(days=ay*YEAR_DAYS)
        lines.append(f"  {ml}/{al}: {cursor.strftime('%b %Y')} → {ad_end.strftime('%b %Y')}{'  ◀ NOW' if al==cur_al else ''}")
        cursor=ad_end
    return lines
def d2_si(lon):
    s=sign_index_from_lon(lon); d=lon%30
    return (4 if d<15 else 3) if s%2==0 else (3 if d<15 else 4)
def d3_si(lon): return (sign_index_from_lon(lon)+int((lon%30)//10)*4)%12
def d4_si(lon): return (sign_index_from_lon(lon)+int((lon%30)//7.5)*3)%12
def d7_si(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/7))
    return ((s if s%2==0 else (s+6)%12)+slot)%12
def d9_si(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/9))
    start=s if s in MOVABLE_SIGNS else ((s+8)%12 if s in FIXED_SIGNS else (s+4)%12)
    return (start+slot)%12
def d10_si(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//3)
    return ((s if s%2==0 else (s+8)%12)+slot)%12
def d12_si(lon): return (sign_index_from_lon(lon)+int((lon%360%30)//2.5))%12
def d60_si(lon): return (sign_index_from_lon(lon)+int((lon%30)*2))%12
def get_moon_lon_from_profile(profile):
    d=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    t=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd,_,__=local_to_julian_day(d,t,profile['tz']); lon,_=get_planet_longitude_and_speed(jd,PLANETS["Moon"]); return lon

# ═══════════════════════════════════════════════════════════
# NUMEROLOGY ENGINE
# ═══════════════════════════════════════════════════════════
def _reduce(n,keep=True):
    if keep and n in [11,22,33]: return n
    while n>9:
        if keep and n in [11,22,33]: return n
        n=sum(int(d) for d in str(n))
    return n
def calculate_numerology_core(name,dob_str,system="Western (Pythagorean)"):
    y,m,d=map(int,dob_str.split('-'))
    nm=PYTH_MAP if system=="Western (Pythagorean)" else CHALDEAN_MAP
    lp=_reduce(_reduce(y)+_reduce(m)+_reduce(d))
    clean=name.lower().replace(" ",""); vowels=set('aeiou')
    ds=su=ps=0
    for ch in clean:
        if ch in nm:
            val=nm[ch]; ds+=val
            if ch in vowels: su+=val
            else: ps+=val
    return _reduce(lp),_reduce(ds),_reduce(su),_reduce(ps)
def get_personal_year(dob_str,for_year=None):
    if for_year is None: for_year=datetime.now(ZoneInfo("Asia/Kolkata")).year
    y,m,d=map(int,dob_str.split('-'))
    return _reduce(_reduce(m)+_reduce(d)+_reduce(for_year))
def get_personal_month(dob_str,tz="Asia/Kolkata"):
    py=get_personal_year(dob_str); cm=datetime.now(ZoneInfo(tz)).month  # FIX: use tz
    return _reduce(py+_reduce(cm))
def get_personal_day(dob_str,tz="Asia/Kolkata"):
    pm=get_personal_month(dob_str,tz); cd=datetime.now(ZoneInfo(tz)).day  # FIX: use tz
    return _reduce(pm+_reduce(cd))
def get_pinnacle_cycles(dob_str):
    y,m,d=map(int,dob_str.split('-'))
    lp,_,_,_=calculate_numerology_core("",dob_str)
    p1=_reduce(_reduce(m)+_reduce(d)); p2=_reduce(_reduce(d)+_reduce(y))
    p3=_reduce(p1+p2); p4=_reduce(_reduce(m)+_reduce(y))
    # Challenges: subtraction method
    c1=abs(_reduce(m,keep=False)-_reduce(d,keep=False))
    c2=abs(_reduce(d,keep=False)-_reduce(y,keep=False))
    c3=abs(c1-c2)
    c4=abs(_reduce(m,keep=False)-_reduce(y,keep=False))
    d1e=36-lp
    r1=(y,y+d1e,p1,c1); r2=(y+d1e,y+d1e+9,p2,c2)
    r3=(y+d1e+9,y+d1e+18,p3,c3); r4=(y+d1e+18,y+100,p4,c4)
    return r1,r2,r3,r4
def get_tarot_birth_card(dob_str):
    digits=[int(c) for c in dob_str.replace('-','') if c.isdigit()]
    total=sum(digits)
    while total>22: total=sum(int(d) for d in str(total))
    if total==22 or total==0: return FULL_TAROT_DECK[0]
    return FULL_TAROT_DECK[total-1]

# ═══════════════════════════════════════════════════════════
# DOSSIER GENERATOR
# ═══════════════════════════════════════════════════════════
def generate_astrology_dossier(profile,include_d60=False,compact=False):
    lat,lon,tz_name=profile['lat'],profile['lon'],profile['tz']
    name,place_text=profile['name'],profile['place']
    prof_date=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    prof_time=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd_ut,dt_local,_=local_to_julian_day(prof_date,prof_time,tz_name)
    lagna_lon,_=get_lagna_and_cusps(jd_ut,lat,lon)
    placidus_cusps=get_placidus_cusps(jd_ut,lat,lon)
    planet_data={pn:get_planet_longitude_and_speed(jd_ut,pid) for pn,pid in PLANETS.items()}
    r_lon=get_rahu_longitude(jd_ut); k_lon=(r_lon+180.0)%360
    dasha_info=build_vimshottari_timeline(dt_local,planet_data["Moon"][0],datetime.now(ZoneInfo(tz_name)))
    panchanga=get_panchanga(planet_data["Sun"][0],planet_data["Moon"][0],dt_local)
    ls=sign_index_from_lon(lagna_lon); moon_sidx=sign_index_from_lon(planet_data["Moon"][0])
    mars_sidx=sign_index_from_lon(planet_data["Mars"][0])
    ll_chain=get_lagna_lord_chain(ls,planet_data,r_lon,k_lon)
    conjunctions=get_conjunctions(ls,planet_data,r_lon,k_lon)
    mutual_asp=get_mutual_aspects(ls,planet_data,r_lon,k_lon)
    graha_yuddha=detect_graha_yuddha(jd_ut,planet_data)
    f_ben,f_mal,yogak,f_neu=get_functional_planets(ls)
    manglik=check_manglik_dosha(ls,moon_sidx,mars_sidx)
    sade_sati=calculate_sade_sati(moon_sidx)
    ak,ak_deg,amk,amk_deg=get_chara_karakas(planet_data)
    yogas_present,yogas_absent=detect_yogas(ls,moon_sidx,planet_data,r_lon,k_lon)
    ad_table=get_antardasha_table(dasha_info)
    house_summary=get_house_strength_summary(ls,planet_data,r_lon,k_lon,placidus_cusps)
    lat_lbl=f"{abs(lat):.5f}{'N' if lat>=0 else 'S'}"; lon_lbl=f"{abs(lon):.5f}{'E' if lon>=0 else 'W'}"
    lines=[]
    lines.append(f"{'═'*58}\nKUNDLI DOSSIER — {name.upper()}")
    lines.append(f"System: Swiss Ephemeris | Lahiri Ayanamsa | Whole Sign + KP Placidus\n{'═'*58}")
    lines.append(f"\nBIRTH DATA:\nName: {name} | Place: {place_text}")
    lines.append(f"Time: {dt_local.strftime('%d %b %Y, %I:%M %p')} ({panchanga['weekday']})")
    lines.append(f"Coordinates: {lat_lbl}, {lon_lbl} | Timezone: {tz_name}")
    lines.append(f"Tithi: {panchanga['tithi']} | Yoga: {panchanga['yoga']} | Karana: {panchanga['karana']}")
    lines.append(f"\nLAGNA FOUNDATION:\nAscendant: {sign_name(ls)} {format_dms(lagna_lon%30)}")
    lines.append(f"Lagna Lord Chain: {ll_chain} | Manglik: {manglik}")
    lines.append(f"\nFUNCTIONAL PLANETS FOR {sign_name(ls).upper()} LAGNA (DO NOT override):")
    lines.append(f"  Yogakarakas: {', '.join(yogak) if yogak else 'None'}")
    lines.append(f"  Functional Benefics: {', '.join(f_ben) if f_ben else 'None'}")
    lines.append(f"  Functional Malefics: {', '.join(f_mal) if f_mal else 'None'}")
    lines.append(f"\nPLANETARY POSITIONS (D1 Rasi):")
    house_occupants={i:[] for i in range(1,13)}
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        plon,pspd=planet_data[pname]; sidx=sign_index_from_lon(plon); house=whole_sign_house(ls,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); avastha=get_baladi_avastha(plon); sl=get_kp_sub_lord(plon)
        asp={"Mars":"H4,H8,H7","Jupiter":"H5,H9,H7","Saturn":"H3,H7,H10","Rahu":"H5,H7,H9","Ketu":"H5,H7,H9"}.get(pname,f"H{((house+6)%12)+1}")
        house_occupants[house].append(pname); tags=[]
        if pspd<0 and pname not in ["Sun","Moon"]: tags.append("Retrograde")
        if pname in COMBUST_DEGREES:
            diff=min(abs(plon-planet_data["Sun"][0]),360-abs(plon-planet_data["Sun"][0]))
            if diff<=COMBUST_DEGREES[pname]: tags.append("Combust")
        if pname in DIGNITIES:
            if sidx==DIGNITIES[pname][0]: tags.append("Exalted")
            elif sidx==DIGNITIES[pname][1]: tags.append("Debilitated")
        if pname in OWN_SIGNS and sidx in OWN_SIGNS[pname]: tags.append("Own Sign")
        tag_str=f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pname}: H{house} {sign_name(sidx)} {format_dms(plon%30)}{tag_str} | Avastha:{avastha} | Nak:{nak}(NL:{nak_lord} SL:{sl} P:{pada}) | Asp:{asp}")
    for pname,plon in [("Rahu",r_lon),("Ketu",k_lon)]:
        sidx=sign_index_from_lon(plon); house=whole_sign_house(ls,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); sl=get_kp_sub_lord(plon); house_occupants[house].append(pname)
        lines.append(f"  {pname}: H{house} {sign_name(sidx)} {format_dms(plon%30)} [Retrograde] | Nak:{nak}(NL:{nak_lord} SL:{sl} P:{pada})")
    lines.append(f"\nPRE-COMPUTED CRITICAL FACTS (DO NOT re-derive):")
    lines.append(f"[Conjunctions]\n" + ("\n".join(f"  ✓ {c}" for c in conjunctions) if conjunctions else "  None"))
    lines.append(f"[Mutual Aspects]\n" + ("\n".join(f"  ↔ {m}" for m in mutual_asp) if mutual_asp else "  None"))
    lines.append("[Graha Yuddha — Planetary War]")
    if graha_yuddha:
        for winner,loser,deg in graha_yuddha:
            lines.append(f"  ⚔ {winner} vs {loser} (sep:{deg}°) — {winner} WINS (higher ecliptic latitude)")
            lines.append(f"    → {loser}'s significations suppressed. {winner}'s amplified.")
    else: lines.append("  No Graha Yuddha in this chart.")
    lines.append("[Neecha Bhanga]")
    nb_found=False
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        psidx=sign_index_from_lon(planet_data[pname][0])
        if pname in DIGNITIES and psidx==DIGNITIES[pname][1]:
            nb_found=True
            conds=check_neecha_bhanga(pname,ls,moon_sidx,planet_data,r_lon,k_lon)
            if conds:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NEECHA BHANGA APPLIES → treat as Raja Yoga.")
                for c in conds: lines.append(f"    ✓ {c}")
            else:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NO NEECHA BHANGA → genuinely weakened.")
    if not nb_found: lines.append("  No debilitated planets.")
    lines.append("[Yogas — PRESENT ✓]")
    for yn,yd in yogas_present: lines.append(f"  ✓ {yn}: {yd}")
    if not yogas_present: lines.append("  None detected.")
    lines.append("[Yogas — ABSENT ✗ — do NOT mention these]")
    for ya in yogas_absent: lines.append(f"  ✗ {ya}")
    lines.append(f"[Jaimini Karakas]\n  Atmakaraka: {ak} ({ak_deg:.2f}°) | Amatyakaraka: {amk} ({amk_deg:.2f}°)")
    lines.append(f"\nHOUSE STRENGTH SUMMARY (pre-computed, use directly):")
    for hs in house_summary: lines.append(f"  {hs}")
    lines.append(f"\nHOUSE RULERSHIP MAP:")
    for h in range(1,13):
        h_sidx=(ls+h-1)%12; h_lord=SIGN_LORDS_MAP[h_sidx]
        ll_house=get_planet_house(h_lord,ls,planet_data,r_lon,k_lon)
        occ=", ".join(house_occupants[h]) if house_occupants[h] else "Empty"
        lines.append(f"  H{h:02d}({sign_name(h_sidx)}): Lord={h_lord}(H{ll_house}) | {occ}")
    if not compact:
        lines.append(f"\nKP PLACIDUS CUSPS (for timing/event promise only):")
        for h in range(1,13):
            clon=placidus_cusps[h-1]; csidx=sign_index_from_lon(clon)
            _,cnl,_=nakshatra_info(clon); csl=get_kp_sub_lord(clon)
            lines.append(f"  H{h:02d}: {sign_name(csidx)} {format_dms(clon%30)} | NL:{cnl} | SL:{csl}")
    lines.append(f"\nDIVISIONAL CHARTS:")
    all_pn=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    d2,d3,d4,d7,d9,d10,d12,d60=[],[],[],[],[],[],[],[]
    for pn in all_pn:
        pl=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        d2.append(f"{pn}:{sign_name(d2_si(pl))}"); d3.append(f"{pn}:{sign_name(d3_si(pl))}")
        d4.append(f"{pn}:{sign_name(d4_si(pl))}"); d7.append(f"{pn}:{sign_name(d7_si(pl))}")
        d9.append(f"{pn}:{sign_name(d9_si(pl))}"); d10.append(f"{pn}:{sign_name(d10_si(pl))}")
        d12.append(f"{pn}:{sign_name(d12_si(pl))}")
        if include_d60: d60.append(f"{pn}:{sign_name(d60_si(pl))}")
    lines.append(f"  D9 Navamsa(Marriage): {', '.join(d9)}")
    lines.append(f"  D10 Dasamsa(Career):  {', '.join(d10)}")
    lines.append(f"  D2 Hora(Wealth):      {', '.join(d2)}")
    lines.append(f"  D3 Drekkana(Courage): {', '.join(d3)}")
    lines.append(f"  D4 Chaturt(Property): {', '.join(d4)}")
    lines.append(f"  D7 Saptam(Children):  {', '.join(d7)}")
    lines.append(f"  D12 Dwadam(Parents):  {', '.join(d12)}")
    if include_d60: lines.append(f"  D60 Shashtiamsa(Karma): {', '.join(d60)}")
    lines.append(f"\nVIMSHOTTARI DASHA:")
    lines.append(f"Birth Nakshatra: {dasha_info['birth_nakshatra']} | Balance: {dasha_info['balance_years']:.2f} yrs of {dasha_info['start_lord']}")
    lines.append(f"Current MD: {dasha_info['current_md']} ({dasha_info['md_start'].strftime('%b %Y')} → {dasha_info['md_end'].strftime('%b %Y')})")
    lines.append(f"Current AD: {dasha_info['current_ad']} ({dasha_info['ad_start'].strftime('%b %Y')} → {dasha_info['ad_end'].strftime('%b %Y')})")
    lines.append(f"Current PD: {dasha_info['current_pd']} ({dasha_info['pd_start'].strftime('%d %b %Y')} → {dasha_info['pd_end'].strftime('%d %b %Y')})")
    lines.append(f"\nFULL ANTARDASHA SEQUENCE IN {dasha_info['current_md'].upper()} MAHADASHA:")
    lines.append("(Use ONLY these exact dates — do NOT calculate independently)")
    for row in ad_table: lines.append(row)
    lines.append(f"\nCURRENT AFFLICTIONS:\nSade Sati: {sade_sati}")
    return "\n".join(lines)

def get_gochara_overlay(profile):
    """Live transit vs natal chart overlay."""
    dt_now=datetime.now(ZoneInfo("UTC"))
    jd_now=swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    prof_date=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    prof_time=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd_natal,dt_local,_=local_to_julian_day(prof_date,prof_time,profile['tz'])
    lagna_lon,_=get_lagna_and_cusps(jd_natal,profile['lat'],profile['lon'])
    natal_data={pn:get_planet_longitude_and_speed(jd_natal,pid) for pn,pid in PLANETS.items()}
    natal_r=get_rahu_longitude(jd_natal)
    transit_data={pn:get_planet_longitude_and_speed(jd_now,pid) for pn,pid in PLANETS.items()}
    transit_r=get_rahu_longitude(jd_now)
    ls=sign_index_from_lon(lagna_lon)
    lines=["NATAL CHART (birth positions):"]
    for pn in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        nl=get_planet_lon_helper(pn,natal_data,natal_r,(natal_r+180)%360)
        nh=whole_sign_house(ls,sign_index_from_lon(nl))
        lines.append(f"  Natal {pn}: {sign_name(sign_index_from_lon(nl))} H{nh}")
    lines.append(f"\nLIVE TRANSIT POSITIONS ({dt_now.strftime('%d %b %Y')}):")
    for pn in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        tl=get_planet_lon_helper(pn,transit_data,transit_r,(transit_r+180)%360)
        nl=get_planet_lon_helper(pn,natal_data,natal_r,(natal_r+180)%360)
        th=whole_sign_house(ls,sign_index_from_lon(tl))
        nh=whole_sign_house(ls,sign_index_from_lon(nl))
        diff_houses=((th-nh)%12)
        lines.append(f"  Transit {pn}: {sign_name(sign_index_from_lon(tl))} H{th} (was H{nh} at birth, {diff_houses} houses moved)")
    lines.append(f"  Transit Rahu: {sign_name(sign_index_from_lon(transit_r))} H{whole_sign_house(ls,sign_index_from_lon(transit_r))}")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
# GUARDRAILS
# ═══════════════════════════════════════════════════════════
GUARDRAILS = f"""<instructions>
<role>
You are an elite Vedic astrologer fully trained in both Parashari and KP systems.
All values in the chart data below are PRE-COMPUTED by Swiss Ephemeris. Your role is
INTERPRETATION ONLY — never recalculate anything.
</role>

<primary_knowledge_base>
Your interpretive rules, definitions, and logic MUST come from these PDFs:
1. {PDF_HTRH1}
2. {PDF_HTRH2}
These are your absolute master references. External logic that contradicts them is forbidden.
Read them carefully before interpreting ANYTHING.
</primary_knowledge_base>

<two_layer_method>
LAYER 1 — PARASHARI ("What & Why"):
  Use D1 chart, house lords, yogas, divisional charts for character and karmic blueprint.
LAYER 2 — KP ("Whether & When"):
  Use the HOUSE STRENGTH SUMMARY and Antardasha Table for event promise and timing.
Synthesis rule: State Parashari finding first, then confirm/qualify with KP.
If they conflict, note it explicitly and lean toward KP for timing questions.
</two_layer_method>

<absolute_laws>
1. DATA IS IMMUTABLE: All positions, lords, Sub-Lords, verdicts, and Dasha dates are locked.
   DO NOT re-derive or recalculate anything.
2. FUNCTIONAL PLANETS: Use exactly as pre-classified. Do not reclassify any planet.
3. GRAHA YUDDHA: If a planet LOST — its significations are suppressed. If it WON — amplified.
   Never ignore this.
4. CONJUNCTIONS: Only use the pre-listed conjunctions. Do not infer new ones.
5. NEECHA BHANGA: APPLIES → treat as Raja Yoga quality. DOES NOT APPLY → genuinely weak.
6. YOGAS: Reference ONLY ✓ PRESENT yogas. Never mention ✗ ABSENT yogas.
7. DASHA DATES: Use ONLY the Antardasha Table. Never calculate independently.
8. HOUSE STRENGTH SUMMARY: Use those verdicts directly — they are pre-computed.
9. PROVE EVERY CLAIM: Format: "Saturn [Exalted, H7], 7th cusp SL, signifies H2+H7+H11, confirming marriage promise..."
10. NO GENERIC STATEMENTS: Every prediction must cite specific chart data as evidence.
</absolute_laws>
</instructions>"""

# ═══════════════════════════════════════════════════════════
# PROMPT BUILDERS (XML tagged)
# ═══════════════════════════════════════════════════════════
def build_deep_analysis_prompt(dossier):
    return f"""{GUARDRAILS}

<mission>
Deliver a complete, deeply insightful life reading. Each section MUST cite specific data from the chart.

## 1. Core Identity & Lagna
   DATA: Ascendant, Lagna Lord Chain, Functional Planets, H1 occupants.
   PARASHARI: Personality, constitution, life approach.
   KP: H1 cusp Sub-Lord and what its significations reveal.

## 2. Mind & Emotional World
   DATA: Moon (sign, house, nakshatra, Avastha, Sade Sati).
   Note Moon Avastha quality directly. If Sade Sati ACTIVE, describe the phase's practical impact.

## 3. Career & Profession
   DATA: H10 sign/lord/occupants, D10, Amatyakaraka, HOUSE STRENGTH SUMMARY H10.
   PARASHARI: Best professions and trajectory. KP: Apply H10 verdict exactly.

## 4. Wealth & Finances
   DATA: H2+H11 lords, D2 Hora, HOUSE STRENGTH SUMMARY H2+H11, PRESENT Dhana Yogas only.

## 5. Relationships & Marriage
   DATA: H7 lord/sign, D9 Navamsa H7, HOUSE STRENGTH SUMMARY H7 (use verdict exactly).
   PARASHARI: Spouse nature from D1+D9. KP: Apply Marriage Verdict and explain timing.

## 6. Health & Longevity
   DATA: H1, H6, H8 lords/occupants. Combust or debilitated planets post-Neecha Bhanga check.
   Note any GRAHA YUDDHA losers — their health significations are suppressed.

## 7. Current Dasha Phase
   DATA: Full Antardasha Table, Sade Sati, current MD/AD/PD.
   Analyse current combination. Identify next 2-3 sub-period shifts using ONLY the table.
   DO NOT generate new dates.

## 8. Practical Remedies
   ONLY for: Debilitated planets WITHOUT Neecha Bhanga, Combust planets, or Graha Yuddha losers.
   No remedies for strong planets.
</mission>

<user_chart_data>
{dossier}
</user_chart_data>"""

def build_matchmaking_prompt(dos_a,dos_b,koota,manglik_canc):
    return f"""{GUARDRAILS}

<mission>
Definitive compatibility analysis. Follow these sections exactly:

## 1. Ashta Koota Guna Milan
   CRITICAL: Do NOT recalculate. Use this pre-computed result exactly:
   {koota}
   Explain the practical meaning. For any Koota scoring 0, explain the specific challenge.

## 2. Manglik Dosha
   Pre-computed verdict: {manglik_canc}
   If cancelled, confirm no remedies needed for this.

## 3. Parashari Compatibility (D1 + D9)
   Compare 7th house lords, signs, D9 charts. Check Lagna lord friendship/enmity.

## 4. KP Marriage Promise & Timing (Both)
   Apply each person's H7 HOUSE STRENGTH SUMMARY verdict.
   Use ONLY their Antardasha Tables for timing.

## 5. Long-Term Harmony & Friction
   Use Gana, Graha Maitri, Bhakoot scores to identify temperament differences.

## 6. Final Verdict
   Score out of 10 with specific evidence. List only genuinely needed remedies.
</mission>

<person_1_chart>
{dos_a}
</person_1_chart>

<person_2_chart>
{dos_b}
</person_2_chart>"""

def build_comparison_prompt(profiles_dossiers,criteria):
    profile_sections="\n\n".join(f"<profile_{i+1}_chart>\n{dossier}\n</profile_{i+1}_chart>" for i,(name,dossier) in enumerate(profiles_dossiers))
    criteria_str="\n".join(f"  - {c}" for c in criteria)
    return f"""{GUARDRAILS}

<mission>
Compare the following individuals on these parameters:
{criteria_str}

Rules:
1. Rank ALL individuals per parameter, highest to lowest.
2. Every rank requires specific chart evidence (planet, house, dignity, yoga, or KP verdict).
3. Parashari for character/potential parameters. KP+HOUSE STRENGTH SUMMARY for event-based.
4. NEVER mention ABSENT yogas.
5. State final ranking as a numbered list then explain.
</mission>

{profile_sections}"""

def build_prashna_prompt(question,dossier):
    return f"""{GUARDRAILS}

<mission>
PRASHNA (Horary) reading — cast for this exact moment, for this question ONLY.

QUESTION: "{question}"

PRASHNA RULES:
1. Lagna and its lord = the querent.
2. Relevant house by question:
   Career/Job=H10 | Marriage=H7 | Money=H2,H11 | Health=H1,H6 | Children=H5
   Property=H4 | Travel/Foreign=H9,H12 | Education=H4,H5 | Enemies/Legal=H6,H7
3. PARASHARI: Strong relevant house lord → Favourable. Weak (debilitated, combust, dusthana) → Delay/denial.
4. KP: Apply the HOUSE STRENGTH SUMMARY verdict for the relevant house.
5. Moon's nakshatra provides timing context.
6. MANDATORY FINAL LINE: "VERDICT: [Yes / No / Delayed] — [one sentence]"
</mission>

<prashna_chart_data>
{dossier}
</prashna_chart_data>"""

def build_transit_prompt(dossier,gochara_overlay):
    return f"""{GUARDRAILS}

<mission>
GOCHARA (Live Transit) Analysis — how today's planetary positions activate the natal chart.

For each transiting planet, explain:
1. Which natal house it currently transits
2. How this activates or suppresses the natal house themes
3. Whether the current transit supports or challenges the running Dasha period
4. Key opportunities or cautions for the next 4-6 weeks

Use the PARASHARI layer for house themes and the KP layer (Antardasha Table) for timing alignment.
Focus on practical, actionable insights the person can use today.
</mission>

<natal_and_transit_data>
{gochara_overlay}

FULL NATAL DOSSIER:
{dossier}
</natal_and_transit_data>"""

def build_raw_prompt(dossier):
    return f"""<instructions>
This is a complete, pre-computed Vedic birth chart. All values are mathematically locked.

Your rules and interpretations MUST come from:
1. {PDF_HTRH1}
2. {PDF_HTRH2}

Do NOT recalculate any values. Ask me what you want to know about this chart.
</instructions>

<user_chart_data>
{dossier}
</user_chart_data>"""

def build_tarot_prompt(question,cards,states,mode="General Guidance"):
    TAROT_MODES={"General Guidance":{"roles":["Situation / Past","Challenge / Present","Advice / Future"],
        "instruction":"General life overview — where they are, what blocks them, best path forward."},
     "Love & Dynamics":{"roles":["Your Energy","Their Energy","The Connection / Outcome"],
        "instruction":"Read through the lens of a relationship or emotional dynamic."},
     "Decision / Two Paths":{"roles":["Path A","Path B","Hidden Factor / Recommendation"],
        "instruction":"Contrast the two paths. Card 3 is the deciding weight or hidden truth."}}
    cfg=TAROT_MODES.get(mode,TAROT_MODES["General Guidance"])
    roles=cfg["roles"]
    cards_str="\n".join(f"  {i+1}. {roles[i]}: {cards[i]} ({states[i]})" for i in range(len(cards)))
    return f"""<instructions>
You are an expert, intuitive Tarot Reader.

PRIMARY KNOWLEDGE BASE (MANDATORY — read before interpreting):
Your card meanings, symbolism, and interpretive logic MUST come from:
  {PDF_TGUIDE}
Do NOT use external knowledge that contradicts this guide.

INTERPRETATION RULES:
1. SYNERGY: Analyse card-to-card interplay, elemental dignities, and Major Arcana weight. Never read cards in isolation.
2. REVERSED: If a card is Reversed, interpret its energy as blocked, internalised, or delayed.
3. TONE: Confident but not fatalistic. Use "suggests", "points to", "leans toward".
4. DO NOT invent meanings not supported by the guide.
</instructions>

<reading_context>
Question: "{question}"
Spread: {mode}
Cards drawn (cryptographically randomised):
{cards_str}

Focus: {cfg['instruction']}

DELIVER (follow this format exactly):
- Overall Summary (2-3 sentences)
- Card-by-Card (each card's meaning in its specific spread position)
- Combined Message (how the three interact)
- Practical Action Step
- One-Line Takeaway
</reading_context>"""

def build_yesno_prompt(question,card,state):
    return f"""<instructions>
You are an expert Tarot Reader — Yes/No Oracle mode.

PRIMARY KNOWLEDGE BASE (MANDATORY):
  {PDF_TGUIDE}

YES/NO RULES:
- Upright cards generally lean Yes; Reversed lean No — but nuanced by card archetype.
- Major Arcana carry more weight than Minor Arcana.
- Court cards indicate people/situations — factor in narrative, not just polarity.
- DO NOT give a vague "it depends" answer. Commit to a clear verdict.
</instructions>

<reading_context>
Question: "{question}"
Card: {card} ({state})

DELIVER:
1. Clear verdict: YES / LIKELY YES / UNCLEAR / LIKELY NO / NO
2. Why — the card's specific energy in this context (2-3 sentences from the guide)
3. Condition — what must happen (or be avoided) for the outcome to manifest
4. One-Line Takeaway
</reading_context>"""

def build_celtic_cross_prompt(question,cards,states):
    cards_str="\n".join(f"  {CELTIC_CROSS_POSITIONS[i]}: {cards[i]} ({states[i]})" for i in range(10))
    return f"""<instructions>
You are an expert Tarot Reader — Celtic Cross spread.

PRIMARY KNOWLEDGE BASE (MANDATORY):
  {PDF_TGUIDE}

CELTIC CROSS RULES:
1. Cards 1 and 2 form the core tension — establish this first.
2. Cards 3-6 provide context (foundation, past, potential, near future).
3. Cards 7-10 form the Staff — internal journey, external influences, hopes/fears, outcome.
4. Look for patterns: suits clustering, Major Arcana count, recurring numbers.
5. Reversed cards = blocked or internalised energy of that position.
6. Synthesise ALL 10 cards into one coherent narrative — do not read them as 10 isolated cards.
</instructions>

<reading_context>
Question: "{question}"
Ten-card Celtic Cross (cryptographically randomised):
{cards_str}

DELIVER (follow exactly):
- Core Message (Cards 1+2 tension, 2-3 sentences)
- Position-by-position reading (all 10 cards)
- Patterns & Themes observed across the spread
- Overall Narrative
- Practical Guidance
- Final One-Line Takeaway
</reading_context>"""

def build_birth_card_prompt(card,dob):
    return f"""<instructions>
You are an expert Tarot Reader — Tarot Birth Card reading.

PRIMARY KNOWLEDGE BASE (MANDATORY):
  {PDF_TGUIDE}

This is a PERMANENT card — it never changes and represents the person's soul archetype and life theme.
Interpret it as a deep, lifelong energy — not a daily or situational reading.
</instructions>

<reading_context>
Date of Birth: {dob}
Tarot Birth Card: {card}

DELIVER:
1. The archetypal meaning and core symbolism of this card (from the guide)
2. How this archetype manifests as a lifelong theme and purpose
3. Core strengths this energy naturally brings
4. Core challenges and shadow aspects to be aware of
5. The soul's karmic lesson encoded in this card
6. A personal mantra for living this archetype with full power
</reading_context>"""

def build_daily_tarot_prompt(card,state):
    return f"""<instructions>
You are an expert Tarot Reader — Daily Guidance reading.

PRIMARY KNOWLEDGE BASE (MANDATORY):
  {PDF_TGUIDE}
</instructions>

<reading_context>
Today's card: {card} ({state})

Deliver a practical, insightful daily reading:
- What this card means today
- The energy available right now
- Best action to take
- What to be mindful of
- One-Line Mantra for Today
</reading_context>"""

def build_numerology_prompt(name,dob_str,lp,dest,soul,pers,astro_dossier=None,user_q="",system="Western (Pythagorean)"):
    is_vedic=system=="Indian/Vedic (Chaldean)"
    pdf_ref=f"  {PDF_NUMEV}" if is_vedic else f"  {PDF_NUMEW1}\n  {PDF_NUMEW2}"
    sys_name="Chaldean (Indian/Vedic)" if is_vedic else "Pythagorean (Western)"
    py=get_personal_year(dob_str); pm=get_personal_month(dob_str); pd=get_personal_day(dob_str)
    r1,r2,r3,r4=get_pinnacle_cycles(dob_str); y=int(dob_str.split('-')[0])
    cur_age=datetime.now(ZoneInfo("Asia/Kolkata")).year-y
    def which_p():
        for s,e,n,c in [r1,r2,r3,r4]:
            if s-y<=cur_age<e-y: return s,e,n,c
        return r4
    cp=which_p()
    instructions=f"""<instructions>
You are a Master Numerologist — {sys_name} system.

PRIMARY KNOWLEDGE BASE (MANDATORY — read before interpreting):
{pdf_ref}
These are your absolute references. Do NOT use logic that contradicts these guides.
Do NOT contradict them with external numerology knowledge.

CRITICAL: All core numbers below are PRE-COMPUTED and LOCKED.
DO NOT recalculate them from the name or date. Use them exactly as given.
</instructions>"""
    data=f"""<numerology_data>
Subject: {name.upper()} | DOB: {dob_str} | System: {sys_name}

LOCKED CORE NUMBERS:
  Life Path   : {lp}{' ★ Master Number' if lp in [11,22,33] else ''} — {PERSONAL_YEAR_MEANINGS.get(lp,'')}
  Destiny     : {dest}{' ★ Master Number' if dest in [11,22,33] else ''}
  Soul Urge   : {soul}{' ★ Master Number' if soul in [11,22,33] else ''}
  Personality : {pers}{' ★ Master Number' if pers in [11,22,33] else ''}

LOCKED TIMING NUMBERS:
  Personal Year  ({datetime.now(ZoneInfo('Asia/Kolkata')).year}): {py} — {PERSONAL_YEAR_MEANINGS.get(py,'')}
  Personal Month (this month): {pm}
  Personal Day   (today): {pd}

PINNACLE CYCLES:
  Pinnacle 1 (Ages {r1[0]-y}–{r1[1]-y}): Number {r1[2]} | Challenge: {r1[3]}
  Pinnacle 2 (Ages {r2[0]-y}–{r2[1]-y}): Number {r2[2]} | Challenge: {r2[3]}
  Pinnacle 3 (Ages {r3[0]-y}–{r3[1]-y}): Number {r3[2]} | Challenge: {r3[3]}
  Pinnacle 4 (Ages {r4[0]-y}+):           Number {r4[2]} | Challenge: {r4[3]}
  CURRENT PINNACLE: Number {cp[2]} | Challenge: {cp[3]}
  (Challenge number = the specific obstacle/lesson of this life phase)
</numerology_data>"""
    if astro_dossier:
        cross=f"""<astro_numerology_synthesis>
Also use: {PDF_HTRH1} and {PDF_HTRH2} for the astrological layer.
EXPLICIT SYNTHESIS REQUIRED:
  - Life Path {lp} vs Lagna lord: reinforce or contradict?
  - Destiny {dest} vs Amatyakaraka: career numbers aligned?
  - Soul Urge {soul} vs Moon sign+nakshatra: inner drive matches emotional blueprint?
  - Personal Year {py} vs current Mahadasha: double-confirm or tension?
State explicitly where both systems AGREE (high confidence) and where they DIVERGE.

<natal_chart>
{astro_dossier}
</natal_chart>
</astro_numerology_synthesis>"""
    else: cross=""
    if user_q and user_q.strip():
        mission=f'<mission>Answer this question directly: "{user_q}"\nUse both numbers and (if provided) chart data as evidence.</mission>'
    else:
        mission=f"""<mission>
Deliver a complete report:
1. Life Path — Core purpose and life journey
2. Destiny — What they are meant to accomplish
3. Soul Urge — Inner desires and motivations
4. Personality — How the world sees them
5. Personal Year {py} Forecast — What this year brings
6. Active Pinnacle ({cp[2]}) + Active Challenge ({cp[3]}) — Theme and obstacle right now
{'7. Astro-Numerology Synthesis — Where both systems agree and diverge' if astro_dossier else ''}
</mission>"""
    return f"{instructions}\n\n{data}\n\n{cross}\n\n{mission}"

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
def inject_nebula_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Base ── */
html,body,.stApp{background:radial-gradient(circle at 15% 50%,#1a0f2e,#0c0814 60%,#050308 100%)!important;font-family:'Inter',sans-serif!important;color:#e2e0ec!important}
#MainMenu,footer,[data-testid="stHeader"]{visibility:hidden!important;height:0!important}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:#fff}
.block-container{padding:1rem 1.25rem 5rem!important;max-width:960px!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,0.03)!important;backdrop-filter:blur(12px)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:16px!important;box-shadow:0 8px 32px rgba(0,0,0,0.3)!important}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div,.stDateInput>div>div>input,.stTextArea>div>div>textarea{background:rgba(255,255,255,0.04)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:10px!important;color:#eceaf4!important}
div[data-testid="stButton"]>button{border-radius:10px!important;font-weight:600!important;transition:all 0.3s ease!important;border:1px solid rgba(255,255,255,0.1)!important;font-family:'Inter',sans-serif!important}
div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,rgba(144,98,222,0.8),rgba(205,140,80,0.8))!important;border:none!important;color:#fff!important}
div[data-testid="stButton"]>button[kind="primary"]:hover{transform:translateY(-2px)!important;box-shadow:0 8px 20px rgba(144,98,222,0.4)!important}
div[data-testid="stButton"]>button:not([kind="primary"]){background:rgba(255,255,255,0.05)!important;color:#fff!important}
div[data-testid="stButton"]>button:not([kind="primary"]):hover{background:rgba(255,255,255,0.1)!important}
.stLinkButton>a{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:10px!important;color:#fff!important;transition:all 0.3s!important}
.stLinkButton>a:hover{background:rgba(255,255,255,0.1)!important}
[data-testid="stExpander"]{border:1px solid rgba(255,255,255,0.1)!important;border-radius:12px!important;background:rgba(0,0,0,0.2)!important}
.stCodeBlock{border-radius:12px!important;border:1px solid rgba(255,255,255,0.1)!important;max-height:300px!important;overflow-y:auto!important}
[data-testid="stSidebar"]{background:rgba(5,3,15,0.98)!important;border-right:1px solid rgba(144,98,222,0.25)!important}

/* ── Weather widget ── */
.weather-widget{text-align:center;padding:1.5rem;border-radius:16px;background:linear-gradient(180deg,rgba(205,140,80,0.1),rgba(144,98,222,0.05));border:1px solid rgba(205,140,80,0.2)}
.w-main{font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;color:#fff;margin:.3rem 0;text-shadow:0 0 20px rgba(205,140,80,0.4)}

/* ── Feature cards ── */
.feat-card{border-radius:14px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.035);padding:1rem;position:relative;overflow:hidden;transition:all .2s}
.feat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent)}
.feat-card:hover{border-color:rgba(255,255,255,0.14);transform:translateY(-2px)}
.feat-icon{font-size:1.6rem;display:block;margin-bottom:.4rem}
.feat-title{font-family:'Space Grotesk',sans-serif;font-size:.9rem;font-weight:600;color:#fff;margin:0 0 .25rem}
.feat-desc{font-size:.76rem;color:rgba(190,185,210,0.58);margin:0;line-height:1.5}

/* ── Saved profile cards ── */
.prof-card{background:rgba(255,255,255,0.03);border-radius:14px;padding:1rem;margin-bottom:.5rem;position:relative;overflow:hidden}
.prof-card-def{border:1px solid rgba(205,140,80,0.45)}
.prof-card-norm{border:1px solid rgba(255,255,255,0.07)}
.prof-name{font-weight:600;font-size:1rem;color:#fff;margin:0 0 .15rem}
.prof-sub{font-size:.78rem;color:rgba(190,185,210,.55);margin:0}
.def-badge{display:inline-block;background:rgba(205,140,80,0.18);border:1px solid rgba(205,140,80,0.4);color:#d4944a;font-size:.66rem;padding:1px 7px;border-radius:10px;font-weight:600;margin-bottom:.35rem;animation:badge-pulse 3s ease-in-out infinite}
@keyframes badge-pulse{0%,100%{box-shadow:0 0 0 0 rgba(205,140,80,0)}50%{box-shadow:0 0 8px 2px rgba(205,140,80,0.25)}}

/* ── Banner for default profile on dashboard ── */
.prof-banner{background:linear-gradient(135deg,rgba(144,98,222,0.15),rgba(205,140,80,0.08));border:1px solid rgba(144,98,222,0.3);border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1.5rem}

/* ── Bottom navigation (mobile only) ── */
.bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;z-index:9999;background:rgba(8,4,20,0.97);backdrop-filter:blur(20px);border-top:1px solid rgba(144,98,222,0.3);padding:6px 0 max(env(safe-area-inset-bottom),6px)}
.bottom-nav-inner{display:flex;justify-content:space-around;align-items:center;max-width:640px;margin:0 auto}
.bnav-btn{display:flex;flex-direction:column;align-items:center;gap:2px;padding:4px 8px;background:none;border:none;cursor:pointer;color:rgba(200,195,220,0.5);font-family:'Inter',sans-serif;font-size:.65rem;font-weight:500;min-width:52px;border-radius:8px;transition:all .2s;text-decoration:none}
.bnav-btn.active,.bnav-btn:hover{color:#c090e0;background:rgba(144,98,222,0.12)}
.bnav-icon{font-size:1.35rem;line-height:1}
@media(max-width:768px){.bottom-nav{display:block}.block-container{padding-bottom:6rem!important}}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# COPY BUTTON (Clipboard API)
# ═══════════════════════════════════════════════════════════
def render_copy_button(text_to_copy, label="✨ Copy Prompt to Clipboard"):
    b64=base64.b64encode(text_to_copy.encode("utf-8")).decode("utf-8")
    uid=secrets.token_hex(4)
    components.html(f"""
<div style="width:100%;padding:0 2px;">
<button id="cb_{uid}" onclick="doCopy_{uid}()" style="background:linear-gradient(135deg,rgba(144,98,222,0.85),rgba(205,140,80,0.85));border:1px solid rgba(255,255,255,0.2);color:white;padding:14px 20px;font-size:15px;cursor:pointer;border-radius:12px;font-weight:600;width:100%;box-shadow:0 4px 15px rgba(0,0,0,0.3);font-family:'Inter',sans-serif;transition:all .3s">{label}</button>
</div>
<script>
async function doCopy_{uid}(){{
  const btn=document.getElementById("cb_{uid}");
  const text=decodeURIComponent(escape(atob('{b64}')));
  try{{await navigator.clipboard.writeText(text);}}
  catch(e){{const el=document.createElement('textarea');el.value=text;el.style.cssText='position:fixed;opacity:0';document.body.appendChild(el);el.select();document.execCommand('copy');document.body.removeChild(el);}}
  btn.innerHTML="✅ Copied!";btn.style.background="linear-gradient(135deg,rgba(46,184,134,0.85),rgba(26,138,98,0.85))";
  setTimeout(()=>{{btn.innerHTML="{label}";btn.style.background="linear-gradient(135deg,rgba(144,98,222,0.85),rgba(205,140,80,0.85))"}},3000);
}}
</script>""", height=56)

def render_post_generation(prompt):
    st.markdown("---")
    st.markdown("""<div style='background:rgba(144,98,222,0.1);border:1px solid rgba(144,98,222,0.3);border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;'>
<h4 style='margin:0 0 .5rem;color:#fff;'>💡 How to use this</h4>
<p style='color:#beb9cd;font-size:.9rem;margin:0;'>1. Click <b>Copy</b> below &nbsp;→&nbsp; 2. Open an AI &nbsp;→&nbsp; 3. <b>Paste & Send</b></p></div>""",
                unsafe_allow_html=True)
    render_copy_button(prompt)
    st.markdown("<br>", unsafe_allow_html=True)
    a1,a2,a3=st.columns(3)
    a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
    a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)
    a3.link_button("🚀 Grok","https://grok.com/",use_container_width=True)
    with st.expander("📄 View Raw Prompt",expanded=False):
        st.code(prompt,language="text")

# ═══════════════════════════════════════════════════════════
# BOTTOM NAV (mobile, functional via query params)
# ═══════════════════════════════════════════════════════════
def render_bottom_nav():
    items=[("🌌","Home","Dashboard"),("🔮","Oracle","The Oracle"),
           ("🃏","Tarot","Mystic Tarot"),("🔢","Numbers","Numerology"),("👤","Profiles","Saved Profiles")]
    nav_html='<div class="bottom-nav"><div class="bottom-nav-inner">'
    for icon,label,page in items:
        active="active" if st.session_state.nav_page==page else ""
        nav_html+=f'<a class="bnav-btn {active}" href="?p={page}" title="{label}"><span class="bnav-icon">{icon}</span><span>{label}</span></a>'
    nav_html+='</div></div>'
    st.markdown(nav_html,unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAROT CARD OVERLAY — completely rewritten with img tags
# ═══════════════════════════════════════════════════════════
def render_tarot_overlay(cards, states, layout="three"):
    """
    layout: 'one' | 'three' | 'ten'
    Uses actual <img> tags + GSAP 3D flip. Works every draw.
    """
    back_url=f"{TAROT_BASE}tarotrear.png"
    vid_desk=f"{TAROT_BASE}tarotvid.mp4"
    vid_mob=f"{TAROT_BASE}tarotvideo.mp4"
    n=len(cards)

    # Card HTML blocks
    card_blocks=""
    for i,(card,state) in enumerate(zip(cards,states)):
        front_url=f"{TAROT_BASE}{get_filename(card)}"
        rev=""
        if state=="Reversed": rev='style="transform:scaleY(-1)"'
        card_blocks+=f"""
<div class="tcw w{i}" data-idx="{i}">
  <div class="tc3d c{i}">
    <img class="tcback" src="{back_url}" alt="back">
    <img class="tcfront" src="{front_url}" alt="{card}" {rev}>
  </div>
</div>"""

    # Layout-specific CSS
    if layout=="one":
        container_css="""
.card-row{display:flex;justify-content:center;align-items:center;gap:0;}
.tcw{width:28%;max-width:130px;}"""
        bottom_pct="10%"; bottom_mob="12%"; card_pct="28%"; card_mob="32%"
    elif layout=="three":
        container_css="""
.card-row{display:flex;justify-content:center;align-items:center;gap:4%;}
.tcw{width:24%;max-width:115px;}"""
        bottom_pct="9%"; bottom_mob="11%"; card_pct="24%"; card_mob="27%"
    else:  # ten — 2 rows of 5
        container_css="""
.card-row{display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:repeat(2,auto);gap:2% 2%;width:90%;}
.tcw{width:100%;}"""
        bottom_pct="8%"; bottom_mob="10%"; card_pct="100%"; card_mob="100%"

    uid=secrets.token_hex(4)
    # GSAP targets: pass DOM element arrays from parent document, not string selectors
    # (st.markdown strips <script> tags; scripts must go in components.html)
    fade_parts="".join(
        f"var el{i}=doc.querySelectorAll('.w{i}_{uid}');"
        f"if(el{i}.length)gsap.fromTo(el{i},{{opacity:0,y:30}},{{opacity:1,y:0,duration:.8,delay:{0.2+i*0.35:.2f},ease:'power3.out'}});"
        for i in range(n)
    )
    flip_parts="".join(
        f"var ci{i}=doc.querySelectorAll('.c{i}_{uid}');"
        f"if(ci{i}.length)gsap.to(ci{i},{{rotationY:180,duration:.75,delay:{1.0+i*0.45:.2f},ease:'back.out(1.5)',transformOrigin:'center center'}});"
        for i in range(n)
    )
    scroll_delay=round(1.0+n*0.45+0.5,2)

    # Re-generate card_blocks with uid-scoped classes so multiple draws don't clash
    card_blocks_uid=""
    for i,(card,state) in enumerate(zip(cards,states)):
        front_url=f"{TAROT_BASE}{get_filename(card)}"
        rev='style="transform:scaleY(-1)"' if state=="Reversed" else ""
        card_blocks_uid+=f"""
<div class="tcw w{i}_{uid}">
  <div class="tc3d c{i}_{uid}">
    <img class="tcback" src="{back_url}" alt="back">
    <img class="tcfront" src="{front_url}" alt="{card}" {rev}>
  </div>
</div>"""

    html=f"""<style>
.tarot-stage-{uid}{{position:relative;width:100%;max-width:560px;margin:0 auto 1.5rem;border-radius:16px;overflow:hidden;box-shadow:0 10px 35px rgba(0,0,0,.6);background:linear-gradient(45deg,#1a0f2e,#0c0814)}}
.vid-d-{uid}{{width:100%;display:block;object-fit:cover;opacity:.82;aspect-ratio:1440/1678}}
.vid-m-{uid}{{display:none;width:100%;object-fit:cover;opacity:.82;aspect-ratio:24/41}}
.card-container-{uid}{{position:absolute;bottom:{bottom_pct};width:100%;display:flex;justify-content:center;align-items:flex-end}}
{container_css}
.tcw{{aspect-ratio:2/3;opacity:0}}
.tc3d{{width:100%;height:100%;position:relative;transform-style:preserve-3d;transform:rotateY(0deg)}}
.tcback,.tcfront{{position:absolute;top:0;left:0;width:100%;height:100%;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:7px;box-shadow:0 4px 14px rgba(0,0,0,.8);object-fit:cover}}
.tcback{{border:1.5px solid rgba(205,140,80,.5)}}
.tcfront{{transform:rotateY(180deg);border:1.5px solid rgba(205,140,80,.85)}}
.scroll-txt-{uid}{{position:absolute;bottom:2.5%;width:100%;text-align:center;color:rgba(255,255,255,.9);font-family:'Space Grotesk',sans-serif;font-size:.88rem;letter-spacing:1px;opacity:0;text-shadow:0 2px 6px rgba(0,0,0,.9);pointer-events:none}}
@media(max-width:768px){{.vid-d-{uid}{{display:none}}.vid-m-{uid}{{display:block}}.card-container-{uid}{{bottom:{bottom_mob}}}}}
</style>
<div class="tarot-stage-{uid}" id="ts_{uid}">
  <video class="vid-d-{uid}" autoplay loop muted playsinline><source src="{vid_desk}" type="video/mp4"></video>
  <video class="vid-m-{uid}" autoplay loop muted playsinline><source src="{vid_mob}" type="video/mp4"></video>
  <div class="card-container-{uid}"><div class="card-row">{card_blocks_uid}</div></div>
  <div class="scroll-txt-{uid}" id="sp_{uid}">✨ The cards have spoken. Scroll down for your reading. ✨</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

    # JS must go in components.html — st.markdown strips <script> tags entirely.
    # Pass DOM element arrays (not CSS selector strings) to GSAP so it targets
    # the parent document, not the components iframe.
    components.html(f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script>
(function(){{
  function runAnim(){{
    var doc=window.parent.document;
    if(!doc.querySelector('.w0_{uid}')){{ setTimeout(runAnim,250); return; }}
    {fade_parts}
    {flip_parts}
    var sp=doc.getElementById('sp_{uid}');
    if(sp) gsap.to(sp,{{opacity:1,duration:.8,delay:{scroll_delay}}});
  }}
  setTimeout(runAnim,300);
}})();
</script>""", height=0, width=0)

# ═══════════════════════════════════════════════════════════
# PROFILE FORM HELPERS
# ═══════════════════════════════════════════════════════════
def render_profile_form(key_prefix,show_d60=True,default_from_profile=None):
    """Render profile form. If default_from_profile is set, pre-fill with it."""
    if st.session_state.db:
        method=st.radio("Source",["Enter New Details","Saved Profile"],horizontal=True,
                        key=f"rad_{key_prefix}",label_visibility="collapsed")
    else: method="Enter New Details"
    dp,dp_idx=get_default_profile()
    with st.container(border=True):
        if method=="Enter New Details":
            pre=default_from_profile or dp  # auto-fill from default profile
            pt=datetime.strptime(pre['time'],"%H:%M").time() if pre else None
            pre_hr=pt.hour%12 or 12 if pt else 12; pre_mi=pt.minute if pt else 0
            pre_ampm=1 if pt and pt.hour>=12 else 0
            st.session_state[f"n_{key_prefix}"]=st.text_input("Name",value=pre['name'] if pre else "",key=f"wn_{key_prefix}")
            pre_date=date.fromisoformat(pre['date']) if pre else date(2000,1,1)
            st.session_state[f"d_{key_prefix}"]=st.date_input("Date of Birth",pre_date,key=f"wd_{key_prefix}")
            t1,t2,t3=st.columns(3)
            with t1: st.session_state[f"hr_{key_prefix}"]=st.number_input("Hour",1,12,pre_hr,key=f"whr_{key_prefix}")
            with t2: st.session_state[f"mi_{key_prefix}"]=st.number_input("Min",0,59,pre_mi,key=f"wmi_{key_prefix}")
            with t3: st.session_state[f"ampm_{key_prefix}"]=st.selectbox("AM/PM",["AM","PM"],index=pre_ampm,key=f"wa_{key_prefix}")
            pre_place=pre['place'] if pre and pre['place']!="Manual Coordinates" else ""
            u_place=st.text_input("Birth Place (City, Country)",value=pre_place,key=f"wp_{key_prefix}")
            st.session_state[f"p_{key_prefix}"]=u_place
            manual=st.checkbox("Enter coordinates manually",key=f"wman_{key_prefix}")
            st.session_state[f"man_{key_prefix}"]=manual
            if u_place.strip() and not manual:
                geo=geocode_place(u_place.strip())
                if geo: st.success(f"📍 {geo[2]}")
                else: st.warning("Not found — check spelling or use manual coordinates.")
            if manual:
                c1,c2,c3=st.columns(3)
                pre_lat=pre['lat'] if pre else 0.0; pre_lon=pre['lon'] if pre else 0.0; pre_tz=pre['tz'] if pre else "Asia/Kolkata"
                with c1: st.session_state[f"lat_{key_prefix}"]=st.number_input("Lat",value=float(pre_lat),format="%.4f",key=f"wlat_{key_prefix}")
                with c2: st.session_state[f"lon_{key_prefix}"]=st.number_input("Lon",value=float(pre_lon),format="%.4f",key=f"wlon_{key_prefix}")
                with c3: st.session_state[f"tz_{key_prefix}"]=st.text_input("Timezone",pre_tz,key=f"wtz_{key_prefix}")
            st.session_state[f"save_{key_prefix}"]=st.checkbox("Save to Saved Profiles",key=f"wsave_{key_prefix}")
            if show_d60: st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time is exact to the minute (enables D60 karma chart)",key=f"wd60_{key_prefix}")
            return {"type":"new","idx":key_prefix}
        else:
            opts_raw=sorted_profile_options()
            if not opts_raw: return {"type":"empty_saved","idx":key_prefix}
            labels=["— Select —"]+[f"{'⭐ ' if i==st.session_state.default_profile_idx else ''}{p['name']} ({format_date_ui(p['date'])})" for i,p in opts_raw]
            sel=st.selectbox("Select Profile",labels,key=f"sel_{key_prefix}",label_visibility="collapsed")
            if sel!="— Select —":
                _,p=opts_raw[labels.index(sel)-1]
                st.success(f"Loaded: **{p['name']}** 📍 {p['place'].split(',')[0]}")
                if show_d60: st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time exact",key=f"wd60_{key_prefix}")
                return {"type":"saved","data":p,"idx":key_prefix}
            return {"type":"empty_saved","idx":key_prefix}

def resolve_profile(item):
    i=item["idx"]; include_d60=st.session_state.get(f"d60_{i}",False)
    if item["type"]=="saved": return item["data"],include_d60
    if item["type"]=="empty_saved": st.error("Please select a valid profile."); st.stop()
    u_name=st.session_state.get(f"n_{i}","")
    if not u_name.strip(): st.error("Enter a name."); st.stop()
    hr=st.session_state.get(f"hr_{i}",12); mi=st.session_state.get(f"mi_{i}",0); am=st.session_state.get(f"ampm_{i}","AM")
    h24=(hr+12 if am=="PM" and hr!=12 else 0 if am=="AM" and hr==12 else hr)
    u_time=time(h24,mi); u_date=st.session_state.get(f"d_{i}",date(2000,1,1))
    is_manual=st.session_state.get(f"man_{i}",False)
    if is_manual:
        fl=st.session_state.get(f"lat_{i}",0.0); flon=st.session_state.get(f"lon_{i}",0.0); ftz=st.session_state.get(f"tz_{i}","")
        if fl==0.0 and flon==0.0: st.error("Enter valid coordinates."); st.stop()
        if not ftz.strip(): st.error("Enter a timezone."); st.stop()
        fp="Manual Coordinates"
    else:
        u_place=st.session_state.get(f"p_{i}","")
        if not u_place.strip(): st.error("Enter a birth place."); st.stop()
        geo=geocode_place(u_place.strip())
        if not geo: st.error(f"'{u_place}' not found."); st.stop()
        fl,flon,fp=geo; ftz=timezone_for_latlon(fl,flon)
        if not ftz: st.error("Timezone detection failed."); st.stop()
    prof={"name":u_name.strip(),"date":u_date.isoformat(),"time":u_time.strftime("%H:%M"),"place":fp,"lat":fl,"lon":flon,"tz":ftz}
    if st.session_state.get(f"save_{i}",False) and not is_duplicate_in_db(prof):
        st.session_state.db.append(prof); sync_db()
    return prof,include_d60

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;margin-bottom:1.5rem;font-size:1.3rem;'>🪐 Kundli AI</h2>",unsafe_allow_html=True)
        pages=[("🌌 Dashboard","Dashboard"),("🔮 The Oracle","The Oracle"),("🃏 Mystic Tarot","Mystic Tarot"),
               ("🌟 Horoscopes","Horoscopes"),("🔢 Numerology","Numerology"),("📖 Saved Profiles","Saved Profiles")]
        for label,page in pages:
            kind="primary" if st.session_state.nav_page==page else "secondary"
            if st.button(label,use_container_width=True,type=kind,key=f"side_{page}"):
                st.session_state.nav_page=page
                # Close sidebar on mobile via JS
                components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
                st.rerun()
        dp,_=get_default_profile()
        if dp:
            st.markdown("---")
            st.markdown(f"<p style='font-size:.72rem;color:rgba(200,190,220,.5);margin:0'>⭐ My Profile</p><p style='font-size:.88rem;color:#e0d8f0;font-weight:600;margin:0'>{dp['name']}</p>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════
def show_dashboard():
    dp,dp_idx=get_default_profile()
    user_tz=dp['tz'] if dp else "Asia/Kolkata"
    today=get_local_today(user_tz)  # FIX: use user timezone

    if dp:
        st.markdown(f"""<div class="prof-banner">
<p style='font-size:.7rem;text-transform:uppercase;letter-spacing:1.5px;color:rgba(205,140,80,.7);margin:0 0 .25rem'>Welcome back</p>
<h2 style='margin:0 0 .15rem;font-size:1.4rem'>{dp['name']}</h2>
<p style='margin:0;font-size:.8rem;color:rgba(200,190,220,.55)'>📍 {dp['place'].split(',')[0]}</p>
</div>""",unsafe_allow_html=True)
    else:
        st.markdown("<h1>🌌 Cosmic Dashboard</h1>",unsafe_allow_html=True)
        st.info("💡 Go to **Saved Profiles** and set a ⭐ default profile to personalise your dashboard.")

    with st.spinner("Loading cosmic weather..."):
        cw=get_live_cosmic_weather()

    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown(f"""<div class="weather-widget">
<div style='font-size:.75rem;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.55)'>Moon Today</div>
<div class="w-main">{cw['moon_sign']} 🌙</div>
<div style='color:rgba(255,255,255,.75);font-size:.85rem'>Nakshatra: <b>{cw['nakshatra']}</b></div>
</div>""",unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.markdown(f"<h4 style='margin-top:0;font-size:.95rem'>🌟 {cw['nature']}</h4>",unsafe_allow_html=True)
            st.caption(cw['advice'])
            if cw['retrogrades']: st.warning(f"Retrograde: {', '.join(cw['retrogrades'])}")
            else: st.success("No planets retrograde.")
    with c3:
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0;font-size:.95rem'>📅 Vedic Calendar</h4>",unsafe_allow_html=True)
            st.write(f"**Tithi:** {cw['tithi']}")
            st.write(f"**Yoga:** {cw['yoga']}")
            st.write(f"**Sun in:** {cw['sun_sign']}")

    # Personal trackers
    if dp:
        st.markdown("---")
        st.markdown("### ⏳ Your Live Snapshot")
        try:
            d_val=date.fromisoformat(dp['date']); t_val=datetime.strptime(dp['time'],"%H:%M").time()
            jd,dt_local,_=local_to_julian_day(d_val,t_val,dp['tz'])
            moon_lon,_=get_planet_longitude_and_speed(jd,PLANETS["Moon"])
            dt_now=datetime.now(ZoneInfo(dp['tz']))
            di=build_vimshottari_timeline(dt_local,moon_lon,dt_now)
            ss=calculate_sade_sati(sign_index_from_lon(moon_lon))
            d1,d2,d3=st.columns(3)
            with d1:
                with st.container(border=True):
                    st.markdown("**🔴 Major Period**")
                    st.markdown(f"## {di['current_md']}")
                    st.caption(f"Until {di['md_end'].strftime('%b %Y')}")
                    st.caption("The dominant life season you're in.")
            with d2:
                with st.container(border=True):
                    st.markdown("**🟡 Sub Period**")
                    st.markdown(f"## {di['current_ad']}")
                    st.caption(f"Until {di['ad_end'].strftime('%b %Y')}")
                    st.caption("Colours events within the major period.")
            with d3:
                with st.container(border=True):
                    st.markdown("**🪐 Sade Sati**")
                    if "ACTIVE" in ss:
                        st.warning(ss.split(':')[0].replace("ACTIVE — ",""))
                        st.caption("Saturn 7.5-yr transit. Period of pressure & transformation.")
                    else:
                        st.success("Not Active")
                        st.caption("No Saturn pressure on your Moon currently.")
        except Exception as e:
            st.error(f"Could not load personal data: {e}")

    # Daily tarot
    st.markdown("---")
    st.markdown("### 🃏 Daily Tarot Card")
    with st.container(border=True):
        today_str=today.isoformat()  # FIX: use local today
        already=st.session_state.dash_tarot_date==today_str and st.session_state.dash_tarot_card
        dt1,dt2=st.columns([1,2])
        with dt1:
            if already:
                c=st.session_state.dash_tarot_card; s=st.session_state.dash_tarot_state
                rev_style="transform:rotate(180deg);" if s=="Reversed" else ""
                st.markdown(f"""<div style='text-align:center'>
<img src='{TAROT_BASE}{get_filename(c)}' style='width:110px;border-radius:8px;border:2px solid rgba(205,140,80,.8);{rev_style}'>
<p style='font-weight:600;margin:.4rem 0 0;font-size:.85rem'>{c}</p>
<p style='margin:0;font-size:.72rem;color:rgba(200,190,220,.55)'>{s}</p></div>""",unsafe_allow_html=True)
                st.caption("Come back tomorrow for a new card.")
            else:
                st.caption("Draw one card for today's energy and guidance.")
                if st.button("✨ Draw My Daily Card",use_container_width=True):
                    rng=secrets.SystemRandom()
                    st.session_state.dash_tarot_card=rng.choice(FULL_TAROT_DECK)
                    st.session_state.dash_tarot_state=rng.choice(["Upright","Reversed"])
                    st.session_state.dash_tarot_date=today_str; st.rerun()
        with dt2:
            if st.session_state.get('dash_tarot_card'):
                render_copy_button(build_daily_tarot_prompt(st.session_state.dash_tarot_card,st.session_state.dash_tarot_state),"Copy Daily Reading Prompt")
                a1,a2=st.columns(2)
                a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
                a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)

    # Feature cards
    st.markdown("---")
    st.markdown("### 🚀 What would you like to do?")
    tools=[
        ("🔮","linear-gradient(90deg,#4e28a0,#8050cc)","Full Life Reading","Complete life analysis — personality, career, wealth, marriage, timing.","The Oracle","Deep Personal Analysis"),
        ("✦","linear-gradient(90deg,#8e2050,#c85080)","Compatibility","Full Ashta Koota + Manglik + KP marriage analysis for two people.","The Oracle","Matchmaking / Compatibility"),
        ("🌍","linear-gradient(90deg,#1a5540,#28a870)","Live Transits","See how today's planets activate your birth chart right now.","The Oracle","Gochara / Live Transit"),
        ("⚖","linear-gradient(90deg,#185578,#2888b8)","Compare Charts","Rank multiple charts on wealth, luck, health, and custom traits.","The Oracle","Comparison (Multiple Profiles)"),
        ("🎯","linear-gradient(90deg,#6a3000,#c07020)","Ask a Question","Prashna horary chart. Get a Yes/No/Delayed answer to any specific question.","The Oracle","Prashna Kundli"),
        ("📋","linear-gradient(90deg,#3a3a3a,#6a6a6a)","Raw Chart Data","Get your full chart data. Paste into any AI and ask it anything.","The Oracle","Raw Data Only"),
        ("🃏","linear-gradient(90deg,#185578,#2888b8)","3-Card Tarot","Ask a question, draw three cards, get a full reading prompt.","Mystic Tarot",""),
        ("☯","linear-gradient(90deg,#2a1060,#6030b0)","Yes / No Oracle","Single card. Clear answer.","Mystic Tarot",""),
        ("🔢","linear-gradient(90deg,#1a6040,#28a870)","Numerology Report","Core numbers, Personal Year, Pinnacles, and optional astro cross-reference.","Numerology",""),
        ("🌟","linear-gradient(90deg,#603018,#a85028)","Horoscope","Daily, monthly, and yearly — Western or Vedic.","Horoscopes",""),
    ]
    cols=st.columns(2)
    for i,tool in enumerate(tools):
        icon,grad,title,desc,target,mission=tool
        with cols[i%2]:
            st.markdown(f"""<div class="feat-card" style="--accent:{grad};margin-bottom:.6rem">
<span class="feat-icon">{icon}</span>
<p class="feat-title">{title}</p>
<p class="feat-desc">{desc}</p></div>""",unsafe_allow_html=True)
            if st.button(f"Open →",key=f"feat_{i}",use_container_width=True):
                if mission: st.session_state.active_mission=mission
                st.session_state.nav_page=target; st.rerun()

    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# ORACLE
# ═══════════════════════════════════════════════════════════
def show_oracle():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🔮 The Oracle</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6)'>Mathematically locked AI prompts from Swiss Ephemeris precision.</p>",unsafe_allow_html=True)
    missions={"Deep Personal Analysis":"🔮 Full Life Reading","Matchmaking / Compatibility":"✦ Compatibility Match",
              "Gochara / Live Transit":"🌍 Live Transit Analysis","Comparison (Multiple Profiles)":"⚖ Compare Profiles",
              "Prashna Kundli":"🎯 Ask a Question","Raw Data Only":"📋 Raw Chart Data"}
    descs={"Deep Personal Analysis":"Complete reading — personality, career, wealth, marriage, timing.",
           "Matchmaking / Compatibility":"Ashta Koota + Manglik + KP marriage promise.",
           "Gochara / Live Transit":"How today's planets activate your natal chart right now.",
           "Comparison (Multiple Profiles)":"Rank multiple people with planetary evidence.",
           "Prashna Kundli":"Ask a specific question. Get Yes/No/Delayed.",
           "Raw Data Only":"Full chart data. Paste into any AI and ask anything."}
    cur=st.session_state.active_mission if st.session_state.active_mission in missions else "Deep Personal Analysis"
    cur_label=missions.get(cur,"🔮 Full Life Reading")
    sel_label=st.selectbox("Select Tool",list(missions.values()),index=list(missions.values()).index(cur_label),label_visibility="collapsed")
    mid=[k for k,v in missions.items() if v==sel_label][0]
    st.session_state.active_mission=mid
    st.markdown(f"<p style='color:rgba(190,185,210,.6);font-size:.88rem;margin-bottom:1.5rem'>{descs[mid]}</p><hr>",unsafe_allow_html=True)
    _run_oracle(mid)

def _run_oracle(mission):
    dp,_=get_default_profile()
    if mission=="Prashna Kundli":
        question=st.text_area("Your question",placeholder="e.g. Will I get the job I applied for? When will I get married?")
        st.markdown("#### Your current location")
        c1,c2=st.columns(2)
        with c1:
            cur_place=st.text_input("City, Country",key="pr_place")
            if cur_place.strip() and not st.session_state.get("pr_man",False):
                geo=geocode_place(cur_place.strip())
                if geo: st.success(f"📍 {geo[2]}")
                else: st.warning("Not found.")
        with c2:
            pr_man=st.checkbox("Manual coordinates",key="pr_man")
            if pr_man:
                prl=st.number_input("Lat",value=30.76,format="%.4f",key="prl")
                prn=st.number_input("Lon",value=76.80,format="%.4f",key="prn")
                prt=st.text_input("Timezone","Asia/Kolkata",key="prt")
        if st.button("Generate Prashna Prompt",type="primary",use_container_width=True):
            if not question.strip(): st.error("Enter a question."); return
            if not pr_man:
                geo=geocode_place(cur_place.strip())
                if not geo: st.error("Location not found."); return
                p_lat,p_lon,pn=geo; p_tz=timezone_for_latlon(p_lat,p_lon)
            else: p_lat,p_lon,p_tz,pn=prl,prn,prt,"Manual"
            now=datetime.now(ZoneInfo(p_tz))
            prof={"name":"Prashna","date":now.date().isoformat(),"time":now.strftime("%H:%M"),"place":pn,"lat":p_lat,"lon":p_lon,"tz":p_tz}
            with st.spinner("Casting chart..."): dos=generate_astrology_dossier(prof)
            render_post_generation(build_prashna_prompt(question,dos))
        return

    if mission=="Gochara / Live Transit":
        st.markdown("#### Select your natal chart")
        item=render_profile_form("gochara",show_d60=False)
        if st.button("Generate Live Transit Prompt",type="primary",use_container_width=True):
            if item["type"]=="empty_saved": st.error("Select a profile."); return
            prof,d60=resolve_profile(item)
            with st.spinner("Overlaying transits..."):
                dos=generate_astrology_dossier(prof,d60); overlay=get_gochara_overlay(prof)
            render_post_generation(build_transit_prompt(dos,overlay))
        return

    req=1 if mission in ["Raw Data Only","Deep Personal Analysis"] else 2
    num_slots=st.session_state.comp_slots if mission=="Comparison (Multiple Profiles)" else req
    st.markdown("#### Profile Selection")
    active=[]
    if mission=="Comparison (Multiple Profiles)":
        for i in range(num_slots):
            st.markdown(f"**Profile {i+1}**"); active.append(render_profile_form(f"orc_{mission}_{i}"))
        ca,cb,_=st.columns([1,1,4])
        if ca.button("＋ Add",key=f"addc_{mission}"):
            if st.session_state.comp_slots<10: st.session_state.comp_slots+=1; st.rerun()
        if cb.button("－ Remove",key=f"remc_{mission}"):
            if st.session_state.comp_slots>2: st.session_state.comp_slots-=1; st.rerun()
    else:
        cols=st.columns(min(num_slots,2))
        for i in range(num_slots):
            with cols[i%2]:
                st.markdown(f"**{'Person '+str(i+1) if num_slots>1 else 'Your Details'}**")
                active.append(render_profile_form(f"orc_{mission}_{i}"))

    selected_criteria=[]
    if mission=="Comparison (Multiple Profiles)":
        st.markdown("### What to Compare")
        st.checkbox("Select All",key="select_all_cb",on_change=toggle_all_criteria)
        ca2,cb3=st.columns(2)
        for i,crit in enumerate(COMPARISON_CRITERIA):
            with (ca2 if i%2==0 else cb3):
                if st.checkbox(crit,key=f"chk_{i}"): selected_criteria.append(crit)
        nc_c,nc_a=st.columns([4,1])
        nc=nc_c.text_input("Custom",label_visibility="collapsed",placeholder="e.g. Most likely to be famous")
        if nc_a.button("Add"):
            if nc.strip() and nc.strip() not in st.session_state.custom_criteria:
                st.session_state.custom_criteria.append(nc.strip()); st.rerun()
        for i,c in enumerate(st.session_state.custom_criteria):
            r1,r2=st.columns([6,1])
            if r1.checkbox(c,key=f"cc_{i}"): selected_criteria.append(c)
            if r2.button("✕",key=f"delc_{i}"): st.session_state.custom_criteria.pop(i); st.rerun()

    btn_labels={"Raw Data Only":"Generate Chart Data","Deep Personal Analysis":"Generate Full Reading Prompt",
                "Matchmaking / Compatibility":"Generate Compatibility Prompt","Comparison (Multiple Profiles)":"Generate Comparison Prompt"}
    if st.button(btn_labels.get(mission,"Generate Prompt"),type="primary",use_container_width=True,key=f"gen_{mission}"):
        profiles=[]; d60s=[]
        for item in active:
            if item["type"]=="empty_saved": st.error("Fill all profile slots."); return
            prof,d60=resolve_profile(item); profiles.append(prof); d60s.append(d60)
        if len(profiles)<req: return
        compact=mission=="Comparison (Multiple Profiles)" and len(profiles)>3
        with st.spinner("Consulting the ephemeris..."):
            if mission=="Raw Data Only":
                final=build_raw_prompt(generate_astrology_dossier(profiles[0],d60s[0]))
            elif mission=="Deep Personal Analysis":
                final=build_deep_analysis_prompt(generate_astrology_dossier(profiles[0],d60s[0]))
            elif mission=="Matchmaking / Compatibility":
                ma=get_moon_lon_from_profile(profiles[0]); mb=get_moon_lon_from_profile(profiles[1])
                koota=calculate_ashta_koota(ma,mb)
                jda,dtla,_=local_to_julian_day(date.fromisoformat(profiles[0]['date']),datetime.strptime(profiles[0]['time'],"%H:%M").time(),profiles[0]['tz'])
                pla={pn:get_planet_longitude_and_speed(jda,pid) for pn,pid in PLANETS.items()}
                laga=sign_index_from_lon(get_lagna_and_cusps(jda,profiles[0]['lat'],profiles[0]['lon'])[0])
                ma_d=check_manglik_dosha(laga,sign_index_from_lon(pla["Moon"][0]),sign_index_from_lon(pla["Mars"][0]))
                jdb,dtlb,_=local_to_julian_day(date.fromisoformat(profiles[1]['date']),datetime.strptime(profiles[1]['time'],"%H:%M").time(),profiles[1]['tz'])
                plb={pn:get_planet_longitude_and_speed(jdb,pid) for pn,pid in PLANETS.items()}
                lagb=sign_index_from_lon(get_lagna_and_cusps(jdb,profiles[1]['lat'],profiles[1]['lon'])[0])
                mb_d=check_manglik_dosha(lagb,sign_index_from_lon(plb["Moon"][0]),sign_index_from_lon(plb["Mars"][0]))
                canc=get_manglik_cancellation_verdict(ma_d,mb_d)
                final=build_matchmaking_prompt(generate_astrology_dossier(profiles[0],d60s[0]),generate_astrology_dossier(profiles[1],d60s[1]),koota,canc)
            elif mission=="Comparison (Multiple Profiles)":
                if not selected_criteria: st.warning("Select at least one criterion."); return
                pairs=[(p['name'],generate_astrology_dossier(p,d,compact)) for p,d in zip(profiles,d60s)]
                final=build_comparison_prompt(pairs,selected_criteria)
        render_post_generation(final)

    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# TAROT — Fully rewritten with working animations, all modes
# ═══════════════════════════════════════════════════════════
def show_tarot():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🃏 Mystic Tarot</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6)'>Ask a question and consult the cards. Cryptographically secure randomisation.</p>",unsafe_allow_html=True)

    # Tab selection — switching resets state
    tab_choice=st.radio("Mode",["✦ Three-Card Spread","☯ Yes / No Oracle","🔮 Celtic Cross (10 Cards)","🌟 Birth Card"],
                        horizontal=True,key="tarot_mode_radio",label_visibility="collapsed")

    # Reset when tab changes
    if st.session_state.get("_last_tarot_tab","")!=tab_choice:
        st.session_state.tarot3_drawn=False; st.session_state.tarot3_cards=[]
        st.session_state.tarot3_states=[]; st.session_state.tarot3_mode="General Guidance"
        st.session_state.yn_drawn=False; st.session_state.yn_card=None; st.session_state.yn_state=None
        st.session_state.cc_drawn=False; st.session_state.cc_cards=[]; st.session_state.cc_states=[]
        st.session_state.bc_revealed=False; st.session_state._last_tarot_tab=tab_choice

    st.markdown("---")

    # ── THREE-CARD SPREAD ──
    if "Three-Card" in tab_choice:
        def on_mode_change():
            st.session_state.tarot3_drawn=False; st.session_state.tarot3_cards=[]
            st.session_state.tarot3_states=[]
        spread_mode=st.radio("Spread type",["General Guidance","Love & Dynamics","Decision / Two Paths"],
                             horizontal=True,key="t3_spread",label_visibility="collapsed",on_change=on_mode_change)
        q=st.text_area("Your question",placeholder={"General Guidance":"e.g. What energy is around my career this month?",
            "Love & Dynamics":"e.g. What should I know about my connection with...","Decision / Two Paths":"e.g. Path A or Path B?"}[spread_mode],key="t3_q")
        rev=st.checkbox("Include Reversed Cards",key="t3_rev")
        if st.button("Draw 3 Cards",type="primary",use_container_width=True,key="draw3"):
            if not q.strip(): st.error("Ask a question first."); return
            with st.spinner("Shuffling..."): time_module.sleep(1.2)
            rng=secrets.SystemRandom(); st.session_state.tarot3_cards=rng.sample(FULL_TAROT_DECK,3)
            st.session_state.tarot3_states=[rng.choice(["Upright","Reversed"]) if rev else "Upright" for _ in range(3)]
            st.session_state.tarot3_drawn=True; st.session_state.tarot3_mode=spread_mode
        if st.session_state.tarot3_drawn and st.session_state.tarot3_cards:
            render_tarot_overlay(st.session_state.tarot3_cards,st.session_state.tarot3_states,"three")
            st.markdown(f"**Cards:** {' · '.join(f'{c} ({s})' for c,s in zip(st.session_state.tarot3_cards,st.session_state.tarot3_states))}")
            prompt=build_tarot_prompt(q,st.session_state.tarot3_cards,st.session_state.tarot3_states,st.session_state.tarot3_mode)
            render_post_generation(prompt)
            if st.button("🔄 New Reading",key="reset3"):
                st.session_state.tarot3_drawn=False; st.session_state.tarot3_cards=[]; st.rerun()

    # ── YES / NO ORACLE ──
    elif "Yes / No" in tab_choice:
        q=st.text_input("Your yes/no question",placeholder="e.g. Will this situation resolve in my favour?",key="yn_q")
        rev=st.checkbox("Include Reversed",key="yn_rev")
        if st.button("Draw One Card",type="primary",use_container_width=True,key="draw_yn"):
            if not q.strip(): st.error("Ask a question."); return
            rng=secrets.SystemRandom(); st.session_state.yn_card=rng.choice(FULL_TAROT_DECK)
            st.session_state.yn_state="Upright" if not rev else rng.choice(["Upright","Reversed"])
            st.session_state.yn_drawn=True
        if st.session_state.yn_drawn and st.session_state.yn_card:
            render_tarot_overlay([st.session_state.yn_card],[st.session_state.yn_state],"one")
            st.markdown(f"**Card:** {st.session_state.yn_card} ({st.session_state.yn_state})")
            render_post_generation(build_yesno_prompt(q,st.session_state.yn_card,st.session_state.yn_state))
            if st.button("🔄 Ask Again",key="reset_yn"):
                st.session_state.yn_drawn=False; st.session_state.yn_card=None; st.rerun()

    # ── CELTIC CROSS ──
    elif "Celtic Cross" in tab_choice:
        q=st.text_area("Your question (optional)",placeholder="e.g. What do I need to know about the next chapter of my life?",key="cc_q")
        rev=st.checkbox("Include Reversed Cards",key="cc_rev")
        if st.button("Draw 10 Cards",type="primary",use_container_width=True,key="draw_cc"):
            with st.spinner("Laying out the Celtic Cross..."): time_module.sleep(1.5)
            rng=secrets.SystemRandom(); st.session_state.cc_cards=rng.sample(FULL_TAROT_DECK,10)
            st.session_state.cc_states=["Upright" if not rev else rng.choice(["Upright","Reversed"]) for _ in range(10)]
            st.session_state.cc_drawn=True
        if st.session_state.cc_drawn and st.session_state.cc_cards:
            render_tarot_overlay(st.session_state.cc_cards,st.session_state.cc_states,"ten")
            for i,(c,s) in enumerate(zip(st.session_state.cc_cards,st.session_state.cc_states)):
                st.markdown(f"**{CELTIC_CROSS_POSITIONS[i]}:** {c} ({s})")
            prompt=build_celtic_cross_prompt(q or "General life overview",st.session_state.cc_cards,st.session_state.cc_states)
            render_post_generation(prompt)
            if st.button("🔄 New Celtic Cross",key="reset_cc"):
                st.session_state.cc_drawn=False; st.session_state.cc_cards=[]; st.rerun()

    # ── BIRTH CARD ──
    elif "Birth Card" in tab_choice:
        st.markdown("#### Your Tarot Birth Card")
        st.caption("A permanent card determined by your date of birth — it represents your soul's archetype and lifelong theme.")
        bc_dob=st.date_input("Date of Birth",date(2000,1,1),key="bc_dob_input")
        if st.button("Reveal My Birth Card",type="primary",use_container_width=True,key="reveal_bc"):
            st.session_state.bc_dob=bc_dob; st.session_state.bc_revealed=True
        if st.session_state.bc_revealed and st.session_state.bc_dob:
            card=get_tarot_birth_card(st.session_state.bc_dob.isoformat())
            # Show single card with same overlay style as yes/no
            render_tarot_overlay([card],["Upright"],"one")
            st.markdown(f"**Your Birth Card:** {card}")
            st.caption("This card never changes — it is your permanent soul archetype.")
            render_post_generation(build_birth_card_prompt(card,str(st.session_state.bc_dob)))
            if st.button("🔄 Check Another Date",key="reset_bc"):
                st.session_state.bc_revealed=False; st.rerun()
    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# HOROSCOPES
# ═══════════════════════════════════════════════════════════
def show_horoscopes():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🌟 Horoscopes</h1>",unsafe_allow_html=True)
    st.info("ℹ️ These are algorithmically generated from traditional sign-based guidance — not from your personal birth chart. For a chart-accurate personalised reading, use **The Oracle**.")
    dp,_=get_default_profile()
    user_tz=dp['tz'] if dp else "Asia/Kolkata"
    today=get_local_today(user_tz)  # FIX: use user timezone
    t1,t2=st.tabs(["☀️ Western (Sun Sign)","🌙 Vedic (Moon Sign)"])
    with t1:
        dob=st.date_input("Date of Birth",date(2000,1,1),key="h_w_dob")
        if st.button("Show Horoscope",type="primary",key="w_btn"):
            sign=get_western_sign(dob.month,dob.day); st.success(f"Your Sun Sign: **{sign}**")
            pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
            with pt1: st.write(generate_horoscope_text(sign,"D",today.isoformat()))
            with pt2: st.write(generate_horoscope_text(sign,"M",f"{today.year}-{today.month}"))
            with pt3: st.write(generate_horoscope_text(sign,"Y",f"{today.year}"))
    with t2:
        item=render_profile_form("vedic_horo",show_d60=False)
        if st.button("Calculate Vedic Horoscope",type="primary",key="v_btn"):
            if item["type"]=="empty_saved": st.error("Select or enter a profile.")
            else:
                prof,_=resolve_profile(item)
                moon_lon=get_moon_lon_from_profile(prof); moon_sidx=sign_index_from_lon(moon_lon)
                sign_n=sign_name(moon_sidx); nak,_,_=nakshatra_info(moon_lon)
                st.success(f"Your Rashi (Moon Sign): **{sign_n}** | Birth Star: **{nak}**")
                pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
                with pt1: st.write(generate_horoscope_text(sign_n,"DV",today.isoformat()))
                with pt2: st.write(generate_horoscope_text(sign_n,"MV",f"{today.year}-{today.month}"))
                with pt3: st.write(generate_horoscope_text(sign_n,"YV",f"{today.year}"))
    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# NUMEROLOGY
# ═══════════════════════════════════════════════════════════
def show_numerology():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🔢 Numerology</h1>",unsafe_allow_html=True)
    tab1,tab2=st.tabs(["📊 Full Report","⭕ Personal Cycles & Pinnacles"])
    with tab1:
        system=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="num_sys")
        if "Chaldean" in system: st.caption("ℹ️ Chaldean system — authentic ancient tradition. Number 9 is sacred and not assigned to letters.")
        mode=st.radio("Mode",["Full Report","Ask a Question"],horizontal=True,key="num_mode")
        question=""
        if mode=="Ask a Question": question=st.text_area("Your question",key="num_q",placeholder="e.g. When will my career take off?")
        use_astro=st.checkbox("🌌 Cross-validate with Vedic Kundli (maximum accuracy)",key="num_use_astro")
        dp,_=get_default_profile()
        if use_astro:
            st.info("Name and DOB from the astrological profile will be used for numerology.")
            item=render_profile_form("num_prof",show_d60=True)
        else:
            c1,c2=st.columns(2)
            with c1: num_name=st.text_input("Full Birth Name",value=dp['name'] if dp else "",key="num_name")
            with c2: pre_dob=date.fromisoformat(dp['date']) if dp else date(2000,1,1); num_dob=st.date_input("Date of Birth",pre_dob,key="num_dob")
        if st.button("Generate Numerology Prompt",type="primary",use_container_width=True):
            if use_astro:
                if item["type"]=="empty_saved": st.error("Select a saved profile."); return
                prof,d60=resolve_profile(item); name=prof['name']; dob_str=prof['date']
            else:
                if not num_name.strip(): st.error("Enter your name."); return
                name=num_name.strip(); dob_str=num_dob.isoformat()
            with st.spinner("Computing numbers..."):
                lp,dest,soul,pers=calculate_numerology_core(name,dob_str,system)
                user_tz=prof['tz'] if use_astro and 'tz' in prof else "Asia/Kolkata"
                dossier=generate_astrology_dossier(prof,d60) if use_astro else None
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Life Path",f"{lp}{'★' if lp in [11,22,33] else ''}")
            c2.metric("Destiny",f"{dest}{'★' if dest in [11,22,33] else ''}")
            c3.metric("Soul Urge",f"{soul}{'★' if soul in [11,22,33] else ''}")
            c4.metric("Personality",f"{pers}{'★' if pers in [11,22,33] else ''}")
            render_post_generation(build_numerology_prompt(name,dob_str,lp,dest,soul,pers,dossier,question,system))
    with tab2:
        st.markdown("#### Personal Cycles & Pinnacle Challenges")
        st.caption("Understand the numerical timing of your life phases — including the obstacles built into each cycle.")
        sys3=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="cyc_sys")
        c1,c2=st.columns(2)
        with c1: cyc_name=st.text_input("Full Birth Name",value=dp['name'] if dp else "",key="cyc_name")
        with c2: pre_dob=date.fromisoformat(dp['date']) if dp else date(2000,1,1); cyc_dob=st.date_input("Date of Birth",pre_dob,key="cyc_dob")
        if st.button("Show My Cycles",type="primary",use_container_width=True):
            if not cyc_name.strip(): st.error("Enter your name."); return
            lp,_,_,_=calculate_numerology_core(cyc_name.strip(),cyc_dob.isoformat(),sys3)
            user_tz=dp['tz'] if dp else "Asia/Kolkata"
            py=get_personal_year(cyc_dob.isoformat()); pm=get_personal_month(cyc_dob.isoformat(),user_tz); pd=get_personal_day(cyc_dob.isoformat(),user_tz)
            r1,r2,r3,r4=get_pinnacle_cycles(cyc_dob.isoformat()); y=cyc_dob.year
            cur_age=get_local_today(user_tz).year-y
            st.markdown("#### Your Timing Numbers Today")
            c1,c2,c3=st.columns(3)
            c1.metric(f"Personal Year {get_local_today(user_tz).year}",str(py)); c1.caption(PERSONAL_YEAR_MEANINGS.get(py,''))
            c2.metric("Personal Month",str(pm)); c3.metric("Personal Day",str(pd))
            st.markdown("#### Pinnacle Cycles & Challenges")
            for i,(s,e,n,c) in enumerate([r1,r2,r3,r4],1):
                is_curr=s-y<=cur_age<e-y
                badge="◀ YOU ARE HERE" if is_curr else ""
                col=st.container(border=True)
                col.markdown(f"**Pinnacle {i}** (Ages {s-y}–{e-y if e-y-y<100 else '∞'}) &nbsp; {f'<span style=\"color:#c09040\">{badge}</span>' if badge else ''}",unsafe_allow_html=True)
                col.write(f"**Pinnacle Number: {n}** — {PERSONAL_YEAR_MEANINGS.get(n,'')}")
                col.write(f"**Challenge Number: {c}** — {'Master your need for control and ego.' if c==1 else 'Overcome fear of confrontation and indecision.' if c==2 else 'Build self-discipline to channel your emotions.' if c==3 else 'Learn to work within limitations patiently.' if c==4 else 'Ground your need for constant change and freedom.' if c==5 else 'Release perfectionism and learn to receive.' if c==6 else 'Trust yourself without constant external validation.' if c==7 else 'Balance material ambition with spiritual values.' if c==8 else 'Complete cycles; resist clinging to the past.' if c==9 else 'Own your spiritual sensitivity as a gift.'}")
            is_vedic="Vedic" in sys3
            pdf_r=f"  {PDF_NUMEV}" if is_vedic else f"  {PDF_NUMEW1}\n  {PDF_NUMEW2}"
            prompt=f"""<instructions>
You are a Master Numerologist — {'Chaldean (Indian/Vedic)' if is_vedic else 'Pythagorean (Western)'} system.
PRIMARY KNOWLEDGE BASE (MANDATORY):
{pdf_r}
All numbers below are PRE-COMPUTED and LOCKED. Do NOT recalculate.
</instructions>
<numerology_data>
Subject: {cyc_name.strip()} | DOB: {cyc_dob.isoformat()} | Life Path: {lp}
Personal Year: {py} — {PERSONAL_YEAR_MEANINGS.get(py,'')}
Personal Month: {pm} | Personal Day: {pd}
Pinnacle 1 (Ages {r1[0]-y}–{r1[1]-y}): Number {r1[2]} | Challenge: {r1[3]}
Pinnacle 2 (Ages {r2[0]-y}–{r2[1]-y}): Number {r2[2]} | Challenge: {r2[3]}
Pinnacle 3 (Ages {r3[0]-y}–{r3[1]-y}): Number {r3[2]} | Challenge: {r3[3]}
Pinnacle 4 (Ages {r4[0]-y}+): Number {r4[2]} | Challenge: {r4[3]}
</numerology_data>
<mission>
Explain:
1. Current Personal Year energy and what it means for the next 12 months
2. Personal Month and Day energy — what to focus on right now
3. The currently active Pinnacle Number and its life theme
4. The currently active Challenge Number — what specific obstacle is the universe asking you to master?
5. How the Pinnacle and Challenge work together as a push-pull dynamic
</mission>"""
            render_post_generation(prompt)
    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# SAVED PROFILES / VAULT
# ═══════════════════════════════════════════════════════════
def show_vault():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>📖 Saved Profiles</h1>",unsafe_allow_html=True)
    dp_idx=st.session_state.default_profile_idx

    if not st.session_state.db:
        st.info("No saved profiles yet. Add your first one below.")
    else:
        st.markdown("### Your Profiles")
        st.caption("☆ Tap the star on any profile to set it as your default — it will auto-load across the app.")
        cols=st.columns(min(len(st.session_state.db),3))
        for i,p in enumerate(st.session_state.db):
            is_def=dp_idx==i
            with cols[i%3]:
                # Plain text rendering, no stray CSS
                badge_html='<span class="def-badge">⭐ My Profile</span><br>' if is_def else ''
                st.markdown(f"""<div class="prof-card {'prof-card-def' if is_def else 'prof-card-norm'}">
{badge_html}<p class="prof-name">{p['name']}</p>
<p class="prof-sub">{format_date_ui(p['date'])} · {p['time']}</p>
<p class="prof-sub">📍 {p['place'].split(',')[0]}</p>
</div>""",unsafe_allow_html=True)
                b1,b2,b3=st.columns(3)
                with b1:
                    if st.button("✏️",key=f"ve_{i}",use_container_width=True,help="Edit"):
                        st.session_state.editing_idx=i; st.rerun()
                with b2:
                    if is_def:
                        if st.button("★",key=f"vd_{i}",use_container_width=True,help="Remove default"):
                            clear_default_profile(); st.rerun()
                    else:
                        if st.button("☆",key=f"vd_{i}",use_container_width=True,help="Set as my profile"):
                            set_default_profile(i); st.rerun()
                with b3:
                    if st.button("🗑️",key=f"vdel_{i}",use_container_width=True,help="Delete"):
                        st.session_state.db.pop(i); sync_db()
                        if dp_idx==i: clear_default_profile()
                        elif dp_idx is not None and dp_idx>i: set_default_profile(dp_idx-1)
                        if st.session_state.editing_idx==i: st.session_state.editing_idx=None
                        st.rerun()

    if st.session_state.editing_idx is not None:
        st.markdown("---"); ei=st.session_state.editing_idx; pd_=st.session_state.db[ei]
        st.markdown(f"### ✏️ Editing: {pd_['name']}")
        e1,e2=st.columns(2)
        with e1:
            u_name=st.text_input("Name",pd_['name'],key="ve_n")
            u_date=st.date_input("Date",date.fromisoformat(pd_['date']),key="ve_d")
            pt=datetime.strptime(pd_['time'],"%H:%M").time()
            t1,t2,t3=st.columns(3); dhr=pt.hour%12 or 12; dai=0 if pt.hour<12 else 1
            with t1: u_hr=st.number_input("Hour",1,12,dhr,key="ve_hr")
            with t2: u_mi=st.number_input("Min",0,59,pt.minute,key="ve_mi")
            with t3: u_am=st.selectbox("AM/PM",["AM","PM"],index=dai,key="ve_am")
        with e2:
            is_m=pd_['place']=="Manual Coordinates"
            u_place=st.text_input("Birth Place","" if is_m else pd_['place'],key="ve_p")
            manual=st.checkbox("Manual coordinates",is_m,key="ve_man")
            det_lat=det_lon=det_tz=det_place=None
            if u_place.strip() and not manual:
                geo=geocode_place(u_place.strip())
                if geo: det_lat,det_lon,det_place=geo; det_tz=timezone_for_latlon(det_lat,det_lon); st.success(f"📍 {geo[2]}")
                else: st.warning("Not found.")
            if manual:
                m1,m2,m3=st.columns(3)
                with m1: m_lat=st.number_input("Lat",float(pd_['lat']),format="%.4f",key="ve_lat")
                with m2: m_lon=st.number_input("Lon",float(pd_['lon']),format="%.4f",key="ve_lon")
                with m3: m_tz=st.text_input("TZ",pd_['tz'],key="ve_tz")
        b1,b2=st.columns(2)
        if b1.button("Save Changes",type="primary"):
            h24=(u_hr+12 if u_am=="PM" and u_hr!=12 else 0 if u_am=="AM" and u_hr==12 else u_hr)
            if manual:
                if not m_tz.strip(): st.error("Enter timezone."); st.stop()
                fl2,fln2,ftz2,fp2=m_lat,m_lon,m_tz,"Manual Coordinates"
            else:
                if det_lat is None: st.error("Enter valid birth place."); st.stop()
                fl2,fln2,ftz2,fp2=det_lat,det_lon,det_tz,det_place
                if not ftz2: st.error("Timezone failed."); st.stop()
            st.session_state.db[ei]={"name":u_name,"date":u_date.isoformat(),"time":time(h24,u_mi).strftime("%H:%M"),"place":fp2,"lat":fl2,"lon":fln2,"tz":ftz2}
            st.session_state.editing_idx=None; sync_db(); st.rerun()
        if b2.button("Cancel"): st.session_state.editing_idx=None; st.rerun()

    st.markdown("---")
    if not st.session_state.show_add_profile:
        if st.button("➕ Add New Profile",use_container_width=True,key="toggle_add"):
            st.session_state.show_add_profile=True; st.rerun()
    else:
        st.markdown("### ➕ Add New Profile")
        with st.container(border=True):
            c1,c2=st.columns(2)
            with c1:
                v_n=st.text_input("Name",key="v_new_n"); v_d=st.date_input("Date of Birth",date(2000,1,1),key="v_new_d")
                t1,t2,t3=st.columns(3)
                with t1: v_h=st.number_input("Hour",1,12,12,key="v_new_h")
                with t2: v_m=st.number_input("Min",0,59,0,key="v_new_m")
                with t3: v_a=st.selectbox("AM/PM",["AM","PM"],index=1,key="v_new_a")
            with c2:
                v_p=st.text_input("Birth Place (City, Country)",key="v_new_p")
                v_man=st.checkbox("Manual coordinates",key="v_new_man")
                if v_man:
                    vm1,vm2,vm3=st.columns(3)
                    with vm1: v_lat=st.number_input("Lat",value=0.0,format="%.4f",key="v_new_lat")
                    with vm2: v_lon_v=st.number_input("Lon",value=0.0,format="%.4f",key="v_new_lon")
                    with vm3: v_tz=st.text_input("TZ","Asia/Kolkata",key="v_new_tz")
            also_def=st.checkbox("Set this as my default profile",key="v_also_def")
            sa1,sa2=st.columns(2)
            if sa1.button("Add Profile",type="primary",use_container_width=True):
                if not v_n.strip(): st.error("Name required."); st.stop()
                h24=(v_h+12 if v_a=="PM" and v_h!=12 else 0 if v_a=="AM" and v_h==12 else v_h)
                if v_man:
                    if not v_tz.strip(): st.error("Timezone required."); st.stop()
                    lat,lon,tz,pn=v_lat,v_lon_v,v_tz,"Manual Coordinates"
                else:
                    if not v_p.strip(): st.error("Place required."); st.stop()
                    geo=geocode_place(v_p.strip())
                    if not geo: st.error("Location not found."); st.stop()
                    lat,lon,pn=geo; tz=timezone_for_latlon(lat,lon)
                new_prof={"name":v_n.strip(),"date":v_d.isoformat(),"time":time(h24,v_m).strftime("%H:%M"),"place":pn,"lat":lat,"lon":lon,"tz":tz}
                if not is_duplicate_in_db(new_prof):
                    st.session_state.db.append(new_prof); sync_db()
                    if also_def: set_default_profile(len(st.session_state.db)-1)
                    st.success("Profile added!"); st.session_state.show_add_profile=False; time_module.sleep(.5); st.rerun()
                else: st.warning("Profile already exists.")
            if sa2.button("Cancel",use_container_width=True): st.session_state.show_add_profile=False; st.rerun()

    st.markdown("---")
    st.markdown("### 💾 Data Backup")
    # Export includes default profile index
    export_data={"profiles":st.session_state.db,"default_idx":st.session_state.default_profile_idx}
    b1,b2=st.columns(2)
    with b1:
        st.download_button("⬇️ Export Profiles",data=json.dumps(export_data,indent=2),file_name="kundli_backup.json",use_container_width=True)
    with b2:
        uf=st.file_uploader("Import Backup JSON",type="json",label_visibility="collapsed")
        if uf:
            try:
                imp=json.loads(uf.getvalue().decode('utf-8'))
                if isinstance(imp,dict) and "profiles" in imp:
                    st.session_state.db=imp["profiles"]; sync_db()
                    if imp.get("default_idx") is not None:
                        set_default_profile(imp["default_idx"])
                    st.success("Backup restored!"); time_module.sleep(.5); st.rerun()
                elif isinstance(imp,list):  # legacy format
                    st.session_state.db=imp; sync_db(); st.success("Imported."); time_module.sleep(.5); st.rerun()
                else: st.error("Invalid format.")
            except Exception as e: st.error(f"Invalid file: {e}")
    render_bottom_nav()

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
inject_nebula_css()
render_sidebar()

page=st.session_state.nav_page
if   page=="Dashboard":      show_dashboard()
elif page=="The Oracle":     show_oracle()
elif page=="Mystic Tarot":   show_tarot()
elif page=="Horoscopes":     show_horoscopes()
elif page=="Numerology":     show_numerology()
elif page=="Saved Profiles": show_vault()

if st.session_state.get('needs_sync',False):
    localS.setItem("kundli_vault",json.dumps(st.session_state.db))
    st.session_state.needs_sync=False
