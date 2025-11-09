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

CREATE OR REPLACE FUNCTION add_booking(
    _user_id INT,
    _session_id INT,
    _seat_number INT
)
RETURNS SETOF bookings
LANGUAGE plpgsql
AS $$
DECLARE
    _session sessions;
BEGIN
    SELECT *
    INTO _session
    FROM sessions
    WHERE id = _session_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Session % not found', _session_id;
    END IF;
    IF _seat_number <= 0 OR _seat_number > _session.total_seats THEN
        RAISE EXCEPTION 'Invalid seat number %', _seat_number;
    END IF;
    IF _session.available_seats <= 0 THEN
        RAISE EXCEPTION 'No available seats';
    END IF;
    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE session_id = _session_id
          AND seat_number = _seat_number
          AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'Seat % is already booked', _seat_number;
    END IF;
    UPDATE sessions
    SET available_seats = available_seats - 1
    WHERE id = _session_id;
    RETURN QUERY
    INSERT INTO bookings (user_id, session_id, seat_number)
    VALUES (_user_id, _session_id, _seat_number)
    RETURNING *;
END;
$$;


CREATE OR REPLACE FUNCTION cancel_booking(
    _booking_id INT,
    _user_id INT
)
RETURNS SETOF bookings
LANGUAGE plpgsql
AS $$
DECLARE
    _booking bookings;
BEGIN
    SELECT *
    INTO _booking
    FROM bookings
    WHERE id = _booking_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking % not found', _booking_id;
    END IF;
    IF _booking.user_id <> _user_id THEN
        RAISE EXCEPTION 'Forbidden: booking does not belong to user';
    END IF;
    IF _booking.status <> 'active' THEN
        RAISE EXCEPTION 'Booking already canceled';
    END IF;
    UPDATE sessions
    SET available_seats = available_seats + 1
    WHERE id = _booking.session_id;
    UPDATE bookings
    SET status = 'canceled'
    WHERE id = _booking_id;
    RETURN QUERY
    SELECT *
    FROM bookings
    WHERE id = _booking_id;
END;
$$;

DO $$
BEGIN
    BEGIN
        ALTER TABLE bookings
        ADD CONSTRAINT booking_status_check
        CHECK (status IN ('active', 'canceled'));
    EXCEPTION
        WHEN duplicate_object THEN null;
    END;
END;
$$;

CREATE OR REPLACE FUNCTION check_active_bookings_limit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    active_count INT;
BEGIN
    IF NEW.status = 'active' THEN
        SELECT COUNT(*) INTO active_count
        FROM bookings
        WHERE user_id = NEW.user_id
          AND status = 'active';
        IF active_count >= 5 THEN
            RAISE EXCEPTION
                'User % cannot have more than 5 active bookings',
                NEW.user_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_check_active_bookings_limit'
    ) THEN
        CREATE TRIGGER trg_check_active_bookings_limit
        BEFORE INSERT ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION check_active_bookings_limit();
    END IF;
END;
$$;






