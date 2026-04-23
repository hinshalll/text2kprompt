from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


# ------------------------------------------------------------
# App config
# ------------------------------------------------------------
st.set_page_config(page_title="Kundli Prompt Generator", page_icon="🪐", layout="wide")

try:
    swe.set_ephe_path("ephe")
except Exception:
    pass

# Lahiri = standard sidereal ayanamsa commonly used in Indian astrology.
swe.set_sid_mode(swe.SIDM_LAHIRI)


# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
YEAR_DAYS = 365.2425
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def sign_name(sign_index: int) -> str:
    return SIGNS[sign_index % 12]


def sign_index_from_lon(lon: float) -> int:
    return int(lon // 30) % 12


def format_dms(angle: float) -> str:
    angle = angle % 360
    deg = int(angle)
    minutes_float = (angle - deg) * 60
    minute = int(minutes_float)
    second = int(round((minutes_float - minute) * 60))
    if second == 60:
        second = 0
        minute += 1
    if minute == 60:
        minute = 0
        deg += 1
    return f"{deg:03d}°{minute:02d}'{second:02d}\""


def sign_and_deg(lon: float) -> str:
    lon = lon % 360
    s = sign_name(sign_index_from_lon(lon))
    deg_in_sign = lon % 30
    return f"{s} {format_dms(deg_in_sign)}"


def nakshatra_info(lon: float) -> tuple[str, str, int]:
    lon = lon % 360
    nak_span = 360 / 27
    index = int(lon // nak_span)
    nak = NAKSHATRAS[index]
    lord = NAKSHATRA_LORDS[index]
    pada = int(((lon % nak_span) // (nak_span / 4))) + 1
    return nak, lord, pada


def navamsa_sign_index(lon: float) -> int:
    lon = lon % 360
    sign_idx = sign_index_from_lon(lon)
    within_sign = lon % 30
    navamsa_slot = int(within_sign // (30 / 9))

    if sign_idx in MOVABLE_SIGNS:
        start = sign_idx
    elif sign_idx in FIXED_SIGNS:
        start = (sign_idx + 8) % 12
    else:
        start = (sign_idx + 4) % 12

    return (start + navamsa_slot) % 12


def whole_sign_house(lagna_sign_idx: int, planet_sign_idx: int) -> int:
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


@st.cache_data(show_spinner=False)
def geocode_place(place_text: str):
    geolocator = Nominatim(user_agent="kundli_prompt_generator")
    loc = geolocator.geocode(place_text, exactly_one=True, timeout=20)
    if loc is None:
        return None
    return loc.latitude, loc.longitude, loc.address


@st.cache_data(show_spinner=False)
def timezone_for_latlon(lat: float, lon: float):
    return TimezoneFinder().timezone_at(lat=lat, lng=lon)


def local_to_julian_day(d: date, t: time, tz_name: str) -> tuple[float, datetime, datetime]:
    local_zone = ZoneInfo(tz_name)
    dt_local = datetime.combine(d, t).replace(tzinfo=local_zone)
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    ut_hours = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
        + dt_utc.microsecond / 3_600_000_000.0
    )
    jd_ut = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_hours)
    return jd_ut, dt_local, dt_utc


def get_lagna_longitude(jd_ut: float, lat: float, lon: float) -> float:
    # Ascendant from houses() is tropical; subtract ayanamsha to get sidereal.
    _, ascmc = swe.houses(jd_ut, lat, lon, b"P")
    tropical_asc = float(ascmc[0]) % 360
    ayanamsha = swe.get_ayanamsa_ut(jd_ut)
    return (tropical_asc - ayanamsha) % 360


def get_planet_longitude(jd_ut: float, planet_id: int) -> float:
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res, _ = swe.calc_ut(jd_ut, planet_id, flags)
    return float(res[0]) % 360


def get_rahu_longitude(jd_ut: float) -> float:
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
    return float(res[0]) % 360


def dasha_balance_years(moon_lon: float) -> tuple[str, float, str]:
    nak_span = 360 / 27
    nak_index = int((moon_lon % 360) // nak_span)
    lord = NAKSHATRA_LORDS[nak_index]
    portion_used = ((moon_lon % nak_span) / nak_span)
    balance = DASHA_YEARS[lord] * (1 - portion_used)
    return lord, balance, NAKSHATRAS[nak_index]


def build_vimshottari_timeline(dt_birth: datetime, moon_lon: float, dt_now: datetime):
    start_lord, balance_years, birth_nak = dasha_balance_years(moon_lon)
    start_index = DASHA_ORDER.index(start_lord)
    sequence = DASHA_ORDER[start_index:] + DASHA_ORDER[:start_index]

    mahadashas = [(sequence[0], balance_years)]
    mahadashas.extend((lord, DASHA_YEARS[lord]) for lord in sequence[1:])

    dt_cursor = dt_birth
    current_md = None
    current_ad = None
    md_start = None
    md_end = None
    ad_start = None
    ad_end = None

    for md_lord, md_years in mahadashas:
        md_days = md_years * YEAR_DAYS
        next_md_cursor = dt_cursor + timedelta(days=md_days)

        if dt_now < next_md_cursor:
            current_md = md_lord
            md_start = dt_cursor
            md_end = next_md_cursor

            ad_cursor = dt_cursor
            md_pos = DASHA_ORDER.index(md_lord)
            ad_sequence = DASHA_ORDER[md_pos:] + DASHA_ORDER[:md_pos]
            for ad_lord in ad_sequence:
                ad_years = (md_years * DASHA_YEARS[ad_lord]) / 120.0
                ad_days = ad_years * YEAR_DAYS
                next_ad_cursor = ad_cursor + timedelta(days=ad_days)
                if dt_now < next_ad_cursor:
                    current_ad = ad_lord
                    ad_start = ad_cursor
                    ad_end = next_ad_cursor
                    break
                ad_cursor = next_ad_cursor
            break

        dt_cursor = next_md_cursor

    return {
        "birth_nakshatra": birth_nak,
        "start_lord": start_lord,
        "balance_years": balance_years,
        "current_md": current_md,
        "current_ad": current_ad,
        "md_start": md_start,
        "md_end": md_end,
        "ad_start": ad_start,
        "ad_end": ad_end,
    }


def years_to_ymd(years: float) -> str:
    total_days = max(0.0, years) * YEAR_DAYS
    whole_days = int(total_days)
    y = whole_days // 365
    rem = whole_days % 365
    m = rem // 30
    d = rem % 30
    return f"{y}y {m}m {d}d"


def build_prompt(
    name: str,
    place_text: str,
    lat: float,
    lon: float,
    tz_name: str,
    dt_birth_local: datetime,
    dt_birth_utc: datetime,
    lagna_lon: float,
    planet_lons: dict,
    dasha_info: dict,
) -> str:
    lagna_sign = sign_name(sign_index_from_lon(lagna_lon))
    lagna_dms = format_dms(lagna_lon % 30)

    d1_lines = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        plon = planet_lons[pname]
        sidx = sign_index_from_lon(plon)
        nak, nak_lord, pada = nakshatra_info(plon)
        house = whole_sign_house(sign_index_from_lon(lagna_lon), sidx)
        d1_lines.append(
            f"{pname}: {sign_and_deg(plon)} | Nakshatra: {nak} (Lord: {nak_lord}, Pada: {pada}) | House: {house}"
        )

    rahu_lon = planet_lons["Rahu"]
    ketu_lon = (rahu_lon + 180.0) % 360
    for pname, plon in [("Rahu", rahu_lon), ("Ketu", ketu_lon)]:
        sidx = sign_index_from_lon(plon)
        nak, nak_lord, pada = nakshatra_info(plon)
        house = whole_sign_house(sign_index_from_lon(lagna_lon), sidx)
        d1_lines.append(
            f"{pname}: {sign_and_deg(plon)} | Nakshatra: {nak} (Lord: {nak_lord}, Pada: {pada}) | House: {house}"
        )

    d9_lines = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        plon = planet_lons[pname] if pname != "Ketu" else ketu_lon
        nav_sign = sign_name(navamsa_sign_index(plon))
        d9_lines.append(f"{pname}: {nav_sign}")

    lines = []
    lines.append("Analyze the following kundli using Vedic astrology only.")
    lines.append("")
    lines.append("SYSTEM SETTINGS:")
    lines.append("- Zodiac: Sidereal")
    lines.append("- Ayanamsa: Lahiri")
    lines.append("- House System: Whole Sign")
    lines.append("- Node Type: Mean Node")
    lines.append("- Chart Style: North Indian")
    lines.append("")
    lines.append("BIRTH DATA:")
    lines.append(f"- Name: {name}")
    lines.append(f"- Place: {place_text}")
    lines.append(f"- Latitude: {lat:.6f}")
    lines.append(f"- Longitude: {lon:.6f}")
    lines.append(f"- Timezone: {tz_name}")
    lines.append(f"- Birth Time (local): {dt_birth_local.strftime('%d %b %Y, %I:%M %p')}")
    lines.append(f"- Birth Time (UTC): {dt_birth_utc.strftime('%d %b %Y, %H:%M UTC')}")
    lines.append("")
    lines.append("D1 / RASI CHART:")
    lines.append(f"Ascendant (Lagna): {lagna_sign} {lagna_dms}")
    lines.extend(d1_lines)
    lines.append("")
    lines.append("D9 / NAVAMSA CHART:")
    lines.extend(d9_lines)
    lines.append("")
    lines.append("VIMSHOTTARI DASHA:")
    lines.append(f"Birth Nakshatra: {dasha_info['birth_nakshatra']}")
    lines.append(f"Start Mahadasha Lord at Birth: {dasha_info['start_lord']}")
    lines.append(f"Mahadasha Balance at Birth: {dasha_info['balance_years']:.2f} years (~{years_to_ymd(dasha_info['balance_years'])})")
    lines.append(f"Current Mahadasha: {dasha_info['current_md'] or 'N/A'}")
    lines.append(f"Current Antardasha: {dasha_info['current_ad'] or 'N/A'}")
    if dasha_info["md_start"] and dasha_info["md_end"]:
        lines.append(
            f"Current Mahadasha Period: {dasha_info['md_start'].strftime('%d %b %Y')} to {dasha_info['md_end'].strftime('%d %b %Y')}"
        )
    if dasha_info["ad_start"] and dasha_info["ad_end"]:
        lines.append(
            f"Current Antardasha Period: {dasha_info['ad_start'].strftime('%d %b %Y')} to {dasha_info['ad_end'].strftime('%d %b %Y')}"
        )
    lines.append("")
    lines.append("IMPORTANT:")
    lines.append("- Do NOT recalculate anything.")
    lines.append("- Use ONLY the provided data.")
    lines.append("- Do NOT assume missing details.")
    lines.append("- Give detailed, logical, non-generic analysis.")
    lines.append("- You may analyze personality, education, career, finances, relationships, health tendencies, timing, strengths, weaknesses, yogas, and life patterns.")

    return "\n".join(lines)


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("🪐 Kundli Prompt Generator")
st.caption("Enter birth details, generate a Vedic kundli data pack, then copy it into any AI for analysis.")

with st.expander("How this works", expanded=True):
    st.write(
        "This app uses sidereal Lahiri settings, whole-sign houses, Swiss Ephemeris calculations, and a copyable text output. "
        "For best accuracy, give the exact birth time and, if possible, fill latitude/longitude and timezone."
    )

st.markdown("### Enter Birth Details")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Name")
    birth_date = st.date_input("Date of birth", value=date(2000, 1, 1))

    t1, t2, t3 = st.columns(3)
    with t1:
        hour = st.number_input("Hour", min_value=1, max_value=12, value=12, step=1)
    with t2:
        minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=1)
    with t3:
        am_pm = st.selectbox("AM/PM", ["AM", "PM"])

    if am_pm == "PM" and hour != 12:
        hour_24 = hour + 12
    elif am_pm == "AM" and hour == 12:
        hour_24 = 0
    else:
        hour_24 = hour
    birth_time = time(hour_24, minute)

    use_manual_coords = st.checkbox("Use manual latitude/longitude")
    place_text = ""
    if not use_manual_coords:
        place_text = st.text_input(
            "Birth place",
            placeholder="Shimla, Himachal Pradesh, India",
            help="Type a city, town, village, or full address. The app will try to resolve coordinates automatically.",
        )
        if place_text.strip():
            preview = geocode_place(place_text.strip())
            if preview:
                st.info(f"Auto-detected: Lat {preview[0]:.6f}, Lon {preview[1]:.6f}")
            else:
                st.warning("Place not found yet. Try a more complete name like 'Banjar, Kullu, Himachal Pradesh, India'.")

with col2:
    if use_manual_coords:
        lat_in = st.text_input("Latitude", placeholder="31.1048")
        lon_in = st.text_input("Longitude", placeholder="77.1734")
        tz_in = st.text_input("Timezone (optional override)", placeholder="Asia/Kolkata")
        st.warning("Manual coordinates are ON. Birth place text will not be used.")
    else:
        lat_in = ""
        lon_in = ""
        tz_in = ""
        st.write("Manual coordinates are OFF.")

st.write("Rahu/Ketu type: **Mean Node**")

if st.button("Generate prompt"):
    try:
        if use_manual_coords:
            if not lat_in.strip() or not lon_in.strip():
                st.error("When manual coordinates are enabled, latitude and longitude are required.")
                st.stop()
            lat = float(lat_in)
            lon = float(lon_in)
            resolved_place = place_text.strip() or "Manual coordinates"
            tz_name = tz_in.strip() if tz_in.strip() else timezone_for_latlon(lat, lon)
            if not tz_name:
                st.error("Timezone could not be auto-detected. Enter it manually, for example Asia/Kolkata.")
                st.stop()
        else:
            if not place_text.strip():
                st.error("Enter a birth place or turn on manual coordinates.")
                st.stop()
            place_match = geocode_place(place_text.strip())
            if place_match is None:
                st.error("I could not find that place automatically. Try a fuller place name or use manual coordinates.")
                st.stop()
            lat, lon, resolved_place = place_match
            tz_name = timezone_for_latlon(lat, lon)
            if not tz_name:
                st.error("Timezone could not be auto-detected for that place.")
                st.stop()

        jd_ut, dt_local, dt_utc = local_to_julian_day(birth_date, birth_time, tz_name)
        lagna_lon = get_lagna_longitude(jd_ut, lat, lon)
        planet_lons = {pname: get_planet_longitude(jd_ut, pid) for pname, pid in PLANETS.items()}
        planet_lons["Rahu"] = get_rahu_longitude(jd_ut)

        now_local = datetime.now(ZoneInfo(tz_name))
        dasha_info = build_vimshottari_timeline(dt_local, planet_lons["Moon"], now_local)

        st.subheader("Resolved location")
        st.write(f"Place used: {resolved_place}")
        st.write(f"Latitude: {lat:.6f}")
        st.write(f"Longitude: {lon:.6f}")
        st.write(f"Timezone: {tz_name}")

        prompt = build_prompt(
            name=name.strip() or "Not provided",
            place_text=resolved_place,
            lat=lat,
            lon=lon,
            tz_name=tz_name,
            dt_birth_local=dt_local,
            dt_birth_utc=dt_utc,
            lagna_lon=lagna_lon,
            planet_lons=planet_lons,
            dasha_info=dasha_info,
        )

        st.subheader("Copy this output")
        st.code(prompt, language="text")
        st.download_button(
            label="Download as .txt",
            data=prompt,
            file_name="kundli_prompt.txt",
            mime="text/plain",
        )

        with st.expander("What was calculated"):
            lagna_sign = sign_name(sign_index_from_lon(lagna_lon))
            st.write(f"Lagna: {lagna_sign} {format_dms(lagna_lon % 30)}")
            for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]:
                lonp = planet_lons[pname]
                nak, lord, pada = nakshatra_info(lonp)
                st.write(f"{pname}: {sign_and_deg(lonp)} | {nak} | Lord: {lord} | Pada: {pada}")
            st.write(f"Ketu: {sign_and_deg((planet_lons['Rahu'] + 180.0) % 360)}")

    except Exception as exc:
        st.error(f"Could not generate the chart: {exc}")

st.divider()
st.caption(
    "Tip: For the most reliable result, use the exact birth time and, when possible, confirm latitude/longitude and timezone. "
    "If another app gives a slightly different chart, the most common cause is a different ayanamsa, timezone rule, or node setting."
)