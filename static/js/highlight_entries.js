function highlight_entries(watched_authors, watched_kw) {
    const links = document.querySelectorAll('.authors');

    links.forEach(link => {
        var text = link.innerHTML.toLowerCase();
        var change = false;
        watched_authors.forEach(ref => {
            if (text.includes(ref.toLowerCase())) {
                // console.log("Detecting " + ref)
                change = true;
            }
        })
        if (change === true) {
            link.parentElement.parentElement.classList.add("watched")
        }
    })

    const titles = document.querySelectorAll('.title');
    const updated_string = "UPDATED".toLowerCase();
    titles.forEach(title => {
        var text = title.innerHTML.toLowerCase();
        var change = false;
        watched_kw.forEach(kw => {
            if (text.includes(kw.toLowerCase())) {
                change = true;
            }
        })
        if (change === true) {
            title.parentElement.classList.add("watched")
        }
        if (text.includes(updated_string)) {
            title.parentElement.classList.add("updated")
        }
    })

    // show_hide_duplicates()

    var button_watched = document.getElementById('button_watched');
    var button_updated = document.getElementById('button_updated');

    button_watched.checked = false;
    button_updated.checked = false;

    function hide_elements(event) {
        const els = document.querySelectorAll('li');
        var unwatched_state = button_watched.checked
        var updated_state   = button_updated.checked
        els.forEach(link => {
            var is_watched     = (link.classList.contains('watched'))
            var is_not_updated = !(link.classList.contains('updated'))
            if (updated_state) {
                if (unwatched_state) {
                    truestate = (is_not_updated) && (is_watched)
                } else {
                    truestate = (is_not_updated)
                }
            } else {
                if (unwatched_state) {
                    truestate = (is_watched)
                } else {
                    truestate = true
                }
            }
            if (!truestate) {
                link.classList.add('hidden')
            } else {
                link.classList.remove('hidden')
            }
        })
    }
    button_watched.addEventListener('change', hide_elements)
    button_updated.addEventListener('change', hide_elements)

    button_watched.checked = true;
    hide_elements();
}