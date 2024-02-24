from app.pages.models import Page

def pages_menu_bar():
    pages = Page.query.filter(Page.active).all()
    for result in pages:
        print(result)
        yield result

def update_pages_jinja_globals(app):
    app.jinja_env.globals.update(pages_menu_bar=pages_menu_bar)
