from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


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


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
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
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == "POST":
        title = request.form['title']
        body = request.form['body']
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
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/detail')
def detail(id):
    db = get_db()
    post = get_post(id, check_author=False)
    likes = get_likes(id)
    comments = get_comments(id)
    return render_template('blog/detail.html', post=post, likes=likes, comments=comments)


@bp.route('/<int:id>/like')
@login_required
def like(id):
    db = get_db()
    post = get_post(id)
    new_value = request.args.get('new_value')
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
