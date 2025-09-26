from django.shortcuts import render
import requests
from datetime import datetime
from .models import City  # optional, if you want to save searched cities

API_KEY = '079385bdca3142840ed95950590610a2'

def get_weather(city):
    """
    Fetch weather data from OpenWeatherMap API for a given city in Pakistan.
    Returns a dictionary with weather info or None if city is invalid.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},PK&units=metric&appid={API_KEY}"
    response = requests.get(url).json()
    
    # Handle invalid city
    if response.get("cod") != 200:
        return None

    weather = {
        'city': response['name'],  # Proper city name from API
        'temp': int(response['main']['temp']),
        'feels_like': int(response['main']['feels_like']),
        'description': response['weather'][0]['main'],
        'icon': response['weather'][0]['icon'],
        'sunrise': response['sys']['sunrise'],
        'sunset': response['sys']['sunset'],
    }
    return weather

def get_forecast(city):
    """
    Fetch 5-day / 3-hour forecast data from OpenWeatherMap API for a given city in Pakistan.
    Returns a dictionary with forecast list or None.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city},PK&units=metric&appid={API_KEY}"
    response = requests.get(url).json()

    if response.get("cod") != "200":
        return None
    
    return response

def get_background(weather_desc):
    """
    Determine background image filename based on current time and weather description.
    Returns a string like 'morning_clear.jpg'.
    """
    hour = datetime.now().hour

    # Determine time of day
    if hour < 6:
        time_of_day = 'night'
    elif hour < 12:
        time_of_day = 'morning'
    elif hour < 18:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    # Determine weather type
    if 'Rain' in weather_desc or 'Drizzle' in weather_desc:
        weather_type = 'rainy'
    elif 'Thunderstorm' in weather_desc:
        weather_type = 'storm'
    elif 'Cloud' in weather_desc or 'Haze' in weather_desc or 'Smoke' in weather_desc:
        weather_type = 'cloudy'
    else:
        weather_type = 'clear'

    return f"{time_of_day}_{weather_type}.jpg"

def get_icon_for_time(hour, weather_desc):
    """
    Decide whether to show sun or moon depending on hour and weather.
    """
    if hour >= 18 or hour < 6:  # Night time
        return "🌙"
    else:  # Day time
        return "☀️"


def home(request):
    """
    Main view for the weather dashboard.
    Default city is Sahiwal on first load.
    Allows searching for any Pakistani city via GET parameter 'city'.
    """
    # Get city from GET parameter or default to Sahiwal
    city_name = request.GET.get('city', 'Sahiwal')
    
    # Optional: save searched city
    # if city_name and not City.objects.filter(name__iexact=city_name).exists():
    #     City.objects.create(name=city_name)
    
    # Fetch current weather data
    weather = get_weather(city_name)
    
    # Initialize forecast variables
    hourly_forecast = []
    weekly_forecast = []

    if weather:
        background_image = get_background(weather['description'])
        city_display = weather['city']  # Use API-returned city name

        # Fetch and process forecast data
        forecast_data = get_forecast(city_name)
        if forecast_data:
            # Hourly forecast (first 8 entries for 24 hours)
            hourly_data = forecast_data['list'][:8]
            for hour in hourly_data:
                hourly_forecast.append({
                    'time': datetime.fromtimestamp(hour['dt']).strftime('%H:%M'),
                    'temp': int(hour['main']['temp']),
                    'icon': hour['weather'][0]['icon'],
                })

            # Weekly forecast (one entry per day)
            daily_data = {}
            for entry in forecast_data['list']:
                day = datetime.fromtimestamp(entry['dt']).strftime('%A')
                if day not in daily_data:
                    daily_data[day] = {
                        'date': datetime.fromtimestamp(entry['dt']),
                        'temp_min': entry['main']['temp_min'],
                        'temp_max': entry['main']['temp_max'],
                        'icon': entry['weather'][0]['icon']
                    }
                else:
                    # Update min/max temperatures for the day
                    daily_data[day]['temp_min'] = min(daily_data[day]['temp_min'], entry['main']['temp_min'])
                    daily_data[day]['temp_max'] = max(daily_data[day]['temp_max'], entry['main']['temp_max'])
            
            # Convert dictionary to a list and append to weekly_forecast
            for day_data in daily_data.values():
                weekly_forecast.append({
                    'day': day_data['date'].strftime('%A'),
                    'temp_min': int(day_data['temp_min']),
                    'temp_max': int(day_data['temp_max']),
                    'icon': day_data['icon']
                })
                # Limit to 7 days
                if len(weekly_forecast) >= 7:
                    break

    else:
        background_image = 'default.jpg'
        city_display = city_name

    context = {
        'weather': weather,
        'background_image': background_image,
        'city': city_display,
        'hourly_forecast': hourly_forecast,
        'weekly_forecast': weekly_forecast,
    }
    return render(request, 'weather/home.html', context)