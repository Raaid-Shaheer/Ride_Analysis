import sys
import logging
from src.loader  import load_all_files
from src.cleaner import run_pipeline
from src.export  import run_export
from src.model   import run_model_pipeline
from src.config  import RAW_DIR, PROCESSED_DIR

logging.basicConfig(
    level   = logging.INFO,
    stream  = sys.stdout,
    format  = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    try:
        # ── Phase 1 — Load ───────────────────────────────────────
        raw_df = load_all_files(RAW_DIR)

        if raw_df.empty:
            logger.info("No new files to process — running model on existing data")
        else:
            # ── Phase 2 — Clean ──────────────────────────────────
            clean_df = run_pipeline(raw_df)

            # ── Phase 3 — Export ─────────────────────────────────
            results = run_export(clean_df, PROCESSED_DIR)
            logger.info(f"Cleaned rides → {results['cleaned_path']}")
            logger.info(f"Summary stats → {results['summary_path']}")
            logger.info(f"Total rows processed: {results['row_count']}")

        # ── Phase 4 — Model ──────────────────────────────────────
        # Always retrain — simpler than tracking whether cleaned_rides.csv changed.
        # Retraining is fast enough that the overhead is acceptable.
        # Also picks up any config or hyperparameter changes automatically.
        model_results = run_model_pipeline(PROCESSED_DIR)

        logger.info("=" * 60)
        logger.info("MODEL RESULTS")
        logger.info("=" * 60)
        for platform in ['pickme', 'uber']:
            m = model_results[platform]
            logger.info(
                f"{platform.upper():8s} | "
                f"RMSE: {m['rmse']:8.2f} | "
                f"MAE: {m['mae']:8.2f} | "
                f"R²: {m['r2']:.4f} | "
                f"Best: {m['model_name']}"
            )
        logger.info(f"Predictions → {model_results['predictions_path']}")
        logger.info(f"Grid rows   → {model_results['prediction_rows']:,}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()