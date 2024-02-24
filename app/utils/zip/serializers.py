import json
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from decimal import Decimal
from app.extensions import db
from sqlalchemy.exc import OperationalError

string_types = (str,)

def is_database_mariadb():
    try:
        result = db.session.execute("SELECT version()").fetchone()[0]
        mariadb = "mariadb" in result.lower()
    except OperationalError:
        mariadb = False
    return mariadb


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)


class JSONSerializer(object):
    def __init__(self, query, fileobj):
        self.query = query
        self.fileobj = fileobj
        self.buckets = defaultdict(list)

    def serialize(self):
        for row in self.query:
            self.write(None, row)
        self.close()

    def write(self, path, result):
        self.buckets[path].append(result)

    def wrap(self, result):
        result = OrderedDict(
            [("count", len(result)), ("results", result), ("meta", {})]
        )
        return result

    def close(self):
        mariadb = is_database_mariadb()
        for _path, result in self.buckets.items():
            result = self.wrap(result)

            # Certain databases (MariaDB) store JSON as LONGTEXT.
            # Before emitting a file we should standardize to valid JSON (i.e. a dict)
            # See Issue #973
            for i, r in enumerate(result["results"]):
                # Handle JSON used in FieldEntries table
                if mariadb:
                    if sorted(r.keys()) == [
                        "field_id",
                        "id",
                        "team_id",
                        "type",
                        "user_id",
                        "value",
                    ]:
                        value = r.get("value")
                        if value:
                            try:
                                result["results"][i]["value"] = json.loads(value)
                            except ValueError:
                                pass

            data = json.dumps(result, cls=JSONEncoder, separators=(",", ":"))
            self.fileobj.write(data.encode("utf-8"))
