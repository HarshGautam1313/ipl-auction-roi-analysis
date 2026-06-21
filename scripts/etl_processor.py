import os
import json
import pandas as pd

# Initialize data containers
matches_data = []
deliveries_data = []
reviews_data = []
replacements_data = []

# Global unique player catalog
global_players_registry = {}

DATA_DIR = "E:/ipl-auction-roi-analysis/data/raw"

print("Starting ETL Pipeline (Patching IDs, dynamic DRS, and Over/Ball split logic)...")

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".json"):
        match_id = filename.replace(".json", "")
        file_path = os.path.join(DATA_DIR, filename)

        with open(file_path, "r") as file:
            data = json.load(file)

        info = data.get("info", {})

        # --- 1. POPULATE PLAYER REGISTRY & LOOKUP ---
        match_registry = info.get("registry", {}).get("people", {})
        for name_string, unique_id in match_registry.items():
            global_players_registry[unique_id] = name_string

        # Core team identification
        teams = info.get("teams", [None, None])
        team_1 = teams[0]
        team_2 = teams[1]

        # --- 2. EXTRACT INNINGS, DELIVERIES, REVIEWS & REPLACEMENTS ---
        for innings_idx, innings_entry in enumerate(data.get("innings", []), start=1):
            batting_team = innings_entry.get("team")
            # Determine active bowling team for this inning
            bowling_team = team_2 if team_1 == batting_team else team_1

            for over_entry in innings_entry.get("overs", []):
                over_num = over_entry.get("over")

                for delivery_seq, delivery in enumerate(
                    over_entry.get("deliveries", []), start=1
                ):

                    # --- NEW OVER/BALL SPLIT LOGIC ---
                    # Force the delivery notation to a string (e.g., "14.10")
                    raw_ball_string = str(
                        delivery.get("actual_delivery", f"{over_num}.{delivery_seq}")
                    )

                    # Split on the decimal point
                    over_str, ball_str = raw_ball_string.split(".")

                    # Convert to clean integers
                    over_number = int(over_str)
                    ball_number = int(ball_str)

                    # Build bulletproof delivery ID
                    delivery_id = (
                        f"{match_id}_{innings_idx}_{over_number}_{delivery_seq}"
                    )
                    # ---------------------------------

                    batter_name = delivery.get("batter")
                    bowler_name = delivery.get("bowler")
                    non_striker_name = delivery.get("non_striker")

                    # Lookups use match_registry to get the IDs
                    batter_id = match_registry.get(batter_name)
                    bowler_id = match_registry.get(bowler_name)
                    non_striker_id = match_registry.get(non_striker_name)

                    # --- REPLACEMENTS BLOCK ---
                    if (
                        "replacements" in delivery
                        and "match" in delivery["replacements"]
                    ):
                        for rep_idx, rep in enumerate(
                            delivery["replacements"]["match"]
                        ):
                            player_in_name = rep.get("in")
                            player_out_name = rep.get("out")

                            # Fixed ID lookups
                            player_in_id = match_registry.get(player_in_name)
                            player_out_id = match_registry.get(player_out_name)

                            replacement_id = f"rep_{delivery_id}_{rep_idx}"

                            replacement_row = {
                                "replacement_id": replacement_id,
                                "match_id": match_id,
                                "delivery_id": delivery_id,
                                "player_in_id": player_in_id,
                                "player_out_id": player_out_id,
                                "replacement_by_team": rep.get("team"),
                                "replacement_reason": rep.get("reason"),
                            }
                            replacements_data.append(replacement_row)

                    runs = delivery.get("runs", {})
                    runs_batter = runs.get("batter", 0)
                    runs_extras = runs.get("extras", 0)
                    runs_total = runs.get("total", 0)

                    extra_type = None
                    if "extras" in delivery:
                        extra_type = " and ".join(delivery["extras"].keys())

                    is_wicket = "wickets" in delivery
                    player_out_id = None
                    wicket_kind = None
                    fielder_involved = None

                    if is_wicket:
                        wicket_info = delivery["wickets"][0]
                        p_out_name = wicket_info.get("player_out")
                        player_out_id = match_registry.get(p_out_name)
                        wicket_kind = wicket_info.get("kind")

                        fielders = wicket_info.get("fielders", [])
                        if fielders:
                            first_fielder = fielders[0]
                            fielder_involved = (
                                first_fielder.get("name")
                                if isinstance(first_fielder, dict)
                                else first_fielder
                            )

                    # --- DRS REVIEW BLOCK ---
                    review_id = None
                    if "review" in delivery:
                        review_info = delivery["review"]

                        # Match the review ID directly to our new bulletproof delivery ID
                        review_id = f"rev_{delivery_id}"

                        # Handle old vs new team keys
                        review_team = review_info.get("by") or review_info.get("team")

                        # Calculate who initiated the review
                        if review_team == batting_team:
                            review_called_by = "batting"
                        elif review_team == bowling_team:
                            review_called_by = "fielding"
                        else:
                            review_called_by = None

                        # Fallback for older JSONs missing 'batter'
                        rev_batter_name = review_info.get("batter", batter_name)
                        batter_involved_id = match_registry.get(rev_batter_name)

                        # Standardize outcome vs decision strings
                        review_decision = review_info.get(
                            "decision"
                        ) or review_info.get("outcome")

                        review_type = review_info.get("type", "wicket")

                        review_row = {
                            "review_id": review_id,
                            "review_by_team": review_team,
                            "review_called_by": review_called_by,
                            "challenged_umpire": review_info.get("umpire"),
                            "batter_involved_id": batter_involved_id,
                            "review_type": review_type,
                            "review_decision": review_decision,
                        }
                        reviews_data.append(review_row)

                    # Compile delivery row (UPDATED KEYS)
                    delivery_row = {
                        "delivery_id": delivery_id,
                        "match_id": match_id,
                        "review_id": review_id,
                        "innings": innings_idx,
                        "over_number": over_number,
                        "ball_number": ball_number,
                        "actual_delivery": raw_ball_string,
                        "batter_id": batter_id,
                        "bowler_id": bowler_id,
                        "non_striker_id": non_striker_id,
                        "runs_batter": runs_batter,
                        "runs_extras": runs_extras,
                        "runs_total": runs_total,
                        "extra_type": extra_type,
                        "is_wicket": is_wicket,
                        "player_out_id": player_out_id,
                        "wicket_kind": wicket_kind,
                        "fielder_involved": fielder_involved,
                    }
                    deliveries_data.append(delivery_row)

        # --- 3. EXTRACT MATCH DIMENSION ---
        outcome = info.get("outcome", {})
        by_wincrit = outcome.get("by", {})
        win_by_type = list(by_wincrit.keys())[0] if by_wincrit else None
        win_by_amount = by_wincrit.get(win_by_type) if win_by_type else None

        event = info.get("event", {})
        stage = event.get("stage") if isinstance(event, dict) else None

        match_row = {
            "match_id": match_id,
            "season": info.get("season"),
            "stage": stage,
            "match_date": info.get("dates", [None])[0],
            "venue": info.get("venue"),
            "city": info.get("city"),
            "team_1": team_1,
            "team_2": team_2,
            "toss_winner": info.get("toss", {}).get("winner"),
            "toss_decision": info.get("toss", {}).get("decision"),
            "winner": outcome.get("winner"),
            "win_by_amount": win_by_amount,
            "win_by_type": win_by_type,
            "player_of_match": info.get("player_of_match", [None])[0],
        }
        matches_data.append(match_row)

print("Extraction complete. Exporting structured dataset layers...")

# Dataframe compilations
players_list = [
    {"player_id": k, "player_name": v} for k, v in global_players_registry.items()
]
df_players = pd.DataFrame(players_list)
df_matches = pd.DataFrame(matches_data)
df_deliveries = pd.DataFrame(deliveries_data)
df_reviews = pd.DataFrame(reviews_data)
df_replacements = pd.DataFrame(replacements_data)

assert (
    not df_deliveries["delivery_id"].duplicated().any()
), "Duplicate delivery IDs found!"

# fixing the problem with win_by_amount
df_matches["win_by_amount"] = df_matches["win_by_amount"].astype("Int64")

# Save dataset layers to disk
df_matches.to_csv(
    "E:/ipl-auction-roi-analysis/data/processed/dim_matches.csv", index=False
)
df_deliveries.to_csv(
    "E:/ipl-auction-roi-analysis/data/processed/fact_deliveries.csv", index=False
)
df_reviews.to_csv(
    "E:/ipl-auction-roi-analysis/data/processed/dim_reviews.csv", index=False
)
df_players.to_csv(
    "E:/ipl-auction-roi-analysis/data/processed/dim_players.csv", index=False
)
df_replacements.to_csv(
    "E:/ipl-auction-roi-analysis/data/processed/dim_replacements.csv", index=False
)

print("ETL successfully patched. All foreign keys and float notation bugs fixed.")
