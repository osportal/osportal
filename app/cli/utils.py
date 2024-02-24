import click
import re

class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """
    _email_regex = r"[^@]+@[^@]+\.[^@]+"
    name = 'email'

    def convert(self, value, param, ctx):
        # Exact match
        if re.match(self._email_regex, value):
            return value
        else:
            self.fail(('invalid email: %s' % value), param, ctx)

    def __repr__(self):
        return 'email'
