const paperFile = document.getElementById('paper-file');
const paperContainer = document.getElementById('paper-container');
const paperTitle = document.getElementById('paper-title');
const paperPdf = document.getElementById('paper-pdf');
const paperAbs = document.getElementById('paper-abs');
const ratingValue = document.getElementById('paper-rating');
const paperKeywords = document.getElementById('paper-keywords');
const paperAbstract = document.getElementById('paper-abstract');
const paperSubjects = document.getElementById('paper-subjects');
const paperComments = document.getElementById('paper-comments');
const currentIndexSpan = document.getElementById('current-index');
const totalPapersSpan = document.getElementById('total-papers');
const prevButton = document.getElementById('prev-paper');
const jumpButton = document.getElementById('jump-paper');
const nextButton = document.getElementById('next-paper');
const llmScore = document.getElementById('llm-score');
const llmComment = document.getElementById('llm-comment');
const paperTopic = document.getElementById('paper-topic');

let papers = [];
let currentPaperIndex = 0;

function logging(info) {
    fetch("/", {
        method: "POST",
        headers: {"Content-Type": "application/json; charset=utf-8"},
        body: JSON.stringify({
            task: "log",
            info: info
        })
    })
}

function displayPaper(index) {
    const paper = papers[index];
    if (!paper) return;

    paperTitle.textContent = paper['title'];
    paperPdf.href = `${paper['abstract url']}.pdf#view=FitH`.replace("abs", "pdf");
    paperAbs.href = `${paper['abstract url']}`;
    ratingValue.textContent = `${paper['rating']}`;
    paperKeywords.textContent = `${paper['keywords'].join(', ')}`;
    paperAbstract.textContent = `${paper['abstract']}`;
    paperSubjects.textContent = `${paper['subjects'].join(', ')}`;
    paperComments.textContent = `${paper['comment']}`;
    // Add LLM score and comment
    if ('llm_score' in paper) {
        llmScore.textContent = paper['llm_score'];
        llmScore.parentElement.style.display = 'block';
    } else {
        llmScore.parentElement.style.display = 'none';
    }

    if ('llm_comment' in paper) {
        llmComment.textContent = paper['llm_comment'];
        llmComment.parentElement.style.display = 'block';
    } else {
        llmComment.parentElement.style.display = 'none';
    }
    userScore.value = '';

    if ('topic' in paper) {
        paperTopic.querySelector('span').textContent = paper['topic'];
        paperTopic.style.display = 'block';
    } else {
        paperTopic.style.display = 'none';
    }

    logging({
        action: "change paper",
        fileName: paperFile.value,
        index: index
    })
}

function updateNavigation() {
    currentIndexSpan.textContent = currentPaperIndex + 1;
    totalPapersSpan.textContent = papers.length;
    prevButton.disabled = currentPaperIndex === 0;
    nextButton.disabled = currentPaperIndex === papers.length - 1;
}

async function selectFile() {
    const response = await fetch("/", {
        method: "POST",
        headers: {"Content-Type": "application/json; charset=utf-8"},
        body: JSON.stringify({
            task: "selectFile",
            fileName: paperFile.value
        })
    });
    response_json = await response.json();
    papers = response_json["papers"];
    currentPaperIndex = 0;
    displayPaper(currentPaperIndex);
    updateNavigation();
}

function prevPaper() {
    if (currentPaperIndex > 0) {
        currentPaperIndex--;
        displayPaper(currentPaperIndex);
        updateNavigation();
    }
}

function nextPaper() {
    if (currentPaperIndex < papers.length - 1) {
        currentPaperIndex++;
        displayPaper(currentPaperIndex);
        updateNavigation();
    }
}

function jumpPaper() {
    const newIndex = parseInt(prompt("Enter an index:"));
    if (!isNaN(newIndex)) {
        if (newIndex < 1) {
            currentPaperIndex = 0;
        } else if (newIndex > papers.length) {
            currentPaperIndex = papers.length - 1;
        } else {
            currentPaperIndex = newIndex - 1;
        }
        displayPaper(currentPaperIndex);
        updateNavigation();
    }
}

function jumpToNextDay() {
    const currentIndex = paperFile.selectedIndex;
    if (currentIndex > 0) {
        paperFile.selectedIndex = currentIndex - 1;
        selectFile();
    }
}

function jumpToPreviousDay() {
    const currentIndex = paperFile.selectedIndex;
    if (currentIndex < paperFile.options.length - 1) {
        paperFile.selectedIndex = currentIndex + 1;
        selectFile();
    }
}

window.addEventListener('load', selectFile);
paperFile.addEventListener('change', selectFile);
prevButton.addEventListener('click', prevPaper);
nextButton.addEventListener('click', nextPaper);
jumpButton.addEventListener('click', jumpPaper);


// for keyboard shortcut
async function preWriteNotes() {
    const response = await fetch("/", {
        method: "POST",
        headers: {"Content-Type": "application/json; charset=utf-8"},
        body: JSON.stringify({
            task: "pre-writeNotes",
            url: papers[currentPaperIndex]['abstract url']
        })
    });
    const prevNotes = (await response.json())["prevNotes"]

    return prevNotes
}

async function handleKeyDown(event) {
    const key = event.key;

    if (key === "ArrowLeft" || key === "h") {
        prevPaper();
    } else if (key === "ArrowRight" || key === "l") {
        nextPaper();
    } else if (key === "/") {
        jumpPaper();
    } else if (key == "s") {
        paperFile.focus();
    } else if (key == "p") {
        window.open(`${papers[currentPaperIndex]['abstract url']}.pdf#view=FitH`.replace("abs", "pdf"), '_blank', 'location=yes,scrollbars=yes,status=yes')
    } else if (key == "n") {
        const prevNotes = await preWriteNotes();
        const body = {
            task: "writeNotes",
            date: paperFile.value.replace(".json", ""),
            title: papers[currentPaperIndex]['title'],
            note: prompt("Enter note here:", prevNotes),
            url: papers[currentPaperIndex]['abstract url'],
            keywords: papers[currentPaperIndex]['keywords']
        }

        fetch("/", {
            method: "POST",
            headers: {"Content-Type": "application/json; charset=utf-8"},
            body: JSON.stringify(body)
        })
    } else if (key == "t") {
        navigator.clipboard.writeText(papers[currentPaperIndex]['title'])
        alert("title copied");
    } else if (key == "a") {
        navigator.clipboard.writeText(papers[currentPaperIndex]['abstract url'])
        alert("abstract url copied");
    }
    else if (key == "r") {
        userScore.focus();
    } 
    else if (key === "k") {
        jumpToNextDay();
    } 
    else if (key === "j") {
        jumpToPreviousDay();
    }
    else if (key === "?") {
        alert("Keyboard shortcuts:\n" +
              "previous paper: left, h\n" +
              "next paper: right, l\n" +
              "Jump to index: /\n" +
              "Focus select file: s\n" +
              "Open pdf: p\n" +
              "Write note: n\n" +
              "Copy title: t\n" +
              "Copy abstract url: a\n" +
              "Focus score input: r\n" +
              "Submit score and next paper: Enter (when score input is focused)\n" +
              "Jump to next day: k\n" +
              "Jump to previous day: j");
    }
    if ((key === "ArrowLeft" || key === "ArrowRight") && document.activeElement === userScore) {
        event.preventDefault();
    }
}

const userScore = document.getElementById('user-score');
const submitScoreButton = document.getElementById('submit-score');

function submitScore() {
    const score = userScore.value;
    if (score >= 1 && score <= 10) {
        fetch("/", {
            method: "POST",
            headers: {"Content-Type": "application/json; charset=utf-8"},
            body: JSON.stringify({
                task: "submitScore",
                paperId: papers[currentPaperIndex]['paper id'],
                score: parseInt(score),
                date: paperFile.value.replace(".json", ""),
                title: papers[currentPaperIndex]['title'],
                topic: papers[currentPaperIndex]['topic'], // Add this line
                abstract: papers[currentPaperIndex]['abstract']
            })
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                userScore.value = "";
                nextPaper(); // Automatically move to the next paper
            } else {
                alert("Failed to submit score. Please try again.");
            }
        });
    } else {
        alert("Please enter a valid score between 1 and 10.");
    }
}

submitScoreButton.addEventListener('click', submitScore);

// Add event listener for Enter key on the score input
userScore.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent form submission
        submitScore();
    }
});

document.addEventListener("keydown", handleKeyDown);


submitScoreButton.addEventListener('click', submitScore);


