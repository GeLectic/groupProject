-- Textbook-style DML examples mapped to application behavior

-- 1) Register
INSERT INTO users (email, password_hash)
VALUES ('student@example.com', '$2b$12$hashed_password_here');

-- 2) Login lookup
SELECT id, email, password_hash, created_at
FROM users
WHERE email = 'student@example.com';

-- 3) Store generated itinerary header (raw JSON retained)
WITH new_itinerary AS (
  INSERT INTO itineraries (
    user_id,
    destination,
    days,
    month,
    budget_level,
    travel_style,
    itinerary_data,
    generated_at
  )
  VALUES (
    1,
    'Manali, Himachal Pradesh',
    7,
    'October',
    'mid-range',
    'adventure',
    '{"itinerary": [{"day": 1}], "hotels": {"budget": []}}',
    NOW()
  )
  RETURNING id
)
INSERT INTO itinerary_days (
  itinerary_id,
  day_number,
  theme,
  morning,
  afternoon,
  evening,
  night,
  day_notes,
  travel_times,
  opening_hours_warnings
)
SELECT
  id,
  1,
  'Arrival and local exploration',
  '{"activity": "Cafe breakfast"}',
  '{"activity": "Museum visit"}',
  '{"activity": "Mall road walk"}',
  '{"activity": "Rest"}',
  'Keep buffer for local traffic.',
  '["Hotel -> Museum: 20 min"]',
  '["Museum closes by 6 PM"]'
FROM new_itinerary;

-- 4) Store normalized hotels, hidden gems, warnings, must-eat, notes, and budget
INSERT INTO itinerary_hotels (
  itinerary_id,
  tier,
  name,
  area,
  est_cost_per_night_inr,
  pros,
  cons,
  best_for
)
VALUES
  (1, 'budget', 'Pine Stay', 'Old Manali', '2500', 'Near cafes', 'Limited parking', 'Backpackers'),
  (1, 'mid_range', 'Valley View', 'Mall Road', '4500', 'Central location', 'Crowded area', 'Families');

INSERT INTO itinerary_hidden_gems (itinerary_id, name, why_special, how_to_get_there)
VALUES
  (1, 'Jogini Waterfall Trail', 'Scenic and less crowded', 'Taxi to Vashisht then short hike');

INSERT INTO itinerary_warnings (itinerary_id, issue, advice)
VALUES
  (1, 'Altitude sickness risk', 'Stay hydrated and avoid overexertion on day 1');

INSERT INTO itinerary_must_eat_items (itinerary_id, dish, where_to_find, approx_cost)
VALUES
  (1, 'Siddu', 'Local Himachali cafes', 'INR 120-180');

INSERT INTO itinerary_text_notes (itinerary_id, note_type, note_text, order_index)
VALUES
  (1, 'cultural_tip', 'Respect temple dress norms.', 1),
  (1, 'packing', 'Carry a warm layer for evenings.', 1),
  (1, 'notice', 'Weather can change rapidly.', 1);

INSERT INTO itinerary_budget_items (itinerary_id, item_key, item_value)
VALUES
  (1, 'stay', '31500'),
  (1, 'food', '14000'),
  (1, 'transport', '9000');

-- 5) List history for user
SELECT id, destination, days, month, budget_level, travel_style, created_at
FROM itineraries
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 100;

-- 6) Fetch one itinerary header
SELECT *
FROM itineraries
WHERE id = 10
  AND user_id = 1;

-- 7) Fetch normalized breakdown for one itinerary
SELECT * FROM itinerary_days WHERE itinerary_id = 10 ORDER BY day_number;
SELECT * FROM itinerary_hotels WHERE itinerary_id = 10;
SELECT * FROM itinerary_hidden_gems WHERE itinerary_id = 10;
SELECT * FROM itinerary_warnings WHERE itinerary_id = 10;
SELECT * FROM itinerary_must_eat_items WHERE itinerary_id = 10;
SELECT * FROM itinerary_text_notes WHERE itinerary_id = 10 ORDER BY note_type, order_index;
SELECT * FROM itinerary_budget_items WHERE itinerary_id = 10;

-- 8) Delete one itinerary
DELETE FROM itineraries
WHERE id = 10
  AND user_id = 1;
-- Related child rows are removed by ON DELETE CASCADE.

-- 9) Clear all itineraries for user
DELETE FROM itineraries
WHERE user_id = 1;
-- Related child rows are removed by ON DELETE CASCADE.

-- 10) Delete account
DELETE FROM users
WHERE id = 1;
-- Related itinerary and itinerary child rows are removed via ON DELETE CASCADE.
