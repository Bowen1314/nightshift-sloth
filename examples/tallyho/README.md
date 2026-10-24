# tallyho

A tiny expense ledger for your terminal. No accounts, no cloud, one JSON file.

## Install

```sh
pip install -e .
```

Or run it straight from a checkout with `python -m tally`.

## Usage

```sh
tally add 4.50 --category coffee
tally list
tally report
```

Entries live in `~/.tallyho.json`. Set `TALLY_FILE` to use a different file.

## Development

```sh
python3 -m unittest discover -s tests
```

## License

MIT
