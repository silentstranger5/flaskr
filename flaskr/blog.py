from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db

import os.path


bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    offset = request.args.get('offset')
    if offset is None:
        offset = 0
    else:
        offset = int(offset) 

    length = db.execute(
        'SELECT COUNT(*) FROM post'
    ).fetchone()[0]

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
        ' LIMIT 5 OFFSET ?',
        (offset,)
    ).fetchall()
    tags = dict(tuple((post['id'], get_tags(post['id'])) for post in posts))

    return render_template(
        'blog/index.html', 
        posts=posts, 
        tags=tags, 
        offset=offset, 
        length=length
    )


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f'Post id {id} doesn\'t exist.')

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


def get_likes(id):
    likes = get_db().execute(
        'SELECT SUM(value) FROM like WHERE post_id = ?',
        (id,)
    ).fetchone()[0]

    if likes is None:
        likes = 0

    return likes


def get_comments(id):
    comments = get_db().execute(
        'SELECT *, username FROM comment'
        ' JOIN user ON comment.author_id = user.id'
        ' WHERE comment.post_id = ?',
        (id,)
    ).fetchall()

    return comments


def get_tags(id):
    tags = get_db().execute(
        'SELECT tag FROM tag'
        ' JOIN tag_post ON tag.id = tag_post.tag_id'
        ' WHERE tag_post.post_id = ?',
        (id,)
    ).fetchall()

    if tags is not None:
        tags = list(tag['tag'] for tag in tags)

    return tags


def insert_tags(id, tags):
    db = get_db()
    for tag in tags:
        current = db.execute(
            'SELECT * FROM tag WHERE tag = ?',
            (tag,)
        ).fetchone()
        if current is None:
            db.execute(
                'INSERT INTO tag (tag)'
                ' VALUES (?)',
                (tag,)
            )
    db.commit()
    for tag in tags:
        tag_id = db.execute(
            'SELECT id FROM tag WHERE tag = ?',
            (tag,)
        ).fetchone()['id']
        db.execute(
            'INSERT INTO tag_post (tag_id, post_id)'
            ' VALUES (?, ?)',
            (tag_id, id)
        )
    db.commit()


def get_image(id):
    image = get_db().execute(
        'SELECT path FROM image WHERE post_id = ?',
        (id,)
    ).fetchone()

    if image is not None:
        image = os.path.join(os.pardir, image['path'])

    return image


def upload_image(id, image):
    db = get_db()
    if image:
        path = os.path.join(
            'static',
            secure_filename(image.filename)
        )
        image.save(os.path.join(current_app.root_path, path))
        db.execute(
            'INSERT INTO image (path, post_id)'
            ' VALUES (?, ?)',
            (path, id)
        )
        db.commit()


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags']
        image = request.files['image']
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            if tags is not None:
                tags = tags.split()
            post_id = db.execute(
                'SELECT id FROM post WHERE'
                ' title = ? AND body = ? AND author_id = ?'
                ' ORDER BY created DESC'
                ' LIMIT 1',
                (title, body, g.user['id'])
            ).fetchone()['id']
            insert_tags(post_id, tags)
            upload_image(post_id, image)
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    tags = get_tags(id)
    tags = ' '.join(tags)
    image = get_image(id)

    if request.method == "POST":
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags']
        image = request.files['image']
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.execute(
                'DELETE FROM tag_post WHERE post_id = ?',
                (id,)
            )
            db.commit()
            if tags is not None:
                tags = tags.split()
            insert_tags(id, tags)

            images = db.execute(
                'SELECT path FROM image WHERE post_id = ?',
                (id,)
            ).fetchall()
            for image in images:
                path = os.path.join(current_app.root_path, image['path'])
                os.remove(path)

            db.execute(
                'DELETE FROM image WHERE post_id = ?',
                (id,)
            )
            db.commit()
            upload_image(id, image)

            return redirect(url_for('blog.index'))

    return render_template(
        'blog/update.html',
        post=post,
        tags=tags,
        image=image
    )


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db = get_db()
    image = db.execute(
        'SELECT path FROM image'
        ' WHERE post_id = ?',
        (post['id'],)
    ).fetchone()
    if image is not None:
        path = os.path.join(current_app.root_path, image['path'])
        os.remove(path)
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/detail')
def detail(id):
    post = get_post(id, check_author=False)
    likes = get_likes(id)
    tags = get_tags(id)
    comments = get_comments(id)
    image = get_image(id)

    return render_template(
        'blog/detail.html', 
        post=post, 
        tags=tags, 
        likes=likes, 
        comments=comments,
        image=image
    )


@bp.route('/<int:id>/like')
@login_required
def like(id):
    db = get_db()
    post = get_post(id)
    new_value = request.args.get('new_value')

    if not new_value:
        abort(400)

    new_value = int(new_value)
    value = db.execute(
        'SELECT value FROM like WHERE user_id = ? AND post_id = ?',
        (g.user['id'], post['id'])
    ).fetchone()
    if value is None:
        value = 0
        db.execute(
            'INSERT INTO like (user_id, post_id, value)'
            ' VALUES (?, ?, ?)',
            (g.user['id'], post['id'], value)
        )
        db.commit()
    else:
        value = value['value']
    if value == new_value:
        new_value = 0
    db.execute(
        'UPDATE like SET value = ? WHERE user_id = ? AND post_id = ?',
        (new_value, g.user['id'], post['id'])
    )
    db.commit()
    return redirect(url_for('blog.detail', id=post['id']))


@bp.route('/<int:id>/comment', methods=('POST',))
@login_required
def comment(id):
    body = request.form['body']
    error = None

    if not body:
        error = 'Comment is required'

    if error is not None:
        flash(error)
    else:
        db = get_db()
        db.execute(
            'INSERT INTO comment (author_id, post_id, body)'
            ' VALUES (?, ?, ?)',
            (g.user['id'], id, body)
        )
        db.commit()

    return redirect(url_for('blog.detail', id=id))


@bp.route('/tags/<tag>')
def tag_filter(tag):
    db = get_db()
    offset = request.args.get('offset')
    if offset is None:
        offset = 0
    else:
        offset = int(offset)
    length = db.execute(
        'SELECT COUNT(*) FROM post'
        ' JOIN tag_post ON post.id = tag_post.post_id'
        ' JOIN tag ON tag_post.tag_id = tag.id'
        ' JOIN user ON post.author_id = user.id'
        ' WHERE tag.tag = ?'
        ' ORDER BY created DESC',
        (tag,)
    ).fetchone()[0]
    posts = db.execute(
        'SELECT *, username FROM post'
        ' JOIN tag_post ON post.id = tag_post.post_id'
        ' JOIN tag ON tag_post.tag_id = tag.id'
        ' JOIN user ON post.author_id = user.id'
        ' WHERE tag.tag = ?'
        ' ORDER BY created DESC'
        ' LIMIT 5 OFFSET ?',
        (tag, offset)
    ).fetchall()
    tags = dict(tuple((post['id'], get_tags(post['id'])) for post in posts))

    return render_template(
        'blog/filter.html',
        posts=posts,
        tags=tags,
        offset=offset,
        length=length
    )


@bp.route('/search')
def search():
    db = get_db()
    query = request.args.get('query')
    offset = request.args.get('offset')

    if not query:
        abort(400, 'Search query is empty')

    if not offset:
        offset = 0
    else:
        offset = int(offset)

    length = db.execute(
        'SELECT COUNT(*) FROM post'
        ' JOIN user ON post.author_id = user.id'
        ' WHERE post.title LIKE ?'
        ' ORDER BY created DESC',
        (f'%{query}%',)
    ).fetchone()[0]

    posts = db.execute(
        'SELECT *, username FROM post'
        ' JOIN user ON post.author_id = user.id'
        ' WHERE post.title LIKE ?'
        ' ORDER BY created DESC'
        ' LIMIT 5 OFFSET ?',
        (f'%{query}%', offset)
    ).fetchall()
    tags = dict(tuple((post['id'], get_tags(post['id'])) for post in posts))

    return render_template(
        'blog/filter.html', 
        posts=posts, 
        tags=tags,
        length=length,
        offset=offset
    )
