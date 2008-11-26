from __future__ import with_statement
from threading import Thread, RLock
import time

from logging import log
from protocol import InfoPayload, DataPayload

class Reporter(Thread):
  
  def __init__(self, config):
    self.config = config
    self.interval = config.report_interval
    self.tick = 1
    self.stop_requested = False
    self.reported_info = False
    Thread.__init__(self)
    
  def stop(self, *args, **kwargs):
    log("Shutting down...")
    self.stop_requested = True
  
  def run(self):
    self._report_info()
    self.last_report = time.time()
    while not self.stop_requested:
      time.sleep(self.tick)
      if self.stop_requested: break 
      if self._is_ready():
        self._report_data()
    log("Shut down")
          
  def _is_ready(self):
    return time.time() - self.last_report > self.interval
    
  def _report_info(self):
    info = InfoPayload(self.config)
    log("Sending InfoPayload...")
    self.reported_info = info.send()
    return self.reported_info

  def _report_data(self):
    self.last_report = time.time()
    data = DataPayload(self.config)
    if self.reported_info or self._report_info():
      log("Sending DataPayload...")
      return data.send()
    else:
      log("Discarding data for this interval.")
      return False