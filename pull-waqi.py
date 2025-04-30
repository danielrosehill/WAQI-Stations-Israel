#!/usr/bin/env python3
import requests
import sys
from datetime import datetime

OUTFILE = "/var/lib/node_exporter/textfile_collector/waqi.prom"
TOKEN = "7242424242424242424242424242"

STATIONS = {
    "Talbiye": "H5784",
    "Central Bus Station": "H8655",
    "Sanhedriya": "H2966",
    "Baka": "H2985",
    "Kfar Etzion": "H2986",
    "Tel Aviv": "H5783"
}

def fetch_station(station_name, station_id):
    url = f"https://api.waqi.info/feed/@{station_id}/?token={TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok":
            raise ValueError(f"API returned error for {station_name} ({station_id})")

        d = data["data"]
        iaqi = d.get("iaqi", {})
        geo = d["city"].get("geo", [None, None])
        time_unix = d["time"].get("v")
        dominentpol = d.get("dominentpol", "unknown")

        label = f'station="{station_name}",id="{station_id}"'

        metrics = [
            ("waqi_aqi", d["aqi"], "Air Quality Index"),
            ("waqi_pm25", iaqi.get("pm25", {}).get("v"), "PM2.5 µg/m³"),
            ("waqi_pm10", iaqi.get("pm10", {}).get("v"), "PM10 µg/m³"),
            ("waqi_co", iaqi.get("co", {}).get("v"), "Carbon Monoxide (CO) ppm"),
            ("waqi_no2", iaqi.get("no2", {}).get("v"), "Nitrogen Dioxide (NO2) ppb"),
            ("waqi_o3", iaqi.get("o3", {}).get("v"), "Ozone (O3) ppb"),
            ("waqi_temp_c", iaqi.get("t", {}).get("v"), "Temperature °C"),
            ("waqi_humidity", iaqi.get("h", {}).get("v"), "Humidity %"),
            ("waqi_pressure", iaqi.get("p", {}).get("v"), "Pressure hPa"),
            ("waqi_wind", iaqi.get("w", {}).get("v"), "Wind m/s"),
            ("waqi_geo_lat", geo[0], "Sensor latitude"),
            ("waqi_geo_lon", geo[1], "Sensor longitude"),
            ("waqi_last_updated", time_unix, "Last reading timestamp (Unix)"),
        ]

        lines = [f"# WAQI scrape for {station_name} ({station_id}) — Dominant pollutant: {dominentpol}"]
        for name, value, desc in metrics:
            if value is not None:
                lines.append(f"# HELP {name} {desc}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f'{name}{{{label}}} {value}')
        return "\n".join(lines)

    except Exception as e:
        sys.stderr.write(f"Failed for {station_name} ({station_id}): {e}\n")
        return None


def main():
    output_lines = [f"# Multi-station WAQI export - {datetime.utcnow().isoformat()}Z"]
    for name, sid in STATIONS.items():
        block = fetch_station(name, sid)
        if block:
            output_lines.append(block)
    with open(OUTFILE, "w") as f:
        f.write("\n\n".join(output_lines) + "\n")


if __name__ == "__main__":
    main()
