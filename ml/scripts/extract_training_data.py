import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.analytics import UserInteraction, UserFeature
from app.models.moderation import Listing

async def extract_data():
    print("🚀 Starting Training Data Extraction...")
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch Interactions (Last 90 Days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        
        # Join Strategy: Interaction -> Listing -> UserFeature
        # Note: In pure SQL this is a JOIN. Here we fetch and merge in Pandas for simplicity/flexibility in MVP.
        
        # A. Get Interactions
        q_events = select(
            UserInteraction.user_id,
            UserInteraction.listing_id,
            UserInteraction.event_type,
            UserInteraction.created_at
        ).where(
            UserInteraction.created_at >= cutoff,
            UserInteraction.user_id.isnot(None),
            UserInteraction.listing_id.isnot(None)
        )
        r_events = await db.execute(q_events)
        rows_events = r_events.all()
        
        if not rows_events:
            print("⚠️ No interaction data found. Generating empty dataset.")
            df = pd.DataFrame(columns=["user_id", "listing_id", "label", "price", "is_premium"])
            df.to_csv("/app/ml/training_data_latest.csv", index=False)
            return

        df_events = pd.DataFrame(rows_events, columns=["user_id", "listing_id", "event_type", "created_at"])
        
        # B. Labeling & Weighting
        # 1 = Click/Fav, 0 = View
        positive_events = ['listing_contact_clicked', 'listing_favorited']
        
        def get_label_weight(row):
            if row['event_type'] == 'listing_contact_clicked':
                return 1, 10.0 # Label 1, High Weight
            elif row['event_type'] == 'listing_favorited':
                return 1, 5.0  # Label 1, Med Weight
            elif row['event_type'] == 'listing_viewed':
                return 0, 1.0  # Label 0, Base Weight
            return 0, 1.0

        df_events[['label', 'weight']] = df_events.apply(
            lambda x: pd.Series(get_label_weight(x)), axis=1
        )
        
        # Deduplicate: Take max label and max weight
        df_dataset = df_events.groupby(['user_id', 'listing_id']).agg({
            'label': 'max',
            'weight': 'max'
        }).reset_index()
        
        # C. Get Listing Features
        listing_ids = df_dataset['listing_id'].unique().tolist()
        if listing_ids:
            q_listings = select(Listing.id, Listing.price, Listing.is_premium).where(Listing.id.in_(listing_ids))
            r_listings = await db.execute(q_listings)
            df_listings = pd.DataFrame(r_listings.all(), columns=["listing_id", "price", "is_premium"])
            
            # Merge
            df_dataset = pd.merge(df_dataset, df_listings, on='listing_id', how='left')
            
        # D. Get User Features (Snapshot)
        # In a real ML pipeline, we need 'Point-in-Time' features. For MVP, we use current snapshot.
        user_ids = df_dataset['user_id'].unique().tolist()
        if user_ids:
            q_users = select(UserFeature.user_id, UserFeature.activity_score).where(UserFeature.user_id.in_(user_ids))
            r_users = await db.execute(q_users)
            df_users = pd.DataFrame(r_users.all(), columns=["user_id", "activity_score"])
            
            # Merge
            df_dataset = pd.merge(df_dataset, df_users, on='user_id', how='left')

        # Fill NaNs
        df_dataset = df_dataset.fillna(0)
        
        print(f"✅ Extracted {len(df_dataset)} rows.")
        output_path = "/app/ml/training_data_latest.csv"
        df_dataset.to_csv(output_path, index=False)
        print(f"💾 Saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(extract_data())
