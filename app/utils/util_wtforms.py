from flask_wtf import FlaskForm

class ModelForm(FlaskForm):
    """ For CSRF protection """
    def __init__(self, obj=None, prefix='', **kwargs):
        FlaskForm.__init__(self, obj=obj, prefix=prefix, **kwargs)
        self._obj = obj

def choices_from_dict(source, prepend_blank=True):
    """
    Convert a dict to a format that's compatible with WTForm's choices. It also
    optionally prepends a "Please select one..." value.

    Example:
      # Convert this data structure:
      STATUS = OrderedDict([
          ('unread', 'Unread'),
          ('open', 'Open'),
          ('contacted', 'Contacted'),
          ('closed', 'Closed')
      ])

      # Into this:
      choices = [('', 'Please select one...'), ('unread', 'Unread) ...]

    :param source: Input source
    :type source: dict
    :param prepend_blank: An optional blank item
    :type prepend_blank: bool
    :return: list
    """
    choices = []

    if prepend_blank:
        choices.append(('', 'Please select one...'))

    for key, value in source.items():
        pair = (key, value)
        choices.append(pair)

    return choices
