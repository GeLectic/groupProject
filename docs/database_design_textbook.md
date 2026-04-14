# Database Design (Textbook Format)

This document provides a standard textbook-style database design pack for the AI Evidence-Based Tour Planner backend.

## 1. Requirement Analysis (RA)

### 1.1 Problem Statement
The system must support secure user accounts and persistent itinerary history. Each generated itinerary must be tied to its owner, retrievable in future sessions, and stored in both raw JSON form and normalized relational form for queryability.

### 1.2 Functional Requirements
- FR1: A user can register with unique email and password.
- FR2: A user can log in and receive an authentication token.
- FR3: The system can store generated itineraries for an authenticated user.
- FR4: Itinerary generation must persist a normalized day-wise breakdown.
- FR5: Itinerary generation must persist normalized hotel options by tier.
- FR6: Itinerary generation must persist normalized hidden gems, warnings, and must-eat entries.
- FR7: Itinerary generation must persist normalized text notes (cultural tips, packing notes, notices).
- FR8: Itinerary generation must persist normalized budget breakdown key-value items.
- FR9: A user can list itinerary history.
- FR10: A user can fetch one itinerary by id.
- FR11: A user can delete one itinerary by id.
- FR12: A user can clear all itinerary history.
- FR13: A user can delete account using password confirmation.
- FR14: On account deletion, all related itinerary rows in child tables must be removed.
- FR15: Itinerary storage must preserve the original structured JSON payload for compatibility.

### 1.3 Non-Functional Requirements
- NFR1: Data integrity via primary key, foreign key, and uniqueness constraints.
- NFR2: Security through hashed passwords and token-based authorization.
- NFR3: Query performance through indexes on key lookup fields.
- NFR4: Extensibility for adding new itinerary metadata attributes and new itinerary child tables.

## 2. Data Requirements

### 2.1 Core Entities
- User: stores login identity and account creation timestamp.
- StoredItinerary: stores generated trip metadata and full itinerary JSON payload.
- ItineraryDayPlan: stores per-day schedule blocks and day-level notes.
- ItineraryHotelOption: stores normalized hotel options by budget tier.
- ItineraryHiddenGem: stores hidden places and visit guidance.
- ItineraryWarning: stores safety or planning warnings.
- ItineraryMustEatItem: stores food recommendations.
- ItineraryTextNote: stores note lists such as cultural tips, packing, and notices.
- ItineraryBudgetItem: stores budget breakdown key-value entries.

### 2.2 Attribute Requirements
- User.email must be unique and non-null.
- StoredItinerary.user_id must reference User.id.
- StoredItinerary.itinerary_data must be non-null JSON.
- Every itinerary child table must include itinerary_id as non-null FK to itineraries.id.
- Day plan JSON blocks (morning/afternoon/evening/night) must be non-null JSON fields.
- Timestamps should be stored with timezone support.

### 2.3 Relationship Requirements
- One User can own zero to many StoredItinerary records.
- One StoredItinerary belongs to exactly one User.
- One StoredItinerary can own zero to many day plans.
- One StoredItinerary can own zero to many hotel options.
- One StoredItinerary can own zero to many hidden gems.
- One StoredItinerary can own zero to many warnings.
- One StoredItinerary can own zero to many must-eat items.
- One StoredItinerary can own zero to many text notes.
- One StoredItinerary can own zero to many budget items.
- Deleting a User cascades to delete owned itineraries.
- Deleting an itinerary cascades to delete all child rows.

## 3. ER Diagram

Notation follows textbook convention: PK = Primary Key, FK = Foreign Key, UK = Unique Key.

```mermaid
erDiagram
    USERS ||--o{ ITINERARIES : owns
  ITINERARIES ||--o{ ITINERARY_DAYS : has
  ITINERARIES ||--o{ ITINERARY_HOTELS : has
  ITINERARIES ||--o{ ITINERARY_HIDDEN_GEMS : has
  ITINERARIES ||--o{ ITINERARY_WARNINGS : has
  ITINERARIES ||--o{ ITINERARY_MUST_EAT_ITEMS : has
  ITINERARIES ||--o{ ITINERARY_TEXT_NOTES : has
  ITINERARIES ||--o{ ITINERARY_BUDGET_ITEMS : has

    USERS {
        INT id PK
        VARCHAR_320 email UK
        VARCHAR_255 password_hash
        TIMESTAMPTZ created_at
    }

    ITINERARIES {
        INT id PK
        INT user_id FK
        VARCHAR_200 destination
        INT days
        VARCHAR_50 month
        VARCHAR_40 budget_level
        VARCHAR_40 travel_style
        JSON itinerary_data
        TIMESTAMPTZ generated_at
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

      ITINERARY_DAYS {
        INT id PK
        INT itinerary_id FK
        INT day_number
        VARCHAR_200 theme
        JSON morning
        JSON afternoon
        JSON evening
        JSON night
        TEXT day_notes
        JSON travel_times
        JSON opening_hours_warnings
      }

      ITINERARY_HOTELS {
        INT id PK
        INT itinerary_id FK
        VARCHAR_20 tier
        VARCHAR_200 name
        VARCHAR_200 area
        VARCHAR_80 est_cost_per_night_inr
        TEXT pros
        TEXT cons
        VARCHAR_120 best_for
      }

      ITINERARY_HIDDEN_GEMS {
        INT id PK
        INT itinerary_id FK
        VARCHAR_200 name
        TEXT why_special
        TEXT how_to_get_there
      }

      ITINERARY_WARNINGS {
        INT id PK
        INT itinerary_id FK
        VARCHAR_200 issue
        TEXT advice
      }

      ITINERARY_MUST_EAT_ITEMS {
        INT id PK
        INT itinerary_id FK
        VARCHAR_200 dish
        TEXT where_to_find
        VARCHAR_120 approx_cost
      }

      ITINERARY_TEXT_NOTES {
        INT id PK
        INT itinerary_id FK
        VARCHAR_40 note_type
        TEXT note_text
        INT order_index
      }

      ITINERARY_BUDGET_ITEMS {
        INT id PK
        INT itinerary_id FK
        VARCHAR_120 item_key
        VARCHAR_255 item_value
      }
```

## 4. RM (Relational Model)

### 4.1 Relation Schemas
- USERS(id, email, password_hash, created_at)
- ITINERARIES(id, user_id, destination, days, month, budget_level, travel_style, itinerary_data, generated_at, created_at, updated_at)
- ITINERARY_DAYS(id, itinerary_id, day_number, theme, morning, afternoon, evening, night, day_notes, travel_times, opening_hours_warnings)
- ITINERARY_HOTELS(id, itinerary_id, tier, name, area, est_cost_per_night_inr, pros, cons, best_for)
- ITINERARY_HIDDEN_GEMS(id, itinerary_id, name, why_special, how_to_get_there)
- ITINERARY_WARNINGS(id, itinerary_id, issue, advice)
- ITINERARY_MUST_EAT_ITEMS(id, itinerary_id, dish, where_to_find, approx_cost)
- ITINERARY_TEXT_NOTES(id, itinerary_id, note_type, note_text, order_index)
- ITINERARY_BUDGET_ITEMS(id, itinerary_id, item_key, item_value)

### 4.2 Keys and Constraints
- USERS: PK(id), UK(email)
- ITINERARIES: PK(id), FK(user_id) references USERS(id) ON DELETE CASCADE
- ITINERARY_DAYS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_HOTELS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_HIDDEN_GEMS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_WARNINGS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_MUST_EAT_ITEMS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_TEXT_NOTES: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE
- ITINERARY_BUDGET_ITEMS: PK(id), FK(itinerary_id) references ITINERARIES(id) ON DELETE CASCADE

### 4.3 RM Diagram

```mermaid
classDiagram
    class USERS {
        +id : INTEGER <<PK>>
        +email : VARCHAR(320) <<UK, NN>>
        +password_hash : VARCHAR(255) <<NN>>
        +created_at : TIMESTAMPTZ <<NN>>
    }

    class ITINERARIES {
        +id : INTEGER <<PK>>
        +user_id : INTEGER <<FK, NN>>
        +destination : VARCHAR(200) <<NN>>
        +days : INTEGER <<NN>>
        +month : VARCHAR(50) <<NN>>
        +budget_level : VARCHAR(40) <<NN>>
        +travel_style : VARCHAR(40) <<NN>>
        +itinerary_data : JSON <<NN>>
        +generated_at : TIMESTAMPTZ <<NN>>
        +created_at : TIMESTAMPTZ <<NN>>
        +updated_at : TIMESTAMPTZ <<NN>>
    }

      class ITINERARY_DAYS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +day_number : INTEGER <<NN>>
        +theme : VARCHAR(200) <<NN>>
        +morning : JSON <<NN>>
        +afternoon : JSON <<NN>>
        +evening : JSON <<NN>>
        +night : JSON <<NN>>
      }

      class ITINERARY_HOTELS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +tier : VARCHAR(20) <<NN>>
        +name : VARCHAR(200) <<NN>>
      }

      class ITINERARY_HIDDEN_GEMS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +name : VARCHAR(200) <<NN>>
      }

      class ITINERARY_WARNINGS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +issue : VARCHAR(200) <<NN>>
      }

      class ITINERARY_MUST_EAT_ITEMS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +dish : VARCHAR(200) <<NN>>
      }

      class ITINERARY_TEXT_NOTES {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +note_type : VARCHAR(40) <<NN>>
        +order_index : INTEGER <<NN>>
      }

      class ITINERARY_BUDGET_ITEMS {
        +id : INTEGER <<PK>>
        +itinerary_id : INTEGER <<FK, NN>>
        +item_key : VARCHAR(120) <<NN>>
        +item_value : VARCHAR(255) <<NN>>
      }

    USERS "1" --> "0..*" ITINERARIES : user_id
      ITINERARIES "1" --> "0..*" ITINERARY_DAYS : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_HOTELS : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_HIDDEN_GEMS : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_WARNINGS : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_MUST_EAT_ITEMS : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_TEXT_NOTES : itinerary_id
      ITINERARIES "1" --> "0..*" ITINERARY_BUDGET_ITEMS : itinerary_id
```

## 5. DDL Design

### 5.1 DDL Dependency Diagram

```mermaid
flowchart TB
    A[CREATE TABLE users]
    B[CREATE TABLE itineraries]
  C[CREATE TABLE itinerary_days]
  D[CREATE TABLE itinerary_hotels]
  E[CREATE TABLE itinerary_hidden_gems]
  F[CREATE TABLE itinerary_warnings]
  G[CREATE TABLE itinerary_must_eat_items]
  H[CREATE TABLE itinerary_text_notes]
  I[CREATE TABLE itinerary_budget_items]
  J[CREATE INDEX and UNIQUE constraints]

    A --> B
  B --> C
  B --> D
  B --> E
  B --> F
  B --> G
  B --> H
  B --> I
  A --> J
  B --> J
  C --> J
  D --> J
  E --> J
  F --> J
  G --> J
  H --> J
  I --> J
```

### 5.2 DDL Script
See [db_schema_ddl.sql](db_schema_ddl.sql).

## 6. DML Design

### 6.1 DML Operation Diagram

```mermaid
flowchart LR
    T_USERS[(users)]
    T_ITIN[(itineraries)]
    T_DAYS[(itinerary_days)]
    T_HOTELS[(itinerary_hotels)]
    T_GEMS[(itinerary_hidden_gems)]
    T_WARN[(itinerary_warnings)]
    T_EAT[(itinerary_must_eat_items)]
    T_NOTES[(itinerary_text_notes)]
    T_BUDGET[(itinerary_budget_items)]

    OP_REG[Register User]
    OP_LOGIN[Login User]
    OP_GEN[Generate Itinerary]
    OP_NORM[Normalize and Persist Breakdown]
    OP_LIST[List History]
    OP_VIEW[View One Itinerary]
    OP_DEL[Delete One Itinerary]
    OP_CLEAR[Clear Itinerary History]
    OP_ACC_DEL[Delete Account]

    OP_REG -->|INSERT users| T_USERS
    OP_LOGIN -->|SELECT users by email| T_USERS

    OP_GEN -->|INSERT itineraries| T_ITIN
    OP_GEN --> OP_NORM
    OP_NORM -->|INSERT day rows| T_DAYS
    OP_NORM -->|INSERT hotel rows| T_HOTELS
    OP_NORM -->|INSERT hidden gems| T_GEMS
    OP_NORM -->|INSERT warnings| T_WARN
    OP_NORM -->|INSERT must-eat rows| T_EAT
    OP_NORM -->|INSERT text notes| T_NOTES
    OP_NORM -->|INSERT budget rows| T_BUDGET

    OP_LIST -->|SELECT itineraries by user_id| T_ITIN

    OP_VIEW -->|SELECT itinerary by id and user_id| T_ITIN
    OP_VIEW -->|SELECT by itinerary_id| T_DAYS
    OP_VIEW -->|SELECT by itinerary_id| T_HOTELS
    OP_VIEW -->|SELECT by itinerary_id| T_GEMS
    OP_VIEW -->|SELECT by itinerary_id| T_WARN
    OP_VIEW -->|SELECT by itinerary_id| T_EAT
    OP_VIEW -->|SELECT by itinerary_id| T_NOTES
    OP_VIEW -->|SELECT by itinerary_id| T_BUDGET

    OP_DEL -->|DELETE itinerary by id and user_id| T_ITIN
    OP_CLEAR -->|DELETE itineraries by user_id| T_ITIN

    OP_ACC_DEL -->|DELETE itineraries by user_id cascade| T_ITIN
    OP_ACC_DEL -->|DELETE user by id| T_USERS
```

### 6.2 DML Script
See [db_sample_dml.sql](db_sample_dml.sql).

## 7. RA (Relational Algebra) for Core Queries

Let U = USERS, I = ITINERARIES, D = ITINERARY_DAYS, H = ITINERARY_HOTELS,
G = ITINERARY_HIDDEN_GEMS, W = ITINERARY_WARNINGS, M = ITINERARY_MUST_EAT_ITEMS,
T = ITINERARY_TEXT_NOTES, B = ITINERARY_BUDGET_ITEMS.

- Q1 (find user by email):
  sigma_{email = e}(U)

- Q2 (user itinerary history):
  tau_{created_at DESC}(sigma_{user_id = uid}(I))

- Q3 (specific itinerary owned by user):
  sigma_{id = iid and user_id = uid}(I)

- Q4 (day-wise breakdown of one itinerary):
  sigma_{itinerary_id = iid}(D)

- Q5 (hotel options of one itinerary):
  sigma_{itinerary_id = iid}(H)

- Q6 (clear all itineraries for user):
  I <- I - sigma_{user_id = uid}(I)
  (dependent tuples in D, H, G, W, M, T, B are removed by FK cascade)

- Q7 (account delete with cascade semantics):
  U <- U - sigma_{id = uid}(U)
  (dependent tuples in I, D, H, G, W, M, T, B are removed by FK cascade)
