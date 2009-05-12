from simplejson import loads
from datetime import datetime, timedelta
import sys
import urllib2
from fiveruns import dash

TERM = 'iphone'

class TwitterGetter(object):
    def load(self):
        url = 'http://twitter.com/statuses/public_timeline_partners_nrab481.json'
        #url = 'http://twitter.com/statuses/public_timeline.json'
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        return loads(response.read())
    
class TwitterWordTrack(object):
    def __init__(self, term_to_track, twitter=TwitterGetter()):
        self.twitter = twitter
        self.term = term_to_track.lower()
        self.hits = 0
        self.hits_per_day = 0
        self.misses = 0
        self.last_load = datetime.now() - timedelta(seconds=61)

    def incr_hits(self):
        self.hits += 1

    def incr_misses(self):
        self.misses += 1

    def percent_hits(self):
        return self.hits / float(self.total()) * 100

    def percent_misses(self):
        if self.total() == 0:
            return 0.0
        return self.misses / float(self.total()) * 100

    def total(self):
        return self.hits + self.misses

    def search_for_term(self):
        for message in self.twitter.load():
            if self.term in [word.lower() for word in message['text'].split()]:
                print self.term
                self.incr_hits()
            else:
                self.incr_misses()

    def run(self):
        while 1:
            now = datetime.now()
            if (now - self.last_load) > timedelta(seconds=5):
                self.last_load = now
                self.search_for_term()
            
def build_dash_config(tracker, app_token):
    recipe = dash.recipe('twitter_tracker', 'http://dash.fiveruns.com')
    recipe.counter('hits', 'Number of times the TERM is encountered', wrap=TwitterWordTrack.incr_hits)
    recipe.counter('misses', 'Number of times the TERM is not encountered', wrap=TwitterWordTrack.incr_misses)
    recipe.time('twitter_wait', 'Time spent waiting on Twitter', wrap=TwitterGetter.load)
    recipe.percentage('percent_hits', 'Percentage of messages that are hits', call=tracker.percent_hits)
    recipe.percentage('percent_misses', 'Percentage of messages that are misses', call=tracker.percent_misses)

    config = dash.configure(app_token=app_token)
    config.add_recipe('twitter_tracker')
    return config

            
def main():
    app_token = sys.argv[1]
    tracker = TwitterWordTrack(TERM)
    config = build_dash_config(tracker, app_token)
   
    reporter = dash.start(config) 
    try:
        tracker.run()
    except KeyboardInterrupt:
        reporter.stop()
        raise KeyboardInterrupt

if __name__ == '__main__':
    main()
