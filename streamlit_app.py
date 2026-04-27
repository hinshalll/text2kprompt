import json
import base64
import secrets
import textwrap
import time as time_module
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_local_storage import LocalStorage

# ════════════════════════════════════════════════════════════════
# APP CONFIG
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Kundli AI",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="collapsed",   # FIX: was "expanded" — bad on mobile
)
try:
    swe.set_ephe_path("ephe")
except Exception:
    pass
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ════════════════════════════════════════════════════════════════
# CONSTANTS & ASTROLOGICAL DATA MAPS
# ════════════════════════════════════════════════════════════════
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

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati"
]
NAKSHATRA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"] * 3

NAK_NATURES = {
    "Fixed (Dhruva)":   ["Rohini","Uttara Phalguni","Uttara Ashadha","Uttara Bhadrapada"],
    "Movable (Chara)":  ["Punarvasu","Swati","Shravana","Dhanishta","Shatabhisha"],
    "Fierce (Ugra)":    ["Bharani","Magha","Purva Phalguni","Purva Ashadha","Purva Bhadrapada"],
    "Mixed (Mishra)":   ["Krittika","Vishakha"],
    "Swift (Kshipra)":  ["Ashwini","Pushya","Hasta"],
    "Tender (Mridu)":   ["Mrigashira","Chitra","Anuradha","Revati"],
    "Sharp (Tikshna)":  ["Ardra","Ashlesha","Jyeshtha","Mula"],
}
NAK_ADVICE = {
    "Fixed (Dhruva)":  "Excellent for long-term commitments, property decisions, and foundations.",
    "Movable (Chara)": "Great energy for travel, change, buying vehicles, and new beginnings.",
    "Fierce (Ugra)":   "Intense day. Good for assertive action, overcoming obstacles. Avoid gentle tasks.",
    "Mixed (Mishra)":  "Routine energy. Stick to everyday tasks, organization, pending work.",
    "Swift (Kshipra)": "High-paced energy. Perfect for quick tasks, trading, and fast decisions.",
    "Tender (Mridu)":  "Soft, creative energy. Ideal for romance, arts, and new friendships.",
    "Sharp (Tikshna)": "Piercing energy. Good for research, deep analysis, and breaking bad habits.",
}

DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
               "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

YOGA_NAMES = ["Vishkambha","Priti","Ayushman","Saubhagya","Sobhana","Atiganda",
              "Sukarma","Dhriti","Soola","Ganda","Vriddhi","Dhruva","Vyaghata",
              "Harshana","Vajra","Siddhi","Vyatipata","Variyan","Parigha","Siva",
              "Siddha","Sadhya","Subha","Sukla","Brahma","Indra","Vaidhriti"]

YEAR_DAYS   = 365.2425
MOVABLE_SIGNS = {0,3,6,9}
FIXED_SIGNS   = {1,4,7,10}

DEB_SIGN_LORDS = {
    "Sun":"Venus","Moon":"Mars","Mars":"Moon","Mercury":"Jupiter",
    "Jupiter":"Saturn","Venus":"Mercury","Saturn":"Mars"
}
EXALT_LORD_IN_DEB_SIGN = {
    "Sun":"Saturn","Moon":None,"Mars":"Jupiter","Mercury":"Venus",
    "Jupiter":"Mars","Venus":"Mercury","Saturn":"Sun"
}

# Pythagorean (Western) number map
PYTH_MAP = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
            'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
            's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8}

# Chaldean (Vedic/Indian) number map — 9 is not assigned
CHALDEAN_MAP = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,
                'j':1,'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':2,
                's':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}

COMPARISON_CRITERIA = [
    "Wealth Potential — Who builds the most wealth?",
    "Relationship Quality — Who has the best marriage/love life?",
    "Career Success — Who reaches the highest professional position?",
    "Life Struggles — Who faces the most karmic obstacles?",
    "Health & Longevity — Who has the strongest constitution?",
    "Happiness & Contentment — Who lives the most fulfilled life?",
    "Luck & Fortune — Who is the most naturally fortunate?",
    "Spiritual Depth — Who is the most spiritually evolved?",
    "Hidden Pitfalls — Who faces unexpected structural problems?",
]

FULL_TAROT_DECK = [
    "The Fool","The Magician","The High Priestess","The Empress","The Emperor",
    "The Hierophant","The Lovers","The Chariot","Strength","The Hermit",
    "Wheel of Fortune","Justice","The Hanged Man","Death","Temperance",
    "The Devil","The Tower","The Star","The Moon","The Sun","Judgement","The World"
]
for suit in ["Wands","Cups","Swords","Pentacles"]:
    for rank in ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine",
                 "Ten","Page","Knight","Queen","King"]:
        FULL_TAROT_DECK.append(f"{rank} of {suit}")

# ════════════════════════════════════════════════════════════════
# SESSION STATE & LOCAL STORAGE
# ════════════════════════════════════════════════════════════════
localS = LocalStorage()

if 'db' not in st.session_state: st.session_state.db = []
if 'db_loaded' not in st.session_state:
    saved = localS.getItem("kundli_vault")
    if saved is not None:
        if isinstance(saved, str) and saved.strip():
            try: st.session_state.db = json.loads(saved)
            except Exception: pass
        elif isinstance(saved, list):
            st.session_state.db = saved
    st.session_state.db_loaded = True

if 'needs_sync'         not in st.session_state: st.session_state.needs_sync = False
if 'custom_criteria'    not in st.session_state: st.session_state.custom_criteria = []
if 'editing_idx'        not in st.session_state: st.session_state.editing_idx = None
if 'comp_slots'         not in st.session_state: st.session_state.comp_slots = 2
if 'nav_page'           not in st.session_state: st.session_state.nav_page = "Dashboard"
if 'active_mission'     not in st.session_state: st.session_state.active_mission = "Deep Personal Analysis"
if 'tarot_drawn'        not in st.session_state: st.session_state.tarot_drawn = False
if 'tarot_cards'        not in st.session_state: st.session_state.tarot_cards = []
if 'tarot_states'       not in st.session_state: st.session_state.tarot_states = []
if 'tarot_question_input' not in st.session_state: st.session_state.tarot_question_input = ""
if 'dash_tarot_card'    not in st.session_state: st.session_state.dash_tarot_card = None
if 'dash_tarot_state'   not in st.session_state: st.session_state.dash_tarot_state = None
if 'dash_tarot_date'    not in st.session_state: st.session_state.dash_tarot_date = None  # date lock
if 'show_western'       not in st.session_state: st.session_state.show_western = False
if 'show_vedic'         not in st.session_state: st.session_state.show_vedic = False
if 'vedic_horo_prof'    not in st.session_state: st.session_state.vedic_horo_prof = None
if 'select_all_cb'      not in st.session_state: st.session_state.select_all_cb = False

for i in range(len(COMPARISON_CRITERIA)):
    if f"chk_{i}" not in st.session_state: st.session_state[f"chk_{i}"] = False


def sync_db():
    st.session_state.needs_sync = True

def is_duplicate_in_db(p):
    return any(x['name']==p['name'] and x['date']==p['date'] for x in st.session_state.db)

def format_date_ui(s):
    return datetime.fromisoformat(s).strftime('%d %b %Y')

def get_filename(card_name):
    return card_name.lower().replace(' ','') + '.jpg'

def toggle_all_criteria():
    val = st.session_state.select_all_cb
    for i in range(len(COMPARISON_CRITERIA)):
        st.session_state[f"chk_{i}"] = val
    for i in range(len(st.session_state.custom_criteria)):
        st.session_state[f"cc_{i}"] = val

def auto_collapse_sidebar():
    components.html("""<script>
        setTimeout(function() {
            if (window.innerWidth <= 768) {
                var btns = window.parent.document.querySelectorAll('button[aria-label="Collapse sidebar"]');
                if (btns.length > 0) { btns[0].click(); }
            }
        }, 50);
    </script>""", height=0, width=0)

# ════════════════════════════════════════════════════════════════
# BASIC CALCULATION HELPERS
# ════════════════════════════════════════════════════════════════
def sign_name(i): return SIGNS[i % 12]
def sign_index_from_lon(lon): return int(lon // 30) % 12

def format_dms(angle):
    angle %= 360
    d=int(angle); mf=(angle-d)*60; m=int(mf); s=int(round((mf-m)*60))
    if s==60: s,m=0,m+1
    if m==60: m,d=0,d+1
    return f"{d:02d}°{m:02d}'"

def sign_and_deg(lon): return f"{sign_name(sign_index_from_lon(lon))} {format_dms(lon%30)}"

def nakshatra_info(lon):
    ns=360/27; idx=min(int((lon%360)//ns),26)
    return NAKSHATRAS[idx], NAKSHATRA_LORDS[idx], int(((lon%360%ns)//(ns/4)))+1

def get_baladi_avastha(lon):
    si=int(lon//30)%12; states=["Infant","Youth","Adult","Old","Dead"]
    if si%2!=0: states=states[::-1]
    return states[int((lon%30)//6)]

def get_panchanga(sun_lon, moon_lon, dt_local):
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

def whole_sign_house(lagna_sidx, planet_sidx): return ((planet_sidx-lagna_sidx)%12)+1

def get_western_sign(month, day):
    """FIX: Cleaner, unambiguous boundary table replacing fragile logic."""
    # (end_month, end_day, sign ending on that date)
    cusps = [
        (1,19,"Capricorn"),(2,18,"Aquarius"),(3,20,"Pisces"),(4,19,"Aries"),
        (5,20,"Taurus"),(6,20,"Gemini"),(7,22,"Cancer"),(8,22,"Leo"),
        (9,22,"Virgo"),(10,22,"Libra"),(11,21,"Scorpio"),(12,21,"Sagittarius"),
    ]
    for em,ed,sign in cusps:
        if month < em or (month==em and day<=ed): return sign
    return "Capricorn"  # Dec 22+

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
    return float(ascmc[0])%360, cusps

def get_planet_longitude_and_speed(jd_ut,planet_id):
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED; res,_=swe.calc_ut(jd_ut,planet_id,f)
    return float(res[0])%360, float(res[3])

def get_rahu_longitude(jd_ut):
    res,_=swe.calc_ut(jd_ut,swe.MEAN_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    return float(res[0])%360

def get_placidus_cusps(jd_ut, lat, lon):
    cusps,_=swe.houses_ex(jd_ut,lat,lon,b"P",swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    return cusps

# ════════════════════════════════════════════════════════════════
# LIVE COSMIC WEATHER (CACHED HOURLY — FIX: was uncached + utcnow)
# ════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def get_live_cosmic_weather():
    dt_now = datetime.now(ZoneInfo("UTC"))   # FIX: deprecated datetime.utcnow()
    jd = swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    moon_lon,_ = swe.calc_ut(jd,swe.MOON,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    sun_lon,_  = swe.calc_ut(jd,swe.SUN, swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    moon_sidx  = sign_index_from_lon(moon_lon[0])
    sun_sidx   = sign_index_from_lon(sun_lon[0])
    nak,_,_    = nakshatra_info(moon_lon[0])
    panch      = get_panchanga(sun_lon[0],moon_lon[0],dt_now)
    retrogrades= []
    for pname in ["Mars","Mercury","Jupiter","Venus","Saturn"]:
        _,spd=get_planet_longitude_and_speed(jd,PLANETS[pname])
        if spd<0: retrogrades.append(pname)
    nature_type="Mixed (Mishra)"; advice=NAK_ADVICE["Mixed (Mishra)"]
    for n_type,naks in NAK_NATURES.items():
        if nak in naks: nature_type=n_type; advice=NAK_ADVICE[n_type]; break
    all_pos={}
    for pname,pid in PLANETS.items():
        lon,_=get_planet_longitude_and_speed(jd,pid)
        all_pos[pname]=sign_name(sign_index_from_lon(lon))
    r_lon,_=swe.calc_ut(jd,swe.MEAN_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    all_pos["Rahu"]=sign_name(sign_index_from_lon(float(r_lon[0])%360))
    all_pos["Ketu"]=sign_name(sign_index_from_lon((float(r_lon[0])+180)%360))
    return {"moon_sign":sign_name(moon_sidx),"sun_sign":sign_name(sun_sidx),
            "nakshatra":nak,"tithi":panch["tithi"],"yoga":panch["yoga"],
            "retrogrades":retrogrades,"nature":nature_type,"advice":advice,"all_pos":all_pos}

def generate_horoscope_text(sign, mode, date_val):
    import random
    seed=f"{sign}_{mode}_{date_val}"; rng=random.Random(seed)
    general=["The cosmos is aligning in your favor. A sudden burst of clarity will help you navigate confusing situations.",
             "Patience is your best friend right now. Take a step back and let things unfold naturally.",
             "You are radiating positive energy. Others will be drawn to your aura — a great time to network.",
             "A period of introspection is needed. Spend quiet time reflecting on your recent choices.",
             "Unexpected news might shift your perspective. Stay adaptable and open-minded.",
             "Your creative juices are flowing! Channel this energy into a passion project.",
             "You might feel a bit drained mentally. Prioritize rest and don't overcommit.",
             "A fantastic time to set new goals. The universe fully supports your ambitions."]
    love=["Communication flows easily with loved ones. Express your true feelings.",
          "You might experience a slight misunderstanding. Approach it with empathy.",
          "Romantic energy surrounds you. Plan something special.",
          "Focus on self-love. Treat yourself to something that makes you happy.",
          "A connection from the past might reappear. Proceed with caution but keep an open heart."]
    career=["Your hard work is catching the right eyes. Tangible rewards are near.",
            "A challenge at work tests your patience. Stay calm and think strategically.",
            "Collaboration is your superpower today. Reach out to a colleague for a joint project.",
            "A brilliant idea strikes you. Write it down and act on it — timing is perfect.",
            "Avoid making major financial decisions impulsively. Research before committing."]
    return f"**General:** {rng.choice(general)}\n\n**Love & Relationships:** {rng.choice(love)}\n\n**Career & Finance:** {rng.choice(career)}"

# ════════════════════════════════════════════════════════════════
# ADVANCED ASTROLOGICAL ENGINES
# ════════════════════════════════════════════════════════════════
def get_kp_sub_lord(lon):
    ns=360/27; idx=int((lon%360)//ns); nak_lord=NAKSHATRA_LORDS[idx]
    deg=lon%360-idx*ns
    si=DASHA_ORDER.index(nak_lord); seq=DASHA_ORDER[si:]+DASHA_ORDER[:si]
    acc=0.0
    for sl in seq:
        acc+=(DASHA_YEARS[sl]/120.0)*ns
        if deg<=acc+1e-9: return sl
    return seq[-1]

def get_vedic_aspects(planet_name, current_house):
    jumps={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[5,7,9],"Ketu":[5,7,9]}.get(planet_name,[7])
    return ", ".join(str(((current_house+j-2)%12)+1) for j in jumps)

def get_planet_lon(pname, planet_data, r_lon, k_lon):
    if pname in planet_data: return planet_data[pname][0]
    elif pname=="Rahu": return r_lon
    elif pname=="Ketu": return k_lon
    return None

def get_planet_house(pname, lagna_sidx, planet_data, r_lon, k_lon):
    lon=get_planet_lon(pname,planet_data,r_lon,k_lon)
    return whole_sign_house(lagna_sidx,sign_index_from_lon(lon)) if lon is not None else None

def get_lagna_lord_chain(lagna_sidx, planet_data, r_lon, k_lon):
    ll=SIGN_LORDS_MAP[lagna_sidx]; ll_lon=get_planet_lon(ll,planet_data,r_lon,k_lon)
    ll_sidx=sign_index_from_lon(ll_lon); ll_house=whole_sign_house(lagna_sidx,ll_sidx)
    tags=[]
    if ll in DIGNITIES:
        if ll_sidx==DIGNITIES[ll][0]: tags.append("Exalted")
        elif ll_sidx==DIGNITIES[ll][1]: tags.append("Debilitated")
    if ll in OWN_SIGNS and ll_sidx in OWN_SIGNS[ll]: tags.append("Own Sign")
    if planet_data.get(ll,(0,0))[1]<0: tags.append("Retrograde")
    tag_str=f" [{', '.join(tags)}]" if tags else ""
    dispositor=SIGN_LORDS_MAP[ll_sidx]
    disp_house=get_planet_house(dispositor,lagna_sidx,planet_data,r_lon,k_lon)
    return (f"{ll} → placed in H{ll_house} ({sign_name(ll_sidx)}{tag_str}) → "
            f"H{ll_house} dispositor is {dispositor} (H{disp_house})")

def get_conjunctions(lagna_sidx, planet_data, r_lon, k_lon):
    all_p={}
    for pn,(plon,_) in planet_data.items():
        h=whole_sign_house(lagna_sidx,sign_index_from_lon(plon)); all_p.setdefault(h,[]).append(pn)
    for pn,plon in [("Rahu",r_lon),("Ketu",k_lon)]:
        h=whole_sign_house(lagna_sidx,sign_index_from_lon(plon)); all_p.setdefault(h,[]).append(pn)
    return [f"{' + '.join(plist)} conjunct in H{h} ({sign_name((lagna_sidx+h-1)%12)})"
            for h,plist in all_p.items() if len(plist)>=2]

def get_mutual_aspects(lagna_sidx, planet_data, r_lon, k_lon):
    spec={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[5,7,9],"Ketu":[5,7,9]}
    def aspected(pn,h): return {((h+j-2)%12)+1 for j in spec.get(pn,[7])}
    houses={pn:whole_sign_house(lagna_sidx,sign_index_from_lon(planet_data[pn][0])) for pn in planet_data}
    houses["Rahu"]=whole_sign_house(lagna_sidx,sign_index_from_lon(r_lon))
    houses["Ketu"]=whole_sign_house(lagna_sidx,sign_index_from_lon(k_lon))
    plist=list(houses.keys()); mutual=[]
    for i,p1 in enumerate(plist):
        for p2 in plist[i+1:]:
            h1,h2=houses[p1],houses[p2]
            if h1!=h2 and h2 in aspected(p1,h1) and h1 in aspected(p2,h2):
                mutual.append(f"{p1} (H{h1}) ↔ {p2} (H{h2})")
    return mutual

def check_neecha_bhanga(planet_name, lagna_sidx, moon_sidx, planet_data, r_lon, k_lon):
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
        if h in kendra: conds.append(f"exaltation lord of debilitation sign ({exl}) in Kendra H{h} from Lagna")
    h_from_moon=whole_sign_house(moon_sidx,p_sidx)
    if h_from_moon in kendra: conds.append(f"debilitated planet in Kendra H{h_from_moon} from Moon")
    return conds if conds else None

def get_chara_karakas(planet_data):
    deg={pn:planet_data[pn][0]%30 for pn in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]}
    ranked=sorted(deg,key=deg.get,reverse=True)
    return ranked[0],deg[ranked[0]],ranked[1],deg[ranked[1]]

def detect_yogas(lagna_sidx, moon_sidx, planet_data, r_lon, k_lon):
    def ho(pn):
        lon=get_planet_lon(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(lagna_sidx,sign_index_from_lon(lon)) if lon else None
    def in_kendra(h1,h2): return (h2-h1)%12 in {0,3,6,9}
    yogas=[]; absent=[]

    # Gajakesari
    mh,jh=ho("Moon"),ho("Jupiter")
    if mh and jh and in_kendra(mh,jh):
        yogas.append(("Gajakesari Yoga",f"Moon (H{mh}) & Jupiter (H{jh}) in mutual Kendra — intelligence, fame, financial stability"))
    else: absent.append("Gajakesari Yoga — Moon and Jupiter not in mutual Kendra")

    # Pancha Mahapurusha
    for planet,(yname,exalt_sidx) in {"Mars":("Ruchaka",9),"Mercury":("Bhadra",5),
            "Jupiter":("Hamsa",3),"Venus":("Malavya",11),"Saturn":("Shasha",6)}.items():
        psidx=sign_index_from_lon(planet_data[planet][0]); ph=whole_sign_house(lagna_sidx,psidx)
        own=planet in OWN_SIGNS and psidx in OWN_SIGNS[planet]; exalt=psidx==exalt_sidx
        if (own or exalt) and ph in {1,4,7,10}:
            yogas.append((f"{yname} Yoga",f"{planet} in {'own sign' if own else 'exaltation'} in Kendra (H{ph}) — Pancha Mahapurusha"))
        else: absent.append(f"{yname} Yoga — {planet} not in own/exalt + Kendra")

    # Budha-Aditya
    if ho("Sun")==ho("Mercury"): yogas.append(("Budha-Aditya Yoga",f"Sun + Mercury conjunct in H{ho('Sun')} — intelligence, communication, professional reputation"))
    else: absent.append("Budha-Aditya Yoga — Sun and Mercury not conjunct")

    # Chandra-Mangala
    if ho("Moon")==ho("Mars"): yogas.append(("Chandra-Mangala Yoga",f"Moon + Mars conjunct in H{ho('Moon')} — entrepreneurial drive, financial ambition"))
    else: absent.append("Chandra-Mangala Yoga — Moon and Mars not conjunct")

    # Adhi Yoga
    mh2=ho("Moon")
    if mh2:
        t6=((mh2-1+5)%12)+1; t7=((mh2-1+6)%12)+1; t8=((mh2-1+7)%12)+1
        ben=[b for b in ["Mercury","Jupiter","Venus"] if ho(b) in {t6,t7,t8}]
        if len(ben)>=2: yogas.append(("Adhi Yoga",f"{', '.join(ben)} in 6th/7th/8th from Moon — leadership, longevity, authority"))
        else: absent.append("Adhi Yoga — fewer than 2 benefics in 6th/7th/8th from Moon")
    else: absent.append("Adhi Yoga — Moon not determinable")

    # Raja Yoga
    tri_lords={SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [1,5,9]}
    ken_lords={SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [1,4,7,10]}
    rj=[]
    for tl in tri_lords:
        for kl in ken_lords:
            if tl!=kl:
                th,kh=ho(tl),ho(kl)
                if th and kh and th==kh: rj.append(f"{tl}+{kl} in H{th}")
    if rj: yogas.append(("Raja Yoga",f"Trikona/Kendra lords conjunct: {'; '.join(rj[:2])} — power, authority, high status"))
    else: absent.append("Raja Yoga (Trikona+Kendra conjunction) — lords not conjunct")

    # Viparita Raja Yoga
    dust_lords=[SIGN_LORDS_MAP[(lagna_sidx+h-1)%12] for h in [6,8,12]]
    dust_in=[dl for dl in dust_lords if ho(dl) in {6,8,12}]
    if len(dust_in)>=2: yogas.append(("Viparita Raja Yoga",f"Dusthana lords ({', '.join(dust_in)}) in dusthana — unexpected rise, triumph after hardship"))
    else: absent.append("Viparita Raja Yoga — dusthana lords not sufficiently in dusthana")

    # Kemadruma (negative)
    if mh2:
        h2m=((mh2-1+1)%12)+1; h12m=((mh2-1-1)%12)+1
        all_h={pn:ho(pn) for pn in list(planet_data.keys())+["Rahu","Ketu"] if pn!="Moon"}
        flanking=[pn for pn,h in all_h.items() if h in {h2m,h12m} and pn not in {"Rahu","Ketu"}]  # FIX: removed extra }
        if not flanking: yogas.append(("Kemadruma Yoga (Negative)",f"No planets in 2nd/12th from Moon (H{h2m}/H{h12m}) — loneliness, emotional instability. Check: cancelled by Jupiter aspect on Moon?"))

    return yogas, absent

def calculate_sade_sati(natal_moon_sidx):
    dt_now=datetime.now(ZoneInfo("UTC"))   # FIX: deprecated utcnow
    jd=swe.julday(dt_now.year,dt_now.month,dt_now.day,dt_now.hour+dt_now.minute/60.0)
    res,_=swe.calc_ut(jd,swe.SATURN,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    sat_sidx=sign_index_from_lon(float(res[0])%360); diff=(sat_sidx-natal_moon_sidx)%12
    phases={11:"ACTIVE — Phase 1 (Rising): Saturn in sign before natal Moon",
            0: "ACTIVE — Phase 2 (Peak): Saturn directly on natal Moon sign",
            1: "ACTIVE — Phase 3 (Setting): Saturn in sign after natal Moon"}
    if diff in phases: return f"{phases[diff]}. Saturn now in {sign_name(sat_sidx)}, Natal Moon in {sign_name(natal_moon_sidx)}."
    return f"NOT ACTIVE. Saturn in {sign_name(sat_sidx)} ({diff} signs from natal Moon in {sign_name(natal_moon_sidx)})."

def check_manglik_dosha(lagna_sidx, moon_sidx, mars_sidx):
    mh_l=whole_sign_house(lagna_sidx,mars_sidx); mh_m=whole_sign_house(moon_sidx,mars_sidx)
    il=mh_l in [1,4,7,8,12]; im=mh_m in [1,4,7,8,12]
    if il and im: return "HIGH MANGLIK — Mars in Manglik house from both Ascendant and Moon"
    elif il: return "MILD MANGLIK — Mars in Manglik house from Ascendant only"
    elif im: return "MILD MANGLIK — Mars in Manglik house from Moon only"
    return "NOT MANGLIK — No Kuja Dosha"

# ── RESTORED: Full Ashta Koota Calculation ────────────────────
def calculate_ashta_koota(moon_lon_a, moon_lon_b):
    s1=sign_index_from_lon(moon_lon_a); s2=sign_index_from_lon(moon_lon_b)
    n1=min(int((moon_lon_a%360)//(360/27)),26); n2=min(int((moon_lon_b%360)//(360/27)),26)

    # 1. Varna (1 pt)
    vm=[1,2,3,0,1,2,3,0,1,2,3,0]
    v_pts=1 if vm[s1]<=vm[s2] else 0

    # 2. Vashya (2 pts)
    va=[0,0,1,2,3,1,1,4,0,2,1,2]; va1,va2=va[s1],va[s2]
    if va1==va2: va_pts=2
    elif {va1,va2} in [{1,3},{1,4},{2,3}]: va_pts=0
    else: va_pts=1

    # 3. Tara (3 pts)
    t1=((n2-n1)%27)%9; t2=((n1-n2)%27)%9
    ta_pts=(0 if t1 in [2,4,6] else 1.5)+(0 if t2 in [2,4,6] else 1.5)

    # 4. Yoni (4 pts)
    ym=[0,1,2,3,3,4,5,2,5,6,6,7,8,9,8,9,10,10,4,11,12,11,13,0,13,7,1]
    y1,y2=ym[n1],ym[n2]
    enemies=[{0,8},{1,13},{2,11},{3,12},{4,10},{5,6},{7,9}]
    yoni_pts=4 if y1==y2 else (0 if {y1,y2} in enemies else 2)

    # 5. Graha Maitri (5 pts)
    lm=[0,1,2,3,4,2,1,0,5,6,6,5]; l1,l2=lm[s1],lm[s2]
    f_map={0:[3,4,5],1:[2,6],2:[1,4],3:[2,4],4:[0,3,5],5:[0,3,4],6:[1,2]}
    e_map={0:[2],1:[3,4],2:[3],3:[],4:[1,6],5:[1,2],6:[0,3,4]}
    def rel(a,b): return 2 if b in f_map.get(a,[]) else (0 if b in e_map.get(a,[]) else 1)
    ms_map={(2,2):5,(2,1):4,(1,2):4,(1,1):3,(2,0):1,(0,2):1,(1,0):0.5,(0,1):0.5,(0,0):0}
    m_pts=ms_map.get((rel(l1,l2),rel(l2,l1)),0)

    # 6. Gana (6 pts)
    gm={0:0,1:1,2:2,3:1,4:0,5:1,6:0,7:0,8:2,9:2,10:1,11:1,12:0,
        13:2,14:0,15:2,16:0,17:2,18:2,19:1,20:1,21:0,22:2,23:2,24:1,25:1,26:0}
    g1,g2=gm[n1],gm[n2]
    if g1==g2: g_pts=6
    elif g1==0 and g2==1: g_pts=6
    elif g1==1 and g2==0: g_pts=5
    elif g1==0 and g2==2: g_pts=1
    else: g_pts=0

    # 7. Bhakoot (7 pts)
    dist=(s2-s1)%12
    b_pts=7 if dist in [0,2,3,6,8,9,10] else 0

    # 8. Nadi (8 pts) with exception detection
    nb=[0,1,2]*9; nd1,nd2=nb[n1],nb[n2]
    nadi_note=""
    if nd1==nd2:
        n_pts=0
        if n1==n2: nadi_note="NADI DOSHA EXCEPTION: Same birth Nakshatra — Dosha CANCELLED."
        elif SIGN_LORDS_MAP[s1]!=SIGN_LORDS_MAP[s2]: nadi_note="NADI DOSHA PARTIAL EXCEPTION: Different Moon sign lords — severity is reduced."
    else:
        n_pts=8

    total=v_pts+va_pts+ta_pts+yoni_pts+m_pts+g_pts+b_pts+n_pts
    result=(f"TOTAL ASHTA KOOTA SCORE: {total}/36\n"
            f"  Varna (1pt): {v_pts}/1 | Vashya (2pt): {va_pts}/2 | Tara (3pt): {ta_pts}/3 | Yoni (4pt): {yoni_pts}/4\n"
            f"  Graha Maitri (5pt): {m_pts}/5 | Gana (6pt): {g_pts}/6 | Bhakoot (7pt): {b_pts}/7 | Nadi (8pt): {n_pts}/8")
    if nadi_note: result+=f"\n  NOTE: {nadi_note}"
    if total>=31: result+="\n  INTERPRETATION: Excellent match (31-36/36). Highly compatible."
    elif total>=18: result+="\n  INTERPRETATION: Good match (18-30/36). Compatible with minor considerations."
    else: result+=f"\n  INTERPRETATION: Challenging match ({total}/36). Significant compatibility concerns."
    return result

# ── RESTORED: Manglik Cancellation Verdict ───────────────────
def get_manglik_cancellation_verdict(mang_a, mang_b):
    m1="NOT MANGLIK" not in mang_a; m2="NOT MANGLIK" not in mang_b
    if m1 and m2:
        return ("MANGLIK DOSHA CANCELLED — Both partners are Manglik. This is the classical cancellation. "
                "No Kuja Dosha remedy required. The Mars energies balance each other.")
    elif not m1 and not m2:
        return "No Manglik Dosha in either chart. No issue whatsoever on this count."
    else:
        who=("Person 1 is Manglik" if m1 else "Person 2 is Manglik")
        return (f"MANGLIK IMBALANCE — {who} and the other is not. "
                "A carefully chosen Muhurta for the wedding and classical remedies are advisable. "
                "This does not make marriage impossible — only one partner being Manglik is very common.")

def get_planet_house_significations(pname, lagna_sidx, planet_data, r_lon, k_lon):
    lon=get_planet_lon(pname,planet_data,r_lon,k_lon)
    if lon is None: return set()
    sigs=set(); psidx=sign_index_from_lon(lon)
    sigs.add(whole_sign_house(lagna_sidx,psidx))
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

def get_kp_verdict(cusp_lon, lagna_sidx, planet_data, r_lon, k_lon, event_houses, event_name):
    sl=get_kp_sub_lord(cusp_lon); nl=nakshatra_info(cusp_lon)[1]
    sigs=get_planet_house_significations(sl,lagna_sidx,planet_data,r_lon,k_lon)
    matched=sigs&event_houses
    sig_str=", ".join(f"H{h}" for h in sorted(sigs))
    if len(matched)>=2 or (max(event_houses) in matched): verdict="STRONGLY PROMISED"
    elif len(matched)==1: verdict="WEAKLY PROMISED (partial signification)"
    else: verdict="NOT CLEARLY PROMISED"
    return sl,nl,verdict,sig_str

# ════════════════════════════════════════════════════════════════
# VIMSHOTTARI DASHA ENGINE
# ════════════════════════════════════════════════════════════════
def build_vimshottari_timeline(dt_birth, moon_lon, dt_now):
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

# ════════════════════════════════════════════════════════════════
# DIVISIONAL CHART HELPERS
# ════════════════════════════════════════════════════════════════
def d2_sign_index(lon):
    s=sign_index_from_lon(lon); d=lon%30
    return (4 if d<15 else 3) if s%2==0 else (3 if d<15 else 4)
def d3_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)//10)*4)%12
def d4_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)//7.5)*3)%12
def saptamsa_sign_index(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/7))
    return ((s if s%2==0 else (s+6)%12)+slot)%12
def navamsa_sign_index(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/9))
    start=s if s in MOVABLE_SIGNS else ((s+8)%12 if s in FIXED_SIGNS else (s+4)%12)
    return (start+slot)%12
def dasamsa_sign_index(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//3)
    return ((s if s%2==0 else (s+8)%12)+slot)%12
def dwadasamsa_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%360%30)//2.5))%12
def d60_sign_index(lon): return (sign_index_from_lon(lon)+int((lon%30)*2))%12

# ════════════════════════════════════════════════════════════════
# MASTER DOSSIER GENERATOR
# ════════════════════════════════════════════════════════════════
def get_moon_lon_from_profile(profile):
    d=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    t=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd,_,__=local_to_julian_day(d,t,profile['tz'])
    lon,_=get_planet_longitude_and_speed(jd,PLANETS["Moon"]); return lon

def generate_astrology_dossier(profile, include_d60=False, compact=False):
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
    lagna_sidx=sign_index_from_lon(lagna_lon)
    moon_sidx=sign_index_from_lon(planet_data["Moon"][0])
    mars_sidx=sign_index_from_lon(planet_data["Mars"][0])

    ll_chain    =get_lagna_lord_chain(lagna_sidx,planet_data,r_lon,k_lon)
    conjunctions=get_conjunctions(lagna_sidx,planet_data,r_lon,k_lon)
    mutual_asp  =get_mutual_aspects(lagna_sidx,planet_data,r_lon,k_lon)
    manglik     =check_manglik_dosha(lagna_sidx,moon_sidx,mars_sidx)
    sade_sati   =calculate_sade_sati(moon_sidx)
    ak,ak_deg,amk,amk_deg=get_chara_karakas(planet_data)
    yogas_present,yogas_absent=detect_yogas(lagna_sidx,moon_sidx,planet_data,r_lon,k_lon)
    ad_table    =get_antardasha_table(dasha_info)
    kp7_sl,kp7_nl,kp7_verdict,kp7_sigs=get_kp_verdict(placidus_cusps[6],lagna_sidx,planet_data,r_lon,k_lon,{2,7,11},"Marriage")
    kp10_sl,kp10_nl,kp10_verdict,kp10_sigs=get_kp_verdict(placidus_cusps[9],lagna_sidx,planet_data,r_lon,k_lon,{1,6,10,11},"Career")

    # FIX: coordinates label based on actual hemisphere
    lat_label=f"{abs(lat):.5f}{'N' if lat>=0 else 'S'}"
    lon_label=f"{abs(lon):.5f}{'E' if lon>=0 else 'W'}"

    lines=[]
    lines.append(f"{'═'*60}")
    lines.append(f"KUNDLI DOSSIER — {name.upper()}")
    lines.append(f"System: Swiss Ephemeris | Lahiri Ayanamsa | Whole Sign + Placidus KP")
    lines.append(f"{'═'*60}")

    lines.append("\n━━━ BIRTH DATA & PANCHANGA ━━━")
    lines.append(f"Name: {name} | Place: {place_text}")
    lines.append(f"Local Time: {dt_local.strftime('%d %b %Y, %I:%M %p')} ({panchanga['weekday']})")
    lines.append(f"Coordinates: {lat_label}, {lon_label} | Timezone: {tz_name}")
    lines.append(f"Tithi: {panchanga['tithi']} | Yoga: {panchanga['yoga']} | Karana: {panchanga['karana']}")

    lines.append("\n━━━ LAGNA FOUNDATION ━━━")
    lines.append(f"Ascendant (Lagna): {sign_name(lagna_sidx)} {format_dms(lagna_lon%30)}")
    lines.append(f"LAGNA LORD CHAIN: {ll_chain}")
    lines.append(f"Manglik (Kuja Dosha): {manglik}")

    lines.append("\n━━━ PLANETARY POSITIONS — D1 RASI (Parashari) ━━━")
    house_occupants={i:[] for i in range(1,13)}
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        plon,pspd=planet_data[pname]
        sidx=sign_index_from_lon(plon); house=whole_sign_house(lagna_sidx,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); avastha=get_baladi_avastha(plon)
        sub_lord=get_kp_sub_lord(plon); aspects=get_vedic_aspects(pname,house)
        house_occupants[house].append(pname)
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
        lines.append(f"  {pname}: H{house} | {sign_name(sidx)} {format_dms(plon%30)}{tag_str} | Avastha: {avastha} | Nak: {nak} (NL:{nak_lord} SL:{sub_lord} Pada:{pada}) | Aspects: H{aspects}")
    for pname,plon in [("Rahu",r_lon),("Ketu",k_lon)]:
        sidx=sign_index_from_lon(plon); house=whole_sign_house(lagna_sidx,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); sub_lord=get_kp_sub_lord(plon)
        aspects=get_vedic_aspects(pname,house); house_occupants[house].append(pname)
        lines.append(f"  {pname}: H{house} | {sign_name(sidx)} {format_dms(plon%30)} [Retrograde] | Nak: {nak} (NL:{nak_lord} SL:{sub_lord} Pada:{pada}) | Aspects: H{aspects}")

    lines.append("\n━━━ PRE-COMPUTED CRITICAL FACTS ━━━")
    lines.append("(Mathematically verified. DO NOT re-derive or override.)")

    lines.append("\n[CONJUNCTIONS]")
    for c in conjunctions: lines.append(f"  ✓ {c}")
    if not conjunctions: lines.append("  None")

    lines.append("\n[MUTUAL ASPECTS]")
    for m in mutual_asp: lines.append(f"  ↔ {m}")
    if not mutual_asp: lines.append("  None")

    lines.append("\n[NEECHA BHANGA — DEBILITATION CANCELLATION]")
    nb_found=False
    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        psidx=sign_index_from_lon(planet_data[pname][0])
        if pname in DIGNITIES and psidx==DIGNITIES[pname][1]:
            nb_found=True
            conds=check_neecha_bhanga(pname,lagna_sidx,moon_sidx,planet_data,r_lon,k_lon)
            if conds:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NEECHA BHANGA APPLIES.")
                for c in conds: lines.append(f"    ✓ Condition met: {c}")
                lines.append(f"    → TREAT AS: Raja Yoga quality. Do NOT interpret as weak.")
            else:
                lines.append(f"  {pname} — Debilitated in {sign_name(psidx)}. NEECHA BHANGA DOES NOT APPLY.")
                lines.append(f"    → TREAT AS: Genuinely weakened. Analyze house and aspects accordingly.")
    if not nb_found: lines.append("  No debilitated planets in this chart.")

    lines.append("\n[YOGA VERDICTS — PRESENT ✓]")
    for yname,ydesc in yogas_present: lines.append(f"  ✓ {yname}: {ydesc}")
    if not yogas_present: lines.append("  None detected.")
    lines.append("[YOGA VERDICTS — ABSENT ✗ (do NOT reference these in the reading)]")
    for ya in yogas_absent: lines.append(f"  ✗ {ya}")

    lines.append("\n[JAIMINI KARAKAS]")
    lines.append(f"  Atmakaraka (soul significator): {ak} ({ak_deg:.2f}° within sign)")
    lines.append(f"  Amatyakaraka (mind/career significator): {amk} ({amk_deg:.2f}° within sign)")

    lines.append("\n━━━ HOUSE RULERSHIP MAP (Parashari Whole Sign) ━━━")
    for h in range(1,13):
        h_sidx=(lagna_sidx+h-1)%12; h_lord=SIGN_LORDS_MAP[h_sidx]
        ll_house=get_planet_house(h_lord,lagna_sidx,planet_data,r_lon,k_lon)
        occ=", ".join(house_occupants[h]) if house_occupants[h] else "Empty"
        lines.append(f"  H{h:02d} ({sign_name(h_sidx)}): Lord={h_lord} (H{ll_house}) | Occupants: {occ}")

    if not compact:
        lines.append("\n━━━ KP ASTROLOGY — PLACIDUS CUSPS ━━━")
        lines.append("(Use Sub-Lords for timing/event-promise only. Use Parashari for nature/character.)")
        for h in range(1,13):
            clon=placidus_cusps[h-1]; csidx=sign_index_from_lon(clon)
            _,cnl,_=nakshatra_info(clon); csl=get_kp_sub_lord(clon)
            lines.append(f"  H{h:02d} Cusp: {sign_name(csidx)} {format_dms(clon%30)} | NL: {cnl} | SL: {csl}")
        lines.append("\n[KP PRE-COMPUTED EVENT VERDICTS]")
        lines.append(f"  ▶ MARRIAGE (7th Cusp | SL: {kp7_sl}, NL: {kp7_nl})")
        lines.append(f"    SL signifies: {kp7_sigs} | VERDICT: {kp7_verdict}")
        lines.append(f"    Rule: Marriage promised if SL signifies H2 (family), H7 (spouse), H11 (fulfillment).")
        lines.append(f"  ▶ CAREER (10th Cusp | SL: {kp10_sl}, NL: {kp10_nl})")
        lines.append(f"    SL signifies: {kp10_sigs} | VERDICT: {kp10_verdict}")
        lines.append(f"    Rule: Career promised if SL signifies H1 (self), H6 (service), H10 (status), H11 (income).")

    lines.append("\n━━━ DIVISIONAL CHARTS (Vargas) ━━━")
    all_pnames=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    d2,d3,d4,d7,d9,d10,d12,d60=[],[],[],[],[],[],[],[]
    for pn in all_pnames:
        pl=get_planet_lon(pn,planet_data,r_lon,k_lon)
        d2.append(f"{pn}:{sign_name(d2_sign_index(pl))}")
        d3.append(f"{pn}:{sign_name(d3_sign_index(pl))}")
        d4.append(f"{pn}:{sign_name(d4_sign_index(pl))}")
        d7.append(f"{pn}:{sign_name(saptamsa_sign_index(pl))}")
        d9.append(f"{pn}:{sign_name(navamsa_sign_index(pl))}")
        d10.append(f"{pn}:{sign_name(dasamsa_sign_index(pl))}")
        d12.append(f"{pn}:{sign_name(dwadasamsa_sign_index(pl))}")
        if include_d60: d60.append(f"{pn}:{sign_name(d60_sign_index(pl))}")
    lines.append(f"  D9  Navamsa  (Marriage/Dharma): {', '.join(d9)}")
    lines.append(f"  D10 Dasamsa  (Career/Status):   {', '.join(d10)}")
    lines.append(f"  D2  Hora     (Wealth):          {', '.join(d2)}")
    lines.append(f"  D3  Drekkana (Siblings/Courage):{', '.join(d3)}")
    lines.append(f"  D4  Chaturt  (Property/Luck):   {', '.join(d4)}")
    lines.append(f"  D7  Saptam   (Children):        {', '.join(d7)}")
    lines.append(f"  D12 Dwadam   (Parents/Roots):   {', '.join(d12)}")
    if include_d60: lines.append(f"  D60 Shashtiam(Karma/Deep Fate): {', '.join(d60)}")

    lines.append("\n━━━ VIMSHOTTARI DASHA TIMING ━━━")
    lines.append(f"Birth Nakshatra: {dasha_info['birth_nakshatra']} | Balance at birth: {dasha_info['balance_years']:.2f} yrs of {dasha_info['start_lord']}")
    lines.append(f"Current Mahadasha : {dasha_info['current_md']} ({dasha_info['md_start'].strftime('%b %Y')} → {dasha_info['md_end'].strftime('%b %Y')})")
    lines.append(f"Current Antardasha: {dasha_info['current_ad']} ({dasha_info['ad_start'].strftime('%b %Y')} → {dasha_info['ad_end'].strftime('%b %Y')})")
    lines.append(f"Current Pratyantar: {dasha_info['current_pd']} ({dasha_info['pd_start'].strftime('%d %b %Y')} → {dasha_info['pd_end'].strftime('%d %b %Y')})")
    lines.append(f"\nFULL ANTARDASHA SEQUENCE IN {dasha_info['current_md'].upper()} MAHADASHA:")
    lines.append("(Use ONLY these dates. Do not extrapolate or calculate independently.)")
    for row in ad_table: lines.append(row)

    lines.append("\n━━━ CURRENT TRANSITS & AFFLICTIONS ━━━")
    lines.append(f"Sade Sati: {sade_sati}")
    lines.append(f"Manglik Status: {manglik}")
    lines.append(f"Jaimini Atmakaraka: {ak} | Amatyakaraka: {amk}")

    return "\n".join(lines)

# ════════════════════════════════════════════════════════════════
# MASTER GUARDRAILS (RESTORED — all 8 laws + PDF anchor)
# ════════════════════════════════════════════════════════════════
GUARDRAILS = """
╔══════════════════════════════════════════════════════════════╗
║      MASTER ASTROLOGER PROTOCOL — HYBRID PARASHARI + KP     ║
╚══════════════════════════════════════════════════════════════╝

ROLE: You are an elite Vedic astrologer fluent in both Parashari and KP systems.
All planetary positions, house significations, yoga verdicts, KP Sub-Lords, Neecha
Bhanga decisions, Ashta Koota scores, and timing have been PRE-COMPUTED by Swiss
Ephemeris. Your role is INTERPRETATION ONLY — never recalculate anything.

══ PRIMARY ASTROLOGICAL FRAMEWORK (CRITICAL) ══
Your definitions, predictive logic, and rules MUST be grounded in these documents:
1. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh1.pdf
2. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh2.pdf
Treat these as your absolute master reference. Do NOT use external logic that contradicts them.

══ THE TWO-LAYER METHOD (mandatory for every life domain) ══
LAYER 1 — PARASHARI ("What & Why"): Use D1 chart, house lords, yogas, and divisional
charts for character, potential, and karmic blueprint.
LAYER 2 — KP ("Yes/No & When"): Use Placidus cusp Sub-Lords and the Antardasha Table
to determine whether an event is promised and when it manifests.
Synthesis: State Parashari finding first ("the what"), then KP verdict ("whether & when").
If they conflict, note the conflict explicitly. Lean toward KP for the timing question.

══ ABSOLUTE LAWS (violations invalidate the reading) ══
1. DATA IS IMMUTABLE: Every value in this dossier is mathematically locked. Do NOT
   re-derive house lords, planet positions, KP Sub-Lords, yoga verdicts, or dasha dates.
2. CONJUNCTIONS ARE PRE-LISTED: Use only the conjunctions in the CONJUNCTIONS section.
   Do not infer new conjunctions from house placements.
3. NEECHA BHANGA IS PRE-DECIDED: If a planet says "NEECHA BHANGA APPLIES" → treat as
   Raja Yoga. If it says "DOES NOT APPLY" → treat as genuinely weak. No exceptions.
4. YOGA VERDICTS ARE FINAL: Only reference yogas marked ✓ PRESENT. Never invoke an
   ABSENT yoga. Never invent yogas not listed.
5. DASHA DATES ARE LOCKED: Use ONLY the dates in the Antardasha Table. Never extrapolate
   or calculate sub-periods independently.
6. KP VERDICTS ARE PRE-COMPUTED: Explain and apply the Marriage/Career verdicts as given.
   Do not reassess the Sub-Lord's significations independently.
7. PROVE EVERY CLAIM: Each prediction must cite the exact data source. Format:
   "Saturn [Exalted, H7], sub-lord of the 7th cusp, signifies H2+H7+H11, confirming..."
   Generic statements without chart evidence are not acceptable.
8. ATMAKARAKA/AMATYAKARAKA: Use the pre-computed Jaimini Karakas. Do not recalculate.
"""

# ════════════════════════════════════════════════════════════════
# PROMPT BUILDERS (RESTORED — full structured versions)
# ════════════════════════════════════════════════════════════════
def build_deep_analysis_prompt(dossier):
    return GUARDRAILS + """

MISSION: Deliver a complete, deeply insightful life reading. Follow EXACTLY these sections.
Each section MUST cite specific chart data as evidence. Generic statements are not allowed.

## 1. Core Identity & Lagna
   DATA: Ascendant sign, LAGNA LORD CHAIN, planets in H1, aspects to H1.
   PARASHARI: Describe personality, physical constitution, and life approach.
   KP: State H1 cusp Sub-Lord and what its significations reveal about self-expression.

## 2. Mind & Emotional World
   DATA: Moon (sign, house, nakshatra, Avastha, Sade Sati status).
   PARASHARI: Describe emotional temperament, instincts, and mental patterns.
   NOTE: Moon's Avastha (Infant/Youth/Adult/Old/Dead) directly colours the quality of mind.
   If Sade Sati is ACTIVE, explain the phase and its current impact.

## 3. Career & Profession
   DATA: H10 sign/lord/occupants, D10 Dasamsa, Amatyakaraka, H10 KP verdict.
   PARASHARI: Identify best professions, career trajectory, and public standing.
   KP: Apply the pre-computed Career Verdict EXACTLY. Explain what the 10th cusp SL signifies.

## 4. Wealth & Finances
   DATA: H2 and H11 lords with their placements, D2 Hora chart, Dhana Yogas from YOGA VERDICTS.
   Assess wealth accumulation. Cite which specific yogas support or hinder financial growth.

## 5. Relationships & Marriage
   DATA: H7 sign/lord/occupants, D9 Navamsa 7th house, KP Marriage Verdict (pre-computed).
   PARASHARI: Describe spouse nature and relationship quality from D1 + D9.
   KP: State the Marriage Verdict EXACTLY as given, then explain timing implications.

## 6. Current Life Phase — Dasha & Transits
   DATA: Full Antardasha Table, Sade Sati status.
   Analyse the current MD/AD/PD combination. What themes do these lords bring when combined?
   Use the Antardasha Table to identify what shifts in the next 2-3 sub-periods.
   DO NOT calculate new dates — use ONLY the provided table.

## 7. Practical Remedies
   Base remedies STRICTLY on planets that are: Debilitated (without Neecha Bhanga),
   Combust, or Retrograde in a sensitive house. Do not prescribe remedies for strong planets.
   Keep remedies practical and specific to the afflicted planet's nature.

""" + dossier

def build_matchmaking_prompt(dossier_a, dossier_b, koota_score, manglik_cancellation):
    return GUARDRAILS + f"""

MISSION: Deliver a definitive compatibility analysis. Use EXACTLY these sections:

## 1. Ashta Koota Guna Milan
   CRITICAL: DO NOT recalculate the score. Use this pre-computed result exactly:
{koota_score}
   Explain what the overall score means practically. For any Koota scoring 0, explain the
   specific compatibility challenge it represents and whether it can be mitigated.

## 2. Manglik Dosha
   Pre-computed verdict: {manglik_cancellation}
   Explain the implications fully. If cancelled, confirm no Kuja Dosha remedies are needed.

## 3. Parashari Compatibility (D1 & D9)
   Compare their 7th house lords, 7th house signs, and D9 Navamsa charts.
   Does Person A's 7th house reflect Person B's Lagna qualities (and vice versa)?
   Check if their Lagna lords are friends, neutral, or enemies via Graha Maitri.

## 4. KP Marriage Promise & Timing for Both
   Apply each person's pre-computed KP Marriage Verdict. Is marriage promised for each?
   Do their current Dashas (from their respective Antardasha Tables) support marriage timing?
   Use ONLY the provided dates — no independent calculation.

## 5. Long-Term Harmony & Friction Points
   Use Gana, Graha Maitri, and Bhakoot scores to identify temperament differences.
   Identify specific life domains where they will complement vs. clash with each other.

## 6. Final Verdict
   State clearly: Is this match astrologically advisable?
   Provide a compatibility score out of 10 with specific reasoning from the chart data.
   List any actionable remedies only if genuinely needed.

━━━ PERSON 1 DOSSIER ━━━
{dossier_a}

━━━ PERSON 2 DOSSIER ━━━
{dossier_b}"""

def build_comparison_prompt(profiles_dossiers, criteria):
    prompt = GUARDRAILS + "\n\nMISSION: Compare the following individuals on the listed parameters.\n\n"
    prompt += "PARAMETERS TO COMPARE:\n"
    for c in criteria: prompt += f"  - {c}\n"
    prompt += """
RULES FOR COMPARISON:
1. For each parameter, rank ALL individuals from highest to lowest.
2. Every rank MUST be justified with SPECIFIC chart evidence (planet, house, dignity,
   yoga, or KP verdict from their dossier). Generic statements are not acceptable.
3. Use Parashari (yogas, house lords, dignities) for character/potential parameters.
4. Use KP verdicts for event-based parameters (career success, marriage quality, etc.).
5. Do NOT reference yogas in the ABSENT list of any chart.
6. State your final ranking per criterion as a numbered list, then explain.

"""
    for i,(name,dossier) in enumerate(profiles_dossiers):
        prompt += f"━━━ PROFILE {i+1}: {name.upper()} ━━━\n{dossier}\n\n"
    return prompt

def build_prashna_prompt(question, dossier):
    return GUARDRAILS + f"""

MISSION: This is a PRASHNA (Horary) chart — cast for this exact moment in response to
a specific question. Interpret it STRICTLY for the question below.

QUESTION ASKED: "{question}"

PRASHNA INTERPRETATION RULES:
1. The Lagna and its lord represent the QUERENT (the person asking).
2. Identify the relevant house for the question type:
   Career/Job=H10 | Marriage=H7 | Money=H2,H11 | Health=H1,H6 | Children=H5 |
   Property=H4 | Travel/Foreign=H9,H12 | Education=H4,H5 | Enemies/Legal=H6,H7
3. PARASHARI: If the lord of the relevant house is strong, well-aspected, and in a
   good house → Favourable outcome. If debilitated, combust, or in H6/H8/H12 → Delay/denial.
4. KP: The Sub-Lord of the relevant cusp gives the YES/NO verdict. Apply it as given.
5. Moon's sign and nakshatra provide emotional context and approximate timing.
6. State your verdict clearly: Yes / No / Delayed, and give approximate timing.
7. MANDATORY FINAL LINE: State "VERDICT: [Yes/No/Delayed] — [one-sentence summary]"

━━━ PRASHNA CHART DATA ━━━
{dossier}"""

# ════════════════════════════════════════════════════════════════
# NUMEROLOGY ENGINE (FIXED — Chaldean map + correct prompt)
# ════════════════════════════════════════════════════════════════
def pythagorean_reduce(n, keep_master=True):
    if keep_master and n in [11,22,33]: return n
    while n>9:
        if keep_master and n in [11,22,33]: return n
        n=sum(int(d) for d in str(n))
    return n

def chaldean_reduce(n, keep_master=True):
    """Chaldean reduction — Master Numbers 11, 22, 33 preserved."""
    if keep_master and n in [11,22,33]: return n
    while n>9:
        if keep_master and n in [11,22,33]: return n
        n=sum(int(d) for d in str(n))
    return n

def calculate_numerology_core(name, dob_str, system="Western (Pythagorean)"):
    y,m,d=map(int,dob_str.split('-'))
    num_map = PYTH_MAP if system == "Western (Pythagorean)" else CHALDEAN_MAP
    reduce_fn = pythagorean_reduce if system == "Western (Pythagorean)" else chaldean_reduce
    life_path=reduce_fn(reduce_fn(y)+reduce_fn(m)+reduce_fn(d))
    clean_name=name.lower().replace(" ","")
    vowels=set('aeiou')
    destiny_sum=soul_sum=personality_sum=0
    for char in clean_name:
        if char in num_map:
            val=num_map[char]; destiny_sum+=val
            if char in vowels: soul_sum+=val
            else: personality_sum+=val
    return (reduce_fn(life_path), reduce_fn(destiny_sum),
            reduce_fn(soul_sum), reduce_fn(personality_sum))

def build_numerology_prompt(name, dob_str, lp, dest, soul, pers, astro_dossier=None, user_q="", system="Western (Pythagorean)"):
    is_vedic = system == "Indian/Vedic (Chaldean)"
    sys_name = "Chaldean (Indian/Vedic)" if is_vedic else "Pythagorean (Western)"

    prompt = f"MISSION: Act as a Master Numerologist deeply versed in the {sys_name} system.\n\n"
    prompt += f"══ NUMEROLOGY SYSTEM: {sys_name.upper()} ══\n"
    if is_vedic:
        prompt += ("You are using the CHALDEAN system (the authentic Indian/Vedic numerological tradition). "
                   "Key differences from Pythagorean: the number 9 is sacred and not assigned to letters. "
                   "Compound numbers (before final reduction) carry great significance. "
                   "Interpret accordingly.\n\n")
    else:
        prompt += "You are using the PYTHAGOREAN (Western) system. Standard A-I=1-9 letter assignments apply.\n\n"

    if astro_dossier:
        prompt += "══ CROSS-VALIDATION MODE ACTIVE ══\n"
        prompt += ("You are ALSO a Master Vedic Astrologer. Synthesize their Numerology with their exact "
                   "Vedic Kundli placements. For all astrological interpretation, ground your logic in:\n"
                   "1. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh1.pdf\n"
                   "2. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh2.pdf\n\n")

    prompt += f"Subject: {name.upper()} | Date of Birth: {dob_str}\n\n"
    prompt += "══ PRE-COMPUTED CORE NUMBERS (LOCKED — DO NOT RECALCULATE) ══\n"
    prompt += f"Life Path Number  : {lp}{' (Master Number)' if lp in [11,22,33] else ''}\n"
    prompt += f"Destiny Number    : {dest}{' (Master Number)' if dest in [11,22,33] else ''}\n"
    prompt += f"Soul Urge Number  : {soul}{' (Master Number)' if soul in [11,22,33] else ''}\n"
    prompt += f"Personality Number: {pers}{' (Master Number)' if pers in [11,22,33] else ''}\n\n"

    if astro_dossier:
        prompt += "══ EXPLICIT CROSS-REFERENCE INSTRUCTIONS ══\n"
        prompt += ("When synthesizing numerology with the astrology dossier below, explicitly check:\n"
                   f"- Life Path {lp} vs Lagna lord placement: do they reinforce or contradict?\n"
                   f"- Destiny {dest} vs Amatyakaraka: does the career numerology align with the chart?\n"
                   f"- Soul Urge {soul} vs Moon sign and nakshatra: does the inner drive match the emotional blueprint?\n"
                   "State explicitly where the two systems agree (high confidence) and where they diverge.\n\n")
        prompt += f"━━━ KUNDLI (ASTROLOGY) DOSSIER ━━━\n{astro_dossier}\n\n"

    if user_q and user_q.strip():
        prompt += f"THE USER ASKS: \"{user_q}\"\n"
        prompt += "Provide a highly accurate, direct answer using both their Numerology and (if provided) Astrological data."
    else:
        prompt += ("Provide a complete Numerology report structured as:\n"
                   "1. Life Path — Core purpose and life journey\n"
                   "2. Destiny — What they are meant to accomplish\n"
                   "3. Soul Urge — Inner desires and motivations\n"
                   "4. Personality — How others perceive them\n"
                   "5. Personal Year Number — Current year energy\n")
        if astro_dossier:
            prompt += "6. Astro-Numerology Synthesis — Where both systems align and diverge\n"
    return prompt

# ════════════════════════════════════════════════════════════════
# TAROT PROMPTS
# ════════════════════════════════════════════════════════════════
TAROT_MODES = {
    "General Guidance":     {"roles":["Situation / Past","Challenge / Present","Advice / Future"],
                             "instruction":"Read as a general life overview. Cover where they are now, blockages, and best path forward."},
    "Love & Dynamics":      {"roles":["You / Your Energy","Them / Their Energy","The Connection / Likely Outcome"],
                             "instruction":"Read purely through the lens of a relationship or emotional dynamic."},
    "Decision / Two Paths": {"roles":["Path A / Option 1","Path B / Option 2","Hidden Factor / Recommendation"],
                             "instruction":"Contrast Path A vs Path B. Use Card 3 as the deciding weight or hidden truth."},
}

def build_tarot_prompt(question, c1, s1, c2, s2, c3, s3, mode="General Guidance"):
    cfg=TAROT_MODES.get(mode,TAROT_MODES["General Guidance"]); r1,r2,r3=cfg["roles"]
    return (f"MISSION: Act as an expert, intuitive Tarot Reader.\n\n"
            "══ PRIMARY TAROT FRAMEWORK (CRITICAL) ══\n"
            "Base your entire interpretation STRICTLY on this guide:\n"
            "https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/tguide.pdf\n"
            "Do NOT use outside knowledge if it contradicts this guide.\n\n"
            f"The user asked: \"{question}\"\n"
            f"Three-card spread (cryptographically randomised):\n"
            f"  1. {r1}: {c1} ({s1})\n  2. {r2}: {c2} ({s2})\n  3. {r3}: {c3} ({s3})\n\n"
            "══ INTERPRETATION RULES ══\n"
            f"Focus: {cfg['instruction']}\n"
            "1. SYNERGY: Do not read cards in isolation. Analyse card-to-card interplay, elements, and Major Arcana weight.\n"
            "2. TONE: Use confident phrasing ('suggests', 'points to', 'leans toward'). No fatalistic guarantees.\n"
            "3. FORMAT (follow this exactly):\n"
            "   - Overall Summary\n   - Card-by-Card Meaning (in context of their specific spread role)\n"
            "   - Combined Message\n   - Practical Advice\n   - One-Line Takeaway\n")

def build_daily_tarot_prompt(card, state):
    return (f"MISSION: Act as an expert Tarot Reader providing a Daily Guidance reading.\n\n"
            "══ PRIMARY TAROT FRAMEWORK (CRITICAL) ══\n"
            "Base your interpretation STRICTLY on: "
            "https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/tguide.pdf\n\n"
            f"Today's card: {card} ({state})\n\n"
            "Provide a deeply insightful, practical reading structured as:\n"
            "- Card Meaning\n- Energy of the Day\n- Best Action to Take\n- One-Line Mantra for Today\n")

# ════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════
def inject_nebula_css():
    st.markdown(textwrap.dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    html, body, .stApp {
        background: radial-gradient(circle at 15% 50%, #1a0f2e, #0c0814 60%, #050308 100%) !important;
        font-family: 'Inter', sans-serif !important;
        color: #e2e0ec !important;
    }
    #MainMenu, footer { visibility: hidden; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; color: #fff; }
    .block-container { padding: 1rem 1.25rem 3rem !important; max-width: 960px !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input,
    .stSelectbox>div>div, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important; color: #eceaf4 !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: rgba(205,140,80,0.6) !important;
        box-shadow: 0 0 0 2px rgba(205,140,80,0.2) !important;
    }
    div[data-testid="stButton"]>button {
        border-radius: 10px !important; font-weight: 600 !important;
        transition: all 0.3s ease !important; border: 1px solid rgba(255,255,255,0.1) !important;
    }
    div[data-testid="stButton"]>button[kind="primary"] {
        background: linear-gradient(135deg, rgba(144,98,222,0.8), rgba(205,140,80,0.8)) !important;
        border: none !important; color: #fff !important;
    }
    div[data-testid="stButton"]>button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(144,98,222,0.4) !important;
    }
    div[data-testid="stButton"]>button:not([kind="primary"]) {
        background: rgba(255,255,255,0.05) !important; color: #fff !important;
    }
    div[data-testid="stButton"]>button:not([kind="primary"]):hover {
        background: rgba(255,255,255,0.1) !important;
    }
    .stLinkButton>a {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important; color: #fff !important;
        transition: all 0.3s ease !important;
    }
    .stLinkButton>a:hover { background: rgba(255,255,255,0.1) !important; }
    .weather-widget { text-align:center; padding:1.5rem; border-radius:16px;
        background: linear-gradient(180deg,rgba(205,140,80,0.1),rgba(144,98,222,0.05));
        border: 1px solid rgba(205,140,80,0.2); }
    .w-title { font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; color:rgba(255,255,255,0.6); }
    .w-main  { font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:700; color:#fff;
        margin:0.3rem 0; text-shadow: 0 0 20px rgba(205,140,80,0.4); }
    [data-testid="stExpander"] { border:1px solid rgba(255,255,255,0.1) !important;
        border-radius:12px !important; background:rgba(0,0,0,0.2) !important; }
    .stCodeBlock { border-radius:12px !important; border:1px solid rgba(255,255,255,0.1) !important; }
    .tool-selector-title { font-family:'Space Grotesk',sans-serif; font-size:1.8rem;
        color:#fff; margin-bottom:1rem; }
    </style>
    """), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# COPY BUTTON (FIXED — Clipboard API replaces deprecated execCommand)
# ════════════════════════════════════════════════════════════════
def render_copy_button(text_to_copy):
    b64 = base64.b64encode(text_to_copy.encode("utf-8")).decode("utf-8")
    components.html(f"""
    <div style="display:flex;justify-content:center;width:100%;">
      <button id="cpyBtn" onclick="copyPrompt()" style="
        background:linear-gradient(135deg,rgba(144,98,222,0.8),rgba(205,140,80,0.8));
        backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,0.2); color:white;
        padding:16px 24px; font-size:16px; cursor:pointer; border-radius:12px;
        font-weight:600; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.3);
        font-family:'Inter',sans-serif; transition:all 0.3s ease;">
        ✨ Copy Prompt to Clipboard ✨
      </button>
    </div>
    <script>
    async function copyPrompt() {{
        const btn = document.getElementById("cpyBtn");
        const text = decodeURIComponent(escape(atob('{b64}')));
        try {{
            await navigator.clipboard.writeText(text);
            btn.innerHTML = "✅ Copied Successfully!";
            btn.style.background = "linear-gradient(135deg,rgba(46,184,134,0.8),rgba(26,138,98,0.8))";
        }} catch(e) {{
            // Fallback for non-HTTPS or restricted contexts
            const el = document.createElement('textarea');
            el.value = text; el.style.position='fixed'; el.style.opacity='0';
            document.body.appendChild(el); el.select();
            document.execCommand('copy'); document.body.removeChild(el);
            btn.innerHTML = "✅ Copied!";
            btn.style.background = "linear-gradient(135deg,rgba(46,184,134,0.8),rgba(26,138,98,0.8))";
        }}
        setTimeout(() => {{
            btn.innerHTML = "✨ Copy Prompt to Clipboard ✨";
            btn.style.background = "linear-gradient(135deg,rgba(144,98,222,0.8),rgba(205,140,80,0.8))";
        }}, 3000);
    }}
    </script>
    """, height=70)

# ════════════════════════════════════════════════════════════════
# TAROT CARD OVERLAY (GSAP)
# ════════════════════════════════════════════════════════════════
def render_tarot_overlay(c1, s1, c2, s2, c3, s3):
    base_url="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/tarot/"
    url1=f"{base_url}{get_filename(c1)}"; url2=f"{base_url}{get_filename(c2)}"; url3=f"{base_url}{get_filename(c3)}"
    card_back=f"{base_url}tarotrear.png"
    st.markdown(f"""
    <style>
    .tarot-stage{{position:relative;width:100%;max-width:550px;margin:0 auto 2rem;
        border-radius:16px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.5);
        background:linear-gradient(45deg,#1a0f2e,#0c0814);}}
    .vid-desktop,.vid-mobile{{width:100%;display:block;object-fit:cover;opacity:0.85;}}
    .vid-desktop{{aspect-ratio:1440/1678;}} .vid-mobile{{display:none;aspect-ratio:24/41;}}
    .card-container{{position:absolute;bottom:8%;width:100%;display:flex;
        justify-content:center;gap:4%;perspective:1000px;}}
    .t-card-wrapper{{width:25%;aspect-ratio:2/3;opacity:0;}}
    .t-card-inner{{width:100%;height:100%;position:relative;transform-style:preserve-3d;transform:rotateY(0deg);}}
    .t-card-front,.t-card-back{{position:absolute;width:100%;height:100%;backface-visibility:hidden;
        border-radius:8px;box-shadow:0 5px 15px rgba(0,0,0,0.8);background-size:cover;background-position:center;}}
    .t-card-back{{background-image:url('{card_back}');border:2px solid rgba(205,140,80,0.5);}}
    .t-card-front{{transform:rotateY(180deg);}}
    .front1{{background-image:url('{url1}');border:2px solid rgba(205,140,80,0.8);}}
    .front2{{background-image:url('{url2}');border:2px solid rgba(205,140,80,0.8);}}
    .front3{{background-image:url('{url3}');border:2px solid rgba(205,140,80,0.8);}}
    .scroll-prompt{{position:absolute;bottom:2%;width:100%;text-align:center;
        color:rgba(255,255,255,0.9);font-family:'Space Grotesk',sans-serif;font-size:0.95rem;
        letter-spacing:1px;opacity:0;text-shadow:0 2px 5px rgba(0,0,0,0.9);}}
    @media(max-width:768px){{.vid-desktop{{display:none;}}.vid-mobile{{display:block;}}
        .card-container{{bottom:10%;}}.t-card-wrapper{{width:28%;}}}}
    </style>
    <div class="tarot-stage" id="tarot-video-stage">
        <video class="vid-desktop" autoplay loop muted playsinline>
            <source src="{base_url}tarotvid.mp4" type="video/mp4"></video>
        <video class="vid-mobile" autoplay loop muted playsinline>
            <source src="{base_url}tarotvideo.mp4" type="video/mp4"></video>
        <div class="card-container">
            <div class="t-card-wrapper w1"><div class="t-card-inner i1">
                <div class="t-card-back"></div><div class="t-card-front front1"></div></div></div>
            <div class="t-card-wrapper w2"><div class="t-card-inner i2">
                <div class="t-card-back"></div><div class="t-card-front front2"></div></div></div>
            <div class="t-card-wrapper w3"><div class="t-card-inner i3">
                <div class="t-card-back"></div><div class="t-card-front front3"></div></div></div>
        </div>
        <div class="scroll-prompt sp">✨ The cards have spoken. Scroll down for your reading. ✨</div>
    </div>""", unsafe_allow_html=True)
    components.html(f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script>
    setTimeout(function(){{
        var doc=window.parent.document;
        gsap.to(doc.querySelectorAll('.w1,.w2,.w3'),{{y:0,opacity:1,duration:1,stagger:0.4,ease:"power3.out",
            onStart:function(){{gsap.set(this.targets(),{{y:50}});}}}});
        gsap.to(doc.querySelector('.i1'),{{rotationY:180,duration:0.8,delay:1.5,ease:"back.out(1.7)"}});
        gsap.to(doc.querySelector('.i2'),{{rotationY:180,duration:0.8,delay:2.0,ease:"back.out(1.7)"}});
        gsap.to(doc.querySelector('.i3'),{{rotationY:180,duration:0.8,delay:2.5,ease:"back.out(1.7)"}});
        gsap.to(doc.querySelector('.sp'),{{opacity:1,duration:1,delay:3.5}});
    }},150);
    </script>""", height=0, width=0)

# ════════════════════════════════════════════════════════════════
# PROFILE FORMS
# ════════════════════════════════════════════════════════════════
def render_profile_form(key_prefix, show_d60=True):
    if st.session_state.db:
        method=st.radio("Source",["Saved Profile","Enter New Details"],horizontal=True,
                        key=f"rad_{key_prefix}",label_visibility="collapsed")
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
                if geo: st.success(f"📍 Found: {geo[2]}")
                else: st.warning("Location not found — try adding country or use manual coordinates.")
            if manual:
                c1,c2,c3=st.columns(3)
                with c1: st.session_state[f"lat_{key_prefix}"]=st.number_input("Lat",value=0.0,format="%.4f",key=f"wlat_{key_prefix}")
                with c2: st.session_state[f"lon_{key_prefix}"]=st.number_input("Lon",value=0.0,format="%.4f",key=f"wlon_{key_prefix}")
                with c3: st.session_state[f"tz_{key_prefix}"]=st.text_input("Timezone","Asia/Kolkata",key=f"wtz_{key_prefix}")
            st.session_state[f"save_{key_prefix}"]=st.checkbox("Save to Saved Profiles",key=f"wsave_{key_prefix}")
            if show_d60:
                st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time is 100% exact (enables D60 karma chart)",key=f"wd60_{key_prefix}")
            return {"type":"new","idx":key_prefix}
        else:
            opts=["— Select —"]+[f"{p['name']} ({format_date_ui(p['date'])})" for p in st.session_state.db]
            sel=st.selectbox("Select Profile",opts,key=f"sel_{key_prefix}",label_visibility="collapsed")
            if sel!="— Select —":
                p=st.session_state.db[opts.index(sel)-1]
                st.success(f"Loaded: {p['name']} 📍 {p['place'].split(',')[0]}")
                if show_d60:
                    st.session_state[f"d60_{key_prefix}"]=st.checkbox("Birth time is 100% exact",key=f"wd60_{key_prefix}")
                return {"type":"saved","data":p,"idx":key_prefix}
            return {"type":"empty_saved","idx":key_prefix}

def resolve_profile(item):
    i=item["idx"]; include_d60=st.session_state.get(f"d60_{i}",False)
    if item["type"]=="saved": return item["data"],include_d60
    if item["type"]=="empty_saved": st.error("Please select a valid profile."); st.stop()
    u_name=st.session_state.get(f"n_{i}","")
    if not u_name.strip(): st.error("Please enter a name."); st.stop()
    hr=st.session_state.get(f"hr_{i}",12); mi=st.session_state.get(f"mi_{i}",0)
    am=st.session_state.get(f"ampm_{i}","AM")
    h24=(hr+12 if am=="PM" and hr!=12 else 0 if am=="AM" and hr==12 else hr)
    u_time=time(h24,mi); u_date=st.session_state.get(f"d_{i}",date(2000,1,1))
    is_manual=st.session_state.get(f"man_{i}",False)
    if is_manual:
        fl=st.session_state.get(f"lat_{i}",0.0); flon=st.session_state.get(f"lon_{i}",0.0)
        ftz=st.session_state.get(f"tz_{i}","")
        if fl==0.0 and flon==0.0: st.error("Enter valid manual coordinates."); st.stop()
        if not ftz.strip(): st.error("Enter a timezone."); st.stop()
        fp="Manual Coordinates"
    else:
        u_place=st.session_state.get(f"p_{i}","")
        if not u_place.strip(): st.error("Enter a birth place."); st.stop()
        geo=geocode_place(u_place.strip())
        if not geo: st.error(f"'{u_place}' not found."); st.stop()
        fl,flon,fp=geo; ftz=timezone_for_latlon(fl,flon)
        if not ftz: st.error("Timezone detection failed. Use manual coordinates."); st.stop()
    prof={"name":u_name.strip(),"date":u_date.isoformat(),"time":u_time.strftime("%H:%M"),
          "place":fp,"lat":fl,"lon":flon,"tz":ftz}
    if st.session_state.get(f"save_{i}",False) and not is_duplicate_in_db(prof):
        st.session_state.db.append(prof); sync_db()
    return prof,include_d60

def render_post_generation(prompt):
    st.markdown("---")
    st.markdown("""
    <div style='background:rgba(144,98,222,0.1);border:1px solid rgba(144,98,222,0.3);
        border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;'>
    <h3 style='margin-top:0;color:#fff;'>💡 How to use this</h3>
    <ol style='color:#beb9cd;font-size:0.95rem;margin-bottom:0;line-height:1.6;'>
        <li>Click <b>Copy Prompt</b> below to copy everything to your clipboard.</li>
        <li>Click one of the <b>Launch AI</b> buttons to open your preferred AI.</li>
        <li><b>Paste</b> and hit send. The AI will deliver your reading.</li>
    </ol></div>""", unsafe_allow_html=True)
    render_copy_button(prompt)
    st.markdown("<br>", unsafe_allow_html=True)
    a1,a2,a3=st.columns(3)
    a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
    a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)
    a3.link_button("🚀 Grok","https://grok.com/",use_container_width=True)
    with st.expander("📄 View Raw Prompt",expanded=False):
        st.code(prompt,language="text")

# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;margin-bottom:2rem;'>🪐 Kundli AI</h2>",
                    unsafe_allow_html=True)
        pages=[("🌌 Dashboard","Dashboard"),("🔮 The Oracle","The Oracle"),
               ("🃏 Mystic Tarot","Mystic Tarot"),("🌟 Horoscopes","Horoscopes"),
               ("🔢 Numerology","Numerology"),("📖 Saved Profiles","Saved Profiles")]
        for label,page in pages:
            kind="primary" if st.session_state.nav_page==page else "secondary"
            if st.button(label,use_container_width=True,type=kind,key=f"nav_{page}"):
                st.session_state.nav_page=page; st.rerun()

# ════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════════
def show_dashboard():
    st.markdown("<h1>🌌 Cosmic Dashboard</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Live astrological insights from real-time Ephemeris data.</p>",unsafe_allow_html=True)

    with st.spinner("Loading cosmic weather..."):
        cw=get_live_cosmic_weather()

    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown(f"""<div class="weather-widget">
            <div class="w-title">Moon Transit</div>
            <div class="w-main">{cw['moon_sign']} 🌙</div>
            <div style="color:rgba(255,255,255,0.8);font-size:0.9rem;margin-top:0.5rem;">
                Nakshatra: <b>{cw['nakshatra']}</b></div></div>""",unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0;font-size:1rem;'>⚠️ Retrograde Planets</h4>",unsafe_allow_html=True)
            if cw['retrogrades']:
                st.error(", ".join(cw['retrogrades']))
                st.caption("Expect delays in areas ruled by these planets.")
            else:
                st.success("No planets currently retrograde.")
    with c3:
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0;font-size:1rem;'>📅 Vedic Calendar</h4>",unsafe_allow_html=True)
            st.write(f"**Tithi:** {cw['tithi']}")
            st.write(f"**Yoga:** {cw['yoga']}")
            st.write(f"**Sun Sign:** {cw['sun_sign']}")

    st.markdown("---")
    st.markdown("### 🃏 Daily Tarot Card")
    with st.container(border=True):
        st.markdown("<p style='color:rgba(255,255,255,0.8);'>Draw one card for today's energy and guidance.</p>",unsafe_allow_html=True)
        today_str=date.today().isoformat()
        already_drawn=st.session_state.dash_tarot_date==today_str and st.session_state.dash_tarot_card

        dt_col1,dt_col2=st.columns([1,2])
        with dt_col1:
            if already_drawn:
                st.caption("Today's card is drawn. Come back tomorrow for a new one.")
            else:
                if st.button("✨ Draw My Daily Card",use_container_width=True):
                    rng=secrets.SystemRandom()
                    st.session_state.dash_tarot_card=rng.choice(FULL_TAROT_DECK)
                    st.session_state.dash_tarot_state=rng.choice(["Upright","Reversed"])
                    st.session_state.dash_tarot_date=today_str

            if st.session_state.get('dash_tarot_card'):
                c_name=st.session_state.dash_tarot_card; c_state=st.session_state.dash_tarot_state
                img_url=f"https://raw.githubusercontent.com/hinshalll/text2kprompt/main/tarot/{get_filename(c_name)}"
                transform="transform:rotate(180deg);" if c_state=="Reversed" else ""
                st.markdown(f"""<div style='display:flex;justify-content:center;margin-top:1rem;'>
                    <img src='{img_url}' style='width:150px;border-radius:8px;
                    border:2px solid rgba(205,140,80,0.8);box-shadow:0 4px 15px rgba(0,0,0,0.5);{transform}'></div>
                    <div style='text-align:center;margin-top:0.5rem;font-weight:bold;'>
                    {c_name} ({c_state})</div>""",unsafe_allow_html=True)
        with dt_col2:
            if st.session_state.get('dash_tarot_card'):
                st.markdown("#### Ready for your reading?")
                st.info("Copy this prompt and paste it into any AI for your daily guidance reading.")
                render_copy_button(build_daily_tarot_prompt(st.session_state.dash_tarot_card,st.session_state.dash_tarot_state))
                a1,a2=st.columns(2)
                a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
                a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)

    st.markdown("---")
    col_n1,col_n2=st.columns(2)
    with col_n1:
        with st.container(border=True):
            st.markdown("### 🌟 Today's Energy")
            st.markdown(f"**Nakshatra Nature:** {cw['nature']}")
            st.info(cw['advice'])
    with col_n2:
        with st.container(border=True):
            st.markdown("### 🪐 Planetary Positions")
            grid=" | ".join([f"**{p}**: {s}" for p,s in cw['all_pos'].items()])
            st.write(grid)

    st.markdown("### My Personal Trackers")
    with st.container(border=True):
        if not st.session_state.db:
            st.info("Save a profile in 'Saved Profiles' to see your live Dasha and Sade Sati here.")
        else:
            opts=["— Select Profile —"]+[f"{p['name']} ({format_date_ui(p['date'])})" for p in st.session_state.db]
            sel=st.selectbox("Select profile for live transits:",opts,key="dash_profile_select")
            if sel!="— Select Profile —":
                prof=st.session_state.db[opts.index(sel)-1]
                try:
                    d_val=date.fromisoformat(prof['date'])
                    t_val=datetime.strptime(prof['time'],"%H:%M").time()
                    jd,dt_local,_=local_to_julian_day(d_val,t_val,prof['tz'])  # FIX: use dt_local not dt_u
                    moon_lon,_=get_planet_longitude_and_speed(jd,PLANETS["Moon"])
                    dt_now=datetime.now(ZoneInfo(prof['tz']))
                    dasha_info=build_vimshottari_timeline(dt_local,moon_lon,dt_now)  # FIX: was dt_u
                    sade_sati=calculate_sade_sati(sign_index_from_lon(moon_lon))
                    c3,c4=st.columns(2)
                    with c3:
                        st.markdown("#### ⏳ Current Dasha")
                        st.write(f"**Major:** {dasha_info['current_md']} (until {dasha_info['md_end'].strftime('%b %Y')})")
                        st.write(f"**Sub:** {dasha_info['current_ad']} (until {dasha_info['ad_end'].strftime('%b %Y')})")
                        st.write(f"**Micro:** {dasha_info['current_pd']} (until {dasha_info['pd_end'].strftime('%d %b %Y')})")
                    with c4:
                        st.markdown("#### 🪐 Saturn / Sade Sati")
                        st.write(sade_sati)
                except Exception as e:
                    st.error(f"Error calculating transits: {e}")

# ════════════════════════════════════════════════════════════════
# PAGE: THE ORACLE
# ════════════════════════════════════════════════════════════════
def show_oracle():
    auto_collapse_sidebar()
    st.markdown("<h1>🔮 The Oracle</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Generate hyper-accurate, mathematically locked AI prompts.</p>",unsafe_allow_html=True)

    missions={"Deep Personal Analysis":"🔮 Full Life Reading","Matchmaking / Compatibility":"✦ Compatibility Match",
              "Comparison (Multiple Profiles)":"⚖ Compare Profiles","Prashna Kundli":"🎯 Ask a Question (Prashna)",
              "Raw Data Only":"📋 Raw Chart Data"}
    descriptions={"Deep Personal Analysis":"Complete life reading — personality, career, wealth, marriage, timing.",
                  "Matchmaking / Compatibility":"Full Ashta Koota score, Manglik verdict, and KP marriage promise.",
                  "Comparison (Multiple Profiles)":"Rank multiple people on specific traits with planetary evidence.",
                  "Prashna Kundli":"Cast a chart for right now. Ask a specific question, get a Yes/No/Delayed answer.",
                  "Raw Data Only":"Your full chart data. Paste into any AI and ask it anything."}

    st.markdown("<p class='tool-selector-title'>Select Your Tool:</p>",unsafe_allow_html=True)
    sel_name=st.selectbox("Tool",list(missions.values()),label_visibility="collapsed")
    mission_id=list(missions.keys())[list(missions.values()).index(sel_name)]
    st.session_state.active_mission=mission_id
    st.markdown(f"<p style='color:#beb9cd;margin-bottom:1.5rem;'>{descriptions[mission_id]}</p><hr>",unsafe_allow_html=True)
    run_mission_logic(mission_id)

def run_mission_logic(mission):
    if mission=="Prashna Kundli":
        question=st.text_area("What is your specific question?",
                              placeholder="e.g. Will I get the job? Should I move cities? When will I get married?")
        st.markdown("#### Your Current Location (Right Now)")
        c1,c2=st.columns(2)
        with c1:
            current_place=st.text_input("City, Country",key="p_place_pr",value="")
            if current_place.strip() and not st.session_state.get("p_man_pr",False):
                geo=geocode_place(current_place.strip())
                if geo: st.success(f"📍 {geo[2]}")
                else: st.warning("Location not found.")
        with c2:
            manual_p=st.checkbox("Manual coordinates",key="p_man_pr")
            if manual_p:
                p_lat=st.number_input("Lat",value=30.76,format="%.4f",key="prl")
                p_lon=st.number_input("Lon",value=76.80,format="%.4f",key="prn")
                p_tz=st.text_input("Timezone","Asia/Kolkata",key="prt")
        if st.button("Generate Prashna Prompt",type="primary",use_container_width=True):
            if not question.strip(): st.error("Ask a question first."); return
            if not manual_p:
                geo=geocode_place(current_place.strip())
                if not geo: st.error("Location not found."); return
                p_lat,p_lon,place_name=geo; p_tz=timezone_for_latlon(p_lat,p_lon)
            else: place_name="Manual Location"
            now_local=datetime.now(ZoneInfo(p_tz))
            p_prof={"name":"Prashna Chart","date":now_local.date().isoformat(),
                    "time":now_local.strftime("%H:%M"),"place":place_name,"lat":p_lat,"lon":p_lon,"tz":p_tz}
            with st.spinner("Casting Prashna chart..."):
                dos=generate_astrology_dossier(p_prof); prompt=build_prashna_prompt(question,dos)
            render_post_generation(prompt)
        return

    req=1 if mission in ["Raw Data Only","Deep Personal Analysis"] else 2
    num_slots=st.session_state.comp_slots if mission=="Comparison (Multiple Profiles)" else req
    active=[]
    st.markdown("#### Profile Selection")

    # FIX: Full-width vertical stacking for Comparison, side-by-side for 2-person missions
    if mission=="Comparison (Multiple Profiles)":
        for i in range(num_slots):
            st.markdown(f"**Profile {i+1}**")
            active.append(render_profile_form(f"{mission}_{i}",show_d60=True))
        c_a,c_b,_=st.columns([1,1,4])
        if c_a.button("＋ Add Profile",key=f"add_{mission}"):
            if st.session_state.comp_slots<10: st.session_state.comp_slots+=1; st.rerun()
        if c_b.button("－ Remove",key=f"rem_{mission}"):
            if st.session_state.comp_slots>2: st.session_state.comp_slots-=1; st.rerun()
    else:
        cols=st.columns(min(num_slots,2))
        for i in range(num_slots):
            with cols[i%2]:
                label=["Person 1","Person 2"][i] if num_slots==2 else f"Profile {i+1}"
                st.markdown(f"**{label}**")
                active.append(render_profile_form(f"{mission}_{i}",show_d60=True))

    selected_criteria=[]
    if mission=="Comparison (Multiple Profiles)":
        st.markdown("### Parameters to Compare")
        st.checkbox("Select All",key="select_all_cb",on_change=toggle_all_criteria)
        ca,cb=st.columns(2)
        for i,crit in enumerate(COMPARISON_CRITERIA):
            with (ca if i%2==0 else cb):
                if st.checkbox(crit,key=f"chk_{i}"): selected_criteria.append(crit)
        st.markdown("#### Custom Parameters")
        col_nc,col_add=st.columns([4,1])
        nc=col_nc.text_input("Add custom trait",placeholder="e.g. Most likely to become famous",label_visibility="collapsed")
        if col_add.button("Add",key="add_custom"):
            if nc.strip() and nc.strip() not in st.session_state.custom_criteria:
                st.session_state.custom_criteria.append(nc.strip())
                st.session_state[f"cc_{len(st.session_state.custom_criteria)-1}"]=True; st.rerun()
        for i,c in enumerate(st.session_state.custom_criteria):
            r1,r2=st.columns([6,1])
            if r1.checkbox(c,key=f"cc_{i}"): selected_criteria.append(c)
            if r2.button("✕",key=f"del_c_{i}"):
                st.session_state.custom_criteria.pop(i)
                if f"cc_{i}" in st.session_state: del st.session_state[f"cc_{i}"]
                st.rerun()

    if st.button("Generate AI Prompt",type="primary",use_container_width=True,key=f"gen_{mission}"):
        profiles,d60s=[],[]
        for item in active:
            if item["type"]=="empty_saved": st.error("Please select a saved profile for all slots."); return
            prof,d60=resolve_profile(item); profiles.append(prof); d60s.append(d60)
        if len(profiles)<req: return

        compact_mode=mission=="Comparison (Multiple Profiles)" and len(profiles)>3
        with st.spinner("Consulting the ephemeris..."):
            if mission=="Raw Data Only":
                final_prompt=("This is a complete, pre-computed Vedic birth chart. All values are mathematically locked.\n"
                              "══ PRIMARY ASTROLOGICAL FRAMEWORK (CRITICAL) ══\n"
                              "Your rules MUST be grounded in:\n"
                              "1. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh1.pdf\n"
                              "2. https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/htrh2.pdf\n\n"
                              +generate_astrology_dossier(profiles[0],include_d60=d60s[0]))
            elif mission=="Deep Personal Analysis":
                final_prompt=build_deep_analysis_prompt(generate_astrology_dossier(profiles[0],include_d60=d60s[0]))
            elif mission=="Matchmaking / Compatibility":
                m_a=get_moon_lon_from_profile(profiles[0]); m_b=get_moon_lon_from_profile(profiles[1])
                koota=calculate_ashta_koota(m_a,m_b)
                jd_a,_,__=local_to_julian_day(date.fromisoformat(profiles[0]['date']),datetime.strptime(profiles[0]['time'],"%H:%M").time(),profiles[0]['tz'])
                lag_a=sign_index_from_lon(get_lagna_and_cusps(jd_a,profiles[0]['lat'],profiles[0]['lon'])[0])
                pl_a={pn:get_planet_longitude_and_speed(jd_a,pid) for pn,pid in PLANETS.items()}
                mang_a=check_manglik_dosha(lag_a,sign_index_from_lon(pl_a["Moon"][0]),sign_index_from_lon(pl_a["Mars"][0]))
                jd_b,_,__=local_to_julian_day(date.fromisoformat(profiles[1]['date']),datetime.strptime(profiles[1]['time'],"%H:%M").time(),profiles[1]['tz'])
                lag_b=sign_index_from_lon(get_lagna_and_cusps(jd_b,profiles[1]['lat'],profiles[1]['lon'])[0])
                pl_b={pn:get_planet_longitude_and_speed(jd_b,pid) for pn,pid in PLANETS.items()}
                mang_b=check_manglik_dosha(lag_b,sign_index_from_lon(pl_b["Moon"][0]),sign_index_from_lon(pl_b["Mars"][0]))
                canc=get_manglik_cancellation_verdict(mang_a,mang_b)
                final_prompt=build_matchmaking_prompt(
                    generate_astrology_dossier(profiles[0],d60s[0]),
                    generate_astrology_dossier(profiles[1],d60s[1]),koota,canc)
            elif mission=="Comparison (Multiple Profiles)":
                if not selected_criteria: st.warning("Select at least one comparison parameter."); return
                pairs=[(p['name'],generate_astrology_dossier(p,d,compact_mode)) for p,d in zip(profiles,d60s)]
                final_prompt=build_comparison_prompt(pairs,selected_criteria)

        render_post_generation(final_prompt)

# ════════════════════════════════════════════════════════════════
# PAGE: MYSTIC TAROT
# ════════════════════════════════════════════════════════════════
def show_tarot():
    auto_collapse_sidebar()
    st.markdown("<h1>🃏 Mystic Tarot</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Ask a question and consult the cards. Cryptographically secure randomisation.</p>",unsafe_allow_html=True)

    def reset_tarot():
        st.session_state.tarot_drawn=False; st.session_state.tarot_cards=[]
        st.session_state.tarot_states=[]; st.session_state.tarot_question_input=""

    st.markdown("### 1. Select Spread Type")
    tarot_mode=st.radio("Spread",["General Guidance","Love & Dynamics","Decision / Two Paths"],
                        horizontal=True,label_visibility="collapsed")
    placeholder_map={"General Guidance":"e.g. What energy surrounds my career this month?",
                     "Love & Dynamics":"e.g. What should I know about my connection with...",
                     "Decision / Two Paths":"e.g. Should I choose path A or path B?"}

    st.markdown("### 2. Enter Your Question")
    question=st.text_area("Question",key="tarot_question_input",
                          placeholder=placeholder_map[tarot_mode],label_visibility="collapsed")
    use_reversed=st.checkbox("Include Reversed Cards",value=False,
                             help="Allows cards to appear reversed, adding nuance and complexity.")

    if st.button("Draw 3 Cards",type="primary",use_container_width=True):
        if not question.strip(): st.error("Please ask a question before drawing."); return
        with st.spinner("Channeling the cosmos (crypto-secure shuffle)..."):
            time_module.sleep(1.5)
            rng=secrets.SystemRandom()
            st.session_state.tarot_cards=rng.sample(FULL_TAROT_DECK,3)
            st.session_state.tarot_states=(
                [rng.choice(["Upright","Reversed"]) for _ in range(3)] if use_reversed
                else ["Upright","Upright","Upright"])
            st.session_state.tarot_drawn=True

    if st.session_state.get('tarot_drawn'):
        c1,c2,c3=st.session_state.tarot_cards; s1,s2,s3=st.session_state.tarot_states
        render_tarot_overlay(c1,s1,c2,s2,c3,s3)
        st.markdown("<h3 style='margin-top:0;color:#fff;'>💡 Ready for your Reading?</h3>",unsafe_allow_html=True)
        st.markdown("""<div style='background:rgba(144,98,222,0.1);border:1px solid rgba(144,98,222,0.3);
            border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;'>
            <ol style='color:#beb9cd;font-size:0.95rem;margin-bottom:0;line-height:1.6;'>
            <li>Click <b>Copy Prompt</b> below.</li>
            <li>Click a <b>Launch AI</b> button.</li>
            <li><b>Paste</b> and send!</li></ol></div>""",unsafe_allow_html=True)
        prompt=build_tarot_prompt(question,c1,s1,c2,s2,c3,s3,mode=tarot_mode)
        render_copy_button(prompt); st.markdown("<br>",unsafe_allow_html=True)
        a1,a2,a3=st.columns(3)
        a1.link_button("💬 ChatGPT","https://chatgpt.com/",use_container_width=True)
        a2.link_button("✨ Gemini","https://gemini.google.com/",use_container_width=True)
        a3.link_button("🚀 Grok","https://grok.com/",use_container_width=True)
        if st.button("🔄 Ask Another Question",type="secondary",on_click=reset_tarot,use_container_width=True): pass
        with st.expander("📄 View Raw Prompt",expanded=False): st.code(prompt,language="text")

# ════════════════════════════════════════════════════════════════
# PAGE: HOROSCOPES (with disclosure — FIX)
# ════════════════════════════════════════════════════════════════
def show_horoscopes():
    auto_collapse_sidebar()
    st.markdown("<h1>🌟 Horoscopes</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Traditional sign-based guidance, computed locally — no AI required.</p>",unsafe_allow_html=True)

    # FIX: Honest disclosure about the nature of this feature
    st.info("ℹ️ These horoscopes are algorithmically generated from traditional sign-based guidance texts. "
            "They are not computed from your personal birth chart. For a personalised, chart-accurate reading, "
            "use **The Oracle** instead.")

    t1,t2=st.tabs(["☀️ Western (Sun Sign)","🌙 Indian / Vedic (Moon Sign)"])
    today=date.today()

    with t1:
        st.markdown("### Western Horoscope")
        st.caption("Based on your Sun Sign. Enter your birth date if you're unsure of your sign.")
        dob=st.date_input("Date of Birth",date(2000,1,1),key="h_w_dob")
        if st.button("Show Western Horoscope",type="primary",key="w_horo_btn"):
            st.session_state.show_western=True
        if st.session_state.get('show_western',False):
            sign=get_western_sign(dob.month,dob.day)
            st.success(f"Your Western Sun Sign is **{sign}**")
            pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
            with pt1: st.write(generate_horoscope_text(sign,"Daily",today.isoformat()))
            with pt2: st.write(generate_horoscope_text(sign,"Monthly",f"{today.year}-{today.month}"))
            with pt3: st.write(generate_horoscope_text(sign,"Yearly",f"{today.year}"))

    with t2:
        st.markdown("### Vedic Horoscope")
        st.caption("In Indian astrology, your daily horoscope is based on your Rashi (Moon Sign). Enter exact birth details.")
        item=render_profile_form("vedic_horo",show_d60=False)
        if st.button("Calculate Vedic Horoscope",type="primary",key="v_horo_btn"):
            if item["type"]=="empty_saved": st.error("Select a saved profile to continue.")
            else:
                prof,_=resolve_profile(item)
                st.session_state.vedic_horo_prof=prof; st.session_state.show_vedic=True
        if st.session_state.get('show_vedic') and st.session_state.vedic_horo_prof:
            prof=st.session_state.vedic_horo_prof
            moon_lon=get_moon_lon_from_profile(prof)
            moon_sidx=sign_index_from_lon(moon_lon); sign_n=sign_name(moon_sidx)
            nak,_,_=nakshatra_info(moon_lon)
            st.success(f"Your Vedic Rashi (Moon Sign) is **{sign_n}** (Birth Star: {nak})")
            pt1,pt2,pt3=st.tabs(["Daily","Monthly","Yearly"])
            with pt1: st.write(generate_horoscope_text(sign_n,"Daily_V",today.isoformat()))
            with pt2: st.write(generate_horoscope_text(sign_n,"Monthly_V",f"{today.year}-{today.month}"))
            with pt3: st.write(generate_horoscope_text(sign_n,"Yearly_V",f"{today.year}"))

# ════════════════════════════════════════════════════════════════
# PAGE: NUMEROLOGY (FIXED — Chaldean + improved prompt)
# ════════════════════════════════════════════════════════════════
def show_numerology():
    auto_collapse_sidebar()
    st.markdown("<h1>🔢 Numerology</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Generate mathematically precise numerology profiles with Master Number support.</p>",unsafe_allow_html=True)

    system_choice=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True)
    if system_choice=="Indian/Vedic (Chaldean)":
        st.caption("ℹ️ Using the **Chaldean** system — the authentic ancient Indian tradition. "
                   "Key difference: the number 9 is sacred and not assigned to letters.")

    mode=st.radio("Reading Type",["Full Comprehensive Report","Ask a Specific Question"],horizontal=True)
    question=""
    if mode=="Ask a Specific Question":
        question=st.text_area("What is your specific question?",
                              placeholder="e.g. When will my career take off? Is my current path aligned with my numbers?")

    use_astro=st.checkbox("🌌 Cross-Validate with Vedic Kundli (Recommended for maximum accuracy)",value=False)
    if use_astro:
        st.info("Cross-validation enabled. Select or create an astrological profile — Name and DOB will be used for numerology.")
        item=render_profile_form("num_prof",show_d60=True)
    else:
        st.markdown("#### Enter Your Details")
        num_name=st.text_input("Full Birth Name (as on birth certificate)")
        num_dob=st.date_input("Date of Birth",date(2000,1,1))

    if st.button("Generate Numerology Prompt",type="primary",use_container_width=True):
        if use_astro:
            if item["type"]=="empty_saved": st.error("Please select a saved profile."); return
            prof,d60=resolve_profile(item); name=prof['name']; dob_str=prof['date']
        else:
            if not num_name.strip(): st.error("Please enter your name."); return
            name=num_name.strip(); dob_str=num_dob.isoformat()

        with st.spinner("Calculating core numbers..."):
            lp,dest,soul,pers=calculate_numerology_core(name,dob_str,system=system_choice)
            dossier=None
            if use_astro: dossier=generate_astrology_dossier(prof,d60)

        st.success("Numbers computed!")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Life Path",str(lp)+(" ★" if lp in [11,22,33] else ""))
        c2.metric("Destiny",str(dest)+(" ★" if dest in [11,22,33] else ""))
        c3.metric("Soul Urge",str(soul)+(" ★" if soul in [11,22,33] else ""))
        c4.metric("Personality",str(pers)+(" ★" if pers in [11,22,33] else ""))
        if any(n in [11,22,33] for n in [lp,dest,soul,pers]):
            st.caption("★ = Master Number")

        prompt=build_numerology_prompt(name,dob_str,lp,dest,soul,pers,dossier,question,system=system_choice)
        render_post_generation(prompt)

# ════════════════════════════════════════════════════════════════
# PAGE: SAVED PROFILES (VAULT)
# ════════════════════════════════════════════════════════════════
def show_vault():
    auto_collapse_sidebar()
    st.markdown("<h1>📖 Saved Profiles</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,0.6);'>Manage your saved astrological profiles.</p>",unsafe_allow_html=True)

    if not st.session_state.db:
        st.info("Your address book is currently empty. Add a profile below.")
    else:
        cols=st.columns(3)
        for i,p in enumerate(st.session_state.db):
            with cols[i%3]:
                with st.container(border=True):
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"{format_date_ui(p['date'])} • {p['time']}")
                    st.caption(f"📍 {p['place'].split(',')[0]}")
                    d1,d2=st.columns(2)
                    if d1.button("Edit",key=f"v_edit_{i}",use_container_width=True):
                        st.session_state.editing_idx=i; st.rerun()
                    if d2.button("Delete",key=f"v_del_{i}",use_container_width=True):
                        st.session_state.db.pop(i); sync_db(); st.rerun()

    if st.session_state.editing_idx is not None:
        st.markdown("---")
        ei=st.session_state.editing_idx; pd_=st.session_state.db[ei]
        st.markdown(f"### Editing {pd_['name']}")
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
            is_manual=pd_['place']=="Manual Coordinates"
            u_place=st.text_input("Birth Place","" if is_manual else pd_['place'],key="ve_p")
            manual=st.checkbox("Manual coordinates",value=is_manual,key="ve_man")
            det_lat=det_lon=det_tz=det_place=None
            if u_place.strip() and not manual:
                geo=geocode_place(u_place.strip())
                if geo: det_lat,det_lon,det_place=geo; det_tz=timezone_for_latlon(det_lat,det_lon); st.success(f"📍 {geo[2]}")
                else: st.warning("Location not found.")
            if manual:
                m1,m2,m3=st.columns(3)
                with m1: m_lat=st.number_input("Lat",value=float(pd_['lat']),format="%.4f",key="ve_lat")
                with m2: m_lon=st.number_input("Lon",value=float(pd_['lon']),format="%.4f",key="ve_lon")
                with m3: m_tz=st.text_input("TZ",pd_['tz'],key="ve_tz")
        b1,b2=st.columns(2)
        if b1.button("Save Changes",type="primary"):
            h24=(u_hr+12 if u_am=="PM" and u_hr!=12 else 0 if u_am=="AM" and u_hr==12 else u_hr)
            if manual:
                if not m_tz.strip(): st.error("Enter a timezone."); st.stop()
                fl2,fln2,ftz2,fp2=m_lat,m_lon,m_tz,"Manual Coordinates"
            else:
                if det_lat is None: st.error("Enter a valid birth place."); st.stop()
                fl2,fln2,ftz2,fp2=det_lat,det_lon,det_tz,det_place
            st.session_state.db[ei]={"name":u_name,"date":u_date.isoformat(),
                "time":time(h24,u_mi).strftime("%H:%M"),"place":fp2,"lat":fl2,"lon":fln2,"tz":ftz2}
            st.session_state.editing_idx=None; sync_db(); st.rerun()
        if b2.button("Cancel"): st.session_state.editing_idx=None; st.rerun()

    st.markdown("---")
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
                m1,m2,m3=st.columns(3)
                with m1: v_lat=st.number_input("Lat",value=0.0,format="%.4f",key="v_new_lat")
                with m2: v_lon=st.number_input("Lon",value=0.0,format="%.4f",key="v_new_lon")
                with m3: v_tz=st.text_input("TZ","Asia/Kolkata",key="v_new_tz")
        if st.button("Add Profile",type="primary"):
            if not v_n.strip(): st.error("Name required."); st.stop()
            h24=(v_h+12 if v_a=="PM" and v_h!=12 else 0 if v_a=="AM" and v_h==12 else v_h)
            if v_man:
                if not v_tz.strip(): st.error("Timezone required."); st.stop()
                lat,lon,tz,p_name=v_lat,v_lon,v_tz,"Manual Coordinates"
            else:
                if not v_p.strip(): st.error("Place required."); st.stop()
                geo=geocode_place(v_p.strip())
                if not geo: st.error("Location not found."); st.stop()
                lat,lon,p_name=geo; tz=timezone_for_latlon(lat,lon)
            new_prof={"name":v_n.strip(),"date":v_d.isoformat(),"time":time(h24,v_m).strftime("%H:%M"),
                      "place":p_name,"lat":lat,"lon":lon,"tz":tz}
            if not is_duplicate_in_db(new_prof):
                st.session_state.db.append(new_prof); sync_db()
                st.success("Profile added!"); time_module.sleep(1); st.rerun()
            else: st.warning("Profile already exists.")

    st.markdown("---")
    st.markdown("### Data Backup")
    b1,b2=st.columns(2)
    with b1:
        st.download_button("⬇️ Export Profiles",data=json.dumps(st.session_state.db,indent=2),
                           file_name="kundli_backup.json",use_container_width=True)
    with b2:
        uf=st.file_uploader("Upload Backup JSON",type="json",label_visibility="collapsed")
        if uf is not None:
            try:
                uploaded=json.loads(uf.getvalue().decode('utf-8'))
                if isinstance(uploaded,list):
                    st.session_state.db=uploaded; sync_db()
                    st.success("Backup restored!"); time_module.sleep(1); st.rerun()
                else: st.error("Invalid format.")
            except Exception as e: st.error(f"Invalid file: {e}")

# ════════════════════════════════════════════════════════════════
# MAIN LAUNCHER
# ════════════════════════════════════════════════════════════════
inject_nebula_css()
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
