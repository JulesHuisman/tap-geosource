from typing import Dict, Generator, List
from osgeo import gdal, ogr, osr
import singer
import os


LOGGER = singer.get_logger()

# Enable GDAL/OGR exceptions
gdal.UseExceptions()
gdal.SetConfigOption('OGR_WFS_LOAD_MULTIPLE_LAYER_DEFN', 'NO')
gdal.SetConfigOption('OGR_LVBAG_LEGACY_ID', 'YES')

# A mapping from ogr types to jsonschema types
OGR_DATA_TYPES = {
    0: {'type': ['null', 'integer']},
    2: {'type': ['null', 'number']},
    4: {'type': ['null', 'string']},
    5: {'type': ['null', 'array'], 'items': {'type': ['null', 'string']}},
    # 9: {'type': ['null', 'string'], 'format': 'date'},
    # 11: {'type': ['null', 'string'], 'format': 'date-time'},
    12: {'type': ['null', 'integer']}
}


class GeoLayer:
    def __init__(self, layer: ogr.Layer, source_srid: int, target_srid: int) -> None:
        self.layer: ogr.Layer = layer
        self.source_srid: int = source_srid
        self.target_srid: int = target_srid
        self.should_transform: bool = self.source_is_target == False
        self.transformer = self.create_transformer()

    @property
    def name(self) -> str:
        """Get the name of the layer, we need to replace the ':' as it interferes with the bigquery table names 

        Returns:
            str: The name of the layer
        """
        return self.layer.GetName().replace(':', '_').lower()

    @property
    def has_geometry(self) -> bool:
        """Check if the layer has geometry

        Returns:
            bool: Returns true if the layer has geometry
        """
        return self.layer.GetGeomType() != 0

    @property
    def source_projection(self) -> osr.SpatialReference:
        """The original reference system from the data source

        Returns:
            osr.SpatialReference: The original spatial reference
        """
        if self.source_srid:
            source_reference = osr.SpatialReference()
            source_reference.ImportFromEPSG(self.source_srid)
        else:
            source_reference = self.layer.GetSpatialRef()

        # If there source reference system cannot be found
        if not source_reference:
            raise Exception(
                'Source spatial reference system cannot be infered, please supply it using the config'
            )

        return source_reference

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

    def create_transformer(self) -> osr.CoordinateTransformation:
        """Creates a transformer to re-project the ingested geometries

        Returns:
            osr.CoordinateTransformation: The spatial transformer object
        """
        return osr.CoordinateTransformation(self.source_projection, self.target_projection)

    @property
    def schema(self) -> Dict[str, Dict[str, List[str]]]:
        layer_schema = {}

        # Loop through the fields in the schema
        for field in self.layer.schema:
            layer_schema[field.name] = OGR_DATA_TYPES.get(
                field.type,
                {
                    'type': ['null', 'string']
                }
            )

        # Add a default geometry field if the layer has geometry
        if self.has_geometry:
            layer_schema['geometry'] = {
                'format': 'geography',
                **OGR_DATA_TYPES[4]
            }

        return layer_schema

    def features(self) -> Generator[Dict, None, None]:
        # Iterate over features
        feature = self.layer.GetNextFeature()
        while feature is not None:

            # Create a record with all the non spatial data
            record = {
                **feature.items()
            }

            # Add geometry to record if the layer has geometry
            if self.has_geometry:
                geometry = feature.GetGeometryRef()

                # If a re-projection is defined
                if self.should_transform:
                    geometry.Transform(self.transformer)

                record['geometry'] = geometry.ExportToJson()

            # Yield the record
            yield record

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
        source_srid = self.config.get('source_srid', None)
        include_layers = self.config.get('include_layers', None)

        # Fetch all layers
        layers = [GeoLayer(layer=layer,
                           source_srid=source_srid,
                           target_srid=target_srid)
                  for layer
                  in self.data_source if layer]

        # If a selection of layers was made
        if include_layers:
            return {layer.name: layer for layer in layers if layer.name in include_layers}
        # Return all layers
        else:
            return {layer.name: layer for layer in layers}
