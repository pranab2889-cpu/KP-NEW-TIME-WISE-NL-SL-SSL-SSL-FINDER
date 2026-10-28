from datetime import datetime, timedelta
import math
import tkinter as tk
from tkinter import messagebox, ttk

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
    raise ImportError("pysweph library install kora nei!")

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
    sub_cumulative += span
    if deg_in_nak <= sub_cumulative:
      sub_lord = current_lord
      sub_span_deg = span
      deg_in_sub = deg_in_nak - (sub_cumulative - span)
      break

  ssl_cumulative = 0.0
  sub_sub_lord = ""
  ssl_span_deg = 0.0
  deg_in_ssl = 0.0
  ssl_start_idx = LORDS_ORDER.index(sub_lord)

  for i in range(9):
    current_ssl = LORDS_ORDER[(ssl_start_idx + i) % 9]
    ssl_span = (LORD_YEARS[current_ssl] / TOTAL_YEARS) * sub_span_deg
    ssl_cumulative += ssl_span
    if deg_in_sub <= ssl_cumulative:
      sub_sub_lord = current_ssl
      ssl_span_deg = ssl_span
      deg_in_ssl = deg_in_sub - (ssl_cumulative - ssl_span)
      break

  sssl_cumulative = 0.0
  sub_sub_sub_lord = ""
  sssl_start_idx = LORDS_ORDER.index(sub_sub_lord)

  for i in range(9):
    current_sssl = LORDS_ORDER[(sssl_start_idx + i) % 9]
    sssl_span = (LORD_YEARS[current_sssl] / TOTAL_YEARS) * ssl_span_deg
    sssl_cumulative += sssl_span
    if deg_in_ssl <= sssl_cumulative:
      sub_sub_sub_lord = current_sssl
      break

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


class KPMoonApp:

  def __init__(self, root):
    self.root = root
    self.root.title(
        "KP Moon Live & Rashi Tracker (Swiss Ephemeris - KP New & True Node)"
    )
    self.root.geometry("860x920")
    self.root.config(bg="#f4f6f9")

    self.current_mode = "live"

    title_label = tk.Label(
        root,
        text="🌟 KP True Node & New Ayanamsa Tracker 🌟",
        font=("Arial", 14, "bold"),
        bg="#f4f6f9",
        fg="#0056b3",
    )
    title_label.pack(pady=5)

    highlight_frame = tk.Frame(root, bg="#1e1e2f", bd=2, relief="ridge")
    highlight_frame.pack(fill="x", padx=15, pady=5)

    tk.Label(
        highlight_frame,
        text="⚡ PRESENT RUNNING LORDS (LIVE) ⚡",
        font=("Arial", 10, "bold"),
        bg="#1e1e2f",
        fg="#ffc107",
    ).pack(pady=3)

    lords_card_sub = tk.Frame(highlight_frame, bg="#1e1e2f")
    lords_card_sub.pack(pady=5, padx=10, fill="x")

    self.nl_val_lbl = tk.Label(
        lords_card_sub,
        text="NL: --",
        font=("Consolas", 11, "bold"),
        bg="#282a36",
        fg="#50fa7b",
        padx=10,
        pady=5,
    )
    self.nl_val_lbl.grid(row=0, column=0, padx=5, sticky="ew")

    self.sl_val_lbl = tk.Label(
        lords_card_sub,
        text="SL: --",
        font=("Consolas", 11, "bold"),
        bg="#282a36",
        fg="#8be9fd",
        padx=10,
        pady=5,
    )
    self.sl_val_lbl.grid(row=0, column=1, padx=5, sticky="ew")

    self.ssl_val_lbl = tk.Label(
        lords_card_sub,
        text="SSL: --",
        font=("Consolas", 11, "bold"),
        bg="#282a36",
        fg="#ffb86c",
        padx=10,
        pady=5,
    )
    self.ssl_val_lbl.grid(row=0, column=2, padx=5, sticky="ew")

    self.sssl_val_lbl = tk.Label(
        lords_card_sub,
        text="SSSL: --",
        font=("Consolas", 11, "bold"),
        bg="#282a36",
        fg="#ff79c6",
        padx=10,
        pady=5,
    )
    self.sssl_val_lbl.grid(row=0, column=3, padx=5, sticky="ew")

    lords_card_sub.grid_columnconfigure(0, weight=1)
    lords_card_sub.grid_columnconfigure(1, weight=1)
    lords_card_sub.grid_columnconfigure(2, weight=1)
    lords_card_sub.grid_columnconfigure(3, weight=1)

    input_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
    input_frame.pack(pady=5, padx=15, fill="x")

    tk.Label(
        input_frame,
        text="Location Name:",
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#333333",
    ).grid(row=0, column=0, sticky="w", padx=10, pady=4)
    display_cities = [city.title() for city in LOCATIONS_DB.keys()]
    self.loc_combo = ttk.Combobox(
        input_frame, values=display_cities, font=("Arial", 9), width=16
    )
    self.loc_combo.grid(row=0, column=1, columnspan=3, padx=10, pady=4, sticky="w")
    self.loc_combo.set("Suri")
    self.loc_combo.bind("<<ComboboxSelected>>", self.update_coordinates)
    self.loc_combo.bind("<KeyRelease>", self.update_coordinates)

    tk.Label(
        input_frame,
        text="Latitude:",
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#333333",
    ).grid(row=1, column=0, sticky="w", padx=10, pady=4)
    self.lat_entry = tk.Entry(
        input_frame, font=("Arial", 9), width=16, bg="#f9f9f9"
    )
    self.lat_entry.grid(row=1, column=1, padx=10, pady=4, sticky="w")
    self.lat_entry.insert(0, "23.9167")

    tk.Label(
        input_frame,
        text="Longitude:",
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#333333",
    ).grid(row=2, column=0, sticky="w", padx=10, pady=4)
    self.lon_entry = tk.Entry(
        input_frame, font=("Arial", 9), width=16, bg="#f9f9f9"
    )
    self.lon_entry.grid(row=2, column=1, padx=10, pady=4, sticky="w")
    self.lon_entry.insert(0, "87.5333")

    tk.Label(
        input_frame,
        text="Date (YYYY-MM-DD):",
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#333333",
    ).grid(row=3, column=0, sticky="w", padx=10, pady=4)
    self.date_entry = tk.Entry(
        input_frame, font=("Arial", 9), width=16, bg="#f9f9f9"
    )
    self.date_entry.grid(row=3, column=1, padx=10, pady=4, sticky="w")
    self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    tk.Label(
        input_frame,
        text="Time (HH:MM):",
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#333333",
    ).grid(row=4, column=0, sticky="w", padx=10, pady=4)

    time_sub_frame = tk.Frame(input_frame, bg="#ffffff")
    time_sub_frame.grid(row=4, column=1, padx=5, pady=4, sticky="w")

    self.hour_entry = tk.Entry(
        time_sub_frame, font=("Arial", 9), width=3, justify="center"
    )
    self.hour_entry.pack(side="left")
    self.hour_entry.insert(0, datetime.now().strftime("%I"))

    tk.Label(time_sub_frame, text=":", font=("Arial", 10, "bold"), bg="#ffffff").pack(
        side="left"
    )

    self.min_entry = tk.Entry(
        time_sub_frame, font=("Arial", 9), width=3, justify="center"
    )
    self.min_entry.pack(side="left")
    self.min_entry.insert(0, datetime.now().strftime("%M"))

    self.ampm_combo = ttk.Combobox(
        input_frame, values=["AM", "PM"], font=("Arial", 9), width=5
    )
    self.ampm_combo.grid(row=4, column=2, padx=2, pady=4, sticky="w")
    self.ampm_combo.set(datetime.now().strftime("%p"))

    self.status_var = tk.StringVar(value="🟢 Live Mode Active")
    status_label = tk.Label(
        input_frame,
        textvariable=self.status_var,
        font=("Arial", 9, "bold"),
        bg="#ffffff",
        fg="#28a745",
    )
    status_label.grid(row=4, column=3, padx=5, pady=4, sticky="w")

    btn_frame = tk.Frame(root, bg="#f4f6f9")
    btn_frame.pack(pady=5)

    calc_btn = tk.Button(
        btn_frame,
        text="🔍 Check Live",
        font=("Arial", 9, "bold"),
        bg="#007bff",
        fg="white",
        padx=6,
        pady=4,
        command=self.calculate_live,
    )
    calc_btn.grid(row=0, column=0, padx=5)

    custom_btn = tk.Button(
        btn_frame,
        text="🎯 Check Custom Time",
        font=("Arial", 9, "bold"),
        bg="#ff8c00",
        fg="white",
        padx=6,
        pady=4,
        command=self.calculate_custom_time,
    )
    custom_btn.grid(row=0, column=1, padx=5)

    sched_btn = tk.Button(
        btn_frame,
        text="⚡ Track Full Day Schedule",
        font=("Arial", 9, "bold"),
        bg="#28a745",
        fg="white",
        padx=6,
        pady=4,
        command=self.generate_transitions,
    )
    sched_btn.grid(row=0, column=2, padx=5)

    output_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
    output_frame.pack(fill="both", expand=True, padx=15, pady=5)

    self.text_area = tk.Text(
        output_frame,
        font=("Consolas", 9),
        bg="#ffffff",
        fg="#111111",
        insertbackground="black",
        wrap="word",
    )
    scrollbar = tk.Scrollbar(output_frame, command=self.text_area.yview)
    self.text_area.configure(yscrollcommand=scrollbar.set)

    self.text_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    self.text_area.tag_config(
        "header", foreground="#d9534f", font=("Consolas", 10, "bold")
    )
    self.text_area.tag_config(
        "time", foreground="#0275d8", font=("Consolas", 9, "bold")
    )
    self.text_area.tag_config("nak", foreground="#292b2c", font=("Consolas", 9))
    self.text_area.tag_config(
        "rashi", foreground="#d9534f", font=("Consolas", 9, "bold")
    )
    self.text_area.tag_config("lord", foreground="#6f42c1", font=("Consolas", 9))
    self.text_area.tag_config(
        "sl", foreground="#0275d8", font=("Consolas", 9, "bold")
    )
    self.text_area.tag_config("ssl", foreground="#f0ad4e", font=("Consolas", 9))
    self.text_area.tag_config("sssl", foreground="#5cb85c", font=("Consolas", 9))
    self.text_area.tag_config(
        "highlight",
        foreground="#ffffff",
        background="#d9534f",
        font=("Consolas", 9, "bold"),
    )

    self.auto_refresh_loop()

  def update_coordinates(self, event=None):
    typed_city = self.loc_combo.get().strip().lower()
    if typed_city in LOCATIONS_DB:
      lat, lon = LOCATIONS_DB[typed_city]
      self.lat_entry.delete(0, tk.END)
      self.lat_entry.insert(0, str(lat))
      self.lon_entry.delete(0, tk.END)
      self.lon_entry.insert(0, str(lon))

  def calculate_live(self):
    self.current_mode = "live"
    self.status_var.set("🟢 Live Mode Active")
    self.update_coordinates()
    loc_name = self.loc_combo.get().strip()
    try:
      target_dt = datetime.now()
      lat = float(self.lat_entry.get().strip())
      lon_val = float(self.lon_entry.get().strip())

      moon_lon, moon_speed = get_swiss_moon_longitude(target_dt, lat, lon_val)
      res = calculate_kp_details(moon_lon, moon_speed)

      self.nl_val_lbl.config(text=f"NL: {res['NakshatraLord']}")
      self.sl_val_lbl.config(text=f"SL: {res['SubLord']}")
      self.ssl_val_lbl.config(text=f"SSL: {res['SubSubLord']}")
      self.sssl_val_lbl.config(text=f"SSSL: {res['SubSubSubLord']}")

      self.text_area.delete("1.0", tk.END)
      self.text_area.insert(
          tk.END,
          f"=== LIVE CURRENT TIME DETAILS ({loc_name}) [KP New / Swiss]"
          f" ===\n\n",
          "header",
      )
      self.text_area.insert(
          tk.END,
          f"Live Time        : {target_dt.strftime('%Y-%m-%d %I:%M:%S %p')}\n",
          "time",
      )
      self.text_area.insert(
          tk.END, f"Moon Longitude   : {res['Longitude']:.4f}°\n", "nak"
      )
      self.text_area.insert(
          tk.END, f"Moon Rashi       : {res['Rashi']}\n\n", "rashi"
      )
      self.text_area.insert(
          tk.END,
          f"Nakshatra        : {res['Nakshatra']} ({res['NakshatraLord']})\n",
          "nak",
      )
      self.text_area.insert(
          tk.END, f"Nakshatra Lord   : {res['NakshatraLord']}\n", "lord"
      )
      self.text_area.insert(
          tk.END, f"Sub-Lord (SL)    : {res['SubLord']}\n", "sl"
      )
      self.text_area.insert(
          tk.END, f"Sub-Sub-Lord     : {res['SubSubLord']}\n", "ssl"
      )
      self.text_area.insert(
          tk.END, f"Sub-Sub-Sub (SSSL): {res['SubSubSubLord']}\n\n", "sssl"
      )
      self.text_area.insert(
          tk.END, f"Remaining Time   : {res['RemainingHours']:.2f} hours\n", "time"
      )
    except Exception as e:
      messagebox.showerror("Error", f"Somoshya hoyeche: {str(e)}")

  def calculate_custom_time(self):
    self.current_mode = "custom"
    self.status_var.set("🎯 Custom Time Mode")
    self.update_coordinates()
    loc_name = self.loc_combo.get().strip()
    d_str = self.date_entry.get().strip()

    try:
      h_str = self.hour_entry.get().strip().zfill(2)
      m_str = self.min_entry.get().strip().zfill(2)
      t_str = f"{h_str}:{m_str}:00"
      ampm_val = self.ampm_combo.get().strip()

      target_dt = datetime.strptime(
          f"{d_str} {t_str} {ampm_val}", "%Y-%m-%d %I:%M:%S %p"
      )
      lat = float(self.lat_entry.get().strip())
      lon_val = float(self.lon_entry.get().strip())

      moon_lon, moon_speed = get_swiss_moon_longitude(target_dt, lat, lon_val)
      res = calculate_kp_details(moon_lon, moon_speed)

      self.nl_val_lbl.config(text=f"NL: {res['NakshatraLord']}")
      self.sl_val_lbl.config(text=f"SL: {res['SubLord']}")
      self.ssl_val_lbl.config(text=f"SSL: {res['SubSubLord']}")
      self.sssl_val_lbl.config(text=f"SSSL: {res['SubSubSubLord']}")

      self.text_area.delete("1.0", tk.END)
      self.text_area.insert(
          tk.END,
          f"=== CUSTOM TIME DETAILS ({loc_name}) [KP New / Swiss]"
          f" ===\n\n",
          "header",
      )
      self.text_area.insert(
          tk.END,
          f"Target Time      : {target_dt.strftime('%Y-%m-%d %I:%M:%S %p')}\n",
          "time",
      )
      self.text_area.insert(
          tk.END, f"Moon Longitude   : {res['Longitude']:.4f}°\n", "nak"
      )
      self.text_area.insert(
          tk.END, f"Moon Rashi       : {res['Rashi']}\n\n", "rashi"
      )
      self.text_area.insert(
          tk.END,
          f"Nakshatra        : {res['Nakshatra']} ({res['NakshatraLord']})\n",
          "nak",
      )
      self.text_area.insert(
          tk.END, f"Nakshatra Lord   : {res['NakshatraLord']}\n", "lord"
      )
      self.text_area.insert(
          tk.END, f"Sub-Lord (SL)    : {res['SubLord']}\n", "sl"
      )
      self.text_area.insert(
          tk.END, f"Sub-Sub-Lord     : {res['SubSubLord']}\n", "ssl"
      )
      self.text_area.insert(
          tk.END, f"Sub-Sub-Sub (SSSL): {res['SubSubSubLord']}\n\n", "sssl"
      )
      self.text_area.insert(
          tk.END, f"Remaining Time   : {res['RemainingHours']:.2f} hours\n", "time"
      )
    except Exception as e:
      messagebox.showerror(
          "Error",
          f"Sothik format-e Hour, Minute ebong AM/PM select korun!"
          f" ({str(e)})",
      )

  def generate_transitions(self):
    self.current_mode = "schedule"
    self.status_var.set("⏸️ Schedule Mode (Static)")
    self.update_coordinates()
    loc_name = self.loc_combo.get().strip()
    d_str = self.date_entry.get().strip()

    try:
      lat = float(self.lat_entry.get().strip())
      lon_val = float(self.lon_entry.get().strip())

      start_dt = datetime.strptime(f"{d_str} 00:00", "%Y-%m-%d %H:%M")
      current_real_time = datetime.now()

      curr_moon_lon, curr_moon_speed = get_swiss_moon_longitude(
          current_real_time, lat, lon_val
      )
      curr_res = calculate_kp_details(curr_moon_lon, curr_moon_speed)
      self.nl_val_lbl.config(text=f"NL: {curr_res['NakshatraLord']}")
      self.sl_val_lbl.config(text=f"SL: {curr_res['SubLord']}")
      self.ssl_val_lbl.config(text=f"SSL: {curr_res['SubSubLord']}")
      self.sssl_val_lbl.config(text=f"SSSL: {curr_res['SubSubSubLord']}")

      self.text_area.delete("1.0", tk.END)
      self.text_area.insert(
          tk.END,
          f"=== FULL DAY SCHEDULE FOR {d_str} ({loc_name}) [Swiss] ===\n\n",
          "header",
      )
      header_str = f"{'MARK':<4} | {'TIME':<10} | {'RASHI':<16} | {'NAKSHATRA & LORD':<22} | {'SL':<7} | {'SSL':<7} | {'SSSL':<7}\n"
      self.text_area.insert(tk.END, header_str, "time")
      self.text_area.insert(tk.END, "-" * 98 + "\n", "nak")

      prev_rashi = ""
      prev_nak = ""
      prev_sl = ""
      prev_ssl = ""
      prev_sssl = ""

      transitions_list = []

      for minute_offset in range(0, 24 * 60, 2):
        current_dt = start_dt + timedelta(minutes=minute_offset)
        moon_lon, moon_speed = get_swiss_moon_longitude(
            current_dt, lat, lon_val
        )
        res = calculate_kp_details(moon_lon, moon_speed)

        curr_rashi = res["Rashi"]
        curr_nak = res["Nakshatra"]
        curr_nl = res["NakshatraLord"]
        curr_sl = res["SubLord"]
        curr_ssl = res["SubSubLord"]
        curr_sssl = res["SubSubSubLord"]

        if (
            curr_rashi != prev_rashi
            or curr_nak != prev_nak
            or curr_sl != prev_sl
            or curr_ssl != prev_ssl
            or curr_sssl != prev_sssl
        ):
          transitions_list.append(
              (
                  current_dt,
                  curr_rashi,
                  curr_nak,
                  curr_nl,
                  curr_sl,
                  curr_ssl,
                  curr_sssl,
              )
          )
          prev_rashi = curr_rashi
          prev_nak = curr_nak
          prev_sl = curr_sl
          prev_ssl = curr_ssl
          prev_sssl = curr_sssl

      for i, trans in enumerate(transitions_list):
        t_dt, c_rashi, c_nak, c_nl, c_sl, c_ssl, c_sssl = trans
        time_str = t_dt.strftime("%I:%M %p")
        nak_with_lord = f"{c_nak} ({c_nl})"

        is_current = False
        if i < len(transitions_list) - 1:
          if t_dt <= current_real_time < transitions_list[i + 1][0]:
            is_current = True
        else:
          if current_real_time >= t_dt:
            is_current = True

        mark = "==>" if is_current else "   "
        tag_to_use = "highlight" if is_current else "nak"

        row_str = (
            f"{mark:<4} | {time_str:<10} | {c_rashi:<16} |"
            f" {nak_with_lord:<22} | {c_sl:<7} | {c_ssl:<7} | {c_sssl:<7}\n"
        )
        self.text_area.insert(tk.END, row_str, tag_to_use)

    except Exception as e:
      messagebox.showerror("Error", f"Somoshya hoyeche: {str(e)}")

  def auto_refresh_loop(self):
    try:
      if self.current_mode == "live":
        self.calculate_live()
    except Exception:
      pass
    self.root.after(5000, self.auto_refresh_loop)


if __name__ == "__main__":
  root = tk.Tk()
  app = KPMoonApp(root)
  root.mainloop()
