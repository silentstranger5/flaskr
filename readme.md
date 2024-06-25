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
pip install -e .
flask --app flaskr init-db
flask --app flaskr run
```

You optionally can use virtual environment before resolving dependencies. You can read about it [here](https://docs.python.org/3/tutorial/venv.html)
