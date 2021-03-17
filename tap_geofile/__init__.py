#!/usr/bin/env python3
import os
import json
from pprint import pprint
from tap_geosource.geo import GeoSource
import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema
from tap_geosource.discovery import generate_schemas
from tap_geosource.sync import geo_generator


REQUIRED_CONFIG_KEYS = ['path']
LOGGER = singer.get_logger()


def discover(config):
    streams = []
    schemas = generate_schemas(config)

    for stream_id, schema in schemas.items():
        stream_metadata = []
        key_properties = []

        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )

    return Catalog(streams)


def sync(config, state, catalog):
    """ Sync data from tap source """
    geo_source = GeoSource(path=config['path'], config=config)

    for stream in catalog.get_selected_streams(state):
        # Fetch the layer from the geo source
        layer = geo_source.layers[stream.tap_stream_id]

        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        for row in layer.features():
            # write one or more rows to the stream:
            singer.write_records(stream.tap_stream_id, [row])

    # # Loop over selected streams in catalog
    # for stream in catalog.get_selected_streams(state):
    #     LOGGER.info("Syncing stream:" + stream.tap_stream_id)

    #     singer.write_schema(
    #         stream_name=stream.tap_stream_id,
    #         schema=stream.schema.to_dict(),
    #         key_properties=stream.key_properties,
    #     )

    #     for row in geo_generator(stream):
    #         # write one or more rows to the stream:
    #         singer.write_records(stream.tap_stream_id, [row])
    # return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover(args.config)
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover(args.config)
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
