from typing import Dict, Generator, List
from osgeo import gdal, ogr, osr

# Enable GDAL/OGR exceptions
gdal.UseExceptions()

gdal.SetConfigOption('OGR_WFS_LOAD_MULTIPLE_LAYER_DEFN', 'NO')

URL = 'WFS:https://geo.leefbaarometer.nl/leefbaarometer/ows?service=WFS&version=1.0.0'
# URL = '/home/jules/Github/thesis/data/dresden/gis_osm_adminareas_a_07_1.shp'

# A mapping from ogr types to jsonschema types
OGR_DATA_TYPES = {
    0: ['null', 'integer'],
    2: ['null', 'number'],
    4: ['null', 'string'],
    12: ['null', 'integer']
}


class GeoLayer:
    def __init__(self, layer: ogr.Layer, target_srid: int) -> None:
        self.layer: ogr.Layer = layer
        self.target_srid: int = target_srid

    @property
    def name(self) -> str:
        """Get the name of the layer, we need to replace the ':' as it interferes with the bigquery table names 

        Returns:
            str: The name of the layer
        """
        return self.layer.GetName().replace(':', '_')

    @property
    def source_projection(self) -> osr.SpatialReference:
        return self.layer.GetSpatialRef()

    @property
    def target_projection(self) -> osr.SpatialReference:
        target_reference = osr.SpatialReference()
        target_reference.ImportFromEPSG(self.target_srid)

        return target_reference

    @property
    def transformer(self) -> osr.CoordinateTransformation:
        return osr.CoordinateTransformation(self.source_projection, self.target_projection)

    @property
    def schema(self) -> Dict[str, Dict[str, List[str]]]:
        layer_schema = {}

        # Loop through the fields in the schema
        for field in self.layer.schema:
            layer_schema[field.name] = {
                'type': OGR_DATA_TYPES[field.type]
            }

        # Add a default geometry field
        layer_schema['geometry'] = {
            'type': OGR_DATA_TYPES[4]
        }

        return layer_schema

    def features(self) -> Generator[Dict, None, None]:
        # Iterate over features
        feature = self.layer.GetNextFeature()
        while feature is not None:
            geometry = feature.GetGeometryRef()

            # If a re-projection is defined
            if self.target_srid:
                geometry.Transform(self.transformer)

            # Yield the properties and geometry
            yield {
                **feature.items(),
                'geometry': geometry.ExportToWkt()
            }
            # Get the next feature
            feature = self.layer.GetNextFeature()


class GeoSource:
    def __init__(self, path: str, config: Dict) -> None:
        self.path: str = path
        self.data_source: ogr.DataSource = ogr.Open(path)
        self.config: Dict = config

    @property
    def layers(self) -> Dict[str, GeoLayer]:
        target_srid = self.config.get('target_srid', None)
        include_layers = self.config.get('include_layers', None)

        # Fetch all layers
        layers = [GeoLayer(layer=layer, target_srid=target_srid)
                  for layer in self.data_source if layer]

        # If a selection of layers was made
        if include_layers:
            return {layer.name: layer for layer in layers if layer.name in include_layers}
        # Return all layers
        else:
            return {layer.name: layer for layer in layers}
