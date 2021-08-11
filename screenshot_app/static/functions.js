function initializeForm() {
    enableButton();
    refreshForm();
}

function refreshForm() {
    // Expand Rubric if Category is 'Notice'
    if (document.getElementsByName('category')[3].checked) {
        enableRubric();
    } else {
        disableRubric();
    }

    // Expand Further Review Fields if Checked
    revealElement(document.getElementById('furtherreview'), document.getElementById('furtherreviewreasons'));
    revealElement(document.getElementById('furtherreview_language'), document.getElementById('furtherreview_language_select_area'));
    revealElement(document.getElementById('furtherreview_other'), document.getElementById('furtherreview_other_text_area'));
}


async function enableButton() {
    // Show Button After Time
    var fillprevious = document.getElementById("fillprevious");
    var fillpreviousbutton = document.getElementById("fillpreviousbutton");
    if (fillprevious.hidden == false) {
        await sleep(1000);
        fillpreviousbutton.disabled = false;
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function enableRubric() {
    var rubric = document.getElementById("rubric");
    rubric.hidden = false;
}

function disableRubric() {
    var rubric = document.getElementById("rubric");
    rubric.hidden = true;
}

function revealElement(item, itemelement) {
    if (item.checked == 1) {
        itemelement.hidden = false;
    } else if (item.checked == 0) {
        itemelement.hidden = true;
    }
}