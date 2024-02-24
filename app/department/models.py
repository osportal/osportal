from app.extensions import db
from app.event.models import Event
from app.user.models import User
from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from sqlalchemy import or_


class DepartmentMembers(db.Model, ResourceMixin):
    __tablename__ = 'department_members'
    id = db.Column(db.Integer, nullable=True) # used in import zip job
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
                                                  onupdate='CASCADE',
                                                  ondelete='CASCADE'),
                        index=True, primary_key=True)
    department_id = db.Column(db.Integer,
                              db.ForeignKey('department.id',
                                            onupdate='CASCADE',
                                            ondelete='CASCADE'),
                              index=True, primary_key=True)

    def __repr__(self):
        user = User.query.get(self.user_id)
        return f'{user.username} ({user.email})'


class Department(db.Model, ResourceMixin):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(65), unique=True, nullable=False)
    description = db.Column(StripStr(350), nullable=True)
    #approvers = db.relationship('User', secondary='department_approvers', backref=db.backref('approvals', lazy='dynamic'), uselist=True)
    members = db.relationship('User', secondary='department_members', backref='department', lazy='dynamic', uselist=True)
    head_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    head = db.relationship('User', foreign_keys=[head_id])

    def __repr__(self):
        return self.name

    def get_member_events(self):
        events = db.session.query(Event).join(User) \
                .filter(DepartmentMembers.user_id==User.id,
                        DepartmentMembers.department_id==self.id,
                        Event.status!='Declined',
                        Event.status!='Revoked')
        return events.all()

    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Department.name.ilike(search_query),)

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        delete_count = 0

        for id in ids:
            dept = Department.query.get(id)
            if dept is None:
                continue
            dept.delete()
            delete_count += 1
        return delete_count
