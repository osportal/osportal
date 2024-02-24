from app.admin.utils import get_settings_value
from app.extensions import db
from app.utils.util_sqlalchemy import ResourceMixin
from datetime import datetime
from flask import request, current_app
from sqlalchemy import text, or_


class Post(db.Model, ResourceMixin):
    __tablename__ = 'post'
    __searchable__ = ['title', 'content']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pin = db.Column(db.Boolean, nullable=False, default=False)
    # relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
                        index=True, nullable=False)
    #post_author = db.relationship('User', foreign_keys=[user_id])
    comments = db.relationship('Comment', backref='parent', passive_deletes=True, lazy='dynamic')

    def __repr__(self):
        return self.name

    def pin(self):
        self.is_pin = True
        self.save()

    def unpin(self):
        self.is_pin = False
        self.save()


    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Post.name.ilike(search_query),
                        Post.content.ilike(search_query))

        return or_(*search_chain)

    def paginated_comments(self, page):
        sort_by = Comment.sort_by(request.args.get('sort', 'created_at'),
                               request.args.get('direction', 'desc'))
        order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
        comments = Comment.query \
                .filter(Comment.post_id==self.id) \
                .order_by(text(order_values)) \
                .paginate(page, get_settings_value('comments_per_page'), False)
        return comments


class Comment(db.Model, ResourceMixin):
    __tablename__ = 'comment'
    __searchable__ = ['text']
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    # relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, nullable=False)
    #parent = db.relationship('Post', foreign_keys=[post_id])
    #author = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return self.text

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Comment.text.ilike(search_query))

        return or_(*search_chain)
