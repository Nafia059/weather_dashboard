from http.server import BaseHTTPRequestHandler
import os
import sys
import mimetypes
from urllib.parse import urlparse, parse_qs
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_dashboard.settings')

import django
django.setup()

from django.template.loader import render_to_string
from weather.views import get_weather, get_forecast, get_background

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path.startswith('/static/'):
                self._serve_static(path)
                return

            query = parse_qs(parsed.query)
            city = query.get('city', ['Sahiwal'])[0]

            weather = get_weather(city)
            hourly_forecast = []
            weekly_forecast = []

            if weather:
                background_image = get_background(weather['description'])
                city_display = weather['city']

                forecast_data = get_forecast(city)
                if forecast_data:
                    hourly_data = forecast_data['list'][:8]
                    for hour in hourly_data:
                        hourly_forecast.append({
                            'time': datetime.fromtimestamp(hour['dt']).strftime('%H:%M'),
                            'temp': int(hour['main']['temp']),
                            'icon': hour['weather'][0]['icon'],
                        })

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
                            daily_data[day]['temp_min'] = min(daily_data[day]['temp_min'], entry['main']['temp_min'])
                            daily_data[day]['temp_max'] = max(daily_data[day]['temp_max'], entry['main']['temp_max'])

                    for day_data in daily_data.values():
                        weekly_forecast.append({
                            'day': day_data['date'].strftime('%A'),
                            'temp_min': int(day_data['temp_min']),
                            'temp_max': int(day_data['temp_max']),
                            'icon': day_data['icon']
                        })
                        if len(weekly_forecast) >= 7:
                            break
            else:
                background_image = 'default.jpg'
                city_display = city

            context = {
                'weather': weather,
                'background_image': background_image,
                'city': city_display,
                'hourly_forecast': hourly_forecast,
                'weekly_forecast': weekly_forecast,
            }

            html = render_to_string('weather/home.html', context)
            html_bytes = html.encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        except Exception as e:
            error_msg = f'Error: {str(e)}'.encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(error_msg)))
            self.end_headers()
            self.wfile.write(error_msg)

    def _serve_static(self, path):
        rel_path = path.lstrip('/')
        file_path = os.path.join(BASE_DIR, rel_path)

        if not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            return

        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        with open(file_path, 'rb') as f:
            data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'public, max-age=86400')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self.do_GET()
