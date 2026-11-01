import os

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌧️"),
    57: ("Freezing drizzle", "🌧️"),
    61: ("Light rain", "🌦️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌧️"),
    67: ("Freezing rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "🌨️"),
    80: ("Light showers", "🌦️"),
    81: ("Showers", "🌧️"),
    82: ("Heavy showers", "🌧️"),
    85: ("Snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def fetch_weather(city):
    geo_response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    geo_response.raise_for_status()
    locations = geo_response.json().get("results", [])
    if not locations:
        raise LookupError(f'No weather location found for "{city}".')

    location = locations[0]
    weather_response = requests.get(
        WEATHER_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m"
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        },
        timeout=10,
    )
    weather_response.raise_for_status()
    current = weather_response.json()["current"]
    description, icon = WEATHER_CODES.get(
        current.get("weather_code"), ("Unknown conditions", "🌡️")
    )

    return {
        "city": location["name"],
        "region": location.get("admin1", ""),
        "country": location.get("country_code", ""),
        "temperature": round(current["temperature_2m"]),
        "feels_like": round(current["apparent_temperature"]),
        "humidity": current["relative_humidity_2m"],
        "wind_speed": round(current["wind_speed_10m"]),
        "description": description,
        "icon": icon,
    }


@app.get("/")
def home():
    return render_template("weather.html", city=request.args.get("city", "").strip())


@app.post("/")
def weather():
    city = request.form.get("city", "").strip()
#    city = "Cleveland, oh"
    if not city:
        return render_template("weather.html", error="Enter a city to see the weather."), 400

    try:
        weather_data = fetch_weather(city)
    except LookupError as error:
        return render_template("weather.html", city=city, error=str(error)), 404
    except (requests.RequestException, KeyError, ValueError):
        return (
            render_template(
                "weather.html",
                city=city,
                error="The weather service is unavailable. Please try again.",
            ),
            502,
        )

    return render_template("weather.html", city=city, weather=weather_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5052")), debug=True)