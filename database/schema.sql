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
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_seat'
    ) THEN
        ALTER TABLE bookings DROP CONSTRAINT unique_seat;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'unique_active_seat'
    ) THEN
        CREATE UNIQUE INDEX unique_active_seat
        ON bookings (session_id, seat_number)
        WHERE status = 'active';
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
    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE session_id = _session_id
          AND seat_number = _seat_number
          AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'Seat % is already booked', _seat_number;
    END IF;
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

CREATE OR REPLACE FUNCTION get_film_sessions(_film_id INT)
RETURNS SETOF sessions AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM sessions
    WHERE film_id = _film_id
    ORDER BY start_time;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION monthly_report(_year INT, _month INT)
RETURNS TABLE(
    film_title TEXT,
    total_sessions INT,
    total_bookings INT,
    total_income NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.title,
        COUNT(DISTINCT s.id) AS total_sessions,
        COUNT(b.id) AS total_bookings,
        COALESCE(SUM(s.price), 0) AS total_income
    FROM films f
    LEFT JOIN sessions s ON f.id = s.film_id
    LEFT JOIN bookings b ON b.session_id = s.id AND b.status = 'active'
    WHERE EXTRACT(YEAR FROM s.start_time) = _year
      AND EXTRACT(MONTH FROM s.start_time) = _month
    GROUP BY f.title;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_seat_availability()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE session_id = NEW.session_id
          AND seat_number = NEW.seat_number
          AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'Seat % already booked for session %', NEW.seat_number, NEW.session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_check_seat_availability'
    ) THEN
        CREATE TRIGGER trg_check_seat_availability
        BEFORE INSERT ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION check_seat_availability();
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION update_session_capacity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET available_seats = available_seats - 1
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_update_session_capacity'
    ) THEN
        CREATE TRIGGER trg_update_session_capacity
        AFTER INSERT ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION update_session_capacity();
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION restore_capacity_on_cancel()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'active' AND NEW.status = 'canceled' THEN
        UPDATE sessions
        SET available_seats = (
            SELECT total_seats - COUNT(*)
            FROM bookings
            WHERE session_id = NEW.session_id AND status = 'active'
        )
        WHERE id = NEW.session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_restore_capacity_on_cancel'
    ) THEN
        CREATE TRIGGER trg_restore_capacity_on_cancel
        AFTER UPDATE ON bookings
        FOR EACH ROW
        EXECUTE FUNCTION restore_capacity_on_cancel();
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION validate_rating()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rating < 0 OR NEW.rating > 10 THEN
        RAISE EXCEPTION 'Rating must be between 0 and 10';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_validate_rating'
    ) THEN
        CREATE TRIGGER trg_validate_rating
        BEFORE UPDATE ON films
        FOR EACH ROW
        EXECUTE FUNCTION validate_rating();
    END IF;
END;
$$;

CREATE OR REPLACE VIEW vw_upcoming_sessions AS
SELECT *
FROM sessions
WHERE start_time > NOW()
ORDER BY start_time;

CREATE OR REPLACE VIEW vw_active_bookings AS
SELECT *
FROM bookings
WHERE status = 'active';

CREATE OR REPLACE VIEW vw_sessions_with_halls AS
SELECT
   s.*,
   h.name AS hall_name,
   h.capacity AS hall_capacity
FROM sessions s
JOIN halls h ON h.id = s.hall_id;

CREATE OR REPLACE VIEW vw_top_films AS
SELECT
    f.id,
    f.title,
    COUNT(b.id) AS total_bookings
FROM films f
LEFT JOIN sessions s ON s.film_id = f.id
LEFT JOIN bookings b ON b.session_id = s.id AND b.status='active'
GROUP BY f.id
ORDER BY total_bookings DESC;

CREATE OR REPLACE VIEW vw_user_history AS
SELECT
    u.id AS user_id,
    u.name,
    u.email,
    b.id AS booking_id,
    f.title AS film_title,
    s.start_time,
    b.seat_number,
    CASE
        WHEN b.status = 'canceled' THEN 'canceled'
        WHEN s.start_time < NOW() THEN 'expired'
        ELSE 'active'
    END AS status
FROM bookings b
JOIN users u ON u.id = b.user_id
JOIN sessions s ON s.id = b.session_id
JOIN films f ON f.id = s.film_id
ORDER BY s.start_time DESC;

CREATE OR REPLACE VIEW vw_hall_usage AS
SELECT
    h.id AS hall_id,
    h.name,
    h.capacity,
    COUNT(s.id) AS total_sessions
FROM halls h
LEFT JOIN sessions s ON s.hall_id = h.id
GROUP BY h.id, h.name, h.capacity;

CREATE OR REPLACE VIEW vw_user_info AS
SELECT
    id,
    name,
    email,
    role,
    created_at
FROM users;

CREATE OR REPLACE VIEW vw_top_rated_films AS
SELECT
    id,
    title,
    genre,
    duration,
    rating,
    description,
    is_active,
    image_url
FROM films
WHERE rating IS NOT NULL
ORDER BY rating DESC;

CREATE OR REPLACE VIEW vw_films_with_upcoming_sessions AS
SELECT DISTINCT
    f.id,
    f.title,
    f.genre,
    f.duration,
    f.rating,
    f.description,
    f.image_url,
    MIN(s.start_time) AS next_session
FROM films f
JOIN sessions s ON s.film_id = f.id
WHERE s.start_time > NOW()
GROUP BY f.id;

CREATE OR REPLACE VIEW vw_popular_last_week AS
SELECT
    f.id,
    f.title,
    f.genre,
    f.duration,
    f.rating,
    f.description,
    f.image_url,
    COUNT(b.id) AS weekly_bookings
FROM films f
LEFT JOIN sessions s ON s.film_id = f.id
LEFT JOIN bookings b
    ON b.session_id = s.id
    AND b.status = 'active'
    AND b.created_at >= NOW() - INTERVAL '7 days'
GROUP BY f.id
ORDER BY weekly_bookings DESC;

CREATE OR REPLACE FUNCTION delete_session(_session_id INT)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM sessions WHERE id = _session_id) THEN
        RAISE EXCEPTION 'Session % not found', _session_id;
    END IF;
    IF EXISTS (
        SELECT 1
        FROM bookings
        WHERE session_id = _session_id AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'Cannot delete session with active bookings';
    END IF;
    DELETE FROM sessions WHERE id = _session_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_film(
    _title TEXT,
    _genre TEXT,
    _duration INT,
    _rating FLOAT,
    _description TEXT,
    _image_url TEXT DEFAULT NULL
)
RETURNS SETOF films AS $$
BEGIN
    IF _rating < 0 OR _rating > 10 THEN
        RAISE EXCEPTION 'Rating must be between 0 and 10';
    END IF;
    IF _duration <= 0 THEN
        RAISE EXCEPTION 'Duration must be positive';
    END IF;
    IF _title IS NULL OR _title = '' THEN
        RAISE EXCEPTION 'Title is required';
    END IF;
    IF _genre IS NULL OR _genre = '' THEN
        RAISE EXCEPTION 'Genre is required';
    END IF;
    RETURN QUERY
    INSERT INTO films (title, genre, duration, rating, description, image_url)
    VALUES (_title, _genre, _duration, _rating, _description, _image_url)
    RETURNING *;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_film(
    _film_id INT,
    _title TEXT,
    _genre TEXT,
    _duration INT,
    _rating FLOAT,
    _description TEXT,
    _is_active BOOLEAN,
    _image_url TEXT DEFAULT NULL
)
RETURNS SETOF films AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM films WHERE id = _film_id) THEN
        RAISE EXCEPTION 'Film not found';
    END IF;
    IF _rating < 0 OR _rating > 10 THEN
        RAISE EXCEPTION 'Rating must be between 0 and 10';
    END IF;
    IF _duration <= 0 THEN
        RAISE EXCEPTION 'Duration must be positive';
    END IF;
    IF _title IS NULL OR _title = '' THEN
        RAISE EXCEPTION 'Title is required';
    END IF;
    IF _genre IS NULL OR _genre = '' THEN
        RAISE EXCEPTION 'Genre is required';
    END IF;
    RETURN QUERY
    UPDATE films
    SET title = _title,
        genre = _genre,
        duration = _duration,
        rating = _rating,
        description = _description,
        is_active = _is_active,
        image_url = _image_url
    WHERE id = _film_id
    RETURNING *;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_hall(_name TEXT, _capacity INT)
RETURNS SETOF halls AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM halls WHERE LOWER(name) = LOWER(_name)) THEN
        RAISE EXCEPTION 'Hall with name "%" already exists', _name;
    END IF;
    IF _capacity <= 0 THEN
        RAISE EXCEPTION 'Capacity must be positive';
    END IF;
    IF _name IS NULL OR _name = '' THEN
        RAISE EXCEPTION 'Hall name is required';
    END IF;
    RETURN QUERY
    INSERT INTO halls (name, capacity)
    VALUES (_name, _capacity)
    RETURNING *;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_hall(_hall_id INT)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM halls WHERE id = _hall_id) THEN
        RAISE EXCEPTION 'Hall not found';
    END IF;
    IF EXISTS (SELECT 1 FROM sessions WHERE hall_id = _hall_id AND start_time > NOW()) THEN
        RAISE EXCEPTION 'Cannot delete hall with future sessions';
    END IF;
    DELETE FROM halls WHERE id = _hall_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_user(_name TEXT, _email TEXT, _password_hash BYTEA)
RETURNS TABLE(
    id INT,
    name TEXT,
    email TEXT,
    role TEXT
) AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM users WHERE users.email = _email) THEN
        RAISE EXCEPTION 'User with email "%" already exists', _email;
    END IF;
    IF _name IS NULL OR _name = '' THEN
        RAISE EXCEPTION 'User name is required';
    END IF;
    IF _email IS NULL OR _email = '' THEN
        RAISE EXCEPTION 'Email is required';
    END IF;
    IF _password_hash IS NULL THEN
        RAISE EXCEPTION 'Password hash is required';
    END IF;
    RETURN QUERY
    INSERT INTO users (name, email, password_hash, role)
    VALUES (_name, _email, _password_hash, 'user')
    RETURNING users.id, users.name, users.email, users.role;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_user_bookings_detailed(_user_id INT)
RETURNS TABLE(
    booking_id INT,
    user_id INT,
    session_id INT,
    seat_number INT,
    status TEXT,
    created_at TIMESTAMP,
    film_title TEXT,
    start_time TIMESTAMPTZ,
    hall_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id, b.user_id, b.session_id, b.seat_number, b.status, b.created_at,
        f.title, s.start_time, h.name
    FROM bookings b
    JOIN sessions s ON s.id = b.session_id
    JOIN films f ON f.id = s.film_id
    JOIN halls h ON h.id = s.hall_id
    WHERE b.user_id = _user_id
    ORDER BY b.created_at DESC;
END;
$$ LANGUAGE plpgsql;