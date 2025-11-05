CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash BYTEA NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS films (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    duration INT NOT NULL,
    rating FLOAT NOT NULL CHECK (rating >= 0 AND rating <= 10),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS halls (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INT NOT NULL CHECK(capacity > 0)
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    film_id INT NOT NULL REFERENCES films(id) ON DELETE CASCADE,
    hall_id INT NOT NULL REFERENCES halls(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK(price >= 0),
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    seat_number INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_seat'
    ) THEN
        ALTER TABLE bookings
        ADD CONSTRAINT unique_seat UNIQUE(session_id, seat_number);
    END IF;
END
$$;


CREATE OR REPLACE FUNCTION add_session(
    _film_id INT,
    _hall_id INT,
    _start_time TIMESTAMPTZ,
    _price NUMERIC(10, 2)
)
RETURNS SETOF sessions
AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM sessions s
        JOIN films f2 ON f2.id = s.film_id
        JOIN films f1 ON f1.id = _film_id
        WHERE s.hall_id = _hall_id
          AND _start_time < s.start_time + (f2.duration || ' minutes')::interval
          AND _start_time + (f1.duration || ' minutes')::interval > s.start_time
    ) THEN
        RAISE EXCEPTION 'Time conflict in hall %', _hall_id;
    END IF;
    RETURN QUERY
    INSERT INTO sessions (
        film_id, hall_id, start_time, price, total_seats, available_seats
    )
    SELECT
        _film_id,
        _hall_id,
        _start_time,
        _price,
        h.capacity,
        h.capacity
    FROM halls h
    WHERE h.id = _hall_id
    RETURNING *;
END;
$$ LANGUAGE plpgsql;





