from typing import Dict, Generator, List
from osgeo import gdal, ogr, osr

# Enable GDAL/OGR exceptions
gdal.UseExceptions()
gdal.SetConfigOption('OGR_WFS_LOAD_MULTIPLE_LAYER_DEFN', 'NO')

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
        self.should_transform: bool = self.source_is_target == False

    @property
    def name(self) -> str:
        """Get the name of the layer, we need to replace the ':' as it interferes with the bigquery table names 

        Returns:
            str: The name of the layer
        """
        return self.layer.GetName().replace(':', '_')

    @property
    def source_projection(self) -> osr.SpatialReference:
        """The original reference system from the data source

        Returns:
            osr.SpatialReference: The original spatial reference
        """
        return self.layer.GetSpatialRef()

    @property
    def target_projection(self) -> osr.SpatialReference:
        """The target reference system, defined by the user

        Returns:
            osr.SpatialReference: The target spatial reference
        """
        target_reference = osr.SpatialReference()
        target_reference.ImportFromEPSG(self.target_srid)
        return target_reference

    @property
    def source_is_target(self) -> bool:
        """Check if the source projection is the same as the target
        projection.

        Returns:
            bool: True, if source projection is equal to the target projection
        """
        if not self.target_srid:
            return True
        else:
            is_same = self.source_projection.IsSame(self.target_projection)
            return is_same == 1

    @property
    def transformer(self) -> osr.CoordinateTransformation:
        """Creates a transformer to re-project the ingested geometries

        Returns:
            osr.CoordinateTransformation: The actual transformer object
        """
        return osr.CoordinateTransformation(self.source_projection, self.target_projection)

    @property
    def schema(self) -> Dict[str, Dict[str, List[str]]]:
        layer_schema = {}

        # Loop through the fields in the schema
        for field in self.layer.schema:
            layer_schema[field.name] = {
                'type': OGR_DATA_TYPES.get(field.type, 'string')
            }

        # Add a default geometry field
        layer_schema['geometry'] = {
            'format': 'geography',
            'type': OGR_DATA_TYPES[4]
        }

        return layer_schema

    def features(self) -> Generator[Dict, None, None]:
        # Iterate over features
        feature = self.layer.GetNextFeature()
        while feature is not None:
            geometry = feature.GetGeometryRef()

            # If a re-projection is defined
            if self.should_transform:
                geometry.Transform(self.transformer)

            # Yield the properties and geometry
            yield {
                **feature.items(),
                'geometry': geometry.ExportToJson()
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
