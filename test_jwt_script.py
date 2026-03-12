from datetime import datetime, timedelta, timezone

from jose import jwt

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"


def test_jwt():
    data = {"sub": "test@example.com"}

    # Create token
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    try:
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print("Created token:", token)
    except Exception as e:
        print("Error creating:", e)
        return

    # Decode token
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Decoded successfully:", decoded)
    except Exception as e:
        print("Error decoding:", type(e), e)


test_jwt()
