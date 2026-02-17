import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import select, text

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal

async def analyze_results():
    print("📊 Analyzing Experiment: revenue_boost_v1")
    
    async with AsyncSessionLocal() as db:
        # Fetch Data: Join Experiment Logs with Interactions
        # We want: Group, User Count, Contact Count
        
        query = text("""
            SELECT 
                el.variant as "group",
                COUNT(DISTINCT el.user_id) as users,
                COUNT(DISTINCT CASE WHEN ui.event_type = 'listing_contact_clicked' THEN el.user_id END) as converters
            FROM experiment_logs el
            LEFT JOIN user_interactions ui ON el.user_id = ui.user_id 
                AND ui.created_at >= el.created_at -- Interaction after exposure
            WHERE el.experiment_name = 'revenue_boost_v1'
            GROUP BY el.variant
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("⚠️ No data found.")
            return

        df = pd.DataFrame(rows, columns=["group", "users", "converters"])
        df['cvr'] = (df['converters'] / df['users']) * 100
        
        print("\n--- RESULTS ---")
        print(df)
        
        # Determine Winner
        a_cvr = df[df['group'] == 'A']['cvr'].values[0] if not df[df['group'] == 'A'].empty else 0
        b_cvr = df[df['group'] == 'B']['cvr'].values[0] if not df[df['group'] == 'B'].empty else 0
        
        uplift = ((b_cvr - a_cvr) / a_cvr) * 100 if a_cvr > 0 else 0
        print(f"\n📈 Uplift (B vs A): {uplift:.2f}%")
        
        if uplift > 5.0:
            print("✅ Winner: Group B (Revenue Boost)")
            print("🚀 Recommendation: Rollout to 100%")
        else:
            print("⏸️ Result: Neutral or Negative. Keep testing.")

if __name__ == "__main__":
    asyncio.run(analyze_results())
