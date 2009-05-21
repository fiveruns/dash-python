from threading import Thread, RLock
import time, logging

import exceptions
from protocol import InfoPayload, DataPayload

logger = logging.getLogger('fiveruns.dash.session')

class Reporter(Thread):
    
    def __init__(self, config):
        self.config = config
        self.interval = config.report_interval
        self.tick = 1
        self.stop_requested = False
        self.reported_info = False
        self.exception_recorder = exceptions.Recorder(self)
        Thread.__init__(self)
        
    def stop(self, *args, **kwargs):
        logger.debug("Shutting down...")
        self.stop_requested = True
    
    def run(self):
        self._report_info()
        self.last_report = time.time()
        while not self.stop_requested:
            time.sleep(self.tick)
            if self.stop_requested: break 
            if self._is_ready():
                self._report_data()
        logger.debug("Shut down")
        self._report_data()

    def add_exception(self, info, sample={}):
        self.exception_recorder.record(info, sample)
                    
    def _is_ready(self):
        return time.time() - self.last_report > self.interval
        
    def _report_info(self):
        info = InfoPayload(self.config)
        logger.debug("Sending InfoPayload...")
        self.reported_info = info.send()
        return self.reported_info

    def _report_data(self):
        self.last_report = time.time()
        data = DataPayload(self.config)
        if self.reported_info or self._report_info():
            logger.debug("Sending DataPayload...")
            return data.send()
        else:
            logger.debug("Discarding data for this interval.")
            return False
