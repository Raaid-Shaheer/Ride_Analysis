import logging
from src.loader  import load_all_files
from src.cleaner import run_pipeline
from src.export  import run_export
from src.config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
   try:
       raw_df =load_all_files(RAW_DIR)
       # Guard — if no new files, exit cleanly
       if raw_df.empty:
           logger.info("Nothing to do — exiting")
           return

       clean_df =run_pipeline(raw_df)
       results =run_export(clean_df,PROCESSED_DIR)

       logger.info(f"Cleaned rides → {results['cleaned_path']}")
       logger.info(f"Summary stats → {results['summary_path']}")
       logger.info(f"Total rows processed: {results['row_count']}")

   except Exception as e:
        logger.error(f"Pipeline failed: {e}")






if __name__ == "__main__":
    main()