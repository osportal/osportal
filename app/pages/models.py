from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from app.extensions import db

class Page(db.Model, ResourceMixin):
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    active = db.Column(db.Boolean, default=True)
    # TODO change nullable=False
    route = db.Column(FmtString(128), nullable=True, unique=True)
    auth = db.Column(db.Boolean, default=True)
    content = db.Column(db.Text)

    def __repr__(self):
        return self.name

    @classmethod
    def bulk_delete(cls, ids):
        delete_count = 0
        for id in ids:
            page = Page.query.get(id)
            if page is None:
                continue
            page.delete()
            delete_count += 1
        return delete_count

    @classmethod
    def bulk_disable(cls, ids):
        disable_count = 0
        for id in ids:
            page = Page.query.get(id)
            if page is None:
                continue
            page.active = False
            page.save()
            disable_count += 1
        return disable_count


    @classmethod
    def bulk_enable(cls, ids):
        enable_count = 0

        for id in ids:
            page = Page.query.get(id)
            if page is None:
                continue
            page.active = True
            page.save()
            enable_count += 1
        return enable_count


