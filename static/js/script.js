const PLACEHOLDER_POSTER = "/static/images/no-poster.svg";
const SKELETON_COUNT = 6;
const STORAGE_KEYS = {
    watchlist: "cinemate-watchlist",
    recentSearches: "cinemate-recent-searches",
};
const FEATURED_COLLECTIONS = [
    "weekend-movies",
    "rainy-day",
    "space-adventure",
    "feel-good",
    "mind-bending",
    "family-night",
];

let watchlistItems = [];
let recentSearches = [];

function readStorage(key) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : [];
    } catch (error) {
        console.warn("Local storage is unavailable:", error);
        return [];
    }
}

function writeStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.warn("Could not save to local storage:", error);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const searchForm = document.getElementById("search-form");
    const searchInput = document.getElementById("movie-search");
    const searchBtn = document.getElementById("search-btn");
    const resultsSection = document.getElementById("results");
    const collectionsGrid = document.getElementById("collections-grid");
    const recentList = document.getElementById("recent-list");
    const watchlistSection = document.getElementById("watchlist-section");
    const watchlistGrid = document.getElementById("watchlist-grid");
    const watchlistSearch = document.getElementById("watchlist-search");
    const clearWatchlistBtn = document.getElementById("clear-watchlist-btn");
    const watchlistNavBtn = document.getElementById("watchlist-nav-btn");
    const recentNavBtn = document.getElementById("recent-nav-btn");
    const collectionsNavBtn = document.getElementById("collections-nav-btn");

    setTimeOfDayTheme();
    initializeState();
    bindEvents();
    renderCollections();
    renderRecentSearches();
    renderWatchlist();
    updateNavBadges();

    function setTimeOfDayTheme() {
        const hour = new Date().getHours();
        let theme = "theme-night";

        if (hour >= 5 && hour < 11) {
            theme = "theme-morning";
        } else if (hour >= 11 && hour < 17) {
            theme = "theme-afternoon";
        } else if (hour >= 17 && hour < 20) {
            theme = "theme-evening";
        }

        document.body.classList.remove("theme-morning", "theme-afternoon", "theme-evening", "theme-night");
        document.body.classList.add(theme);
    }

    function initializeState() {
        watchlistItems = readStorage(STORAGE_KEYS.watchlist);
        recentSearches = readStorage(STORAGE_KEYS.recentSearches);
    }

    function bindEvents() {
        searchForm.addEventListener("submit", searchMovies);
        resultsSection.addEventListener("click", handleResultsCardClick);
        watchlistGrid.addEventListener("click", handleWatchlistCardClick);
        recentList.addEventListener("click", handleRecentClick);

        watchlistNavBtn.addEventListener("click", function () {
            watchlistSection.classList.remove("is-hidden");
            watchlistSection.scrollIntoView({ behavior: "smooth", block: "start" });
        });

        recentNavBtn.addEventListener("click", function () {
            document.getElementById("recent-section").scrollIntoView({ behavior: "smooth", block: "start" });
        });

        collectionsNavBtn.addEventListener("click", function () {
            document.getElementById("collections-section").scrollIntoView({ behavior: "smooth", block: "start" });
        });

        watchlistSearch.addEventListener("input", renderWatchlist);
        clearWatchlistBtn.addEventListener("click", clearWatchlist);
    }

    function escapeHtml(text) {
        if (!text) {
            return "";
        }

        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function getPosterUrl(poster) {
        if (poster && poster !== "N/A") {
            return poster;
        }

        return PLACEHOLDER_POSTER;
    }

    function usePosterFallback(image) {
        if (!image || image.dataset.fallbackApplied === "true") {
            return;
        }

        image.dataset.fallbackApplied = "true";
        image.src = PLACEHOLDER_POSTER;
    }

    function bindPosterFallbacks() {
        const posters = document.querySelectorAll(".movie-poster");

        for (let i = 0; i < posters.length; i++) {
            const poster = posters[i];
            poster.addEventListener("error", function () {
                usePosterFallback(poster);
            });
        }

        window.setTimeout(function () {
            for (let i = 0; i < posters.length; i++) {
                const poster = posters[i];
                if (!poster.complete || poster.naturalWidth === 0) {
                    usePosterFallback(poster);
                }
            }
        }, 8000);
    }

    function cleanValue(value, fallback) {
        if (!value || value === "N/A") {
            return fallback;
        }

        return value;
    }

    function buildGenrePills(genreString) {
        if (!genreString || genreString === "N/A") {
            return "";
        }

        const genres = String(genreString).split(",");
        let html = "<div class=\"genre-list\" aria-label=\"Genres\">";

        for (let i = 0; i < genres.length; i++) {
            const genre = genres[i].trim();
            if (genre) {
                html += "<span class=\"genre-pill\">" + escapeHtml(genre) + "</span>";
            }
        }

        html += "</div>";
        return html;
    }

    function formatMatchScore(score) {
        const numericScore = Number(score);

        if (!Number.isNaN(numericScore) && numericScore <= 1) {
            return Math.round(numericScore * 100) + "% Match Score";
        }

        return escapeHtml(String(score)) + " Match Score";
    }

    function showSkeletonLoading() {
        let html = "<div class=\"skeleton-wrap\" aria-label=\"Loading suggestions\">";
        html += "<div class=\"skeleton-grid\">";

        for (let i = 0; i < SKELETON_COUNT; i++) {
            html += "<article class=\"skeleton-card\" aria-hidden=\"true\">";
            html += "<div class=\"skeleton-poster\"></div>";
            html += "<div class=\"skeleton-body\">";
            html += "<div class=\"skeleton-line skeleton-line--title\"></div>";
            html += "<div class=\"skeleton-line skeleton-line--short\"></div>";
            html += "<div class=\"skeleton-line skeleton-line--medium\"></div>";
            html += "<div class=\"skeleton-line skeleton-line--long\"></div>";
            html += "</div>";
            html += "</article>";
        }

        html += "</div>";
        html += "<p class=\"skeleton-message\">Finding something wonderful for you...</p>";
        html += "</div>";

        resultsSection.innerHTML = html;
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function setButtonLoading(isLoading) {
        const buttonText = searchBtn.querySelector(".btn-text");
        searchBtn.disabled = isLoading;

        if (isLoading) {
            searchBtn.classList.add("is-loading");
            buttonText.textContent = "✨ Looking...";
        } else {
            searchBtn.classList.remove("is-loading");
            buttonText.textContent = "🍿 Discover Movies";
        }
    }

    function showEmptyState(title, message) {
        resultsSection.innerHTML =
            "<div class=\"empty-state\" role=\"status\">" +
            "<div class=\"empty-illustration\" aria-hidden=\"true\">" +
            "<svg viewBox=\"0 0 240 170\" xmlns=\"http://www.w3.org/2000/svg\">" +
            "<path class=\"empty-ground\" d=\"M20 136 C54 114 90 120 120 132 C154 148 190 142 220 124 V156 H20Z\"/>" +
            "<path class=\"empty-screen\" d=\"M66 34 H174 Q184 34 184 44 V104 Q184 114 174 114 H66 Q56 114 56 104 V44 Q56 34 66 34Z\"/>" +
            "<path class=\"empty-curtain-left\" d=\"M66 34 C82 52 78 92 62 114 H66 Q56 114 56 104 V44 Q56 34 66 34Z\"/>" +
            "<path class=\"empty-curtain-right\" d=\"M174 34 C158 52 162 92 178 114 H174 Q184 114 184 104 V44 Q184 34 174 34Z\"/>" +
            "<path class=\"empty-branch\" d=\"M52 126 C72 96 88 82 112 72\" fill=\"none\"/>" +
            "<path class=\"empty-branch\" d=\"M188 126 C170 98 152 82 128 72\" fill=\"none\"/>" +
            "<ellipse class=\"empty-leaf\" cx=\"92\" cy=\"84\" rx=\"8\" ry=\"16\"/>" +
            "<ellipse class=\"empty-leaf\" cx=\"150\" cy=\"84\" rx=\"8\" ry=\"16\"/>" +
            "<circle class=\"empty-star\" cx=\"112\" cy=\"60\" r=\"3\"/>" +
            "<circle class=\"empty-star\" cx=\"132\" cy=\"56\" r=\"2\"/>" +
            "</svg>" +
            "</div>" +
            "<h2 class=\"empty-title\">" + escapeHtml(title) + "</h2>" +
            "<p class=\"empty-message\">" + escapeHtml(message) + "</p>" +
            "</div>";

        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function showErrorCard(title, message) {
        resultsSection.innerHTML =
            "<div class=\"error-card\" role=\"alert\">" +
            "<svg class=\"error-icon\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" aria-hidden=\"true\">" +
            "<path d=\"M12 3 2.8 19.5h18.4L12 3Z\"></path>" +
            "<path d=\"M12 9v4\"></path>" +
            "<path d=\"M12 17h.01\"></path>" +
            "</svg>" +
            "<h2 class=\"error-title\">" + escapeHtml(title) + "</h2>" +
            "<p class=\"error-text\">" + escapeHtml(message) + "</p>" +
            "</div>";

        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function runSearch(query) {
        const movieName = String(query || "").trim();

        if (!movieName) {
            return;
        }

        searchInput.value = movieName;
        showSkeletonLoading();
        setButtonLoading(true);

        fetch("/recommend", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ movie: movieName }),
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success) {
                    addRecentSearch(movieName);
                }
                displayResults(data);
            })
            .catch(function () {
                showErrorCard(
                    "The lights flickered.",
                    "Something interrupted the search. Please try again in a moment."
                );
            })
            .finally(function () {
                setButtonLoading(false);
            });
    }

    function searchMovies(event) {
        event.preventDefault();
        runSearch(searchInput.value);
    }

    function addRecentSearch(query) {
        const cleanQuery = String(query || "").trim();

        if (!cleanQuery) {
            return;
        }

        recentSearches = recentSearches.filter(function (item) {
            return item !== cleanQuery;
        });

        recentSearches.unshift(cleanQuery);
        recentSearches = recentSearches.slice(0, 10);
        writeStorage(STORAGE_KEYS.recentSearches, recentSearches);
        renderRecentSearches();
    }

    function renderRecentSearches() {
        if (!recentSearches.length) {
            recentList.innerHTML = "<div class=\"empty-inline\">No search history yet. Your next discovery will appear here.</div>";
            return;
        }

        let html = "<div class=\"recent-list-grid\">";

        for (let i = 0; i < recentSearches.length; i++) {
            const query = recentSearches[i];
            html += "<button type=\"button\" class=\"recent-chip\" data-query=\"" + escapeHtml(query) + "\">" + escapeHtml(query) + "</button>";
        }

        html += "</div>";
        recentList.innerHTML = html;
    }

    function getMovieKey(movie) {
        if (!movie) {
            return "";
        }

        if (movie.id) {
            return String(movie.id).toLowerCase();
        }

        return String(movie.title || "").toLowerCase();
    }

    function isMovieSaved(movie) {
        const key = getMovieKey(movie);

        return watchlistItems.some(function (item) {
            return getMovieKey(item) === key;
        });
    }

    function saveMovie(movie) {
        const key = getMovieKey(movie);

        if (!key) {
            return;
        }

        const alreadySaved = watchlistItems.some(function (item) {
            return getMovieKey(item) === key;
        });

        if (!alreadySaved) {
            watchlistItems.unshift(movie);
            writeStorage(STORAGE_KEYS.watchlist, watchlistItems);
            updateNavBadges();
            renderWatchlist();
        }
    }

    function removeMovie(movie) {
        const key = getMovieKey(movie);

        if (!key) {
            return;
        }

        watchlistItems = watchlistItems.filter(function (item) {
            return getMovieKey(item) !== key;
        });

        writeStorage(STORAGE_KEYS.watchlist, watchlistItems);
        updateNavBadges();
        renderWatchlist();
    }

    function clearWatchlist() {
        watchlistItems = [];
        writeStorage(STORAGE_KEYS.watchlist, watchlistItems);
        updateNavBadges();
        renderWatchlist();
    }

    function updateNavBadges() {
        const count = watchlistItems.length;
        watchlistNavBtn.textContent = count ? "♡ Watchlist (" + count + ")" : "♡ Watchlist";
    }

    function renderWatchlist() {
        const query = watchlistSearch.value.trim().toLowerCase();
        const filteredItems = watchlistItems.filter(function (movie) {
            if (!query) {
                return true;
            }

            const haystack = [movie.title, movie.year, movie.genre, movie.director, movie.plot]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();

            return haystack.indexOf(query) >= 0;
        });

        if (!filteredItems.length) {
            watchlistGrid.innerHTML = "<div class=\"watchlist-empty\">No watchlist items yet. Save a few favorites and they will appear here.</div>";
            return;
        }

        let html = "<div class=\"cards-container watchlist-cards\">";

        for (let i = 0; i < filteredItems.length; i++) {
            const movie = filteredItems[i];
            const posterUrl = getPosterUrl(movie.poster);
            const title = cleanValue(movie.title, "Untitled film");
            const year = cleanValue(movie.year, "");
            const rating = cleanValue(movie.rating, "Not rated");
            const runtime = cleanValue(movie.runtime, "Runtime unknown");
            const plot = cleanValue(movie.plot, "A little mystery still surrounds this one.");
            const director = cleanValue(movie.director, "A storyteller");
            const language = cleanValue(movie.language, "A language of cinema");

            html += "<article class=\"movie-card watchlist-card\">";
            html += "<div class=\"poster-wrapper\">";
            html += "<img class=\"movie-poster\" src=\"" + escapeHtml(posterUrl) + "\" alt=\"Poster for " + escapeHtml(title) + "\" loading=\"lazy\">";
            html += "</div>";
            html += "<div class=\"movie-details\">";
            html += "<div class=\"card-topline\">";
            html += "<h3 class=\"card-title\">" + escapeHtml(title) + "</h3>";
            html += "<button type=\"button\" class=\"card-action-btn card-action-btn--watchlist is-active\" data-action=\"remove-watchlist\" data-title=\"" + escapeHtml(title) + "\">Remove</button>";
            html += "</div>";
            html += "<div class=\"card-meta\">";
            if (year) {
                html += "<span class=\"meta-badge\">" + escapeHtml(year) + "</span>";
            }
            html += "<span class=\"rating-badge\" aria-label=\"IMDb rating\">&#9733; " + escapeHtml(rating) + "</span>";
            html += "<span class=\"meta-badge\">" + escapeHtml(runtime) + "</span>";
            html += "</div>";
            html += buildGenrePills(movie.genre);
            html += "<p class=\"card-plot\">" + escapeHtml(plot) + "</p>";
            html += "<div class=\"card-credits\">";
            html += "<div class=\"credit-block\"><span class=\"credit-label\">Director</span>" + escapeHtml(director) + "</div>";
            html += "<div class=\"credit-block\"><span class=\"credit-label\">Language</span>" + escapeHtml(language) + "</div>";
            html += "</div>";
            html += "</div>";
            html += "</article>";
        }

        html += "</div>";
        watchlistGrid.innerHTML = html;
        bindPosterFallbacks();
    }

    function renderCollections() {
        collectionsGrid.innerHTML = "<div class=\"skeleton-grid\">" + Array.from({ length: 6 }, function () {
            return "<article class=\"skeleton-card collection-skeleton\" aria-hidden=\"true\"><div class=\"skeleton-body\"><div class=\"skeleton-line skeleton-line--title\"></div><div class=\"skeleton-line skeleton-line--short\"></div><div class=\"skeleton-line skeleton-line--medium\"></div></div></article>";
        }).join("") + "</div>";

        fetch("/collections")
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (!data.success || !Array.isArray(data.collections)) {
                    collectionsGrid.innerHTML = "<div class=\"empty-inline\">Collections are taking a quiet moment. Please try again soon.</div>";
                    return;
                }

                const featured = data.collections.filter(function (item) {
                    return FEATURED_COLLECTIONS.indexOf(item.slug) >= 0;
                });

                const requests = featured.map(function (item) {
                    return fetch("/collections/" + item.slug)
                        .then(function (response) {
                            return response.json();
                        })
                        .then(function (collectionData) {
                            return {
                                slug: item.slug,
                                title: item.title,
                                collectionData: collectionData,
                            };
                        });
                });

                Promise.all(requests)
                    .then(function (results) {
                        let html = "";

                        for (let i = 0; i < results.length; i++) {
                            const item = results[i];
                            const movies = item.collectionData && item.collectionData.movies ? item.collectionData.movies : [];
                            const previewMovies = movies.slice(0, 4);

                            html += "<article class=\"collection-card\">";
                            html += "<div class=\"collection-card__head\">";
                            html += "<h3 class=\"collection-title\">" + escapeHtml(item.title) + "</h3>";
                            html += "<span class=\"collection-count\">" + previewMovies.length + " picks</span>";
                            html += "</div>";
                            html += "<ul class=\"collection-list\">";

                            if (!previewMovies.length) {
                                html += "<li class=\"collection-list-item\">A few more stories are on the way.</li>";
                            } else {
                                for (let j = 0; j < previewMovies.length; j++) {
                                    const movie = previewMovies[j];
                                    html += "<li class=\"collection-list-item\">" + escapeHtml(movie.title) + " <span class=\"collection-year\">" + escapeHtml(movie.year || "") + "</span></li>";
                                }
                            }

                            html += "</ul>";
                            html += "</article>";
                        }

                        collectionsGrid.innerHTML = html;
                    })
                    .catch(function () {
                        collectionsGrid.innerHTML = "<div class=\"empty-inline\">Collections are taking a quiet moment. Please try again soon.</div>";
                    });
            })
            .catch(function () {
                collectionsGrid.innerHTML = "<div class=\"empty-inline\">Collections are taking a quiet moment. Please try again soon.</div>";
            });
    }

    function displayResults(data) {
        if (!data.success) {
            showErrorCard("We could not find that story.", data.message || "Please try a different mood, title, or genre.");
            return;
        }

        if (!data.recommendations || !data.recommendations.length) {
            showEmptyState("No stories surfaced yet.", "The garden cinema could not find a match for that request. Try another title, mood, or occasion.");
            return;
        }

        let html =
            "<div class=\"results-header\">" +
            "<p class=\"section-eyebrow\">Picked especially for you</p>" +
            "<h2 class=\"section-title\">Because you loved " +
            escapeHtml(data.movie || searchInput.value.trim()) +
            "</h2>" +
            "<p class=\"section-note\">A small bouquet of films with a familiar kind of magic.</p>" +
            "</div>";

        html += "<div class=\"cards-container\">";

        for (let i = 0; i < data.recommendations.length; i++) {
            const movie = data.recommendations[i];
            const posterUrl = getPosterUrl(movie.poster);
            const title = cleanValue(movie.title, "Untitled film");
            const year = cleanValue(movie.year, "");
            const rating = cleanValue(movie.rating, "Not rated");
            const runtime = cleanValue(movie.runtime, "Runtime unknown");
            const plot = cleanValue(movie.plot, "A little mystery still surrounds this one.");
            const director = cleanValue(movie.director, "A storyteller");
            const language = cleanValue(movie.language, "A language of cinema");
            const saved = isMovieSaved(movie);
            const reason = cleanValue(movie.recommendation_reason, "This recommendation fits your current mood.");

            html += "<article class=\"movie-card\">";
            html += "<div class=\"poster-wrapper\">";
            html += "<img class=\"movie-poster\" src=\"" + escapeHtml(posterUrl) + "\" alt=\"Poster for " + escapeHtml(title) + "\" loading=\"lazy\">";
            html += "</div>";

            html += "<div class=\"movie-details\">";
            html += "<div class=\"card-topline\">";
            html += "<h3 class=\"card-title\">" + escapeHtml(title) + "</h3>";
            html += "<button type=\"button\" class=\"card-action-btn card-action-btn--watchlist\" data-action=\"toggle-watchlist\" data-title=\"" + escapeHtml(title) + "\" aria-pressed=\"" + (saved ? "true" : "false") + "\">" + (saved ? "✓ Saved" : "♡ Save") + "</button>";
            html += "</div>";
            html += "<div class=\"card-meta\">";

            if (year) {
                html += "<span class=\"meta-badge\">" + escapeHtml(year) + "</span>";
            }

            html += "<span class=\"rating-badge\" aria-label=\"IMDb rating\">&#9733; " + escapeHtml(rating) + "</span>";
            html += "<span class=\"meta-badge\">" + escapeHtml(runtime) + "</span>";
            html += "<span class=\"similarity-badge\">" + formatMatchScore(movie.similarity_score) + "</span>";
            html += "</div>";

            html += buildGenrePills(movie.genre);
            html += "<p class=\"reason-line\">✨ Why this recommendation? " + escapeHtml(reason) + "</p>";
            html += "<p class=\"card-plot\">" + escapeHtml(plot) + "</p>";
            html += "<div class=\"card-credits\">";
            html += "<div class=\"credit-block\"><span class=\"credit-label\">Director</span>" + escapeHtml(director) + "</div>";
            html += "<div class=\"credit-block\"><span class=\"credit-label\">Language</span>" + escapeHtml(language) + "</div>";
            html += "</div>";

            if (movie.omdb_message) {
                html += "<p class=\"warning-note\">" + escapeHtml(movie.omdb_message) + "</p>";
            }

            html += "<div class=\"chat-card\">";
            html += "<button type=\"button\" class=\"card-action-btn card-action-btn--chat\" data-action=\"toggle-chat\" data-title=\"" + escapeHtml(title) + "\">Ask CineMate</button>";
            html += "<div class=\"chat-panel is-hidden\">";
            html += "<p class=\"chat-panel-title\">Try one of these</p>";
            html += "<div class=\"chat-question-list\">";
            html += "<button type=\"button\" class=\"example-question\" data-question=\"Is it scary?\">Is it scary?</button>";
            html += "<button type=\"button\" class=\"example-question\" data-question=\"Family friendly?\">Family friendly?</button>";
            html += "<button type=\"button\" class=\"example-question\" data-question=\"Worth watching?\">Worth watching?</button>";
            html += "<button type=\"button\" class=\"example-question\" data-question=\"Runtime?\">Runtime?</button>";
            html += "<button type=\"button\" class=\"example-question\" data-question=\"Happy ending?\">Happy ending?</button>";
            html += "</div>";
            html += "<div class=\"chat-response\">Ask a question to get a quick, spoiler-free answer.</div>";
            html += "</div>";
            html += "</div>";
            html += "</article>";
        }

        html += "</div>";

        if (data.ai_explanation) {
            html += buildCompanionSection(data.ai_explanation);
        }

        resultsSection.innerHTML = html;
        bindPosterFallbacks();
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function buildCompanionSection(explanation) {
        return (
            "<section class=\"companion-section\" aria-label=\"Why you'll love these movies\">" +
            "<p class=\"section-eyebrow\">A little note for your watchlist</p>" +
            "<h2 class=\"companion-title\">&#10024; Why You'll Love These</h2>" +
            "<p class=\"companion-text\">" + escapeHtml(explanation) + "</p>" +
            "</section>"
        );
    }

    function handleResultsCardClick(event) {
        const button = event.target.closest("button");

        if (!button) {
            return;
        }

        const action = button.getAttribute("data-action");
        const title = button.getAttribute("data-title");

        if (action === "toggle-watchlist") {
            const card = button.closest(".movie-card");
            const movie = buildMovieFromCard(card, title);

            if (button.getAttribute("aria-pressed") === "true") {
                removeMovie(movie);
                button.setAttribute("aria-pressed", "false");
                button.textContent = "♡ Save";
            } else {
                saveMovie(movie);
                button.setAttribute("aria-pressed", "true");
                button.textContent = "✓ Saved";
            }
            return;
        }

        if (action === "toggle-chat") {
            const panel = button.nextElementSibling;
            if (panel && panel.classList.contains("chat-panel")) {
                panel.classList.toggle("is-hidden");
            }
            return;
        }

        if (button.classList.contains("example-question")) {
            const card = button.closest(".movie-card");
            const movie = buildMovieFromCard(card, title);
            askMovieQuestion(card, movie, button.getAttribute("data-question"));
        }
    }

    function handleWatchlistCardClick(event) {
        const button = event.target.closest("button");

        if (!button) {
            return;
        }

        if (button.getAttribute("data-action") === "remove-watchlist") {
            removeMovie({ title: button.getAttribute("data-title") });
        }
    }

    function handleRecentClick(event) {
        const button = event.target.closest("button[data-query]");

        if (button) {
            runSearch(button.getAttribute("data-query"));
        }
    }

    function buildMovieFromCard(card, fallbackTitle) {
        if (!card) {
            return { title: fallbackTitle || "" };
        }

        const poster = card.querySelector(".movie-poster");
        const titleEl = card.querySelector(".card-title");
        const metaBadges = card.querySelectorAll(".meta-badge");
        const rating = card.querySelector(".rating-badge");
        const plot = card.querySelector(".card-plot");
        const credits = card.querySelectorAll(".credit-block");
        const genrePills = card.querySelectorAll(".genre-pill");

        return {
            title: titleEl ? titleEl.textContent.trim() : fallbackTitle || "",
            year: metaBadges[0] ? metaBadges[0].textContent.trim() : "",
            poster: poster ? poster.getAttribute("src") : "",
            rating: rating ? rating.textContent.replace("★", "").trim() : "",
            runtime: metaBadges[1] ? metaBadges[1].textContent.trim() : "",
            genre: Array.from(genrePills).map(function (pill) {
                return pill.textContent.trim();
            }).join(", "),
            plot: plot ? plot.textContent.trim() : "",
            director: credits[0] ? credits[0].textContent.replace("Director", "").trim() : "",
            language: credits[1] ? credits[1].textContent.replace("Language", "").trim() : "",
        };
    }

    function askMovieQuestion(card, movie, question) {
        const responseBox = card.querySelector(".chat-response");

        if (!responseBox) {
            return;
        }

        responseBox.innerHTML = "<span class=\"chat-loading\">CineMate is thinking...</span>";

        fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: question,
                movie: {
                    title: movie.title,
                    genre: movie.genre,
                    runtime: movie.runtime,
                    plot: movie.plot,
                },
            }),
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success) {
                    responseBox.innerHTML = "<p class=\"chat-answer\">" + escapeHtml(data.answer) + "</p>";
                } else {
                    responseBox.innerHTML = "<p class=\"chat-answer chat-answer--error\">" + escapeHtml(data.message || "The companion is offline right now.") + "</p>";
                }
            })
            .catch(function () {
                responseBox.innerHTML = "<p class=\"chat-answer chat-answer--error\">The chat companion could not respond. Please try again in a moment.</p>";
            });
    }
});
