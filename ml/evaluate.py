import pandas as pd
import numpy as np
from sklearn.metrics import ndcg_score

class OfflineEvaluator:
    def __init__(self, ground_truth_df, prediction_df):
        """
        ground_truth_df: DataFrame [user_id, listing_id, actual_label (0/1)]
        prediction_df: DataFrame [user_id, listing_id, predicted_score (0.0-1.0)]
        """
        self.gt = ground_truth_df
        self.pred = prediction_df

    def evaluate(self, k=10):
        # Merge on User + Listing
        merged = pd.merge(self.gt, self.pred, on=['user_id', 'listing_id'])
        
        ndcg_scores = []
        precision_scores = []
        
        # Group by User to evaluate ranking per session/user
        grouped = merged.groupby('user_id')
        
        for user_id, group in grouped:
            if len(group) < 2: continue # Need at least 2 items to rank
            
            y_true = [group['actual_label'].values]
            y_score = [group['predicted_score'].values]
            
            # NDCG
            try:
                score = ndcg_score(y_true, y_score, k=k)
                ndcg_scores.append(score)
            except:
                pass
                
            # Precision@K
            # Sort by score
            sorted_group = group.sort_values('predicted_score', ascending=False).head(k)
            hits = sorted_group['actual_label'].sum()
            precision = hits / k
            precision_scores.append(precision)
            
        return {
            "ndcg@10": np.mean(ndcg_scores) if ndcg_scores else 0.0,
            "precision@10": np.mean(precision_scores) if precision_scores else 0.0,
            "sample_size": len(ndcg_scores)
        }

if __name__ == "__main__":
    # Mock Data Test
    print("Running Mock Evaluation...")
    gt = pd.DataFrame({
        'user_id': [1, 1, 1, 2, 2],
        'listing_id': [101, 102, 103, 201, 202],
        'actual_label': [1, 0, 1, 0, 1]
    })
    pred = pd.DataFrame({
        'user_id': [1, 1, 1, 2, 2],
        'listing_id': [101, 102, 103, 201, 202],
        'predicted_score': [0.9, 0.2, 0.8, 0.4, 0.7] # Good ranking
    })
    
    evaluator = OfflineEvaluator(gt, pred)
    metrics = evaluator.evaluate()
    print(f"Metrics: {metrics}")
