-- 1. Create the Player Dimension (Run this first)
CREATE TABLE dim_players (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100)
);

-- 2. Create the Match Dimension (Captains removed)
CREATE TABLE dim_matches (
    match_id VARCHAR(50) PRIMARY KEY,
    season VARCHAR(20),
    stage VARCHAR(50),
    match_date DATE,
    venue VARCHAR(150),
    city VARCHAR(100),
    team_1 VARCHAR(100),
    team_2 VARCHAR(100),
    toss_winner VARCHAR(100),
    toss_decision VARCHAR(20),
    winner VARCHAR(100),
    win_by_amount INT,
    win_by_type VARCHAR(20),
    player_of_match VARCHAR(100)
);

-- 3. Create the DRS Reviews Outrigger Dimension
CREATE TABLE dim_reviews (
    review_id VARCHAR(100) PRIMARY KEY,
    review_by_team VARCHAR(100),
    review_called_by VARCHAR(20),
    challenged_umpire VARCHAR(100),
    batter_involved_id VARCHAR(50) REFERENCES dim_players(player_id),
    review_type VARCHAR(50),
    review_decision VARCHAR(50)
);

-- 4. Create the Core Fact Table
CREATE TABLE fact_deliveries (
    delivery_id VARCHAR(100) PRIMARY KEY,
    match_id VARCHAR(50) REFERENCES dim_matches(match_id),
    review_id VARCHAR(100) REFERENCES dim_reviews(review_id),
    innings INT,
    over_no INT,
    ball_no DECIMAL(4,1),
    actual_delivery VARCHAR(10),
    batter_id VARCHAR(50) REFERENCES dim_players(player_id),
    bowler_id VARCHAR(50) REFERENCES dim_players(player_id),
    non_striker_id VARCHAR(50) REFERENCES dim_players(player_id),
    runs_batter INT,
    runs_extras INT,
    runs_total INT,
    extra_type VARCHAR(100),
    is_wicket BOOLEAN,
    player_out_id VARCHAR(50) REFERENCES dim_players(player_id),
    wicket_kind VARCHAR(50),
    fielder_involved VARCHAR(100)
);

-- 5. Create the Replacements Bridge Table
CREATE TABLE dim_replacements (
    replacement_id VARCHAR(100) PRIMARY KEY,
    match_id VARCHAR(50) REFERENCES dim_matches(match_id),
    delivery_id VARCHAR(100) REFERENCES fact_deliveries(delivery_id),
    player_in_id VARCHAR(50) REFERENCES dim_players(player_id),
    player_out_id VARCHAR(50) REFERENCES dim_players(player_id),
    replacement_by_team VARCHAR(100),
    replacement_reason VARCHAR(50)
);