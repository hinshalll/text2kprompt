from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from streamlit_local_storage import LocalStorage

# ------------------------------------------------------------
# App config & Constants
# ------------------------------------------------------------
st.set_page_config(page_title="Kundli AI Master Suite", page_icon="🪐", layout="wide")

try:
    swe.set_ephe_path("ephe")
except Exception:
    pass

swe.set_sid_mode(swe.SIDM_LAHIRI)

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
PLANETS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
DIGNITIES = {"Sun": (0, 6), "Moon": (1, 7), "Mars": (9, 3), "Mercury": (5, 11), "Jupiter": (3, 9), "Venus": (11, 5), "Saturn": (6, 0)}
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
NAKSHATRA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] * 3
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
YEAR_DAYS = 365.2425
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}

COMPARISON_CRITERIA = [
    "Wealth potential (who will become the richest)",
    "Lifetime wealth (who will die the richest)",
    "Overall life satisfaction and happiness",
    "Saddest or most difficult life",
    "Best life partner potential (marriage quality)",
    "Physical appearance and personality",
    "Luck (most fortunate)",
    "Unluckiest (most challenges/obstacles)",
    "Health and longevity",
    "Spiritual purity / aura (positive energy presence)"
]

# ------------------------------------------------------------
# State Management & Local Storage Bridge
# ------------------------------------------------------------
localS = LocalStorage()

if 'db_loaded' not in st.session_state:
    with st.spinner("Initializing..."):
        saved_data = localS.getItem("kundli_vault")
        st.session_state.db = saved_data if saved_data else []
        st.session_state.db_loaded = True

if 'needs_sync' not in st.session_state:
    st.session_state.needs_sync = False

if st.session_state.needs_sync:
    localS.setItem("kundli_vault", st.session_state.db)
    st.session_state.needs_sync = False

if 'custom_criteria' not in st.session_state:
    st.session_state.custom_criteria = []
if 'editing_idx' not in st.session_state:
    st.session_state.editing_idx = None
if 'comp_slots' not in st.session_state:
    st.session_state.comp_slots = 2

def sync_db():
    st.session_state.needs_sync = True

def is_duplicate_in_db(new_p):
    for p in st.session_state.db:
        if p['name'] == new_p['name'] and p['date'] == new_p['date']:
            return True
    return False

def format_date_ui(iso_date_str):
    """Converts YYYY-MM-DD to Indian format DD-MM-YYYY for UI display"""
    return datetime.fromisoformat(iso_date_str).strftime('%d-%m-%Y')

# ------------------------------------------------------------
# Calculation Helpers 
# ------------------------------------------------------------
def sign_name(sign_index: int) -> str: return SIGNS[sign_index % 12]
def sign_index_from_lon(lon: float) -> int: return int(lon // 30) % 12

def format_dms(angle: float) -> str:
    angle %= 360
    deg = int(angle)
    minutes_float = (angle - deg) * 60
    minute = int(minutes_float)
    second = int(round((minutes_float - minute) * 60))
    if second == 60: second, minute = 0, minute + 1
    if minute == 60: minute, deg = 0, deg + 1
    return f"{deg:03d}°{minute:02d}'{second:02d}\""

def sign_and_deg(lon: float) -> str:
    return f"{sign_name(sign_index_from_lon(lon))} {format_dms(lon % 30)}"

def nakshatra_info(lon: float) -> tuple[str, str, int]:
    nak_span = 360 / 27
    idx = int((lon % 360) // nak_span)
    return NAKSHATRAS[idx], NAKSHATRA_LORDS[idx], int(((lon % 360 % nak_span) // (nak_span / 4))) + 1

def navamsa_sign_index(lon: float) -> int:
    s_idx = sign_index_from_lon(lon)
    slot = int((lon % 360 % 30) // (30 / 9))
    start = s_idx if s_idx in MOVABLE_SIGNS else ((s_idx + 8) % 12 if s_idx in FIXED_SIGNS else (s_idx + 4) % 12)
    return (start + slot) % 12

def dasamsa_sign_index(lon: float) -> int:
    s_idx = sign_index_from_lon(lon)
    slot = int((lon % 360 % 30) // 3)
    start = s_idx if s_idx % 2 == 0 else (s_idx + 8) % 12
    return (start + slot) % 12

def whole_sign_house(lagna_sign_idx: int, planet_sign_idx: int) -> int:
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1

@st.cache_data(show_spinner=False)
def geocode_place(place_text: str):
    try:
        loc = Nominatim(user_agent="kundli_ai_suite").geocode(place_text, exactly_one=True, timeout=10)
        return (loc.latitude, loc.longitude, loc.address) if loc else None
    except: return None

@st.cache_data(show_spinner=False)
def timezone_for_latlon(lat: float, lon: float):
    return TimezoneFinder().timezone_at(lat=lat, lng=lon)

def local_to_julian_day(d: date, t: time, tz_name: str):
    local_zone = ZoneInfo(tz_name)
    dt_local = datetime.combine(d, t).replace(tzinfo=local_zone)
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    ut_hrs = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_hrs), dt_local, dt_utc

def get_lagna_longitude(jd_ut: float, lat: float, lon: float) -> float:
    _, ascmc = swe.houses(jd_ut, lat, lon, b"P")
    return (float(ascmc[0]) - swe.get_ayanamsa_ut(jd_ut)) % 360

def get_planet_longitude(jd_ut: float, planet_id: int) -> float:
    res, _ = swe.calc_ut(jd_ut, planet_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return float(res[0]) % 360

def get_planet_speed(jd_ut: float, planet_id: int) -> float:
    res, _ = swe.calc_ut(jd_ut, planet_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return float(res[3])

def get_rahu_longitude(jd_ut: float) -> float:
    res, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return float(res[0]) % 360

def build_vimshottari_timeline(dt_birth: datetime, moon_lon: float, dt_now: datetime):
    nak_span = 360 / 27
    idx = int((moon_lon % 360) // nak_span)
    lord = NAKSHATRA_LORDS[idx]
    balance = DASHA_YEARS[lord] * (1 - ((moon_lon % 360 % nak_span) / nak_span))
    s_idx = DASHA_ORDER.index(lord)
    seq = DASHA_ORDER[s_idx:] + DASHA_ORDER[:s_idx]
    
    dt_cursor = dt_birth
    md_list = [(seq[0], balance)] + [(l, DASHA_YEARS[l]) for l in seq[1:]]
    for md_lord, md_yrs in md_list:
        next_md = dt_cursor + timedelta(days=md_yrs * YEAR_DAYS)
        if dt_now < next_md:
            ad_cursor = dt_cursor
            ad_seq = DASHA_ORDER[DASHA_ORDER.index(md_lord):] + DASHA_ORDER[:DASHA_ORDER.index(md_lord)]
            for ad_lord in ad_seq:
                ad_yrs = (md_yrs * DASHA_YEARS[ad_lord]) / 120.0
                next_ad = ad_cursor + timedelta(days=ad_yrs * YEAR_DAYS)
                if dt_now < next_ad:
                    return {"birth_nakshatra": NAKSHATRAS[idx], "start_lord": lord, "balance_years": balance, 
                            "current_md": md_lord, "current_ad": ad_lord, "md_start": dt_cursor, 
                            "md_end": next_md, "ad_start": ad_cursor, "ad_end": next_ad}
                ad_cursor = next_ad
        dt_cursor = next_md
    return {"birth_nakshatra": "Unknown", "start_lord": "Unknown", "balance_years": 0, "current_md": "Unknown", "current_ad": "Unknown", "md_start": datetime.now(), "md_end": datetime.now(), "ad_start": datetime.now(), "ad_end": datetime.now()}

def years_to_ymd(years: float) -> str:
    whole_days = int(max(0.0, years) * YEAR_DAYS)
    return f"{whole_days // 365}y {(whole_days % 365) // 30}m {(whole_days % 365) % 30}d"

# ------------------------------------------------------------
# CORE PROFILE GENERATOR STRING
# ------------------------------------------------------------
def generate_profile_text(profile):
    lat, lon, tz_name, name, place_text = profile['lat'], profile['lon'], profile['tz'], profile['name'], profile['place']
    
    prof_date = date.fromisoformat(profile['date']) if isinstance(profile['date'], str) else profile['date']
    prof_time = datetime.strptime(profile['time'], "%H:%M").time() if isinstance(profile['time'], str) else profile['time']
    
    jd_ut, dt_local, dt_utc = local_to_julian_day(prof_date, prof_time, tz_name)
    lagna_lon = get_lagna_longitude(jd_ut, lat, lon)
    
    planet_lons = {pname: get_planet_longitude(jd_ut, pid) for pname, pid in PLANETS.items()}
    planet_lons["Rahu"] = get_rahu_longitude(jd_ut)
    planet_speeds = {pname: get_planet_speed(jd_ut, pid) for pname, pid in PLANETS.items()}
    
    dasha_info = build_vimshottari_timeline(dt_local, planet_lons["Moon"], datetime.now(ZoneInfo(tz_name)))
    lagna_sign = sign_name(sign_index_from_lon(lagna_lon))
    lagna_dms = format_dms(lagna_lon % 30)

    d1_lines = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        plon = planet_lons[pname]
        sidx = sign_index_from_lon(plon)
        nak, nak_lord, pada = nakshatra_info(plon)
        house = whole_sign_house(sign_index_from_lon(lagna_lon), sidx)
        
        status_labels = []
        if planet_speeds.get(pname, 0) < 0 and pname not in ["Sun", "Moon"]: status_labels.append("Retrograde")
        if pname != "Sun":
            if abs(plon - planet_lons["Sun"]) < 8.5 or abs(plon - planet_lons["Sun"]) > 351.5: status_labels.append("Combust")
        if pname in DIGNITIES:
            if sidx == DIGNITIES[pname][0]: status_labels.append("Exalted")
            elif sidx == DIGNITIES[pname][1]: status_labels.append("Debilitated")
                
        status_str = f" ({', '.join(status_labels)})" if status_labels else ""
        d1_lines.append(f"{pname}: {sign_and_deg(plon)}{status_str} | Nakshatra: {nak} (Lord: {nak_lord}, Pada: {pada}) | House: {house}")

    r_lon = planet_lons["Rahu"]
    k_lon = (r_lon + 180.0) % 360
    for pname, plon in [("Rahu", r_lon), ("Ketu", k_lon)]:
        sidx = sign_index_from_lon(plon)
        nak, nak_lord, pada = nakshatra_info(plon)
        house = whole_sign_house(sign_index_from_lon(lagna_lon), sidx)
        d1_lines.append(f"{pname}: {sign_and_deg(plon)} (Retrograde) | Nakshatra: {nak} (Lord: {nak_lord}, Pada: {pada}) | House: {house}")

    d9_lines, d10_lines = [], []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        plon = planet_lons[pname] if pname != "Ketu" else k_lon
        d9_lines.append(f"{pname}: {sign_name(navamsa_sign_index(plon))}")
        d10_lines.append(f"{pname}: {sign_name(dasamsa_sign_index(plon))}")

    lines = [
        f"BIRTH DATA:",
        f"- Name: {name}", f"- Place: {place_text}", f"- Latitude: {lat:.6f}", f"- Longitude: {lon:.6f}",
        f"- Timezone: {tz_name}", f"- Birth Time (local): {dt_local.strftime('%d %b %Y, %I:%M %p')}",
        f"- Birth Time (UTC): {dt_utc.strftime('%d %b %Y, %H:%M UTC')}", "",
        f"D1 / RASI CHART:\nAscendant (Lagna): {lagna_sign} {lagna_dms}", "\n".join(d1_lines), "",
        f"D9 / NAVAMSA CHART:\n" + ", ".join(d9_lines), "",
        f"D10 / DASAMSA CHART:\n" + ", ".join(d10_lines), "",
        f"VIMSHOTTARI DASHA:",
        f"Birth Nakshatra: {dasha_info['birth_nakshatra']}", f"Start Mahadasha Lord at Birth: {dasha_info['start_lord']}",
        f"Mahadasha Balance at Birth: {dasha_info['balance_years']:.2f} years (~{years_to_ymd(dasha_info['balance_years'])})",
        f"Current Mahadasha: {dasha_info['current_md']} ({dasha_info['md_start'].year}-{dasha_info['md_end'].year})",
        f"Current Antardasha: {dasha_info['current_ad']} ({dasha_info['ad_start'].strftime('%b %Y')} to {dasha_info['ad_end'].strftime('%b %Y')})"
    ]
    return "\n".join(lines)


# ------------------------------------------------------------
# UI - SECTION 1: AI MISSION CONTROL
# ------------------------------------------------------------
st.title("🪐 Vedic AI Master Suite")

st.markdown("### 1. Select AI Mission")
mission = st.radio("Choose your goal:", ["Raw Data Only", "Deep Personal Analysis", "Matchmaking / Compatibility", "Comparison (Multiple Profiles)"], horizontal=True, label_visibility="collapsed")

if mission in ["Raw Data Only", "Deep Personal Analysis"]: 
    req_profiles = 1
elif mission == "Matchmaking / Compatibility": 
    req_profiles = 2
else: 
    req_profiles = 2 

num_slots = st.session_state.comp_slots if mission == "Comparison (Multiple Profiles)" else req_profiles

st.markdown("---")
st.markdown("### 2. Enter or Select Details")

active_profiles_data = [] 

# Render Dynamic Slots
for i in range(num_slots):
    st.markdown(f"#### Profile {i+1}")
    
    if len(st.session_state.db) > 0:
        input_method = st.radio(f"Input Source for Profile {i+1}", ["📝 Enter New Details", "📚 Select from Address Book"], horizontal=True, key=f"method_{i}", label_visibility="collapsed")
    else:
        input_method = "📝 Enter New Details"

    with st.container(border=True):
        if input_method == "📝 Enter New Details":
            c1, c2 = st.columns(2)
            with c1:
                st.session_state[f"n_{i}"] = st.text_input("Name", key=f"w_n_{i}", autocomplete="name")
                st.session_state[f"d_{i}"] = st.date_input("Date of birth", date(2000, 1, 1), format="DD/MM/YYYY", key=f"w_d_{i}")
                t1, t2, t3 = st.columns(3)
                with t1: st.session_state[f"hr_{i}"] = st.number_input("Hour", 1, 12, 12, key=f"w_hr_{i}")
                with t2: st.session_state[f"mi_{i}"] = st.number_input("Minute", 0, 59, 0, key=f"w_mi_{i}")
                with t3: st.session_state[f"ampm_{i}"] = st.selectbox("AM/PM", ["AM", "PM"], index=1, key=f"w_ampm_{i}")
            with c2:
                u_place = st.text_input("Birth Place (City, State, Country)", key=f"w_p_{i}")
                st.session_state[f"p_{i}"] = u_place
                
                if u_place.strip() and not st.session_state.get(f"w_man_{i}", False):
                    geo = geocode_place(u_place.strip())
                    if geo:
                        st.success(f"📍 Auto-detected: {geo[0]:.4f}, {geo[1]:.4f}")
                    else:
                        st.warning("⚠️ Location not found. Please check spelling or use manual coordinates below.")

                manual = st.checkbox("Manual Coordinates", key=f"w_man_{i}")
                st.session_state[f"man_{i}"] = manual
                if manual:
                    st.session_state[f"lat_{i}"] = st.number_input("Latitude", value=0.0, format="%.4f", key=f"w_lat_{i}")
                    st.session_state[f"lon_{i}"] = st.number_input("Longitude", value=0.0, format="%.4f", key=f"w_lon_{i}")
                    st.session_state[f"tz_{i}"] = st.text_input("Timezone (e.g. Asia/Kolkata)", key=f"w_tz_{i}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.session_state[f"save_cb_{i}"] = st.checkbox("💾 Save this profile to Address Book for future use", value=False, key=f"w_save_cb_{i}")
            active_profiles_data.append({"type": "new", "idx": i})
            
        else:
            opts = ["-- Select a Saved Profile --"] + [f"{idx}: {p['name']} (Born: {format_date_ui(p['date'])})" for idx, p in enumerate(st.session_state.db)]
            sel = st.selectbox("Select Profile:", opts, key=f"src_{i}", label_visibility="collapsed")
            
            if sel != "-- Select a Saved Profile --":
                db_idx = int(sel.split(":")[0])
                p = st.session_state.db[db_idx]
                st.success(f"✅ **{p['name']}** selected (Born: {format_date_ui(p['date'])} at {p['time']} in {p['place']})")
                active_profiles_data.append({"type": "saved", "data": p, "idx": i})
            else:
                active_profiles_data.append({"type": "empty_saved", "idx": i})

# Add/Remove Profile Buttons for Comparison Mode
if mission == "Comparison (Multiple Profiles)":
    btn_c1, btn_c2, btn_c3 = st.columns([2, 2, 6])
    with btn_c1:
        if st.session_state.comp_slots < 10:
            if st.button("➕ Add Another Profile"):
                st.session_state.comp_slots += 1
                st.rerun()
    with btn_c2:
        if st.session_state.comp_slots > 2:
            if st.button("➖ Remove Last Profile"):
                st.session_state.comp_slots -= 1
                st.rerun()

# Optional Comparison Criteria UI 
selected_criteria = []
if mission == "Comparison (Multiple Profiles)":
    st.markdown("---")
    st.markdown("### 3. Choose Comparison Criteria")
    
    col_a, col_b = st.columns(2)
    for i, crit in enumerate(COMPARISON_CRITERIA):
        if i % 2 == 0:
            with col_a:
                if st.checkbox(crit, value=False, key=f"crit_{i}"): selected_criteria.append(crit)
        else:
            with col_b:
                if st.checkbox(crit, value=False, key=f"crit_{i}"): selected_criteria.append(crit)

    st.markdown("##### Add Custom Criteria")
    cc1, cc2 = st.columns([4, 1])
    with cc1: new_c = st.text_input("E.g., Most likely to travel abroad", key="new_c_input", label_visibility="collapsed")
    with cc2:
        if st.button("Add Custom"):
            if new_c.strip() and new_c not in st.session_state.custom_criteria:
                st.session_state.custom_criteria.append(new_c.strip())
                st.rerun()
                
    for i, c in enumerate(st.session_state.custom_criteria):
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.checkbox(c, value=False, key=f"cc_{i}"): selected_criteria.append(c)
        with col2:
            if st.button("Delete", key=f"del_c_{i}"):
                st.session_state.custom_criteria.pop(i)
                st.rerun()

# ------------------------------------------------------------
# GENERATE PROMPT LOGIC 
# ------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
if st.button(f"✨ Generate {mission} Prompt ✨", type="primary", use_container_width=True):
    
    final_profiles_to_process = []

    for item in active_profiles_data:
        i = item["idx"]
        
        if item["type"] == "saved":
            final_profiles_to_process.append(item["data"])
            
        elif item["type"] == "empty_saved":
            if i < req_profiles:
                st.error(f"Profile {i+1}: Please select a saved profile from the dropdown.")
                st.stop()
            else:
                continue 
                
        else:
            u_name = st.session_state.get(f"n_{i}", "")
            u_place = st.session_state.get(f"p_{i}", "")
            is_manual = st.session_state.get(f"man_{i}", False)

            if not u_name.strip() and not u_place.strip() and not is_manual:
                if i < req_profiles:
                    st.error(f"Profile {i+1}: Please enter the required details (Name & Location).")
                    st.stop()
                else:
                    continue 

            if not u_name.strip(): 
                st.error(f"Profile {i+1}: Please enter a name."); st.stop()
            
            u_date = st.session_state.get(f"d_{i}")
            hr = st.session_state.get(f"hr_{i}")
            mi = st.session_state.get(f"mi_{i}")
            am_pm = st.session_state.get(f"ampm_{i}")
            
            h24 = hr if (am_pm == "AM" or hr == 12) and not (am_pm == "AM" and hr == 12) else hr + 12
            if am_pm == "AM" and hr == 12: h24 = 0
            u_time = time(h24, mi)

            if is_manual:
                final_lat = st.session_state.get(f"lat_{i}", 0.0)
                final_lon = st.session_state.get(f"lon_{i}", 0.0)
                final_tz = st.session_state.get(f"tz_{i}", "")
                if not final_tz.strip():
                    st.error(f"Profile {i+1}: Please provide a valid timezone for your manual coordinates (e.g. Asia/Kolkata).")
                    st.stop()
                final_place = "Manual Coordinates"
            else:
                if not u_place.strip(): 
                    st.error(f"Profile {i+1}: Please enter a birth place."); st.stop()
                
                geo = geocode_place(u_place.strip())
                if not geo: 
                    st.error(f"Profile {i+1}: The location '{u_place}' could not be found. Please check your spelling or switch to Manual Coordinates.")
                    st.stop()
                
                final_lat, final_lon, final_place = geo
                final_tz = timezone_for_latlon(final_lat, final_lon)
                if not final_tz:
                    st.error(f"Profile {i+1}: Could not determine the timezone for that location. Please use Manual Coordinates.")
                    st.stop()

            new_profile = {
                "name": u_name.strip(), 
                "date": u_date.isoformat(), 
                "time": u_time.strftime("%H:%M"), 
                "place": final_place, "lat": final_lat, "lon": final_lon, "tz": final_tz
            }

            final_profiles_to_process.append(new_profile)

            if st.session_state.get(f"save_cb_{i}", False):
                if not is_duplicate_in_db(new_profile):
                    st.session_state.db.append(new_profile)
                    sync_db()

    if len(final_profiles_to_process) < req_profiles:
        st.error(f"Not enough valid profiles to generate. This mission requires at least {req_profiles}.")
        st.stop()

    final_prompt = "SYSTEM SETTINGS FOR AI:\n- Zodiac: Sidereal\n- Ayanamsa: Lahiri\n- House System: Whole Sign\n- Node Type: Mean Node\n- Chart Style: North Indian\n\n"
    
    if mission == "Raw Data Only":
        final_prompt += "MISSION: [TYPE YOUR SPECIFIC QUESTION OR REQUEST FOR THE AI HERE]\n\n"
        final_prompt += "Below is the raw astrological data. Please use this to answer my request accurately.\n\n"
        final_prompt += "--- KUNDLI DATA ---\n"
        final_prompt += generate_profile_text(final_profiles_to_process[0])
    
    elif mission == "Deep Personal Analysis":
        final_prompt += "AI PERSONA INSTRUCTIONS:\nAct as a compassionate, expert Vedic Astrologer speaking directly to a client. Translate complex astrological jargon into clear, easy-to-understand layman's language. Always explain *why* a certain prediction is made based on the provided planetary positions. Format your response beautifully using bold text and bullet points for readability.\n\n"
        final_prompt += "MISSION: Provide a highly detailed, comprehensive analysis of the following Kundli.\n"
        final_prompt += "Cover the following areas in extreme depth:\n"
        final_prompt += "1. Personality traits, psychological profile, and core strengths/weaknesses.\n"
        final_prompt += "2. Health tendencies and potential physical vulnerabilities.\n"
        final_prompt += "3. Career path, optimal professions, and success trajectory (Analyze D10 Dasamsa carefully).\n"
        final_prompt += "4. Financial status, wealth accumulation potential, and Dhana Yogas.\n"
        final_prompt += "5. Relationships, marriage timing, and spouse characteristics (Analyze 7th house, Venus, and D9 Navamsa).\n"
        final_prompt += "6. Major future life events and transformations.\n"
        final_prompt += "7. Vimshottari Dasha analysis (Current and upcoming periods).\n"
        final_prompt += "8. Practical, actionable astrological remedies and solutions for any afflicted or debilitated planets.\n\n"
        final_prompt += generate_profile_text(final_profiles_to_process[0])

    elif mission == "Matchmaking / Compatibility":
        final_prompt += "AI PERSONA INSTRUCTIONS:\nAct as a compassionate, expert Vedic Astrologer speaking directly to a client. Translate complex astrological jargon into clear, easy-to-understand layman's language. Always explain *why* a certain prediction is made based on the provided planetary positions. Format your response beautifully using bold text and bullet points for readability.\n\n"
        final_prompt += "MISSION: Perform a deep, highly detailed compatibility analysis of the two Kundlis provided below. Ensure your analysis strictly covers:\n\n"
        final_prompt += "1. Ashta Koota Guna Milan (Calculate and explain the 36 Points system in simple terms):\n"
        final_prompt += "   - Varna (1 pt): Ego and spiritual compatibility.\n"
        final_prompt += "   - Vashya (2 pts): Mutual attraction and dominance.\n"
        final_prompt += "   - Tara (3 pts): Destiny and health.\n"
        final_prompt += "   - Yoni (4 pts): Physical compatibility and intimacy.\n"
        final_prompt += "   - Graha Maitri (5 pts): Friendliness of the moon signs.\n"
        final_prompt += "   - Gana (6 pts): Temperament and behavior.\n"
        final_prompt += "   - Bhakoot (7 pts): Emotional connection and family bonding.\n"
        final_prompt += "   - Nadi (8 pts): Health, genetics, and progeny.\n"
        final_prompt += "2. Manglik Dosh Analysis: Check for the influence of Mars (Mangal) on the 7th house (marriage), affecting harmony and longevity.\n"
        final_prompt += "3. Overall Compatibility & Stability: Predict potential for financial stability, mental compatibility, and longevity of the relationship.\n"
        final_prompt += "4. Long-term Harmony & Potential Issues: Identify specific friction points and suggest practical, real-world relationship advice and astrological remedies.\n"
        final_prompt += "5. Final Score & Definitive Recommendation.\n\n"
        
        final_prompt += f"--- PERSON 1 (Partner 1) ---\n"
        final_prompt += generate_profile_text(final_profiles_to_process[0])
        final_prompt += f"\n\n--- PERSON 2 (Partner 2) ---\n"
        final_prompt += generate_profile_text(final_profiles_to_process[1])

    elif mission == "Comparison (Multiple Profiles)":
        final_prompt += "AI PERSONA INSTRUCTIONS:\nAct as a compassionate, expert Vedic Astrologer speaking directly to a client. Translate complex astrological jargon into clear, easy-to-understand layman's language. Always explain *why* a certain prediction is made based on the provided planetary positions. Format your response beautifully using bold text and bullet points for readability.\n\n"
        final_prompt += f"MISSION: I am providing Kundli Data Packs for {len(final_profiles_to_process)} individuals.\n"
        final_prompt += "Your task is to comprehensively analyze and compare them across the following specific parameters:\n"
        for c in selected_criteria:
            final_prompt += f"- {c}\n"
        final_prompt += "\nProvide a clear, objective comparative analysis for each criterion. Declare a 'winner' or rank the individuals where applicable, backed by precise astrological reasoning from their D1, D9, and D10 charts. Explain your logic simply.\n\n"
        
        for i, p in enumerate(final_profiles_to_process):
            final_prompt += f"--- PROFILE {i+1}: {p['name']} ---\n"
            final_prompt += generate_profile_text(p) + "\n\n"

    final_prompt += "\nFINAL REMINDER: Do NOT recalculate astronomical data. Use ONLY the provided data. Do NOT hallucinate missing details."

    st.subheader("Copy this Output")
    st.code(final_prompt, language="text")

# ------------------------------------------------------------
# UI - SECTION 3: EDIT & MANAGE ADDRESS BOOK
# ------------------------------------------------------------
if len(st.session_state.db) > 0:
    st.markdown("---")
    is_editing = st.session_state.editing_idx is not None
    with st.expander("📖 Manage Saved Profiles (Address Book)", expanded=is_editing):
        for i, p in enumerate(st.session_state.db):
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1: st.write(f"👤 **{p['name']}** (Born: {format_date_ui(p['date'])} at {p['time']} | {p['place']})")
            with col2:
                if st.button("Edit", key=f"edit_db_{i}"):
                    st.session_state.editing_idx = i
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_db_{i}"):
                    st.session_state.db.pop(i)
                    sync_db()
                    if st.session_state.editing_idx == i: st.session_state.editing_idx = None
                    st.rerun()

        if is_editing:
            st.markdown("---")
            edit_i = st.session_state.editing_idx
            p_data = st.session_state.db[edit_i]
            
            d_name = p_data.get('name', '')
            d_date = date.fromisoformat(p_data['date']) if isinstance(p_data.get('date'), str) else p_data.get('date', date(2000, 1, 1))
            p_time = datetime.strptime(p_data['time'], "%H:%M").time() if isinstance(p_data.get('time'), str) else p_data.get('time', time(12, 0))
            
            d_hr = p_time.hour % 12
            if d_hr == 0: d_hr = 12
            d_mi = p_time.minute
            d_ampm_idx = 0 if p_time.hour < 12 else 1
            
            is_manual = p_data.get('place') == "Manual Coordinates"
            d_place = "" if is_manual else p_data.get('place', '')
            d_lat = p_data.get('lat', 31.1048)
            d_lon = p_data.get('lon', 77.1734)
            d_tz = p_data.get('tz', 'Asia/Kolkata')

            st.markdown(f"**✏️ Edit Profile: {d_name}**")
            c1, c2 = st.columns(2)
            with c1:
                u_name = st.text_input("Name", value=d_name, autocomplete="name", key="edit_n")
                u_date = st.date_input("Date of birth", value=d_date, format="DD/MM/YYYY", key="edit_d")
                t1, t2, t3 = st.columns(3)
                with t1: hr = st.number_input("Hour", 1, 12, value=d_hr, key="edit_hr")
                with t2: mi = st.number_input("Minute", 0, 59, value=d_mi, key="edit_mi")
                with t3: am_pm = st.selectbox("AM/PM", ["AM", "PM"], index=d_ampm_idx, key="edit_ampm")
            with c2:
                u_place = st.text_input("Birth Place (City, State, Country)", value=d_place, key="edit_p")
                
                detected_lat, detected_lon, detected_tz, detected_place = None, None, None, None
                if u_place.strip() and not is_manual: 
                    geo = geocode_place(u_place.strip())
                    if geo:
                        detected_lat, detected_lon, detected_place = geo
                        detected_tz = timezone_for_latlon(detected_lat, detected_lon)
                        st.success(f"📍 Auto-detected: {detected_lat:.6f}, {detected_lon:.6f} | TZ: {detected_tz}")
                    else:
                        st.warning("Location not found. Please check spelling or use manual coordinates below.")

                manual = st.checkbox("Manual Coordinates", value=is_manual, key="edit_man")
                if manual:
                    m_lat = st.number_input("Latitude", value=float(d_lat), format="%.4f", key="edit_lat")
                    m_lon = st.number_input("Longitude", value=float(d_lon), format="%.4f", key="edit_lon")
                    m_tz = st.text_input("Timezone", value=d_tz, key="edit_tz")

            bc1, bc2 = st.columns([1, 4])
            with bc1:
                if st.button("Update Profile", type="primary"):
                    if not u_name.strip(): st.error("Please enter a name."); st.stop()
                    h24 = hr if (am_pm == "AM" or hr == 12) and not (am_pm == "AM" and hr == 12) else hr + 12
                    if am_pm == "AM" and hr == 12: h24 = 0
                    u_time = time(h24, mi)

                    if manual:
                        final_lat, final_lon, final_tz, final_place = m_lat, m_lon, m_tz, "Manual Coordinates"
                    else:
                        if detected_lat is None: st.error("Please enter a valid birth place or check Manual."); st.stop()
                        final_lat, final_lon, final_tz, final_place = detected_lat, detected_lon, detected_tz, detected_place

                    st.session_state.db[edit_i] = {
                        "name": u_name, "date": u_date.isoformat(), "time": u_time.strftime("%H:%M"), 
                        "place": final_place, "lat": final_lat, "lon": final_lon, "tz": final_tz
                    }
                    st.session_state.editing_idx = None
                    sync_db()
                    st.rerun()
            with bc2:
                if st.button("Cancel Edit"):
                    st.session_state.editing_idx = None
                    st.rerun()

        st.markdown("---")
        fc1, fc2 = st.columns([4, 1])
        fc1.caption("🟢 Address Book saved securely to your local browser.")
        if fc2.button("Clear Address Book", help="Wipes all saved profiles from this device"):
            st.session_state.db = []
            sync_db()
            st.session_state.editing_idx = None
            st.rerun()