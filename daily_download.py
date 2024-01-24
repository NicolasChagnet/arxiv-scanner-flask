## This file should be set via some cron task to run once a day after the arXiv announcement.

from flask_app import *

manual_download_rss(get_filename(date.today()))
