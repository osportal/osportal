#from app.user.routes import user

def user_profile_links(user):
    results = [
        ('user.profile', 'Profile', ''),
        ('user.posts', 'Posts', ''),
        ('user.comments', 'Comments', ''),
    ]
    for result in results:
        yield result

def update_user_jinja_globals(app):
    app.jinja_env.globals.update(user_profile_links=user_profile_links)
