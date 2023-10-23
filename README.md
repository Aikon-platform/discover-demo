# DTI-demo
A web interface as demo for DTI clustering

## Development

See [api/README.md] and [front/README.md] for individual part installations.

### Running everything

To start everything in one killable process, run

    (trap 'kill 0' SIGINT; (cd api/ && source venv/bin/activate && flask --app app.main run --debug) & (cd api/ && source venv/bin/activate && dramatiq app.main -p 1 -t 1) & (cd front/ && source venv/bin/activate && python manage.py runserver); )

You can add `--watch` to dramatiq part (if you have run `pip install dramatiq[watch]` first).