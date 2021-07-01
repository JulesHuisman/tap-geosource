# Tap Geosource

Singer.io tap to ingest geospatial files.

## Setup
Make sure you have GDAL installed in the environment where you are running this tap. An installation instruction can be found here: [installing gdal](https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html)

## Config
`path (str)` The location of the geospatial file (/data/file.shp) (wfs:https://wfssource.com/wfs)

`include_layers (list(str))` Which layers to process from the source (["layer_1", "layer_2"])

`source_srid (int)` The source coordinate reference system code (28664)

`target_srid (int)` The target coordinate reference system code (4326)
