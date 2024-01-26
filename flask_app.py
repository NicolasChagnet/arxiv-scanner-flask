## Run @ http://arxivscan.pythonanywhere.com

from time import strftime
from datetime import date, datetime, timedelta
import os
from html import unescape
import re

import requests as rq
import feedparser as fd
from flask import Flask, request, redirect, url_for, render_template
import json


# Checks whether a string is a date of the correct format
def validate_date(date_str, dateformat):
    try:
        if date_str != datetime.strptime(date_str, dateformat).strftime(dateformat):
            raise ValueError
        return True
    except ValueError:
        return False


# Useful log function
def log(text):
    with open("arxiv_scanner.log", "a") as f:
        f.write(f"\n {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}: {text}")


LINKREG = r"<a[^>]*>([^<]*)<\/a>"  # Useful regex
USECACHE = True
CACHERSSFOLDER = "./cache_rss/"  # Folder where cached rss elements can be found
# Password to implement minimal security on the addition of new authors/kws
with open("password.txt", "r") as f:
    PASSWDADD = f.read()
# Loading the various parameters from the .json file
with open("./parameters.json") as f:
    parameters = json.loads(f.read())
SUBJECTS = parameters["categories"]


# Maximum articles from each category
MAX_ARTICLES = 2000
# Useful date formats
DATEFORMAT = "%Y-%m-%d"
DATEFORMATOUT = "%Y%m%d"


# This function gets the rss feed for each subject, calls the formatting function on each entry and builds a dictionary with all the necessary info
def get_rss():
    ret_dict = {
        "date": None,
        "topics": {},
        "number_articles": 0,
    }  # Format of the return dictionary
    ids = {}
    nentries = 0

    # Loop over each arXiv categories
    for sub in SUBJECTS:
        # Downloading of RSS feed
        url = f"http://export.arxiv.org/rss/{sub}"
        r = rq.get(url)
        rss_dict = fd.parse(r.text)

        # Extract and count the entries
        entries = rss_dict["entries"]
        nentries += len(entries)
        ret_dict["topics"][sub] = []
        # Uncomment the following line if you want to completely remove the updated entries
        # entries = list(filter(lambda e: e['title'][-8:-1] != 'UPDATED', entries))
        # Loop over entries formatting them and sorting the resulting list by arXiv identifier
        for e in entries:
            ret_dict["topics"][sub].append(format_entry_rss(e, sub, ids))
        ret_dict["topics"][sub] = sorted(
            ret_dict["topics"][sub], key=lambda u: u.get("identifier"), reverse=True
        )

    # Finishes packaging the output dictionary
    ret_dict["number_articles"] = nentries
    d = rss_dict["feed"]["updated_parsed"]
    d_f = strftime(DATEFORMAT, d)
    ret_dict["date"] = d_f

    return ret_dict


# Extracts the text inside an HTML link <a href=URL>text</a>
def format_link(link):
    return re.findall(LINKREG, link)


# From an entry of the RSS feed, extract useful information about the entry
def format_entry_rss(e, sub, ids):
    ret = {}  # Output dict initialization
    # We extract the title, removing useless portions
    title = e["title"].replace("\n ", "")
    inull = e["title"].find("arXiv:") - 2
    ret["title"] = title[:inull]
    # If the entry corresponds to an update, adds the proper postfix to our shortened title
    ret["updated"] = title.find("UPDATED") > -1
    if ret["updated"]:
        ret["title"] += " [UPDATED]"

    # Extracts the link to the abstract and to the pdf
    ret["link_abs"] = e["link"]
    ret["link_pdf"] = ret["link_abs"].replace("abs", "pdf") + ".pdf"
    ret["identifier"] = ret["link_abs"][ret["link_abs"].find("abs") + 4 :]

    # The authors are given as a series of HTML links. This extracts them all from the one string. The "unescape" function is required for accents in names escaped in the RSS feed.
    ret["authors"] = [
        unescape(author) for author in format_link(e["authors"][0]["name"])
    ]
    # Checks whether this entry is "duplicate" as in if it is present in more than one category we are watching at a given time. Stores this information using a global dictionary ids.
    if ret["identifier"] in ids:
        ret["duplicate"] = True
    else:
        ret["duplicate"] = False
        ids[ret["identifier"]] = True
    return ret


# Server app
app = Flask(__name__)


# Returns a filename in the cache folder given a date
def get_filename(date):
    date_str = date.strftime(DATEFORMAT)
    return f"{CACHERSSFOLDER}{date_str}.json"


# Gets the day's entries in RSS and writes to files
def manual_download_rss(filename):
    log(f"Manual downloading to {filename}")
    entries = get_rss()
    with open(filename, "w") as f:
        print(f"Write cache: {filename}")
        json.dump(entries, f)
    return entries


# Loads a file from cache **THIS ASSUMES THE FILE EXISTS**
def load_from_file(filename):
    print(f"From cache: {filename}")
    with open(filename) as f:
        entries = json.loads(f.read())
    return entries


# Routes the home to our home template with the day's RSS feed (either from cache or downloaded)
@app.route("/")
def home():
    filename = get_filename(date.today())
    if os.path.exists(filename) and USECACHE:
        log("Loading from cache")
        entries = load_from_file(filename)
        if entries["number_articles"] == 0:
            log("Cache empty")
            entries = manual_download_rss(filename)
    else:
        entries = manual_download_rss(filename)
    return render_template(
        "home.html",
        data=entries,
        watched_authors=parameters["authors"],
        watched_kw=parameters["keywords"],
        home_active=True,
    )


# If a date is given, checks whether a cached RSS exists
@app.route("/bydate")
def bydate():
    date_query_str = request.args.get("date", date.today().strftime(DATEFORMAT))
    date_query = datetime.strptime(date_query_str, DATEFORMAT)
    if validate_date(date_query_str, DATEFORMAT):
        filename = get_filename(date_query)
        if os.path.exists(filename):
            log("Loading from cache")
            entries = load_from_file(filename)
            return render_template(
                "home.html",
                data=entries,
                watched_authors=parameters["authors"],
                watched_kw=parameters["keywords"],
                home_active=False,
            )
        else:
            log("Cache file does not exist")
            return render_template("error.html", error="No file for that date!")
    else:
        log("Invalid date format requested")
        return render_template("error.html", error="Invalid date!")


@app.route("/add")
def show_add():
    return render_template("add_form.html")


@app.route("/add_treat", methods=["POST"])
def treat_add():
    new_author = request.form["author"]
    new_kw = request.form["keyword"]
    passwd = request.form["pass"]
    if passwd != PASSWDADD:
        log("Wrong password access")
        return render_template("error.html", error="Wrong password!")
    changed = False
    if new_author != "":
        log(f"Adding author {new_author}")
        parameters["authors"].append(new_author)
        changed = True
    if new_kw != "":
        log(f"Adding keyword {new_kw}")
        parameters["keywords"].append(new_kw)
        changed = True
    if changed:
        log("Saving new parameters to file")
        with open("./parameters.json", "w") as f:
            json.dump(parameters, f)

    return redirect(url_for("show_add"), code=302)


@app.route("/show")
def show_params():
    return render_template(
        "show_parameters.html",
        watched_authors=parameters["authors"],
        watched_kw=parameters["keywords"],
    )


if __name__ == "__main__":
    app.run(debug=False)
