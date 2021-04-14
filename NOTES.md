# Notes

Pipe into a csv file
```
~/.virtualenvs/tap-geosource/bin/tap-geosource -c config.json | ~/.virtualenvs/target-csv/bin/target-csv
```

`python3 -m venv ~/.virtualenvs/tap-geosource`
`source ~/.virtualenvs/tap-geosource/bin/activate`

## Config
```
path
include_layers
```

include_layers: ["leefbaarometer:pc6_2018"]

```
~/.virtualenvs/tap-geosource/bin/tap-geosource -c config.json | ~/.virtualenvs/target-postgres/bin/target-postgres -c ~/singer.io/target_postgres_config.json >> state.json
```

```
export GOOGLE_APPLICATION_CREDENTIALS=/home/jules/singer.io/target_bigquery_secret.json

~/.virtualenvs/tap-geosource/bin/tap-geosource -c config.json | ~/.virtualenvs/target-bigquery/bin/target-bigquery -c ~/singer.io/target_bigquery_config.json >> state.json
~/.cache/pypoetry/virtualenvs/tap-scrapy-ZAii4hvM-py3.6/bin/tap-scrapy --config ~/Github/tap-scrapy/config.json | ~/.virtualenvs/target-bigquery/bin/target-bigquery -c ~/singer.io/target_bigquery_config.json >> state.json
```