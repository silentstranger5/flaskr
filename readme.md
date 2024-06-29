# Flaskr

This is an implementation of [Flaskr](https://flask.palletsprojects.com/en/3.0.x/tutorial/), a Flask tutorial blog page.
Upon the basis provided by the tutorial, this project implements features suggested in the [Last](https://flask.palletsprojects.com/en/3.0.x/tutorial/next/) section. Here is a list of them:

- Detail view of each post.
- Like / unlike post
- Comments
- Tags. Clicking a tag shows all the posts with that tag.
- A search box that filters the index page by name.
- Paged display. Only show 5 posts per page.
- Upload an image to go along with a post.
- Format posts using Markdown.

## How to build

Building should be fairly straightforward:

```
git clone https://github.com/silentstranger5/flaskr.git
cd flaskr
# activate your virtual environment here (platform dependent)
pip install -e .
flask --app flaskr init-db
flask --app flaskr run
```

You can use virtual environment before resolving dependencies. Read about it [here](https://docs.python.org/3/tutorial/venv.html)
If you want to deploy this server to production, you can build and install this project. In this case, setting up a virtual environment is necessary:

```
pip install build
python -m build --wheel
mkdir prod
cp dist/flaskr-1.0.0-py3-none-any.whl prod
cd prod
# activate your virtural environment here (platform dependent)
pip install flaskr-1.0.0-py3-none-any.whl
flask --app flaskr init-db
# this command generates a secret key; copy it into the clipboard
python -c 'import secrets; print(secrets.token_hex())'
# paste your secret key in this file as 'SECRET_KEY = <your key>'
vi .venv/var/flaskr-instance/config.py
pip install waitress
waitress-serve --host 127.0.0.1 --call 'flask:create_app'
```
