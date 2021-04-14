import singer
from typing import Dict
from singer.schema import Schema
from tap_geosource.geo import GeoSource

LOGGER = singer.get_logger()


def generate_schemas(config: Dict) -> Dict:
    """Generate schemas based on the files or urls supplied in the config

    Args:
        config (Dict): Configuration

    Returns:
        Dict: Return a dictionary with stream_id: schema, key value pairs
    """
    # Storage place for the individual schemas
    schemas = {}

    # Create a geo datasource instance
    geo_source = GeoSource(path=config['path'], config=config)

    # Each layer is a stream
    for layer_name, layer in geo_source.layers.items():
        LOGGER.info(f'Found layer {layer_name}')
        schemas[layer_name] = Schema.from_dict({
            'type': ['null', 'object'],
            'additionalProperties': False,
            'selected': True,
            'properties': layer.schema
        })

    return schemas
