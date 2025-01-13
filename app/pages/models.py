from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from app.extensions import db
from sqlalchemy import text, or_

class Page(ResourceMixin):
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    active = db.Column(db.Boolean, default=True)
    route = db.Column(FmtString(128), nullable=False, unique=True)
    auth = db.Column(db.Boolean, default=True)
    content = db.Column(db.Text)

    def __repr__(self):
        return self.name

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Page.name.ilike(search_query),
                        Page.route.ilike(search_query),)

        return or_(*search_chain)
