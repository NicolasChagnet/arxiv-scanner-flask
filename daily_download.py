""" This file should be set via some cron task to run once a day after the arXiv announcement. """

from datetime import date
from flask_app import manual_download_rss, get_filename

manual_download_rss(get_filename(date.today()))
