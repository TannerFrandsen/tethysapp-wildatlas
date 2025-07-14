from datetime import datetime, timezone
from dateutil import parser
from django.http import HttpResponseBadRequest
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from tethys_sdk.gizmos import MVView
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller
import json
import os

from .app import App
from .models import Animal
from .models import Sighting


@controller(name="home")
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

    def compose_layers(self, request, map_view, *args, **kwargs):
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
                'path': os.path.join(os.path.dirname(__file__), 'resources', 'YellowstoneNationalPark.geojson'),
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


def datetime_to_age(date):
    return (datetime.now(timezone.utc) - date).total_seconds() / 3600

