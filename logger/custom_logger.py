import os
import logging
from datetime import datetime
class CustomLogger:
    def __init__(self):
        self.logs_dir=os.path.join(os.getcwd(),"log_dir")
        os.makedirs(self.logs_dir,exist_ok=True)

        #create timestamped log file
        log_file_name=f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.logs"
        log_file_path = os.path.join(self.logs_dir, log_file_name)
        #Configure logging
        logging.basicConfig(
            filename=log_file_path,
            format="[ %(asctime)s] %(levelname)s %(name)s (line:%(lineno)d)- %(message)s",
            level=logging.INFO,
        )
    def get_logger(self,name=__file__):
        return logging.getLogger(os.path.basename(name))
if __name__ == "__main__":
    logger=CustomLogger()
    logger=logger.get_logger(__file__)
    logger.info("Custom logger Initialized.")