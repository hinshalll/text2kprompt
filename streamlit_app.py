import json, base64, secrets, textwrap, time as time_module
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_local_storage import LocalStorage

# ══════════════════════════════════════════════════════
# CONFIG & IMMERSION
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="Kundli AI", page_icon="🪐", layout="wide",
                   initial_sidebar_state="expanded")
try: swe.set_ephe_path("ephe")
except: pass
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ══════════════════════════════════════════════════════
# CONSTANTS & PDF GUIDES
# ══════════════════════════════════════════════════════
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
PLANETS = {"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
DIGNITIES = {"Sun":(0,6),"Moon":(1,7),"Mars":(9,3),"Mercury":(5,11),"Jupiter":(3,9),"Venus":(11,5),"Saturn":(6,0)}
OWN_SIGNS = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],"Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
SIGN_LORDS_MAP = {0:"Mars",1:"Venus",2:"Mercury",3:"Moon",4:"Sun",5:"Mercury",6:"Venus",7:"Mars",8:"Jupiter",9:"Saturn",10:"Saturn",11:"Jupiter"}
COMBUST_DEGREES = {"Mercury":14,"Venus":10,"Mars":17,"Jupiter":11,"Saturn":15}
NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
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
NAK_PLAIN = {
    "Fixed (Dhruva)":  ("🏛️ Stable Day","Great for long-term decisions, property, investments, or starting something permanent."),
    "Movable (Chara)": ("🌊 Dynamic Day","Good energy for travel, change, buying vehicles, or flexible plans."),
    "Fierce (Ugra)":   ("⚔️ Intense Day","Best for bold action, confronting problems. Avoid gentle or sensitive conversations."),
    "Mixed (Mishra)":  ("📋 Routine Day","Average energy. Good for everyday tasks, admin, and pending work."),
    "Swift (Kshipra)": ("⚡ Fast Day","Quick wins. Great for trading, fast decisions, and communication."),
    "Tender (Mridu)":  ("💫 Soft Day","Beautiful energy for romance, creativity, friendships, and arts."),
    "Sharp (Tikshna)": ("🔍 Focused Day","Excellent for deep research, breaking bad habits, or ending things."),
}
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
YOGA_NAMES = ["Vishkambha","Priti","Ayushman","Saubhagya","Sobhana","Atiganda","Sukarma","Dhriti","Soola","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra","Siddhi","Vyatipata","Variyan","Parigha","Siva","Siddha","Sadhya","Subha","Sukla","Brahma","Indra","Vaidhriti"]
YEAR_DAYS=365.2425; MOVABLE_SIGNS={0,3,6,9}; FIXED_SIGNS={1,4,7,10}
DEB_SIGN_LORDS={"Sun":"Venus","Moon":"Mars","Mars":"Moon","Mercury":"Jupiter","Jupiter":"Saturn","Venus":"Mercury","Saturn":"Mars"}
EXALT_LORD_IN_DEB_SIGN={"Sun":"Saturn","Moon":None,"Mars":"Jupiter","Mercury":"Venus","Jupiter":"Mars","Venus":"Mercury","Saturn":"Sun"}
PYTH_MAP={'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,'s':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8}
CHALDEAN_MAP={'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':2,'s':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}
MAJOR_ARCANA=["The Fool","The Magician","The High Priestess","The Empress","The Emperor","The Hierophant","The Lovers","The Chariot","Strength","The Hermit","Wheel of Fortune","Justice","The Hanged Man","Death","Temperance","The Devil","The Tower","The Star","The Moon","The Sun","Judgement","The World"]
FULL_TAROT_DECK = MAJOR_ARCANA[:]
for suit in ["Wands","Cups","Swords","Pentacles"]:
    for rank in ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Page","Knight","Queen","King"]:
        FULL_TAROT_DECK.append(f"{rank} of {suit}")
COMPARISON_CRITERIA=["Wealth Potential — Who builds the most wealth?",
    "Relationship Quality — Who has the best marriage/love life?",
    "Career Success — Who reaches the highest professional position?",
    "Life Struggles — Who faces the most karmic obstacles?",
    "Health & Longevity — Who has the strongest constitution?",
    "Happiness & Contentment — Who lives the most fulfilled life?",
    "Luck & Fortune — Who is the most naturally fortunate?",
    "Spiritual Depth — Who is the most spiritually evolved?",
    "Hidden Pitfalls — Who faces the most unexpected structural problems?"]
PERSONAL_YEAR_MEANINGS={
    1:"New beginnings, independence, leadership. Plant seeds now.",
    2:"Partnership, patience, diplomacy. Relationships are highlighted.",
    3:"Creativity, expression, social energy. A year to shine.",
    4:"Hard work, foundations, discipline. Build something lasting.",
    5:"Freedom, change, adventure. Expect the unexpected.",
    6:"Home, family, responsibility. Nurture your relationships.",
    7:"Reflection, spirituality, inner growth. A year to go inward.",
    8:"Power, ambition, material success. Financial opportunities arise.",
    9:"Completion, release, transformation. Let go of what no longer serves.",
    11:"Intuition, spiritual awakening, inspiration. Master Number energy.",
    22:"Mastery, large-scale building, legacy. Master Number energy.",
    33:"Compassion, teaching, healing. Master Number energy."}
CELTIC_CROSS_POSITIONS=[
    "1. The Present — The core issue or central energy",
    "2. The Challenge — What crosses or complicates the present",
    "3. The Foundation — Unconscious influences, deep roots",
    "4. The Past — What is passing or recently passed",
    "5. The Crown — Potential outcome or conscious goal",
    "6. The Near Future — What approaches in the coming weeks",
    "7. The Self — Your attitude and how you show up",
    "8. External Influences — How others or environment affect you",
    "9. Hopes & Fears — Inner tension, what you desire and dread",
    "10. The Outcome — The most likely resolution if path continues"]

PDF_BASE="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/"
PDF_HTRH1=f"{PDF_BASE}htrh1.pdf"
PDF_HTRH2=f"{PDF_BASE}htrh2.pdf"
PDF_TGUIDE=f"{PDF_BASE}tguide.pdf"
PDF_NUMEW1=f"{PDF_BASE}numeguide1.pdf"
PDF_NUMEW2=f"{PDF_BASE}numeguide2.pdf"
PDF_NUMEV=f"{PDF_BASE}vedicnume.pdf"

# ══════════════════════════════════════════════════════
# SESSION STATE & TIME HELPERS
# ══════════════════════════════════════════════════════
localS=LocalStorage()
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
    di=localS.getItem("kundli_default_profile")
    st.session_state.default_profile_idx=int(di) if di is not None and str(di).isdigit() else None
if 'needs_sync' not in st.session_state: st.session_state.needs_sync=False
if 'custom_criteria' not in st.session_state: st.session_state.custom_criteria=[]
if 'editing_idx' not in st.session_state: st.session_state.editing_idx=None
if 'comp_slots' not in st.session_state: st.session_state.comp_slots=2
if 'nav_page' not in st.session_state: st.session_state.nav_page="Dashboard"
if 'active_mission' not in st.session_state: st.session_state.active_mission="Deep Personal Analysis"
if 'tarot_drawn' not in st.session_state: st.session_state.tarot_drawn=False
if 'tarot_cards' not in st.session_state: st.session_state.tarot_cards=[]
if 'tarot_states' not in st.session_state: st.session_state.tarot_states=[]
if 'tarot_question_input' not in st.session_state: st.session_state.tarot_question_input=""
if 'tarot_mode' not in st.session_state: st.session_state.tarot_mode="General Guidance"
if 'yesno_drawn' not in st.session_state: st.session_state.yesno_drawn=False
if 'yesno_card' not in st.session_state: st.session_state.yesno_card=None
if 'yesno_state' not in st.session_state: st.session_state.yesno_state=None
if 'dash_tarot_card' not in st.session_state: st.session_state.dash_tarot_card=None
if 'dash_tarot_state' not in st.session_state: st.session_state.dash_tarot_state=None
if 'dash_tarot_date' not in st.session_state: st.session_state.dash_tarot_date=None
if 'show_add_profile' not in st.session_state: st.session_state.show_add_profile=False
if 'select_all_cb' not in st.session_state: st.session_state.select_all_cb=False
for i in range(len(COMPARISON_CRITERIA)):
    if f"chk_{i}" not in st.session_state: st.session_state[f"chk_{i}"]=False

def get_local_today(tz_string="Asia/Kolkata"):
    return datetime.now(ZoneInfo(tz_string)).date()

def sync_db(): st.session_state.needs_sync=True
def is_duplicate_in_db(p): return any(x['name']==p['name'] and x['date']==p['date'] for x in st.session_state.db)
def format_date_ui(s): return datetime.fromisoformat(s).strftime('%d %b %Y')
def get_filename(card_name): return card_name.lower().replace(' ','')+'.jpg'
def set_nav(page): st.session_state.nav_page=page
def toggle_all_criteria():
    val=st.session_state.select_all_cb
    for i in range(len(COMPARISON_CRITERIA)): st.session_state[f"chk_{i}"]=val
    for i in range(len(st.session_state.custom_criteria)): st.session_state[f"cc_{i}"]=val
def get_default_profile():
    idx=st.session_state.default_profile_idx
    if idx is not None and 0<=idx<len(st.session_state.db): return st.session_state.db[idx]
    return None
def set_default_profile(idx):
    st.session_state.default_profile_idx=idx
    localS.setItem("kundli_default_profile",str(idx))
def clear_default_profile():
    st.session_state.default_profile_idx=None
    localS.setItem("kundli_default_profile","")

# ══════════════════════════════════════════════════════
# GEO, EPHEMERIS & CALC HELPERS
# ══════════════════════════════════════════════════════
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
    paksha="Shukla (Waxing)" if tv<180 else "Krishna (Waning)"
    td=tn if tn<=15 else tn-15
    yn=min(int(((moon_lon+sun_lon)%360)/(360/27)),26)
    ki=int(tv/6)
    if ki==0: kn="Kintughna (Fixed)"
    elif 1<=ki<=56: kn=f"{['Bava','Balava','Kaulava','Taitila','Gara','Vanija','Vishti'][(ki-1)%7]} (Movable)"
    elif ki==57: kn="Sakuni (Fixed)"
    elif ki==58: kn="Chatushpada (Fixed)"
    else: kn="Naga (Fixed)"
    return {"tithi":f"{td} {paksha}","yoga":YOGA_NAMES[yn],"karana":kn,
            "weekday":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][dt_local.weekday()]}
def whole_sign_house(lagna_sidx,planet_sidx): return ((planet_sidx-lagna_sidx)%12)+1
def get_western_sign(month,day):
    cusps=[(1,19,"Capricorn"),(2,18,"Aquarius"),(3,20,"Pisces"),(4,19,"Aries"),(5,20,"Taurus"),
           (6,20,"Gemini"),(7,22,"Cancer"),(8,22,"Leo"),(9,22,"Virgo"),(10,22,"Libra"),
           (11,21,"Scorpio"),(12,21,"Sagittarius")]
    for em,ed,sign in cusps:
        if month<em or (month==em and day<=ed): return sign
    return "Capricorn"

@st.cache_data(show_spinner=False)
def geocode_place(place_text):
    try:
        loc=Nominatim(user_agent="kundli_ai_suite").geocode(place_text,exactly_one=True,timeout=10)
        return (loc.latitude,loc.longitude,loc.address) if loc else None
    except: return None
@st.cache_data(show_spinner=False)
def timezone_for_latlon(lat,lon):
    return TimezoneFinder().timezone_at(lat=lat,lng=lon)
def local_to_julian_day(d,t,tz_name):
    lz=ZoneInfo(tz_name); dtl=datetime.combine(d,t).replace(tzinfo=lz)
    dtu=dtl.astimezone(ZoneInfo("UTC"))
    return swe.julday(dtu.year,dtu.month,dtu.day,dtu.hour+dtu.minute/60+dtu.second/3600),dtl,dtu
def get_lagna_and_cusps(jd_ut,lat,lon):
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL; cusps,ascmc=swe.houses_ex(jd_ut,lat,lon,b"O",f)
    return float(ascmc[0])%360,cusps

def get_planet_metrics(jd_ut, planet_id):
    """Returns (longitude, latitude, speed). Fixed for Graha Yuddha calculation."""
    f = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    res, _ = swe.calc_ut(jd_ut, planet_id, f)
    return float(res[0])%360, float(res[1]), float(res[3])

def get_rahu_longitude(jd_ut):
    res,_=swe.calc_ut(jd_ut,swe.MEAN_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    return float(res[0])%360
def get_placidus_cusps(jd_ut,lat,lon):
    cusps,_=swe.houses_ex(jd_ut,lat,lon,b"P",swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    return cusps

@st.cache_data(ttl=3600,show_spinner=False)
def get_live_cosmic_weather():
    dt_now=datetime.now(ZoneInfo("UTC"))
    jd=swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    moon_metrics=get_planet_metrics(jd,swe.MOON); sun_metrics=get_planet_metrics(jd,swe.SUN)
    moon_sidx=sign_index_from_lon(moon_metrics[0]); sun_sidx=sign_index_from_lon(sun_metrics[0])
    nak,_,_=nakshatra_info(moon_metrics[0]); panch=get_panchanga(sun_metrics[0],moon_metrics[0],dt_now)
    retrogrades=[]
    for pname in ["Mars","Mercury","Jupiter","Venus","Saturn"]:
        _,_,spd=get_planet_metrics(jd,PLANETS[pname])
        if spd<0: retrogrades.append(pname)
    nature_type="Mixed (Mishra)"; plain_title,plain_desc=NAK_PLAIN["Mixed (Mishra)"]
    for nt,naks in NAK_NATURES.items():
        if nak in naks: nature_type=nt; plain_title,plain_desc=NAK_PLAIN[nt]; break
    all_pos={}
    for pname,pid in PLANETS.items():
        lon,_,_=get_planet_metrics(jd,pid); all_pos[pname]=f"{sign_name(sign_index_from_lon(lon))} {format_dms(lon%30)}"
    r_lon=get_rahu_longitude(jd)
    all_pos["Rahu"]=f"{sign_name(sign_index_from_lon(r_lon))} {format_dms(r_lon%30)}"
    all_pos["Ketu"]=f"{sign_name(sign_index_from_lon((r_lon+180)%360))} {format_dms((r_lon+180)%30)}"
    return {"moon_sign":sign_name(moon_sidx),"sun_sign":sign_name(sun_sidx),"nakshatra":nak,
            "tithi":panch["tithi"],"yoga":panch["yoga"],"retrogrades":retrogrades,
            "nature":nature_type,"plain_title":plain_title,"plain_desc":plain_desc,"all_pos":all_pos}

# ══════════════════════════════════════════════════════
# ADVANCED ASTROLOGICAL ENGINES
# ══════════════════════════════════════════════════════
def get_kp_sub_lord(lon):
    ns=360/27; idx=int((lon%360)//ns); nak_lord=NAKSHATRA_LORDS[idx]
    deg=lon%360-idx*ns; si=DASHA_ORDER.index(nak_lord); seq=DASHA_ORDER[si:]+DASHA_ORDER[:si]
    acc=0.0
    for sl in seq:
        acc+=(DASHA_YEARS[sl]/120.0)*ns
        if deg<=acc+1e-9: return sl
    return seq[-1]

def get_vedic_aspects(planet_name,current_house):
    jumps={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[5,7,9],"Ketu":[5,7,9]}.get(planet_name,[7])
    return ", ".join(str(((current_house+j-2)%12)+1) for j in jumps)

def get_planet_lon(pname,planet_data,r_lon,k_lon):
    if pname in planet_data: return planet_data[pname][0]
    elif pname=="Rahu": return r_lon
    elif pname=="Ketu": return k_lon

def get_planet_house(pname,lagna_sidx,planet_data,r_lon,k_lon):
    lon=get_planet_lon(pname,planet_data,r_lon,k_lon)
    return whole_sign_house(lagna_sidx,sign_index_from_lon(lon)) if lon is not None else None

def get_lagna_lord_chain(lagna_sidx,planet_data,r_lon,k_lon):
    ll=SIGN_LORDS_MAP[lagna_sidx]; ll_lon=get_planet_lon(ll,planet_data,r_lon,k_lon)
    ll_sidx=sign_index_from_lon(ll_lon); ll_house=whole_sign_house(lagna_sidx,ll_sidx)
    tags=[]
    if ll in DIGNITIES:
        if ll_sidx==DIGNITIES[ll][0]: tags.append("Exalted")
        elif ll_sidx==DIGNITIES[ll][1]: tags.append("Debilitated")
    if ll in OWN_SIGNS and ll_sidx in OWN_SIGNS[ll]: tags.append("Own Sign")
    if ll in planet_data and planet_data[ll][2]<0: tags.append("Retrograde") # [2] is speed
    tag_str=f" [{', '.join(tags)}]" if tags else ""
    disp=SIGN_LORDS_MAP[ll_sidx]; disp_house=get_planet_house(disp,lagna_sidx,planet_data,r_lon,k_lon)
    return f"{ll} → H{ll_house} ({sign_name(ll_sidx)}{tag_str}) → dispositor {disp} in H{disp_house}"

def get_conjunctions(lagna_sidx,planet_data,r_lon,k_lon):
    all_p={}
    for pn,metrics in planet_data.items(): h=whole_sign_house(lagna_sidx,sign_index_from_lon(metrics[0])); all_p.setdefault(h,[]).append(pn)
    for pn,plon in [("Rahu",r_lon),("Ketu",k_lon)]: h=whole_sign_house(lagna_sidx,sign_index_from_lon(plon)); all_p.setdefault(h,[]).append(pn)
    return [f"{' + '.join(plist)} conjunct in H{h} ({sign_name((lagna_sidx+h-1)%12)})" for h,plist in all_p.items() if len(plist)>=2]

def get_mutual_aspects(lagna_sidx,planet_data,r_lon,k_lon):
    spec={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[5,7,9],"Ketu":[5,7,9]}
    def asp(pn,h): return {((h+j-2)%12)+1 for j in spec.get(pn,[7])}
    houses={pn:whole_sign_house(lagna_sidx,sign_index_from_lon(planet_data[pn][0])) for pn in planet_data}
    houses["Rahu"]=whole_sign_house(lagna_sidx,sign_index_from_lon(r_lon))
    houses["Ketu"]=whole_sign_house(lagna_sidx,sign_index_from_lon(k_lon))
    plist=list(houses.keys()); mutual=[]
    for i,p1 in enumerate(plist):
        for p2 in plist[i+1:]:
            h1,h2=houses[p1],houses[p2]
            if h1!=h2 and h2 in asp(p1,h1) and h1 in asp(p2,h2): mutual.append(f"{p1} (H{h1}) ↔ {p2} (H{h2})")
    return mutual

def detect_graha_yuddha(planet_data):
    """FIXED: Planetary War winner is decided by celestial latitude (North/South), not longitude."""
    eligible = {pn: (planet_data[pn][0], planet_data[pn][1]) for pn in ["Mars","Mercury","Jupiter","Venus","Saturn"]}
    plist = list(eligible.items())
    wars = []
    for i, (p1, (l1_lon, l1_lat)) in enumerate(plist):
        for p2, (l2_lon, l2_lat) in plist[i+1:]:
            diff = abs(l1_lon - l2_lon)
            diff = min(diff, 360 - diff)
            if diff <= 1.0:
                winner = p1 if l1_lat > l2_lat else p2
                loser  = p2 if l1_lat > l2_lat else p1
                wars.append((winner, loser, round(diff, 3)))
    return wars

def get_functional_planets(lagna_sidx):
    trikona={1,5,9}; kendra={1,4,7,10}; trika={6,8,12}
    house_lords={}
    for h in range(1,13): lord=SIGN_LORDS_MAP[(lagna_sidx+h-1)%12]; house_lords.setdefault(lord,[]).append(h)
    benefics=[]; malefics=[]; yogakarakas=[]; neutral=[]
    for planet,houses in house_lords.items():
        has_tri=any(h in trikona for h in houses); has_ken=any(h in kendra and h!=1 for h in houses)
        has_trika=any(h in trika for h in houses)
        if has_tri and has_ken: yogakarakas.append(planet)
        elif has_tri: benefics.append(planet)
        elif has_trika and not has_tri: malefics.append(planet)
        else: neutral.append(planet)
    return benefics,malefics,yogakarakas,neutral

def get_house_strength_summary(lagna_sidx,planet_data,r_lon,k_lon,placidus_cusps):
    key_houses={7:("Marriage & Spouse",{2,7,11}),10:("Career & Status",{1,6,10,11}),
                2:("Wealth & Family",{2,11}),5:("Intelligence & Children",{5,11}),
                4:("Home & Mother",{4,12}),11:("Gains & Desires",{3,6,11})}
    summaries=[]
    for h,(theme,ev_houses) in key_houses.items():
        h_sidx=(lagna_sidx+h-1)%12; h_lord=SIGN_LORDS_MAP[h_sidx]
        lord_house=get_planet_house(h_lord,lagna_sidx,planet_data,r_lon,k_lon)
        lord_sidx=sign_index_from_lon(get_planet_lon(h_lord,planet_data,r_lon,k_lon))
        flags=[]
        if h_lord in DIGNITIES:
            if lord_sidx==DIGNITIES[h_lord][0]: flags.append("Lord Exalted")
            elif lord_sidx==DIGNITIES[h_lord][1]: flags.append("Lord Debilitated")
        if h_lord in OWN_SIGNS and lord_sidx in OWN_SIGNS[h_lord]: flags.append("Lord in Own Sign")
        if lord_house in {6,8,12}: flags.append(f"Lord in dusthana H{lord_house}")
        elif lord_house in {1,4,7,10}: flags.append(f"Lord in Kendra H{lord_house}")
        elif lord_house in {1,5,9}: flags.append(f"Lord in Trikona H{lord_house}")
        kp_sl,kp_nl,kp_verdict,kp_sigs=get_kp_verdict(placidus_cusps[h-1],lagna_sidx,planet_data,r_lon,k_lon,ev_houses,theme)
        flag_str=" | ".join(flags) if flags else "Neutral placement"
        summaries.append(f"H{h} ({theme}): Lord={h_lord}(H{lord_house}) [{flag_str}] | KP SL={kp_sl}: {kp_verdict}")
    return summaries

def check_neecha_bhanga(planet_name,lagna_sidx,moon_sidx,planet_data,r_lon,k_lon):
    if planet_name not in DIGNITIES: return None
    p_sidx=sign_index_from_lon(planet_data[planet_name][0])
    if p_sidx!=DIGNITIES[planet_name][1]: return None
    kendra={1,4,7,10}
    def hf(ref,pn):
        lon=get_planet_lon(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(ref,sign_index_from_lon(lon)) if lon else None
    conds=[]
    dsl=DEB_SIGN_LORDS.get(planet_name)
    if dsl:
        h=hf(lagna_sidx,dsl)
        if h in kendra: conds.append(f"dispositor ({dsl}) in Kendra H{h} from Lagna")
        h=hf(moon_sidx,dsl)
        if h in kendra: conds.append(f"dispositor ({dsl}) in Kendra H{h} from Moon")
    exl=EXALT_LORD_IN_DEB_SIGN.get(planet_name)
    if exl:
        h=hf(lagna_sidx,exl)
        if h in kendra: conds.append(f"exaltation-sign lord ({exl}) in Kendra H{h} from Lagna")
    h_from_moon=whole_sign_house(moon_sidx,p_sidx)
    if h_from_moon in kendra: conds.append(f"debilitated planet in Kendra H{h_from_moon} from Moon")
    return conds if conds else None

def get_chara_karakas(planet_data):
    deg={pn:planet_data[pn][0]%30 for pn in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]}
    ranked=sorted(deg,key=deg.get,reverse=True)
    return ranked[0],deg[ranked[0]],ranked[1],deg[ranked[1]]

def detect_yogas(lagna_sidx,moon_sidx,planet_data,r_lon,k_lon):
    def ho(pn):
        lon=get_planet_lon(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(lagna_sidx,sign_index_from_lon(lon)) if lon else None
    def in_kendra(h1,h2): return (h2-h1)%12 in {0,3,6,9}
    yogas=[]; absent=[]
    mh,jh=ho("Moon"),ho("Jupiter")
    if mh and jh and in_kendra(mh,jh): yogas.append(("Gajakesari Yoga",f"Moon(H{mh}) + Jupiter(H{jh}) in mutual Kendra — intelligence, fame, stability"))
    else: absent.append("Gajakesari Yoga — Moon and Jupiter not in mutual Kendra")
    for planet,(yname,exalt_sidx) in {"Mars":("Ruchaka",9),"Mercury":("Bhadra",5),"Jupiter":("Hamsa",3),"Venus":("Malavya",11),"Saturn":("Shasha",6)}.items():
        psidx=sign_index_from_lon(planet_data[planet][0]); ph=whole_sign_house(lagna_sidx,psidx)
        own=planet in OWN_SIGNS and psidx in OWN_SIGNS[planet]; exalt=psidx==exalt_sidx
        if (own or exalt) and ph in {1,4,7,10}: yogas.append((f"{yname} Yoga",f"{planet} in {'own sign' if own else 'exaltation'} in Kendra H{ph} — Pancha Mahapurusha, strong {planet} significations"))
        else: absent.append(f"{yname} Yoga — {planet} not in own/exalt + Kendra simultaneously")
    if ho("Sun")==ho("Mercury"): yogas.append(("Budha-Aditya Yoga",f"Sun + Mercury conjunct H{ho('Sun')} — sharp intellect, communication, professional reputation"))
    else: absent.append("Budha-Aditya Yoga — Sun and Mercury not conjunct")
    if ho("Moon")==ho("Mars"): yogas.append(("Chandra-Mangala Yoga",f"Moon + Mars conjunct H{ho('Moon')} — entrepreneurial drive, financial ambition"))
    else: absent.append("Chandra-Mangala Yoga — Moon and Mars not conjunct")
    mh2=ho("Moon")
    if mh2:
        t6=((mh2-1+5)%12)+1; t7=((mh2-1+6)%12)+1; t8=((mh2-1+7)%12)+1
        ben=[b for b in ["Mercury","Jupiter","Venus"] if ho(b) in {t6,t7,t8}]
        if len(ben)>=2: yogas.append(("Adhi Yoga",f"{', '.join(ben)} in 6/7/8 from Moon — authority, longevity, leadership"))
        else: absent.append("Adhi Yoga — fewer than 2 benefics in 6/7/8 from Moon")
    tri_lords={SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [1,5,9]}
    ken_lords={SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [1,4,7,10]}
    rj=[]
    for tl in tri_lords:
        for kl in ken_lords:
            if tl!=kl:
                th,kh=ho(tl),ho(kl)
                if th and kh and th==kh: rj.append(f"{tl}+{kl} in H{th}")
    if rj: yogas.append(("Raja Yoga",f"Trikona+Kendra lords conjunct: {'; '.join(rj[:2])} — power, high status"))
    else: absent.append("Raja Yoga — no Trikona+Kendra lord conjunction found")
    dust_lords=[SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [6,8,12]]
    dust_in=[dl for dl in dust_lords if ho(dl) in {6,8,12}]
    if len(dust_in)>=2: yogas.append(("Viparita Raja Yoga",f"Dusthana lords ({', '.join(dust_in)}) in dusthana — unexpected rise after adversity"))
    else: absent.append("Viparita Raja Yoga — insufficient dusthana lords in dusthana")
    if mh2:
        h2m=((mh2-1+1)%12)+1; h12m=((mh2-1-1)%12)+1
        all_h={pn:ho(pn) for pn in list(planet_data.keys())+["Rahu","Ketu"] if pn!="Moon"}
        flanking=[pn for pn,h in all_h.items() if h in {h2m,h12m} and pn not in {"Rahu","Ketu"}]
        if not flanking: yogas.append(("Kemadruma Yoga (Negative)",f"No planets flanking Moon in H{h2m}/H{h12m} — emotional isolation tendency. Verify: is it cancelled by Lagna strength or Jupiter aspect?"))
    return yogas,absent

def calculate_sade_sati(natal_moon_sidx):
    dt_now=datetime.now(ZoneInfo("UTC"))
    jd=swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    res,_=swe.calc_ut(jd,swe.SATURN,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    sat_sidx=sign_index_from_lon(float(res[0])%360); diff=(sat_sidx-natal_moon_sidx)%12
    phases={11:"ACTIVE — Phase 1 (Rising)",0:"ACTIVE — Phase 2 (Peak — most intense)",1:"ACTIVE — Phase 3 (Setting)"}
    if diff in phases: return f"{phases[diff]}: Saturn in {sign_name(sat_sidx)}, Natal Moon in {sign_name(natal_moon_sidx)}."
    return f"NOT ACTIVE (Saturn is {diff} signs from natal Moon in {sign_name(natal_moon_sidx)})."

def check_manglik_dosha(lagna_sidx,moon_sidx,mars_sidx):
    mh_l=whole_sign_house(lagna_sidx,mars_sidx); mh_m=whole_sign_house(moon_sidx,mars_sidx)
    il=mh_l in [1,4,7,8,12]; im=mh_m in [1,4,7,8,12]
    if il and im: return "HIGH MANGLIK — Mars in Manglik house from both Ascendant and Moon"
    elif il: return "MILD MANGLIK — Mars in Manglik house from Ascendant only"
    elif im: return "MILD MANGLIK — Mars in Manglik house from Moon only"
    return "NOT MANGLIK — No Kuja Dosha"

def get_manglik_cancellation_verdict(mang_a,mang_b):
    m1="NOT MANGLIK" not in mang_a; m2="NOT MANGLIK" not in mang_b
    if m1 and m2: return "MANGLIK DOSHA CANCELLED — Both partners are Manglik (classical cancellation). No Kuja Dosha remedy required."
    elif not m1 and not m2: return "No Manglik Dosha in either chart. No issue."
    who="Person 1 is Manglik" if m1 else "Person 2 is Manglik"
    return f"MANGLIK IMBALANCE — {who}, the other is not. A carefully chosen Muhurta and classical remedies are advisable."

def calculate_ashta_koota(moon_lon_a,moon_lon_b):
    s1=sign_index_from_lon(moon_lon_a); s2=sign_index_from_lon(moon_lon_b)
    n1=min(int((moon_lon_a%360)//(360/27)),26); n2=min(int((moon_lon_b%360)//(360/27)),26)
    vm=[1,2,3,0,1,2,3,0,1,2,3,0]; v_pts=1 if vm[s1]<=vm[s2] else 0
    va=[0,0,1,2,3,1,1,4,0,2,1,2]; va1,va2=va[s1],va[s2]
    if va1==va2: va_pts=2
    elif {va1,va2} in [{1,3},{1,4},{2,3}]: va_pts=0
    else: va_pts=1
    t1=((n2-n1)%27)%9; t2=((n1-n2)%27)%9
    ta_pts=(0 if t1 in [2,4,6] else 1.5)+(0 if t2 in [2,4,6] else 1.5)
    ym=[0,1,2,3,3,4,5,2,5,6,6,7,8,9,8,9,10,10,4,11,12,11,13,0,13,7,1]
    y1,y2=ym[n1],ym[n2]
    enemies=[{0,8},{1,13},{2,11},{3,12},{4,10},{5,6},{7,9}]
    yoni_pts=4 if y1==y2 else (0 if {y1,y2} in enemies else 2)
    lm=[0,1,2,3,4,2,1,0,5,6,6,5]; l1,l2=lm[s1],lm[s2]
    f_map={0:[3,4,5],1:[2,6],2:[1,4],3:[2,4],4:[0,3,5],5:[0,3,4],6:[1,2]}
    e_map={0:[2],1:[3,4],2:[3],3:[],4:[1,6],5:[1,2],6:[0,3,4]}
    def rel(a,b): return 2 if b in f_map.get(a,[]) else (0 if b in e_map.get(a,[]) else 1)
    ms_map={(2,2):5,(2,1):4,(1,2):4,(1,1):3,(2,0):1,(0,2):1,(1,0):0.5,(0,1):0.5,(0,0):0}
    m_pts=ms_map.get((rel(l1,l2),rel(l2,l1)),0)
    gm={0:0,1:1,2:2,3:1,4:0,5:1,6:0,7:0,8:2,9:2,10:1,11:1,12:0,
        13:2,14:0,15:2,16:0,17:2,18:2,19:1,20:1,21:0,22:2,23:2,24:1,25:1,26:0}
    g1,g2=gm[n1],gm[n2]
    if g1==g2: g_pts=6
    elif g1==0 and g2==1: g_pts=6
    elif g1==1 and g2==0: g_pts=5
    elif g1==0 and g2==2: g_pts=1
    else: g_pts=0
    dist=(s2-s1)%12; b_pts=7 if dist in [0,2,3,6,8,9,10] else 0
    nb=[0,1,2]*9; nd1,nd2=nb[n1],nb[n2]; nadi_note=""
    if nd1==nd2:
        n_pts=0
        if n1==n2: nadi_note="NADI DOSHA EXCEPTION: Same birth Nakshatra — Dosha CANCELLED."
        elif SIGN_LORDS_MAP[s1]!=SIGN_LORDS_MAP[s2]: nadi_note="NADI DOSHA PARTIAL EXCEPTION: Different Moon sign lords — severity reduced."
    else: n_pts=8
    total=v_pts+va_pts+ta_pts+yoni_pts+m_pts+g_pts+b_pts+n_pts
    result=(f"TOTAL ASHTA KOOTA SCORE: {total}/36\n"
            f"  Varna(1pt):{v_pts} | Vashya(2pt):{va_pts} | Tara(3pt):{ta_pts} | Yoni(4pt):{yoni_pts}\n"
            f"  GrahaMaitri(5pt):{m_pts} | Gana(6pt):{g_pts} | Bhakoot(7pt):{b_pts} | Nadi(8pt):{n_pts}")
    if nadi_note: result+=f"\n  NOTE: {nadi_note}"
    if total>=31: result+="\n  QUALITY: Excellent match (31-36). Highly compatible."
    elif total>=18: result+="\n  QUALITY: Good match (18-30). Compatible with some considerations."
    else: result+=f"\n  QUALITY: Challenging match ({total}/36). Significant concerns."
    return result

def get_planet_house_significations(pname,lagna_sidx,planet_data,r_lon,k_lon):
    lon=get_planet_lon(pname,planet_data,r_lon,k_lon)
    if lon is None: return set()
    sigs=set(); psidx=sign_index_from_lon(lon); sigs.add(whole_sign_house(lagna_sidx,psidx))
    for sidx,lord in SIGN_LORDS_MAP.items():
        if lord==pname: sigs.add(whole_sign_house(lagna_sidx,sidx))
    _,sl,_=nakshatra_info(lon)
    if sl!=pname:
        sl_lon=get_planet_lon(sl,planet_data,r_lon,k_lon)
        if sl_lon:
            sigs.add(whole_sign_house(lagna_sidx,sign_index_from_lon(sl_lon)))
            for sidx,lord in SIGN_LORDS_MAP.items():
                if lord==sl: sigs.add(whole_sign_house(lagna_sidx,sidx))
    return sigs

def get_kp_verdict(cusp_lon,lagna_sidx,planet_data,r_lon,k_lon,event_houses,event_name):
    sl=get_kp_sub_lord(cusp_lon); nl=nakshatra_info(cusp_lon)[1]
    sigs=get_planet_house_significations(sl,lagna_sidx,planet_data,r_lon,k_lon)
    matched=sigs&event_houses; sig_str=", ".join(f"H{h}" for h in sorted(sigs))
    if len(matched)>=2 or (max(event_houses) in matched): verdict="STRONGLY PROMISED"
    elif len(matched)==1: verdict="WEAKLY PROMISED (partial)"
    else: verdict="NOT CLEARLY PROMISED"
    return sl,nl,verdict,sig_str

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

def get_antardasha_table(dasha_info):
    ml=dasha_info['current_md']; my=dasha_info['md_total_years']
    if ml=="Unknown" or my==0: return []
    mi=DASHA_ORDER.index(ml); ad_seq=DASHA_ORDER[mi:]+DASHA_ORDER[:mi]
    cursor=dasha_info['md_start']; lines=[]; cur_al=dasha_info['current_ad']
    for al in ad_seq:
        ay=(my*DASHA_YEARS[al])/120.0; ad_end=cursor+timedelta(days=ay*YEAR_DAYS)
        marker=" ◀ NOW" if al==cur_al else ""
        lines.append(f"  {ml}/{al}: {cursor.strftime('%b %Y')} → {ad_end.strftime('%b %Y')}{marker}")
        cursor=ad_end
    return lines

def d2_sign_index(lon): s=sign_index_from_lon(lon); d=lon%30; return (4 if d<15 else 3) if s%2==0 else (3 if d<15 else 4)
def d3_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)//10)*4)%12
def d4_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)//7.5)*3)%12
def saptamsa_sign_index(lon): s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/7)); return ((s if s%2==0 else (s+6)%12)+slot)%12
def navamsa_sign_index(lon): s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/9)); start=s if s in MOVABLE_SIGNS else ((s+8)%12 if s in FIXED_SIGNS else (s+4)%12); return (start+slot)%12
def dasamsa_sign_index(lon): s=sign_index_from_lon(lon); slot=int((lon%360%30)//3); return ((s if s%2==0 else (s+8)%12)+slot)%12
def dwadasamsa_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%360%30)//2.5))%12
def d60_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)*2))%12

def get_moon_lon_from_profile(profile):
    d=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    t=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd,_,__=local_to_julian_day(d,t,profile['tz']); lon,_,_=get_planet_metrics(jd,PLANETS["Moon"]); return lon

# ══════════════════════════════════════════════════════
# MASTER DOSSIER GENERATOR
# ══════════════════════════════════════════════════════
def generate_astrology_dossier(profile,include_d60=False,compact=False):
    lat,lon,tz_name=profile['lat'],profile['lon'],profile['tz']
    name,place_text=profile['name'],profile['place']
    prof_date=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    prof_time=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd_ut,dt_local,_=local_to_julian_day(prof_date,prof_time,tz_name)
    lagna_lon,_=get_lagna_and_cusps(jd_ut,lat,lon)
    placidus_cusps=get_placidus_cusps(jd_ut,lat,lon)
    planet_data={pn:get_planet_metrics(jd_ut,pid) for pn,pid in PLANETS.items()} # (lon, lat, speed)
    r_lon=get_rahu_longitude(jd_ut); k_lon=(r_lon+180.0)%360
    dasha_info=build_vimshottari_timeline(dt_local,planet_data["Moon"][0],datetime.now(ZoneInfo(tz_name)))
    panchanga=get_panchanga(planet_data["Sun"][0],planet_data["Moon"][0],dt_local)
    lagna_sidx=sign_index_from_lon(lagna_lon)
    moon_sidx=sign_index_from_lon(planet_data["Moon"][0])
    mars_sidx=sign_index_from_lon(planet_data["Mars"][0])
    
    ll_chain=get_lagna_lord_chain(lagna_sidx,planet_data,r_lon,k_lon)
    conjunctions=get_conjunctions(lagna_sidx,planet_data,r_lon,k_lon)
    mutual_asp=get_mutual_aspects(lagna_sidx,planet_data,r_lon,k_lon)
    graha_yuddha=detect_graha_yuddha(planet_data)
    f_ben,f_mal,yogak,f_neutral=get_functional_planets(lagna_sidx)
    manglik=check_manglik_dosha(lagna_sidx,moon_sidx,mars_sidx)
    sade_sati=calculate_sade_sati(moon_sidx)
    ak,ak_deg,amk,amk_deg=get_chara_karakas(planet_data)
    yogas_present,yogas_absent=detect_yogas(lagna_sidx,moon_sidx,planet_data,r_lon,k_lon)
    ad_table=get_antardasha_table(dasha_info)
    house_summary=get_house_strength_summary(lagna_sidx,planet_data,r_lon,k_lon,placidus_cusps)
    kp7_sl,kp7_nl,kp7_verdict,kp7_sigs=get_kp_verdict(placidus_cusps[6],lagna_sidx,planet_data,r_lon,k_lon,{2,7,11},"Marriage")
    kp10_sl,kp10_nl,kp10_verdict,kp10_sigs=get_kp_verdict(placidus_cusps[9],lagna_sidx,planet_data,r_lon,k_lon,{1,6,10,11},"Career")
    lat_lbl=f"{abs(lat):.5f}{'N' if lat>=0 else 'S'}"; lon_lbl=f"{abs(lon):.5f}{'E' if lon>=0 else 'W'}"
    
    lines=[]
    lines.append(f"{'═'*60}\nKUNDLI DOSSIER — {name.upper()}")
    lines.append(f"System: Swiss Ephemeris | Lahiri Ayanamsa | Whole Sign + Placidus KP\n{'═'*60}")
    lines.append(f"\n━━━ BIRTH DATA & PANCHANGA ━━━")
    lines.append(f"Name: {name} | Place: {place_text}")
    lines.append(f"Local Time: {dt_local.strftime('%d %b %Y, %I:%M %p')} ({panchanga['weekday']})")
    lines.append(f"Coordinates: {lat_lbl}, {lon_lbl} | Timezone: {tz_name}")
    lines.append(f"Tithi: {panchanga['tithi']} | Yoga: {panchanga['yoga']} | Karana: {panchanga['karana']}")
    lines.append(f"\n━━━ LAGNA FOUNDATION ━━━")
    lines.append(f"Ascendant (Lagna): {sign_name(lagna_sidx)} {format_dms(lagna_lon%30)}")
    lines.append(f"LAGNA LORD CHAIN: {ll_chain}")
    lines.append(f"Manglik: {manglik}")
    lines.append(f"\n━━━ FUNCTIONAL PLANETS FOR {sign_name(lagna_sidx).upper()} LAGNA ━━━")
    lines.append("(Based on house rulership — DO NOT override these classifications)")
    lines.append(f"  Yogakarakas (most auspicious, rule both Kendra+Trikona): {', '.join(yogak) if yogak else 'None'}")
    lines.append(f"  Functional Benefics (Trikona lords): {', '.join(f_ben) if f_ben else 'None'}")
    lines.append(f"  Functional Malefics (Trika lords, no Trikona): {', '.join(f_mal) if f_mal else 'None'}")
    lines.append(f"  Neutral (primarily Kendra or dual-role): {', '.join(f_neutral) if f_neutral else 'None'}")
    lines.append(f"\n━━━ PLANETARY POSITIONS — D1 RASI ━━━")
    house_occupants={i:[] for i in range(1,13)}
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        plon,plat,pspd=planet_data[pname]; sidx=sign_index_from_lon(plon); house=whole_sign_house(lagna_sidx,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); avastha=get_baladi_avastha(plon); sub_lord=get_kp_sub_lord(plon)
        aspects=get_vedic_aspects(pname,house); house_occupants[house].append(pname)
        tags=[]
        if pspd<0 and pname not in ["Sun","Moon"]: tags.append("Retrograde")
        if pname in COMBUST_DEGREES:
            diff=min(abs(plon-planet_data["Sun"][0]),360-abs(plon-planet_data["Sun"][0]))
            if diff<=COMBUST_DEGREES[pname]: tags.append("Combust")
        if pname in DIGNITIES:
            if sidx==DIGNITIES[pname][0]: tags.append("Exalted")
            elif sidx==DIGNITIES[pname][1]: tags.append("Debilitated")
        if pname in OWN_SIGNS and sidx in OWN_SIGNS[pname]: tags.append("Own Sign")
        tag_str=f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {pname}: H{house}|{sign_name(sidx)} {format_dms(plon%30)}{tag_str}|Avastha:{avastha}|Nak:{nak}(NL:{nak_lord} SL:{sub_lord} Pada:{pada})|Aspects:H{aspects}")
    for pname,plon in [("Rahu",r_lon),("Ketu",k_lon)]:
        sidx=sign_index_from_lon(plon); house=whole_sign_house(lagna_sidx,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); sub_lord=get_kp_sub_lord(plon)
        aspects=get_vedic_aspects(pname,house); house_occupants[house].append(pname)
        lines.append(f"  {pname}: H{house}|{sign_name(sidx)} {format_dms(plon%30)} [Retrograde]|Nak:{nak}(NL:{nak_lord} SL:{sub_lord} Pada:{pada})|Aspects:H{aspects}")
    
    lines.append(f"\n━━━ PRE-COMPUTED CRITICAL FACTS ━━━")
    lines.append("(Mathematically verified — DO NOT re-derive or override any of these)")
    lines.append("\n[CONJUNCTIONS]")
    for c in conjunctions: lines.append(f"  ✓ {c}")
    if not conjunctions: lines.append("  None")
    lines.append("\n[MUTUAL ASPECTS]")
    for m in mutual_asp: lines.append(f"  ↔ {m}")
    if not mutual_asp: lines.append("  None")
    
    lines.append("\n[GRAHA YUDDHA — PLANETARY WAR]")
    if graha_yuddha:
        for winner,loser,deg in graha_yuddha:
            lines.append(f"  ⚔️ {winner} vs {loser} (separation: {deg}°) — {winner} WINS the war (higher celestial latitude).")
            lines.append(f"     → {loser}'s significations are weakened/suppressed despite its house placement.")
            lines.append(f"     → {winner}'s significations are amplified.")
    else: lines.append("  No Graha Yuddha in this chart.")
    
    lines.append("\n[NEECHA BHANGA — DEBILITATION CANCELLATION]")
    nb_found=False
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        psidx=sign_index_from_lon(planet_data[pname][0])
        if pname in DIGNITIES and psidx==DIGNITIES[pname][1]:
            nb_found=True
            conds=check_neecha_bhanga(pname,lagna_sidx,moon_sidx,planet_data,r_lon,k_lon)
            if conds:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NEECHA BHANGA APPLIES.")
                for c in conds: lines.append(f"    ✓ {c}")
                lines.append(f"    → INTERPRET AS: Raja Yoga quality. NOT weak.")
            else:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NO NEECHA BHANGA.")
                lines.append(f"    → INTERPRET AS: Genuinely weakened.")
    if not nb_found: lines.append("  No debilitated planets.")
    
    lines.append("\n[YOGA VERDICTS — PRESENT ✓]")
    for yname,ydesc in yogas_present: lines.append(f"  ✓ {yname}: {ydesc}")
    if not yogas_present: lines.append("  None detected.")
    lines.append("[YOGA VERDICTS — ABSENT ✗ (do NOT mention these in the reading)]")
    for ya in yogas_absent: lines.append(f"  ✗ {ya}")
    
    lines.append("\n[JAIMINI KARAKAS]")
    lines.append(f"  Atmakaraka (soul/self): {ak} ({ak_deg:.2f}° within sign)")
    lines.append(f"  Amatyakaraka (mind/career): {amk} ({amk_deg:.2f}° within sign)")
    
    lines.append(f"\n━━━ HOUSE STRENGTH SUMMARY ━━━")
    lines.append("(Pre-computed verdicts for key life domains — use these directly)")
    for hs in house_summary: lines.append(f"  {hs}")
    
    lines.append(f"\n━━━ HOUSE RULERSHIP MAP ━━━")
    for h in range(1,13):
        h_sidx=(lagna_sidx+h-1)%12; h_lord=SIGN_LORDS_MAP[h_sidx]
        ll_house=get_planet_house(h_lord,lagna_sidx,planet_data,r_lon,k_lon)
        occ=", ".join(house_occupants[h]) if house_occupants[h] else "Empty"
        lines.append(f"  H{h:02d}({sign_name(h_sidx)}): Lord={h_lord}(H{ll_house}) | Occupants: {occ}")
        
    if not compact:
        lines.append(f"\n━━━ KP — PLACIDUS CUSPS ━━━")
        lines.append("(Layer 2: Use ONLY for event timing and promise — not for character analysis)")
        for h in range(1,13):
            clon=placidus_cusps[h-1]; csidx=sign_index_from_lon(clon)
            _,cnl,_=nakshatra_info(clon); csl=get_kp_sub_lord(clon)
            lines.append(f"  H{h:02d}: {sign_name(csidx)} {format_dms(clon%30)} | NL:{cnl} | SL:{csl}")
        lines.append("\n[KP EVENT VERDICTS — PRE-COMPUTED]")
        lines.append(f"  ▶ MARRIAGE: 7th Cusp SL={kp7_sl}(NL:{kp7_nl}) | Signifies: {kp7_sigs} | VERDICT: {kp7_verdict}")
        lines.append(f"    Rule: Promised if SL signifies H2(family)+H7(spouse)+H11(fulfillment)")
        lines.append(f"  ▶ CAREER:   10th Cusp SL={kp10_sl}(NL:{kp10_nl}) | Signifies: {kp10_sigs} | VERDICT: {kp10_verdict}")
        lines.append(f"    Rule: Promised if SL signifies H1+H6+H10+H11")
        
    lines.append(f"\n━━━ DIVISIONAL CHARTS ━━━")
    all_pnames=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    d2,d3,d4,d7,d9,d10,d12,d60=[],[],[],[],[],[],[],[]
    for pn in all_pnames:
        pl=get_planet_lon(pn,planet_data,r_lon,k_lon)
        d2.append(f"{pn}:{sign_name(d2_sign_index(pl))}"); d3.append(f"{pn}:{sign_name(d3_sign_index(pl))}")
        d4.append(f"{pn}:{sign_name(d4_sign_index(pl))}"); d7.append(f"{pn}:{sign_name(saptamsa_sign_index(pl))}")
        d9.append(f"{pn}:{sign_name(navamsa_sign_index(pl))}"); d10.append(f"{pn}:{sign_name(dasamsa_sign_index(pl))}")
        d12.append(f"{pn}:{sign_name(dwadasamsa_sign_index(pl))}")
        if include_d60: d60.append(f"{pn}:{sign_name(d60_sign_index(pl))}")
    lines.append(f"  D9  Navamsa  (Marriage/Dharma): {', '.join(d9)}")
    lines.append(f"  D10 Dasamsa  (Career/Status):   {', '.join(d10)}")
    lines.append(f"  D2  Hora     (Wealth):          {', '.join(d2)}")
    lines.append(f"  D3  Drekkana (Siblings/Courage):{', '.join(d3)}")
    lines.append(f"  D4  Chaturt  (Property/Luck):   {', '.join(d4)}")
    lines.append(f"  D7  Saptam   (Children):        {', '.join(d7)}")
    lines.append(f"  D12 Dwadam   (Parents/Roots):   {', '.join(d12)}")
    if include_d60: lines.append(f"  D60 Shashtiam(Karma/Fate):      {', '.join(d60)}")
    
    lines.append(f"\n━━━ VIMSHOTTARI DASHA TIMING ━━━")
    lines.append(f"Birth Nakshatra: {dasha_info['birth_nakshatra']} | Balance at birth: {dasha_info['balance_years']:.2f} yrs of {dasha_info['start_lord']}")
    lines.append(f"Current Mahadasha : {dasha_info['current_md']} ({dasha_info['md_start'].strftime('%b %Y')} → {dasha_info['md_end'].strftime('%b %Y')})")
    lines.append(f"Current Antardasha: {dasha_info['current_ad']} ({dasha_info['ad_start'].strftime('%b %Y')} → {dasha_info['ad_end'].strftime('%b %Y')})")
    lines.append(f"Current Pratyantar: {dasha_info['current_pd']} ({dasha_info['pd_start'].strftime('%d %b %Y')} → {dasha_info['pd_end'].strftime('%d %b %Y')})")
    lines.append(f"\nFULL ANTARDASHA SEQUENCE IN {dasha_info['current_md'].upper()} MAHADASHA:")
    lines.append("(Use ONLY these exact dates. Do not calculate independently.)")
    for row in ad_table: lines.append(row)
    
    lines.append(f"\n━━━ CURRENT AFFLICTIONS & TRANSITS ━━━")
    lines.append(f"Sade Sati: {sade_sati}")
    lines.append(f"Manglik Status: {manglik}")
    lines.append(f"Jaimini Atmakaraka: {ak} | Amatyakaraka: {amk}")
    
    return "\n".join(lines)

# ══════════════════════════════════════════════════════
# XML PROMPT ENGINEERING & GUARDRAILS
# ══════════════════════════════════════════════════════
GUARDRAILS=f"""
ROLE: Elite Vedic astrologer. All values PRE-COMPUTED by Swiss Ephemeris.
Your role is INTERPRETATION ONLY — never recalculate anything.

══ PRIMARY KNOWLEDGE BASE (MANDATORY — read before interpreting) ══
You MUST strictly adhere to the following PDF guides. Do NOT use outside knowledge:
1. {PDF_HTRH1}
2. {PDF_HTRH2}

══ THE TWO-LAYER METHOD (apply to every life domain) ══
LAYER 1 — PARASHARI ("What & Why"): Use D1 chart, house lords, yogas, divisional charts for character and karmic blueprint.
LAYER 2 — KP ("Whether & When"): Use Placidus cusp Sub-Lords and Antardasha Table for event promise and timing.
Synthesis: State Parashari first, then confirm/qualify with KP. If they conflict, note it.

══ ABSOLUTE LAWS (one violation invalidates the entire reading) ══
1. DATA IS IMMUTABLE: Every value is locked. Do NOT re-derive house lords, positions, KP Sub-Lords, yoga verdicts, karakas, or Dasha dates.
2. FUNCTIONAL PLANETS ARE PRE-CLASSIFIED: Use the FUNCTIONAL PLANETS section exactly. Do not reclassify.
3. GRAHA YUDDHA IS PRE-DECIDED: If a planet lost a war, its significations are suppressed. If it won, they are amplified.
4. CONJUNCTIONS ONLY FROM LIST: Use only the pre-listed conjunctions.
5. NEECHA BHANGA IS FINAL: APPLIES → treat as Raja Yoga. DOES NOT APPLY → genuinely weak.
6. YOGAS ARE FINAL: Only reference ✓ PRESENT yogas. Never mention ✗ ABSENT yogas.
7. DASHA DATES ARE LOCKED: Use ONLY the Antardasha Table dates.
8. HOUSE STRENGTH SUMMARY IS PRE-COMPUTED: Use those verdicts directly.
9. PROVE EVERY CLAIM: Format: "Saturn[H7, Exalted] sub-lords the 7th cusp, signifying H2+H7+H11, confirming..."
"""

def build_deep_analysis_prompt(dossier):
    return f"""<context>
<system_rules>
{GUARDRAILS}
</system_rules>
<task>
MISSION: Complete life reading. Each section MUST cite specific chart data.

## 1. Core Identity & Lagna
   DATA: Ascendant, LAGNA LORD CHAIN, FUNCTIONAL PLANETS classification, H1 occupants.
   PARASHARI: Personality, constitution, approach to life. KP: H1 cusp Sub-Lord.

## 2. Mind & Emotional World
   DATA: Moon (sign, house, nakshatra, Avastha, Sade Sati).
   PARASHARI: Emotional temperament. Note Moon Avastha quality directly.
   If Sade Sati ACTIVE: describe current phase and practical impact.

## 3. Career & Profession
   DATA: H10 lord/sign/occupants, D10, Amatyakaraka, HOUSE STRENGTH SUMMARY H10, KP Career Verdict.
   PARASHARI: Best professions, trajectory. KP: Apply the pre-computed Career Verdict exactly.

## 4. Wealth & Finances
   DATA: H2+H11 lords, D2 Hora, Dhana Yogas from YOGA VERDICTS, HOUSE STRENGTH SUMMARY H2+H11.

## 5. Relationships & Marriage
   DATA: H7 lord/sign, D9 Navamsa H7, HOUSE STRENGTH SUMMARY H7, KP Marriage Verdict.

## 6. Health & Longevity
   DATA: H1, H6, H8 lords and occupants. Note any GRAHA YUDDHA losers.

## 7. Current Dasha Phase
   DATA: Full Antardasha Table, Sade Sati, current MD/AD/PD.
   Analyse current combination. Identify next 2-3 sub-period shifts from the table. DO NOT generate new dates.

## 8. Practical Remedies
   Only for planets that are: Debilitated WITHOUT Neecha Bhanga, Combust, lost Graha Yuddha, or Retrograde in sensitive house. No remedies for strong planets.
</task>
<user_chart_data>
{dossier}
</user_chart_data>
</context>"""

def build_matchmaking_prompt(dossier_a,dossier_b,koota_score,manglik_cancellation):
    return f"""<context>
<system_rules>
{GUARDRAILS}
</system_rules>
<task>
MISSION: Definitive compatibility analysis.

## 1. Ashta Koota Guna Milan
   CRITICAL: Use this pre-computed score exactly — do NOT recalculate:
   {koota_score}
   Explain practical meaning of any Koota scoring 0.

## 2. Manglik Dosha
   Pre-computed verdict: {manglik_cancellation}

## 3. Parashari Compatibility (D1 + D9)
   Compare 7th house lords, signs, D9 charts. Check if charts mirror each other.
   Verify Lagna lord friendship/enmity.

## 4. KP Marriage Promise & Timing
   Apply each person's pre-computed KP Marriage Verdict. Use ONLY their Antardasha Tables for timing.

## 5. Long-Term Harmony & Friction
   Identify temperament clashes and specific houses that will cause friction.

## 6. Final Verdict
   Score out of 10 with evidence. List only genuinely required remedies.
</task>
<person_1_data>
{dossier_a}
</person_1_data>
<person_2_data>
{dossier_b}
</person_2_data>
</context>"""

def build_comparison_prompt(profiles_dossiers,criteria):
    prompt=f"<context>\n<system_rules>\n{GUARDRAILS}\n</system_rules>\n<task>\nMISSION: Compare individuals on listed parameters.\n\nPARAMETERS:\n"
    for c in criteria: prompt+=f"  - {c}\n"
    prompt+=("\nRULES:\n1. Rank all individuals per parameter, highest to lowest.\n"
             "2. Every rank requires specific evidence (planet, house, dignity, yoga, or KP verdict).\n"
             "3. Use Parashari for character/potential. Use KP+HOUSE STRENGTH SUMMARY for event-based parameters.\n"
             "4. Never reference ABSENT yogas.\n5. State final ranking as a numbered list then explain.\n</task>\n<profiles_data>\n")
    for i,(name,dossier) in enumerate(profiles_dossiers): prompt+=f"━━━ PROFILE {i+1}: {name.upper()} ━━━\n{dossier}\n\n"
    prompt += "</profiles_data>\n</context>"
    return prompt

def build_prashna_prompt(question,dossier):
    return f"""<context>
<system_rules>
{GUARDRAILS}
</system_rules>
<task>
MISSION: PRASHNA (Horary) reading — cast for this exact moment, for this question ONLY.
QUESTION: "{question}"

PRASHNA RULES:
1. Lagna and its lord = the querent.
2. Relevant house by question type:
   Career/Job=H10 | Marriage=H7 | Money=H2,H11 | Health=H1,H6 | Children=H5 | Property=H4 | Travel/Foreign=H9,H12 | Education=H4,H5 | Enemies/Legal=H6,H7
3. PARASHARI: Strong relevant house lord (in own/exalt, or Kendra/Trikona) → Favourable. Weak (debilitated, combust, H6/H8/H12) → Delay or denial.
4. KP: Apply the HOUSE STRENGTH SUMMARY verdict for the relevant house.
5. Moon's nakshatra and current dasha provide timing context.
6. MANDATORY FINAL LINE: "VERDICT: [Yes / No / Delayed] — [one sentence summary]"
</task>
<prashna_chart>
{dossier}
</prashna_chart>
</context>"""

def build_transit_prompt(dossier, cw):
    return f"""<context>
<system_rules>
{GUARDRAILS}
</system_rules>
<task>
MISSION: Gochara (Live Transit) overlay reading.
You are tasked with analyzing how today's live transiting planets are activating the user's locked natal chart.

1. Overlay the <live_transits> onto the <user_chart_data>.
2. Identify which natal houses the current transiting planets are occupying.
3. Note if any transiting retrograde planets are hitting sensitive natal points.
4. Synthesize the current Moon's Nakshatra ({cw['nakshatra']}) with the user's active Antardasha to predict the immediate 48-hour emotional and practical theme.
5. Deliver a targeted, highly specific daily/weekly forecast.
</task>
<live_transits>
Current Moon Sign: {cw['moon_sign']}
Current Moon Nakshatra: {cw['nakshatra']}
Retrograde Planets Today: {cw['retrogrades']}
All Ephemeris Positions Today: {cw['all_pos']}
</live_transits>
<user_chart_data>
{dossier}
</user_chart_data>
</context>"""

# ══════════════════════════════════════════════════════
# NUMEROLOGY ENGINE
# ══════════════════════════════════════════════════════
def _reduce(n,keep_master=True):
    if keep_master and n in [11,22,33]: return n
    while n>9:
        if keep_master and n in [11,22,33]: return n
        n=sum(int(d) for d in str(n))
    return n

def calculate_numerology_core(name,dob_str,system="Western (Pythagorean)"):
    y,m,d=map(int,dob_str.split('-'))
    num_map=PYTH_MAP if system=="Western (Pythagorean)" else CHALDEAN_MAP
    life_path=_reduce(_reduce(y)+_reduce(m)+_reduce(d))
    clean=name.lower().replace(" ",""); vowels=set('aeiou')
    dest_sum=soul_sum=pers_sum=0
    for char in clean:
        if char in num_map:
            val=num_map[char]; dest_sum+=val
            if char in vowels: soul_sum+=val
            else: pers_sum+=val
    return _reduce(life_path),_reduce(dest_sum),_reduce(soul_sum),_reduce(pers_sum)

def get_personal_year(dob_str,for_year=None):
    if for_year is None: for_year=get_local_today().year
    y,m,d=map(int,dob_str.split('-'))
    return _reduce(_reduce(m)+_reduce(d)+_reduce(for_year))

def get_personal_month(dob_str):
    py=get_personal_year(dob_str); cm=get_local_today().month
    return _reduce(py+_reduce(cm))

def get_personal_day(dob_str):
    pm=get_personal_month(dob_str); cd=get_local_today().day
    return _reduce(pm+_reduce(cd))

def get_pinnacle_cycles(dob_str):
    y,m,d=map(int,dob_str.split('-'))
    m_r = _reduce(m); d_r = _reduce(d); y_r = _reduce(y)
    lp_base = _reduce(y_r + m_r + d_r)
    
    # Pinnacles (Addition)
    p1 = _reduce(m_r + d_r); p2 = _reduce(d_r + y_r)
    p3 = _reduce(p1 + p2); p4 = _reduce(m_r + y_r)
    
    # Challenges (Subtraction)
    c1 = abs(m_r - d_r); c2 = abs(d_r - y_r)
    c3 = abs(c1 - c2); c4 = abs(m_r - y_r)
    
    d1_end = 36 - (_reduce(lp_base, keep_master=False)) # Base Life path reduction for timing
    d2_end = d1_end + 9; d3_end = d2_end + 9
    
    r1=(y, y+d1_end, p1, c1); r2=(y+d1_end, y+d2_end, p2, c2)
    r3=(y+d2_end, y+d3_end, p3, c3); r4=(y+d3_end, y+100, p4, c4)
    return r1,r2,r3,r4

def get_tarot_birth_card(dob_str):
    digits=[int(c) for c in dob_str.replace('-','') if c.isdigit()]
    total=sum(digits)
    while total>22: total=sum(int(d) for d in str(total))
    if total==22 or total==0: return MAJOR_ARCANA[0]
    return MAJOR_ARCANA[total-1]

def get_numerology_compatibility(name_a,dob_a,name_b,dob_b,system="Western (Pythagorean)"):
    lp_a,dst_a,soul_a,_=calculate_numerology_core(name_a,dob_a,system)
    lp_b,dst_b,soul_b,_=calculate_numerology_core(name_b,dob_b,system)
    score=0; notes=[]
    if lp_a==lp_b: score+=3; notes.append(f"Same Life Path ({lp_a}) — deeply aligned life purpose")
    elif abs(lp_a-lp_b)<=1 or {lp_a,lp_b} in [{1,9},{2,8},{3,6},{4,8},{5,9}]: score+=2; notes.append(f"Complementary Life Paths ({lp_a}/{lp_b})")
    else: score+=1; notes.append(f"Different Life Paths ({lp_a}/{lp_b}) — divergent core drives")
    if soul_a==soul_b: score+=3; notes.append(f"Matching Soul Urge ({soul_a}) — same inner desires")
    elif abs(soul_a-soul_b)<=2: score+=1; notes.append(f"Close Soul Urge ({soul_a}/{soul_b}) — similar inner world")
    if dst_a==dst_b: score+=2; notes.append(f"Same Destiny ({dst_a}) — very similar life missions")
    rating="Excellent" if score>=7 else "Good" if score>=5 else "Moderate" if score>=3 else "Challenging"
    return lp_a,soul_a,dst_a,lp_b,soul_b,dst_b,score,rating,notes

def build_numerology_prompt(name,dob_str,lp,dest,soul,pers,astro_dossier=None,user_q="",system="Western (Pythagorean)"):
    is_vedic=system=="Indian/Vedic (Chaldean)"
    sys_name="Chaldean (Indian/Vedic)" if is_vedic else "Pythagorean (Western)"
    py=get_personal_year(dob_str); pm=get_personal_month(dob_str); pd=get_personal_day(dob_str)
    r1,r2,r3,r4=get_pinnacle_cycles(dob_str)
    y,m,d=map(int,dob_str.split('-')); cur_age=get_local_today().year-y
    def which_pinnacle():
        for s,e,n,c in [r1,r2,r3,r4]:
            if s<=y+cur_age<e: return s,e,n,c
        return r4
    curr_pinn=which_pinnacle()
    
    pdf_req = f"  {PDF_NUMEV}" if is_vedic else f"  {PDF_NUMEW1}\n  {PDF_NUMEW2}"
    
    prompt=f"""<context>
<system_rules>
MISSION: Master Numerologist — {sys_name} system.
All rules, interpretations, and meanings MUST come strictly from:
{pdf_req}
Do NOT contradict these PDFs. 
CRITICAL: The core numbers below are PRE-COMPUTED and LOCKED. DO NOT recalculate them.
</system_rules>
<user_data>
Subject: {name.upper()} | DOB: {dob_str} | System: {sys_name}
Life Path   : {lp}
Destiny     : {dest}
Soul Urge   : {soul}
Personality : {pers}
Personal Year (current): {py}
Personal Month: {pm} | Personal Day: {pd}
</user_data>
<pinnacle_cycles>
Pinnacle 1: Number {r1[2]} (Challenge: {r1[3]}) | Ages ~{r1[0]-y}–{r1[1]-y}
Pinnacle 2: Number {r2[2]} (Challenge: {r2[3]}) | Ages ~{r2[0]-y}–{r2[1]-y}
Pinnacle 3: Number {r3[2]} (Challenge: {r3[3]}) | Ages ~{r3[0]-y}–{r3[1]-y}
Pinnacle 4: Number {r4[2]} (Challenge: {r4[3]}) | Ages ~{r4[0]-y} onwards
Active Pinnacle Right Now: Pinnacle Number {curr_pinn[2]}, Challenge Number {curr_pinn[3]}
</pinnacle_cycles>
<task>"""
    if astro_dossier:
        prompt+=f"\n══ ASTRO-NUMEROLOGY CROSS-REFERENCE ══\nAlso use: {PDF_HTRH1} and {PDF_HTRH2} for astrology.\nEXPLICIT SYNTHESIS REQUIRED:\n  - Life Path {lp} vs Lagna lord placement.\n  - Destiny {dest} vs Amatyakaraka.\n  - Soul Urge {soul} vs Moon sign.\nState explicitly where both systems AGREE and where they DIVERGE.\n</task>\n<astrology_dossier>\n{astro_dossier}\n</astrology_dossier>"
    else: prompt+="\nDELIVER A COMPLETE REPORT:\n1. Life Path\n2. Destiny\n3. Soul Urge\n4. Personality\n5. Personal Year Forecast\n6. Active Pinnacle Cycle & the Challenge to overcome.\n</task>"
    
    if user_q: prompt+=f"\n<user_query>{user_q}</user_query>"
    prompt += "\n</context>"
    return prompt

def build_numerology_compatibility_prompt(na,da,lpa,soula,dsta,nb,db,lpb,soulb,dstb,score,rating,notes,system):
    is_vedic=system=="Indian/Vedic (Chaldean)"
    pdf_ref=f"  {PDF_NUMEV}" if is_vedic else f"  {PDF_NUMEW1}\n  {PDF_NUMEW2}"
    return f"""<context>
<system_rules>
MISSION: Numerology Compatibility Analysis — {system}.
All rules MUST come from:\n{pdf_ref}\nPre-computed numbers are LOCKED. Do NOT recalculate.
</system_rules>
<user_data>
PERSON 1: {na.upper()} (DOB: {da}) -> Life Path: {lpa} | Soul Urge: {soula} | Destiny: {dsta}
PERSON 2: {nb.upper()} (DOB: {db}) -> Life Path: {lpb} | Soul Urge: {soulb} | Destiny: {dstb}
SCORE: {score}/8 — {rating}
Notes: {', '.join(notes)}
</user_data>
<task>
DELIVER:
1. Life Path compatibility and dynamic
2. Soul Urge alignment
3. Destiny compatibility
4. Overall verdict & advice
5. Potential strengths AND friction points
6. Final Score out of 10
</task>
</context>"""

# ══════════════════════════════════════════════════════
# TAROT PROMPT BUILDERS
# ══════════════════════════════════════════════════════
TAROT_MODES={"General Guidance":{"roles":["Situation / Past","Challenge / Present","Advice / Future"],"instruction":"General life overview — where they are, what blocks them, best path forward."},
 "Love & Dynamics":{"roles":["Your Energy","Their Energy","The Connection / Outcome"],"instruction":"Read through the lens of a relationship or emotional dynamic."},
 "Decision / Two Paths":{"roles":["Path A","Path B","Hidden Factor / Recommendation"],"instruction":"Contrast paths. Card 3 is the deciding weight or hidden truth."}}

def build_tarot_prompt(question,c1,s1,c2,s2,c3,s3,mode="General Guidance"):
    cfg=TAROT_MODES.get(mode,TAROT_MODES["General Guidance"]); r1,r2,r3=cfg["roles"]
    return f"""<context>
<system_rules>
MISSION: Expert, intuitive Tarot Reader.
All meanings and logic MUST come from: {PDF_TGUIDE}
Trust your training from the PDF. Do not second-guess card meanings.
</system_rules>
<spread_data>
Three-Card Spread ({mode}) — cryptographically randomised:
  1. {r1}: {c1} ({s1})
  2. {r2}: {c2} ({s2})
  3. {r3}: {c3} ({s3})
</spread_data>
<task>
Question: "{question}"
Focus: {cfg['instruction']}
RULES:
1. SYNERGY: Analyse card-to-card interplay.
2. REVERSED: Interpret its energy as blocked, internalised, or delayed.
3. FORMAT: Overall Summary -> Card 1 -> Card 2 -> Card 3 -> Combined Message -> Action Step -> One-Line Takeaway.
</task>
</context>"""

def build_yesno_prompt(question,card,state):
    return f"""<context><system_rules>MISSION: Yes/No Oracle reading. Meanings MUST come from: {PDF_TGUIDE}</system_rules><task>Question: "{question}"\nCard Drawn: {card} ({state})\nRULES:\n- Upright = Yes; Reversed = No (nuance by card).\n- Major Arcana carry weight.\nDELIVER: Verdict (Yes/Likely Yes/Unclear/Likely No/No), Why, Condition, Takeaway.</task></context>"""

def build_celtic_cross_prompt(question,cards,states):
    lines="\n".join(f"  {CELTIC_CROSS_POSITIONS[i]}: {cards[i]} ({states[i]})" for i in range(10))
    return f"""<context>
<system_rules>MISSION: Expert Celtic Cross Tarot reading. Interpretations MUST come from: {PDF_TGUIDE}</system_rules>
<spread_data>\n10-Card Celtic Cross:\n{lines}\n</spread_data>
<task>Question: "{question}"\nRULES:\n1. Core tension = Cards 1 & 2.\n2. Cards 3-6 = Context. Cards 7-10 = Staff.\n3. FORMAT: Core Message -> Position Reading -> Patterns -> Narrative -> Guidance -> Takeaway.</task>
</context>"""

def build_daily_tarot_prompt(card,state):
    return f"""<context><system_rules>MISSION: Daily Guidance reading. Meanings MUST come from: {PDF_TGUIDE}</system_rules><task>Today's card: {card} ({state})\nDeliver: Meaning, Energy, Best action, Watch out for, One-Line Mantra.</task></context>"""

# ══════════════════════════════════════════════════════
# HOROSCOPE TEXT (local, no AI)
# ══════════════════════════════════════════════════════
def generate_horoscope_text(sign,mode,date_val):
    import random; rng=random.Random(f"{sign}_{mode}_{date_val}")
    g=["The cosmos is aligning in your favor. Clarity arrives where there was confusion.","Patience is your best friend right now. Let things unfold naturally.","You are radiating positive energy — others are drawn to your presence.","A period of introspection is needed. Quiet reflection will yield insights.","Unexpected news might shift your perspective. Stay adaptable.","Your creative energy is at a peak. Channel it into something meaningful.","Rest is needed. Don't overcommit — your energy is precious.","A fantastic time to set new goals. The universe supports your ambitions."]
    l=["Communication flows easily. Express your true feelings.","A slight misunderstanding is possible. Approach with empathy.","Romantic energy surrounds you. Plan something thoughtful.","Focus on self-love today. You deserve care and kindness.","A past connection may resurface. Proceed with an open but discerning heart."]
    c=["Your hard work is catching the right attention. Recognition is near.","A challenge at work tests your patience. Stay calm, think strategically.","Collaboration is your superpower today. Reach out to a colleague.","A brilliant idea strikes. Write it down — timing is perfect.","Avoid impulsive financial decisions. Research before committing."]
    return f"**General:** {rng.choice(g)}\n\n**Love & Relationships:** {rng.choice(l)}\n\n**Career & Finance:** {rng.choice(c)}"

# ══════════════════════════════════════════════════════
# CSS INJECTION (Polished Glass, Pulses, Overflows)
# ══════════════════════════════════════════════════════
def inject_css():
    st.markdown(textwrap.dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global Theming & Chrome Hiding */
    [data-testid="stHeader"] {display: none !important;}
    html,body,.stApp{background:radial-gradient(circle at 15% 50%,#1a0f2e,#0c0814 60%,#050308 100%)!important;font-family:'Inter',sans-serif!important;color:#e2e0ec!important}
    #MainMenu,footer{visibility:hidden}
    h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;color:#fff}
    .block-container{padding:1rem 1.25rem 5rem!important;max-width:960px!important}
    
    /* Inputs & Containers */
    [data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,0.03)!important;backdrop-filter:blur(12px)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:16px!important;box-shadow:0 8px 32px rgba(0,0,0,0.3)!important}
    .stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div,.stDateInput>div>div>input,.stTextArea>div>div>textarea{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(255,255,255,0.12)!important;border-radius:10px!important;color:#eceaf4!important;font-family:'Inter',sans-serif!important}
    
    /* Buttons */
    div[data-testid="stButton"]>button{border-radius:10px!important;font-weight:600!important;transition:all 0.3s ease!important;border:1px solid rgba(255,255,255,0.1)!important;font-family:'Inter',sans-serif!important}
    div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,rgba(144,98,222,0.85),rgba(205,140,80,0.85))!important;border:none!important;color:#fff!important}
    div[data-testid="stButton"]>button[kind="primary"]:hover{transform:translateY(-2px)!important;box-shadow:0 8px 20px rgba(144,98,222,0.4)!important}
    div[data-testid="stButton"]>button:not([kind="primary"]){background:rgba(255,255,255,0.05)!important;color:#e2e0ec!important}
    div[data-testid="stButton"]>button:not([kind="primary"]):hover{background:rgba(255,255,255,0.1)!important;color:#fff!important}
    
    /* Code block container restrictions */
    [data-testid="stExpander"]{border:1px solid rgba(255,255,255,0.1)!important;border-radius:12px!important;background:rgba(0,0,0,0.2)!important}
    .stCodeBlock{border-radius:12px!important;border:1px solid rgba(255,255,255,0.1)!important}
    
    /* ── BOTTOM NAV (mobile only) ── */
    .bot-nav{display:none;position:fixed;bottom:0;left:0;right:0;z-index:9999;background:rgba(10,6,22,0.95);backdrop-filter:blur(20px);border-top:1px solid rgba(144,98,222,0.3);padding:8px 0 env(safe-area-inset-bottom,8px)}
    .bot-nav-inner{display:flex;justify-content:space-around;align-items:center;max-width:600px;margin:0 auto}
    .bnav-item{display:flex;flex-direction:column;align-items:center;gap:2px;padding:4px 10px;border-radius:10px;cursor:pointer;border:none;background:transparent;color:rgba(200,195,220,0.55);font-family:'Inter',sans-serif;font-size:10px;font-weight:500;transition:all 0.2s;min-width:56px}
    .bnav-item.active{color:#c990e0}
    .bnav-item:hover{color:#e0d0f5;background:rgba(144,98,222,0.15)}
    .bnav-icon{font-size:20px;line-height:1}
    @media(max-width:768px){.bot-nav{display:block}}
    
    /* ── SIDEBAR improvements ── */
    [data-testid="stSidebar"]{background:rgba(8,4,20,0.97)!important;border-right:1px solid rgba(144,98,222,0.2)!important}
    [data-testid="stSidebar"] [data-testid="stButton"]>button{text-align:left!important;justify-content:flex-start!important;padding:10px 16px!important}
    
    /* ── Feature cards ── */
    .feat-card{border-radius:14px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.04);padding:1.2rem;transition:all 0.2s;position:relative;overflow:hidden}
    .feat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--c)}
    .feat-card:hover{border-color:rgba(255,255,255,0.15);transform:translateY(-2px)}
    .feat-icon{font-size:1.8rem;display:block;margin-bottom:.5rem}
    .feat-title{font-family:'Space Grotesk',sans-serif;font-size:.95rem;font-weight:600;color:#fff;margin:0 0 .3rem}
    .feat-desc{font-size:.78rem;color:rgba(190,185,210,0.6);margin:0;line-height:1.55}
    
    /* ── Default badge Pulse ── */
    @keyframes pulse { 0% { opacity: 0.8; box-shadow: 0 0 0 0 rgba(205,140,80,0.4); } 70% { opacity: 1; box-shadow: 0 0 0 4px rgba(205,140,80,0); } 100% { opacity: 0.8; } }
    .default-badge{background:rgba(205,140,80,0.2);border:1px solid rgba(205,140,80,0.4);color:#d4944a;font-size:.7rem;padding:1px 8px;border-radius:10px;font-weight:600; animation: pulse 2s infinite;}
    
    .prof-banner{background:linear-gradient(135deg,rgba(144,98,222,0.2),rgba(205,140,80,0.1));border:1px solid rgba(144,98,222,0.3);border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1.5rem}
    .stat-val{font-family:'Space Grotesk',sans-serif;font-size:1.4rem;font-weight:700;color:#fff}
    .stat-lbl{font-size:.72rem;color:rgba(190,185,210,0.55);margin-top:2px}
    </style>
    """),unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# COPY BUTTON
# ══════════════════════════════════════════════════════
def render_copy_button(text_to_copy,label="✨ Copy Prompt to Clipboard"):
    b64=base64.b64encode(text_to_copy.encode("utf-8")).decode("utf-8")
    uid=secrets.token_hex(4)
    components.html(f"""
    <div style="width:100%;padding:0 2px;">
    <button id="cpyBtn_{uid}" onclick="copyIt_{uid}()" style="background:linear-gradient(135deg,rgba(144,98,222,0.85),rgba(205,140,80,0.85));border:1px solid rgba(255,255,255,0.2);color:white;padding:14px 20px;font-size:15px;cursor:pointer;border-radius:12px;font-weight:600;width:100%;box-shadow:0 4px 15px rgba(0,0,0,0.3);font-family:'Inter',sans-serif;transition:all 0.3s">{label}</button>
    </div>
    <script>
    async function copyIt_{uid}(){{
        const btn=document.getElementById("cpyBtn_{uid}");
        const text=decodeURIComponent(escape(atob('{b64}')));
        try{{await navigator.clipboard.writeText(text);}}
        catch(e){{const el=document.createElement('textarea');el.value=text;el.style.position='fixed';el.style.opacity='0';document.body.appendChild(el);el.select();document.execCommand('copy');document.body.removeChild(el);}}
        btn.innerHTML="✅ Copied!";btn.style.background="linear-gradient(135deg,rgba(46,184,134,0.85),rgba(26,138,98,0.85))";
        setTimeout(()=>{{btn.innerHTML="{label}";btn.style.background="linear-gradient(135deg,rgba(144,98,222,0.85),rgba(205,140,80,0.85))"}},3000);
    }}
    </script>""",height=58)

def render_post_generation(prompt):
    st.markdown("---")
    st.markdown("""<div style='background:rgba(144,98,222,0.1);border:1px solid rgba(144,98,222,0.3);border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;'>
    <h4 style='margin:0 0 .5rem;color:#fff;'>💡 How to use</h4>
    <p style='color:#beb9cd;font-size:.9rem;margin:0;line-height:1.6;'>1. Click <b>Copy</b> → 2. Open an AI (buttons below) → 3. <b>Paste & Send</b></p></div>""",unsafe_allow_html=True)
    render_copy_button(prompt); st.markdown("<br>",unsafe_allow_html=True)
    a1,a2,a3=st.columns(3)
    a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
    a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)
    a3.link_button("🚀 Grok","https://grok.com/",use_container_width=True)
    with st.expander("📄 View Raw Prompt",expanded=False): st.code(prompt,language="text")

# ══════════════════════════════════════════════════════
# BOTTOM NAV
# ══════════════════════════════════════════════════════
def render_bottom_nav():
    items=[("🌌","Home","Dashboard"),("🔮","Oracle","The Oracle"),("🃏","Cards","Mystic Tarot"),("🔢","Numbers","Numerology"),("👤","Profiles","Saved Profiles")]
    html='<div class="bot-nav"><div class="bot-nav-inner">'
    for icon,label,page in items:
        active="active" if st.session_state.nav_page==page else ""
        html+=f'<button class="bnav-item {active}" onclick="setPage(\'{page}\')" title="{label}"><span class="bnav-icon">{icon}</span><span>{label}</span></button>'
    html+='</div></div>'
    st.markdown(html,unsafe_allow_html=True)
    components.html("""<script>
    function setPage(page){
        window.parent.postMessage({type:'streamlit:setComponentValue',value:page},'*');
        var btns=window.parent.document.querySelectorAll('[data-testid="stButton"] button');
        btns.forEach(function(b){if(b.innerText.trim()==='nav_trigger_'+page){b.click();}});
    }
    </script>""",height=0,width=0)

# ══════════════════════════════════════════════════════
# TAROT OVERLAY (FIXED & SCALED)
# ══════════════════════════════════════════════════════
def get_filename(n): return n.lower().replace(' ','')+'.jpg'
BASE_URL="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/tarot/"
def render_tarot_overlay(cards,states,num=3):
    urls=[f"{BASE_URL}{get_filename(c)}" for c in cards]
    card_back=f"{BASE_URL}tarotrear.png"
    cards_html="".join(f'<div class="t-card-wrapper w{i+1}"><div class="t-card-inner i{i+1}"><div class="t-card-back"></div><div class="t-card-front f{i+1}" style="background-image:url(\'{urls[i]}\');{"transform:rotate(180deg);" if states[i]=="Reversed" else ""}"></div></div></div>' for i in range(num))
    
    st.markdown(f"""
    <style>
    .tarot-stage{{position:relative;width:100%;max-width:600px;margin:0 auto 1.5rem;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.6);background:linear-gradient(45deg,#1a0f2e,#0c0814)}}
    .vid-d,.vid-m{{width:100%;display:block;object-fit:cover;opacity:.8}}
    .vid-d{{aspect-ratio:1440/1678}}.vid-m{{display:none;aspect-ratio:24/41}}
    .card-container{{position:absolute;bottom:2%;width:100%;display:flex;justify-content:center;perspective:1000px;flex-wrap:wrap;padding:0 5%;}}
    .t-card-inner{{width:100%;height:100%;position:relative;transform-style:preserve-3d;transform:rotateY(0deg)}}
    .t-card-front,.t-card-back{{position:absolute;width:100%;height:100%;backface-visibility:hidden;border-radius:8px;box-shadow:0 5px 20px rgba(0,0,0,.8);background-size:cover;background-position:center}}
    .t-card-back{{background-image:url('{card_back}');border:2px solid rgba(205,140,80,.5)}}
    .t-card-front{{transform:rotateY(180deg);border:2px solid rgba(205,140,80,.8)}}
    .scroll-prompt{{position:absolute;bottom:0.5%;width:100%;text-align:center;color:#fff;font-size:0.85rem;font-weight:600;opacity:0;text-shadow:0 2px 5px rgba(0,0,0,0.8);letter-spacing:1px;font-family:'Space Grotesk',sans-serif;}}
    
    /* Layout Logic */
    .num-10 .t-card-wrapper {{ width: 15%; margin: 0 1.5% 2% 1.5%; aspect-ratio: 2/3; opacity: 0; }} /* 5 per row */
    .num-3 .t-card-wrapper {{ width: 28%; margin: 0 2%; aspect-ratio: 2/3; opacity: 0; }}
    .num-1 .t-card-wrapper {{ width: 32%; aspect-ratio: 2/3; opacity: 0; }}
    
    @media(max-width:768px){{.vid-d{{display:none}}.vid-m{{display:block}}.num-10 .t-card-wrapper{{width:16%; margin: 0 1% 2% 1%;}}.num-3 .t-card-wrapper{{width:28%;margin: 0 1%;}}}}
    </style>
    <div class="tarot-stage">
        <video class="vid-d" autoplay loop muted playsinline><source src="{BASE_URL}tarotvid.mp4" type="video/mp4"></video>
        <video class="vid-m" autoplay loop muted playsinline><source src="{BASE_URL}tarotvideo.mp4" type="video/mp4"></video>
        <div class="card-container num-{num}">{cards_html}</div>
        <div class="scroll-prompt sp">✨ The cards have spoken. Scroll down for your reading. ✨</div>
    </div>""",unsafe_allow_html=True)
    
    flip_js="".join(f'gsap.to(doc.querySelector(".i{i+1}"),{{rotationY:180,duration:.8,delay:{1.2+i*0.2},ease:"back.out(1.7)"}}); ' for i in range(num))
    components.html(f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script>setTimeout(function(){{var doc=window.parent.document;
    gsap.to(doc.querySelectorAll({','.join([f'".w{i+1}"' for i in range(num)])}),{{y:0,opacity:1,duration:1,stagger:.2,ease:"power3.out",onStart:function(){{gsap.set(this.targets(),{{y:50}})}}}});
    {flip_js}
    gsap.to(doc.querySelector('.sp'), {{opacity:1, duration:1, delay:{1.5 + num*0.2}}});
    gsap.delayedCall({2.0 + num*0.2}, function() {{ window.parent.scrollBy({{top: 500, behavior: 'smooth'}}); }});
    }},150);</script>""",height=0,width=0)

# ══════════════════════════════════════════════════════
# PROFILE FORM HELPERS
# ══════════════════════════════════════════════════════
def sorted_profile_options():
    if not st.session_state.db: return []
    def_idx=st.session_state.default_profile_idx
    result=[]
    for i,p in enumerate(st.session_state.db):
        label=f"⭐ {p['name']} ({format_date_ui(p['date'])})" if i==def_idx else f"{p['name']} ({format_date_ui(p['date'])})"
        result.append((i,p,label))
    if def_idx is not None and 0<=def_idx<len(st.session_state.db):
        result.sort(key=lambda x: 0 if x[0]==def_idx else 1)
    return result

def render_profile_form(key_prefix,show_d60=True):
    if st.session_state.db: method=st.radio("Source",["Enter New Details","Saved Profile"],horizontal=True,key=f"rad_{key_prefix}",label_visibility="collapsed")
    else: method="Enter New Details"
    with st.container(border=True):
        if method=="Enter New Details":
            st.session_state[f"n_{key_prefix}"]=st.text_input("Name",key=f"wn_{key_prefix}")
            st.session_state[f"d_{key_prefix}"]=st.date_input("Date of Birth",date(2000,1,1),key=f"wd_{key_prefix}")
            t1,t2,t3=st.columns(3)
            with t1: st.session_state[f"hr_{key_prefix}"]=st.number_input("Hour",1,12,12,key=f"whr_{key_prefix}")
            with t2: st.session_state[f"mi_{key_prefix}"]=st.number_input("Min",0,59,0,key=f"wmi_{key_prefix}")
            with t3: st.session_state[f"ampm_{key_prefix}"]=st.selectbox("AM/PM",["AM","PM"],index=1,key=f"wa_{key_prefix}")
            u_place=st.text_input("Birth Place (City, Country)",key=f"wp_{key_prefix}")
            st.session_state[f"p_{key_prefix}"]=u_place
            manual=st.checkbox("Enter coordinates manually",key=f"wman_{key_prefix}")
            st.session_state[f"man_{key_prefix}"]=manual
            if u_place.strip() and not manual:
                geo=geocode_place(u_place.strip())
                if geo: st.success(f"📍 {geo[2]}")
                else: st.warning("Not found — check spelling or use manual coordinates.")
            if manual:
                c1,c2,c3=st.columns(3)
                with c1: st.session_state[f"lat_{key_prefix}"]=st.number_input("Lat",value=0.0,format="%.4f",key=f"wlat_{key_prefix}")
                with c2: st.session_state[f"lon_{key_prefix}"]=st.number_input("Lon",value=0.0,format="%.4f",key=f"wlon_{key_prefix}")
                with c3: st.session_state[f"tz_{key_prefix}"]=st.text_input("Timezone","Asia/Kolkata",key=f"wtz_{key_prefix}")
            st.session_state[f"save_{key_prefix}"]=st.checkbox("Save to Saved Profiles",key=f"wsave_{key_prefix}")
            if show_d60: st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time exact to minute (enables D60 karma chart)",key=f"wd60_{key_prefix}")
            return {"type":"new","idx":key_prefix}
        else:
            opts=sorted_profile_options()
            if not opts: return {"type":"empty_saved","idx":key_prefix}
            opt_labels=["— Select —"]+[x[2] for x in opts]
            sel=st.selectbox("Select Profile",opt_labels,key=f"sel_{key_prefix}",label_visibility="collapsed")
            if sel!="— Select —":
                _,p,_=opts[opt_labels.index(sel)-1]
                st.success(f"Loaded: **{p['name']}** 📍 {p['place'].split(',')[0]}")
                if show_d60: st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time exact",key=f"wd60_{key_prefix}")
                return {"type":"saved","data":p,"idx":key_prefix}
            return {"type":"empty_saved","idx":key_prefix}

def resolve_profile(item):
    i=item["idx"]; include_d60=st.session_state.get(f"d60_{i}",False)
    if item["type"]=="saved": return item["data"],include_d60
    if item["type"]=="empty_saved": st.error("Please select a valid profile."); st.stop()
    u_name=st.session_state.get(f"n_{i}","")
    if not u_name.strip(): st.error("Please enter a name."); st.stop()
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

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;margin-bottom:1.5rem;font-size:1.3rem;'>🪐 Kundli AI</h2>",unsafe_allow_html=True)
        pages=[("🌌 Dashboard","Dashboard"),("🔮 The Oracle","The Oracle"),
               ("🃏 Mystic Tarot","Mystic Tarot"),("🌟 Horoscopes","Horoscopes"),
               ("🔢 Numerology","Numerology"),("📖 Saved Profiles","Saved Profiles")]
        for label,page in pages:
            kind="primary" if st.session_state.nav_page==page else "secondary"
            if st.button(label,use_container_width=True,type=kind,key=f"side_{page}"):
                st.session_state.nav_page=page; st.rerun()
        st.markdown("---")
        dp=get_default_profile()
        if dp:
            st.markdown(f"<p style='font-size:.75rem;color:rgba(200,190,220,.55);'>⭐ Active Profile</p>",unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:.88rem;color:#e0d8f0;font-weight:600;margin:0;'>{dp['name']}</p>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════
def show_dashboard():
    dp=get_default_profile()
    if dp:
        st.markdown(f"""<div class="prof-banner">
        <p style='font-size:.72rem;text-transform:uppercase;letter-spacing:1.5px;color:rgba(205,140,80,.7);margin:0 0 .3rem;'>Welcome back</p>
        <h2 style='margin:0 0 .2rem;font-size:1.4rem;'>{dp['name']}</h2>
        <p style='margin:0;font-size:.82rem;color:rgba(200,190,220,.6);'>📍 {dp['place'].split(',')[0]}</p>
        </div>""",unsafe_allow_html=True)
    else:
        st.markdown("<h1>🌌 Dashboard</h1>",unsafe_allow_html=True)
        st.info("💡 Set a default profile in **Saved Profiles** to get personalised insights here.")

    with st.spinner("Loading cosmic weather..."):
        cw=get_live_cosmic_weather()

    st.markdown("### 🌍 Today's Cosmic Weather")
    cw1,cw2,cw3=st.columns(3)
    with cw1:
        with st.container(border=True):
            st.markdown(f"<div class='stat-val'>{cw['moon_sign']} 🌙</div><div class='stat-lbl'>Moon Sign</div>",unsafe_allow_html=True)
            st.caption(f"Nakshatra: **{cw['nakshatra']}**")
    with cw2:
        with st.container(border=True):
            ptitle,pdesc=cw['plain_title'],cw['plain_desc']
            st.markdown(f"<div class='stat-val' style='font-size:1rem;'>{ptitle}</div>",unsafe_allow_html=True)
            st.caption(pdesc)
    with cw3:
        with st.container(border=True):
            st.markdown("<div class='stat-lbl' style='margin-bottom:.3rem;'>Vedic Calendar</div>",unsafe_allow_html=True)
            st.write(f"**Tithi:** {cw['tithi']}")
            st.write(f"**Yoga:** {cw['yoga']}")

    if cw['retrogrades']:
        with st.container(border=True):
            st.markdown(f"⚠️ **Retrograde Alert:** {', '.join(cw['retrogrades'])} {'is' if len(cw['retrogrades'])==1 else 'are'} retrograde.")
            tips={"Mercury":"Communication, tech, and travel may face delays. Back up files, re-read messages before sending.",
                  "Venus":"Relationship or financial decisions may need a second look. Not ideal for new commitments.",
                  "Mars":"Energy can be scattered. Avoid starting new ventures; finish existing ones.",
                  "Jupiter":"Growth and expansion may feel slower. Focus on consolidation and inner wisdom.",
                  "Saturn":"Structure and authority may be tested. Review your plans and obligations."}
            for r in cw['retrogrades']:
                if r in tips: st.caption(f"**{r}:** {tips[r]}")

    if dp:
        st.markdown("### ⏳ Your Live Planetary Snapshot")
        try:
            d_val=date.fromisoformat(dp['date']); t_val=datetime.strptime(dp['time'],"%H:%M").time()
            jd,dt_local,_=local_to_julian_day(d_val,t_val,dp['tz'])
            moon_lon,_,_=get_planet_metrics(jd,PLANETS["Moon"])
            dt_now=datetime.now(ZoneInfo(dp['tz']))
            dasha_info=build_vimshottari_timeline(dt_local,moon_lon,dt_now)
            sade_sati=calculate_sade_sati(sign_index_from_lon(moon_lon))
            d1,d2,d3=st.columns(3)
            with d1:
                with st.container(border=True):
                    st.markdown("#### 🔴 Mahadasha")
                    st.markdown(f"**{dasha_info['current_md']}**")
                    st.caption(f"Until {dasha_info['md_end'].strftime('%b %Y')}")
                    st.caption("The major life theme currently running. Like a season of your life.")
            with d2:
                with st.container(border=True):
                    st.markdown("#### 🟡 Antardasha")
                    st.markdown(f"**{dasha_info['current_ad']}**")
                    st.caption(f"Until {dasha_info['ad_end'].strftime('%b %Y')}")
                    st.caption("The sub-theme active right now — colours day-to-day events.")
            with d3:
                with st.container(border=True):
                    st.markdown("#### 🪐 Sade Sati")
                    if "ACTIVE" in sade_sati:
                        st.warning(sade_sati.split(':')[0])
                        st.caption("Saturn's 7.5-year transit over your Moon — brings pressure and transformation.")
                    else:
                        st.success("Not Active")
                        st.caption(f"Saturn is comfortably away from your Moon in {sign_name(sign_index_from_lon(moon_lon))}.")
        except Exception as e: st.error(f"Could not load personal data: {e}")
    else:
        st.markdown("### ⏳ Personal Tracker")
        st.info("Set a default profile to see your live Dasha, Antardasha, and Sade Sati here automatically.")

    st.markdown("### 🃏 Daily Tarot Card")
    with st.container(border=True):
        today_str=get_local_today(dp['tz'] if dp else "Asia/Kolkata").isoformat()
        already_drawn=st.session_state.dash_tarot_date==today_str and st.session_state.dash_tarot_card
        dt1,dt2=st.columns([1,2])
        with dt1:
            if already_drawn:
                c=st.session_state.dash_tarot_card; s=st.session_state.dash_tarot_state
                img_url=f"{BASE_URL}{get_filename(c)}"
                tr="transform:rotate(180deg);" if s=="Reversed" else ""
                st.markdown(f"""<div style='text-align:center;'>
                <img src='{img_url}' style='width:120px;border-radius:8px;border:2px solid rgba(205,140,80,.8);{tr}'>
                <p style='margin:.4rem 0 0;font-size:.85rem;font-weight:600;'>{c}</p>
                <p style='margin:0;font-size:.75rem;color:rgba(200,190,220,.6);'>{s}</p></div>""",unsafe_allow_html=True)
                st.caption("Come back tomorrow for a new card.")
            else:
                st.markdown("<p style='color:rgba(200,190,220,.7);font-size:.9rem;'>Draw one card for today's energy and guidance.</p>",unsafe_allow_html=True)
                if st.button("✨ Draw My Daily Card",use_container_width=True,key="draw_daily"):
                    rng=secrets.SystemRandom()
                    st.session_state.dash_tarot_card=rng.choice(FULL_TAROT_DECK)
                    st.session_state.dash_tarot_state=rng.choice(["Upright","Reversed"])
                    st.session_state.dash_tarot_date=today_str; st.rerun()
        with dt2:
            if st.session_state.get('dash_tarot_card'):
                st.markdown("**Get your reading:**")
                render_copy_button(build_daily_tarot_prompt(st.session_state.dash_tarot_card,st.session_state.dash_tarot_state),"Copy Daily Reading Prompt")
                a1,a2=st.columns(2)
                a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
                a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)

    st.markdown("### 🚀 What would you like to do?")
    feats=[("🔮","linear-gradient(90deg,#4e28a0,#8050cc)","Full Life Reading","Deep life analysis — personality, career, wealth, marriage, timing. Paste one prompt into any AI.","The Oracle"),
           ("🪐","linear-gradient(90deg,#8e2050,#c85080)","Live Transit Overlay","See how today's transits trigger your natal chart events right now.","The Oracle"),
           ("🃏","linear-gradient(90deg,#185578,#2888b8)","3-Card Tarot Spread","Ask a question, draw three cards, get a full reading prompt for any AI.","Mystic Tarot"),
           ("🔢","linear-gradient(90deg,#1a6040,#28a870)","Numerology Report","Core numbers, Personal Year, Pinnacle cycles, and optional astro cross-reference.","Numerology"),
           ("✦","linear-gradient(90deg,#8e2050,#c85080)","Compatibility Check","Complete Ashta Koota scoring, Manglik verdict, and KP marriage analysis for two charts.","The Oracle"),
           ("⚖","linear-gradient(90deg,#185578,#2888b8)","Compare Charts","Rank multiple people on wealth, luck, health, and custom parameters with planetary evidence.","The Oracle")]
    r1,r2=st.columns(2); r3,r4=st.columns(2); r5,r6=st.columns(2)
    cols_feat=[r1,r2,r3,r4,r5,r6]
    for i,(icon,grad,title,desc,target) in enumerate(feats):
        with cols_feat[i]:
            st.markdown(f"""<div class="feat-card" style="--c:{grad};margin-bottom:.6rem;">
            <span class="feat-icon">{icon}</span>
            <p class="feat-title">{title}</p>
            <p class="feat-desc">{desc}</p></div>""",unsafe_allow_html=True)
            if st.button(f"Open →",key=f"feat_{i}",use_container_width=True):
                if target=="The Oracle":
                    mission_map={"Full Life Reading":"Deep Personal Analysis","Compatibility Check":"Matchmaking / Compatibility",
                                 "Live Transit Overlay":"Live Transit vs Natal","Compare Charts":"Comparison (Multiple Profiles)"}
                    st.session_state.active_mission=mission_map.get(title,"Deep Personal Analysis")
                st.session_state.nav_page=target; st.rerun()

    render_bottom_nav()

# ══════════════════════════════════════════════════════
# ORACLE
# ══════════════════════════════════════════════════════
def show_oracle():
    st.markdown("<h1>🔮 The Oracle</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6);'>Mathematically locked AI prompts from Swiss Ephemeris precision.</p>",unsafe_allow_html=True)
    missions={"Deep Personal Analysis":"🔮 Full Life Reading", "Live Transit vs Natal": "🪐 Live Transit Overlay", "Matchmaking / Compatibility":"✦ Compatibility Match",
              "Comparison (Multiple Profiles)":"⚖ Compare Profiles","Prashna Kundli":"🎯 Ask a Question (Prashna)","Raw Data Only":"📋 Raw Chart Data"}
    descs={"Deep Personal Analysis":"Complete reading — personality, career, wealth, marriage, timing.",
           "Live Transit vs Natal": "How today's planetary transits are activating your natal chart.",
           "Matchmaking / Compatibility":"Full Ashta Koota + Manglik + KP marriage promise.",
           "Comparison (Multiple Profiles)":"Rank multiple people on custom traits with planetary evidence.",
           "Prashna Kundli":"Ask a specific question now. Get Yes/No/Delayed.",
           "Raw Data Only":"Your full chart data. Paste into any AI and ask anything."}
    sel_name=st.selectbox("Select Tool",list(missions.values()),label_visibility="collapsed",key="oracle_tool_sel")
    mission_id=list(missions.keys())[list(missions.values()).index(sel_name)]
    if st.session_state.active_mission!=mission_id: st.session_state.active_mission=mission_id
    st.markdown(f"<p style='color:rgba(190,185,210,.6);font-size:.88rem;margin-bottom:1.5rem;'>{descs[mission_id]}</p><hr>",unsafe_allow_html=True)
    run_oracle_mission(mission_id)

def run_oracle_mission(mission):
    dp=get_default_profile()
    if mission=="Prashna Kundli":
        question=st.text_area("Your question",placeholder="e.g. Will I get the job? When will I get married? Should I invest now?")
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
                p_lat=st.number_input("Lat",value=30.76,format="%.4f",key="prl")
                p_lon=st.number_input("Lon",value=76.80,format="%.4f",key="prn")
                p_tz=st.text_input("Timezone","Asia/Kolkata",key="prt")
        if st.button("Generate Prashna Prompt",type="primary",use_container_width=True):
            if not question.strip(): st.error("Enter a question."); return
            if not pr_man:
                geo=geocode_place(cur_place.strip())
                if not geo: st.error("Location not found."); return
                p_lat,p_lon,pn=geo; p_tz=timezone_for_latlon(p_lat,p_lon)
            else: pn="Manual"
            now=datetime.now(ZoneInfo(p_tz))
            prof={"name":"Prashna Chart","date":now.date().isoformat(),"time":now.strftime("%H:%M"),"place":pn,"lat":p_lat,"lon":p_lon,"tz":p_tz}
            with st.spinner("Casting Prashna chart..."):
                dos=generate_astrology_dossier(prof)
            render_post_generation(build_prashna_prompt(question,dos))
        return
        
    req=1 if mission in ["Raw Data Only","Deep Personal Analysis", "Live Transit vs Natal"] else 2
    num_slots=st.session_state.comp_slots if mission=="Comparison (Multiple Profiles)" else req
    st.markdown("#### Profile Selection")
    active=[]
    if mission=="Comparison (Multiple Profiles)":
        for i in range(num_slots):
            st.markdown(f"**Profile {i+1}**"); active.append(render_profile_form(f"orc_{mission}_{i}"))
        ca,cb,_=st.columns([1,1,4])
        if ca.button("＋ Add",key=f"add_{mission}"):
            if st.session_state.comp_slots<10: st.session_state.comp_slots+=1; st.rerun()
        if cb.button("－ Remove",key=f"rem_{mission}"):
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
        nc_c,nc_add=st.columns([4,1])
        nc=nc_c.text_input("Custom criteria",label_visibility="collapsed",placeholder="e.g. Most likely to be famous")
        if nc_add.button("Add",key="add_custom"):
            if nc.strip() and nc.strip() not in st.session_state.custom_criteria:
                st.session_state.custom_criteria.append(nc.strip()); st.rerun()
        for i,c in enumerate(st.session_state.custom_criteria):
            r1x,r2x=st.columns([6,1])
            if r1x.checkbox(c,key=f"cc_{i}"): selected_criteria.append(c)
            if r2x.button("✕",key=f"delc_{i}"): st.session_state.custom_criteria.pop(i); st.rerun()
            
    btn_labels={"Raw Data Only":"Generate Chart Data","Deep Personal Analysis":"Generate Full Reading Prompt", "Live Transit vs Natal": "Generate Overlay Prompt", "Matchmaking / Compatibility":"Generate Compatibility Prompt","Comparison (Multiple Profiles)":"Generate Comparison Prompt"}
    
    if st.button(btn_labels[mission],type="primary",use_container_width=True,key=f"gen_{mission}"):
        profiles=[]; d60s=[]
        for item in active:
            if item["type"]=="empty_saved": st.error("Please fill all profile slots."); return
            prof,d60=resolve_profile(item); profiles.append(prof); d60s.append(d60)
        if len(profiles)<req: return
        compact=mission=="Comparison (Multiple Profiles)" and len(profiles)>3
        with st.spinner("Consulting the ephemeris..."):
            if mission=="Raw Data Only":
                final_prompt=(f"<context>\n<system_rules>\nThis is a complete, pre-computed Vedic birth chart. All values are locked.\n"
                              f"Rules MUST come from:\n  {PDF_HTRH1}\n  {PDF_HTRH2}\n</system_rules>\n<user_chart_data>\n"
                              +generate_astrology_dossier(profiles[0],d60s[0])+"\n</user_chart_data>\n</context>")
            elif mission=="Deep Personal Analysis":
                final_prompt=build_deep_analysis_prompt(generate_astrology_dossier(profiles[0],d60s[0]))
            elif mission=="Live Transit vs Natal":
                cw = get_live_cosmic_weather()
                final_prompt=build_transit_prompt(generate_astrology_dossier(profiles[0],d60s[0]), cw)
            elif mission=="Matchmaking / Compatibility":
                ma=get_moon_lon_from_profile(profiles[0]); mb=get_moon_lon_from_profile(profiles[1])
                koota=calculate_ashta_koota(ma,mb)
                jda,dtla,_=local_to_julian_day(date.fromisoformat(profiles[0]['date']),datetime.strptime(profiles[0]['time'],"%H:%M").time(),profiles[0]['tz'])
                pla={pn:get_planet_metrics(jda,pid) for pn,pid in PLANETS.items()}
                laga=sign_index_from_lon(get_lagna_and_cusps(jda,profiles[0]['lat'],profiles[0]['lon'])[0])
                ma_d=check_manglik_dosha(laga,sign_index_from_lon(pla["Moon"][0]),sign_index_from_lon(pla["Mars"][0]))
                jdb,dtlb,_=local_to_julian_day(date.fromisoformat(profiles[1]['date']),datetime.strptime(profiles[1]['time'],"%H:%M").time(),profiles[1]['tz'])
                plb={pn:get_planet_metrics(jdb,pid) for pn,pid in PLANETS.items()}
                lagb=sign_index_from_lon(get_lagna_and_cusps(jdb,profiles[1]['lat'],profiles[1]['lon'])[0])
                mb_d=check_manglik_dosha(lagb,sign_index_from_lon(plb["Moon"][0]),sign_index_from_lon(plb["Mars"][0]))
                canc=get_manglik_cancellation_verdict(ma_d,mb_d)
                final_prompt=build_matchmaking_prompt(generate_astrology_dossier(profiles[0],d60s[0]),generate_astrology_dossier(profiles[1],d60s[1]),koota,canc)
            elif mission=="Comparison (Multiple Profiles)":
                if not selected_criteria: st.warning("Select at least one comparison criterion."); return
                pairs=[(p['name'],generate_astrology_dossier(p,d,compact)) for p,d in zip(profiles,d60s)]
                final_prompt=build_comparison_prompt(pairs,selected_criteria)
        render_post_generation(final_prompt)

# ══════════════════════════════════════════════════════
# TAROT
# ══════════════════════════════════════════════════════
def show_tarot():
    st.markdown("<h1>🃏 Mystic Tarot</h1>",unsafe_allow_html=True)
    tab1,tab2,tab3,tab4=st.tabs(["✦ Three-Card Spread","☯ Yes / No Oracle","🔮 Celtic Cross (10 Cards)","🌟 Birth Card"])

    with tab1:
        st.markdown("#### Ask a Question")
        tarot_mode=st.radio("Spread type",["General Guidance","Love & Dynamics","Decision / Two Paths"],horizontal=True,label_visibility="collapsed")
        question=st.text_area("Your question",key="t3_q",placeholder={"General Guidance":"e.g. What energy surrounds my career this month?","Love & Dynamics":"e.g. What should I know about my connection with...","Decision / Two Paths":"e.g. Should I choose path A or path B?"}[tarot_mode],label_visibility="collapsed")
        use_rev=st.checkbox("Include Reversed Cards",help="Adds nuance — reversed cards indicate blocked or internalised energy.")
        if st.button("Draw 3 Cards",type="primary",use_container_width=True,key="draw3"):
            if not question.strip(): st.error("Enter a question first."); return
            with st.spinner("Shuffling..."): time_module.sleep(1.2)
            rng=secrets.SystemRandom(); st.session_state.tarot_cards=rng.sample(FULL_TAROT_DECK,3)
            st.session_state.tarot_states=([rng.choice(["Upright","Reversed"]) for _ in range(3)] if use_rev else ["Upright"]*3)
            st.session_state.tarot_drawn=True; st.session_state.tarot_mode=tarot_mode
        if st.session_state.get('tarot_drawn') and st.session_state.tarot_cards:
            c1,c2,c3=st.session_state.tarot_cards; s1,s2,s3=st.session_state.tarot_states
            render_tarot_overlay([c1,c2,c3],[s1,s2,s3],3)
            prompt=build_tarot_prompt(question,c1,s1,c2,s2,c3,s3,st.session_state.tarot_mode)
            render_post_generation(prompt)
            if st.button("🔄 New Reading",key="reset3"): st.session_state.tarot_drawn=False; st.session_state.tarot_cards=[]; st.rerun()

    with tab2:
        st.markdown("#### Ask a Yes or No Question")
        st.caption("One card. One answer. Backed by the full weight of its archetype.")
        yn_q=st.text_input("Your yes/no question",placeholder="e.g. Will this situation resolve in my favour?",key="yn_q")
        yn_rev=st.checkbox("Include Reversed",key="yn_rev")
        if st.button("Draw One Card",type="primary",use_container_width=True,key="draw_yn"):
            if not yn_q.strip(): st.error("Enter a question."); return
            rng=secrets.SystemRandom(); st.session_state.yesno_card=rng.choice(FULL_TAROT_DECK)
            st.session_state.yesno_state=rng.choice(["Upright","Reversed"]) if yn_rev else "Upright"; st.session_state.yesno_drawn=True
        if st.session_state.get('yesno_drawn') and st.session_state.yesno_card:
            card=st.session_state.yesno_card; state=st.session_state.yesno_state
            render_tarot_overlay([card],[state],1)
            st.markdown(f"<p style='text-align:center;font-size:1rem;font-weight:600;'>{card} — {state}</p>",unsafe_allow_html=True)
            prompt=build_yesno_prompt(yn_q,card,state); render_post_generation(prompt)
            if st.button("🔄 Ask Again",key="reset_yn"): st.session_state.yesno_drawn=False; st.session_state.yesno_card=None; st.rerun()

    with tab3:
        st.markdown("#### The Celtic Cross — A Full-Life Spread")
        st.caption("10 cards covering your present, past, potential, inner world, and outcome.")
        cc_q=st.text_area("Your question (optional — if blank, reads as general life overview)",key="cc_q",placeholder="e.g. What do I need to know about the next chapter of my life?")
        cc_rev=st.checkbox("Include Reversed Cards",key="cc_rev")
        if st.button("Draw 10 Cards",type="primary",use_container_width=True,key="draw_cc"):
            with st.spinner("Laying out the Celtic Cross..."): time_module.sleep(1.5)
            rng=secrets.SystemRandom()
            st.session_state.cc_cards=rng.sample(FULL_TAROT_DECK,10)
            st.session_state.cc_states=[rng.choice(["Upright","Reversed"]) if cc_rev else "Upright" for _ in range(10)]
            st.session_state.cc_drawn=True
        if st.session_state.get('cc_drawn') and st.session_state.get('cc_cards'):
            cards=st.session_state.cc_cards; states=st.session_state.cc_states
            render_tarot_overlay(cards,states,10)
            for i,(c,s) in enumerate(zip(cards,states)):
                st.markdown(f"**{CELTIC_CROSS_POSITIONS[i]}:** {c} ({s})")
            prompt=build_celtic_cross_prompt(cc_q or "General life overview",cards,states); render_post_generation(prompt)
            if st.button("🔄 New Celtic Cross",key="reset_cc"): st.session_state.cc_drawn=False; st.session_state.cc_cards=[]; st.rerun()

    with tab4:
        st.markdown("#### Your Tarot Birth Card")
        st.caption("A permanent card determined by your date of birth — it represents your soul's archetype and life theme.")
        bc_dob=st.date_input("Date of Birth",date(2000,1,1),key="bc_dob")
        if st.button("Reveal My Birth Card",type="primary",use_container_width=True,key="reveal_bc"):
            card=get_tarot_birth_card(bc_dob.isoformat())
            img_url=f"{BASE_URL}{get_filename(card)}"
            st.markdown(f"""<div style='text-align:center;margin:1.5rem 0;'>
            <img src='{img_url}' style='width:160px;border-radius:10px;border:2px solid rgba(205,140,80,.8);box-shadow:0 4px 20px rgba(0,0,0,.5);'>
            <h3 style='margin:.8rem 0 .2rem;'>{card}</h3>
            <p style='color:rgba(200,190,220,.6);font-size:.82rem;'>Your Tarot Birth Card</p></div>""",unsafe_allow_html=True)
            prompt=f"""<context><system_rules>MISSION: Tarot Birth Card reading. Meanings MUST come from: {PDF_TGUIDE}</system_rules><task>Name's DOB: {bc_dob.isoformat()}\nBirth Card: {card}\nDeliver: Archetype meaning, life theme, core strengths, shadows/challenges, famous figures, personal mantra.</task></context>"""
            render_post_generation(prompt)

# ══════════════════════════════════════════════════════
# HOROSCOPES
# ══════════════════════════════════════════════════════
def show_horoscopes():
    st.markdown("<h1>🌟 Horoscopes</h1>",unsafe_allow_html=True)
    st.info("ℹ️ These horoscopes are algorithmically generated from traditional sign-based guidance — not computed from your personal birth chart. For a chart-accurate, personalised reading, use **The Oracle**.")
    dp=get_default_profile()
    today=get_local_today(dp['tz'] if dp else "Asia/Kolkata")
    
    t1,t2=st.tabs(["☀️ Western (Sun Sign)","🌙 Vedic (Moon Sign / Rashi)"])
    with t1:
        dob=st.date_input("Date of Birth",date(2000,1,1),key="h_w_dob")
        if st.button("Show My Western Horoscope",type="primary",key="w_btn"):
            sign=get_western_sign(dob.month,dob.day)
            st.success(f"Your Sun Sign: **{sign}**")
            pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
            with pt1: st.write(generate_horoscope_text(sign,"D",today.isoformat()))
            with pt2: st.write(generate_horoscope_text(sign,"M",f"{today.year}-{today.month}"))
            with pt3: st.write(generate_horoscope_text(sign,"Y",f"{today.year}"))
    with t2:
        item=render_profile_form("vedic_horo",show_d60=False)
        if st.button("Calculate My Vedic Horoscope",type="primary",key="v_btn"):
            if item["type"]=="empty_saved": st.error("Please select or enter a profile.")
            else:
                prof,_=resolve_profile(item)
                moon_lon=get_moon_lon_from_profile(prof); moon_sidx=sign_index_from_lon(moon_lon)
                sign_n=sign_name(moon_sidx); nak,_,_=nakshatra_info(moon_lon)
                st.success(f"Your Rashi (Moon Sign): **{sign_n}** | Birth Star: **{nak}**")
                pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
                with pt1: st.write(generate_horoscope_text(sign_n,"DV",today.isoformat()))
                with pt2: st.write(generate_horoscope_text(sign_n,"MV",f"{today.year}-{today.month}"))
                with pt3: st.write(generate_horoscope_text(sign_n,"YV",f"{today.year}"))

# ══════════════════════════════════════════════════════
# NUMEROLOGY
# ══════════════════════════════════════════════════════
def show_numerology():
    st.markdown("<h1>🔢 Numerology</h1>",unsafe_allow_html=True)
    tab1,tab2,tab3=st.tabs(["📊 Full Report","🤝 Compatibility","⭕ Personal Cycles"])

    with tab1:
        system=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="num_sys")
        if system=="Indian/Vedic (Chaldean)": st.caption("ℹ️ **Chaldean system** — authentic ancient tradition. Number 9 is sacred and not assigned to letters.")
        mode=st.radio("Mode",["Full Report","Ask a Question"],horizontal=True,key="num_mode")
        question=""
        if mode=="Ask a Question": question=st.text_area("Your question",placeholder="e.g. When will my career take off?",key="num_q")
        use_astro=st.checkbox("🌌 Cross-Validate with Vedic Kundli (maximum accuracy)",key="num_use_astro")
        if use_astro:
            st.info("Name and DOB from the astrological profile will be used for numerology.")
            item=render_profile_form("num_prof",show_d60=True)
        else:
            c1,c2=st.columns(2)
            with c1: num_name=st.text_input("Full Birth Name",key="num_name")
            with c2: num_dob=st.date_input("Date of Birth",date(2000,1,1),key="num_dob")
        if st.button("Generate Numerology Prompt",type="primary",use_container_width=True,key="gen_num"):
            if use_astro:
                if item["type"]=="empty_saved": st.error("Select a saved profile."); return
                prof,d60=resolve_profile(item); name=prof['name']; dob_str=prof['date']
            else:
                if not num_name.strip(): st.error("Enter your name."); return
                name=num_name.strip(); dob_str=num_dob.isoformat()
            with st.spinner("Computing numbers..."):
                lp,dest,soul,pers=calculate_numerology_core(name,dob_str,system)
                py=get_personal_year(dob_str); pm=get_personal_month(dob_str); pd=get_personal_day(dob_str)
                dossier=None
                if use_astro: dossier=generate_astrology_dossier(prof,d60)
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Life Path",f"{lp}{'★' if lp in [11,22,33] else ''}")
            c2.metric("Destiny",f"{dest}{'★' if dest in [11,22,33] else ''}")
            c3.metric("Soul Urge",f"{soul}{'★' if soul in [11,22,33] else ''}")
            c4.metric("Personality",f"{pers}{'★' if pers in [11,22,33] else ''}")
            pc1,pc2,pc3=st.columns(3)
            pc1.metric(f"Personal Year {get_local_today().year}",str(py))
            pc2.metric(f"Personal Month",str(pm)); pc3.metric("Personal Day",str(pd))
            if any(n in [11,22,33] for n in [lp,dest,soul,pers]): st.caption("★ = Master Number")
            prompt=build_numerology_prompt(name,dob_str,lp,dest,soul,pers,dossier,question,system)
            render_post_generation(prompt)

    with tab2:
        st.markdown("#### Numerology Compatibility")
        sys2=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="nc_sys")
        c1,c2=st.columns(2)
        with c1:
            st.markdown("**Person 1**")
            nc_n1=st.text_input("Full Name",key="nc_n1"); nc_d1=st.date_input("Date of Birth",date(1995,1,1),key="nc_d1")
        with c2:
            st.markdown("**Person 2**")
            nc_n2=st.text_input("Full Name",key="nc_n2"); nc_d2=st.date_input("Date of Birth",date(1997,1,1),key="nc_d2")
        if st.button("Calculate Compatibility",type="primary",use_container_width=True,key="calc_nc"):
            if not nc_n1.strip() or not nc_n2.strip(): st.error("Enter both names."); return
            lpa,soula,dsta,lpb,soulb,dstb,score,rating,notes=get_numerology_compatibility(nc_n1.strip(),nc_d1.isoformat(),nc_n2.strip(),nc_d2.isoformat(),sys2)
            color={"Excellent":"#28a870","Good":"#2888b8","Moderate":"#c07020","Challenging":"#c85080"}[rating]
            st.markdown(f"<div style='background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:1.2rem;text-align:center;margin-bottom:1rem;'><div style='font-size:2rem;font-weight:700;color:{color};'>{score}/8</div><div style='font-size:1rem;color:{color};font-weight:600;'>{rating} Compatibility</div></div>",unsafe_allow_html=True)
            for note in notes: st.write(f"• {note}")
            prompt=build_numerology_compatibility_prompt(nc_n1,nc_d1.isoformat(),lpa,soula,dsta,nc_n2,nc_d2.isoformat(),lpb,soulb,dstb,score,rating,notes,sys2)
            render_post_generation(prompt)

    with tab3:
        st.markdown("#### Personal Cycles & Pinnacles")
        st.caption("Understand the numerical timing and specific challenges of your life phases.")
        sys3=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="cyc_sys")
        c1,c2=st.columns(2)
        with c1: cyc_name=st.text_input("Full Birth Name",key="cyc_name")
        with c2: cyc_dob=st.date_input("Date of Birth",date(2000,1,1),key="cyc_dob")
        if st.button("Show My Cycles",type="primary",use_container_width=True,key="show_cyc"):
            if not cyc_name.strip(): st.error("Enter your name."); return
            lp,_,_,_=calculate_numerology_core(cyc_name.strip(),cyc_dob.isoformat(),sys3)
            py=get_personal_year(cyc_dob.isoformat()); pm=get_personal_month(cyc_dob.isoformat()); pd=get_personal_day(cyc_dob.isoformat())
            r1,r2,r3,r4=get_pinnacle_cycles(cyc_dob.isoformat()); y=cyc_dob.year
            st.markdown("#### Current Timing")
            c1,c2,c3=st.columns(3)
            c1.metric(f"Personal Year {get_local_today().year}",str(py)); c1.caption(PERSONAL_YEAR_MEANINGS.get(py,''))
            c2.metric("Personal Month",str(pm)); c3.metric("Personal Day",str(pd))
            st.markdown("#### Pinnacle Cycles & Challenges")
            cur_age=get_local_today().year-y
            for i,(s,e,n,c) in enumerate([r1,r2,r3,r4],1):
                is_curr=s-y<=cur_age<e-y
                border="border:1px solid rgba(205,140,80,.5);" if is_curr else "border:1px solid rgba(255,255,255,.07);"
                label="◀ CURRENT" if is_curr else ""
                st.markdown(f"<div style='background:rgba(255,255,255,.03);{border}border-radius:10px;padding:.8rem 1rem;margin-bottom:.5rem;'><b>Pinnacle {i}</b> (Ages {s-y}–{e-y if e-y-y<100 else '∞'}): <b>Number {n}</b> (Challenge: {c}) <br><span style='font-size: 0.8rem;'>{PERSONAL_YEAR_MEANINGS.get(n,'')}</span> <span style='color:#d4944a;font-size:.75rem;float:right;'>{label}</span></div>",unsafe_allow_html=True)
            
            pdf_req = f"  {PDF_NUMEV}" if "Vedic" in sys3 else f"  {PDF_NUMEW1}\n  {PDF_NUMEW2}"
            prompt=f"""<context>
<system_rules>
MISSION: Personal Cycles and Pinnacle analysis — {sys3}.
MUST use rules from:\n{pdf_req}
</system_rules>
<user_data>
Subject: {cyc_name.strip()} | DOB: {cyc_dob.isoformat()}
Life Path: {lp} | Personal Year: {py} | Personal Month: {pm} | Personal Day: {pd}
Pinnacle 1 (Ages {r1[0]-y}-{r1[1]-y}): Number {r1[2]} | Challenge Number: {r1[3]}
Pinnacle 2 (Ages {r2[0]-y}-{r2[1]-y}): Number {r2[2]} | Challenge Number: {r2[3]}
Pinnacle 3 (Ages {r3[0]-y}-{r3[1]-y}): Number {r3[2]} | Challenge Number: {r3[3]}
Pinnacle 4 (Ages {r4[0]-y}+): Number {r4[2]} | Challenge Number: {r4[3]}
</user_data>
<task>Explain current Personal Year energy and what it means for the next 12 months. Explain the active Pinnacle, what theme it represents, AND how the Challenge Number associated with it will test them.</task>
</context>"""
            render_post_generation(prompt)

# ══════════════════════════════════════════════════════
# SAVED PROFILES / VAULT
# ══════════════════════════════════════════════════════
def show_vault():
    st.markdown("<h1>📖 Saved Profiles</h1>",unsafe_allow_html=True)
    dp_idx=st.session_state.default_profile_idx
    if not st.session_state.db:
        st.info("No saved profiles yet. Add your first profile below.")
    else:
        st.markdown("### Your Profiles")
        cols=st.columns(min(len(st.session_state.db),3))
        for i,p in enumerate(st.session_state.db):
            with cols[i%3]:
                is_def=dp_idx==i
                
                # FIXED: Removed raw HTML injection to prevent code leakage. Now utilizing native st.container.
                with st.container(border=True):
                    if is_def:
                        st.markdown('<span class="default-badge" style="margin-bottom:0.5rem; display:inline-block;">⭐ Default</span>', unsafe_allow_html=True)
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"{format_date_ui(p['date'])} · {p['time']}")
                    st.caption(f"📍 {p['place'].split(',')[0]}")
                    
                    btn_col1,btn_col2,btn_col3=st.columns(3)
                    with btn_col1:
                        if st.button("✏️",key=f"v_edit_{i}",use_container_width=True,help="Edit"):
                            st.session_state.editing_idx=i; st.rerun()
                    with btn_col2:
                        if is_def:
                            if st.button("★",key=f"v_def_{i}",use_container_width=True,help="Remove default"):
                                clear_default_profile(); st.rerun()
                        else:
                            if st.button("☆",key=f"v_def_{i}",use_container_width=True,help="Set as my profile"):
                                set_default_profile(i); st.rerun()
                    with btn_col3:
                        if st.button("🗑️",key=f"v_del_{i}",use_container_width=True,help="Delete"):
                            st.session_state.db.pop(i); sync_db()
                            if dp_idx==i: clear_default_profile()
                            elif dp_idx is not None and dp_idx>i: set_default_profile(dp_idx-1)
                            if st.session_state.editing_idx==i: st.session_state.editing_idx=None
                            st.rerun()
                            
        if dp_idx is not None and 0<=dp_idx<len(st.session_state.db):
            st.info(f"⭐ **{st.session_state.db[dp_idx]['name']}** is your default profile. It appears first in all dropdowns and auto-loads on the Dashboard.")
        else:
            st.caption("☆ Tap the star icon on any profile to set it as your default. It will auto-load on the Dashboard and appear first in all dropdowns.")

    if st.session_state.editing_idx is not None:
        st.markdown("---"); ei=st.session_state.editing_idx; pd_=st.session_state.db[ei]
        st.markdown(f"### ✏️ Editing: {pd_['name']}")
        e1,e2=st.columns(2)
        with e1:
            u_name=st.text_input("Name",pd_['name'],key="ve_n")
            u_date=st.date_input("Date",date.fromisoformat(pd_['date']),key="ve_d")
            pt=datetime.strptime(pd_['time'],"%H:%M").time()
            t1,t2,t3=st.columns(3)
            dhr=pt.hour%12 or 12; dai=0 if pt.hour<12 else 1
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
            also_default=st.checkbox("Set as my default profile",key="v_new_def")
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
                    if also_default: set_default_profile(len(st.session_state.db)-1)
                    st.success(f"✅ {v_n.strip()} added!"); st.session_state.show_add_profile=False; time_module.sleep(0.5); st.rerun()
                else: st.warning("Profile already exists.")
            if sa2.button("Cancel",use_container_width=True): st.session_state.show_add_profile=False; st.rerun()

    st.markdown("---")
    st.markdown("### 💾 Data Backup")
    bc1,bc2=st.columns(2)
    with bc1:
        st.download_button("⬇️ Export Profiles",json.dumps(st.session_state.db,indent=2),file_name="kundli_backup.json",use_container_width=True)
    with bc2:
        uf=st.file_uploader("Import Backup JSON",type="json",label_visibility="collapsed")
        if uf:
            try:
                imp=json.loads(uf.getvalue().decode('utf-8'))
                if isinstance(imp,list): st.session_state.db=imp; sync_db(); st.success("Imported."); time_module.sleep(0.5); st.rerun()
            except: st.error("Invalid file.")

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
inject_css()
render_sidebar()

if   st.session_state.nav_page=="Dashboard":      show_dashboard()
elif st.session_state.nav_page=="The Oracle":     show_oracle()
elif st.session_state.nav_page=="Mystic Tarot":   show_tarot()
elif st.session_state.nav_page=="Horoscopes":     show_horoscopes()
elif st.session_state.nav_page=="Numerology":     show_numerology()
elif st.session_state.nav_page=="Saved Profiles": show_vault()

if st.session_state.get('needs_sync',False):
    localS.setItem("kundli_vault",json.dumps(st.session_state.db))
    st.session_state.needs_sync=False
