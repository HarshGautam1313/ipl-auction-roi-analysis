COPY dim_players FROM 'E:\ipl-auction-roi-analysis\data\processed\dim_players.csv' WITH (FORMAT csv, HEADER true);
COPY dim_matches FROM 'E:\ipl-auction-roi-analysis\data\processed\dim_matches.csv' WITH (FORMAT csv, HEADER true);
COPY dim_reviews FROM 'E:\ipl-auction-roi-analysis\data\processed\dim_reviews.csv' WITH (FORMAT csv, HEADER true);
COPY fact_deliveries FROM 'E:\ipl-auction-roi-analysis\data\processed\fact_deliveries.csv' WITH (FORMAT csv, HEADER true);
COPY dim_replacements FROM 'E:\ipl-auction-roi-analysis\data\processed\dim_replacements.csv' WITH (FORMAT csv, HEADER true);


