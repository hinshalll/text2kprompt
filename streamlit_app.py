import json, base64, secrets, textwrap, time as time_module
import concurrent.futures # 🚀 Allows parallel AI agents
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import streamlit as st
import os
import requests
import google.generativeai as genai
import streamlit.components.v1 as components
import swisseph as swe  # type: ignore[import-unresolved]
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_local_storage import LocalStorage

# ═══════════════════════════════════════════════════════════
# APP CONFIG
# ═══════════════════════════════════════════════════════════

APP_NAME = "ASTRO SUITE beta"
st.set_page_config(page_title=APP_NAME, page_icon="🪐", layout="wide",
                   initial_sidebar_state="collapsed")
try: swe.set_ephe_path("ephe")
except: pass
swe.set_sid_mode(swe.SIDM_LAHIRI)

# 🛠️ FIX 1: CONFIGURE GEMINI GLOBALLY HERE
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing GEMINI_API_KEY in .streamlit/secrets.toml")
    st.stop()
genai.configure(api_key=api_key)

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
    "Karmic Intensity — Who faces the most karmic obstacles?",
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
    
TAROT_BASE="https://raw.githubusercontent.com/hinshalll/text2kprompt/main/tarot/"
NAV_PAGES=["Dashboard", "Consultation Room", "The Oracle", "Mystic Tarot", "Horoscopes", "Numerology", "Saved Profiles"]

# ═══════════════════════════════════════════════════════════
# SESSION STATE & QUERY PARAMS (navigation)
# ═══════════════════════════════════════════════════════════
localS = LocalStorage()

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
    st.session_state.default_profile_idx = idx
    st.session_state.needs_sync = True 
    st.toast("⭐ Default profile locked!")

def clear_default_profile():
    st.session_state.default_profile_idx = None
    st.session_state.needs_sync = True
    st.toast("Default profile cleared.")
def get_local_today(tz_string="Asia/Kolkata"):
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
def safe_json(text_response, fallback_dict):
    try:
        clean_text = text_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return fallback_dict

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
    
def get_western_transits_today():
    """Calculates live Tropical (Western) transits safely without altering Vedic settings."""
    dt_now = datetime.now(ZoneInfo("UTC"))
    jd = swe.julday(dt_now.year, dt_now.month, dt_now.day, dt_now.hour + dt_now.minute / 60.0)
    
    western_pos = {}
    for pname, pid in PLANETS.items():
        # Using swe.FLG_SWIEPH without the Sidereal flag calculates Tropical
        res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        lon = float(res[0]) % 360
        sidx = int(lon // 30) % 12
        western_pos[pname] = SIGNS[sidx]
        
    return western_pos    

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
    f=swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED; res,_=swe.calc_ut(jd,pid,f)
    return float(res[0])%360,float(res[1]),float(res[3])
def get_rahu_longitude(jd):
    res,_=swe.calc_ut(jd,swe.TRUE_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL); return float(res[0])%360
def get_placidus_cusps(jd,lat,lon):
    cusps,_=swe.houses_ex(jd,lat,lon,b"P",swe.FLG_SWIEPH|swe.FLG_SIDEREAL); return cusps

@st.cache_data(ttl=3600,show_spinner=False)
def get_live_cosmic_weather():
    dt_now=datetime.now(ZoneInfo("UTC"))
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
    r_lon,_=swe.calc_ut(jd,swe.TRUE_NODE,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)
    all_pos["Rahu"]=sign_name(sign_index_from_lon(float(r_lon[0])%360))
    all_pos["Ketu"]=sign_name(sign_index_from_lon((float(r_lon[0])+180)%360))
    return {"moon_sign":sign_name(moon_sidx),"sun_sign":sign_name(sun_sidx),"nakshatra":nak,
            "tithi":panch["tithi"],"yoga":panch["yoga"],"retrogrades":retrogrades,
            "nature":nature_type,"advice":advice,"all_pos":all_pos}


# ═══════════════════════════════════════════════════════════
# The AI Engine Helper Function & Auto-Switcher
# ═══════════════════════════════════════════════════════════
# ── MODEL ROUTING ────────────────────────────────────────────
# IMPORTANT: Context window sizes (how many tokens the model can READ at once):
#   gemini-3.1-flash-lite-preview  → 1,000,000 tokens  ← BEST for big books
#   gemini-2.5-flash               → 1,000,000 tokens  ← BEST for big books  
#   gemma-4-31b-it                 →   262,144 tokens  ← Books often EXCEED this → 400 error
#   gemma-4-26b-a4b-it             →   262,144 tokens  ← Same problem
#
# STRATEGY: Always try Flash Lite first (handles big books fine).
#   Only fall to Gemma 4 as LAST RESORT — it has unlimited TPM but tiny context.
#   Gemma 4 is useful ONLY for very short prompts (dashboard JSON, no books).

# Primary: Large context window (1M tokens) — handles books without overflowing
LIGHT_MODELS = [
    "gemini-3.1-flash-lite-preview",  # 500 RPD, 250K TPM, 1M context — PRIMARY for everything
    "gemini-2.5-flash",               #  20 RPD, 250K TPM, 1M context — second fallback
]
# Last resort: Small context window (262K tokens) — unlimited TPM but books may overflow it
HEAVY_MODELS = [
    "gemma-4-31b-it",       # 1500 RPD, Unlimited TPM, 262K context — last resort
    "gemma-4-26b-a4b-it",   # 1500 RPD, Unlimited TPM, 262K context — final fallback
]
# Default order: always Light first, Gemma 4 only if both Gemini models are rate-limited
FREE_MODELS = LIGHT_MODELS + HEAVY_MODELS

@st.cache_data(show_spinner=False, ttl=timedelta(hours=24))
def get_knowledge_files(file_names):
    """Loads MD reference files locally first, then falls back to GitHub."""
    loaded_texts = []
    
    for name in file_names:
        try:
            # Strictly clean the URL to prevent 'No connection adapter' errors
            clean_name = name.strip(" '\n\r")
            local_candidates = [
                os.path.join(os.path.expanduser("~"), "Desktop", "aiguide", clean_name),
                os.path.join(os.path.expanduser("~"), "Desktop", "aiguide", "Being Used", clean_name),
            ]
            for local_path in local_candidates:
                if os.path.exists(local_path):
                    with open(local_path, "r", encoding="utf-8", errors="ignore") as fh:
                        text = fh.read()
                    loaded_texts.append(f"\n--- START OF REFERENCE BOOK: {clean_name} ---\n{text}\n--- END OF REFERENCE BOOK: {clean_name} ---\n")
                    break
            if len(loaded_texts) and loaded_texts[-1].startswith(f"\n--- START OF REFERENCE BOOK: {clean_name} ---"):
                continue
            github_url = f"https://raw.githubusercontent.com/hinshalll/text2kprompt/main/aiguide/{clean_name}"
            
            # Fetch the raw markdown text directly from GitHub
            response = requests.get(github_url, timeout=15)
            response.raise_for_status() 
            
            # Wrap the text so the AI knows exactly which book it is reading
            file_content = f"\n--- START OF REFERENCE BOOK: {clean_name} ---\n{response.text}\n--- END OF REFERENCE BOOK: {clean_name} ---\n"
            loaded_texts.append(file_content)
            
        except Exception as e:
            # Raise the exception so Streamlit aborts the cache and tries cleanly next time
            raise Exception(f"Network error loading {name}. Please check your connection and try again. Details: {e}")
            
    return loaded_texts

@st.cache_data(show_spinner=False, ttl=timedelta(hours=24))
def get_comparison_reference_digest():
    """
    Token-light reference pack for Compare Profiles.
    Uses a compact digest from BPHS1 + KP3 instead of attaching multi-MB books.
    """
    return ["""
--- START OF REFERENCE DIGEST: BPHS1.md + KP3.md for Compare Profiles ---
Use this digest as the book authority for comparison output.

PARASHARI / BPHS1 PRINCIPLES
- Judge a topic from the relevant house, its lord, occupants, aspects/associations, natural karaka, dignity, yogas, and appropriate varga.
- House meanings used here: H1 body/vitality/self; H2 wealth/family/speech; H3 courage/effort; H4 peace of mind/home/happiness/property; H5 intelligence/children/fame/purva punya; H6 disease/debts/enemies/competition; H7 spouse/marriage/partnership; H8 longevity/sudden reversals/hidden matters; H9 fortune/dharma/guru; H10 profession/status/honour; H11 gains/fulfilment; H12 losses/expenditure/moksha.
- Divisional chart use: Hora for wealth; Navamsa for spouse and durable inner strength; Dashamsa for power, position and career; Dvadashamsa can support constitution/family inheritance; Vimsamsa is for worship/spiritual progress when available; Trimsamsa is for evils and hidden adversity.
- Dignity matters: exaltation/own sign/vargottama strengthen; debility/enemy sign/combustion/planetary war/bad avastha weaken or spoil results unless cancelled by Neecha Bhanga or other protection.
- Yogas matter only when the causing planets are strong enough. Kendra-trikona links, yogakarakas and Raja/Dhana/Lakshmi-type yogas support high promise; Kemadruma and severe malefic hemming raise burden.
- Longevity and health use Lagna, Lagna lord, H3/H8, maraka pressure from H2/H7, Saturn, Sun, Moon, and afflictions. Do not turn this into medical diagnosis.
- Spirituality uses H9/H12/H8/H5, Ketu, Jupiter, Saturn, Atmakaraka/Karakamsa ideas, and moksha-oriented varga support.

KP3 PRINCIPLES
- KP refines whether an event manifests. The star lord shows the main house results; the sub-lord selects/denies the specific outcome.
- A cusp sub-lord that signifies the event houses promises the event; if it signifies opposing houses, it delays, obstructs or denies.
- Marriage/engagement: houses 2, 7 and 11 are primary; 3 and 9 can support agreement/consent.
- Finance: H2 is bank position/self-acquisition; H11 is profit/net gain; H12 is loss/expense. For service-linked money include H10.
- Profession/status: H10 is position, fame, reputation and profession; H11 is fulfilment/realisation; H6 supports service, competition and victory over opponents.
- Partnership/business: H7 with H2/H10/H11 supports success; H8/H12 links weaken.
- Disease judgment uses the 6th cusp sub-lord and its star/sub links; chronicity and danger require H8/H12 context.

COMPARISON OUTPUT RULE
- Python scores are final. Explain rankings with chart evidence and this digest. Do not recalculate, invent positions, or use current transits/Sade Sati/current dasha to alter lifetime baseline scores.
--- END OF REFERENCE DIGEST ---
"""]

def get_ai_model_by_name(model_name, custom_system_rules=None):
    """Directly calls a specific model with dynamic system rules, preserving original guardrails."""
    default_rules = """
    <ROLE>
    You are an elite, highly precise Vedic Astrologer, Numerologist, and Tarot Reader.
    </ROLE>
    
    <KNOWLEDGE_BASE_DIRECTIVES>
    1. Your interpretive rules, definitions, and logic MUST come entirely from the attached Markdown files.
    2. If external knowledge contradicts the attached files, the attached files win.
    3. The attached files contain OCR-extracted text. Ignore broken ASCII tables, weird grids, and formatting artifacts. Do not attempt to parse tables.
    4. Auto-correct typos in the prose using your context.
    </KNOWLEDGE_BASE_DIRECTIVES>
    
    <STRICT_MATH_LOCK>
    You are strictly forbidden from altering, correcting, or inferring any numbers, degrees, planetary positions, or mathematical formulas. Treat all numbers in the text and user prompts as absolute, unchangeable facts.
    </STRICT_MATH_LOCK>
    """
    
    system_rules = custom_system_rules or default_rules
    safe_config = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    # Check if the rules mention "warm" or "conversational" to dynamically adjust creativity
    is_chat = custom_system_rules and "conversational" in custom_system_rules.lower()
    gen_config = {"temperature": 0.5 if is_chat else 0.1} 
    
    return genai.GenerativeModel(
        model_name=model_name, 
        system_instruction=system_rules, 
        safety_settings=safe_config,
        generation_config=gen_config
    )

def agent_worker(prompt, file_objs, model_id, custom_system_rules=None, retries=3):
    """
    Calls a model with exponential backoff. Falls back gracefully on both:
    - 429 / quota / RESOURCE_EXHAUSTED  (rate limit — wait and retry)
    - 400 / InvalidArgument / token count (context overflow — skip this model)
    """
    if not isinstance(file_objs, list): file_objs = [file_objs]
    for attempt in range(retries):
        try:
            model = get_ai_model_by_name(model_id, custom_system_rules)
            return model.generate_content(file_objs + [prompt]).text
        except Exception as e:
            err_str = str(e)
            is_rate_limit = any(x in err_str for x in [
                "429", "quota", "RESOURCE_EXHAUSTED", "rate limit"
            ])
            is_token_overflow = any(x in err_str for x in [
                "400", "InvalidArgument", "token count exceeds", "maximum number of tokens"
            ])
            if is_token_overflow:
                # Context window exceeded — retrying won't help, exit immediately
                return f"Agent Note: Content too large for {model_id} ({err_str[:80]}). Inferring from raw dossier."
            elif is_rate_limit and attempt < retries - 1:
                wait_sec = (2 ** attempt) * 4  # 4s, 8s, 16s
                time_module.sleep(wait_sec)
                continue
            else:
                # After all retries or unknown error
                return f"Agent Note: Model {model_id} unavailable ({err_str[:80]}). Inferring from raw dossier."

def generate_content_with_fallback(prompt, knowledge_files=None, preferred_model=None):
    """
    Universal model router with automatic fallback and retry.
    
    Always tries Flash Lite FIRST (1M context, handles big books).
    Falls back to Gemma 4 LAST (unlimited TPM, but only 262K context — may still overflow).
    
    Triggers fallback on BOTH:
      - 429 / rate limit  → wait and retry, then move to next model
      - 400 / token overflow → skip immediately to next model (retrying won't help)
    """
    content_to_send = knowledge_files + [prompt] if knowledge_files else [prompt]

    # Always start with the largest-context models (Flash Lite = 1M context)
    if preferred_model and preferred_model in FREE_MODELS:
        others = [m for m in FREE_MODELS if m != preferred_model]
        models_to_try = [preferred_model] + others
    else:
        models_to_try = FREE_MODELS  # LIGHT first (1M context), HEAVY last (262K context)

    last_error = None
    for m_name in models_to_try:
        for attempt in range(3):
            try:
                return get_ai_model_by_name(m_name).generate_content(content_to_send).text
            except Exception as e:
                err_str = str(e)
                is_rate_limit = any(x in err_str for x in [
                    "429", "quota", "RESOURCE_EXHAUSTED", "rate limit"
                ])
                is_token_overflow = any(x in err_str for x in [
                    "400", "InvalidArgument", "token count exceeds", "maximum number of tokens"
                ])
                if is_token_overflow:
                    # No point retrying — content is too big for this model, try next one
                    last_error = e
                    break
                elif is_rate_limit:
                    if attempt < 2:
                        time_module.sleep((2 ** attempt) * 3)  # 3s, 6s
                        continue
                    else:
                        last_error = e
                        break  # Rate limit exhausted for this model, try next
                else:
                    # Unknown error — don't retry, don't crash the app
                    last_error = e
                    break

    raise Exception(
        f"All models unavailable. Last error: {last_error}. "
        "Please wait a few minutes and try again."
    )

@st.cache_data(ttl=timedelta(hours=24), show_spinner=False)
def generate_western_forecast(sun_sign, today_str):
    # Strictly Daily - no timeframe argument needed
    transits = get_western_transits_today()
    
    prompt = f"""<instructions>
    You are an elite Western Astrologer. Generate a highly accurate daily horoscope for a user whose Western Sun Sign is {sun_sign}.
    
    Use the live Tropical transit data provided below to write extremely concise, 1 to 2 sentence summaries for each category:
    **General:** (One sentence overall theme)
    **Love & Relationships:** (One sentence romantic forecast)
    **Career & Finance:** (One sentence professional forecast)
    
    CRITICAL RULES:
    - Keep it very brief and scannable. MAXIMUM 2 sentences per category.
    - Ground the interpretation strictly in the provided transits.
    - Briefly mention the specific planet transiting to prove authenticity.
    - Do not use markdown headers, just output the bold text.
    </instructions>
    
    <live_tropical_transits>
    {transits}
    </live_tropical_transits>
    """
    
    try:
        return generate_content_with_fallback(prompt)
    except Exception:
        return "**General:** The cosmic connection is catching its breath.\n\n**Love & Relationships:** Try again in a few minutes.\n\n**Career & Finance:** API limits reached, take a coffee break!"

@st.cache_data(ttl=timedelta(hours=24), show_spinner=False)
def generate_vedic_forecast(prof_json, timeframe, today_str):
    prof = json.loads(prof_json)
    
    # 1. PYTHON DOES THE MATH
    days_ahead = {"Daily": 0, "Monthly": 15, "Yearly": 180}[timeframe]
    dt_now = datetime.now(ZoneInfo("UTC"))
    target_date = dt_now + timedelta(days=days_ahead)
    jd_target = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
    
    moon_lon = get_moon_lon_from_profile(prof)
    natal_moon_sidx = sign_index_from_lon(moon_lon)
    rashi = sign_name(natal_moon_sidx)
    
    transit_lines = [f"LIVE TRANSITS FOR {timeframe.upper()} FORECAST ({target_date.strftime('%d %b %Y')}):"]
    for pn in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        t_lon, _ = get_planet_longitude_and_speed(jd_target, PLANETS[pn])
        t_sidx = sign_index_from_lon(t_lon)
        diff_houses = ((t_sidx - natal_moon_sidx) % 12) + 1
        transit_lines.append(f"  {pn} is transiting House {diff_houses} from Natal Moon (in {sign_name(t_sidx)})")
    
    r_lon = get_rahu_longitude(jd_target)
    transit_lines.append(f"  Rahu is transiting House {((sign_index_from_lon(r_lon) - natal_moon_sidx) % 12) + 1} from Natal Moon")
    transit_data = "\n".join(transit_lines)
    
    timeframe_rules = {
        "Daily": "Focus heavily on the Moon's transit and fast-moving planets for immediate 24-hour events.",
        "Monthly": "Focus on the Sun, Mars, Venus, and Mercury transits to predict themes for the next 30 days.",
        "Yearly": "Ignore the Moon. Focus EXCLUSIVELY on slow-moving transits of Jupiter, Saturn, and Rahu."
    }
    
    # 2. PROMPT FORCES AI TO READ THE BOOKS
    prompt = f"""{GUARDRAILS}
<mission>
You are an elite Vedic Astrologer. Generate a highly accurate {timeframe} horoscope for a user whose Moon Sign (Rashi) is {rashi}.
Read the mathematically exact Gochara (transit) data provided below. {timeframe_rules[timeframe]}
</mission>

<KNOWLEDGE_ROUTING>
Open `bphs2.md` and read the exact rules for these specific planetary transits from the Natal Moon. 
Do not invent transit meanings. Rely strictly on the text. Use `iva.md` to format your tone.
</KNOWLEDGE_ROUTING>

<transit_math>
{transit_data}
</transit_math>

<FORMAT>
Write extremely concise, 1 to 2 sentence summaries for each category. Do not use markdown headers, just output the bold text:
**General:** (One sentence overall theme)
**Love & Relationships:** (One sentence romantic forecast)
**Career & Finance:** (One sentence professional forecast)
</FORMAT>"""
    
    try:
        # bphs2.md = Dasha effects, Antardasha for all planets — core timing book.
        # This is what a Vedic horoscope primarily needs (current Dasha period interpretation).
        # Removing iva.md saves ~254K tokens — prevents TPM overflow on Flash Lite.
        books = get_knowledge_files(["bphs2.md"])
        return generate_content_with_fallback(prompt, knowledge_files=books)
    except Exception:
        return "**General:** The cosmic connection is resting.\n\n**Love & Relationships:** Try again later.\n\n**Career & Finance:** API limit reached."

# ═══════════════════════════════════════════════════════════
# DAILY CACHE HELPERS
# ═══════════════════════════════════════════════════════════
def profile_cache_key(prof):
    return f"{prof['name']}|{prof['date']}|{prof['time']}|{prof.get('tz', 'Asia/Kolkata')}"

@st.cache_data(ttl=timedelta(hours=24), show_spinner=False)
def fetch_cached_dashboard_data(prof_json, today_str):
    prof = json.loads(prof_json)
    dos = generate_astrology_dossier(prof, False, compact=True)
    transits = get_gochara_overlay(prof)
    prompt = build_dashboard_data_prompt(dos, transits, prof['name'].split()[0])
    # Dashboard has NO books attached — use light model (preserves Gemma 4 quota for heavy work)
    res = generate_content_with_fallback(prompt, knowledge_files=None, preferred_model="gemini-3.1-flash-lite-preview")
    return safe_json(res, {
        "GREETING": f"Welcome back, {prof['name'].split()[0]}. The cosmic connection is catching its breath, but your tools are ready below.",
        "ENERGY": "Mixed",
        "FOCUS": "Routine",
        "CAUTION": "Impulsivity",
        "WINDOW": "Anytime",
        "SUMMARY": "Balanced day. Stick to your routines."
    })

@st.cache_data(ttl=timedelta(hours=24), show_spinner=False)
def fetch_cached_daily_tarot(prof_json, today_str, daily_card, daily_state):
    _ = json.loads(prof_json)
    base_prompt = build_daily_tarot_prompt(daily_card, daily_state)
    json_prompt = base_prompt + """
RESPOND ONLY IN VALID JSON FORMAT. NO MARKDOWN:
    {
        "MEANING": "What the card means today.",
        "ACTION": "The best practical step to take.",
        "MANTRA": "A short, powerful affirmation."
    }"""
    dash_tarot_file = get_knowledge_files(["tguide.md"])
    # Let the router pick — Flash Lite (1M context) handles tguide.md fine
    res = generate_content_with_fallback(json_prompt, knowledge_files=dash_tarot_file)
    return safe_json(res, {
        "MEANING": "Trust the process unfolding today.",
        "ACTION": "Observe before making any sudden moves.",
        "MANTRA": "I am exactly where I need to be."
    })

# ═══════════════════════════════════════════════════════════
# THE UNIVERSAL AI CHAT ENGINE
# ═══════════════════════════════════════════════════════════

def render_share_buttons(text, title="Astro Suite"):
    import base64
    import streamlit.components.v1 as components
    
    st.markdown("<br>", unsafe_allow_html=True)
    b64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    html = f"""
    <div style="font-family: 'Source Sans Pro', sans-serif; display: flex; gap: 10px; padding: 5px;">
        <button id="pdfBtn" style="flex: 1; padding: 0.5rem 1rem; background-color: transparent; color: #ffffff; border: 1px solid rgba(250, 250, 250, 0.2); border-radius: 0.5rem; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s;" onmouseover="this.style.borderColor='#ff4b4b'; this.style.color='#ff4b4b';" onmouseout="this.style.borderColor='rgba(250, 250, 250, 0.2)'; this.style.color='#ffffff';">
            📄 Save Branded PDF
        </button>
        <button id="shareBtn" style="flex: 1; padding: 0.5rem 1rem; background-color: transparent; color: #ffffff; border: 1px solid rgba(250, 250, 250, 0.2); border-radius: 0.5rem; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s;" onmouseover="this.style.borderColor='#ff4b4b'; this.style.color='#ff4b4b';" onmouseout="this.style.borderColor='rgba(250, 250, 250, 0.2)'; this.style.color='#ffffff';">
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            Share Reading
        </button>
    </div>
    <div id="msg" style="text-align:center; font-size:0.8rem; margin-top:5px; color:#999; opacity:0; transition:opacity 0.3s;">Action completed!</div>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script>
        const raw_text = decodeURIComponent(escape(window.atob('{b64_text}')));
        const msg = document.getElementById('msg');
        
        function showMsg(text) {{
            msg.innerText = text;
            msg.style.opacity = 1;
            setTimeout(() => msg.style.opacity = 0, 3000);
        }}

        // SHARE LOGIC
        document.getElementById('shareBtn').addEventListener('click', async () => {{
            if (navigator.share) {{
                try {{ await navigator.share({{ title: '{title} Reading', text: raw_text }}); }} 
                catch(err) {{ fallback(raw_text); }}
            }} else {{ fallback(raw_text); }}
        }});
        
        function fallback(txt) {{
            navigator.clipboard.writeText(txt).then(() => showMsg("Copied to clipboard!"))
            .catch(err => {{
                const el = document.createElement('textarea');
                el.value = txt; document.body.appendChild(el); el.select();
                document.execCommand('copy'); document.body.removeChild(el);
                showMsg("Copied to clipboard!");
            }});
        }}

        // PDF LOGIC
        document.getElementById('pdfBtn').addEventListener('click', () => {{
            showMsg("Generating PDF...");
            const parsedHTML = marked.parse(raw_text);
            const wrapper = document.createElement('div');
            wrapper.style.padding = '40px'; wrapper.style.fontFamily = 'Helvetica, Arial, sans-serif';
            wrapper.style.color = '#222'; wrapper.style.lineHeight = '1.6';
            wrapper.innerHTML = `
                <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #EEE; padding-bottom: 20px;">
                    <h1 style="color: #4A148C; font-size: 28px; letter-spacing: 2px; margin: 0;">{title}</h1>
                    <p style="color: #777; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; margin-top: 5px;">Personalized Cosmic Reading</p>
                </div>
                <div style="font-size: 14px;">${{parsedHTML}}</div>
                <div style="margin-top: 40px; text-align: center; font-size: 10px; color: #999; border-top: 1px solid #EEE; padding-top: 15px;">
                    Generated securely by {title}
                </div>
            `;
            const opt = {{
                margin: [10, 0, 10, 0],
                filename: '{title.replace(" ", "_")}_Reading.pdf',
                image: {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{ scale: 2, useCORS: true }},
                jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};
            html2pdf().set(opt).from(wrapper).save().then(() => showMsg("PDF Downloaded!"));
        }});
    </script>
    """
    components.html(html, height=100)

def stream_ai_with_followup(prompt, memory_key, spinner_text="Interpreting...", knowledge_files=None, preferred_model=None):
    """
    Universal streaming AI component with full fallback chain.
    
    Model order: Flash Lite → Gemini 2.5 Flash → Gemma 4 31B → Gemma 4 26B
    Flash Lite has 1M context so it handles books fine.
    Gemma 4 is last resort (only 262K context — books often overflow it).
    Falls back on BOTH 429 (rate limit) AND 400 (token overflow).
    """
    st.markdown("---")
    st.markdown("### ✨ AI Reading")

    content_to_send = knowledge_files + [prompt] if knowledge_files else [prompt]
    newly_generated = False

    # Always try Flash Lite first — it has 1M context and handles all book sizes
    if preferred_model and preferred_model in FREE_MODELS:
        models_for_initial = [preferred_model] + [m for m in FREE_MODELS if m != preferred_model]
    else:
        models_for_initial = FREE_MODELS  # Light (1M ctx) first, Heavy (262K ctx) last

    # ── STEP 1: GENERATE THE MAIN READING ──
    if memory_key not in st.session_state or len(st.session_state[memory_key]) == 0:
        st.session_state[memory_key] = []
        newly_generated = True

        with st.chat_message("assistant"):
            res_ph = st.empty()
            with st.spinner(spinner_text):
                success = False
                for m_id in models_for_initial:
                    if success: break
                    for attempt in range(3):
                        try:
                            model = get_ai_model_by_name(m_id)
                            chat = model.start_chat(history=[])
                            response = chat.send_message(content_to_send, stream=True)
                            f_res = ""
                            for chunk in response:
                                f_res += chunk.text
                                res_ph.markdown(f_res + "▌")
                            res_ph.markdown(f_res)
                            # Save only text to history — not the heavy book files
                            st.session_state[memory_key].append({"role": "user", "parts": [prompt]})
                            st.session_state[memory_key].append({"role": "model", "parts": [f_res]})
                            success = True
                            break
                        except Exception as e:
                            err_str = str(e)
                            is_rate = any(x in err_str for x in [
                                "429", "quota", "RESOURCE_EXHAUSTED", "rate limit"
                            ])
                            is_overflow = any(x in err_str for x in [
                                "400", "InvalidArgument", "token count exceeds", "maximum number of tokens"
                            ])
                            if is_overflow:
                                break  # This model can't handle the size — try next immediately
                            elif is_rate and attempt < 2:
                                time_module.sleep((2 ** attempt) * 3)
                                continue
                            else:
                                break  # Move to next model

                if not success:
                    res_ph.warning(
                        "⏳ All AI models are briefly at capacity or the content is too large. "
                        "Please wait a moment and try again."
                    )
                    return

    # ── STEP 2: RENDER EXISTING CHAT HISTORY ──
    if len(st.session_state[memory_key]) > 0 and not newly_generated:
        for i, msg in enumerate(st.session_state[memory_key]):
            if i == 0: continue
            role = "assistant" if msg["role"] == "model" else "user"
            with st.chat_message(role):
                st.markdown(msg["parts"][-1])

    # ── STEP 3: FOLLOW-UP CHAT (text only — no books — Flash Lite is fine) ──
    if follow_up := st.chat_input("Ask a follow-up question...", key=f"chatin_{memory_key}"):
        with st.chat_message("user"):
            st.markdown(follow_up)

        with st.chat_message("assistant"):
            res_ph = st.empty()
            with st.spinner("Thinking..."):
                success = False
                for m_id in FREE_MODELS:  # Light first for follow-ups (text only, no books)
                    if success: break
                    for attempt in range(3):
                        try:
                            model = get_ai_model_by_name(m_id)
                            chat = model.start_chat(history=st.session_state[memory_key])
                            res = chat.send_message(follow_up, stream=True)
                            f_res = ""
                            for chunk in res:
                                f_res += chunk.text
                                res_ph.markdown(f_res + "▌")
                            res_ph.markdown(f_res)
                            st.session_state[memory_key].append({"role": "user", "parts": [follow_up]})
                            st.session_state[memory_key].append({"role": "model", "parts": [f_res]})
                            success = True
                            st.rerun()
                            break
                        except Exception as e:
                            err_str = str(e)
                            is_rate = any(x in err_str for x in [
                                "429", "quota", "RESOURCE_EXHAUSTED", "rate limit"
                            ])
                            is_overflow = any(x in err_str for x in [
                                "400", "InvalidArgument", "token count exceeds", "maximum number of tokens"
                            ])
                            if is_overflow or (not is_rate):
                                break
                            elif is_rate and attempt < 2:
                                time_module.sleep((2 ** attempt) * 3)
                                continue
                            else:
                                break
                if not success:
                    res_ph.warning("⏳ Models are briefly at capacity. Please try your follow-up again in a moment.")

    # ── STEP 4: SHARE / SAVE BUTTONS ──
    if len(st.session_state[memory_key]) > 0:
        # Combine all AI responses for the document
        full_text = "\\n\\n---\\n\\n".join([msg["parts"][-1] for msg in st.session_state[memory_key] if msg["role"] == "model"])
        render_share_buttons(full_text, title=APP_NAME)

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
    # Parashari special aspects: Mars=4,7,8 | Jupiter=5,7,9 | Saturn=3,7,10
    # Rahu/Ketu: 7th aspect ONLY in Parashari (5th/9th is KP convention, not mixed here)
    spec={"Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],"Rahu":[7],"Ketu":[7]}
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
            if diff<=0.5:
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
        has_tri=any(h in trikona for h in houses)
        has_ken=any(h in kendra for h in houses)  # H1 IS a Kendra — Lagna lord ruling H1+H5 = Yogakaraka
        has_trika=any(h in trika for h in houses)
        if has_tri and has_ken: yks.append(planet)
        elif has_tri: bens.append(planet)
        elif has_trika and not has_tri: mals.append(planet)
        else: neu.append(planet)
    return bens,mals,yks,neu

def get_planet_house_significations(pname, ls, planet_data, r_lon, k_lon):
    """KP significator calculation: a planet signifies houses it occupies, owns, and its star lord occupies/owns."""
    lon = get_planet_lon_helper(pname, planet_data, r_lon, k_lon)
    if lon is None: return set()
    sigs = set()
    psidx = sign_index_from_lon(lon)
    sigs.add(whole_sign_house(ls, psidx))                          # House it occupies
    for sidx, lord in SIGN_LORDS_MAP.items():                      # Houses it owns
        if lord == pname: sigs.add(whole_sign_house(ls, sidx))
    _, sl, _ = nakshatra_info(lon)                                  # Star lord's houses
    if sl != pname:
        sl_lon = get_planet_lon_helper(sl, planet_data, r_lon, k_lon)
        if sl_lon:
            sigs.add(whole_sign_house(ls, sign_index_from_lon(sl_lon)))
            for sidx, lord in SIGN_LORDS_MAP.items():
                if lord == sl: sigs.add(whole_sign_house(ls, sidx))
    return sigs

def get_house_strength_summary(ls,planet_data,r_lon,k_lon,placidus_cusps):
    key_houses={
        1:("Self & Vitality",{1,11}),
        2:("Wealth & Family",{2,11}),
        3:("Siblings, Courage & Communication",{3,6,11}),
        4:("Home & Happiness",{4,11}),
        5:("Intelligence & Children",{5,11}),
        6:("Health & Struggles",{6,11}),
        7:("Marriage & Spouse",{2,7,11}),
        8:("Longevity & Obstacles",{8,11}),
        9:("Luck & Dharma",{9,11}),
        10:("Career & Status",{1,6,10,11}),
        11:("Gains & Desires",{3,6,11}),
        12:("Spiritual Depth & Expenditure",{12,11})
    }
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
        # 🛠️ STRICTNESS UPGRADE: Hardcode the base score directly into the dossier so the AI doesn't have to guess.
        verdict="STRONGLY PROMISED (Base Score: 3)" if len(matched)>=2 or (max(ev_houses) in matched) else ("WEAKLY PROMISED (Base Score: 2)" if len(matched)==1 else "NOT CLEARLY PROMISED (Base Score: 1)")
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
    # Condition: debilitated planet itself in Kendra from Moon
    hfm=whole_sign_house(moon_sidx,p_sidx)
    if hfm in kendra: conds.append(f"debilitated planet in Kendra H{hfm} from Moon")
    # Condition: debilitated planet itself in Kendra from Lagna (classical 5th condition)
    hfl=whole_sign_house(ls,p_sidx)
    if hfl in kendra: conds.append(f"debilitated planet in Kendra H{hfl} from Lagna")
    return conds if conds else None
def get_chara_karakas(planet_data):
    # Full 7-karaka chain per Jaimini (excludes Rahu — standard Parashari Jaimini system)
    planets_for_ck = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    deg = {pn: planet_data[pn][0] % 30 for pn in planets_for_ck}
    ranked = sorted(deg, key=deg.get, reverse=True)
    karaka_names = ["Atmakaraka (AK)","Amatyakaraka (AmK)","Bhratrukaraka (BK)",
                    "Matrukaraka (MK)","Pitrukaraka (PiK)","Putrakaraka (PuK)","Darakaraka (DK)"]
    karaka_chain = {karaka_names[i]: (ranked[i], round(deg[ranked[i]],2)) for i in range(len(ranked))}
    ak, ak_deg = ranked[0], deg[ranked[0]]
    amk, amk_deg = ranked[1], deg[ranked[1]]
    return ak, ak_deg, amk, amk_deg, karaka_chain

def calculate_ashtakavarga(ls, planet_data, r_lon, k_lon):
    """
    Calculates Bhinnashtakavarga (BAV) for all 7 planets.
    Each planet casts benefic bindus to houses based on classical SAV rules.
    Returns: dict of planet -> list of 12 bindu counts (H1 to H12)
    """
    # Classical contributing positions for each planet's BAV
    # Format: {planet: [offsets from which positions contribute a bindu]}
    # Offsets are house counts from each planet's own position that contribute
    # This is the standard Parashari table from BPHS
    BAV_RULES = {
        "Sun":     [1,2,4,7,8,9,10,11],    # from Sun
        "Moon":    [3,6,10,11],             # from Moon; also from Sun: [1,3,6,7,8,10,11]
        "Mars":    [1,2,4,7,8,10,11],
        "Mercury": [1,3,5,6,9,10,11,12],
        "Jupiter": [1,2,3,4,7,8,10,11],
        "Venus":   [1,2,3,4,5,8,9,11,12],
        "Saturn":  [3,5,6,11],
    }
    # Houses where each planet contributes from EACH of the 8 reference points
    # Reference points: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Lagna
    FULL_BAV = {
        "Sun": {
            "Sun":[1,2,4,7,8,9,10,11], "Moon":[3,6,10,11], "Mars":[1,2,4,7,8,10,11],
            "Mercury":[3,5,6,9,12], "Jupiter":[5,6,9,11], "Venus":[6,7,12],
            "Saturn":[1,2,4,7,8,10,11], "Lagna":[3,4,6,10,11,12]
        },
        "Moon": {
            "Sun":[3,6,10,11], "Moon":[1,3,6,7,10,11], "Mars":[2,3,5,6,9,10,11],
            "Mercury":[1,3,4,5,7,8,10,11], "Jupiter":[1,4,7,8,10,11,12],
            "Venus":[3,4,5,7,9,10,11], "Saturn":[3,5,6,11], "Lagna":[3,6,10,11]
        },
        "Mars": {
            "Sun":[3,5,6,10,11], "Moon":[3,6,11], "Mars":[1,2,4,7,8,10,11],
            "Mercury":[3,5,6,11], "Jupiter":[6,10,11,12], "Venus":[6,8,11,12],
            "Saturn":[1,4,7,8,9,10,11], "Lagna":[1,2,4,7,8,10,11]
        },
        "Mercury": {
            "Sun":[5,6,9,11], "Moon":[2,4,6,8,10,11], "Mars":[1,2,4,7,8,9,10,11],
            "Mercury":[1,3,5,6,9,10,11,12], "Jupiter":[6,8,11,12],
            "Venus":[1,2,3,4,5,8,9,11], "Saturn":[1,2,4,7,8,9,10,11], "Lagna":[1,2,4,6,8,10,11]
        },
        "Jupiter": {
            "Sun":[1,2,3,4,7,8,9,10,11], "Moon":[2,5,7,9,11],
            "Mars":[1,2,4,7,8,10,11], "Mercury":[1,2,4,5,6,9,10,11],
            "Jupiter":[1,2,3,4,7,8,10,11], "Venus":[2,5,6,9,10,11],
            "Saturn":[3,5,6,11], "Lagna":[1,2,4,5,6,7,9,10,11]
        },
        "Venus": {
            "Sun":[8,11,12], "Moon":[1,2,3,4,5,8,9,11,12],
            "Mars":[3,4,6,9,11,12], "Mercury":[3,5,6,9,11],
            "Jupiter":[5,8,9,10,11], "Venus":[1,2,3,4,5,8,9,11,12],
            "Saturn":[3,4,5,8,9,10,11], "Lagna":[1,2,3,4,5,8,9,11]
        },
        "Saturn": {
            "Sun":[1,2,4,7,8,10,11], "Moon":[3,6,11],
            "Mars":[3,5,6,10,11,12], "Mercury":[6,8,9,12],
            "Jupiter":[5,6,11,12], "Venus":[6,11,12],
            "Saturn":[3,5,6,11], "Lagna":[1,3,4,6,10,11]
        },
    }

    def get_ref_house(ref_name):
        if ref_name == "Lagna": return ls
        lon = get_planet_lon_helper(ref_name, planet_data, r_lon, k_lon)
        return sign_index_from_lon(lon) if lon is not None else ls

    bav = {}
    for planet, rules in FULL_BAV.items():
        bindus = [0] * 12
        ref_names = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Lagna"]
        for ref in ref_names:
            ref_sidx = get_ref_house(ref)
            offsets = rules.get(ref, [])
            for offset in offsets:
                target_sidx = (ref_sidx + offset - 1) % 12
                target_house = whole_sign_house(ls, target_sidx)
                bindus[target_house - 1] += 1
        bav[planet] = bindus
    return bav

def format_ashtakavarga_summary(bav, ls):
    """Formats Ashtakavarga into a compact dossier string for AI use."""
    lines = ["ASHTAKAVARGA (Planetary Strength per House — bindus/8):"]
    total_sav = [0] * 12
    for planet, bindus in bav.items():
        for i in range(12): total_sav[i] += bindus[i]
        house_str = " ".join(f"H{i+1}:{bindus[i]}" for i in range(12))
        lines.append(f"  {planet:9s}: {house_str}")
    sav_str = " ".join(f"H{i+1}:{total_sav[i]}" for i in range(12))
    lines.append(f"  SAV TOTAL: {sav_str}  (28+ = strong house, <25 = weak house)")
    # Flag notably strong/weak houses
    strong = [f"H{i+1}({total_sav[i]})" for i in range(12) if total_sav[i] >= 30]
    weak   = [f"H{i+1}({total_sav[i]})" for i in range(12) if total_sav[i] <= 22]
    if strong: lines.append(f"  STRONG HOUSES (≥30 SAV bindus): {', '.join(strong)}")
    if weak:   lines.append(f"  WEAK HOUSES (≤22 SAV bindus):   {', '.join(weak)}")
    return "\n".join(lines)
def detect_yogas(ls,moon_sidx,planet_data,r_lon,k_lon):
    def ho(pn):
        lon=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        return whole_sign_house(ls,sign_index_from_lon(lon)) if lon else None
    def si(pn):
        lon=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        return sign_index_from_lon(lon) if lon is not None else None
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

    # ── DHARMA-KARMA ADHIPATI YOGA (9th lord + 10th lord) ──
    h9_lord = SIGN_LORDS_MAP[(ls+8)%12]; h10_lord = SIGN_LORDS_MAP[(ls+9)%12]
    if h9_lord != h10_lord:
        h9h = ho(h9_lord); h10h = ho(h10_lord)
        if h9h and h10h and h9h == h10h:
            yogas.append(("Dharma-Karma Adhipati Yoga", f"9th lord ({h9_lord}) + 10th lord ({h10_lord}) conjunct H{h9h} — peak career success, dharmic profession"))
        else:
            absent.append(f"Dharma-Karma Adhipati Yoga — H9 lord ({h9_lord}) and H10 lord ({h10_lord}) not conjunct")
    
    # ── PARIVARTANA YOGA (mutual sign exchange) ──
    para=[]
    all_planets_para=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    for i,p1 in enumerate(all_planets_para):
        for p2 in all_planets_para[i+1:]:
            s1=si(p1); s2=si(p2)
            if s1 is None or s2 is None: continue
            # p1 in sign of p2 AND p2 in sign of p1
            p1_in_p2_sign = p2 in OWN_SIGNS and s1 in OWN_SIGNS[p2]
            p2_in_p1_sign = p1 in OWN_SIGNS and s2 in OWN_SIGNS[p1]
            if p1_in_p2_sign and p2_in_p1_sign:
                h1=ho(p1); h2=ho(p2)
                para.append(f"{p1}(H{h1})↔{p2}(H{h2})")
    if para: yogas.append(("Parivartana Yoga",f"Mutual sign exchange: {'; '.join(para)} — planets act as if conjunct, mutually empowered"))
    
    dust_lords=[SIGN_LORDS_MAP[(ls+h-1)%12] for h in [6,8,12]]
    dust_in=[dl for dl in dust_lords if ho(dl) in {6,8,12}]
    if len(dust_in)>=2: yogas.append(("Viparita Raja Yoga",f"Dusthana lords ({', '.join(dust_in)}) in dusthana — rise after adversity"))
    else: absent.append("Viparita Raja Yoga — insufficient dusthana lords in dusthana")
    
    # ── KEMADRUMA YOGA — with correct cancellation check ──
    if mh2:
        h2m=((mh2-1+1)%12)+1; h12m=((mh2-1-1)%12)+1
        all_h={pn:ho(pn) for pn in list(planet_data.keys())+["Rahu","Ketu"] if pn!="Moon"}
        flanking=[pn for pn,h in all_h.items() if h in {h2m,h12m} and pn not in {"Rahu","Ketu"}]
        moon_in_kendra = mh2 in {1,4,7,10}  # Moon in Kendra cancels Kemadruma
        if not flanking and not moon_in_kendra:
            yogas.append(("Kemadruma Yoga (Negative)",f"No planets flanking Moon in H{h2m}/H{h12m}, Moon not in Kendra — emotional isolation tendency"))
        elif not flanking and moon_in_kendra:
            absent.append(f"Kemadruma Yoga CANCELLED — Moon in Kendra H{mh2} (classical cancellation)")

    # ── LAKSHMI YOGA (BPHS) ──
    # H9 lord in kendra/trikona AND Venus in own/exalted in kendra/trikona
    h9_lord = SIGN_LORDS_MAP[(ls+8)%12]; h9_lord_h = ho(h9_lord)
    ven_sidx = si("Venus"); ven_h = ho("Venus")
    ven_strong = ven_sidx is not None and (ven_sidx == DIGNITIES["Venus"][0] or ("Venus" in OWN_SIGNS and ven_sidx in OWN_SIGNS["Venus"]))
    if h9_lord_h in {1,4,5,7,9,10} and ven_h in {1,4,5,7,9,10} and ven_strong:
        yogas.append(("Lakshmi Yoga", f"H9 lord ({h9_lord}) in H{h9_lord_h} + Venus strong in H{ven_h} — wealth, fortune, prosperity"))
    else: absent.append("Lakshmi Yoga — conditions not met")

    # ── SARASWATI YOGA (BPHS) ──
    # Jupiter, Venus, Mercury all in kendras, trikonas, or H2
    svs = {1,2,4,5,7,9,10}
    jh_s=ho("Jupiter"); vh_s=ho("Venus"); mh_s=ho("Mercury")
    if jh_s in svs and vh_s in svs and mh_s in svs:
        yogas.append(("Saraswati Yoga", f"Jupiter(H{jh_s})+Venus(H{vh_s})+Mercury(H{mh_s}) in favorable houses — learning, wisdom, eloquence"))
    else: absent.append("Saraswati Yoga — Jupiter/Venus/Mercury not all in favorable houses")

    # ── DHANA YOGA (2nd-11th lord connection) ──
    h2_lord = SIGN_LORDS_MAP[(ls+1)%12]; h11_lord = SIGN_LORDS_MAP[(ls+10)%12]
    h2_lord_h = ho(h2_lord); h11_lord_h = ho(h11_lord)
    if h2_lord == h11_lord:
        yogas.append(("Dhana Yoga", f"{h2_lord} lords both H2 and H11 — natural wealth axis connection"))
    elif h2_lord_h and h11_lord_h:
        if h2_lord_h == h11_lord_h:
            yogas.append(("Dhana Yoga", f"H2 lord ({h2_lord}) + H11 lord ({h11_lord}) conjunct in H{h2_lord_h} — strong wealth accumulation"))
        elif ((h11_lord_h - h2_lord_h) % 12) in {0,3,6,9}:
            yogas.append(("Dhana Yoga", f"H2 lord ({h2_lord}, H{h2_lord_h}) + H11 lord ({h11_lord}, H{h11_lord_h}) in mutual kendra — wealth accumulation"))
        else: absent.append(f"Dhana Yoga — H2 lord ({h2_lord}) and H11 lord ({h11_lord}) not connected")

    # ── AMALA YOGA (BPHS) ──
    # Only natural benefics in H10 from Lagna
    h10_occ = [pn for pn in list(planet_data.keys())+["Rahu","Ketu"] if ho(pn)==10]
    if h10_occ and all(p in {"Jupiter","Venus","Mercury","Moon"} for p in h10_occ):
        yogas.append(("Amala Yoga", f"Only benefics ({', '.join(h10_occ)}) in H10 — spotless reputation, ethical career"))
    else: absent.append("Amala Yoga — H10 empty or contains malefics")

    # ── SUNAPHA / ANAPHA / DURUDHURA YOGA (Moon flanking) ──
    if mh2:
        m_h2 = ((mh2-1+1)%12)+1; m_h12 = ((mh2-1-1)%12)+1
        sun_excluded = {"Sun","Rahu","Ketu"}
        sunapha_p = [pn for pn in planet_data if pn not in sun_excluded and ho(pn)==m_h2]
        anapha_p = [pn for pn in planet_data if pn not in sun_excluded and ho(pn)==m_h12]
        if sunapha_p and anapha_p:
            yogas.append(("Durudhura Yoga", f"Planets in H2({', '.join(sunapha_p)}) and H12({', '.join(anapha_p)}) from Moon — wealth, fame, generosity"))
        elif sunapha_p:
            yogas.append(("Sunapha Yoga", f"{', '.join(sunapha_p)} in H2 from Moon — self-made wealth, resourcefulness"))
        elif anapha_p:
            yogas.append(("Anapha Yoga", f"{', '.join(anapha_p)} in H12 from Moon — spiritual depth, generosity"))

    # ── VESHI / VOSHI / UBHAYACHARI YOGA (Sun flanking) ──
    sun_h = ho("Sun")
    if sun_h:
        s_h2 = ((sun_h-1+1)%12)+1; s_h12 = ((sun_h-1-1)%12)+1
        node_moon = {"Moon","Rahu","Ketu"}
        veshi_p = [pn for pn in planet_data if pn not in node_moon and pn!="Sun" and ho(pn)==s_h2]
        voshi_p = [pn for pn in planet_data if pn not in node_moon and pn!="Sun" and ho(pn)==s_h12]
        if veshi_p and voshi_p:
            yogas.append(("Ubhayachari Yoga", f"Planets flanking Sun: H2({', '.join(veshi_p)})+H12({', '.join(voshi_p)}) — regal bearing, authority"))
        elif veshi_p:
            yogas.append(("Veshi Yoga", f"{', '.join(veshi_p)} in H2 from Sun — status, truthfulness"))
        elif voshi_p:
            yogas.append(("Voshi Yoga", f"{', '.join(voshi_p)} in H12 from Sun — learned, charitable"))

    # ── SHUBHA KARTARI YOGA ON LAGNA ──
    # Natural benefics flanking H1 (in H2 and H12)
    nb = {"Jupiter","Venus","Mercury","Moon"}
    h2_all = [pn for pn in list(planet_data.keys())+["Rahu","Ketu"] if ho(pn)==2]
    h12_all = [pn for pn in list(planet_data.keys())+["Rahu","Ketu"] if ho(pn)==12]
    if any(p in nb for p in h2_all) and any(p in nb for p in h12_all):
        yogas.append(("Shubha Kartari Yoga", "Natural benefics flank Lagna — protection, good fortune, auspicious life"))
    else: absent.append("Shubha Kartari Yoga — benefics do not flank Lagna")

    # ── NEECHA BHANGA RAJA YOGA (add to yoga list when detected) ──
    for pname_nb in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        p_nb_sidx = si(pname_nb)
        if p_nb_sidx is not None and pname_nb in DIGNITIES and p_nb_sidx == DIGNITIES[pname_nb][1]:
            conds_nb = check_neecha_bhanga(pname_nb, ls, moon_sidx, planet_data, r_lon, k_lon)
            if conds_nb:
                yogas.append(("Neecha Bhanga Raja Yoga", f"{pname_nb} debilitated but cancelled — rise through adversity, hidden power"))

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

def calculate_arudha_lagna(ls, planet_data, r_lon, k_lon):
    ll_planet = SIGN_LORDS_MAP[ls]
    ll_house = get_planet_house(ll_planet, ls, planet_data, r_lon, k_lon)
    distance = ll_house - 1
    al_house = ((ll_house - 1 + distance) % 12) + 1
    if al_house == 1: al_house = 4
    elif al_house == 7: al_house = 10
    al_sidx = (ls + al_house - 1) % 12
    return al_house, al_sidx

def calculate_indu_lagna(ls, moon_sidx):
    rays = {"Sun":30, "Moon":16, "Mars":6, "Mercury":8, "Jupiter":10, "Venus":12, "Saturn":1}
    l9_lord = SIGN_LORDS_MAP[(ls + 8) % 12]
    m9_lord = SIGN_LORDS_MAP[(moon_sidx + 8) % 12]
    total_rays = rays.get(l9_lord, 0) + rays.get(m9_lord, 0)
    rem = total_rays % 12
    if rem == 0: rem = 12
    indu_sidx = (moon_sidx + rem - 1) % 12
    return indu_sidx

def calculate_ashta_koota(moon_boy, moon_girl):
    # Boy's and Girl's Moon Longitudes
    s1 = sign_index_from_lon(moon_boy)
    s2 = sign_index_from_lon(moon_girl)
    n1 = min(int((moon_boy % 360) // (360 / 27)), 26)
    n2 = min(int((moon_girl % 360) // (360 / 27)), 26)
    
    # 1. Varna (1 point)
    vm = [1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0]
    v = 1 if vm[s1] <= vm[s2] else 0
    
    # 2. Vashya (2 points)
    va = [0, 0, 1, 2, 3, 1, 1, 4, 0, 2, 1, 2]
    va1, va2 = va[s1], va[s2]
    if va1 == va2: vap = 2
    elif {va1, va2} in [{1, 3}, {1, 4}, {2, 3}]: vap = 0
    else: vap = 1
    
    # 3. Tara (3 points) - Calculated from Girl to Boy and Boy to Girl
    t1 = ((n2 - n1) % 27) % 9  # Boy to Girl
    t2 = ((n1 - n2) % 27) % 9  # Girl to Boy
    ta = (0 if t1 in [2, 4, 6] else 1.5) + (0 if t2 in [2, 4, 6] else 1.5)
    
    # 4. Yoni (4 points)
    ym = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1]
    y1, y2 = ym[n1], ym[n2]
    enemies = [{0, 8}, {1, 13}, {2, 11}, {3, 12}, {4, 10}, {5, 6}, {7, 9}]
    yo = 4 if y1 == y2 else (0 if {y1, y2} in enemies else 2)
    
    # 5. Graha Maitri (5 points)
    lm = [0, 1, 2, 3, 4, 2, 1, 0, 5, 6, 6, 5]
    l1, l2 = lm[s1], lm[s2]
    f_map = {0: [3, 4, 5], 1: [2, 6], 2: [1, 4], 3: [2, 4], 4: [0, 3, 5], 5: [0, 3, 4], 6: [1, 2]}
    e_map = {0: [2], 1: [3, 4], 2: [3], 3: [], 4: [1, 6], 5: [1, 2], 6: [0, 3, 4]}
    def rel(a, b): return 2 if b in f_map.get(a, []) else (0 if b in e_map.get(a, []) else 1)
    ms = {(2, 2): 5, (2, 1): 4, (1, 2): 4, (1, 1): 3, (2, 0): 1, (0, 2): 1, (1, 0): .5, (0, 1): .5, (0, 0): 0}
    m = ms.get((rel(l1, l2), rel(l2, l1)), 0)
    
    # 6. Gana (6 points)
    gm = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0]
    g1, g2 = gm[n1], gm[n2]
    if g1 == g2: g = 6
    elif g1 == 0 and g2 == 1: g = 6
    elif g1 == 1 and g2 == 0: g = 5
    elif g1 == 0 and g2 == 2: g = 1
    else: g = 0
    
    # 7. Bhakoot (7 points)
    dist = (s2 - s1) % 12
    bh = 7 if dist in [0, 2, 3, 6, 8, 9, 10] else 0
    
    # 8. Nadi (8 points)
    nb = [0, 1, 2] * 9
    nd1, nd2 = nb[n1], nb[n2]
    nn = ""
    np = 0
    if nd1 == nd2:
        if n1 == n2: nn = "NADI DOSHA EXCEPTION: Same Nakshatra (Dosha Cancelled)"
        elif SIGN_LORDS_MAP[s1] != SIGN_LORDS_MAP[s2]: nn = "NADI DOSHA PARTIAL EXCEPTION: Different Rashi lords"
    else: np = 8
    
    # Stree-Deergha & Mahendra check (Bonus/Mitigation)
    dist_nak = (n2 - n1) % 27
    mahendra = "Present" if dist_nak in [3, 6, 9, 12, 15, 18, 21, 24] else "Absent"
    stree_deergha = "Excellent" if dist_nak >= 15 else "Poor"

    total = v + vap + ta + yo + m + g + bh + np
    return {
        "score": total,
        "varna": v, "vashya": vap, "tara": ta, "yoni": yo,
        "maitri": m, "gana": g, "bhakoot": bh, "nadi": np,
        "nadi_note": nn, "mahendra": mahendra, "stree_deergha": stree_deergha
    }

def calculate_marital_analysis(jd, lat, lon):
    # Calculates D9 7th House, Upapada Lagna (UL) and Darapada (A7)
    cusps = get_lagna_and_cusps(jd, lat, lon)
    lagna_lon = cusps[0]
    lagna_sign = sign_index_from_lon(lagna_lon)
    
    # Planets
    p = {pn: get_planet_longitude_and_speed(jd, pid)[0] for pn, pid in PLANETS.items()}
    
    # Navamsha (D9)
    d9_lagna_sign = int((lagna_lon % 360) / (360/108)) % 12
    d9_7th_sign = (d9_lagna_sign + 6) % 12
    d9_7th_lord = SIGN_LORDS_MAP[d9_7th_sign]
    
    # Upapada Lagna (UL) - Arudha of 12th House
    h12_sign = (lagna_sign + 11) % 12
    h12_lord = SIGN_LORDS_MAP[h12_sign]
    if h12_lord == "Rahu" or h12_lord == "Ketu": h12_lord = "Saturn" # Proxy
    lord_lon = p[h12_lord]
    lord_sign = sign_index_from_lon(lord_lon)
    dist = (lord_sign - h12_sign) % 12
    ul_sign = (lord_sign + dist) % 12
    # Exceptions
    if ul_sign == h12_sign: ul_sign = (ul_sign + 9) % 12
    elif ul_sign == (h12_sign + 6) % 12: ul_sign = (ul_sign + 9) % 12
    
    # Darapada (A7)
    h7_sign = (lagna_sign + 6) % 12
    h7_lord = SIGN_LORDS_MAP[h7_sign]
    if h7_lord == "Rahu" or h7_lord == "Ketu": h7_lord = "Venus"
    l7_sign = sign_index_from_lon(p[h7_lord])
    d7 = (l7_sign - h7_sign) % 12
    a7_sign = (l7_sign + d7) % 12
    if a7_sign == h7_sign: a7_sign = (a7_sign + 9) % 12
    elif a7_sign == (h7_sign + 6) % 12: a7_sign = (a7_sign + 9) % 12
    
    return {
        "D9_7th_Sign": SIGNS[d9_7th_sign],
        "D9_7th_Lord": d9_7th_lord,
        "UL_Sign": SIGNS[ul_sign],
        "A7_Sign": SIGNS[a7_sign],
        "D1_7th_Sign": SIGNS[h7_sign]
    }

def get_kp_cusp_promise(house_num, ls, planet_data, r_lon, k_lon, placidus_cusps):
    """
    KP Core Event Promise Analysis per kp3.md.
    
    Checks if the Sub-Lord of a given house cusp signifies the required houses
    for that event to be PROMISED in the chart.
    
    KP Rule (K.S. Krishnamurti): The cusp Sub-Lord must be the significator of 
    the event-relevant houses for the event to be promised. Otherwise it is denied.
    
    Classic house groupings per kp3.md:
    - Marriage promise: 2nd (family/sustain), 7th (partner), 11th (fulfilment)
    - Career/Service: 2nd (income), 6th (service), 10th (profession), 11th (gains)
    - Career/Business: 2nd, 7th (partnership), 10th, 11th
    - Children: 2nd, 5th (progeny), 11th
    - Property: 4th (property), 11th (gains/acquisition)
    - Foreign travel: 9th (long travel), 12th (foreign land)
    - Health issue: 6th (disease), 8th (chronic), 12th (hospitalisation)
    
    Returns a detailed verdict string for each house analysis.
    """
    if house_num < 1 or house_num > 12: return "Invalid house number"
    
    cusp_lon = placidus_cusps[house_num - 1]
    cusp_sl = get_kp_sub_lord(cusp_lon)
    cusp_sigs = get_planet_house_significations(cusp_sl, ls, planet_data, r_lon, k_lon)
    
    # KP event promise definitions per kp3.md
    kp_house_rules = {
        7:  {"name": "Marriage", "required": {2,7,11}, "deny": {1,6,10},
             "desc": "2-7-11 must be signified (family bond + partner + fulfilment)"},
        10: {"name": "Career/Profession", "required": {6,10,11}, "deny": {5,8,12},
             "desc": "6-10-11 for service; 2-7-10-11 for business"},
        6:  {"name": "Service/Employment", "required": {2,6,11}, "deny": {5,8,12},
             "desc": "2-6-11 for entering/continuing service"},
        5:  {"name": "Children", "required": {2,5,11}, "deny": {1,4,10},
             "desc": "2-5-11 must be signified for progeny"},
        4:  {"name": "Property/Vehicle", "required": {4,11}, "deny": {3,12},
             "desc": "4-11 for acquisition; 4-12 for loss/sale"},
        2:  {"name": "Wealth/Finance", "required": {2,11}, "deny": {6,8,12},
             "desc": "2-11 for wealth accumulation; 6-12 for debts"},
        11: {"name": "Gains/Desires", "required": {11}, "deny": {6,8,12},
             "desc": "11 signified for gains; 6-8-12 deny"},
        9:  {"name": "Luck/Higher Studies/Foreign", "required": {9,11}, "deny": {6,8,12},
             "desc": "9-11 for luck and higher studies"},
        12: {"name": "Foreign Settlement/Moksha", "required": {9,12}, "deny": {1,5},
             "desc": "9-12 for foreign connection; 12 alone for loss/hospital"},
        1:  {"name": "Self/Longevity", "required": {1,11}, "deny": {2,7},
             "desc": "1-11 for recovery; 2-7 are Maraka (death-inflicting)"},
        8:  {"name": "Longevity/Legacy/Research", "required": {8,11}, "deny": {1,2,7},
             "desc": "8-11 for legacy receipt; 1-2-7 Maraka configuration"},
        3:  {"name": "Siblings/Short Travel/Communication", "required": {3,11}, "deny": {8,12},
             "desc": "3-11 for sibling gains and short travel"},
    }
    
    rule = kp_house_rules.get(house_num, {"name": f"H{house_num}", "required": set(), "deny": set(), "desc": ""})
    required = rule["required"]
    deny_houses = rule["deny"]
    
    fulfilled = cusp_sigs & required
    denied = cusp_sigs & deny_houses
    
    if len(fulfilled) >= len(required):
        verdict = "STRONGLY PROMISED"
    elif len(fulfilled) >= len(required) - 1:
        verdict = "PARTIALLY PROMISED"
    else:
        verdict = "NOT PROMISED / DENIED"
    
    if denied and "NOT PROMISED" not in verdict:
        verdict += f" (but DELAYED/OBSTRUCTED — SL also signifies deny houses {denied})"
    
    return (f"H{house_num} KP Promise ({rule['name']}): SL of H{house_num} cusp = {cusp_sl} | "
            f"SL signifies houses: {sorted(cusp_sigs)} | "
            f"Required: {sorted(required)} → Matched: {sorted(fulfilled)} | "
            f"VERDICT: {verdict}")

def get_kp_marriage_timing_clues(ls, planet_data, r_lon, k_lon, placidus_cusps, dasha_info):
    """
    KP Marriage Timing Analysis per kp3.md Chapter 23.
    
    In KP: Marriage occurs when:
    1. Sub-Lord of 7th cusp signifies 2-7-11 (promise)
    2. Dasha/Antardasha lords signify 2-7-11 
    3. Transit of a significator through the sub of another significator triggers the event
    
    Returns timing clues based on current Dasha lords' significations.
    """
    # Check 7th cusp promise first
    h7_promise = get_kp_cusp_promise(7, ls, planet_data, r_lon, k_lon, placidus_cusps)
    
    # Marriage significators = planets signifying H2, H7, H11
    marriage_houses = {2, 7, 11}
    all_planets_and_nodes = list(planet_data.keys()) + ["Rahu", "Ketu"]
    
    sig_list = []
    for pname in all_planets_and_nodes:
        sigs = get_planet_house_significations(pname, ls, planet_data, r_lon, k_lon)
        if sigs & marriage_houses:
            matched = sigs & marriage_houses
            sig_list.append(f"{pname}(H{sorted(matched)})")
    
    # Check if current Dasha/Antardasha lords are significators
    md = dasha_info.get('current_md', 'Unknown')
    ad = dasha_info.get('current_ad', 'Unknown')
    md_sigs = get_planet_house_significations(md, ls, planet_data, r_lon, k_lon) if md != 'Unknown' else set()
    ad_sigs = get_planet_house_significations(ad, ls, planet_data, r_lon, k_lon) if ad != 'Unknown' else set()
    
    md_supports = bool(md_sigs & marriage_houses)
    ad_supports = bool(ad_sigs & marriage_houses)
    
    timing_verdict = ""
    if md_supports and ad_supports:
        timing_verdict = f"ACTIVE WINDOW — Both {md} MD and {ad} AD signify marriage houses. Current period is ACTIVE for marriage."
    elif md_supports:
        timing_verdict = f"PARTIAL — {md} MD supports marriage (signifies {md_sigs & marriage_houses}), but {ad} AD does not directly support."
    elif ad_supports:
        timing_verdict = f"PARTIAL — {ad} AD supports marriage (signifies {ad_sigs & marriage_houses}), but {md} MD does not directly support."
    else:
        timing_verdict = f"INACTIVE WINDOW — Neither {md} MD nor {ad} AD strongly signifies marriage houses 2-7-11."
    
    return {
        "h7_promise": h7_promise,
        "significators": sig_list,
        "timing_verdict": timing_verdict,
        "md_marriage_sigs": sorted(md_sigs & marriage_houses),
        "ad_marriage_sigs": sorted(ad_sigs & marriage_houses)
    }
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
    # BPHS: In odd signs, 1st half (0-15°) = Sun (Leo=4), 2nd half (15-30°) = Moon (Cancer=3)
    # In even signs, 1st half = Moon (Cancer=3), 2nd half = Sun (Leo=4)
    s = sign_index_from_lon(lon); d = lon % 30
    if s % 2 == 0:  # odd sign (0-indexed: Aries=0, Gemini=2... are even indices = odd signs)
        return 4 if d < 15 else 3  # Aries,Gemini,Leo,Libra,Sag,Aquarius: 1st half=Sun, 2nd=Moon
    else:
        return 3 if d < 15 else 4  # Taurus,Cancer,Virgo,Scorpio,Cap,Pisces: 1st half=Moon, 2nd=Sun
def d3_si(lon): return (sign_index_from_lon(lon)+int((lon%30)//10)*4)%12
def d4_si(lon): return (sign_index_from_lon(lon)+int((lon%30)//7.5)*3)%12
def d7_si(lon):
    # BPHS: For odd signs, count from the sign itself. For even signs, count from 7th from it.
    s = sign_index_from_lon(lon); slot = int((lon % 30) // (30 / 7))
    start = s if s % 2 == 0 else (s + 6) % 12  # odd sign(0-indexed even)=self; even sign=+6(7th)
    return (start + slot) % 12
def d9_si(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//(30/9))
    start=s if s in MOVABLE_SIGNS else ((s+8)%12 if s in FIXED_SIGNS else (s+4)%12)
    return (start+slot)%12
def d10_si(lon):
    s=sign_index_from_lon(lon); slot=int((lon%360%30)//3)
    return ((s if s%2==0 else (s+8)%12)+slot)%12
def d12_si(lon): return (sign_index_from_lon(lon)+int((lon%360%30)//2.5))%12
def d30_si(lon):
    # Parashari Trimsamsa: misfortune, hidden weakness, and durable affliction.
    s = sign_index_from_lon(lon); d = lon % 30
    if s % 2 == 0:  # odd signs
        if d < 5: return 0      # Mars/Aries
        if d < 10: return 10    # Saturn/Aquarius
        if d < 18: return 8     # Jupiter/Sagittarius
        if d < 25: return 2     # Mercury/Gemini
        return 6                # Venus/Libra
    else:           # even signs
        if d < 5: return 1      # Venus/Taurus
        if d < 12: return 5     # Mercury/Virgo
        if d < 20: return 11    # Jupiter/Pisces
        if d < 25: return 9     # Saturn/Capricorn
        return 7                # Mars/Scorpio
def d60_si(lon):
    # BPHS D60: each sign divided into 60 parts of 0.5° each.
    # The 60 parts cycle through all 12 signs 5 times (12×5=60).
    # Odd signs count forward from Aries; even signs count backward from Pisces.
    s = sign_index_from_lon(lon); part = int((lon % 30) / 0.5)  # 0-59
    if s % 2 == 0:  # odd sign (0-indexed): count forward from Aries
        return part % 12
    else:           # even sign: count backward from Pisces
        return (11 - (part % 12)) % 12
def get_moon_lon_from_profile(profile):
    d=date.fromisoformat(profile['date']) if isinstance(profile['date'],str) else profile['date']
    t=(datetime.strptime(profile['time'],"%H:%M").time() if isinstance(profile['time'],str) else profile['time'])
    jd,_,__=local_to_julian_day(d,t,profile['tz']); lon,_=get_planet_longitude_and_speed(jd,PLANETS["Moon"]); return lon

def get_placidus_house(lon, cusps):
    """Calculates if a planet shifts houses in the Bhava Chalit chart."""
    for i in range(12):
        c1=cusps[i]; c2=cusps[(i+1)%12]
        if c1<c2:
            if c1<=lon<c2: return i+1
        else:
            if lon>=c1 or lon<c2: return i+1
    return 1

def get_kp_4step(pname, ls, planet_data, r_lon, k_lon):
    """Calculates the lethal accuracy of KP 4-Step Theory (A,B,C,D level significators)."""
    lon=get_planet_lon_helper(pname,planet_data,r_lon,k_lon)
    if lon is None: return ""
    _,nl,_=nakshatra_info(lon)
    nl_lon=get_planet_lon_helper(nl,planet_data,r_lon,k_lon)
    nl_occ=whole_sign_house(ls,sign_index_from_lon(nl_lon)) if nl_lon else None
    nl_own=[h for h in range(1,13) if SIGN_LORDS_MAP[(ls+h-1)%12]==nl]
    p_occ=whole_sign_house(ls,sign_index_from_lon(lon))
    p_own=[h for h in range(1,13) if SIGN_LORDS_MAP[(ls+h-1)%12]==pname]
    
    sigs=[]
    if nl_occ: sigs.append(f"L1(NL in H{nl_occ})")
    sigs.append(f"L2(In H{p_occ})")
    if nl_own: sigs.append(f"L3(NL owns H{','.join(map(str,nl_own))})")
    if p_own: sigs.append(f"L4(Owns H{','.join(map(str,p_own))})")
    return " | ".join(sigs)

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
    ak,ak_deg,amk,amk_deg,karaka_chain=get_chara_karakas(planet_data)
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
    al_house, al_sidx = calculate_arudha_lagna(ls, planet_data, r_lon, k_lon)
    indu_sidx = calculate_indu_lagna(ls, moon_sidx)
    lines.append(f"Lagna Lord Chain: {ll_chain} | Manglik: {manglik}")
    lines.append(f"Arudha Lagna (AL): {sign_name(al_sidx)} (H{al_house}) | Indu Lagna (Wealth): {sign_name(indu_sidx)}")
    lines.append(f"\nFUNCTIONAL PLANETS FOR {sign_name(ls).upper()} LAGNA (DO NOT override):")
    lines.append(f"  Yogakarakas: {', '.join(yogak) if yogak else 'None'}")
    lines.append(f"  Functional Benefics: {', '.join(f_ben) if f_ben else 'None'}")
    lines.append(f"  Functional Malefics: {', '.join(f_mal) if f_mal else 'None'}")
    lines.append(f"\nPLANETARY POSITIONS (D1 Rasi):")
    house_occupants={i:[] for i in range(1,13)}
    lines.append(f"\nPLANETARY POSITIONS (D1 Rasi):")
    house_occupants={i:[] for i in range(1,13)}
    
    # 🛠️ HELPER FOR PAPA-KARTARI: Track where natural malefics are placed
    malefic_houses = []
    for m_pn in ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]:
        m_lon = get_planet_lon_helper(m_pn, planet_data, r_lon, k_lon)
        malefic_houses.append(whole_sign_house(ls, sign_index_from_lon(m_lon)))

    for pname in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]:
        plon,pspd=planet_data[pname]; sidx=sign_index_from_lon(plon); house=whole_sign_house(ls,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); avastha=get_baladi_avastha(plon); sl=get_kp_sub_lord(plon)
        asp={"Mars":"H4,H8,H7","Jupiter":"H5,H9,H7","Saturn":"H3,H7,H10","Rahu":"H5,H7,H9","Ketu":"H5,H7,H9"}.get(pname,f"H{((house+6)%12)+1}")
        house_occupants[house].append(pname); tags=[]
        
        # 1. Standard Dignity & Retrograde
        if pspd<0 and pname not in ["Sun","Moon"]: tags.append("Retrograde")
        if pname in COMBUST_DEGREES:
            diff=min(abs(plon-planet_data["Sun"][0]),360-abs(plon-planet_data["Sun"][0]))
            # Mercury and Venus have different combust orbs when retrograde vs direct
            if pname == "Mercury":
                orb = 14 if pspd < 0 else 12  # Retrograde: 14°, Direct: 12°
            elif pname == "Venus":
                orb = 16 if pspd < 0 else 8   # Retrograde: 16°, Direct: 8°
            else:
                orb = COMBUST_DEGREES[pname]
            if diff <= orb: tags.append(f"Combust({orb}°orb)")
        if pname in DIGNITIES:
            if sidx==DIGNITIES[pname][0]: tags.append("Exalted")
            elif sidx==DIGNITIES[pname][1]: tags.append("Debilitated")
        if pname in OWN_SIGNS and sidx in OWN_SIGNS[pname]: tags.append("Own Sign")
            
        # 2. 🛠️ D9 NAVAMSA DIGNITIES & VARGOTTAMA
        d9_sign = d9_si(plon)
        if sidx == d9_sign: tags.append("VARGOTTAMA (Immense Inner Strength)")
        if pname in DIGNITIES:
            if d9_sign == DIGNITIES[pname][0]: tags.append("D9-Exalted (Hidden Power)")
            elif d9_sign == DIGNITIES[pname][1]: tags.append("D9-Debilitated (Hidden Weakness)")
        if pname in OWN_SIGNS and d9_sign in OWN_SIGNS[pname]: tags.append("D9-Own Sign")
            
        # 3. GANDANTA & PAPA-KARTARI
        plon_mod = plon % 120 
        if plon_mod > 116.66 or plon_mod < 3.33: tags.append("GANDANTA (Karmic Knot)")
        h_prev = 12 if house == 1 else house - 1
        h_next = 1 if house == 12 else house + 1
        if (h_prev in malefic_houses) and (h_next in malefic_houses) and pname not in ["Sun", "Mars", "Saturn"]:
            tags.append("PAPA-KARTARI (Hemmed in/Blocked)")

        # 4. 🛠️ BHAVA CHALIT CUSP SHIFT
        plac_h = get_placidus_house(plon, placidus_cusps)
        if plac_h != house: tags.append(f"Bhava Chalit Shift: Acts as H{plac_h}")

        tag_str=f" [{', '.join(tags)}]" if tags else ""
        kp_4 = get_kp_4step(pname, ls, planet_data, r_lon, k_lon)
        
        lines.append(f"  {pname}: H{house} {sign_name(sidx)} {format_dms(plon%30)}{tag_str} | Avastha:{avastha} | Nak:{nak}(NL:{nak_lord} SL:{sl} P:{pada})")
        lines.append(f"    ↳ Asp: {asp} | KP 4-Step: {kp_4}")

    # Process Nodes (Rahu/Ketu)
    for pname,plon in [("Rahu",r_lon),("Ketu",k_lon)]:
        sidx=sign_index_from_lon(plon); house=whole_sign_house(ls,sidx)
        nak,nak_lord,pada=nakshatra_info(plon); sl=get_kp_sub_lord(plon); house_occupants[house].append(pname)
        
        tags = ["Retrograde"]
        d9_sign = d9_si(plon)
        if sidx == d9_sign: tags.append("VARGOTTAMA")
        plon_mod = plon % 120
        if plon_mod > 116.66 or plon_mod < 3.33: tags.append("GANDANTA")
        plac_h = get_placidus_house(plon, placidus_cusps)
        if plac_h != house: tags.append(f"Bhava Chalit Shift: Acts as H{plac_h}")
        
        kp_4 = get_kp_4step(pname, ls, planet_data, r_lon, k_lon)
        lines.append(f"  {pname}: H{house} {sign_name(sidx)} {format_dms(plon%30)} [{', '.join(tags)}] | Nak:{nak}(NL:{nak_lord} SL:{sl} P:{pada})")
        lines.append(f"    ↳ KP 4-Step: {kp_4}")
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
    lines.append(f"[Jaimini Chara Karakas — Full Chain]")
    for kname,(kplanet,kdeg) in karaka_chain.items():
        lines.append(f"  {kname}: {kplanet} ({kdeg:.2f}°)")
    lines.append(f"\nHOUSE STRENGTH SUMMARY (pre-computed, use directly):")
    for hs in house_summary: lines.append(f"  {hs}")
    if not compact:
        # Ashtakavarga — full calculation
        bav = calculate_ashtakavarga(ls, planet_data, r_lon, k_lon)
        lines.append(f"\n{format_ashtakavarga_summary(bav, ls)}")
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
        
        # KP EVENT PROMISE ANALYSIS — key houses checked per kp3.md rules
        lines.append(f"\nKP EVENT PROMISE ANALYSIS (Sub-Lord of each cusp vs required houses):")
        lines.append("  [Parashari shows NATURE of life. KP shows IF & WHEN events MANIFEST.]")
        lines.append("  [AI RULE: Use these verdicts as the FINAL WORD on event promise/denial.]")
        for h_check in [7, 10, 6, 5, 4, 2, 9, 12]:
            try:
                promise_line = get_kp_cusp_promise(h_check, ls, planet_data, r_lon, k_lon, placidus_cusps)
                lines.append(f"  {promise_line}")
            except Exception:
                pass
        
        # KP Marriage Timing Clues
        try:
            marriage_timing = get_kp_marriage_timing_clues(ls, planet_data, r_lon, k_lon, placidus_cusps, dasha_info)
            lines.append(f"\nKP MARRIAGE TIMING CLUES:")
            lines.append(f"  {marriage_timing['h7_promise']}")
            lines.append(f"  Significators for marriage (2-7-11): {', '.join(marriage_timing['significators'][:8])}")
            lines.append(f"  Current Dasha Timing: {marriage_timing['timing_verdict']}")
        except Exception:
            pass
    lines.append(f"\nDIVISIONAL CHARTS:")
    all_pn=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    d2,d3,d4,d7,d9,d10,d12,d30,d60=[],[],[],[],[],[],[],[],[]
    for pn in all_pn:
        pl=get_planet_lon_helper(pn,planet_data,r_lon,k_lon)
        d2.append(f"{pn}:{sign_name(d2_si(pl))}"); d3.append(f"{pn}:{sign_name(d3_si(pl))}")
        d4.append(f"{pn}:{sign_name(d4_si(pl))}"); d7.append(f"{pn}:{sign_name(d7_si(pl))}")
        d9.append(f"{pn}:{sign_name(d9_si(pl))}"); d10.append(f"{pn}:{sign_name(d10_si(pl))}")
        d12.append(f"{pn}:{sign_name(d12_si(pl))}"); d30.append(f"{pn}:{sign_name(d30_si(pl))}")
        if include_d60: d60.append(f"{pn}:{sign_name(d60_si(pl))}")
    lines.append(f"  D9 Navamsa(Marriage): {', '.join(d9)}")
    lines.append(f"  D10 Dasamsa(Career):  {', '.join(d10)}")
    lines.append(f"  D2 Hora(Wealth):      {', '.join(d2)}")
    lines.append(f"  D3 Drekkana(Courage): {', '.join(d3)}")
    lines.append(f"  D4 Chaturt(Property): {', '.join(d4)}")
    lines.append(f"  D7 Saptam(Children):  {', '.join(d7)}")
    lines.append(f"  D12 Dwadam(Parents):  {', '.join(d12)}")
    lines.append(f"  D30 Trimsamsa(Pitfalls): {', '.join(d30)}")
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

import re

# ═══════════════════════════════════════════════════════════
# THE UNIVERSAL PYTHON MATH ENGINE (THE OBSERVATORY)
# ═══════════════════════════════════════════════════════════
def extract_base_score(dossier_text, house_number):
    """Python reads the generated dossier to find the exact numerical score."""
    match = re.search(rf"H{house_number} \([^)]+\):.*?Base Score: (\d)", dossier_text)
    return int(match.group(1)) if match else 1

def extract_yogas(dossier_text):
    """Python counts the exact number of active yogas."""
    if "[Yogas — PRESENT ✓]" not in dossier_text: return 0
    try:
        yogas_section = dossier_text.split("[Yogas — PRESENT ✓]")[1].split("[Yogas — ABSENT ✗")[0]
        return yogas_section.count("✓")
    except: return 0

def extract_kp_promise(dossier_text, house_number):
    """Extract KP cusp promise verdict for a house from the dossier."""
    pattern = rf"H{house_number} KP Promise[^|]+\| VERDICT: ([^\n]+)"
    match = re.search(pattern, dossier_text)
    if not match: return 0
    v = match.group(1)
    if "STRONGLY PROMISED" in v: return 3
    if "PARTIALLY PROMISED" in v: return 2
    if "DENIED" in v or "NOT PROMISED" in v: return 0
    return 1

def extract_planet_dignity(dossier_text, planet_name):
    """Extract a planet's dignity status from the dossier."""
    pattern = rf"{planet_name}.*?(Exalted|Own Sign|Moolatrikona|Debilitated|Combust|Vargottama|Neecha Bhanga)"
    match = re.search(pattern, dossier_text, re.IGNORECASE)
    if not match: return 0
    d = match.group(1).lower()
    if d in ("exalted", "moolatrikona"): return 3
    if d in ("own sign", "vargottama"): return 2
    if d == "neecha bhanga": return 1
    if d in ("debilitated", "combust"): return -2
    return 0

def extract_yoga_presence(dossier_text, yoga_name):
    """Check if a specific yoga is present."""
    return 1 if (f"✓ {yoga_name}" in dossier_text or yoga_name in dossier_text.split("[Yogas — ABSENT")[0]) else 0

def extract_ashtakavarga_score(dossier_text, house_number):
    """Extract SAV bindu total for a specific house from the dossier."""
    pattern = rf"SAV TOTAL:.*?H{house_number}:(\d+)"
    match = re.search(pattern, dossier_text)
    if match:
        bindus = int(match.group(1))
        # Normalize: 28+ = strong(3), 25-27 = average(2), <25 = weak(1)
        if bindus >= 30: return 3
        if bindus >= 25: return 2
        return 1
    return 2  # Default if not found

def check_affliction(dossier_text, affliction_type):
    """Python flags penalties like Sade Sati."""
    if affliction_type == "Sade Sati": return "Sade Sati: ACTIVE" in dossier_text or "ACTIVE (Phase" in dossier_text
    elif "Graha Yuddha" in affliction_type: return "WINS (higher ecliptic latitude)" in dossier_text
    return False

def extract_planet_house(dossier_text, planet_name):
    """Extract which house a planet occupies from the dossier."""
    pattern = rf"{planet_name}.*?H(\d+)\)"
    match = re.search(pattern, dossier_text[:3000])  # Only look in the planets section
    return int(match.group(1)) if match else 0

def score_planet_in_house(planet_house, good_houses, bad_houses):
    """Score a planet based on whether it's in a good or bad house."""
    if planet_house in good_houses: return 2
    if planet_house in bad_houses: return -1
    return 1

_PLANET_RE = r"(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)"
_CHART_FACTS_CACHE = {}

_NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_DUSTHANAS = {6, 8, 12}
_KENDRAS = {1, 4, 7, 10}
_TRIKONAS = {1, 5, 9}
_SIGN_INDEX = {name: i for i, name in enumerate(SIGNS)}

def _clamp(value, low=0, high=100):
    return max(low, min(high, value))

def _score_positive(parts):
    total = 0
    weight = 0
    for value, w in parts:
        total += _clamp(value) * w
        weight += w
    return _clamp(total / weight if weight else 50)

def _split_csv_ints(raw):
    return {int(x) for x in re.findall(r"\d+", raw or "")}

def _criterion_key(label):
    text = str(label).strip()
    known = [
        "Wealth Potential", "Relationship Quality", "Career Success",
        "Life Struggles", "Health & Longevity", "Happiness & Contentment",
        "Luck & Fortune", "Spiritual Depth", "Hidden Pitfalls",
    ]
    for key in known:
        if text.startswith(key):
            return key
    for sep in [" — ", " â€” ", " - ", " -- ", " – "]:
        if sep in text:
            return text.split(sep, 1)[0].strip()
    return text

def _section_between(text, start_marker, end_marker=None):
    start = text.find(start_marker)
    if start < 0: return ""
    if end_marker is None:
        return text[start:]
    end = text.find(end_marker, start + len(start_marker))
    return text[start:] if end < 0 else text[start:end]

def _kp_score_from_verdict(verdict):
    v = (verdict or "").upper()
    if "STRONGLY PROMISED" in v: return 3
    if "PARTIALLY PROMISED" in v: return 2
    if "DENIED" in v or "NOT PROMISED" in v: return 0
    return 1

def _house_norm(base_score):
    return {1: 38, 2: 62, 3: 84}.get(base_score, 50)

def _sav_norm(bindus):
    if bindus is None: return 50
    return _clamp(50 + (bindus - 28) * 3.2, 25, 85)

def _kp_norm(kp_score):
    return {0: 25, 1: 50, 2: 68, 3: 86}.get(kp_score, 50)

def _parse_varga_line(dossier_text, label):
    match = re.search(rf"{label}[^:]*:\s*([^\n]+)", dossier_text)
    if not match: return {}
    out = {}
    for part in match.group(1).split(","):
        if ":" not in part: continue
        planet, sign = [x.strip() for x in part.split(":", 1)]
        sign = re.sub(r"[^A-Za-z ]", "", sign).strip()
        if planet and sign: out[planet] = sign
    return out

def _extract_present_yogas(dossier_text):
    present = {}
    section = _section_between(dossier_text, "[Yogas", "[Jaimini")
    for line in section.splitlines():
        if "Yoga" not in line or "ABSENT" in line.upper(): continue
        match = re.search(r"([A-Za-z][A-Za-z\-\s]+Yoga(?:\s*\(Negative\))?):\s*(.*)", line)
        if match:
            present[re.sub(r"\s+", " ", match.group(1)).strip()] = match.group(2).strip()
    return present

def _parse_chart_facts(dossier_text):
    key = (len(dossier_text), hash(dossier_text))
    if key in _CHART_FACTS_CACHE:
        return _CHART_FACTS_CACHE[key]

    facts = {
        "houses": {},
        "house_lords": {},
        "planets": {},
        "sav": {},
        "kp": {},
        "yogas": _extract_present_yogas(dossier_text),
        "vargas": {
            "D2": _parse_varga_line(dossier_text, "D2 Hora"),
            "D9": _parse_varga_line(dossier_text, "D9 Navamsa"),
            "D10": _parse_varga_line(dossier_text, "D10 Dasamsa"),
            "D12": _parse_varga_line(dossier_text, "D12"),
            "D30": _parse_varga_line(dossier_text, "D30"),
        },
        "karakas": {},
        "neecha_bhanga": set(),
        "weak_sav_houses": set(),
        "strong_sav_houses": set(),
        "manglik": "NOT MANGLIK",
        "arudha_lagna": {"house": 0, "sign": ""},
        "indu_lagna": {"sign": ""},
    }

    al_match = re.search(r"Arudha Lagna \(AL\):\s*([A-Za-z]+)\s*\(H(\d+)\)", dossier_text)
    if al_match:
        facts["arudha_lagna"] = {"sign": al_match.group(1), "house": int(al_match.group(2))}
        
    indu_match = re.search(r"Indu Lagna \(Wealth\):\s*([A-Za-z]+)", dossier_text)
    if indu_match:
        facts["indu_lagna"] = {"sign": indu_match.group(1)}

    for h, theme, lord, lord_house, flags, kp_sl, base in re.findall(
        r"H(\d{1,2}) \(([^)]+)\): Lord=([A-Za-z]+)\(H(\d{1,2})\) \[([^\]]*)\] \| KP SL=([A-Za-z]+): .*?Base Score: (\d)",
        dossier_text
    ):
        hnum = int(h)
        facts["houses"][hnum] = {"theme": theme, "base": int(base), "kp_sl": kp_sl, "flags": flags, "occupants": []}
        facts["house_lords"][hnum] = {"planet": lord, "house": int(lord_house), "flags": flags}

    for h, sign, lord, lord_house, occ in re.findall(
        r"H(\d{2})\(([A-Za-z]+)\): Lord=([A-Za-z]+)\(H(\d{1,2})\) \| ([^\n]+)",
        dossier_text
    ):
        hnum = int(h)
        facts["house_lords"].setdefault(hnum, {"planet": lord, "house": int(lord_house), "flags": ""})
        facts["houses"].setdefault(hnum, {"theme": sign, "base": extract_base_score(dossier_text, hnum), "kp_sl": "", "flags": "", "occupants": []})
        facts["houses"][hnum]["occupants"] = [x.strip() for x in occ.split(",") if x.strip() and x.strip() != "Empty"]

    planet_pat = re.compile(
        rf"^\s*{_PLANET_RE}: H(\d{{1,2}})\s+([A-Za-z]+)\s+.*?(?:\[(.*?)\])?.*?(?:Avastha:([^|]+)\|)?\s*Nak:([^(]+)\(NL:([A-Za-z]+)\s+SL:([A-Za-z]+)",
        re.MULTILINE
    )
    for match in planet_pat.finditer(dossier_text):
        planet, house, sign, tags_raw, avastha, nak, nl, sl = match.groups()
        tags = {t.strip() for t in (tags_raw or "").split(",") if t.strip()}
        facts["planets"][planet] = {
            "house": int(house),
            "sign": sign,
            "tags": tags,
            "avastha": (avastha or "").strip(),
            "nak": nak.strip(),
            "nak_lord": nl,
            "sub_lord": sl,
            "kp_sigs": set(),
            "war": "",
        }

    for planet, sig_text in re.findall(rf"{_PLANET_RE}.*?KP 4-Step:\s*([^\n]+)", dossier_text):
        facts["planets"].setdefault(planet, {"house": 0, "tags": set(), "kp_sigs": set(), "war": ""})
        facts["planets"][planet]["kp_sigs"] = _split_csv_ints(sig_text)

    sav_match = re.search(r"SAV TOTAL:\s*([^\n]+)", dossier_text)
    if sav_match:
        for h, bindus in re.findall(r"H(\d{1,2}):(\d+)", sav_match.group(1)):
            facts["sav"][int(h)] = int(bindus)
    for h, bindus in re.findall(r"H(\d{1,2})\((\d+)\)", _section_between(dossier_text, "WEAK HOUSES")):
        if int(bindus) <= 22: facts["weak_sav_houses"].add(int(h))
    for h, bindus in re.findall(r"H(\d{1,2})\((\d+)\)", _section_between(dossier_text, "STRONG HOUSES")):
        if int(bindus) >= 30: facts["strong_sav_houses"].add(int(h))

    for h, sigs, matched, verdict in re.findall(
        r"H(\d{1,2}) KP Promise.*?SL signifies houses:\s*\[([^\]]*)\].*?Matched:\s*\[([^\]]*)\].*?VERDICT:\s*([^\n]+)",
        dossier_text
    ):
        hnum = int(h)
        facts["kp"][hnum] = {
            "sigs": _split_csv_ints(sigs),
            "matched": _split_csv_ints(matched),
            "verdict": verdict.strip(),
            "score": _kp_score_from_verdict(verdict),
        }

    for kname, planet in re.findall(r"(Atmakaraka|Amatyakaraka|Darakaraka)[^:]*:\s*([A-Za-z]+)", dossier_text):
        facts["karakas"][kname] = planet

    for planet in re.findall(r"([A-Za-z]+)\s+.*?NEECHA BHANGA APPLIES", dossier_text):
        if planet in PLANETS: facts["neecha_bhanga"].add(planet)

    for winner, loser in re.findall(r"([A-Za-z]+) vs ([A-Za-z]+).*?WINS", dossier_text):
        facts["planets"].setdefault(winner, {"house": 0, "tags": set(), "kp_sigs": set(), "war": ""})["war"] = "WINNER"
        facts["planets"].setdefault(loser, {"house": 0, "tags": set(), "kp_sigs": set(), "war": ""})["war"] = "LOSER"

    m = re.search(r"Manglik:\s*([^\n]+)", dossier_text)
    if m: facts["manglik"] = m.group(1).strip()

    _CHART_FACTS_CACHE[key] = facts
    return facts

def _planet_house(facts, planet):
    return facts["planets"].get(planet, {}).get("house", 0)

def _planet_strength(facts, planet):
    if not planet: return 50
    data = facts["planets"].get(planet, {})
    tags = data.get("tags", set())
    score = 52
    if any(t == "Exalted" or t.startswith("Exalted") for t in tags): score += 24
    if any("Own Sign" in t for t in tags): score += 16
    if any("VARGOTTAMA" in t.upper() for t in tags): score += 10
    if any("D9-Exalted" in t for t in tags): score += 9
    if any("D9-Own Sign" in t for t in tags): score += 6
    if any("D9-Debilitated" in t for t in tags): score -= 10
    if any("Debilitated" in t for t in tags):
        score -= 22
        if planet in facts["neecha_bhanga"]: score += 24
    if any("Combust" in t for t in tags): score -= 11
    if any("GANDANTA" in t for t in tags): score -= 8
    if any("PAPA-KARTARI" in t for t in tags): score -= 10
    if data.get("war") == "LOSER": score -= 14
    if data.get("avastha") in {"Adult", "Youth"}: score += 5
    elif data.get("avastha") == "Old": score -= 4
    elif data.get("avastha") == "Dead": score -= 13
    
    nak_lord = data.get("nak_lord")
    if nak_lord and nak_lord in facts["planets"]:
        nl_tags = facts["planets"][nak_lord].get("tags", set())
        if any(t == "Exalted" or t.startswith("Exalted") for t in nl_tags): score += 6
        if any("Own Sign" in t for t in nl_tags): score += 3
        if any("Debilitated" in t for t in nl_tags): score -= 6

    if planet in {"Rahu", "Ketu"}:
        score = 50
        if any("VARGOTTAMA" in t.upper() for t in tags): score += 8
        if any("GANDANTA" in t for t in tags): score -= 10
    return _clamp(score, 10, 95)

def _varga_sign_strength(facts, chart, planet):
    if not planet: return 50
    sign = facts["vargas"].get(chart, {}).get(planet)
    if not sign: return 50
    sidx = _SIGN_INDEX.get(sign)
    if sidx is None: return 50
    score = 50
    if planet in DIGNITIES:
        if sidx == DIGNITIES[planet][0]: score += 24
        elif sidx == DIGNITIES[planet][1]: score -= 24
    if planet in OWN_SIGNS and sidx in OWN_SIGNS[planet]: score += 16
    if planet in {"Rahu", "Ketu"} and sign in {"Gemini", "Virgo", "Sagittarius", "Pisces", "Scorpio"}:
        score += 6
    return _clamp(score, 20, 88)

def _house_score(facts, house):
    base = _house_norm(facts["houses"].get(house, {}).get("base", 1))
    sav = _sav_norm(facts["sav"].get(house))
    lord = facts["house_lords"].get(house, {}).get("planet")
    lord_strength = _planet_strength(facts, lord) if lord else 50
    lord_house = facts["house_lords"].get(house, {}).get("house")
    placement_bonus = 0
    if lord_house in _KENDRAS or lord_house in _TRIKONAS: placement_bonus += 5
    if lord_house in _DUSTHANAS: placement_bonus -= 7
    return _clamp(base * 0.45 + sav * 0.20 + lord_strength * 0.30 + 5 + placement_bonus, 15, 95)

def _topic_yoga_score(facts, names, planet_data=None, ls=None, lagna_lon=None, jd_ut=None):
    return sum(weight for name, weight in names.items() if name in facts["yogas"])

def _topic_house_connection(facts, planets, houses):
    houses = set(houses)
    score = 0
    for planet in planets:
        if not planet: continue
        pdata = facts["planets"].get(planet, {})
        if pdata.get("house") in houses: score += 4
        matched = pdata.get("kp_sigs", set()) & houses
        score += min(6, len(matched) * 2)
    return score

def _affliction_count(facts, planets=None, houses=None):
    planets = set(planets or facts["planets"].keys())
    houses = set(houses or range(1, 13))
    count = 0
    for planet in planets:
        if not planet: continue
        pdata = facts["planets"].get(planet, {})
        if pdata.get("house") not in houses: continue
        tags = pdata.get("tags", set())
        if any("Debilitated" in t for t in tags) and planet not in facts["neecha_bhanga"]: count += 1
        if any("Combust" in t for t in tags): count += 1
        if any("GANDANTA" in t for t in tags): count += 1
        if any("PAPA-KARTARI" in t for t in tags): count += 1
        if pdata.get("war") == "LOSER": count += 1
        if pdata.get("avastha") == "Dead": count += 1
    return count

def _malefic_pressure(facts, houses):
    houses = set(houses)
    score = 0
    for planet in _NATURAL_MALEFICS:
        h = _planet_house(facts, planet)
        if h in houses:
            score += 6 if planet in {"Rahu", "Ketu", "Saturn", "Mars"} else 3
    return score

def _benefic_support(facts, houses):
    houses = set(houses)
    return sum(5 for planet in _NATURAL_BENEFICS if _planet_house(facts, planet) in houses)

# Overrides for the legacy extractors above. Missing KP is now "unclear", not denial.
def extract_kp_promise(dossier_text, house_number):
    facts = _parse_chart_facts(dossier_text)
    if house_number in facts["kp"]:
        return facts["kp"][house_number]["score"]
    pattern = rf"H{house_number} KP Promise[^|]+\| VERDICT: ([^\n]+)"
    match = re.search(pattern, dossier_text)
    return _kp_score_from_verdict(match.group(1)) if match else 1

def extract_planet_dignity(dossier_text, planet_name):
    strength = _planet_strength(_parse_chart_facts(dossier_text), planet_name)
    if strength >= 78: return 3
    if strength >= 65: return 2
    if strength >= 54: return 1
    if strength <= 35: return -2
    return 0

def extract_yoga_presence(dossier_text, yoga_name):
    return 1 if yoga_name in _parse_chart_facts(dossier_text)["yogas"] else 0

def extract_yogas(dossier_text):
    return len(_parse_chart_facts(dossier_text)["yogas"])

def extract_planet_house(dossier_text, planet_name):
    return _planet_house(_parse_chart_facts(dossier_text), planet_name)

def _recalc_math(dossier):
    import re
    from datetime import datetime
    time_match = re.search(r"Time:\s*(.*?)\s*\(", dossier)
    coord_match = re.search(r"Coordinates:\s*([0-9.]+)([NS]),\s*([0-9.]+)([EW])\s*\|\s*Timezone:\s*([^\s\n]+)", dossier)
    if not time_match or not coord_match: return None
    dt_str = time_match.group(1).strip()
    try:
        dt_local = datetime.strptime(dt_str, "%d %b %Y, %I:%M %p")
    except: return None
    lat_val, lat_dir, lon_val, lon_dir, tz_name = coord_match.groups()
    lat = float(lat_val) if lat_dir == 'N' else -float(lat_val)
    lon = float(lon_val) if lon_dir == 'E' else -float(lon_val)
    
    jd_ut, _, _ = local_to_julian_day(dt_local.date(), dt_local.time(), tz_name)
    lagna_lon, _ = get_lagna_and_cusps(jd_ut, lat, lon)
    ls = sign_index_from_lon(lagna_lon)
    placidus_cusps = get_placidus_cusps(jd_ut, lat, lon)
    planet_data = {pn: get_planet_longitude_and_speed(jd_ut, pid) for pn, pid in PLANETS.items()}
    r_lon = get_rahu_longitude(jd_ut)
    k_lon = (r_lon + 180.0) % 360
    planet_data["Rahu"] = (r_lon, -0.05)
    planet_data["Ketu"] = (k_lon, -0.05)
    return ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon


def calculate_shadbala(pname, p_lon, p_spd, lagna_lon, ls, f, planet_data, jd_ut):
    if pname in {"Rahu", "Ketu"}: return 5.0
    sthana = 0
    deep_exaltation = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}
    if pname in deep_exaltation:
        neecha = (deep_exaltation[pname] + 180) % 360
        dist = abs(p_lon - neecha)
        dist = min(dist, 360 - dist)
        sthana += dist / 3.0 
    p_sign = int(p_lon // 30) % 12
    varga_str = _planet_strength(f, pname) 
    sthana += (varga_str / 95.0) * 112.5 
    if p_sign % 2 == 0:
        if pname in {"Sun", "Mars", "Jupiter", "Saturn", "Mercury"}: sthana += 15
    else:
        if pname in {"Venus", "Moon"}: sthana += 15
    p_house = ((p_sign - ls) % 12) + 1
    if p_house in {1, 4, 7, 10}: sthana += 60
    elif p_house in {2, 5, 8, 11}: sthana += 30
    else: sthana += 15
    drekkana = int((p_lon % 30) // 10)
    if drekkana == 0 and pname in {"Sun", "Mars", "Jupiter"}: sthana += 15
    elif drekkana == 1 and pname in {"Mercury", "Saturn"}: sthana += 15
    elif drekkana == 2 and pname in {"Moon", "Venus"}: sthana += 15
    dig_peak_house = {"Jupiter": 1, "Mercury": 1, "Sun": 10, "Mars": 10, "Saturn": 7, "Moon": 4, "Venus": 4}
    dig = 0
    if pname in dig_peak_house:
        peak_lon = ((ls + dig_peak_house[pname] - 1) * 30 + 15) % 360
        dist = abs(p_lon - peak_lon)
        dist = min(dist, 360 - dist)
        dig = (180 - dist) / 3.0 
    sun_lon = planet_data.get("Sun", (0,0))[0]
    sun_dist = (sun_lon - lagna_lon) % 360
    time_fraction = (sun_dist + 90) % 360 / 360.0
    if pname in {"Moon", "Mars", "Saturn"}: nath = (1.0 - abs(time_fraction - 0.5) * 2) * 60
    elif pname in {"Sun", "Jupiter", "Venus"}: nath = (abs(time_fraction - 0.5) * 2) * 60
    else: nath = 60 
    moon_lon = planet_data.get("Moon", (0,0))[0]
    moon_sun_diff = (moon_lon - sun_lon) % 360
    if pname in {"Moon", "Venus", "Jupiter", "Mercury"}:
        paksha = moon_sun_diff / 3.0 if moon_sun_diff <= 180 else (360 - moon_sun_diff) / 3.0
    else:
        paksha = (180 - (moon_sun_diff if moon_sun_diff <= 180 else (360 - moon_sun_diff))) / 3.0
    if pname == "Moon": paksha *= 2
    kala = nath + paksha
    chesta = 0
    if p_spd < 0: chesta = 60 
    elif pname in {"Sun", "Moon"}:
        if pname == "Sun": chesta = 30
        if pname == "Moon" and paksha > 30: chesta = 30
    else: chesta = 15 
    naisargika = {"Sun": 60, "Moon": 51.4, "Venus": 42.8, "Jupiter": 34.2, "Mercury": 25.7, "Mars": 17.1, "Saturn": 8.5}
    nais = naisargika.get(pname, 0)
    drig = 0
    for op, (olon, ospd) in planet_data.items():
        if op == pname or op in {"Rahu", "Ketu"}: continue
        drishti = _calc_drishti(olon, p_lon, op)
        if op in {"Jupiter", "Venus", "Mercury", "Moon"}: drig += drishti / 4.0
        else: drig -= drishti / 4.0
    return max(0.1, (sthana + dig + kala + chesta + nais + drig) / 60.0)

def calculate_argala(house_idx, f):
    argala_houses = [(house_idx + offset - 1) % 12 + 1 for offset in [2, 4, 5, 11]]
    virodha_houses = [(house_idx + offset - 1) % 12 + 1 for offset in [3, 10, 12]]
    net_argala = 0
    for h in argala_houses:
        occupants = f["houses"].get(h, {}).get("occupants", [])
        for occ in occupants:
            if occ in {"Jupiter", "Venus", "Moon", "Mercury"}: net_argala += 4
            elif occ in {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}: net_argala += 2
    for h in virodha_houses:
        occupants = f["houses"].get(h, {}).get("occupants", [])
        for occ in occupants:
            if occ in {"Jupiter", "Venus", "Moon", "Mercury"}: net_argala -= 3
            elif occ in {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}: net_argala -= 2
    return net_argala

def _yoga_strength_multiplier(yoga_name, facts, planet_data, ls, lagna_lon, jd_ut):
    if yoga_name == "Gajakesari Yoga":
        jup = _get_p_str("Jupiter", planet_data, ls, facts, lagna_lon, jd_ut)
        moon = _get_p_str("Moon", planet_data, ls, facts, lagna_lon, jd_ut)
        return ((jup + moon) / 2.0) / 75.0
    elif yoga_name == "Hamsa Yoga":
        return _get_p_str("Jupiter", planet_data, ls, facts, lagna_lon, jd_ut) / 75.0
    elif yoga_name == "Malavya Yoga":
        return _get_p_str("Venus", planet_data, ls, facts, lagna_lon, jd_ut) / 75.0
    elif yoga_name in {"Ruchaka Yoga", "Chandra-Mangala Yoga"}:
        return _get_p_str("Mars", planet_data, ls, facts, lagna_lon, jd_ut) / 75.0
    elif yoga_name == "Bhadra Yoga":
        return _get_p_str("Mercury", planet_data, ls, facts, lagna_lon, jd_ut) / 75.0
    elif yoga_name == "Shasha Yoga":
        return _get_p_str("Saturn", planet_data, ls, facts, lagna_lon, jd_ut) / 75.0
    return 1.0


def _calc_drishti(p1_lon, p2_lon, p1_name):
    diff = (p2_lon - p1_lon) % 360
    aspects = [180]
    if p1_name == "Mars": aspects += [90, 210]
    elif p1_name in {"Jupiter", "Rahu", "Ketu"}: aspects += [120, 240]
    elif p1_name == "Saturn": aspects += [60, 270]
    max_strength = 0
    for asp in aspects:
        orb = abs(diff - asp)
        orb = min(orb, 360 - orb)
        if orb <= 15:
            strength = 100 - (orb * 6.66)
            if strength > max_strength: max_strength = strength
    return max_strength

def _get_bhava_bala(house_idx, ls, planet_data, f, lagna_lon, jd_ut):
    bindus = f["sav"].get(house_idx, 28)
    base_score = _sav_norm(bindus) 
    lord = f["house_lords"].get(house_idx, {}).get("planet")
    lord_strength = _get_p_str(lord, planet_data, ls, f, lagna_lon, jd_ut) 
    argala = calculate_argala(house_idx, f)
    return max(0, min(100, base_score * 0.45 + lord_strength * 0.40 + argala * 1.5))

def _get_kp_sub_lord_score(house_idx, placidus_cusps, planet_data, r_lon, k_lon, ls, required_houses, deny_houses):
    cusp_lon = placidus_cusps[house_idx - 1]
    sl = get_kp_sub_lord(cusp_lon)
    sigs = get_planet_house_significations(sl, ls, {pn: (plon, 0) for pn, (plon, pspd) in planet_data.items() if pn not in ["Rahu","Ketu"]}, r_lon, k_lon)
    score = 50
    req_match = len(sigs & required_houses)
    deny_match = len(sigs & deny_houses)
    score += (req_match * 15)
    score -= (deny_match * 15)
    return max(0, min(100, score))

def _get_p_str(p, planet_data, ls, f, lagna_lon, jd_ut):
    if not p or p not in planet_data: return 50
    plon, pspd = planet_data[p]
    rupas = calculate_shadbala(p, plon, pspd, lagna_lon, ls, f, planet_data, jd_ut)
    return _clamp(50 + (rupas - 6.0) * 12.5)

def calculate_wealth_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    
    al_house = f.get("arudha_lagna", {}).get("house")
    indu_sign = f.get("indu_lagna", {}).get("sign")
    indu_bonus = 0
    if indu_sign:
        indu_occ_str = sum(5 for p in f["planets"] if f["planets"][p].get("sign") == indu_sign and p in _NATURAL_BENEFICS)
        indu_occ_str -= sum(5 for p in f["planets"] if f["planets"][p].get("sign") == indu_sign and p in _NATURAL_MALEFICS)
        if indu_occ_str > 0: indu_bonus = indu_occ_str + 10
        elif indu_occ_str < 0: indu_bonus = indu_occ_str - 10
        
    al11_score = 0
    if al_house:
        al11_house = ((al_house + 10 - 1) % 12) + 1
        al11_score = _get_bhava_bala(al11_house, ls, planet_data, f, lagna_lon, jd_ut)
        
    structural = _score_positive([(_get_bhava_bala(2, ls, planet_data, f, lagna_lon, jd_ut), 2.4), (_get_bhava_bala(11, ls, planet_data, f, lagna_lon, jd_ut), 2.4), (_get_bhava_bala(5, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_get_bhava_bala(9, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut), 0.5), (al11_score, 1.2), (_sav_norm(f["sav"].get(2)), 1.2), (_sav_norm(f["sav"].get(11)), 1.2)])
    karaka = _score_positive([(_get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut), 1.5), (_get_p_str("Venus", planet_data, ls, f, lagna_lon, jd_ut), 1.0), (_get_p_str("Mercury", planet_data, ls, f, lagna_lon, jd_ut), 0.8), (_varga_sign_strength(f, "D2", "Jupiter"), 0.9), (_varga_sign_strength(f, "D2", "Venus"), 0.7), (_varga_sign_strength(f, "D9", "Jupiter"), 0.5)])
    kp = _score_positive([(_get_kp_sub_lord_score(2, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,11}, {6,8,12}), 1.4), (_get_kp_sub_lord_score(11, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,11}, {6,8,12}), 1.0)])
    yoga = _topic_yoga_score(f, {"Dhana Yoga": 7, "Lakshmi Yoga": 8, "Chandra-Mangala Yoga": 5, "Akhand Samrajya Yoga": 9, "Raja Yoga": 4, "Parivartana Yoga": 3, "Viparita Raja Yoga": 2}, planet_data, ls, lagna_lon, jd_ut)
    placement = _topic_house_connection(f, ["Jupiter", "Venus", "Mercury", "Moon", "Mars"], {2, 5, 9, 11})
    
    h2_lon, h11_lon = ((ls + 1) * 30 + 15) % 360, ((ls + 10) * 30 + 15) % 360
    malefic_drishti = sum((_calc_drishti(planet_data[m][0], h2_lon, m) + _calc_drishti(planet_data[m][0], h11_lon, m)) * 0.05 for m in ["Saturn", "Mars", "Rahu", "Ketu", "Sun"])
    drains = _affliction_count(f, houses={2, 11}) * 3 + malefic_drishti
    if _planet_house(f, "Rahu") in {2, 11} and _get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut) < 55: drains += 5
    return round(_clamp(structural * 0.40 + karaka * 0.22 + kp * 0.18 + yoga + placement + indu_bonus - drains), 2)

def calculate_relationship_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    dk = f["karakas"].get("Darakaraka")
    
    structural = _score_positive([(_get_bhava_bala(7, ls, planet_data, f, lagna_lon, jd_ut), 2.5), (_get_bhava_bala(2, ls, planet_data, f, lagna_lon, jd_ut), 1.2), (_get_bhava_bala(4, ls, planet_data, f, lagna_lon, jd_ut), 1.0), (_get_bhava_bala(5, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_get_bhava_bala(8, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_sav_norm(f["sav"].get(7)), 1.2)])
    karaka = _score_positive([(_get_p_str("Venus", planet_data, ls, f, lagna_lon, jd_ut), 1.8), (_get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut), 1.1), (_get_p_str("Moon", planet_data, ls, f, lagna_lon, jd_ut), 1.1), (_get_p_str(dk, planet_data, ls, f, lagna_lon, jd_ut), 1.0), (_varga_sign_strength(f, "D9", "Venus"), 1.2), (_varga_sign_strength(f, "D9", "Jupiter"), 0.8), (_varga_sign_strength(f, "D9", dk), 0.9)])
    kp = _get_kp_sub_lord_score(7, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,7,11}, {1,6,10})
    yoga = _topic_yoga_score(f, {"Malavya Yoga": 7, "Gajakesari Yoga": 5, "Raja Yoga": 2}, planet_data, ls, lagna_lon, jd_ut)
    
    h7_lon = ((ls + 6) * 30 + 15) % 360
    malefic_drishti = sum(_calc_drishti(planet_data[m][0], h7_lon, m) * 0.05 for m in ["Saturn", "Mars", "Rahu", "Ketu", "Sun"])
    risk = _affliction_count(f, planets={"Venus", "Jupiter", "Moon", dk} - {None}) * 4 + malefic_drishti
    if "HIGH MANGLIK" in f["manglik"]: risk += 8
    elif "MILD MANGLIK" in f["manglik"]: risk += 4
    if _planet_house(f, "Rahu") == 7 or _planet_house(f, "Ketu") == 7: risk += 7
    return round(_clamp(structural * 0.38 + karaka * 0.30 + (kp/100)*22 + yoga - risk), 2)

def calculate_career_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    amk = f["karakas"].get("Amatyakaraka")
    al_house = f.get("arudha_lagna", {}).get("house")
    al10_score = 0
    if al_house:
        al10_house = ((al_house + 9 - 1) % 12) + 1
        al10_score = _get_bhava_bala(al10_house, ls, planet_data, f, lagna_lon, jd_ut)
        
    h7_bala = _get_bhava_bala(7, ls, planet_data, f, lagna_lon, jd_ut)
    h6_weight = 0.5 if h7_bala > _get_bhava_bala(6, ls, planet_data, f, lagna_lon, jd_ut) else 1.1
    structural = _score_positive([(_get_bhava_bala(10, ls, planet_data, f, lagna_lon, jd_ut), 2.7), (_get_bhava_bala(6, ls, planet_data, f, lagna_lon, jd_ut), h6_weight), (_get_bhava_bala(11, ls, planet_data, f, lagna_lon, jd_ut), 1.4), (_get_bhava_bala(2, ls, planet_data, f, lagna_lon, jd_ut), 0.8), (_get_bhava_bala(9, ls, planet_data, f, lagna_lon, jd_ut), 0.8), (_get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut), 0.5), (al10_score, 1.5), (_sav_norm(f["sav"].get(10)), 1.2), (_sav_norm(f["sav"].get(6)), 0.8)])
    karaka = _score_positive([(_get_p_str("Sun", planet_data, ls, f, lagna_lon, jd_ut), 1.2), (_get_p_str("Saturn", planet_data, ls, f, lagna_lon, jd_ut), 1.3), (_get_p_str("Mercury", planet_data, ls, f, lagna_lon, jd_ut), 1.0), (_get_p_str("Mars", planet_data, ls, f, lagna_lon, jd_ut), 0.8), (_get_p_str(amk, planet_data, ls, f, lagna_lon, jd_ut), 1.6), (_varga_sign_strength(f, "D10", amk), 1.5), (_varga_sign_strength(f, "D10", "Sun"), 0.8), (_varga_sign_strength(f, "D10", "Saturn"), 0.8)])
    kp = _score_positive([(_get_kp_sub_lord_score(10, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,6,10,11}, {5,8,12}), 1.7), (_get_kp_sub_lord_score(6, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,6,10,11}, {5,8,12}), 0.8)])
    yoga = _topic_yoga_score(f, {"Dharma-Karma Adhipati Yoga": 10, "Raja Yoga": 7, "Ruchaka Yoga": 6, "Shasha Yoga": 6, "Bhadra Yoga": 5, "Hamsa Yoga": 3, "Neecha Bhanga Raja Yoga": 5, "Viparita Raja Yoga": 3}, planet_data, ls, lagna_lon, jd_ut)
    placement = _topic_house_connection(f, ["Sun", "Saturn", "Mercury", "Mars", amk], {1, 6, 10, 11})
    risk = _affliction_count(f, planets={"Sun", "Saturn", "Mercury", "Mars", amk} - {None}, houses={1, 6, 10, 11}) * 4
    return round(_clamp(structural * 0.40 + karaka * 0.30 + kp * 0.20 + yoga + placement - risk), 2)

def calculate_struggles_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    burden = 18
    burden += (100 - _get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut)) * 0.12
    burden += (100 - _get_bhava_bala(4, ls, planet_data, f, lagna_lon, jd_ut)) * 0.07
    burden += _affliction_count(f, houses={8}) * 3
    burden += _get_bhava_bala(12, ls, planet_data, f, lagna_lon, jd_ut) * 0.10
    burden += max(0, _get_bhava_bala(6, ls, planet_data, f, lagna_lon, jd_ut) - 62) * 0.04
    
    graha_yuddha_count = sum(1 for p in f["planets"].values() if p.get("war") == "LOSER")
    burden += graha_yuddha_count * 5
    
    malefic_drishti = 0
    for h_idx in [1, 4, 7, 8, 10, 12]:
        h_lon = ((ls + h_idx - 1) * 30 + 15) % 360
        malefic_drishti += sum(_calc_drishti(planet_data[m][0], h_lon, m) * 0.03 for m in ["Saturn", "Mars", "Rahu", "Ketu"])
    
    burden += malefic_drishti
    burden += _affliction_count(f, houses={1, 4, 7, 8, 10, 12}) * 3
    if "Kemadruma Yoga (Negative)" in f["yogas"]: burden += 8
    if "Viparita Raja Yoga" in f["yogas"]: burden -= 6
    if "Gajakesari Yoga" in f["yogas"]: burden -= 4
    if f["neecha_bhanga"]: burden -= min(6, len(f["neecha_bhanga"]) * 3)
    return round(_clamp(burden), 2)

def calculate_health_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    lagna_lord = f["house_lords"].get(1, {}).get("planet")
    structural = _score_positive([(_get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut), 2.6), (_get_bhava_bala(8, ls, planet_data, f, lagna_lon, jd_ut), 1.5), (_get_bhava_bala(3, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_get_bhava_bala(6, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_sav_norm(f["sav"].get(1)), 1.0)])
    karaka = _score_positive([(_get_p_str(lagna_lord, planet_data, ls, f, lagna_lon, jd_ut), 1.8), (_get_p_str("Sun", planet_data, ls, f, lagna_lon, jd_ut), 1.1), (_get_p_str("Moon", planet_data, ls, f, lagna_lon, jd_ut), 1.2), (_get_p_str("Saturn", planet_data, ls, f, lagna_lon, jd_ut), 1.1), (_varga_sign_strength(f, "D9", lagna_lord), 0.8), (_varga_sign_strength(f, "D12", lagna_lord), 0.5)])
    kp = _score_positive([(_get_kp_sub_lord_score(1, placidus_cusps, planet_data, r_lon, k_lon, ls, {1,11}, {2,7}), 1.1), (100 - _get_kp_sub_lord_score(6, placidus_cusps, planet_data, r_lon, k_lon, ls, {1,11}, {2,7}) + 40, 0.7), (_get_kp_sub_lord_score(8, placidus_cusps, planet_data, r_lon, k_lon, ls, {1,11}, {2,7}), 0.7)])
    protection = _benefic_support(f, {1, 6, 8}) + _topic_yoga_score(f, {"Hamsa Yoga": 5, "Gajakesari Yoga": 5, "Adhi Yoga": 3}, planet_data, ls, lagna_lon, jd_ut)
    risk = _affliction_count(f, planets={lagna_lord, "Sun", "Moon", "Saturn"} - {None}) * 5 + len(f["weak_sav_houses"] & {1, 6, 8}) * 4
    return round(_clamp(structural * 0.40 + karaka * 0.30 + kp * 0.16 + protection - risk), 2)

def calculate_happiness_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    structural = _score_positive([(_get_bhava_bala(4, ls, planet_data, f, lagna_lon, jd_ut), 2.4), (_get_bhava_bala(5, ls, planet_data, f, lagna_lon, jd_ut), 1.3), (_get_bhava_bala(9, ls, planet_data, f, lagna_lon, jd_ut), 1.0), (_get_bhava_bala(11, ls, planet_data, f, lagna_lon, jd_ut), 0.8), (_get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut), 0.6), (_sav_norm(f["sav"].get(4)), 1.0)])
    karaka = _score_positive([(_get_p_str("Moon", planet_data, ls, f, lagna_lon, jd_ut), 1.8), (_get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut), 1.3), (_get_p_str("Venus", planet_data, ls, f, lagna_lon, jd_ut), 1.0), (_varga_sign_strength(f, "D9", "Moon"), 0.8)])
    yoga = _topic_yoga_score(f, {"Gajakesari Yoga": 9, "Hamsa Yoga": 6, "Malavya Yoga": 5, "Adhi Yoga": 4}, planet_data, ls, lagna_lon, jd_ut)
    support = _benefic_support(f, {1, 4, 5, 9, 11})
    risk = _affliction_count(f, planets={"Moon", "Venus", "Jupiter"}) * 5
    
    fourth_lord = f["house_lords"].get(4, {}).get("planet")
    if fourth_lord:
        fl_house = _planet_house(f, fourth_lord)
        if fl_house in {1, 4, 5, 9, 10, 11}: support += 8
        elif fl_house in {6, 8, 12}: risk += 8
        
    if "Kemadruma Yoga (Negative)" in f["yogas"]: risk += 10
    return round(_clamp(structural * 0.43 + karaka * 0.32 + yoga + support - risk), 2)

def calculate_luck_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    ninth_lord = f["house_lords"].get(9, {}).get("planet")
    structural = _score_positive([(_get_bhava_bala(9, ls, planet_data, f, lagna_lon, jd_ut), 2.6), (_get_bhava_bala(5, ls, planet_data, f, lagna_lon, jd_ut), 1.7), (_get_bhava_bala(11, ls, planet_data, f, lagna_lon, jd_ut), 1.0), (_get_bhava_bala(1, ls, planet_data, f, lagna_lon, jd_ut), 0.8), (_sav_norm(f["sav"].get(9)), 1.2), (_sav_norm(f["sav"].get(5)), 0.8)])
    karaka = _score_positive([(_get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut), 1.7), (_get_p_str(ninth_lord, planet_data, ls, f, lagna_lon, jd_ut), 1.4), (_varga_sign_strength(f, "D9", "Jupiter"), 1.0), (_varga_sign_strength(f, "D9", ninth_lord), 1.0), (_get_p_str("Sun", planet_data, ls, f, lagna_lon, jd_ut), 0.5)])
    kp = _score_positive([(_get_kp_sub_lord_score(9, placidus_cusps, planet_data, r_lon, k_lon, ls, {9,11}, {6,8,12}), 1.4), (_get_kp_sub_lord_score(11, placidus_cusps, planet_data, r_lon, k_lon, ls, {9,11}, {6,8,12}), 0.8)])
    yoga = _topic_yoga_score(f, {"Lakshmi Yoga": 9, "Gajakesari Yoga": 7, "Hamsa Yoga": 6, "Raja Yoga": 6, "Adhi Yoga": 4}, planet_data, ls, lagna_lon, jd_ut)
    placement = _topic_house_connection(f, ["Jupiter", ninth_lord, "Sun"], {1, 5, 9, 11})
    risk = _affliction_count(f, planets={"Jupiter", ninth_lord} - {None}) * 5
    return round(_clamp(structural * 0.42 + karaka * 0.30 + kp * 0.16 + yoga + placement - risk), 2)

def calculate_spiritual_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    ak = f["karakas"].get("Atmakaraka")
    twelfth_lord = f["house_lords"].get(12, {}).get("planet")
    structural = _score_positive([(_get_bhava_bala(12, ls, planet_data, f, lagna_lon, jd_ut), 2.0), (_get_bhava_bala(9, ls, planet_data, f, lagna_lon, jd_ut), 1.6), (_get_bhava_bala(8, ls, planet_data, f, lagna_lon, jd_ut), 1.3), (_get_bhava_bala(5, ls, planet_data, f, lagna_lon, jd_ut), 0.9), (_get_bhava_bala(4, ls, planet_data, f, lagna_lon, jd_ut), 0.6), (_sav_norm(f["sav"].get(12)), 1.0), (_sav_norm(f["sav"].get(9)), 0.8)])
    karaka = _score_positive([(_get_p_str("Ketu", planet_data, ls, f, lagna_lon, jd_ut), 1.6), (_get_p_str("Jupiter", planet_data, ls, f, lagna_lon, jd_ut), 1.4), (_get_p_str("Saturn", planet_data, ls, f, lagna_lon, jd_ut), 0.9), (_get_p_str(ak, planet_data, ls, f, lagna_lon, jd_ut), 1.2), (_get_p_str(twelfth_lord, planet_data, ls, f, lagna_lon, jd_ut), 1.0), (_varga_sign_strength(f, "D9", ak), 0.8), (_varga_sign_strength(f, "D9", "Jupiter"), 0.8)])
    placement = 0
    for planet, points in {"Ketu": 12, "Jupiter": 8, "Saturn": 5, ak: 7, twelfth_lord: 6}.items():
        if planet and _planet_house(f, planet) in {1, 4, 5, 8, 9, 12}: placement += points
    yoga = _topic_yoga_score(f, {"Hamsa Yoga": 8, "Viparita Raja Yoga": 7, "Gajakesari Yoga": 3}, planet_data, ls, lagna_lon, jd_ut)
    return round(_clamp(structural * 0.38 + karaka * 0.31 + placement + yoga), 2)

def calculate_hidden_pitfalls_score(dossier):
    f = _parse_chart_facts(dossier)
    math_data = _recalc_math(dossier)
    if not math_data: return 50.0
    ls, lagna_lon, planet_data, placidus_cusps, jd_ut, r_lon, k_lon = math_data
    ak = f["karakas"].get("Atmakaraka")
    amk = f["karakas"].get("Amatyakaraka")
    dk = f["karakas"].get("Darakaraka")
    burden = 15
    burden += _get_bhava_bala(8, ls, planet_data, f, lagna_lon, jd_ut) * 0.16 + _get_bhava_bala(12, ls, planet_data, f, lagna_lon, jd_ut) * 0.14 + _get_bhava_bala(6, ls, planet_data, f, lagna_lon, jd_ut) * 0.07
    
    malefic_drishti = 0
    for h_idx in [1, 2, 4, 7, 8, 10, 12]:
        h_lon = ((ls + h_idx - 1) * 30 + 15) % 360
        malefic_drishti += sum(_calc_drishti(planet_data[m][0], h_lon, m) * 0.03 for m in ["Saturn", "Mars", "Rahu", "Ketu"])
    burden += malefic_drishti
    
    burden += _affliction_count(f, planets={ak, amk, dk, "Moon", "Venus", "Jupiter"} - {None}) * 5
    burden += _affliction_count(f, houses={1, 2, 4, 7, 8, 10, 12}) * 3
    for planet in {ak, amk, dk, "Moon", "Venus", "Jupiter", "Saturn"} - {None}:
        if _varga_sign_strength(f, "D9", planet) <= 32: burden += 4
        if _varga_sign_strength(f, "D30", planet) <= 32: burden += 5
    
    if _get_kp_sub_lord_score(2, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,11}, {6,8,12}) < 40: burden += 3
    if _get_kp_sub_lord_score(7, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,7,11}, {1,6,10}) < 40: burden += 3
    if _get_kp_sub_lord_score(10, placidus_cusps, planet_data, r_lon, k_lon, ls, {2,6,10,11}, {5,8,12}) < 40: burden += 3
    
    if _planet_house(f, "Rahu") in {1, 2, 4, 7, 10}: burden += 7
    if _planet_house(f, "Ketu") in {1, 2, 4, 7, 10}: burden += 5
    if f["neecha_bhanga"]: burden -= min(5, len(f["neecha_bhanga"]) * 2)
    if "Gajakesari Yoga" in f["yogas"]: burden -= 3
    return round(_clamp(burden), 2)

def _custom_is_reverse_rank(criteria):
    q = str(criteria).lower()
    return any(w in q for w in ["least", "lowest", "fewest", "less likely", "minimum", "smallest"])

def _custom_is_risk_topic(criteria):
    q = str(criteria).lower()
    return any(w in q for w in [
        "struggle", "pitfall", "problem", "risk", "danger", "accident", "disease",
        "illness", "debt", "loss", "failure", "divorce", "separation", "enemy",
        "litigation", "scandal", "delay", "obstacle", "suffer", "hardship",
    ])

def _custom_topic_profile(criteria):
    q = str(criteria).lower()
    profiles = [
        (["rich", "wealth", "money", "finance", "income", "business", "profit"], "Wealth", [2, 11, 5, 9], ["Jupiter", "Venus", "Mercury"], ["D2", "D9"], [2, 11], {"Dhana Yoga": 7, "Lakshmi Yoga": 8, "Chandra-Mangala Yoga": 5, "Raja Yoga": 4}),
        (["marriage", "relationship", "love", "spouse", "partner", "romance"], "Relationship", [7, 2, 4, 5, 8], ["Venus", "Jupiter", "Moon"], ["D9"], [7], {"Malavya Yoga": 7, "Gajakesari Yoga": 5}),
        (["career", "job", "profession", "promotion", "status", "position"], "Career", [10, 6, 11, 2, 9], ["Sun", "Saturn", "Mercury", "Mars"], ["D10", "D9"], [10, 6, 11], {"Dharma-Karma Adhipati Yoga": 10, "Raja Yoga": 7, "Shasha Yoga": 5, "Bhadra Yoga": 5}),
        (["fame", "famous", "celebrity", "public", "recognition", "popular", "renown"], "Fame", [10, 11, 5, 9, 1], ["Sun", "Moon", "Jupiter", "Rahu"], ["D10", "D9"], [10, 11], {"Raja Yoga": 8, "Dharma-Karma Adhipati Yoga": 8, "Gajakesari Yoga": 5}),
        (["leader", "leadership", "politic", "authority", "power", "influence", "command"], "Leadership", [1, 6, 9, 10, 11], ["Sun", "Mars", "Saturn", "Jupiter"], ["D10"], [10, 11], {"Raja Yoga": 8, "Dharma-Karma Adhipati Yoga": 9, "Ruchaka Yoga": 5, "Shasha Yoga": 5}),
        (["intelligence", "education", "study", "academic", "exam", "learning", "wisdom"], "Learning", [4, 5, 9, 10], ["Mercury", "Jupiter", "Moon"], ["D9"], [5, 9], {"Bhadra Yoga": 6, "Hamsa Yoga": 6, "Gajakesari Yoga": 4}),
        (["creative", "creativity", "art", "music", "writing", "writer", "actor", "artist"], "Creativity", [3, 5, 2, 10, 11], ["Venus", "Mercury", "Moon"], ["D9", "D10"], [3, 5, 10, 11], {"Malavya Yoga": 6, "Bhadra Yoga": 5, "Gajakesari Yoga": 4}),
        (["beauty", "beautiful", "attractive", "charm", "style", "luxury"], "Charm", [1, 2, 4, 5, 7], ["Venus", "Moon", "Jupiter"], ["D9"], [1, 7, 11], {"Malavya Yoga": 8, "Gajakesari Yoga": 4}),
        (["child", "children", "progeny", "fertility"], "Children", [5, 2, 9, 11], ["Jupiter", "Moon", "Sun"], ["D9"], [5], {"Hamsa Yoga": 5, "Gajakesari Yoga": 4}),
        (["property", "home", "house", "land", "vehicle", "comfort"], "Property", [4, 2, 11, 9], ["Moon", "Venus", "Mars"], ["D9"], [4, 11], {"Malavya Yoga": 5, "Gajakesari Yoga": 4}),
        (["foreign", "abroad", "travel", "overseas", "settlement", "visa"], "Foreign", [9, 12, 3, 7], ["Rahu", "Moon", "Jupiter", "Saturn"], ["D9"], [9, 12], {"Raja Yoga": 3}),
        (["spiritual", "moksha", "religion", "guru", "occult", "meditation"], "Spiritual", [12, 9, 8, 5], ["Ketu", "Jupiter", "Saturn"], ["D9"], [12, 9], {"Hamsa Yoga": 8, "Viparita Raja Yoga": 7}),
    ]
    for words, name, houses, planets, vargas, kp_houses, yogas in profiles:
        if any(w in q for w in words):
            return {"name": name, "houses": houses, "planets": planets, "vargas": vargas, "kp": kp_houses, "yogas": yogas}
    return {"name": "General Potential", "houses": [1, 5, 9, 10, 11], "planets": ["Sun", "Moon", "Jupiter", "Mercury"], "vargas": ["D9", "D10"], "kp": [10, 11], "yogas": {"Raja Yoga": 6, "Gajakesari Yoga": 5, "Hamsa Yoga": 4}}

def calculate_custom_aspect_score(dossier, criteria):
    """
    Chart-grounded custom scorer. It maps the user's free-text criterion to the
    closest classical house/karaka/KP cluster and returns strength of that trait.
    Negative topics intentionally return risk intensity; ranking direction is
    handled separately by _custom_is_reverse_rank().
    """
    q = str(criteria).lower()
    if any(w in q for w in ["wealth", "rich", "money", "finance"]) and not _custom_is_risk_topic(criteria):
        return calculate_wealth_score(dossier)
    if any(w in q for w in ["marriage", "relationship", "love", "spouse"]) and not _custom_is_risk_topic(criteria):
        return calculate_relationship_score(dossier)
    if any(w in q for w in ["career", "profession", "job", "promotion"]) and not _custom_is_risk_topic(criteria):
        return calculate_career_score(dossier)
    if any(w in q for w in ["health", "longevity", "constitution"]) and not _custom_is_risk_topic(criteria):
        return calculate_health_score(dossier)
    if any(w in q for w in ["happy", "happiness", "contentment", "fulfilled"]) and not _custom_is_risk_topic(criteria):
        return calculate_happiness_score(dossier)
    if any(w in q for w in ["luck", "fortune", "fortunate"]) and not _custom_is_risk_topic(criteria):
        return calculate_luck_score(dossier)
    if any(w in q for w in ["spiritual", "moksha", "religion", "occult"]):
        return calculate_spiritual_score(dossier)
    if any(w in q for w in ["hidden", "pitfall", "unexpected", "scandal", "secret"]):
        return calculate_hidden_pitfalls_score(dossier)
    if _custom_is_risk_topic(criteria):
        return calculate_struggles_score(dossier)

    f = _parse_chart_facts(dossier)
    spec = _custom_topic_profile(criteria)
    structural_parts = []
    for idx, house in enumerate(spec["houses"]):
        structural_parts.append((_house_score(f, house), max(0.7, 2.0 - idx * 0.25)))
    karaka_parts = [(_planet_strength(f, p), 1.0) for p in spec["planets"]]
    for chart in spec["vargas"]:
        for p in spec["planets"][:3]:
            karaka_parts.append((_varga_sign_strength(f, chart, p), 0.45))
    kp_parts = [(_kp_norm(extract_kp_promise(dossier, h)), 1.0) for h in spec["kp"]]
    yoga = _topic_yoga_score(f, spec["yogas"], planet_data, ls, lagna_lon, jd_ut)
    placement = _topic_house_connection(f, spec["planets"], set(spec["houses"]))
    risk = _affliction_count(f, planets=set(spec["planets"])) * 4
    score = _score_positive(structural_parts) * 0.44 + _score_positive(karaka_parts) * 0.29 + _score_positive(kp_parts) * 0.15 + yoga + placement - risk
    return round(_clamp(score), 2)

def get_prashna_python_verdict(question, dossier_text):
    """
    KP Horary routing: maps question keywords to the correct house,
    then uses the KP Promise verdict from the dossier as the authoritative answer.
    """
    q_lower = question.lower()
    house = 1
    if any(w in q_lower for w in ["job","career","promotion","business","work","profession"]): house = 10
    elif any(w in q_lower for w in ["love","marry","marriage","relationship","partner","wedding","spouse"]): house = 7
    elif any(w in q_lower for w in ["money","wealth","finance","loan","buy","invest","rich","earn"]): house = 2
    elif any(w in q_lower for w in ["health","sick","recover","surgery","disease","hospital","cure"]): house = 6
    elif any(w in q_lower for w in ["child","kid","pregnancy","baby","conceive","son","daughter"]): house = 5
    elif any(w in q_lower for w in ["travel","visa","abroad","foreign","overseas","trip"]): house = 9
    elif any(w in q_lower for w in ["house","property","home","flat","vehicle","car","land"]): house = 4
    elif any(w in q_lower for w in ["court","legal","lawsuit","case","enemy","conflict"]): house = 6
    elif any(w in q_lower for w in ["education","study","degree","exam","course"]): house = 5
    elif any(w in q_lower for w in ["spiritual","moksha","liberation","guru","pilgrimage"]): house = 12

    # First try KP promise verdict from dossier (most accurate)
    kp_score = extract_kp_promise(dossier_text, house)
    if kp_score == 3: return "YES", f"KP H{house} Sub-Lord STRONGLY SIGNIFIES the required houses — event is PROMISED."
    elif kp_score == 2: return "DELAYED / PARTIAL", f"KP H{house} Sub-Lord partially signifies required houses — possible but with delay/conditions."
    elif kp_score == 0: return "NO", f"KP H{house} Sub-Lord does NOT signify required houses — event is DENIED by chart structure."

    # Fallback: use base house score if KP data not in dossier
    score = extract_base_score(dossier_text, house)
    if score == 3: return "YES", f"H{house} is mathematically STRONGLY PROMISED (Base Score 3/3)."
    elif score == 2: return "DELAYED / PARTIAL", f"H{house} is WEAKLY PROMISED (Base Score 2/3) — possible with effort/delay."
    else: return "NO", f"H{house} lacks mathematical promise (Base Score 1/3) — chart structure does not support this event now."


def calculate_and_rank_profiles(profiles_dossiers, criteria):
    scoring_map = {
        "Wealth Potential": (calculate_wealth_score, False),
        "Relationship Quality": (calculate_relationship_score, False),
        "Career Success": (calculate_career_score, False),
        "Life Struggles": (calculate_struggles_score, True),
        "Health & Longevity": (calculate_health_score, False),
        "Happiness & Contentment": (calculate_happiness_score, False),
        "Luck & Fortune": (calculate_luck_score, False),
        "Spiritual Depth": (calculate_spiritual_score, False),
        "Hidden Pitfalls": (calculate_hidden_pitfalls_score, True),
    }

    active = []
    for c in criteria:
        key = _criterion_key(c)
        if key in scoring_map:
            active.append((c, key, scoring_map[key][0], scoring_map[key][1]))
        else:
            active.append((c, c.strip(), lambda dossier, custom=c: calculate_custom_aspect_score(dossier, custom), _custom_is_reverse_rank(c)))

    raw = {name: {} for name, _ in profiles_dossiers}
    for name, dossier in profiles_dossiers:
        for full_label, key, func, is_inverted in active:
            try:
                score = float(func(dossier))
            except Exception:
                score = 50.0
            raw[name][key] = {"score": score, "inverted": is_inverted, "label": full_label}

    ranks = {key: {} for _, key, _, _ in active}
    for _, key, _, is_inverted in active:
        ordered = sorted(profiles_dossiers, key=lambda item: raw[item[0]][key]["score"], reverse=not is_inverted)
        for idx, (name, _) in enumerate(ordered, start=1):
            ranks[key][name] = idx

    composite = {}
    for name, _ in profiles_dossiers:
        parts = []
        for _, key, _, is_inverted in active:
            s = raw[name][key]["score"]
            parts.append(100 - s if is_inverted else s)
        composite[name] = sum(parts) / len(parts) if parts else 50.0
    composite_order = sorted(composite, key=composite.get, reverse=True)
    composite_rank = {name: idx for idx, name in enumerate(composite_order, start=1)}

    header_keys = [key for _, key, _, _ in active]
    out = []
    out.append("### Rankings Table")
    out.append("| Profile | Overall | " + " | ".join(header_keys) + " |")
    out.append("|---|---:|" + "---:|" * len(header_keys))
    for name, _ in sorted(profiles_dossiers, key=lambda item: composite_rank[item[0]]):
        cells = [f"#{composite_rank[name]} ({composite[name]:.1f})"]
        for key in header_keys:
            s = raw[name][key]["score"]
            cells.append(f"#{ranks[key][name]} ({s:.1f})")
        out.append(f"| {name} | " + " | ".join(cells) + " |")

    out.append("\n### Overall Composite Rankings")
    for idx, name in enumerate(composite_order, start=1):
        out.append(f"Rank {idx}: {name} (Composite Baseline: {composite[name]:.1f}/100)")

    out.append("\n### Detailed Parameter Rankings")
    for full_label, key, _, is_inverted in active:
        ordered = sorted(profiles_dossiers, key=lambda item: raw[item[0]][key]["score"], reverse=not is_inverted)
        out.append(f"\nParameter: {full_label}")
        out.append(f"Direction: {'lower burden is better' if is_inverted else 'higher structural promise is better'}")
        for idx, (name, _) in enumerate(ordered, start=1):
            out.append(f"Rank {idx}: {name} (Score: {raw[name][key]['score']:.1f})")
    return "\n".join(out)

GUARDRAILS = """
<UNIVERSAL_INTERPRETATION_PROTOCOL>
You are an expert interpretive engine. When a user asks a follow-up question, you MUST NOT use the "I don't have data" fallback unless the request is for information physically impossible to derive from a birth chart.

1. MANDATE TO INTERPRET:
   - Use the provided 11-house HOUSE STRENGTH SUMMARY, Yogas, and Planetary Positions to synthesize answers for ANY life question.
   - For Relationship/Marriage questions (e.g., "Will it last?", "Will we fight?", "Kids?", "Infidelity?"): Analyze H7 (Spouse), H8 (Bond Longevity), H2 (Family), and Moon/Venus/Mars synastry.
   - For Health/Longevity questions (e.g., "Will I be healthy?", "Risks?"): Analyze H1 (Vitality), H6 (Illness), H8 (Longevity), and the Lagna Lord's condition.
   - For Career/Success questions: Analyze H10 (Status), H11 (Gains), and the Amatyakaraka.

2. VERDICT-DRIVEN RESPONSES:
   - Do not be vague. Use the points and "Base Scores" provided in the data to give a clear astrological leaning (e.g., "Based on the high base score of House 7 and the absence of Kuja Dosha, the structural integrity of this marriage is very high...").
   - If the data shows conflicts (e.g., strong H7 but weak H8), explain that as "External harmony with internal challenges."

3. THE ONLY ALLOWED FALLBACK (Strictly for Missing Math):
   - Use the fallback ONLY if asked for a specific date/time for a future event (e.g., "What day in 2029 will I get married?"). 
   - Fallback: "I can see the structural promise of this event in the current report, but for a high-precision calculation of the exact date and timing, please head to the **Consultation Room** where I can run the heavy dasha-math books for you."
</UNIVERSAL_INTERPRETATION_PROTOCOL>
"""

# ═══════════════════════════════════════════════════════════
# PROMPT BUILDERS (XML tagged)
# ═══════════════════════════════════════════════════════════

def build_agent_parashari_prompt(dossier):
    return f"""{GUARDRAILS}

<ROLE>You are the Parashari Specialist. Parashari astrology excels at CHARACTER, PSYCHOLOGY, LIFE THEMES, and KARMIC PATTERNS. It does NOT pinpoint exact event timing — KP does that.</ROLE>

<PARASHARI_DOMAIN>
Parashari is authoritative for:
1. IDENTITY & PERSONALITY — Lagna lord, sign dispositions, Avastha states, yogas
2. PSYCHOLOGICAL NATURE — Moon sign/nakshatra, Mercury, Atmakaraka soul purpose  
3. RELATIONSHIP NATURE — 7th lord/sign character, Venus for spouse qualities, D9 Navamsa
4. KARMIC THEMES — Rahu/Ketu axis, 12th house, Ketu nakshatra, spiritual purpose
5. LIFE CIRCUMSTANCES — Which houses are strong/weak by virtue of lord dignity + occupants
6. YOGAS — These show the PROMISE of qualities/themes (NOT timing of events)

Parashari CANNOT determine exact event timing — that is KP's domain.
</PARASHARI_DOMAIN>

<mission>
From the dossier below, extract ONLY Parashari findings:
- Lagna and its lord's strength/placement
- Moon's condition (sign, house, nakshatra, Avastha, any Sade Sati note)  
- Key yogas present and what life themes they promise
- Atmakaraka and Darakaraka identity and meaning
- Rahu/Ketu axis and the karmic lesson it indicates
- D9 Navamsa key placements for relationship quality
- Which houses are functionally strong vs weak (from HOUSE STRENGTH SUMMARY)
- Any Neecha Bhanga or Vargottama planets that secretly strengthen the chart

Output as structured bullet points. NO timing predictions — leave that for KP agent.
</mission>

<user_chart_data>{dossier}</user_chart_data>"""

def build_agent_timing_prompt(dossier):
    return f"""{GUARDRAILS}

<ROLE>You are the Vimshottari Dasha Timing Specialist. Parashari Dasha system governs BROAD LIFE THEMES and PERIODS. KP sub-lord confirms IF events manifest within those periods.</ROLE>

<TIMING_DOMAIN>
The Vimshottari Dasha system (Parashari) tells us:
- WHICH LIFE THEMES are activated in each period (MD = broad theme, AD = specific flavor)
- The NATURE of events to expect (based on MD/AD lord house ownership and occupation)
- The BROAD WINDOW when something could happen

Critical rules from the dossier:
1. USE ONLY the pre-computed Antardasha table — NEVER calculate dates independently
2. The MD lord's house ownership and occupation determine the main theme
3. The AD lord refines which specific area of life is activated
4. Sade Sati (Saturn's transit over Moon) adds a layer of emotional testing/transformation
5. For timing precision, note which AD lords are ALSO KP significators of event houses
</TIMING_DOMAIN>

<mission>
From the dossier, extract:
- Current MD period: what life theme does this MD lord activate? (based on its house ownership + occupation)
- Current AD period: what specific area does the AD lord bring? (its houses)
- Next 2-3 upcoming AD periods and what they promise based on those planets' significations
- Sade Sati status and its current phase impact
- Any upcoming MD changes in the next 5 years and what the transition means
- Cross-reference: which upcoming Dasha periods also have their lords signifying marriage (2-7-11), career (6-10-11), or other key events from the KP PROMISE section

Output as structured bullet points with approximate date ranges (from the pre-computed table only).
</mission>

<user_chart_data>{dossier}</user_chart_data>"""

def build_agent_kp_prompt(dossier):
    return f"""{GUARDRAILS}

<ROLE>You are the KP Specialist. KP astrology's supreme strength is answering IF an event is promised and WHEN it will manifest. Parashari shows life themes; KP confirms event occurrence.</ROLE>

<KP_DOMAIN>
KP is authoritative for:
1. EVENT PROMISE — Sub-Lord of each cusp signifying required houses = event is promised
   - Marriage: H7 SL must signify 2-7-11 (promised) or 1-6-10 (denied/delayed)  
   - Career service: H10 SL must signify 6-10-11
   - Children: H5 SL must signify 2-5-11
   - Property: H4 SL must signify 4-11
   - Foreign: H9/H12 SL must signify 9-12

2. EVENT TIMING — Dasha lord AND Antardasha lord BOTH signifying the event houses
   → The event triggers when the TRANSIT also passes through the sub of a significator

3. KP 4-STEP for each planet — what events that planet will trigger in its Dasha period
   (L1 = NL's house occupied, L2 = planet's house, L3 = NL's house owned, L4 = planet's house owned)

4. CUSP SUB-LORDS — The SL of each cusp is the FINAL AUTHORITY on that house's results
   A planet may be the lord of a house but if in a negative sub, it denies results.

KP CRITICAL RULES:
- Do NOT mix Parashari house lordship rules with KP sub-lord rules
- The cusp SL verdict OVERRIDES sign lord indications for event prediction
- Nodes (Rahu/Ketu) act as agents of their star lord — check star lord's significations
</KP_DOMAIN>

<mission>
From the KP EVENT PROMISE ANALYSIS section in the dossier, extract and interpret:
1. H7 promise verdict — Is marriage promised? What do the significators say?
2. H10/H6 promise verdict — Is career/service promised? Business or service?
3. H5 promise verdict — Are children promised?
4. H4 promise verdict — Property acquisition promised?
5. H2 promise verdict — Wealth accumulation or financial struggle?
6. Marriage Timing: are current MD/AD lords among the marriage significators (2-7-11)?
7. Career Timing: are current MD/AD lords among the career significators (6-10-11)?
8. For each planet: read its KP 4-Step and state exactly which houses it signifies — this determines what events manifest in its Dasha period

Output as structured findings. Mark each as PROMISED / PARTIALLY PROMISED / DENIED / DELAYED.
</mission>

<user_chart_data>{dossier}</user_chart_data>"""

def build_master_synthesizer_prompt(dossier, p_notes, t_notes, k_notes):
    return f"""{GUARDRAILS}

<ROLE>You are the Master Astrologer integrating Parashari character analysis with KP event prediction. The two systems are COMPLEMENTARY — use both, never confuse their roles.</ROLE>

<SYNTHESIS_RULES>
CRITICAL PROTOCOL — follow this exactly:

1. PARASHARI for PERSONALITY & THEMES: Use Parashari agent notes for describing WHO this person is — their character, psychology, life themes, karmic patterns, spiritual purpose.

2. KP for EVENT DECISIONS: Use KP agent notes for definitively answering WILL this happen? and WHEN? The KP Promise verdicts (PROMISED/DENIED) are FINAL — do not override them with Parashari interpretation.

3. DASHA for TIMING WINDOWS: Use the Timing agent notes for broad timing windows. KP confirms which Dasha periods are truly active for which events.

4. SYNTHESIS RULE: When Parashari and KP appear to conflict, explain both and let the KP verdict be the practical answer. Example: "Parashari shows a powerful 7th house suggesting marriage, and KP confirms this — the H7 Sub-Lord signifies 2-7-11, so marriage is genuinely promised. The current [AD] period and [upcoming AD] are the active windows."

5. MATH LOCK: Every number, date, degree, and nakshatra names, house numbers come ONLY from the dossier. Never calculate, never invent.
</SYNTHESIS_RULES>

<specialist_notes>
PARASHARI ANALYSIS (Character & Life Themes):
{p_notes}

DASHA TIMING ANALYSIS (When & Which Period):  
{t_notes}

KP EVENT PROMISE ANALYSIS (IF & WHEN Events Manifest):
{k_notes}
</specialist_notes>

<mission>
Write a flowing, warm, professional reading covering:
1. Core Identity (Parashari: Lagna + yogas → who they fundamentally are)
2. Mind & Emotional World (Parashari: Moon + Sade Sati if active)
3. Career & Profession (Parashari: nature/field | KP: H10 promise + timing window)
4. Wealth & Finance (Parashari: 2H+11H themes | KP: H2 promise verdict)
5. Relationships & Marriage (Parashari: 7H lord/D9 spouse nature | KP: H7 promise + marriage timing)
6. Health & Vitality (Parashari: 1H/6H/8H constitution | KP: H6 cusp verdict for specific issues)
7. Spiritual Path & Karma (Parashari: Atmakaraka + Ketu + 12H | no KP needed here)
8. Current Life Period (Dasha timing + KP confirmation of active houses)
9. Practical Guidance (remedies only for genuinely afflicted planets — debilitated without Neecha Bhanga, combust, Graha Yuddha losers)
</mission>

<user_chart_data>{dossier}</user_chart_data>"""

def build_deep_analysis_prompt(dossier):
    return f"""{GUARDRAILS}

<SYSTEM>
You have two systems to use — each for what it does best:

PARASHARI handles: Who this person IS (character, psychology, life themes, karmic purpose, spiritual path, relationship nature, family patterns). Uses yogas, house lords, dignities, Atmakaraka, D9/D10 divisional charts.

KP handles: IF events will HAPPEN and WHEN (marriage promised or denied, career service vs business, property acquisition, children). Uses the KP EVENT PROMISE ANALYSIS section which Python pre-computed. The PROMISED/DENIED verdicts are final — do not override them.

DASHA handles: BROAD TIMING WINDOWS — which life themes are activated in each period.

NEVER mix these roles. Never use Parashari to answer "when will I marry" — that is KP's answer.
NEVER use KP sub-lords to describe personality — that is Parashari's answer.
</SYSTEM>

<MATH_LOCK>
- All degrees, dates, nakshatra names, house numbers come ONLY from the dossier
- The KP EVENT PROMISE ANALYSIS verdicts are Python-computed — cite them as-is
- The ANTARDASHA TABLE dates are exact — never calculate differently
- Bhava Chalit shifts: if a planet shifted houses, interpret it in its SHIFTED house
- Vargottama/D9-Exalted planets carry extra strength — mention this
</MATH_LOCK>

<mission>
Write a complete, professional life reading structured as follows:

## 1. Core Identity & Lagna (PARASHARI)
   Use: Ascendant sign + Lagna Lord chain (sign, house, nakshatra, dignity, Avastha)
   Add: Atmakaraka identity — the soul's core lesson and drive
   Add: Key yogas present — what qualities/themes they bestow (NOT when they manifest)
   
## 2. Mind, Emotions & Mental World (PARASHARI)  
   Use: Moon (sign, house, nakshatra, Avastha) + Mercury for intellect
   Add: Sade Sati phase if active — the current emotional/transformational period
   Add: Ketu's house — the soul's past-life comfort zone and detachment area

## 3. Career & Profession (PARASHARI for nature | KP for promise)
   Parashari: 10th lord, D10 Dasamsa, Amatyakaraka — WHAT field/nature of work
   KP: Read the H10 KP Promise verdict from the dossier — cite it exactly
   KP: Check if current MD/AD lords signify 6-10-11 (active career period?)
   Combine: "Your chart shows [Parashari nature] and KP confirms [H10 verdict]"

## 4. Wealth & Finances (PARASHARI for themes | KP for promise)
   Parashari: H2 and H11 lords, Dhana yogas, D2 Hora
   KP: Read H2 KP Promise verdict — cite exactly
   Combine: Timeline of wealth activation using Dasha + KP confirmation

## 5. Relationships & Marriage (PARASHARI for spouse nature | KP for event promise)
   Parashari: H7 lord/sign, Venus/Jupiter condition, D9 Navamsa H7 — describes SPOUSE QUALITIES
   KP: Read H7 KP Promise verdict — is marriage PROMISED or DENIED? Cite exactly
   KP: Marriage Timing Clues — which Dasha periods are active for marriage?
   NOTE: This is where Parashari + KP integration is most powerful. Use both fully.

## 6. Health & Vitality (PARASHARI for constitution | KP for specific vulnerabilities)
   Parashari: Lagna lord strength, H6 lord, H8 lord, any afflictions to H1
   KP: Read H6 KP Promise verdict — what health patterns does this indicate?

## 7. Spiritual Path, Karma & Higher Purpose (PARASHARI only)
   Use: Atmakaraka (soul's mission), Rahu/Ketu axis (karmic direction), H9 + H12 lords
   No KP needed here — spiritual life is Parashari's domain

## 8. Current Life Period & Near Future (DASHA + KP)
   Use: Current MD/AD/PD from the dossier (exact dates from table — cite them)
   What does the MD lord's house ownership/occupation activate?
   What does the AD lord add or restrict?
   KP check: does the current AD lord signify the event houses? Active or inactive window?

## 9. Remedies (ONLY for genuine afflictions)
   ONLY recommend remedies for: debilitated planets WITHOUT Neecha Bhanga, combust planets, Graha Yuddha losers
   Keep practical: gemstones, mantras, lifestyle suggestions
   Do NOT recommend remedies for every planet
</mission>

<user_chart_data>
{dossier}
</user_chart_data>"""

def calculate_matchmaking_synastry(prof_a, prof_b, ma, mb, jda, jdb, dos_a, dos_b):
    koota_data = calculate_ashta_koota(ma, mb)
    marital_a = calculate_marital_analysis(jda, prof_a['lat'], prof_a['lon'])
    marital_b = calculate_marital_analysis(jdb, prof_b['lat'], prof_b['lon'])
    
    # Extract KP H7 Promise
    kp_a = extract_kp_promise(dos_a, 7)
    kp_b = extract_kp_promise(dos_b, 7)
    
    return koota_data, marital_a, marital_b, kp_a, kp_b

def build_matchmaking_prompt(dos_a, dos_b, koota, canc, prof_a, prof_b, marital_a, marital_b, kp_a, kp_b):
    kp_labels = {3: "STRONGLY PROMISED", 2: "PARTIALLY PROMISED", 1: "UNCLEAR", 0: "DENIED"}
    return f"""{GUARDRAILS}

<SYSTEM>
Compatibility analysis now uses an advanced multi-layered Vedic engine incorporating Ashtakoot, Upapada Lagna (UL), Navamsha (D9), Gender-specific rules, and KP Event Promise.

MATH LOCK: Use only pre-computed Python data. Do not recalculate scores or verdicts. Do NOT hallucinate partner traits.
</SYSTEM>

<PYTHON_COMPUTED_DATA>
GENDER SPECIFICS:
Person 1 ({prof_a['name']}): {prof_a.get('gender', 'M')}
Person 2 ({prof_b['name']}): {prof_b.get('gender', 'M')}

KP MARRIAGE PROMISE (Is marriage mathematically supported?):
Person 1: {kp_labels.get(kp_a, "UNCLEAR")} (Score: {kp_a}/3)
Person 2: {kp_labels.get(kp_b, "UNCLEAR")} (Score: {kp_b}/3)

ASHTA KOOTA SCORE: {koota['score']}/36
Varna:{koota['varna']} | Vashya:{koota['vashya']} | Tara:{koota['tara']} | Yoni:{koota['yoni']} | Maitri:{koota['maitri']} | Gana:{koota['gana']} | Bhakoot:{koota['bhakoot']} | Nadi:{koota['nadi']}
Notes: {koota['nadi_note']}
Stree-Deergha: {koota['stree_deergha']} | Mahendra Koota: {koota['mahendra']}
Manglik Status: {canc}

MARITAL ANALYSIS (D9 & UPAPADA LAGNA):
Person 1: 
- D9 7th House (Partner's Nature & Looks): {marital_a['D9_7th_Sign']} (Lord: {marital_a['D9_7th_Lord']})
- Upapada Lagna (Reality of Marriage): {marital_a['UL_Sign']}
- Darapada A7 (Desires): {marital_a['A7_Sign']}

Person 2:
- D9 7th House (Partner's Nature & Looks): {marital_b['D9_7th_Sign']} (Lord: {marital_b['D9_7th_Lord']})
- Upapada Lagna (Reality of Marriage): {marital_b['UL_Sign']}
- Darapada A7 (Desires): {marital_b['A7_Sign']}


</PYTHON_COMPUTED_DATA>

<mission>
Write a deeply insightful, empathetic compatibility reading. 
Use markdown heavily for beautiful formatting. Be extremely detailed about the factors that matter.

### 1. The Ashtakoota (36 Gunas) Deep Dive
Break down their score of {koota['score']}/36 in extreme detail. Elaborate on what each of the 8 Kootas means for them specifically based on their individual scores:
- **Varna (Work & Spiritual Compatibility):** {koota['varna']}/1 
- **Vashya (Dominance & Magnetic Attraction):** {koota['vashya']}/2
- **Tara (Destiny & Auspiciousness):** {koota['tara']}/3
- **Yoni (Intimacy & Physical Compatibility):** {koota['yoni']}/4
- **Graha Maitri (Mental & Psychological Friendship):** {koota['maitri']}/5
- **Gana (Temperament & Life Approach):** {koota['gana']}/6
- **Bhakoot (Emotional Flow & Prosperity):** {koota['bhakoot']}/7
- **Nadi (Genetic & Spiritual Lifeforce):** {koota['nadi']}/8
Discuss what their specific score in each category reveals about their day-to-day life. Also explain the impact of Stree-Deergha ({koota['stree_deergha']}) and Mahendra Koota ({koota['mahendra']}).
*Crucial framing: Emphasize that while Gunas show deep personality and psychological similarity, they do NOT dictate if a wedding will happen, as people can choose to marry regardless of this score.*

### 2. Doshas & Frictions
Discuss their Nadi or Bhakoot doshas (if any) and if they cancel out (check the notes: {koota['nadi_note']}). Discuss the Manglik status ({canc}). 

### 3. Destiny Match & The KP Promise (The True Confirmations)
- **KP Promise**: Discuss if their individual charts actually promise marriage ({kp_labels.get(kp_a, "UNCLEAR")} vs {kp_labels.get(kp_b, "UNCLEAR")}). This is the true cosmic confirmation of whether a marriage will manifest.
- **D9 Cross-Match**: Compare Person 1's D9 7th House traits against Person 2's actual nature, and vice-versa. Describe the *exact* physical looks, appearance, and innate nature each person is destined to attract using the D9 7th Sign and Lord. Does the partner match the destiny?

### 4. Life After Marriage & Sustenance (Upapada Lagna)
Analyze their Upapada Lagnas ({marital_a['UL_Sign']} and {marital_b['UL_Sign']}).
Explain what the reality of their marriage will look like, including familial harmony and stability.

### 5. Final Verdict: What to Do & What to Avoid
Provide the final verdict. List specific, actionable points on "What to Do" and "What to Avoid" *as a couple as a whole* to make this relationship thrive.
Provide a final absolute verdict on whether they are compatible from a traditional Guna perspective.
</mission>

<person_1_chart>{dos_a}</person_1_chart>
<person_2_chart>{dos_b}</person_2_chart>"""






def calculate_destiny_confirmation(prof_a, prof_b, jda, jdb, dos_a, dos_b):
    pla = {pn: get_planet_longitude_and_speed(jda, pid) for pn, pid in PLANETS.items()}
    ra_a, _ = get_planet_longitude_and_speed(jda, swe.MEAN_NODE); pla["Rahu"] = (ra_a, 0); pla["Ketu"] = ((ra_a + 180) % 360, 0)
    plb = {pn: get_planet_longitude_and_speed(jdb, pid) for pn, pid in PLANETS.items()}
    ra_b, _ = get_planet_longitude_and_speed(jdb, swe.MEAN_NODE); plb["Rahu"] = (ra_b, 0); plb["Ketu"] = ((ra_b + 180) % 360, 0)
    
    laga = sign_index_from_lon(get_lagna_and_cusps(jda, prof_a['lat'], prof_a['lon'])[0])
    lagb = sign_index_from_lon(get_lagna_and_cusps(jdb, prof_b['lat'], prof_b['lon'])[0])
    
    moona_sidx = sign_index_from_lon(pla["Moon"][0])
    moonb_sidx = sign_index_from_lon(plb["Moon"][0])
    
    laga_lord = SIGN_LORDS_MAP[laga]
    lagb_lord = SIGN_LORDS_MAP[lagb]
    
    def get_dk_ak(pl):
        degs = [(p, lon % 30) for p, (lon, _) in pl.items() if p not in ["Rahu", "Ketu"]]
        degs.sort(key=lambda x: x[1], reverse=True)
        return degs[0][0], degs[-1][0] 
        
    aka, dka = get_dk_ak(pla)
    akb, dkb = get_dk_ak(plb)
    
    marital_a = calculate_marital_analysis(jda, prof_a['lat'], prof_a['lon'])
    marital_b = calculate_marital_analysis(jdb, prof_b['lat'], prof_b['lon'])
    
    kp_a = extract_kp_promise(dos_a, 7)
    kp_b = extract_kp_promise(dos_b, 7)
    
    from datetime import datetime, date
    dt_loc_a = datetime.combine(date.fromisoformat(prof_a['date']) if isinstance(prof_a['date'], str) else prof_a['date'], datetime.strptime(prof_a['time'], "%H:%M").time() if isinstance(prof_a['time'], str) else prof_a['time'])
    dt_loc_b = datetime.combine(date.fromisoformat(prof_b['date']) if isinstance(prof_b['date'], str) else prof_b['date'], datetime.strptime(prof_b['time'], "%H:%M").time() if isinstance(prof_b['time'], str) else prof_b['time'])
    
    d_info_a = build_vimshottari_timeline(dt_loc_a, pla["Moon"][0], datetime.now())
    d_info_b = build_vimshottari_timeline(dt_loc_b, plb["Moon"][0], datetime.now())
    
    def is_friend(p1, p2):
        friends = {
            "Sun": ["Moon", "Mars", "Jupiter"], "Moon": ["Sun", "Mercury"],
            "Mars": ["Sun", "Moon", "Jupiter"], "Mercury": ["Sun", "Venus"],
            "Jupiter": ["Sun", "Moon", "Mars"], "Venus": ["Mercury", "Saturn"],
            "Saturn": ["Mercury", "Venus"]
        }
        return p2 in friends.get(p1, [])

    def score_blueprint(d9_lord, core_lords):
        if d9_lord in core_lords: return 10
        if any(is_friend(d9_lord, cl) for cl in core_lords): return 7
        return 3

    def check_nodal_obsession(rahu_lon_a, ketu_lon_a, core_lons_b):
        ra_sign = sign_index_from_lon(rahu_lon_a)
        ke_sign = sign_index_from_lon(ketu_lon_a)
        for cl in core_lons_b:
            csign = sign_index_from_lon(cl)
            if csign == ra_sign or csign == ke_sign: return True
        return False

    core_b_lons = [plb["Moon"][0], plb["Venus"][0], plb[lagb_lord][0]]
    core_a_lons = [pla["Moon"][0], pla["Venus"][0], pla[laga_lord][0]]
    
    obsession_a_to_b = check_nodal_obsession(pla["Rahu"][0], pla["Ketu"][0], core_b_lons)
    obsession_b_to_a = check_nodal_obsession(plb["Rahu"][0], plb["Ketu"][0], core_a_lons)

    score_promise = (min(kp_a, 3)/3 * 10) + (min(kp_b, 3)/3 * 10)
    
    score_d9_a = score_blueprint(marital_a['D9_7th_Lord'], [lagb_lord, SIGN_LORDS_MAP[moonb_sidx]])
    score_d9_b = score_blueprint(marital_b['D9_7th_Lord'], [laga_lord, SIGN_LORDS_MAP[moona_sidx]])
    
    ul_lord_a = SIGN_LORDS_MAP[SIGNS.index(marital_a['UL_Sign'])]
    ul_lord_b = SIGN_LORDS_MAP[SIGNS.index(marital_b['UL_Sign'])]
    score_ul_a = 5 if ul_lord_a in [lagb_lord, SIGN_LORDS_MAP[moonb_sidx]] else 0
    score_ul_b = 5 if ul_lord_b in [laga_lord, SIGN_LORDS_MAP[moona_sidx]] else 0
    
    score_soul = 0
    if dka in [akb, lagb_lord]: score_soul += 2.5
    if dkb in [aka, laga_lord]: score_soul += 2.5
    
    score_blueprint_total = score_d9_a + score_d9_b + score_ul_a + score_ul_b + score_soul
    
    def check_insertion(lord_a, sign_a, lag_b):
        b_h7_sign = (lag_b + 6) % 12
        if sign_a == b_h7_sign: return True
        return False
        
    a_in_b7 = check_insertion(laga_lord, sign_index_from_lon(pla[laga_lord][0]), lagb)
    b_in_a7 = check_insertion(lagb_lord, sign_index_from_lon(plb[lagb_lord][0]), laga)
    
    score_synastry = 0
    if a_in_b7: score_synastry += 7.5
    if b_in_a7: score_synastry += 7.5
    if obsession_a_to_b: score_synastry += 5
    if obsession_b_to_a: score_synastry += 5

    def extract_h7_sig(dossier):
        sigs = set()
        if "KP PLANETARY SIGNIFICATORS" in dossier:
            try:
                lines = dossier.split("KP PLANETARY SIGNIFICATORS")[1].split("=")[0].split("\\n")
                for line in lines:
                    if "7" in line:
                        p = line.split(":")[0].strip()
                        if p in PLANETS: sigs.add(p)
            except: pass
        return sigs

    sigs_a = extract_h7_sig(dos_a)
    sigs_b = extract_h7_sig(dos_b)
    shared_sigs = sigs_a.intersection(sigs_b)
    
    score_timing = 0
    if len(shared_sigs) >= 2: score_timing = 20
    elif len(shared_sigs) == 1: score_timing = 10

    total_destiny_percentage = round(score_promise + score_blueprint_total + score_synastry + score_timing)

    return {
        "A": {"kp_promise": kp_a, "weak_warning": kp_a == 0, "sigs": list(sigs_a)},
        "B": {"kp_promise": kp_b, "weak_warning": kp_b == 0, "sigs": list(sigs_b)},
        "Blueprint": {
            "A_D9_7th_Lord": marital_a['D9_7th_Lord'],
            "B_Core": [lagb_lord, SIGN_LORDS_MAP[moonb_sidx]],
            "B_D9_7th_Lord": marital_b['D9_7th_Lord'],
            "A_Core": [laga_lord, SIGN_LORDS_MAP[moona_sidx]],
            "A_UL": marital_a['UL_Sign'],
            "B_UL": marital_b['UL_Sign'],
            "A_DK": dka, "A_AK": aka,
            "B_DK": dkb, "B_AK": akb
        },
        "Synastry": {
            "A_Lagna_in_B_7th": a_in_b7,
            "B_Lagna_in_A_7th": b_in_a7,
            "A_Nodal_Obsession": obsession_a_to_b,
            "B_Nodal_Obsession": obsession_b_to_a
        },
        "Timing": {
            "A_Current_MD_AD": f"{d_info_a['current_md']} / {d_info_a['current_ad']}",
            "B_Current_MD_AD": f"{d_info_b['current_md']} / {d_info_b['current_ad']}",
            "Shared_Significators": list(shared_sigs)
        },
        "Percentage": total_destiny_percentage
    }

def build_destiny_confirmation_prompt(prof_a, prof_b, dos_a, dos_b, dest_data):
    return f"""{GUARDRAILS}

<SYSTEM>
You are an elite Vedic Destiny Matchmaker analyzing the profound **Signal Correlation and Mutual Spouse Confirmation**.
Does Person A's chart mathematically describe Person B as their destined spouse, and vice versa?

MATH LOCK: Rely exclusively on the Python-computed matrix below. Do NOT recalculate planetary degrees or structural insertions.
</SYSTEM>

<PYTHON_COMPUTED_DESTINY_MATRIX>
PERSON A: {prof_a['name']}
PERSON B: {prof_b['name']}

FINAL DESTINY CONFIRMATION SCORE: {dest_data['Percentage']}%

### CATEGORY A: Foundational Promise (Is marriage internally permitted?)
Person A KP Promise Score: {dest_data['A']['kp_promise']}/3 (Weak Warning: {dest_data['A']['weak_warning']})
Person B KP Promise Score: {dest_data['B']['kp_promise']}/3 (Weak Warning: {dest_data['B']['weak_warning']})

### CATEGORY B: Mutual Spouse Description (The Blueprint Match)
1. D9 Blueprint:
- Person A's Destined Spouse (D9 7th Lord): {dest_data['Blueprint']['A_D9_7th_Lord']} | Person B's Actual Core (Lagna/Moon Lords): {', '.join(dest_data['Blueprint']['B_Core'])}
- Person B's Destined Spouse (D9 7th Lord): {dest_data['Blueprint']['B_D9_7th_Lord']} | Person A's Actual Core: {', '.join(dest_data['Blueprint']['A_Core'])}

2. Manifestation Match (Upapada Lagna):
- Person A's UL Sign: {dest_data['Blueprint']['A_UL']}
- Person B's UL Sign: {dest_data['Blueprint']['B_UL']}

3. The Soul Tie (Jaimini Karakas):
- Person A's Soul (AK): {dest_data['Blueprint']['A_AK']} | Person A's Spouse Soul (DK): {dest_data['Blueprint']['A_DK']}
- Person B's Soul (AK): {dest_data['Blueprint']['B_AK']} | Person B's Spouse Soul (DK): {dest_data['Blueprint']['B_DK']}

### CATEGORY C: Structural Synastry (Architectural Cross-Links)
- Person A's Lagna physically falls into Person B's 7th House: {dest_data['Synastry']['A_Lagna_in_B_7th']}
- Person B's Lagna physically falls into Person A's 7th House: {dest_data['Synastry']['B_Lagna_in_A_7th']}
- Nodal Karmic Obsession (Rahu/Ketu hitting Lagna/Moon/Venus): A on B ({dest_data['Synastry']['A_Nodal_Obsession']}), B on A ({dest_data['Synastry']['B_Nodal_Obsession']})

### CATEGORY D: Timing Synchronization (The Reality Lock)
- Person A's Active Calendar Dasha: {dest_data['Timing']['A_Current_MD_AD']}
- Person B's Active Calendar Dasha: {dest_data['Timing']['B_Current_MD_AD']}
- Shared Marriage Timing Significators (Planets that will trigger marriage for both simultaneously): {', '.join(dest_data['Timing']['Shared_Significators']) if dest_data['Timing']['Shared_Significators'] else "None (Timing may misalign)"}
</PYTHON_COMPUTED_DESTINY_MATRIX>

<mission>
Provide a devastatingly accurate, elite-tier **Destiny Marriage Confirmation Reading**.
Explain everything in deep detail, but make it very easy for anyone to understand without confusing astrological jargon.

Stop talking about basic "compatibility". Analyze the deep **Signal Correlation**:
1. Does Person B physically fulfill the exact D9 and UL spouse archetype demanded by Person A's chart? (And vice versa). 
2. Is there a Jaimini Soul Tie (e.g. DK matching AK)?
3. Do their physical structures interlock (Lagna in 7th)? Is there a Karmic Obsession (Rahu/Ketu axis)?
4. Is their real-calendar timing synchronized to trigger the event? 

**Chances of Marriage: {dest_data['Percentage']}%**

**MANDATORY SECTION - KARMIC REMEDIES, SACRIFICES, AND ACTIONABLE DO'S:**
If the Destiny Confirmation Score is low, or if the KP Promise is weak (Warning = True), you MUST explicitly explain that astrology is not fatalistic. Provide a bulleted list of profound, actionable "Do's" and psychological sacrifices required to force this marriage to manifest against the odds. If a chart denies marriage, explain how adopting the highest, most selfless vibration of the 7th house (surrender, spiritual devotion to partner, abandoning ego) can override the planetary denial. List exactly what actions they must consciously take to make this marriage happen despite the mathematical friction.

Conclude with your absolute **FINAL VERDICT** on whether this union is mathematically destined to happen.
</mission>

<person_a_chart>{dos_a}</person_a_chart>
<person_b_chart>{dos_b}</person_b_chart>"""

def build_comparison_prompt(profiles_dossiers, criteria):
    python_rankings = calculate_and_rank_profiles(profiles_dossiers, criteria)
    profile_sections = "\n\n".join(
        f"<profile_{i+1}_chart>\nName: {name}\n{dossier}\n</profile_{i+1}_chart>"
        for i, (name, dossier) in enumerate(profiles_dossiers)
    )

    return f"""{GUARDRAILS}

<SYSTEM>
You are an elite Vedic Astrological Arbiter. Python has already calculated lifetime baseline comparison scores for each person.

CRITICAL SCORING RULES:
1. These scores measure durable natal promise, not temporary weather.
2. Current Sade Sati, current transit pressure, and current MD/AD are NOT allowed to change the baseline ranking.
3. Parashari structure supplies character and lifetime promise.
4. Divisional support refines the topic: D2 for wealth, D9 for relationship/luck/inner strength, D10 for career, D12/D30 when present for constitution and hidden strain.
5. KP cusp promise is used as a manifestation gate, especially for relationship, career, wealth, and health events.
6. For inverted parameters, lower score is better: Karmic Intensity and Hidden Pitfalls are burden scores.

METHODOLOGY SUMMARY:
WEALTH: D1 H2/H11/H5/H9, 2nd/11th lords, Jupiter/Venus/Mercury, D2 Hora, D9 confirmation, Dhana/Lakshmi/Chandra-Mangala/Raja yogas, KP H2/H11, and structural drains.
RELATIONSHIP: D1 H7/H2/H4/H5/H8, Venus/Jupiter/Moon/Darakaraka, D9, Manglik with cancellation logic, H7 affliction, and KP H7.
CAREER: D1 H10/H6/H11/H2/H9, Sun/Saturn/Mercury/Mars/Amatyakaraka, D10, Dharma-Karma/Raja/Pancha Mahapurusha yogas, and KP H10/H6.
STRUGGLES (Karmic Intensity): Durable burden from Lagna/Moon/key-house affliction, dusthana pressure, weak SAV, Kemadruma, war loss, combustion, gandanta, and lack of cancellation. No Sade Sati penalty. Note when high struggle scores co-occur with compensating yogas (e.g. Viparita Raja) as these indicate powerful spiritual evolution rather than mere misfortune.
HEALTH: Lagna/lord, H8, H3, H6, Sun/Moon/Saturn, D9/D12 confirmation, KP H1/H6/H8, benefic protection, and maraka/dusthana pressure.
HAPPINESS: H4/Moon with H5/H9/H11, Jupiter/Venus, D9 Moon, Gajakesari/Hamsa/Malavya/Adhi yogas, Kemadruma and 4th-house afflictions.
LUCK: H9/9th lord, H5 purva punya, Jupiter, D9, Lakshmi/Gajakesari/Hamsa/Raja yogas, and KP H9/H11.
SPIRITUAL: H12/H9/H8/H5, Ketu/Jupiter/Saturn/Atmakaraka/12th lord, D9 support, moksha-house placements, Hamsa and Viparita Raja.
HIDDEN PITFALLS: H8/H12/H6, nodes in sensitive houses, afflicted AK/AmK/DK and Moon/Venus/Jupiter, D9 hidden debility, KP denials, gandanta, combustion, dead avastha, and war loss.
CUSTOM CRITERIA: Python maps free-text criteria to the nearest classical house/karaka/KP cluster. Explain it as a chart-grounded custom heuristic and cite the houses/planets Python used from the ranking evidence and dossiers.

MATH LOCK: The Python rankings are final. Do NOT change rank order or recalculate scores.
</SYSTEM>

<PYTHON_CALCULATED_RANKINGS>
{python_rankings}
</PYTHON_CALCULATED_RANKINGS>

<FORMAT>
Begin the answer with the Rankings Table exactly in the order Python provides.

Then, for each selected parameter:
1. State the ranking in exact Python order.
2. For each person, write 2 concise sentences: first the key astrological reason using specific chart data, then the practical meaning.

Then write:
### Overall Composite Rankings
Use the Python composite order. Do not recompute it.

### Key Astrological Signatures Per Person
For each person: their 3 strongest signatures and 2 biggest vulnerabilities, grounded only in the chart data below.

CRITICAL: Use only the provided dossiers. Never invent planetary positions, yogas, or divisional placements.
</FORMAT>

{profile_sections}"""

def build_prashna_prompt(question, dossier):
    py_verdict, py_reason = get_prashna_python_verdict(question, dossier)
    return f"""{GUARDRAILS}
<mission>
PRASHNA (Horary) reading.
QUESTION: "{question}"

The Python Calculation Engine has already evaluated the chart and determined the exact answer.
**PYTHON VERDICT:** {py_verdict}
**PYTHON REASON:** {py_reason}

<KNOWLEDGE_ROUTING>
Open `kp6.md` and `bphs2.md`. Write the narrative explanation for this verdict based on the rules in the books. You are FORBIDDEN from contradicting the Python Verdict.
</KNOWLEDGE_ROUTING>

MANDATORY FINAL LINE: "VERDICT: [{py_verdict}] — [one sentence summary]"
</mission>

<prashna_chart_data>
{dossier}
</prashna_chart_data>"""

def build_transit_prompt(dossier, gochara_overlay):
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
    return f"""<mission>
You are an expert, intuitive Tarot Reader. Python has cryptographically drawn the following spread:
{cards_str}
Question: "{question}" | Spread: {mode} | Focus: {cfg['instruction']}
</mission>

<KNOWLEDGE_ROUTING>
Open `tguide.md`. You MUST base your interpretation of these cards entirely on the archetypes, reversed meanings, and synergies defined in the guidebook. Do not invent meanings outside the text.
If a card is Reversed, interpret its energy as blocked, internalised, or delayed.
</KNOWLEDGE_ROUTING>

<FORMAT>
- Overall Summary (2-3 sentences)
- Card-by-Card (each card's meaning in its specific spread position)
- Combined Message (how the three interact)
- Practical Action Step
- One-Line Takeaway
</FORMAT>"""

def build_yesno_prompt(question,card,state):
    return f"""<mission>
You are an expert Tarot Reader — Yes/No Oracle mode.
Question: "{question}" | Card drawn: {card} ({state})
</mission>
<KNOWLEDGE_ROUTING>
Open `tguide.md` and read the core energy of this card. 
Upright cards generally lean Yes; Reversed lean No — but factor in the archetype from the book.
</KNOWLEDGE_ROUTING>
<FORMAT>
1. Clear verdict: YES / LIKELY YES / UNCLEAR / LIKELY NO / NO
2. Why — the card's specific energy in this context (2-3 sentences from the guide)
3. Condition — what must happen (or be avoided)
4. One-Line Takeaway
</FORMAT>"""

def build_celtic_cross_prompt(question,cards,states):
    cards_str="\n".join(f"  {CELTIC_CROSS_POSITIONS[i]}: {cards[i]} ({states[i]})" for i in range(10))
    return f"""<mission>
You are an expert Tarot Reader — Celtic Cross spread.
Question: "{question}"
Ten-card spread:
{cards_str}
</mission>
<KNOWLEDGE_ROUTING>
Open `tguide.md`. You must synthesize these 10 cards strictly based on the meanings provided in the text. Look for patterns (suits clustering, Major Arcana count).
</KNOWLEDGE_ROUTING>
<FORMAT>
- Core Message (Cards 1+2 tension)
- Position-by-position reading
- Patterns & Themes observed
- Overall Narrative & Practical Guidance
- Final One-Line Takeaway
</FORMAT>"""

def build_birth_card_prompt(card,dob):
    return f"""<mission>
You are an expert Tarot Reader — Tarot Birth Card reading.
Date of Birth: {dob} | Tarot Birth Card: {card}
</mission>
<KNOWLEDGE_ROUTING>
Open `tguide.md`. This is a PERMANENT card. Interpret it as a deep, lifelong energy from the book's definitions.
</KNOWLEDGE_ROUTING>
<FORMAT>
1. Core symbolism of this card (from the guide)
2. How this archetype manifests as a lifelong theme
3. Core strengths & Core challenges
4. Karmic lesson & Personal mantra
</FORMAT>"""

def build_daily_tarot_prompt(card,state):
    return f"""<mission>
You are an expert Tarot Reader — Daily Guidance reading. Today's card: {card} ({state})
</mission>
<KNOWLEDGE_ROUTING>
Open `tguide.md`. Extract the practical daily advice for this exact card and state.
</KNOWLEDGE_ROUTING>"""

def build_numerology_prompt(name,dob_str,lp,dest,soul,pers,astro_dossier=None,user_q="",system="Western (Pythagorean)"):
    is_vedic=system=="Indian/Vedic (Chaldean)"
    sys_name="Chaldean (Indian/Vedic)" if is_vedic else "Pythagorean (Western)"
    py=get_personal_year(dob_str); pm=get_personal_month(dob_str); pd=get_personal_day(dob_str)
    r1,r2,r3,r4=get_pinnacle_cycles(dob_str); y=int(dob_str.split('-')[0])
    cur_age=datetime.now(ZoneInfo("Asia/Kolkata")).year-y
    def which_p():
        for s,e,n,c in [r1,r2,r3,r4]:
            if s-y<=cur_age<e-y: return s,e,n,c
        return r4
    cp=which_p()
    
    instructions=f"""<mission>
You are a Master Numerologist — {sys_name} system.

Python has already done the mathematical heavy lifting. All core numbers and cycles below are PRE-COMPUTED and LOCKED.
Your job is to explain what these exact numbers mean for the user.
</mission>

<KNOWLEDGE_ROUTING>
You must open and read the attached Numerology Markdown files (`wnum.md` for Pythagorean, or `inum1.md`/`inum2.md` for Chaldean). 
Extract the definitions, challenges, and life themes for the specific numbers Python has calculated below. Do not use generic numerology knowledge; rely strictly on the books provided.
</KNOWLEDGE_ROUTING>"""
    
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

def build_dashboard_data_prompt(dossier, transits, user_name):
    return f"""<instructions>
You are an elite Vedic astrologer. Analyze the natal chart against today's transits.
Provide exactly one short, personalized paragraph (2 sentences max) for {user_name} focusing on the most important planetary movement today. Keep it punchy and practical. DO NOT start with a greeting like 'Hello'.
Then, provide exactly four short, punchy phrases (max 5 words each) and one summary sentence for the general energy.
RESPOND ONLY IN VALID JSON FORMAT. NO MARKDOWN. NO EXTRA TEXT.
{{
  "GREETING": "The 2-sentence transit insight paragraph.",
  "ENERGY": "High/Low/Erratic/Focused",
  "FOCUS": "What to do today",
  "CAUTION": "What to avoid today",
  "WINDOW": "Best time of day",
  "SUMMARY": "One short sentence summarizing the vibe."
}}
</instructions>

<data>
{transits}

{dossier}
</data>"""

def build_astro_decide_prompt(dossier, transits, question, py_verdict, py_advice):
    # 1. PYTHON HAS ALREADY EXECUTED TARA BALA
    return f"""<instructions>
You are an Astro-Decide engine. The mathematical engine has already made the decision based on Tara Bala transit alignments.
Your job is to format this decision into JSON and provide ONE sentence linking the user's specific question to the provided advice.
RESPOND ONLY IN VALID JSON FORMAT. NO MARKDOWN.
{{
  "VERDICT": "{py_verdict}",
  "WHY": "One sentence explaining why based on the transits below.",
  "ALTERNATIVE": "{py_advice}"
}}
</instructions>
<decision_query>{question}</decision_query>
<data>{transits}</data>"""

# ═══════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════
def inject_nebula_css():
    st.markdown("""
<style>
@import url('[https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap](https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap)');

/* ── Base ── */
html,body,.stApp{background:radial-gradient(circle at 15% 50%,#1a0f2e,#0c0814 60%,#050308 100%)!important;font-family:'Inter',sans-serif!important;color:#e2e0ec!important}
#MainMenu, footer {visibility: hidden !important; height: 0 !important;}
[data-testid="stHeader"] {background: transparent !important;}
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

/* ── Bottom nav dropup (mobile only) ── */
#more-toggle { display: none; } /* Hidden checkbox for the pure CSS toggle */

.bnav-dropup {
    display: none;
    position: absolute;
    bottom: calc(100% + 15px);
    right: 10px;
    background: rgba(8,4,20,0.97);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(144,98,222,0.3);
    border-radius: 12px;
    padding: 8px 0;
    flex-direction: column;
    gap: 2px;
    box-shadow: 0 -8px 25px rgba(0,0,0,0.6);
    z-index: 10001;
    min-width: 160px;
}

/* Show menu when checkbox is checked */
#more-toggle:checked ~ .bnav-dropup {
    display: flex;
    animation: slideUp 0.2s ease-out forwards;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

.dropup-item {
    color: rgba(200,195,220,0.7);
    text-decoration: none;
    padding: 12px 18px;
    font-size: 0.88rem;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.2s;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}
.dropup-item:hover, .dropup-item.active {
    color: #c090e0;
    background: rgba(144,98,222,0.12);
}

/* Style for the More label to look like a button */
.more-label {
    display: flex; flex-direction: column; align-items: center; gap: 2px;
    padding: 4px 8px; background: none; border: none; cursor: pointer;
    color: rgba(200,195,220,0.5); font-family: 'Inter', sans-serif;
    font-size: .65rem; font-weight: 500; min-width: 52px; border-radius: 8px;
    transition: all .2s; margin: 0;
}
.more-label:hover, #more-toggle:checked + .more-label, .more-label.active {
    color: #c090e0; background: rgba(144,98,222,0.12);
}

/* Invisible overlay to close menu when clicking outside */
.dropup-overlay {
    display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 10000;
}
#more-toggle:checked ~ .dropup-overlay {
    display: block;
}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# BOTTOM NAV (mobile, functional via query params)
# ═══════════════════════════════════════════════════════════
def render_bottom_nav():
    main_items=[("🌌","Home","Dashboard"),
                ("💬","Chat","Consultation Room"),
                ("🔮","Oracle","The Oracle"),
                ("🃏","Tarot","Mystic Tarot")]
                
    more_items=[("🌟","Horoscopes","Horoscopes"),
                ("🔢","Numerology","Numerology"),
                ("📖","Profiles","Saved Profiles")]

    # Outer container remains FIXED. Inner container is RELATIVE.
    nav_html='<div class="bottom-nav"><div class="bottom-nav-inner" style="position:relative;">'
    
    # 1. Main Navigation Buttons
    for icon,label,page in main_items:
        active="active" if st.session_state.nav_page==page else ""
        safe_url = page.replace(" ", "%20")
        nav_html+=f'<a class="bnav-btn {active}" target="_self" href="?p={safe_url}" title="{label}"><span class="bnav-icon">{icon}</span><span>{label}</span></a>'
        
    # 2. "More" Button (Using a hidden checkbox & label toggle)
    more_active="active" if st.session_state.nav_page in ["Horoscopes", "Numerology", "Saved Profiles"] else ""
    nav_html+=f'''
    <input type="checkbox" id="more-toggle">
    <label for="more-toggle" class="more-label {more_active}" title="More">
        <span class="bnav-icon">☰</span>
        <span>More</span>
    </label>
    '''
    
    # 3. Invisible background overlay (closes the menu if you tap anywhere else)
    nav_html+='<label for="more-toggle" class="dropup-overlay"></label>'
    
    # 4. The Drop-up Menu
    nav_html+='<div class="bnav-dropup">'
    for icon,label,page in more_items:
        active="active" if st.session_state.nav_page==page else ""
        safe_url = page.replace(" ", "%20")
        nav_html+=f'<a class="dropup-item {active}" target="_self" href="?p={safe_url}"><span class="bnav-icon" style="font-size:1.2rem;">{icon}</span><span>{label}</span></a>'
    nav_html+='</div>'
    
    nav_html+='</div></div>'

    st.markdown(nav_html,unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAROT CARD OVERLAY
# ═══════════════════════════════════════════════════════════
def tarot_reversed_help():
    return ("Optional. When this is on, each drawn card has a 50/50 chance to appear upside down. "
            "In tarot, an upside-down card usually means the card's energy is blocked, delayed, hidden, "
            "or being felt internally. Leave this off for a simpler beginner reading where every card is upright.")

def render_tarot_overlay(cards, states, layout="three"):
    """
    layout: 'one' | 'three' | 'ten'
    Reuses the working kapp-style video stage and flip animation while supporting the newer modes.
    """
    cards=list(cards or [])
    if not cards: return
    states=list(states or [])
    if len(states)<len(cards): states += ["Upright"]*(len(cards)-len(states))
    states=states[:len(cards)]

    n=len(cards)
    if layout not in {"one","three","ten"}:
        layout="one" if n==1 else ("ten" if n==10 else "three")

    uid="t"+secrets.token_hex(4)
    back_url=f"{TAROT_BASE}tarotrear.png"
    vid_desk=f"{TAROT_BASE}tarotvid.mp4"
    vid_mob=f"{TAROT_BASE}tarotvideo.mp4"

    if layout=="ten":
        container_css=f"""
.card-row-{uid}{{display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:repeat(2,auto);gap:2% 2%;width:74%;align-items:center;justify-items:center;}}
.card-row-{uid} .t-card-wrapper-{uid}{{width:100%;}}"""
        mobile_layout_css=f".card-row-{uid}{{width:82%;}}"
        rise_stagger=0.14
        flip_stagger=0.16
        flip_start=1.15
    else:
        gap="0" if layout=="one" else "4%"
        container_css=f"""
.card-row-{uid}{{display:flex;justify-content:center;align-items:center;gap:{gap};width:100%;}}
.card-row-{uid} .t-card-wrapper-{uid}{{width:25%;max-width:138px;}}"""
        mobile_layout_css=f".card-row-{uid} .t-card-wrapper-{uid}{{width:28%;max-width:none;}}"
        rise_stagger=0.4
        flip_stagger=0.5
        flip_start=1.5

    card_blocks=""
    for i,(card,state) in enumerate(zip(cards,states)):
        front_url=f"{TAROT_BASE}{get_filename(card)}"
        rev_class=" reversed" if state=="Reversed" else ""
        rise_delay=0.15+(i*rise_stagger)
        flip_delay=flip_start+(i*flip_stagger)
        card_blocks+=f"""
<div class="t-card-wrapper-{uid}" style="--rise-delay:{rise_delay:.2f}s">
  <div class="t-card-inner-{uid}" style="--flip-delay:{flip_delay:.2f}s">
    <div class="t-card-back-{uid}"></div>
    <div class="t-card-front-{uid}{rev_class}" style="background-image:url('{front_url}')" aria-label="{card}"></div>
  </div>
</div>"""

    scroll_delay=flip_start+(max(n-1,0)*flip_stagger)+1.1
    html=f"""<style>
.tarot-stage-{uid}{{position:relative;width:100%;max-width:550px;margin:0 auto 2rem;border-radius:16px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.5);background:linear-gradient(45deg,#1a0f2e,#0c0814)}}
.vid-desktop-{uid},.vid-mobile-{uid}{{width:100%;display:block;object-fit:cover;opacity:.85}}
.vid-desktop-{uid}{{aspect-ratio:1440/1678}}
.vid-mobile-{uid}{{display:none;aspect-ratio:24/41}}
.card-container-{uid}{{position:absolute;bottom:8%;width:100%;display:flex;justify-content:center;perspective:1000px;z-index:2}}
{container_css}
.t-card-wrapper-{uid}{{aspect-ratio:2/3;opacity:1;transform:translateY(0);animation:tarot-rise-{uid} .9s var(--rise-delay) cubic-bezier(.16,1,.3,1) both}}
.t-card-inner-{uid}{{width:100%;height:100%;position:relative;transform-style:preserve-3d;transform:rotateY(180deg);animation:tarot-flip-{uid} .8s var(--flip-delay) cubic-bezier(.34,1.56,.64,1) both}}
.t-card-front-{uid},.t-card-back-{uid}{{position:absolute;inset:0;width:100%;height:100%;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:8px;box-shadow:0 5px 15px rgba(0,0,0,.8);background-size:cover;background-position:center}}
.t-card-back-{uid}{{background-image:url('{back_url}');border:2px solid rgba(205,140,80,.5)}}
.t-card-front-{uid}{{transform:rotateY(180deg);border:2px solid rgba(205,140,80,.8)}}
.t-card-front-{uid}.reversed{{transform:rotateY(180deg) rotate(180deg)}}
.scroll-prompt-{uid}{{position:absolute;bottom:2%;width:100%;text-align:center;color:rgba(255,255,255,.9);font-family:'Space Grotesk',sans-serif;font-size:.95rem;letter-spacing:1px;opacity:1;text-shadow:0 2px 5px rgba(0,0,0,.9);pointer-events:none;animation:tarot-scroll-{uid} .8s {scroll_delay:.2f}s ease both;z-index:3}}
@keyframes tarot-rise-{uid}{{from{{opacity:0;transform:translateY(50px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes tarot-flip-{uid}{{from{{transform:rotateY(0deg)}}to{{transform:rotateY(180deg)}}}}
@keyframes tarot-scroll-{uid}{{from{{opacity:0}}to{{opacity:1}}}}
@media(max-width:768px){{.vid-desktop-{uid}{{display:none}}.vid-mobile-{uid}{{display:block}}.card-container-{uid}{{bottom:10%;}}{mobile_layout_css}}}
</style>
<div class="tarot-stage-{uid}">
  <video class="vid-desktop-{uid}" autoplay loop muted playsinline><source src="{vid_desk}" type="video/mp4"></video>
  <video class="vid-mobile-{uid}" autoplay loop muted playsinline><source src="{vid_mob}" type="video/mp4"></video>
  <div class="card-container-{uid}"><div class="card-row-{uid}">{card_blocks}</div></div>
  <div class="scroll-prompt-{uid}">The cards have spoken. Scroll down for your reading.</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

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
            st.session_state[f"d_{key_prefix}"]=st.date_input("Date of Birth",pre_date,min_value=date(1850,1,1),max_value=date(2050,12,31),key=f"wd_{key_prefix}")
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
            pre_gender=pre.get('gender', 'M') if pre else 'M'
            st.session_state[f"gender_{key_prefix}"]=st.radio("Gender", ["M", "F"], index=0 if pre_gender=='M' else 1, key=f"wg_{key_prefix}", horizontal=True)
            st.session_state[f"save_{key_prefix}"]=st.checkbox("💾 Save this person to My Saved Profiles for future use",key=f"wsave_{key_prefix}")
            pre_exact = pre.get('exact_time', False) if pre else False
            st.session_state[f"exact_{key_prefix}"]=st.checkbox("Birth time is exact to the minute", value=pre_exact, key=f"wexact_{key_prefix}")
            return {"type":"new","idx":key_prefix}
        else:
            opts_raw=sorted_profile_options()
            if not opts_raw: return {"type":"empty_saved","idx":key_prefix}
            labels=["— Select —"]+[f"{'⭐ ' if i==st.session_state.default_profile_idx else ''}{p['name']} ({format_date_ui(p['date'])})" for i,p in opts_raw]
            sel=st.selectbox("Select Profile",labels,key=f"sel_{key_prefix}",label_visibility="collapsed")
            if sel!="— Select —":
                _,p=opts_raw[labels.index(sel)-1]
                st.success(f"Loaded: **{p['name']}** 📍 {p['place'].split(',')[0]} ({p.get('gender', 'M')})")
                st.session_state[f"exact_{key_prefix}"] = p.get('exact_time', False)
                return {"type":"saved","data":p,"idx":key_prefix}
            return {"type":"empty_saved","idx":key_prefix}

def resolve_profile(item):
    i=item["idx"];
    if item["type"]=="saved": return item["data"], item["data"].get('exact_time', False)
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
    u_gender=st.session_state.get(f"gender_{i}","M")
    u_exact=st.session_state.get(f"exact_{i}",False)
    prof={"name":u_name.strip(),"date":u_date.isoformat(),"time":u_time.strftime("%H:%M"),"place":fp,"lat":fl,"lon":flon,"tz":ftz, "gender": u_gender, "exact_time": u_exact}
    if st.session_state.get(f"save_{i}",False) and not is_duplicate_in_db(prof):
        st.session_state.db.append(prof); sync_db()
    return prof, u_exact

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;margin-bottom:1.5rem;font-size:1.3rem;'>🪐 ASTRO SUITE beta</h2>",unsafe_allow_html=True)
        pages=[("🌌 Dashboard","Dashboard"),
               ("💬 Consult Room","Consultation Room"),  # <-- ADDED THIS
               ("🔮 The Oracle","The Oracle"),
               ("🃏 Mystic Tarot","Mystic Tarot"),
               ("🌟 Horoscopes","Horoscopes"),
               ("🔢 Numerology","Numerology"),
               ("📖 Saved Profiles","Saved Profiles")]
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
def calculate_tara_bala(natal_moon_lon, transit_moon_lon):
    """
    Calculates the 9-point Tara Bala (Star Strength) system.
    Returns a dict with the traffic light color, title, and actionable advice.
    """
    ns = 360 / 27
    natal_idx = int((natal_moon_lon % 360) // ns)
    transit_idx = int((transit_moon_lon % 360) // ns)
    
    tara_value = ((transit_idx - natal_idx) % 9) + 1
    
    tara_meanings = {
        1: {"tara": "Janma (Birth)", "color": "🟡 YELLOW", "status": "Caution", "advice": "Your mind may feel restless or overwhelmed today. Stick to routine tasks and avoid making impulsive decisions."},
        2: {"tara": "Sampat (Wealth)", "color": "🟢 GREEN", "status": "Go", "advice": "Highly favorable for finances and resources. Excellent day to ask for a raise, make investments, or close a deal."},
        3: {"tara": "Vipat (Danger)", "color": "🔴 RED", "status": "Stop", "advice": "Obstacles and sudden losses are likely. Keep a very low profile today. Do not start new projects or argue with authority."},
        4: {"tara": "Kshema (Well-being)", "color": "🟢 GREEN", "status": "Go", "advice": "A day of peace, healing, and stability. Perfect for self-care, finalizing plans, and nurturing relationships."},
        5: {"tara": "Pratyak (Obstacles)", "color": "🔴 RED", "status": "Stop", "advice": "You will face resistance and delays. People may oppose your ideas. Focus on patience and do not force outcomes today."},
        6: {"tara": "Sadhaka (Achievement)", "color": "🟢 GREEN", "status": "Go", "advice": "Cosmic green light for ambition. Your efforts will yield direct success today. Push hard on your biggest goals."},
        7: {"tara": "Naidhana (Destruction)", "color": "🔴 RED", "status": "Stop", "advice": "Severe cosmic friction. Avoid travel, signing contracts, or taking risks. Use today strictly for cleaning up old messes."},
        8: {"tara": "Mitra (Friendship)", "color": "🟢 GREEN", "status": "Go", "advice": "Support from others is highlighted. Great day for networking, collaborating, and asking for favors."},
        9: {"tara": "Parama Mitra (Great Joy)", "color": "🟢 GREEN", "status": "Go", "advice": "Extremely auspicious. Things will easily go your way. Take bold actions and enjoy the cosmic tailwind!"}
    }
    return tara_meanings[tara_value]

def show_dashboard():
    if "dash_toggles" not in st.session_state:
        st.session_state.dash_toggles = {
            "greeting": True,
            "consult": True,
            "forecast": True,
            "decide": True,
            "calendar": True,
            "tarot": True,
            "dasha_alert": True
        }

    # ───── STRICT PERSONAL OS LOGIC ─────
    dp, active_idx = get_default_profile()
    
    if not dp:
        st.markdown("## 🧭 The Cosmic Compass")
        st.info("💡 Welcome! Go to **Saved Profiles** and tap the ⭐ next to your name to set up your personal dashboard.")
        return

    prof = dp
    tz = prof.get("tz", "Asia/Kolkata")
    today_str = get_local_today(tz).isoformat()

    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"## 🧭 {prof['name'].split()[0]}'s Compass")
    with c2:
        with st.popover("⚙️"):
            st.session_state.dash_toggles["greeting"] = st.checkbox("Daily Greeting", value=st.session_state.dash_toggles.get("greeting", True))
            st.session_state.dash_toggles["consult"] = st.checkbox("Consultation Room", value=st.session_state.dash_toggles.get("consult", True))
            st.session_state.dash_toggles["forecast"] = st.checkbox("Forecast", value=st.session_state.dash_toggles.get("forecast", True))
            st.session_state.dash_toggles["decide"] = st.checkbox("Astro-Decide", value=st.session_state.dash_toggles.get("decide", True))
            st.session_state.dash_toggles["calendar"] = st.checkbox("Calendar", value=st.session_state.dash_toggles.get("calendar", True))
            st.session_state.dash_toggles["tarot"] = st.checkbox("Tarot", value=st.session_state.dash_toggles.get("tarot", True))
            st.session_state.dash_toggles["dasha_alert"] = st.checkbox("Dasha Shift Alerts", value=st.session_state.dash_toggles.get("dasha_alert", True))

    st.markdown("---")

    # ───── DASHBOARD CONSULTATION CARD ─────
    if st.session_state.dash_toggles.get("consult", True):
        memory_key = f"consult_chat_{prof['name']}"
        last_msg = "Ask any question about your life, timing, or planetary energies."
        
        if memory_key in st.session_state and len(st.session_state[memory_key]) > 0:
            for msg in reversed(st.session_state[memory_key]):
                if msg["role"] == "model":
                    last_msg = msg["parts"][0][:100] + "..." 
                    break

        st.markdown(f"""
        <div style='background:linear-gradient(135deg, rgba(144,98,222,0.15), rgba(205,140,80,0.1)); border:1px solid rgba(144,98,222,0.3); border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
            <h3 style='margin:0 0 0.3rem 0; font-size:1.1rem; color:#fff;'>💬 Ask the Astrologer</h3>
            <p style='margin:0 0 0.8rem 0; font-size:0.85rem; color:#cd8c50;'><em>"{last_msg}"</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Enter Consultation Room →", use_container_width=True):
            st.session_state.nav_page = "Consultation Room"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)


    # ───── UNIFIED DASHBOARD DATA GENERATION ─────
    dash_cache_key = f"dash_data_{active_idx}_{today_str}"
    prof_json = json.dumps(prof, sort_keys=True)

    if st.session_state.dash_toggles.get("greeting", True) or st.session_state.dash_toggles.get("forecast", True):
        if dash_cache_key not in st.session_state:
            with st.spinner("Aligning the stars for your daily report..."):
                try:
                    st.session_state[dash_cache_key] = fetch_cached_dashboard_data(prof_json, today_str)
                except Exception:
                    st.session_state[dash_cache_key] = {
                        "GREETING": "The stars are quiet right now (All Free Models Exhausted). Try again in a minute!",
                        "ENERGY": "Resting", "FOCUS": "Patience", "CAUTION": "Rushing",
                        "WINDOW": "Later", "SUMMARY": "Cosmic bandwidth limit reached."
                    }

    # ───── RENDER DAILY GREETING ─────
    if st.session_state.dash_toggles.get("greeting", True) and dash_cache_key in st.session_state:
        st.markdown(f"""
        <div style="padding-left: 14px; border-left: 4px solid #9062de; margin-bottom: 1.5rem;">
            <p style="font-size: 1.05rem; font-weight: 500; color: #e2e0ec; margin: 0; line-height: 1.5;">
                {st.session_state[dash_cache_key].get('GREETING', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ───── 7 DAY CALENDAR ─────
    if st.session_state.dash_toggles.get("calendar", True):
        st.markdown("### 📅 Your Cosmic Week")
        st.caption("Your personalized weather based on your Moon sign. 🟢 Green = Go, 🔴 Red = Lay low.")
        now = datetime.now(ZoneInfo(tz))
        prof_date = date.fromisoformat(prof['date'])
        prof_time = datetime.strptime(prof['time'], "%H:%M").time()

        jd_natal, _, _ = local_to_julian_day(prof_date, prof_time, tz)
        natal_moon, _ = get_planet_longitude_and_speed(jd_natal, PLANETS["Moon"])  # Sidereal Lahiri

        html = '<div style="display:flex; gap:8px; overflow-x:auto; padding-bottom:10px;">'
        todays_advice = ""

        for i in range(7):
            d = now + timedelta(days=i)
            utc_d = d.astimezone(ZoneInfo("UTC"))
            jd = swe.julday(utc_d.year, utc_d.month, utc_d.day, 12.0)
            
            moon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH|swe.FLG_SIDEREAL); moon = float(moon[0]) % 360
            tara = calculate_tara_bala(natal_moon, moon)

            is_today = (i == 0)
            if is_today:
                todays_advice = f"**Today's Focus ({tara['tara'].split(' ')[0]}):** {tara['advice']}"

            bg = "rgba(144,98,222,0.2)" if is_today else "rgba(255,255,255,0.05)"
            border = "border: 1px solid #9062de;" if is_today else "border: 1px solid rgba(255,255,255,0.1);"
            
            theme = tara['advice'].split('.')[0] + '.'

            html += f"""<div style="min-width:150px; padding:12px; border-radius:10px; background:{bg}; {border} text-align:center; flex-shrink:0; display:flex; flex-direction:column; justify-content:space-between;">
<div>
    <div style="font-size:0.75rem; color:#beb9cd; font-weight:bold; letter-spacing:0.5px;">{'TODAY' if is_today else d.strftime('%a, %b %d').upper()}</div>
    <div style="font-size:1.4rem; margin:6px 0;">{tara['color'].split(' ')[0]}</div>
    <div style="font-size:0.85rem; color:#fff; font-weight:600;">{tara['tara'].split(' ')[0]}</div>
</div>
<div style="font-size:0.68rem; color:rgba(255,255,255,0.65); margin-top:8px; line-height:1.4;">{theme}</div>
</div>"""

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
        st.info(todays_advice)
        st.markdown("<br>", unsafe_allow_html=True)

    # ───── RENDER 10-SECOND FORECAST CARDS ─────
    if st.session_state.dash_toggles.get("forecast", True) and dash_cache_key in st.session_state:
        data = st.session_state[dash_cache_key]
        st.markdown("### 📡 Today's Energy")
        st.markdown(f"""
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 0.5rem;">
            <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; border-left:4px solid #cd8c50;">
                <span style="font-size:0.75rem; color:#beb9cd; text-transform:uppercase;">Energy</span><br>
                <span style="font-weight:600; color:#fff;">{data.get('ENERGY', 'N/A')}</span>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; border-left:4px solid #9062de;">
                <span style="font-size:0.75rem; color:#beb9cd; text-transform:uppercase;">Focus</span><br>
                <span style="font-weight:600; color:#fff;">{data.get('FOCUS', 'N/A')}</span>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; border-left:4px solid #e74c3c;">
                <span style="font-size:0.75rem; color:#beb9cd; text-transform:uppercase;">Caution</span><br>
                <span style="font-weight:600; color:#fff;">{data.get('CAUTION', 'N/A')}</span>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; border-left:4px solid #2ecc71;">
                <span style="font-size:0.75rem; color:#beb9cd; text-transform:uppercase;">Best Time</span><br>
                <span style="font-weight:600; color:#fff;">{data.get('WINDOW', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(data.get("SUMMARY", ""))
      
    # ───── ASTRO DECIDE ─────
    if st.session_state.dash_toggles.get("decide", True):
        st.markdown("### ⚖️ Astro-Decide")
        
        def clear_decide_state():
            st.session_state.astro_decide_q = ""
            if "astro_decide_result" in st.session_state:
                del st.session_state.astro_decide_result

        q = st.text_input("What do you need to decide right now?", key="astro_decide_q", placeholder="e.g. Should I sign this contract today?")

        c1, c2 = st.columns([3, 1])
        with c1:
            decide_btn = st.button("Decide", type="primary", use_container_width=True)
        with c2:
            st.button("Clear", use_container_width=True, on_click=clear_decide_state)

        if decide_btn:
            if not q.strip():
                st.warning("Ask something first.")
            else:
                with st.spinner("Consulting the transits..."):
                    try:
                        dos = generate_astrology_dossier(prof, False, compact=True)
                        transits = get_gochara_overlay(prof)
                        
                        # --- THE PYTHON MATH LAYER ---
                        jd_natal, _, _ = local_to_julian_day(date.fromisoformat(prof['date']), datetime.strptime(prof['time'], "%H:%M").time(), prof['tz'])
                        natal_moon, _ = get_planet_longitude_and_speed(jd_natal, PLANETS["Moon"])  # Sidereal Lahiri
                        dt_now = datetime.now(ZoneInfo("UTC"))
                        jd_now = swe.julday(dt_now.year, dt_now.month, dt_now.day, dt_now.hour + dt_now.minute / 60.0)
                        transit_moon, _ = get_planet_longitude_and_speed(jd_now, PLANETS["Moon"])  # Sidereal
                        
                        tara = calculate_tara_bala(natal_moon, transit_moon)
                        py_verdict = "YES" if tara['status'] == "Go" else ("WAIT" if tara['status'] == "Stop" else "PROCEED CAUTIOUSLY")
                        
                        # --- THE AI FORMATTING LAYER ---
                        prompt = build_astro_decide_prompt(dos, transits, q, py_verdict, tara['advice'])
                        res = generate_content_with_fallback(prompt)
                        st.session_state.astro_decide_result = safe_json(res, {
                            "VERDICT": py_verdict, "WHY": "Cosmic signals processed.", "ALTERNATIVE": tara['advice']
                        })
                    except Exception as e:
                        st.session_state.astro_decide_result = {
                            "VERDICT": "RESTING", "WHY": "Free Models Exhausted.", "ALTERNATIVE": "Try again!"
                        }
        
        if "astro_decide_result" in st.session_state:
            out = st.session_state.astro_decide_result
            with st.container(border=True):
                st.markdown(f"### 🔮 Verdict: {out.get('VERDICT', 'WAIT')}")
                st.markdown(f"**Why:** {out.get('WHY', '')}")
                st.markdown(f"*{out.get('ALTERNATIVE', '')}*")

    # ───── DAILY TAROT ─────
    if st.session_state.dash_toggles.get("tarot", False):
        st.markdown("### 🃏 Daily Tarot Guidance")

        import random
        rng = random.Random(f"{prof['name']}_{today_str}")
        daily_card = rng.choice(FULL_TAROT_DECK)
        daily_state = rng.choice(["Upright", "Reversed"])

        cache_key_tarot = f"dash_tarot_{active_idx}_{today_str}"
        reveal_key_tarot = f"{cache_key_tarot}_revealed"

        is_revealed = st.session_state.get(reveal_key_tarot, False)

        t1, t2 = st.columns([1.2, 3]) 

        with t1:
            img_url = f"{TAROT_BASE}{get_filename(daily_card)}"
            back_url = f"{TAROT_BASE}tarotrear.png"
            rev_class = "reversed" if daily_state == "Reversed" else ""
            anim_class = "dash-tarot-revealed" if is_revealed else "dash-tarot-hidden"

            st.markdown(f"""
            <style>
            .dash-tarot-scene {{
                width: 130px; 
                aspect-ratio: 2/3;
                perspective: 1000px;
                margin: 0 auto;
            }}
            .dash-tarot-card {{
                width: 100%; height: 100%;
                position: relative;
                transform-style: preserve-3d;
            }}
            .dash-tarot-revealed {{
                animation: dashFlip 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
            }}
            .dash-tarot-hidden {{
                transform: rotateY(0deg);
            }}
            @keyframes dashFlip {{
                0% {{ transform: rotateY(0deg); }}
                100% {{ transform: rotateY(180deg); }}
            }}
            .dash-tarot-face {{
                position: absolute; inset: 0;
                width: 100%; height: 100%;
                backface-visibility: hidden;
                border-radius: 6px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                background-size: cover; background-position: center;
                border: 2px solid rgba(205,140,80,.6);
            }}
            .dash-tarot-front {{
                transform: rotateY(180deg);
                background-image: url('{img_url}');
            }}
            .dash-tarot-front.reversed {{
                transform: rotateY(180deg) rotateZ(180deg);
            }}
            .dash-tarot-back {{
                background-image: url('{back_url}');
            }}
            </style>
            <div class="dash-tarot-scene">
                <div class="dash-tarot-card {anim_class}">
                    <div class="dash-tarot-face dash-tarot-back"></div>
                    <div class="dash-tarot-face dash-tarot-front {rev_class}"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_revealed:
                st.markdown(f"<div style='text-align:center; font-size:0.75rem; color:#beb9cd; font-weight:600; margin-top:8px;'>{daily_card}<br>({daily_state})</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; font-size:0.75rem; color:#beb9cd; font-weight:600; margin-top:8px;'>The Oracle is waiting</div>", unsafe_allow_html=True)

        with t2:
            if not is_revealed:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Reveal & Interpret Today's Card ✨", use_container_width=True):
                    st.session_state[reveal_key_tarot] = True
                    with st.spinner("Channeling the deck..."):
                        try:
                            tarot_result = fetch_cached_daily_tarot(json.dumps(prof, sort_keys=True), today_str, daily_card, daily_state)
                        except Exception:
                            tarot_result = {
                                "MEANING": "Trust the process unfolding today.",
                                "ACTION": "Observe before making any sudden moves.",
                                "MANTRA": "I am exactly where I need to be."
                            }
                        st.session_state[cache_key_tarot] = tarot_result
                    st.rerun()

            if st.session_state.get(reveal_key_tarot, False):
                if cache_key_tarot not in st.session_state:
                    with st.spinner("Channeling the deck..."):
                        try:
                            st.session_state[cache_key_tarot] = fetch_cached_daily_tarot(json.dumps(prof, sort_keys=True), today_str, daily_card, daily_state)
                        except Exception:
                            st.session_state[cache_key_tarot] = {
                                "MEANING": "Trust the process unfolding today.",
                                "ACTION": "Observe before making any sudden moves.",
                                "MANTRA": "I am exactly where I need to be."
                            }
                t_data = st.session_state[cache_key_tarot]
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.08); height:100%;">
                    <p style="margin:0 0 10px 0; font-size:0.85rem;"><b style="color:#fff;">Meaning:</b> <span style="color:#beb9cd;">{t_data.get('MEANING', '')}</span></p>
                    <p style="margin:0 0 10px 0; font-size:0.85rem;"><b style="color:#fff;">Action:</b> <span style="color:#beb9cd;">{t_data.get('ACTION', '')}</span></p>
                    <p style="margin:0; font-size:0.85rem;"><b style="color:#cd8c50;">Mantra:</b> <i style="color:#e0d8f0;">"{t_data.get('MANTRA', '')}"</i></p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")


    # ───── DASHA SHIFT ALERTS ─────
    if st.session_state.dash_toggles.get("dasha_alert", True):
        now_dt = datetime.now(ZoneInfo(tz))
        today_date = now_dt.date()
        p_date = date.fromisoformat(prof['date']) if isinstance(prof['date'], str) else prof['date']
        p_time = datetime.strptime(prof['time'], "%H:%M").time() if isinstance(prof['time'], str) else prof['time']
        
        jd_nat, dt_loc, _ = local_to_julian_day(p_date, p_time, tz)
        m_lon, _ = get_planet_longitude_and_speed(jd_nat, PLANETS["Moon"])
        
        d_info = build_vimshottari_timeline(dt_loc, m_lon, now_dt)
        
        ad_days = (d_info['ad_end'].astimezone(ZoneInfo(tz)).date() - today_date).days
        pd_days = (d_info['pd_end'].astimezone(ZoneInfo(tz)).date() - today_date).days
        
        themes = {
            "Sun": "authority, soul-searching, and visibility", "Moon": "emotional shifts and deep changes",
            "Mars": "action, drive, and potential friction", "Rahu": "ambition, obsession, and sudden events",
            "Jupiter": "expansion, wisdom, and opportunities", "Saturn": "discipline, structure, and hard work",
            "Mercury": "intellect, communication, and business", "Ketu": "detachment, endings, and spirituality",
            "Venus": "relationships, comfort, and harmony", "Unknown": "shifting cosmic energies"
        }
        
        try:
            nxt_ad = DASHA_ORDER[(DASHA_ORDER.index(d_info['current_ad']) + 1) % 9]
            nxt_pd = DASHA_ORDER[(DASHA_ORDER.index(d_info['current_pd']) + 1) % 9]
        except:
            nxt_ad, nxt_pd = "Unknown", "Unknown"
            
        if 0 <= ad_days <= 45:
            a_title = f"⚠️ Major Chapter Shift in {ad_days} Days"
            a_text = f"Your Antardasha is shifting from **{d_info['current_ad']}** to **{nxt_ad}**. Prepare for a major life theme shift towards {themes.get(nxt_ad, 'new paths')}."
            b_color = "#e74c3c"
        elif 0 <= pd_days <= 14:
            a_title = f"⏱️ Minor Energy Shift in {pd_days} Days"
            a_text = f"Your Pratyantar Dasha shifts from **{d_info['current_pd']}** to **{nxt_pd}**. Expect a brief pivot towards {themes.get(nxt_pd, 'new paths')}."
            b_color = "#cd8c50"
        else:
            a_title = f"⏳ Current Phase: {d_info['current_ad']} Antardasha"
            a_text = f"You are deep in your **{d_info['current_md']}** Mahadasha and **{d_info['current_ad']}** Antardasha. The next major shift is {ad_days} days away."
            b_color = "rgba(255,255,255,0.08)"

        st.markdown(f"""
        <div style="padding: 14px 18px; border-radius: 12px; background: rgba(0,0,0,0.2); border: 1px solid {b_color}; margin-bottom: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <p style="margin: 0 0 4px 0; font-size: 0.80rem; color: {b_color if b_color != 'rgba(255,255,255,0.08)' else '#beb9cd'}; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">{a_title}</p>
            <p style="margin: 0; font-size: 0.95rem; color: #e2e0ec; line-height: 1.5;">{a_text}</p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# CONSULTATION ROOM (Global Chat)
# ═══════════════════════════════════════════════════════════
def show_consultation_room():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>💬 Ask the Astrologer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6)'>Have a free-flowing conversation about your chart.</p>", unsafe_allow_html=True)

    dp, dp_idx = get_default_profile()
    if not dp:
        st.warning("Please set a ⭐ default profile in 'Saved Profiles' first so the Astrologer knows who to look at.")
        return

    st.success(f"The Astrologer is currently looking at the chart for: **{dp['name']}**")
    
    memory_key = f"v2_chat_{dp['name']}"
    if memory_key not in st.session_state: st.session_state[memory_key] = []
    
    # UI History
    for msg in st.session_state[memory_key]:
        with st.chat_message("assistant" if msg["role"] == "model" else "user"):
            st.markdown(msg["display"])

    if q := st.chat_input("Ask anything..."):
        st.chat_message("user").markdown(q)
        with st.chat_message("assistant"):
            res_ph = st.empty()
            with st.spinner("Consulting books..."):
                dos = generate_astrology_dossier(dp)
                transits = get_gochara_overlay(dp)

                # SINGLE-CALL ARCHITECTURE (replaces 3-agent cascade)
                # Why? 3 parallel agents + 1 synthesis = 4 API calls in ~5 seconds.
                # Flash Lite has 250K TPM — that cascade blew past it every time.
                # One call with the full dossier is MORE accurate (AI sees the complete picture)
                # and uses 1 API call instead of 4.
                guardrails = """<CONSULTATION_GUARDRAILS>
You are a warm, highly empathetic Vedic Astrologer. Speak conversationally, directly to the user.

RULES:
1. MATH LOCK: Never invent or alter any number. Use only data from the dossier.
2. MISSING CONTEXT: If you need the user's current life situation to answer well, ask them warmly.
3. OTHERS (NO DATA): "I'd love to help! Could you share their birth details, full name, or at minimum a first name?"
4. OTHERS (FIRST NAME ONLY): Use Vedic Name Astrology (Nama Nakshatra). Disclaimer: "I'm using name-based Vedic energy — a birth chart gives true precision."
5. OTHERS (FULL NAME): Use Chaldean Numerology + Name Astrology. Disclaimer: "Name-based reading only — birth chart needed for full accuracy."
6. OTHERS (FULL BIRTH DETAILS): General reading from their placements. Note: "For dual-chart math, use the Matchmaking tab."
7. MATCHMAKING: Only redirect to Matchmaking tab if user EXPLICITLY asks for compatibility/rishta check.
8. FUTURE TIMING: Use ONLY the Vimshottari Dasha timeline from the dossier. Never guess future transits.
9. TAROT: Redirect to Mystic Tarot tab warmly.
</CONSULTATION_GUARDRAILS>"""

                # Build a single rich prompt: dossier + transits + question + history context
                hist_text = ""
                if st.session_state[memory_key]:
                    last_few = st.session_state[memory_key][-4:]  # Last 2 exchanges for context
                    hist_text = "\n\nRECENT CONVERSATION:\n" + "\n".join(
                        f"{'User' if m['role']=='user' else 'Astrologer'}: {m['display']}"
                        for m in last_few
                    )

                full_prompt = (
                    f"{guardrails}\n\n"
                    f"BIRTH CHART DOSSIER FOR {dp['name']}:\n{dos}\n\n"
                    f"TODAY'S LIVE TRANSITS:\n{transits}"
                    f"{hist_text}\n\n"
                    f"USER QUESTION: {q}"
                )

                # One call — full dossier fits in Flash Lite's 1M context.
                # htrh1.md = B.V. Raman's practical house reading guide (Houses 1-6).
                # At 119K tokens it fits safely alongside dossier (~20K) within 250K TPM.
                # For questions about H7-H12 (marriage, career) the dossier already has KP verdicts.
                try:
                    consult_book = get_knowledge_files(["htrh1.md"])
                    consult_content = consult_book + [full_prompt]
                except Exception:
                    consult_content = [full_prompt]  # Fallback: no book if GitHub fetch fails

                full_txt = ""
                success = False
                for m_id in FREE_MODELS:
                    if success: break
                    for attempt in range(3):
                        try:
                            model = get_ai_model_by_name(m_id, custom_system_rules=guardrails)
                            response = model.generate_content(consult_content, stream=True)
                            for chunk in response:
                                full_txt += chunk.text
                                res_ph.markdown(full_txt + "▌")
                            res_ph.markdown(full_txt)
                            success = True
                            break
                        except Exception as e:
                            err_str = str(e)
                            is_rate = any(x in err_str for x in ["429", "quota", "RESOURCE_EXHAUSTED", "rate limit"])
                            is_overflow = any(x in err_str for x in ["400", "InvalidArgument", "token count exceeds", "maximum number of tokens"])
                            if is_overflow:
                                break
                            elif is_rate and attempt < 2:
                                time_module.sleep((2 ** attempt) * 3)
                            else:
                                break

                if not success:
                    res_ph.warning("⏳ Models are briefly at capacity. Please try again in a moment.")
                    return

                st.session_state[memory_key].append({"role": "user",  "display": q,        "internal": q})
                st.session_state[memory_key].append({"role": "model", "display": full_txt,  "internal": full_txt})

# ═══════════════════════════════════════════════════════════
# ORACLE
# ═══════════════════════════════════════════════════════════
def show_oracle():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🔮 The Oracle</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6)'>Mathematically locked AI prompts from Swiss Ephemeris precision.</p>",unsafe_allow_html=True)
    missions={"Deep Personal Analysis":"🔮 Full Life Reading",
              "Matchmaking / Compatibility":"✦ Compatibility Match",
              "Destiny & Marriage Chances":"💞 Marriage Chances Calculator",
              "Gochara / Live Transit":"🌍 Live Transit Analysis",
              "Comparison (Multiple Profiles)":"⚖ Compare Profiles",
              "Prashna Kundli":"🎯 Ask a Question"}
    descs={"Deep Personal Analysis":"Complete reading — personality, career, wealth, marriage, timing.",
           "Matchmaking / Compatibility":"Ashta Koota + Manglik + Compatibility.",
           "Destiny & Marriage Chances":"Advanced cross-chart confirmation matrix.",
           "Gochara / Live Transit":"How today's planets activate your natal chart right now.",
           "Comparison (Multiple Profiles)":"Rank multiple people with planetary evidence.",
           "Prashna Kundli":"Ask a specific question. Get Yes/No/Delayed."}
    cur=st.session_state.active_mission if st.session_state.active_mission in missions else "Deep Personal Analysis"
    cur_label=missions.get(cur,"🔮 Full Life Reading")
    sel_label=st.selectbox("Select Tool",list(missions.values()),index=list(missions.values()).index(cur_label),label_visibility="collapsed")
    mid=[k for k,v in missions.items() if v==sel_label][0]
    st.session_state.active_mission=mid
    st.markdown(f"<p style='color:rgba(190,185,210,.6);font-size:.88rem;margin-bottom:1.5rem'>{descs[mid]}</p><hr>",unsafe_allow_html=True)
    _run_oracle(mid)

def _run_oracle(mission):
    dp,_=get_default_profile()
    
    # ── PRASHNA ──
    if mission=="Prashna Kundli":
        question=st.text_area("Your question",placeholder="e.g. Will I get the job I applied for?")
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
                
        if st.button("Generate Prashna Reading ✨",type="primary",use_container_width=True):
            if not question.strip(): st.error("Enter a question."); return
            if not pr_man:
                geo=geocode_place(cur_place.strip())
                if not geo: st.error("Location not found."); return
                p_lat,p_lon,pn=geo; p_tz=timezone_for_latlon(p_lat,p_lon)
            else: p_lat,p_lon,p_tz,pn=prl,prn,prt,"Manual"
            now=datetime.now(ZoneInfo(p_tz))
            prof={"name":"Prashna","date":now.date().isoformat(),"time":now.strftime("%H:%M"),"place":pn,"lat":p_lat,"lon":p_lon,"tz":p_tz}
            with st.spinner("Casting chart..."): dos=generate_astrology_dossier(prof)
            st.session_state.prashna_prompt = build_prashna_prompt(question,dos)
            st.session_state.prashna_chat = [] # Clear memory
            
        if "prashna_prompt" in st.session_state:
            stream_ai_with_followup(st.session_state.prashna_prompt, "prashna_chat", "Answering your Prashna...")
        return

    # ── GOCHARA / TRANSIT ──
    if mission=="Gochara / Live Transit":
        st.markdown("#### Select your natal chart")
        item=render_profile_form("gochara",show_d60=False)
        if st.button("Analyse Live Transits ✨",type="primary",use_container_width=True):
            if item["type"]=="empty_saved": st.error("Select a profile."); return
            prof,d60=resolve_profile(item)
            with st.spinner("Overlaying transits..."):
                dos=generate_astrology_dossier(prof,d60); overlay=get_gochara_overlay(prof)
            st.session_state.transit_prompt = build_transit_prompt(dos,overlay)
            st.session_state.transit_chat = []
            
        if "transit_prompt" in st.session_state:
            stream_ai_with_followup(st.session_state.transit_prompt, "transit_chat", "Reading the stars...")
        return

    # ── MAIN ORACLE MODES ──
    req=1 if mission in ["Deep Personal Analysis"] else 2
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

    btn_labels={"Raw Data Only":"Generate Chart Data","Deep Personal Analysis":"Generate Full Reading ✨",
                "Matchmaking / Compatibility":"Generate Compatibility Match ✨","Comparison (Multiple Profiles)":"Compare Profiles ✨"}
    
    if st.button(btn_labels.get(mission,"Generate Prompt"),type="primary",use_container_width=True,key=f"gen_{mission}"):
        profiles=[]; d60s=[]
        for item in active:
            if item["type"]=="empty_saved": st.error("Fill all profile slots."); return
            prof,d60=resolve_profile(item); profiles.append(prof); d60s.append(d60)
        if len(profiles)<req: return
        compact=mission=="Comparison (Multiple Profiles)" and len(profiles)>3

        # Always reset history so a fresh reading is shown
        st.session_state[f"oracle_{mission}_history"] = []
        final = ""

        with st.spinner("Consulting the ephemeris..."):

            # ── DEEP PERSONAL ANALYSIS ──────────────────────────────
            if mission=="Deep Personal Analysis":
                dossier = generate_astrology_dossier(profiles[0], d60s[0])

                # STEP 1: Parallel agents read the dossier (no book files — dossier IS the data)
                # Why no books? Agents extract Python-computed facts (degrees, dignities, dashas).
                # The dossier already encodes what the books teach. Adding 100K-token books
                # on top causes token overflow AND adds noise, not accuracy.
                st.info("🧠 Firing Parallel AI Agents (Takes ~20s)...")
                expert_rules = "<ROLE>Elite Vedic Astrologer</ROLE><MATH_LOCK>Never alter, invent or estimate any number. Use only data present in the dossier.</MATH_LOCK>"
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    f_p = executor.submit(agent_worker, build_agent_parashari_prompt(dossier), [], FREE_MODELS[0], expert_rules)
                    f_t = executor.submit(agent_worker, build_agent_timing_prompt(dossier),    [], FREE_MODELS[0], expert_rules)
                    f_k = executor.submit(agent_worker, build_agent_kp_prompt(dossier),        [], FREE_MODELS[1], expert_rules)
                    p_notes, t_notes, k_notes = f_p.result(), f_t.result(), f_k.result()

                final = build_master_synthesizer_prompt(dossier, p_notes, t_notes, k_notes)

                # STEP 2: Synthesis with book knowledge.
                # htrh1.md = B.V. Raman Vol 1 (Houses 1-6, personality, practical examples).
                # 119K tokens — safely within Flash Lite's 250K TPM after 3 agent calls settle.
                time_module.sleep(3)
                st.info("📖 Writing your full reading...")
                try:
                    natal_book = get_knowledge_files(["htrh1.md"])
                    result = generate_content_with_fallback(final, knowledge_files=natal_book)
                except Exception as e:
                    result = (f"⚠️ Reading generation paused ({str(e)[:100]}). "
                              "Your chart data was computed successfully. Please try again in ~1 minute.")

                # Pre-populate history → stream_ai_with_followup just renders, NO extra API call
                st.session_state[f"oracle_{mission}_history"] = [
                    {"role": "user",  "parts": [final]},
                    {"role": "model", "parts": [result]},
                ]

            # ── MATCHMAKING ─────────────────────────────────────────
            elif mission=="Destiny & Marriage Chances":
                p_boy = profiles[0] if profiles[0].get('gender') == 'M' else profiles[1]
                p_girl = profiles[1] if p_boy == profiles[0] else profiles[0]
                if p_boy == p_girl: p_boy = profiles[0]; p_girl = profiles[1] # fallback
                p_boy_idx = profiles.index(p_boy)
                p_girl_idx = profiles.index(p_girl)
                
                st.info("Crunching Jaimini & D9 matrices...")
                jda, _, _ = local_to_julian_day(date.fromisoformat(p_boy['date']) if isinstance(p_boy['date'], str) else p_boy['date'], datetime.strptime(p_boy['time'], "%H:%M").time() if isinstance(p_boy['time'], str) else p_boy['time'], p_boy['tz'])
                jdb, _, _ = local_to_julian_day(date.fromisoformat(p_girl['date']) if isinstance(p_girl['date'], str) else p_girl['date'], datetime.strptime(p_girl['time'], "%H:%M").time() if isinstance(p_girl['time'], str) else p_girl['time'], p_girl['tz'])
                
                dos_a = generate_astrology_dossier(p_boy, d60s[p_boy_idx])
                dos_b = generate_astrology_dossier(p_girl, d60s[p_girl_idx])
                
                dest_data = calculate_destiny_confirmation(p_boy, p_girl, jda, jdb, dos_a, dos_b)
                
                final = build_destiny_confirmation_prompt(p_boy, p_girl, dos_a, dos_b, dest_data)
                
                st.info("📖 Generating Destiny Marriage Matrix...")
                marriage_book = get_knowledge_files(["htrh2.md"])
                result = generate_content_with_fallback(final, knowledge_files=marriage_book)
                if result:
                    # Update session state with the result, removing markdown rendering here so stream_ai_with_followup handles it
                    st.session_state[f"oracle_{mission}_history"] = [
                        {"role": "user",  "parts": [final]},
                        {"role": "model", "parts": [result]},
                    ]
            elif mission=="Matchmaking / Compatibility":
                # Ensure Gender is explicit
                p_boy = profiles[0] if profiles[0].get('gender') == 'M' else profiles[1]
                p_girl = profiles[1] if p_boy == profiles[0] else profiles[0]
                if p_boy == p_girl: p_boy = profiles[0]; p_girl = profiles[1] # fallback
                
                ma = get_moon_lon_from_profile(p_boy); mb = get_moon_lon_from_profile(p_girl)
                
                jda, dtla, _ = local_to_julian_day(date.fromisoformat(p_boy['date']), datetime.strptime(p_boy['time'], "%H:%M").time(), p_boy['tz'])
                pla = {pn: get_planet_longitude_and_speed(jda, pid) for pn, pid in PLANETS.items()}
                laga = sign_index_from_lon(get_lagna_and_cusps(jda, p_boy['lat'], p_boy['lon'])[0])
                ma_d = check_manglik_dosha(laga, sign_index_from_lon(pla["Moon"][0]), sign_index_from_lon(pla["Mars"][0]))
                
                jdb, dtlb, _ = local_to_julian_day(date.fromisoformat(p_girl['date']), datetime.strptime(p_girl['time'], "%H:%M").time(), p_girl['tz'])
                plb = {pn: get_planet_longitude_and_speed(jdb, pid) for pn, pid in PLANETS.items()}
                lagb = sign_index_from_lon(get_lagna_and_cusps(jdb, p_girl['lat'], p_girl['lon'])[0])
                mb_d = check_manglik_dosha(lagb, sign_index_from_lon(plb["Moon"][0]), sign_index_from_lon(plb["Mars"][0]))
                
                canc = get_manglik_cancellation_verdict(ma_d, mb_d)
                
                dos_a = generate_astrology_dossier(p_boy, d60s[profiles.index(p_boy)])
                dos_b = generate_astrology_dossier(p_girl, d60s[profiles.index(p_girl)])
                
                koota_data, marital_a, marital_b, kp_a, kp_b = calculate_matchmaking_synastry(p_boy, p_girl, ma, mb, jda, jdb, dos_a, dos_b)
                
                final = build_matchmaking_prompt(
                    dos_a, dos_b, koota_data, canc, p_boy, p_girl, marital_a, marital_b, kp_a, kp_b
                )

                st.info("📖 Generating compatibility reading...")
                try:
                    # htrh2.md = B.V. Raman Vol 2 (Houses 7-12: marriage, relationships, partners).
                    # Most targeted book for compatibility — entire Vol 2 is marriage/partnership focused.
                    marriage_book = get_knowledge_files(["htrh2.md"])
                    result = generate_content_with_fallback(final, knowledge_files=marriage_book)
                except Exception as e:
                    result = f"⚠️ Reading paused ({str(e)[:100]}). Please try again in ~1 minute."
                st.session_state[f"oracle_{mission}_history"] = [
                    {"role": "user",  "parts": [final]},
                    {"role": "model", "parts": [result]},
                ]

            # ── COMPARISON ──────────────────────────────────────────
            elif mission=="Comparison (Multiple Profiles)":
                if not selected_criteria: st.warning("Select at least one criterion."); return
                pairs=[(p['name'],generate_astrology_dossier(p,d,compact)) for p,d in zip(profiles,d60s)]
                final=build_comparison_prompt(pairs,selected_criteria)

                st.info("📖 Comparing profiles...")
                try:
                    # htrh1.md = Raman Vol 1 — practical house strength and planetary dignity rules.
                    # Comparison needs to know what makes a planet/house strong, which this book explains.
                    compare_book = get_comparison_reference_digest()
                    result = generate_content_with_fallback(final, knowledge_files=compare_book)
                except Exception as e:
                    result = f"⚠️ Reading paused ({str(e)[:100]}). Please try again in ~1 minute."
                st.session_state[f"oracle_{mission}_history"] = [
                    {"role": "user",  "parts": [final]},
                    {"role": "model", "parts": [result]},
                ]

        # Store prompt for follow-up context (Prashna/Transit set their own prompts elsewhere)
        if final:
            st.session_state[f"oracle_prompt_{mission}"] = final

    # ── RENDER: show result + follow-up chat box ─────────────────────
    # • Deep Analysis / Matchmaking / Comparison: history is pre-populated above.
    #   stream_ai_with_followup sees history already filled → just renders, zero extra API call.
    # • Prashna / Transit: history is empty, stream_ai_with_followup makes ONE call (with books).
    if f"oracle_prompt_{mission}" in st.session_state:
        if mission == "Prashna Kundli":
            # kp6.md = KP Horary Astrology exclusively — the ONLY book needed for Prashna.
            # kp2.md (KP fundamentals) is useful background but kp6 covers all practical horary rules.
            # Removing kp2 saves ~184K tokens → stays well under 250K TPM.
            oracle_files = get_knowledge_files(["kp6.md"])
        elif mission == "Gochara / Live Transit":
            # iva.md = best single book for transit analysis — covers Ashtakavarga transits,
            # nakshatra transits, divisional chart transits, and Tajaka. Modern and comprehensive.
            # Removing bphs2.md saves ~335K tokens → prevents TPM overflow.
            oracle_files = get_knowledge_files(["iva.md"])
        else:
            # History already has the answer — no files needed, just render + follow-up
            oracle_files = None

        stream_ai_with_followup(
            st.session_state[f"oracle_prompt_{mission}"],
            f"oracle_{mission}_history",
            "The Master Astrologer is writing...",
            knowledge_files=oracle_files
        )


# ═══════════════════════════════════════════════════════════
# TAROT — Fully rewritten with working animations, all modes
# ═══════════════════════════════════════════════════════════
def show_tarot():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🃏 Mystic Tarot</h1>",unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(255,255,255,.6)'>Ask a question and consult the cards. Cryptographically secure randomisation.</p>",unsafe_allow_html=True)

    tab_choice=st.radio("Mode",["✦ Three-Card Spread","☯ Yes / No Oracle","🔮 Celtic Cross (10 Cards)","🌟 Birth Card"],
                        horizontal=True,key="tarot_mode_radio",label_visibility="collapsed")

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
        rev=st.checkbox("Include Reversed Cards",key="t3_rev",help=tarot_reversed_help())
        
        if st.button("Draw 3 Cards",type="primary",use_container_width=True,key="draw3"):
            if not q.strip(): st.error("Ask a question first."); return
            with st.spinner("Shuffling..."): time_module.sleep(1.2)
            rng=secrets.SystemRandom(); st.session_state.tarot3_cards=rng.sample(FULL_TAROT_DECK,3)
            st.session_state.tarot3_states=[rng.choice(["Upright","Reversed"]) if rev else "Upright" for _ in range(3)]
            st.session_state.tarot3_drawn=True; st.session_state.tarot3_mode=spread_mode
            st.session_state.tarot3_chat = [] # Clear old chat history
            
        if st.session_state.tarot3_drawn and st.session_state.tarot3_cards:
            render_tarot_overlay(st.session_state.tarot3_cards,st.session_state.tarot3_states,"three")
            st.markdown(f"**Cards:** {' · '.join(f'{c} ({s})' for c,s in zip(st.session_state.tarot3_cards,st.session_state.tarot3_states))}")
            prompt=build_tarot_prompt(q,st.session_state.tarot3_cards,st.session_state.tarot3_states,st.session_state.tarot3_mode)
            
            stream_ai_with_followup(prompt, "tarot3_chat", "Interpreting the cards...", knowledge_files=get_knowledge_files(["tguide.md"]))
            
            if st.button("🔄 New Reading",key="reset3"):
                st.session_state.tarot3_drawn=False; st.session_state.tarot3_cards=[]; st.rerun()

    # ── YES / NO ORACLE ──
    elif "Yes / No" in tab_choice:
        q=st.text_input("Your yes/no question",placeholder="e.g. Will this situation resolve in my favour?",key="yn_q")
        rev=st.checkbox("Include Reversed Cards",key="yn_rev",help=tarot_reversed_help())
        
        if st.button("Draw One Card",type="primary",use_container_width=True,key="draw_yn"):
            if not q.strip(): st.error("Ask a question."); return
            rng=secrets.SystemRandom(); st.session_state.yn_card=rng.choice(FULL_TAROT_DECK)
            st.session_state.yn_state="Upright" if not rev else rng.choice(["Upright","Reversed"])
            st.session_state.yn_drawn=True
            st.session_state.yn_chat = [] # Clear old chat history
            
        if st.session_state.yn_drawn and st.session_state.yn_card:
            render_tarot_overlay([st.session_state.yn_card],[st.session_state.yn_state],"one")
            st.markdown(f"**Card:** {st.session_state.yn_card} ({st.session_state.yn_state})")
            
            stream_ai_with_followup(build_yesno_prompt(q,st.session_state.yn_card,st.session_state.yn_state), "yn_chat", "Sensing the answer...", knowledge_files=get_knowledge_files(["tguide.md"]))
            
            if st.button("🔄 Ask Again",key="reset_yn"):
                st.session_state.yn_drawn=False; st.session_state.yn_card=None; st.rerun()

    # ── CELTIC CROSS ──
    elif "Celtic Cross" in tab_choice:
        q=st.text_area("Your question (optional)",placeholder="e.g. What do I need to know about the next chapter of my life?",key="cc_q")
        rev=st.checkbox("Include Reversed Cards",key="cc_rev",help=tarot_reversed_help())
        
        if st.button("Draw 10 Cards",type="primary",use_container_width=True,key="draw_cc"):
            with st.spinner("Laying out the Celtic Cross..."): time_module.sleep(1.5)
            rng=secrets.SystemRandom(); st.session_state.cc_cards=rng.sample(FULL_TAROT_DECK,10)
            st.session_state.cc_states=["Upright" if not rev else rng.choice(["Upright","Reversed"]) for _ in range(10)]
            st.session_state.cc_drawn=True
            st.session_state.cc_chat = [] # Clear old chat history
            
        if st.session_state.cc_drawn and st.session_state.cc_cards:
            render_tarot_overlay(st.session_state.cc_cards,st.session_state.cc_states,"ten")
            for i,(c,s) in enumerate(zip(st.session_state.cc_cards,st.session_state.cc_states)):
                st.markdown(f"**{CELTIC_CROSS_POSITIONS[i]}:** {c} ({s})")
            prompt=build_celtic_cross_prompt(q or "General life overview",st.session_state.cc_cards,st.session_state.cc_states)
            
            stream_ai_with_followup(prompt, "cc_chat", "Weaving the narrative...", knowledge_files=get_knowledge_files(["tguide.md"]))
            
            if st.button("🔄 New Celtic Cross",key="reset_cc"):
                st.session_state.cc_drawn=False; st.session_state.cc_cards=[]; st.rerun()

    # ── BIRTH CARD ──
    elif "Birth Card" in tab_choice:
        st.markdown("#### Your Tarot Birth Card")
        st.caption("A permanent card determined by your date of birth — it represents your soul's archetype and lifelong theme.")
        bc_dob=st.date_input("Date of Birth",date(2000,1,1),min_value=date(1850,1,1),max_value=date(2050,12,31),key="bc_dob_input")
        
        if st.button("Reveal My Birth Card",type="primary",use_container_width=True,key="reveal_bc"):
            st.session_state.bc_dob=bc_dob; st.session_state.bc_revealed=True
            st.session_state.bc_chat = [] # Clear old chat history
            
        if st.session_state.bc_revealed and st.session_state.bc_dob:
            card=get_tarot_birth_card(st.session_state.bc_dob.isoformat())
            render_tarot_overlay([card],["Upright"],"one")
            st.markdown(f"**Your Birth Card:** {card}")
            st.caption("This card never changes — it is your permanent soul archetype.")
            
            stream_ai_with_followup(build_birth_card_prompt(card,str(st.session_state.bc_dob)), "bc_chat", "Unlocking archetype...", knowledge_files=get_knowledge_files(["tguide.md"]))
            
            if st.button("🔄 Check Another Date",key="reset_bc"):
                st.session_state.bc_revealed=False; st.rerun()
                

# ═══════════════════════════════════════════════════════════
# HOROSCOPES
# ═══════════════════════════════════════════════════════════
def show_horoscopes():
    components.html("""<script>setTimeout(function(){var b=window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');if(b&&window.parent.innerWidth<=768)b.click();},80);</script>""",height=0,width=0)
    st.markdown("<h1>🌟 Horoscopes</h1>",unsafe_allow_html=True)
    
    dp,_ = get_default_profile()
    user_tz = dp['tz'] if dp else "Asia/Kolkata"
    today = get_local_today(user_tz)
    today_str = today.isoformat()
    
    t1,t2 = st.tabs(["☀️ Western (Sun Sign)","🌙 Vedic (Moon Sign)"])
    
    with t1:
        dob = st.date_input("Date of Birth", date(2000,1,1), min_value=date(1850,1,1), max_value=date(2050,12,31), key="h_w_dob")
        
        if st.button("Calculate Daily Forecast", type="primary", key="w_btn"):
            sun_sign = get_western_sign(dob.month, dob.day)
            st.success(f"Your Sun Sign: **{sun_sign}**")
            
            with st.spinner("Analyzing live tropical transits..."):
                # Strictly daily forecast for Western
                western_reading = generate_western_forecast(sun_sign, today_str)
                st.markdown("### ☀️ Daily Western Forecast")
                st.markdown(western_reading)
                
    with t2:
        item = render_profile_form("vedic_horo", show_d60=False)
        
        if st.button("Calculate Vedic Forecasts", type="primary", key="v_btn"):
            if item["type"] == "empty_saved": 
                st.error("Select or enter a profile.")
            else:
                prof, _ = resolve_profile(item)
                moon_lon = get_moon_lon_from_profile(prof)
                moon_sidx = sign_index_from_lon(moon_lon)
                sign_n = sign_name(moon_sidx)
                nak, _, _ = nakshatra_info(moon_lon)
                
                st.success(f"Your Rashi (Moon Sign): **{sign_n}** | Birth Star: **{nak}**")
                
                with st.spinner("Calculating exact future planetary positions..."):
                    prof_json = json.dumps(prof, sort_keys=True)
                    
                    pt1, pt2, pt3 = st.tabs(["Daily", "Monthly", "Yearly"])
                    with pt1: 
                        st.write(generate_vedic_forecast(prof_json, "Daily", today_str))
                    with pt2: 
                        st.write(generate_vedic_forecast(prof_json, "Monthly", today_str))
                    with pt3: 
                        st.write(generate_vedic_forecast(prof_json, "Yearly", today_str))

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
            with c2: pre_dob=date.fromisoformat(dp['date']) if dp else date(2000,1,1); num_dob=st.date_input("Date of Birth",pre_dob,min_value=date(1850,1,1),max_value=date(2050,12,31),key="num_dob")
            
        if st.button("Generate Numerology Report ✨",type="primary",use_container_width=True):
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
            
            st.session_state.num_prompt = build_numerology_prompt(name,dob_str,lp,dest,soul,pers,dossier,question,system)
            st.session_state.num_chat = [] # Clear memory for a fresh chat
            
        if "num_prompt" in st.session_state:
            # Dynamically select files based on the chosen system
            if "Vedic" in system:
                num_files = get_knowledge_files(["inum1.md", "inum2.md"])
            else:
                num_files = get_knowledge_files(["wnum.md"])
                
            stream_ai_with_followup(st.session_state.num_prompt, "num_chat", "Analysing your numbers...", knowledge_files=num_files)
            
    with tab2:
        st.markdown("#### Personal Cycles & Pinnacle Challenges")
        st.caption("Understand the numerical timing of your life phases — including the obstacles built into each cycle.")
        sys3=st.radio("System",["Western (Pythagorean)","Indian/Vedic (Chaldean)"],horizontal=True,key="cyc_sys")
        c1,c2=st.columns(2)
        with c1: cyc_name=st.text_input("Full Birth Name",value=dp['name'] if dp else "",key="cyc_name")
        with c2: pre_dob=date.fromisoformat(dp['date']) if dp else date(2000,1,1); cyc_dob=st.date_input("Date of Birth",pre_dob,min_value=date(1850,1,1),max_value=date(2050,12,31),key="cyc_dob")
        
        if st.button("Show My Cycles ✨",type="primary",use_container_width=True):
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
                badge_html = f"<span style='color:#c09040'>{badge}</span>" if badge else ""
                col.markdown(f"**Pinnacle {i}** (Ages {s-y}–{e-y if e-y < 100 else '∞'}) &nbsp; {badge_html}", unsafe_allow_html=True)
                col.write(f"**Pinnacle Number: {n}** — {PERSONAL_YEAR_MEANINGS.get(n,'')}")
                col.write(f"**Challenge Number: {c}** — {'Master your need for control and ego.' if c==1 else 'Overcome fear of confrontation and indecision.' if c==2 else 'Build self-discipline to channel your emotions.' if c==3 else 'Learn to work within limitations patiently.' if c==4 else 'Ground your need for constant change and freedom.' if c==5 else 'Release perfectionism and learn to receive.' if c==6 else 'Trust yourself without constant external validation.' if c==7 else 'Balance material ambition with spiritual values.' if c==8 else 'Complete cycles; resist clinging to the past.' if c==9 else 'Own your spiritual sensitivity as a gift.'}")
            
            is_vedic="Vedic" in sys3
            prompt=f"""<instructions>
You are a Master Numerologist — {'Chaldean (Indian/Vedic)' if is_vedic else 'Pythagorean (Western)'} system.
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
            st.session_state.cyc_prompt = prompt
            st.session_state.cyc_chat = []
            
        if "cyc_prompt" in st.session_state:
            # Dynamically select files based on the chosen system
            if "Vedic" in sys3:
                num_files = get_knowledge_files(["inum1.md", "inum2.md"])
            else:
                num_files = get_knowledge_files(["wnum.md"])
                
            stream_ai_with_followup(st.session_state.cyc_prompt, "cyc_chat", "Interpreting life cycles...", knowledge_files=num_files)
            

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
                gnd = p.get('gender', 'M')
                st.markdown(f"""<div class="prof-card {'prof-card-def' if is_def else 'prof-card-norm'}">
{badge_html}<p class="prof-name">{p['name']} ({gnd})</p>
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
            pre_gnd = pd_.get('gender', 'M')
            u_gender = st.radio("Gender", ["M", "F"], index=0 if pre_gnd=='M' else 1, key="ve_gnd", horizontal=True)
            u_exact = st.checkbox("Exact Time Known", value=pd_.get('exact_time', False), key="ve_exact")
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
            st.session_state.db[ei]={"name":u_name,"date":u_date.isoformat(),"time":time(h24,u_mi).strftime("%H:%M"),"place":fp2,"lat":fl2,"lon":fln2,"tz":ftz2, "gender": u_gender, "exact_time": u_exact}
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
                v_n=st.text_input("Name",key="v_new_n"); v_d=st.date_input("Date of Birth",date(2000,1,1),min_value=date(1850,1,1),max_value=date(2050,12,31),key="v_new_d")
                t1,t2,t3=st.columns(3)
                with t1: v_h=st.number_input("Hour",1,12,12,key="v_new_h")
                with t2: v_m=st.number_input("Min",0,59,0,key="v_new_m")
                with t3: v_a=st.selectbox("AM/PM",["AM","PM"],index=1,key="v_new_a")
                v_gender = st.radio("Gender", ["M", "F"], index=0, key="v_new_gnd", horizontal=True)
                v_exact = st.checkbox("Exact Time Known", value=False, key="v_new_exact")
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
                new_prof={"name":v_n.strip(),"date":v_d.isoformat(),"time":time(h24,v_m).strftime("%H:%M"),"place":pn,"lat":lat,"lon":lon,"tz":tz, "gender": v_gender, "exact_time": v_exact}
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


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
inject_nebula_css()
render_sidebar()
render_bottom_nav()  # <--- MOVED HERE SO IT LOADS INSTANTLY!

page=st.session_state.nav_page
if   page=="Dashboard":      show_dashboard()
elif page=="Consultation Room": show_consultation_room() 
elif page=="The Oracle":     show_oracle()
elif page=="Mystic Tarot":   show_tarot()
elif page=="Horoscopes":     show_horoscopes()
elif page=="Numerology":     show_numerology()
elif page=="Saved Profiles": show_vault()

# ═══════════════════════════════════════════════════════════
# ORIGINAL WORKING SYNC ENGINE (UNIQUE KEYS FIX)
# ═══════════════════════════════════════════════════════════
if st.session_state.get('needs_sync', False):
    # Pass a unique key to the first save command
    localS.setItem("kundli_vault", json.dumps(st.session_state.db), key="save_vault_data")
    
    # Pass a different unique key to the second save command
    if st.session_state.default_profile_idx is not None:
        localS.setItem("kundli_default", str(st.session_state.default_profile_idx), key="save_default_data")
    else:
        localS.setItem("kundli_default", "", key="clear_default_data")
        
    st.session_state.needs_sync = False
