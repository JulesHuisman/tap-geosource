import singer
from typing import Dict
from osgeo import gdal, ogr
from singer.schema import Schema
from pathlib import Path
from pprint import pprint

LOGGER = singer.get_logger()

# Enable GDAL/OGR exceptions
gdal.UseExceptions()


def geo_generator(stream: singer.CatalogEntry):
    # Path is stored in the stream name
    path = stream.stream

    # Open or load the geosource
    geo_file = ogr.Open(path)

    # Get the next layer of the geosource
    layer = geo_file.GetLayer()

    for i in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(i)

        yield {
            **feature.items(),
            # 'geometry': str(feature.geometry())
        }
