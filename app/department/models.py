from app.extensions import db
from app.leave.models import Leave
from app.user.models import User
from app.utils.util_sqlalchemy import ResourceMixin, FmtString, StripStr
from sqlalchemy import or_


class DepartmentMembers(ResourceMixin):
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


class Department(ResourceMixin):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(StripStr(65), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    description = db.Column(StripStr(350), nullable=True)
    #approvers = db.relationship('User', secondary='department_approvers', backref=db.backref('approvals', lazy='dynamic'), uselist=True)
    members = db.relationship('User', secondary='department_members', backref='department', lazy='dynamic', uselist=True)
    head_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    head = db.relationship('User', foreign_keys=[head_id])

    def __repr__(self):
        return self.name

    def get_member_leaves(self):
        leaves = db.session.query(Leave).join(User) \
                .filter(DepartmentMembers.user_id==User.id,
                        DepartmentMembers.department_id==self.id,
                        Leave.status!='Declined',
                        Leave.status!='Revoked')
        return leaves.all()

    """
    def get_public_hols(self):
        # Get all members in the department
        department_members = db.session.query(User).join(DepartmentMembers) \
            .filter(DepartmentMembers.department_id == self.id).all()

        # Aggregate holidays for each user
        all_holidays = set()  # Use a set to avoid duplicates
        for user in department_members:
            if user.entt and user.entt.public_holiday_group:
                all_holidays.update(user.entt.public_holiday_group.holidays)

        return all_holidays
    """


    @classmethod
    def search(cls, query):
        search_query = '%{0}%'.format(query)
        search_chain = (Department.name.ilike(search_query),)

        return or_(*search_chain)
