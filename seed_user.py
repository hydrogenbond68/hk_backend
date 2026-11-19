"""seed_user.py - Create a test user, respecting first_name/last_name NOT NULL."""
import sys
import traceback
from werkzeug.security import generate_password_hash

EMAIL    = "harykimsintertech@gmail.com"
PASSWORD = "ChangeMe123!"
NAME     = "Hary Kims"
RESET_PASSWORD = False


def find_db(app):
    ext = app.extensions.get("sqlalchemy")
    if ext is not None and hasattr(ext, "create_all"):
        return ext
    for path in ("app.extensions", "app.database", "app.db"):
        try:
            m = __import__(path, fromlist=["db"])
            c = getattr(m, "db", None)
            if c and hasattr(c, "create_all"):
                return c
        except ImportError:
            continue
    return None


def find_user_class():
    for path in ("app.models", "app.models.user", "app.models.users", "models"):
        try:
            m = __import__(path, fromlist=["User"])
            u = getattr(m, "User", None)
            if u is not None:
                return u
        except ImportError:
            continue
    return None


def main():
    from app import create_app
    app = create_app()
    db = find_db(app)
    User = find_user_class()
    if db is None:
        print("FAIL: db not found"); sys.exit(2)
    if User is None:
        print("FAIL: User model not found"); sys.exit(3)

    cols = {c.name: c for c in User.__table__.columns}
    print("User columns:", sorted(cols.keys()))

    with app.app_context():
        pw_col = next((c for c in ("password_hash", "password", "hashed_password", "pw_hash") if c in cols), None)
        if pw_col is None:
            print("FAIL: no password column found"); sys.exit(4)

        existing = db.session.query(User).filter_by(email=EMAIL).first()
        if existing:
            print(f"User ALREADY EXISTS (id={existing.id})")
            if RESET_PASSWORD:
                setattr(existing, pw_col, generate_password_hash(PASSWORD))
                db.session.commit()
                print(f"OK: reset password for {EMAIL}")
            else:
                print("Set RESET_PASSWORD = True in this script to overwrite it.")
            return

        kw = {"email": EMAIL}
        first, _, last = NAME.partition(" ")
        if "first_name" in cols:
            kw["first_name"] = first or "Hary"
        if "last_name" in cols:
            kw["last_name"] = last or "Kims"
        for c in ("full_name", "name", "username", "display_name"):
            if c in cols:
                kw[c] = NAME
                break
        if "company_name" in cols:
            kw["company_name"] = "Hary Kims Ltd"
        for c in ("phone", "address", "profile_image"):
            if c in cols:
                kw[c] = ""
        if "is_admin" in cols:
            kw["is_admin"] = False
        if "is_verified" in cols:
            kw["is_verified"] = True
        if "role" in cols:
            kw["role"] = "buyer"
        kw[pw_col] = generate_password_hash(PASSWORD)

        print("Creating user with kwargs:", {k: "<hash>" if k == pw_col else v for k, v in kw.items()})
        user = User(**kw)
        db.session.add(user)
        db.session.commit()
        print(f"OK: created {EMAIL} (id={user.id})")
        print(f"    password: {PASSWORD}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
