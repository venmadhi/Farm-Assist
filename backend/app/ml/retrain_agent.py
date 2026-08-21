import os
import datetime
import pickle
from sqlalchemy.orm import Session
from ..models import CropCycle, ModelVersion
from .train_fertilizer import train_fertilizer_model
from .train_market import train_market_model

class RetrainAgent:
    def __init__(self, threshold: int = 1):
        # Set threshold to 1 for direct feedback loops
        self.threshold = threshold

    def check_and_retrain(self, db: Session, force: bool = False) -> (bool, str):
        """
        Check if the count of completed (HARVESTED) cycles since the last retraining
        exceeds the threshold. If so, trigger training.
        """
        # Count all completed crop cycles
        completed_count = db.query(CropCycle).filter(CropCycle.status == "HARVESTED").count()
        
        # Get count of training records used in last training run
        last_run = db.query(ModelVersion).order_by(ModelVersion.training_date.desc()).first()
        last_count = last_run.training_records_count if last_run else 0
        
        new_records = completed_count - last_count
        if new_records < 0:
            new_records = 0
            
        print(f"Retraining checker: Completed Cycles={completed_count}, Last Run Count={last_count}, New Records={new_records}")
        
        if new_records >= self.threshold or force:
            print("Triggering periodic model retraining pipeline...")
            
            # 1. Retrain Fertilizer model
            fert_model_name, fert_acc, fert_count = train_fertilizer_model()
            
            # Save version metadata to DB
            _now = datetime.datetime.now(datetime.timezone.utc)
            fert_version = ModelVersion(
                model_name="fertilizer_model",
                version=f"v{_now.strftime('%Y%m%d%H%M%S')}",
                training_date=_now,
                dataset_version="fertilizer_dataset_v1.0",
                training_records_count=completed_count,
                validation_metric_name="accuracy",
                validation_metric_value=fert_acc,
                is_active=True
            )
            db.add(fert_version)
            
            # 2. Retrain Market model
            market_model_name, market_r2, market_count = train_market_model()
            
            # Save version metadata to DB
            _now2 = datetime.datetime.now(datetime.timezone.utc)
            market_version = ModelVersion(
                model_name="market_model",
                version=f"v{_now2.strftime('%Y%m%d%H%M%S')}",
                training_date=_now2,
                dataset_version="mandi_monthly_v1.0",
                training_records_count=completed_count,
                validation_metric_name="r2",
                validation_metric_value=market_r2,
                is_active=True
            )
            db.add(market_version)
            db.commit()
            
            # Reload agents to pick up new pkl files
            try:
                from .fertilizer_agent import fertilizer_agent
                fertilizer_agent.load_model()
            except Exception as e:
                print(f"Failed to reload fertilizer agent: {e}")
                
            try:
                from .market_agent import market_agent
                market_agent.load_model()
            except Exception as e:
                print(f"Failed to reload market agent: {e}")
                
            msg = f"Successfully retrained models: Fertilizer ({fert_model_name} acc: {fert_acc * 100:.2f}%) and Market ({market_model_name} R2: {market_r2:.4f})."
            print(msg)
            return True, msg
        else:
            return False, f"Retraining skipped. New records ({new_records}) below threshold ({self.threshold})."

retrain_agent = RetrainAgent(threshold=1)
