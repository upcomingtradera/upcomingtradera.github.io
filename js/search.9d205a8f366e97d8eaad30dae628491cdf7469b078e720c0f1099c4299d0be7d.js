let idx;
let documents;

// Immediately update the title based on the query string
const urlParams = new URLSearchParams(window.location.search);
const query = urlParams.get('q');
const titleElement = document.querySelector('.search-page h1');
if (titleElement && query) {
    titleElement.textContent = `Search results for "${query}"`;
}

// Load the data from index.json
fetch('/index.json')
    .then(response => response.json())
    .then(data => {
        documents = data;
        // Initialize the Lunr index
        idx = lunr(function () {
            this.ref('url');
            this.field('title', { boost: 10 });
            this.field('content', { boost: 50 });
            this.field('description', { boost: 15 });
            this.field('type');
            this.field('pageType');
            this.field('date');

            data.forEach(doc => {
                this.add(doc);
            });
        });

        // Perform the search after the index is initialized
        performSearch();
    })
    .catch(error => {
        console.error("Error loading index data:", error);
    });

function handleSearch(event) {
    event.preventDefault();

    if (!idx) {
        console.log("Lunr index is not initialized yet.");
        return false;
    }

    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (typeof gtag !== 'undefined') {
        gtag('event', 'Search JS Query - UT', {
            'event_category': 'site_search',
            'event_label': query
        });
    }

    if (!query) {
        console.log("Search query is empty.");
        return false;
    }

    window.location.href = "/search/?q=" + encodeURIComponent(query);
    return false;
}

function performSearch() {
    if (query && idx) {
        const results = idx.search(query);
        const resultsContainer = document.getElementById('searchResults');

        if (results.length === 0) {
            resultsContainer.innerHTML = "<p>No results found for your search.</p>";
            return;
        }

        results.forEach(result => {
            const ref = result.ref;
            const fullData = documents.find(doc => doc.url === ref);

            // Convert the full URL to a relative URL
            const relativeUrl = new URL(fullData.url).pathname;

            const resultElement = document.createElement('div');
            resultElement.innerHTML = `
                <h2><a href="${relativeUrl}">${fullData.title}</a></h2>
                <p>${fullData.description}</p>
            `;
            resultsContainer.appendChild(resultElement);
        });
    }
}

// If the Lunr index isn't ready when the page loads, the performSearch function will be called after the index is initialized.
document.addEventListener("DOMContentLoaded", function() {
    if (idx) {
        performSearch();
    }
});

