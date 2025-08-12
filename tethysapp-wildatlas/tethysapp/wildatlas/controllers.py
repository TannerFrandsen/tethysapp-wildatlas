from datetime import datetime, timezone
from dateutil import parser
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from tethys_sdk.gizmos import MVView
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller
import json
import os
from pathlib import Path

from .app import App
from .models import Animal
from .models import Sighting


@controller(name="home", app_resources=True)
class HomeMap(MapLayout):
    app = App
    base_template = f'{App.package}/base.html'
    map_title = 'Wild Atlas'
    map_subtitle = 'Animal Sightings'
    basemaps = ['OpenStreetMap', 'ESRI']
    show_properties_popup = True

    def build_geojson_layers(self, configs, selectable=True):
        layers = []
        for config in configs:
            with open(config['path'], 'r', encoding='utf-8') as f:
                geojson = json.load(f)

            layer = self.build_geojson_layer(
                geojson=geojson,
                layer_name=config['name'],
                layer_title=config['title'],
                layer_variable=config['variable'],
                visible=True,
                selectable=selectable
            )
            layers.append(layer)
        return layers

    def compose_layers(self, request, map_view, app_resources, *args, **kwargs):
        sightings = Sighting.all()
        features = []

        for sighting in sightings:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [sighting.longitude, sighting.latitude]
                },
                'properties': {
                    'Animal': (
                        f'{sighting.animal.name} '
                        f'<img src="{sighting.animal.logo_path}" '
                        f'alt="{sighting.animal.name}" width="30" height="30" border="0">'
                    ),
                    'Date': f'{sighting.date_time.isoformat()}',
                    'Age': f'{datetime_to_age(sighting.date_time):.0f} hours',
                    'Sighting Id': str(sighting.id),
                    'pin_path': sighting.animal.pin_path
                }
            }
            features.append(feature)

        sightings_collection = {
            'type': 'FeatureCollection',
            'features': features,
            'crs': {
                'type': 'name',
                'properties': {
                    'name': 'EPSG:4326'
                }
            }
        }

        sightings_layer = self.build_geojson_layer(
            geojson=sightings_collection,
            layer_name='Animal Sightings',
            layer_title='Animal Sightings',
            layer_variable='sightings',
            visible=True,
            selectable=True
        )

        national_parks_configs = [
            {
                'path': Path(app_resources.path) / 'YellowstoneNationalPark.geojson',
                'name': 'Yellowstone National Park',
                'title': 'Yellowstone National Park',
                'variable': 'Yellowstone National Park'
            },
        ]

        national_park_layers = self.build_geojson_layers(national_parks_configs, selectable=False)

        layer_groups = [
            self.build_layer_group(
                id='Sightings',
                display_name='Layers',
                layer_control='checkbox',
                layers=[sightings_layer]
            ),
            self.build_layer_group(
                id='all-layers',
                display_name='National Parks',
                layer_control='checkbox',
                layers=[*national_park_layers]
            )
        ]

        if len(sightings) < 2:
            # No sightings, zoom all the way out.
            extent = [-180.0, -90.0, 180.0, 90.0]
        else:
            min_lat = min(s.latitude for s in sightings)
            max_lat = max(s.latitude for s in sightings)
            min_lon = min(s.longitude for s in sightings)
            max_lon = max(s.longitude for s in sightings)
            extent = [min_lon, max_lat, max_lon, min_lat]

        map_view.view = MVView(
            projection='EPSG:4326',
            extent=extent,
        )

        return layer_groups


# TODO add AnimalId validation
def process_sighting_form(post_data):
    """
    Clean and validate form POST data.
    Returns bool is valid, dict of parsed data, string error message if invalid.
    """
    cleaned_data = {}
    error_messages = []
    try:
        dt = parser.isoparse(post_data.get('date_time', ''))
        dt_utc = dt.astimezone(timezone.utc)

        if dt_utc > datetime.now(timezone.utc):
            error_messages.append({'category': "danger", 'text': 'Date/time cannot be in the future.'})

        cleaned_data['date_time'] = dt_utc
    except (ValueError, TypeError):
        error_messages.append({'category': "danger", 'text': 'Invalid or missing date/time.'})

    try:
        cleaned_data['animal_id'] = int(post_data.get('animalId', ''))
    except (TypeError, ValueError):
        error_messages.append({'category': "danger", 'text': 'Invalid or missing animal ID.'})

    try:
        latitude = float(post_data.get('latitude', ''))
        longitude = float(post_data.get('longitude', ''))
    except (TypeError, ValueError):
        error_messages.append({'category': "danger", 'text': 'Invalid or missing latitude/longitude.'})

    if not (-90 <= latitude <= 90):
        error_messages.append({'category': "danger", 'text': 'Latitude must be between -90 and 90.'})
    cleaned_data['latitude'] = latitude

    if not (-180 <= longitude <= 180):
        error_messages.append({'category': "danger", 'text': 'Longitude must be between -180 and 180.'})
    cleaned_data['longitude'] = longitude

    valid = len(error_messages) == 0
    return valid, cleaned_data, error_messages


def datetime_to_age(date):
    return (datetime.now(timezone.utc) - date).total_seconds() / 3600


# Controller for adding a new animal sighting
@controller(url='sighting/add')
def add_sighting(request):
    registered_animals = Animal.all()

    registered_animals.sort(key=lambda x: x.name)

    selectable_animals = []
    for animal in sorted(registered_animals, key=lambda x: x.name):
        selectable_animals.append(
            {
                'id': animal.id,
                'name': animal.name,
                'logo_path': animal.logo_path
            }
        )

    if request.method == 'POST':
        valid, valid_data, flash_messages = process_sighting_form(request.POST)
        if not valid:
            context = {
                'messages': flash_messages,
                'animals': selectable_animals,
            }
            return App.render(request, 'add_sighting.html', context)

        Sighting.add(
            animal_id=valid_data['animal_id'],
            date_time=valid_data['date_time'],
            latitude=valid_data['latitude'],
            longitude=valid_data['longitude']
        )
        return App.redirect(App.reverse('home'))

    registered_animals.sort(key=lambda x: x.name)

    context = {
        'animals': selectable_animals,
    }
    return App.render(request, 'add_sighting.html', context)


@controller(url='sighting/list')
def list_sightings(request):
    sightings = Sighting.all()
    sightings_data = []
    for sighting in sightings:
        sighting_age = datetime_to_age(sighting.date_time)
        sightings_data.append({
            'id': sighting.id,
            'date_time': sighting.date_time.isoformat(),
            'age_in_hours': f'{sighting_age:.0f}',
            'latitude': sighting.latitude,
            'longitude': sighting.longitude,
            'name': sighting.animal.name,
            'logo_path': sighting.animal.logo_path
        })
    sightings_data.sort(key=lambda x: x['date_time'], reverse=True)
    context = {
        'sightings': sightings_data
    }
    return App.render(request, 'list_sightings.html', context)


@api_view(['DELETE'])
@controller(url='sighting/delete/{sighting_id}', methods=['POST'], name='wildatlas_sighting_delete')
@authentication_classes((TokenAuthentication,))
def delete_sighting_view(request, sighting_id):
    if request.method == 'POST':
        Sighting.delete(sighting_id)
        return App.redirect(App.reverse('list_sightings'))

    return App.redirect(App.reverse('list_sightings'))
