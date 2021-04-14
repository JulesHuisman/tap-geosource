from tap_geosource.geo import GeoSource
import singer
from singer import utils
from singer.catalog import Catalog, CatalogEntry
from singer.metrics import record_counter
from tap_geosource.discovery import generate_schemas


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

        # Log some info about the stream
        LOGGER.info(
            f'Syncing stream: {stream.tap_stream_id} | Transformation: {str(layer.should_transform)}')

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        with record_counter(log_interval=10) as counter:
            for row in layer.features():
                # Write a row to the stream
                singer.write_records(stream.tap_stream_id, [row])

                # Log the records
                counter.increment()


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
