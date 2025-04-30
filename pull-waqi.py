#!/usr/bin/env python3
import requests
import sys
from datetime import datetime

OUTFILE = "/var/lib/node_exporter/textfile_collector/waqi.prom"
TOKEN = "ssssssssssssssssssssssssss"

STATIONS = {
    "Talbiye": "H5784",
    "Central Bus Station": "H8655",
    "Sanhedriya": "H2966",
    "Baka": "H2985",
    "Kfar Etzion": "H2986",
    "Tel Aviv": "H5783"
}

def fetch_station(station_id):
    url = f"https://api.waqi.info/feed/@{station_id}/?token={TOKEN}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok":
            raise ValueError(f"API returned error for station {station_id}")

        d = data["data"]
        iaqi = d.get("iaqi", {})
        geo = d["city"].get("geo", [None, None])
        station_name = d["city"].get("name", "unknown").replace('"', "'")
        time_unix = d["time"].get("v")
        dominentpol = d.get("dominentpol", "unknown")

        label = f'station="{station_name}"'

        metrics = [
            ("waqi_aqi", d.get("aqi")),
            ("waqi_pm25", iaqi.get("pm25", {}).get("v")),
            ("waqi_pm10", iaqi.get("pm10", {}).get("v")),
            ("waqi_co", iaqi.get("co", {}).get("v")),
            ("waqi_no2", iaqi.get("no2", {}).get("v")),
            ("waqi_o3", iaqi.get("o3", {}).get("v")),
            ("waqi_temp_c", iaqi.get("t", {}).get("v")),
            ("waqi_humidity", iaqi.get("h", {}).get("v")),
            ("waqi_pressure", iaqi.get("p", {}).get("v")),
            ("waqi_wind", iaqi.get("w", {}).get("v")),
            ("waqi_geo_lat", geo[0]),
            ("waqi_geo_lon", geo[1]),
            ("waqi_last_updated", time_unix),
        ]

        lines = [f"# WAQI scrape for station @{station_id} — Dominant pollutant: {dominentpol}"]
        for name, value in metrics:
            if value is not None:
                lines.append(f'{name}{{{label}}} {value}')

        return "\n".join(lines)

    except Exception as e:
        sys.stderr.write(f"Failed for station {station_id}: {e}\n")
        return None

def main():
    output_lines = [f"# Multi-station WAQI export - {datetime.utcnow().isoformat()}Z"]
    # Write HELP/TYPE lines for each metric at the top
    metric_headers = [
        ("waqi_aqi", "Air Quality Index"),
        ("waqi_pm25", "PM2.5 µg/m³"),
        ("waqi_pm10", "PM10 µg/m³"),
        ("waqi_co", "Carbon Monoxide (CO) ppm"),
        ("waqi_no2", "Nitrogen Dioxide (NO2) ppb"),
        ("waqi_o3", "Ozone (O3) ppb"),
        ("waqi_temp_c", "Temperature °C"),
        ("waqi_humidity", "Humidity %"),
        ("waqi_pressure", "Pressure hPa"),
        ("waqi_wind", "Wind m/s"),
        ("waqi_geo_lat", "Sensor latitude"),
        ("waqi_geo_lon", "Sensor longitude"),
        ("waqi_last_updated", "Last reading timestamp (Unix)"),
    ]
    for name, desc in metric_headers:
        output_lines.append(f"# HELP {name} {desc}")
        output_lines.append(f"# TYPE {name} gauge")
    for station_id in STATIONS.values():
        block = fetch_station(station_id)
        if block:
            output_lines.append(block)
    with open(OUTFILE, "w") as f:
        f.write("\n\n".join(output_lines) + "\n")

if __name__ == "__main__":
    main()