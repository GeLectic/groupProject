-- Textbook-style DDL for the current backend schema

CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE itineraries (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    destination VARCHAR(200) NOT NULL,
    days INTEGER NOT NULL,
    month VARCHAR(50) NOT NULL,
    budget_level VARCHAR(40) NOT NULL,
    travel_style VARCHAR(40) NOT NULL,
    itinerary_data JSON NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_itineraries_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_days (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,
    theme VARCHAR(200) NOT NULL,
    morning JSON NOT NULL,
    afternoon JSON NOT NULL,
    evening JSON NOT NULL,
    night JSON NOT NULL,
    day_notes TEXT NOT NULL,
    travel_times JSON NOT NULL,
    opening_hours_warnings JSON NOT NULL,
    CONSTRAINT fk_itinerary_days_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_hotels (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    tier VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    area VARCHAR(200) NOT NULL,
    est_cost_per_night_inr VARCHAR(80) NOT NULL,
    pros TEXT NOT NULL,
    cons TEXT NOT NULL,
    best_for VARCHAR(120) NOT NULL,
    CONSTRAINT fk_itinerary_hotels_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_hidden_gems (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    why_special TEXT NOT NULL,
    how_to_get_there TEXT NOT NULL,
    CONSTRAINT fk_itinerary_hidden_gems_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_warnings (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    issue VARCHAR(200) NOT NULL,
    advice TEXT NOT NULL,
    CONSTRAINT fk_itinerary_warnings_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_must_eat_items (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    dish VARCHAR(200) NOT NULL,
    where_to_find TEXT NOT NULL,
    approx_cost VARCHAR(120) NOT NULL,
    CONSTRAINT fk_itinerary_must_eat_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_text_notes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    note_type VARCHAR(40) NOT NULL,
    note_text TEXT NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_itinerary_text_notes_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE TABLE itinerary_budget_items (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    itinerary_id INTEGER NOT NULL,
    item_key VARCHAR(120) NOT NULL,
    item_value VARCHAR(255) NOT NULL,
    CONSTRAINT fk_itinerary_budget_items_itinerary
        FOREIGN KEY (itinerary_id)
        REFERENCES itineraries (id)
        ON DELETE CASCADE
);

CREATE INDEX idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX idx_itineraries_created_at ON itineraries(created_at DESC);
CREATE INDEX idx_itinerary_days_itinerary_id ON itinerary_days(itinerary_id);
CREATE INDEX idx_itinerary_hotels_itinerary_id ON itinerary_hotels(itinerary_id);
CREATE INDEX idx_itinerary_hidden_gems_itinerary_id ON itinerary_hidden_gems(itinerary_id);
CREATE INDEX idx_itinerary_warnings_itinerary_id ON itinerary_warnings(itinerary_id);
CREATE INDEX idx_itinerary_must_eat_items_itinerary_id ON itinerary_must_eat_items(itinerary_id);
CREATE INDEX idx_itinerary_text_notes_itinerary_id ON itinerary_text_notes(itinerary_id);
CREATE INDEX idx_itinerary_budget_items_itinerary_id ON itinerary_budget_items(itinerary_id);
