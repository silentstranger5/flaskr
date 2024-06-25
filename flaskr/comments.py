from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import datetime

bp = Blueprint('comments', __name__, url_prefix='/comments')


def get_comment(id):
    comment = get_db().execute(
        'SELECT *, username FROM comment'
        ' JOIN user ON comment.author_id = user.id'
        ' WHERE comment.id = ?',
        (id,)
    ).fetchone()
    
    if comment is None:
        abort(404, f"Comment id {id} doesn't exist.")

    if comment['author_id'] != g.user['id']:
        abort(403)

    return comment


@bp.route('<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    comment = get_comment(id)

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Body can not be empty.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE comment SET body = ?, created = ?'
                ' WHERE id = ?',
                (body, datetime.datetime.now().isoformat(), id)
            )
            db.commit()
            post_id = comment['post_id']

            return redirect(url_for('blog.detail', id=post_id))

    return render_template('comments/update.html', comment=comment)


@bp.route('<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    comment = get_comment(id)
    post_id = comment['post_id']
    db = get_db()
    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.detail', id=post_id))
