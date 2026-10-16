from datetime import datetime, timedelta
import math
import streamlit as st

try:
  import pysweph as swe
except ImportError:
  try:
    import swe as swe
  except ImportError:
    try:
      import swisseph as swe
    except ImportError:
      swe = None

st.set_page_config(
    page_title="KP Moon & Rashi Tracker", layout="centered", initial_sidebar_state="expanded"
)

LOCATIONS_DB = {
    "suri": [23.9167, 87.5333],
    "kolkata": [22.5726, 88.3639],
    "dhaka": [23.8103, 90.4125],
    "new delhi": [28.6139, 77.2090],
    "mumbai": [19.0760, 72.8777],
    "bangalore": [12.9716, 77.5946],
    "chittagong": [22.3569, 91.7832],
    "sylhet": [24.8949, 91.8687],
    "london": [51.5074, -0.1278],
    "new york": [40.7128, -74.0060],
}

RASHIS = [
    "Mesh (Mesha)",
    "Brisho (Vrishabha)",
    "Mithun (Mithuna)",
    "Korkot (Karka)",
    "Singho (Simha)",
    "Konna (Kanya)",
    "Tula (Tula)",
    "Vrishchika (Vrishchika)",
    "Dhonu (Sagittarius)",
    "Mokor (Capricorn)",
    "Kumbho (Aquarius)",
    "Meen (Pisces)",
]

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

LORDS_ORDER = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

LORD_YEARS = {
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
TOTAL_YEARS = 120


def get_swiss_moon_longitude(dt, lat, lon):
  if swe is None:
    return 0.0, 13.1768

  swe.set_sid_mode(swe.SIDM_KRISHNAMURTI, 0, 0)
  flags = swe.FLG_SWIEPH + swe.FLG_SPEED + swe.FLG_SIDEREAL
  swe.set_topo(lon, lat, 0)

  tz_offset = 5.5
  utc_dt = dt - timedelta(hours=tz_offset)

  jd = swe.julday(
      utc_dt.year,
      utc_dt.month,
      utc_dt.day,
      utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
  )

  calc_res = swe.calc_ut(jd, swe.MOON, flags)
  res = calc_res[0] if isinstance(calc_res, tuple) else calc_res

  moon_lon = res[0]
  moon_daily_speed = res[3] if len(res) > 3 and res[3] != 0 else 13.1768

  return moon_lon, abs(moon_daily_speed)


def calculate_kp_details(moon_lon, moon_daily_speed=13.1768):
  lon = moon_lon % 360

  rashi_index = int(lon / 30.0)
  rashi_name = RASHIS[rashi_index]

  nak_span = 360.0 / 27.0
  nak_index = int(lon / nak_span)
  nakshatra_name = NAKSHATRAS[nak_index]
  nakshatra_lord = LORDS_ORDER[nak_index % 9]
  deg_in_nak = lon - (nak_index * nak_span)

  sub_cumulative = 0.0
  sub_lord = ""
  sub_span_deg = 0.0
  deg_in_sub = 0.0
  lord_start_idx = LORDS_ORDER.index(nakshatra_lord)

  for i in range(9):
    current_lord = LORDS_ORDER[(lord_start_idx + i) % 9]
    span = (LORD_YEARS[current_lord] / TOTAL_YEARS) * nak_span
    next_cumulative = sub_cumulative + span
    
    if deg_in_nak <= next_cumulative or i == 8:
      sub_lord = current_lord
      sub_span_deg = span
      deg_in_sub = deg_in_nak - sub_cumulative
      break
    sub_cumulative = next_cumulative

  ssl_cumulative = 0.0
  sub_sub_lord = ""
  ssl_span_deg = 0.0
  deg_in_ssl = 0.0
  ssl_start_idx = LORDS_ORDER.index(sub_lord)

  for i in range(9):
    current_ssl = LORDS_ORDER[(ssl_start_idx + i) % 9]
    ssl_span = (LORD_YEARS[current_ssl] / TOTAL_YEARS) * sub_span_deg
    next_ssl_cum = ssl_cumulative + ssl_span

    if deg_in_sub <= next_ssl_cum or i == 8:
      sub_sub_lord = current_ssl
      ssl_span_deg = ssl_span
      deg_in_ssl = deg_in_sub - ssl_cumulative
      break
    ssl_cumulative = next_ssl_cum

  sssl_cumulative = 0.0
  sub_sub_sub_lord = ""
  sssl_start_idx = LORDS_ORDER.index(sub_sub_lord)

  for i in range(9):
    current_sssl = LORDS_ORDER[(sssl_start_idx + i) % 9]
    sssl_span = (LORD_YEARS[current_sssl] / TOTAL_YEARS) * ssl_span_deg
    next_sssl_cum = sssl_cumulative + sssl_span

    if deg_in_ssl <= next_sssl_cum or i == 8:
      sub_sub_sub_lord = current_sssl
      break
    sssl_cumulative = next_sssl_cum

  remaining_deg_in_sub = sub_span_deg - deg_in_sub
  rem_hours = (remaining_deg_in_sub / moon_daily_speed) * 24

  return {
      "Longitude": lon,
      "Rashi": rashi_name,
      "Nakshatra": nakshatra_name,
      "NakshatraLord": nakshatra_lord,
      "SubLord": sub_lord,
      "SubSubLord": sub_sub_lord,
      "SubSubSubLord": sub_sub_sub_lord,
      "RemainingHours": rem_hours,
  }


st.markdown(
    "<h2 style='text-align: center; color: #0056b3;'>🌟 KP True Node & New"
    " Ayanamsa Tracker 🌟</h2>",
    unsafe_allow_html=True,
)

st.sidebar.header("⚙️ Settings & Inputs")
selected_city = st.sidebar.selectbox(
    "Location Name", list(LOCATIONS_DB.keys()), index=0
)

default_lat, default_lon = LOCATIONS_DB[selected_city]
lat = st.sidebar.number_input("Latitude", value=default_lat, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=default_lon, format="%.4f")

mode = st.sidebar.radio(
    "Mode", ["Live Time", "Custom Time", "Track Full Day Schedule"]
)

target_dt = datetime.now()
if mode in ["Custom Time", "Track Full Day Schedule"]:
  d_val = st.sidebar.date_input("Date", datetime.now())
  if mode == "Custom Time":
    t_val = st.sidebar.time_input("Time", datetime.now().time())
    target_dt = datetime.combine(d_val, t_val)
  else:
    target_dt = datetime.combine(d_val, datetime.min.time())

if mode != "Track Full Day Schedule":
  moon_lon, moon_speed = get_swiss_moon_longitude(target_dt, lat, lon)
  res = calculate_kp_details(moon_lon, moon_speed)

  st.markdown("### ⚡ PRESENT RUNNING LORDS")
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("NL", res["NakshatraLord"])
  col2.metric("SL", res["SubLord"])
  col3.metric("SSL", res["SubSubLord"])
  col4.metric("SSSL", res["SubSubSubLord"])

  st.markdown("---")

  st.markdown(f"### 📋 Details for ({selected_city.title()})")
  st.write(
      f"**Target Time:** {target_dt.strftime('%Y-%m-%d %I:%M:%S %p')}"
  )
  st.write(f"**Moon Longitude:** {res['Longitude']:.4f}°")
  st.write(f"**Moon Rashi:** {res['Rashi']}")
  st.write(f"**Nakshatra:** {res['Nakshatra']} ({res['NakshatraLord']})")
  st.write(f"**Sub-Lord (SL):** {res['SubLord']}")
  st.write(f"**Sub-Sub-Lord (SSL):** {res['SubSubLord']}")
  st.write(f"**Sub-Sub-Sub (SSSL):** {res['SubSubSubLord']}")
  st.write(f"**Remaining Time in Sub:** {res['RemainingHours']:.2f} hours")

else:
  st.markdown(
      f"### ⚡ Full Day Schedule for {target_dt.strftime('%Y-%m-%d')}"
      f" ({selected_city.title()})"
  )
  with st.spinner("Calculating transitions for the full day... Please wait."):
    start_dt = target_dt
    prev_rashi, prev_nak, prev_sl, prev_ssl, prev_sssl = "", "", "", "", ""
    schedule_data = []

    for minute_offset in range(0, 24 * 60, 2):
      current_dt = start_dt + timedelta(minutes=minute_offset)
      moon_lon, moon_speed = get_swiss_moon_longitude(current_dt, lat, lon)
      res = calculate_kp_details(moon_lon, moon_speed)

      if (
          res["Rashi"] != prev_rashi
          or res["Nakshatra"] != prev_nak
          or res["SubLord"] != prev_sl
          or res["SubSubLord"] != prev_ssl
          or res["SubSubSubLord"] != prev_sssl
      ):
        schedule_data.append({
            "Time": current_dt.strftime("%I:%M %p"),
            "Rashi": res["Rashi"],
            "Nakshatra & Lord": f"{res['Nakshatra']} ({res['NakshatraLord']})",
            "SL": res["SubLord"],
            "SSL": res["SubSubLord"],
            "SSSL": res["SubSubSubLord"],
        })
        prev_rashi, prev_nak, prev_sl, prev_ssl, prev_sssl = (
            res["Rashi"],
            res["Nakshatra"],
            res["SubLord"],
            res["SubSubLord"],
            res["SubSubSubLord"],
        )

    st.table(schedule_data)
