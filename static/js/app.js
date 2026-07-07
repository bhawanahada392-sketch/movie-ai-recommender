const PLACEHOLDER_POSTER = "/static/images/no-poster.svg";
const STORAGE_KEYS = {
    watchlist: "cinemate-watchlist",
    recentSearches: "cinemate-recent-searches",
    viewedMovies: "cinemate-viewed-movies",
};

let watchlistItems = [];
let recentSearches = [];
let viewedMovies = [];

function readStorage(key) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : [];
    } catch (error) {
        console.warn("Local storage unavailable:", error);
        return [];
    }
}

function writeStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.warn("Could not save local storage:", error);
    }
}

function escapeHtml(text) {
    if (!text) {
        return "";
    }

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;");
}

function cleanValue(value, fallback) {
    if (!value || value === "N/A") {
        return fallback || "Not Available";
    }

    return value;
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
    posters.forEach(function (poster) {
        poster.addEventListener("error", function () {
            usePosterFallback(poster);
        });
    });
}

function buildGenrePills(genreString) {
    if (!genreString || genreString === "N/A") {
        return "";
    }

    const genres = String(genreString).split(",");
    let html = '<div class="genre-list" aria-label="Genres">';
    genres.forEach(function (genre) {
        const cleanGenre = genre.trim();
        if (cleanGenre) {
            html += '<span class="genre-pill">' + escapeHtml(cleanGenre) + "</span>";
        }
    });
    html += "</div>";
    return html;
}

function formatMatchScore(score) {
    const numericScore = Number(score);
    if (!Number.isNaN(numericScore) && numericScore <= 1) {
        return Math.round(numericScore * 100) + "% match";
    }
    return escapeHtml(String(score)) + " match";
}

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
    viewedMovies = readStorage(STORAGE_KEYS.viewedMovies);
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
    renderHistory();
}

function addViewedMovie(movie) {
    const title = String(movie && movie.title ? movie.title : "").trim();
    if (!title) {
        return;
    }
    viewedMovies = viewedMovies.filter(function (item) {
        return item.title !== title;
    });
    viewedMovies.unshift({
        title: title,
        year: movie.year || "",
        poster: movie.poster || "",
    });
    viewedMovies = viewedMovies.slice(0, 6);
    writeStorage(STORAGE_KEYS.viewedMovies, viewedMovies);
    renderHistory();
}

function removeViewedMovie(index) {
    const itemIndex = Number(index);
    if (!Number.isInteger(itemIndex) || itemIndex < 0 || itemIndex >= viewedMovies.length) {
        return;
    }

    viewedMovies.splice(itemIndex, 1);
    writeStorage(STORAGE_KEYS.viewedMovies, viewedMovies);
    renderHistory();
}

function isMovieSaved(movie) {
    const key = getMovieKey(movie);
    return watchlistItems.some(function (item) {
        return getMovieKey(item) === key;
    });
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

function saveMovie(movie) {
    const key = getMovieKey(movie);
    if (!key) {
        return;
    }
    const exists = watchlistItems.some(function (item) {
        return getMovieKey(item) === key;
    });
    if (!exists) {
        watchlistItems.unshift(movie);
        writeStorage(STORAGE_KEYS.watchlist, watchlistItems);
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
    renderWatchlist();
}

function clearWatchlist() {
    watchlistItems = [];
    writeStorage(STORAGE_KEYS.watchlist, watchlistItems);
    renderWatchlist();
}

function renderWatchlist() {
    const grid = document.getElementById("watchlist-grid");
    if (!grid) {
        return;
    }

    const query = document.getElementById("watchlist-search")?.value.trim().toLowerCase() || "";
    const filteredItems = watchlistItems.filter(function (movie) {
        if (!query) {
            return true;
        }
        const haystack = [movie.title, movie.year, movie.genre, movie.director, movie.plot].filter(Boolean).join(" ").toLowerCase();
        return haystack.includes(query);
    });

    if (!filteredItems.length) {
        grid.innerHTML = '<div class="empty-inline">Your watchlist is still quiet. Save a few favorites and they will appear here.</div>';
        return;
    }

    let html = "";
    filteredItems.forEach(function (movie) {
        const posterUrl = getPosterUrl(movie.poster);
        const title = cleanValue(movie.title, "Not Available");
        const year = cleanValue(movie.year, "Not Available");
        const rating = cleanValue(movie.rating, "Not Available");
        const runtime = cleanValue(movie.runtime, "Not Available");
        const plot = cleanValue(movie.plot, "Not Available");
        const director = cleanValue(movie.director, "Not Available");
        const language = cleanValue(movie.language, "Not Available");

        html += '<article class="movie-card">';
        html += '<div class="poster-wrapper"><img class="movie-poster" src="' + escapeHtml(posterUrl) + '" alt="Poster for ' + escapeHtml(title) + '" loading="lazy"></div>';
        html += '<div class="movie-details">';
        html += '<div class="card-topline"><h3 class="card-title">' + escapeHtml(title) + '</h3><button type="button" class="card-action-btn card-action-btn--watchlist is-active" data-action="remove-watchlist" data-title="' + escapeHtml(title) + '">Remove</button></div>';
        html += '<div class="card-meta">';
        if (year) {
            html += '<span class="meta-badge">' + escapeHtml(year) + '</span>';
        }
        html += '<span class="rating-badge">★ ' + escapeHtml(rating) + '</span><span class="meta-badge">' + escapeHtml(runtime) + '</span></div>';
        html += buildGenrePills(movie.genre);
        html += '<p class="card-plot">' + escapeHtml(plot) + '</p>';
        html += '<div class="card-credits"><div class="credit-block"><span class="credit-label">Director</span>' + escapeHtml(director) + '</div><div class="credit-block"><span class="credit-label">Language</span>' + escapeHtml(language) + '</div></div>';
        html += '</div></article>';
    });

    grid.innerHTML = '<div class="cards-container">' + html + '</div>';
    bindPosterFallbacks();
}

function renderHistory() {
    const recentList = document.getElementById("recent-searches-list");
    const viewedList = document.getElementById("viewed-movies-list");

    if (recentList) {
        if (!recentSearches.length) {
            recentList.innerHTML = '<div class="empty-inline">No recent searches yet.</div>';
        } else {
            recentList.innerHTML = '<ul class="history-list-items">' + recentSearches.map(function (item) {
                return '<li class="history-item"><span>' + escapeHtml(item) + '</span><span class="history-pill">Saved</span></li>';
            }).join("") + '</ul>';
        }
    }

    if (viewedList) {
        if (!viewedMovies.length) {
            viewedList.innerHTML = '<div class="empty-inline">No viewed films recorded yet.</div>';
        } else {
            viewedList.innerHTML = '<ul class="history-list-items">' + viewedMovies.map(function (item, index) {
                return '<li class="history-item"><span>' + escapeHtml(item.title) + '</span><span class="history-item-actions"><span class="history-pill">' + escapeHtml(item.year || "Recent") + '</span><button type="button" class="history-delete-btn" data-action="remove-viewed" data-index="' + index + '" aria-label="Remove ' + escapeHtml(item.title) + ' from recently viewed">&times;</button></span></li>';
            }).join("") + '</ul>';
        }
    }
}

function renderCollections() {
    const grid = document.getElementById("collections-grid");
    if (!grid) {
        return;
    }

    grid.innerHTML = '<div class="skeleton-grid">' + Array.from({ length: 6 }, function () {
        return '<article class="skeleton-card collection-skeleton" aria-hidden="true"><div class="skeleton-body"><div class="skeleton-line skeleton-line--title"></div><div class="skeleton-line skeleton-line--short"></div><div class="skeleton-line skeleton-line--medium"></div></div></article>';
    }).join("") + '</div>';

    fetch("/collections")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (!data.success || !Array.isArray(data.collections)) {
                grid.innerHTML = '<div class="empty-inline">Collections are taking a quiet moment. Please try again soon.</div>';
                return;
            }

            const featured = data.collections.filter(function (item) {
                return ["family-night", "girls-night", "space-adventure", "rainy-day", "feel-good", "mind-bending"].includes(item.slug);
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

            Promise.all(requests).then(function (results) {
                let html = "";
                results.forEach(function (item) {
                    const movies = item.collectionData && item.collectionData.movies ? item.collectionData.movies : [];
                    const previewMovies = movies.slice(0, 4);
                    html += '<article class="collection-card">';
                    html += '<div class="collection-card__head"><h3 class="collection-title">' + escapeHtml(item.title) + '</h3><span class="collection-count">' + previewMovies.length + ' picks</span></div>';
                    html += '<ul class="collection-list">';
                    if (!previewMovies.length) {
                        html += '<li class="collection-list-item">A few more stories are on the way.</li>';
                    } else {
                        previewMovies.forEach(function (movie) {
                            html += '<li class="collection-list-item">' + escapeHtml(movie.title) + ' <span class="collection-year">' + escapeHtml(movie.year || "") + '</span></li>';
                        });
                    }
                    html += '</ul></article>';
                });
                grid.innerHTML = html;
            }).catch(function () {
                grid.innerHTML = '<div class="empty-inline">Collections are taking a quiet moment. Please try again soon.</div>';
            });
        })
        .catch(function () {
            grid.innerHTML = '<div class="empty-inline">Collections are taking a quiet moment. Please try again soon.</div>';
        });
}

function showResultsLoading() {
    const stage = document.getElementById("results-stage");
    if (!stage) {
        return;
    }
    stage.innerHTML = '<div class="skeleton-wrap"><div class="skeleton-grid">' + Array.from({ length: 6 }, function () {
        return '<article class="skeleton-card" aria-hidden="true"><div class="skeleton-poster"></div><div class="skeleton-body"><div class="skeleton-line skeleton-line--title"></div><div class="skeleton-line skeleton-line--short"></div><div class="skeleton-line skeleton-line--medium"></div><div class="skeleton-line skeleton-line--long"></div></div></article>';
    }).join("") + '</div><p class="skeleton-message">Finding something wonderful for you...</p></div>';
    stage.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderAiPicksSection(aiPicks) {
    if (!Array.isArray(aiPicks) || !aiPicks.length) {
        return "";
    }

    let html = '<section class="companion-section ai-picks-section"><p class="section-eyebrow">✨ AI Picks</p><h2 class="companion-title">A few more stories that fit the mood</h2><div class="cards-container">';

    aiPicks.forEach(function (movie) {
        const posterUrl = getPosterUrl(movie.poster);
        const title = cleanValue(movie.title, "Not Available");
        const year = cleanValue(movie.year, "Not Available");
        const rating = cleanValue(movie.rating, "Not Available");
        const runtime = cleanValue(movie.runtime, "Not Available");
        const plot = cleanValue(movie.plot, "Not Available");
        const director = cleanValue(movie.director, "Not Available");
        const language = cleanValue(movie.language, "Not Available");
        const saved = isMovieSaved(movie);

        html += '<article class="movie-card ai-pick-card">';
        html += '<div class="poster-wrapper"><img class="movie-poster" src="' + escapeHtml(posterUrl) + '" alt="Poster for ' + escapeHtml(title) + '" loading="lazy"></div>';
        html += '<div class="movie-details">';
        html += '<div class="card-topline"><h3 class="card-title">' + escapeHtml(title) + '</h3><button type="button" class="card-action-btn card-action-btn--watchlist' + (saved ? ' is-active' : '') + '" data-action="toggle-watchlist" data-title="' + escapeHtml(title) + '" aria-pressed="' + (saved ? 'true' : 'false') + '">' + (saved ? '✓ Saved' : '♡ Save') + '</button></div>';
        html += '<div class="card-meta">';
        if (year) {
            html += '<span class="meta-badge">' + escapeHtml(year) + '</span>';
        }
        html += '<span class="rating-badge">★ ' + escapeHtml(rating) + '</span><span class="meta-badge">' + escapeHtml(runtime) + '</span></div>';
        html += buildGenrePills(movie.genre);
        html += '<p class="card-plot">' + escapeHtml(plot) + '</p>';
        html += '<div class="card-credits"><div class="credit-block"><span class="credit-label">Director</span>' + escapeHtml(director) + '</div><div class="credit-block"><span class="credit-label">Language</span>' + escapeHtml(language) + '</div></div>';
        html += '</div></article>';
    });

    html += '</div></section>';
    return html;
}

function showResults(data) {
    const stage = document.getElementById("results-stage");
    if (!stage) {
        return;
    }

    if (!data.success) {
        stage.innerHTML = '<div class="error-card" role="alert"><svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3 2.8 19.5h18.4L12 3Z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg><h2 class="error-title">We could not find that story.</h2><p class="error-text">' + escapeHtml(data.message || "Please try a different mood, title, or genre.") + '</p></div>';
        stage.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
    }

    if (!data.recommendations || !data.recommendations.length) {
        stage.innerHTML = '<div class="empty-state"><div class="empty-illustration" aria-hidden="true"><svg viewBox="0 0 240 170" xmlns="http://www.w3.org/2000/svg"><path class="empty-ground" d="M20 136 C54 114 90 120 120 132 C154 148 190 142 220 124 V156 H20Z"/><path class="empty-screen" d="M66 34 H174 Q184 34 184 44 V104 Q184 114 174 114 H66 Q56 114 56 104 V44 Q56 34 66 34Z"/><path class="empty-curtain-left" d="M66 34 C82 52 78 92 62 114 H66 Q56 114 56 104 V44 Q56 34 66 34Z"/><path class="empty-curtain-right" d="M174 34 C158 52 162 92 178 114 H174 Q184 114 184 104 V44 Q184 34 174 34Z"/><path class="empty-branch" d="M52 126 C72 96 88 82 112 72" fill="none"/><path class="empty-branch" d="M188 126 C170 98 152 82 128 72" fill="none"/><ellipse class="empty-leaf" cx="92" cy="84" rx="8" ry="16"/><ellipse class="empty-leaf" cx="150" cy="84" rx="8" ry="16"/><circle class="empty-star" cx="112" cy="60" r="3"/><circle class="empty-star" cx="132" cy="56" r="2"/></svg></div><h2 class="empty-title">No stories surfaced yet.</h2><p class="empty-message">The garden cinema could not find a match for that request. Try another title, mood, or occasion.</p></div>';
        stage.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
    }

    const query = document.getElementById("results-search")?.value || "";
    addRecentSearch(query || data.movie || "");
    addViewedMovie({ title: data.movie || "", year: "", poster: "" });

    let html = '<div class="results-header"><p class="section-eyebrow">Picked especially for you</p><h2 class="section-title">Because you searched ' + escapeHtml(data.movie || query || "this title") + '</h2><p class="section-note">A small bouquet of films with a familiar kind of magic.</p></div>';

    html += '<div class="cards-container">';
    data.recommendations.forEach(function (movie) {
        const posterUrl = getPosterUrl(movie.poster);
        const title = cleanValue(movie.title, "Not Available");
        const year = cleanValue(movie.year, "Not Available");
        const rating = cleanValue(movie.rating, "Not Available");
        const runtime = cleanValue(movie.runtime, "Not Available");
        const plot = cleanValue(movie.plot, "Not Available");
        const director = cleanValue(movie.director, "Not Available");
        const language = cleanValue(movie.language, "Not Available");
        const saved = isMovieSaved(movie);

        html += '<article class="movie-card">';
        html += '<div class="poster-wrapper"><img class="movie-poster" src="' + escapeHtml(posterUrl) + '" alt="Poster for ' + escapeHtml(title) + '" loading="lazy"></div>';
        html += '<div class="movie-details">';
        html += '<div class="card-topline"><h3 class="card-title">' + escapeHtml(title) + '</h3><button type="button" class="card-action-btn card-action-btn--watchlist' + (saved ? ' is-active' : '') + '" data-action="toggle-watchlist" data-title="' + escapeHtml(title) + '" aria-pressed="' + (saved ? 'true' : 'false') + '">' + (saved ? '✓ Saved' : '♡ Save') + '</button></div>';
        html += '<div class="card-meta">';
        if (year) {
            html += '<span class="meta-badge">' + escapeHtml(year) + '</span>';
        }
        html += '<span class="rating-badge">★ ' + escapeHtml(rating) + '</span><span class="meta-badge">' + escapeHtml(runtime) + '</span><span class="similarity-badge">' + formatMatchScore(movie.similarity_score) + '</span></div>';
        html += buildGenrePills(movie.genre);
        html += '<p class="card-plot">' + escapeHtml(plot) + '</p>';
        html += '<div class="card-credits"><div class="credit-block"><span class="credit-label">Director</span>' + escapeHtml(director) + '</div><div class="credit-block"><span class="credit-label">Language</span>' + escapeHtml(language) + '</div></div>';
        html += '</div></article>';
    });

    html += '</div>';

    if (data.ai_explanation) {
        html += '<div class="companion-section companion-section--after-grid"><p class="section-eyebrow">A little note for your watchlist</p><h2 class="companion-title">Why these feel right</h2><p class="companion-text">' + escapeHtml(data.ai_explanation) + '</p></div>';
    }

    if (Array.isArray(data.ai_picks) && data.ai_picks.length) {
        html += renderAiPicksSection(data.ai_picks);
    }

    stage.innerHTML = html;
    bindPosterFallbacks();
    stage.scrollIntoView({ behavior: "smooth", block: "start" });
}

function loadResults(query) {
    const cleanQuery = String(query || "").trim();
    if (!cleanQuery) {
        showResults({ success: false, message: "Please enter a movie name." });
        return;
    }
    showResultsLoading();
    fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ movie: cleanQuery }),
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            showResults(data);
        })
        .catch(function () {
            showResults({ success: false, message: "Something interrupted the search. Please try again in a moment." });
        });
}

function handleResultsClick(event) {
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

function initHomePage() {
    const form = document.getElementById("search-form");
    const input = document.getElementById("movie-search");
    if (!form || !input) {
        return;
    }
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const query = input.value.trim();
        if (!query) {
            return;
        }
        window.location.href = "/results?q=" + encodeURIComponent(query);
    });
}

function initResultsPage() {
    const form = document.querySelector(".search-form--compact");
    const input = document.getElementById("results-search");
    const stage = document.getElementById("results-stage");
    if (!form || !input || !stage) {
        return;
    }

    const queryParam = new URLSearchParams(window.location.search).get("q") || "";
    input.value = queryParam;
    stage.addEventListener("click", handleResultsClick);
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        loadResults(input.value);
    });
    loadResults(queryParam);
}

function initWatchlistPage() {
    const searchInput = document.getElementById("watchlist-search");
    const clearBtn = document.getElementById("clear-watchlist-btn");
    if (searchInput) {
        searchInput.addEventListener("input", renderWatchlist);
    }
    if (clearBtn) {
        clearBtn.addEventListener("click", clearWatchlist);
    }
    const grid = document.getElementById("watchlist-grid");
    if (grid) {
        grid.addEventListener("click", function (event) {
            const button = event.target.closest("button");
            if (!button) {
                return;
            }
            if (button.getAttribute("data-action") === "remove-watchlist") {
                removeMovie({ title: button.getAttribute("data-title") });
            }
        });
    }
    renderWatchlist();
}

function initHistoryPage() {
    const clearHistoryBtn = document.getElementById("clear-history-btn");
    const viewedList = document.getElementById("viewed-movies-list");
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener("click", function () {
            recentSearches = [];
            viewedMovies = [];
            writeStorage(STORAGE_KEYS.recentSearches, recentSearches);
            writeStorage(STORAGE_KEYS.viewedMovies, viewedMovies);
            renderHistory();
        });
    }
    if (viewedList) {
        viewedList.addEventListener("click", function (event) {
            const button = event.target.closest("button");
            if (!button || button.getAttribute("data-action") !== "remove-viewed") {
                return;
            }
            removeViewedMovie(button.getAttribute("data-index"));
        });
    }
    renderHistory();
}

function initCollectionsPage() {
    renderCollections();
}

function initAiCompanionPage() {
    const chatForm = document.getElementById("chat-form");
    const chatLog = document.getElementById("chat-log");
    const questionInput = document.getElementById("ai-question");
    const clearChatButton = document.getElementById("clear-chat-btn");
    const promptButtons = document.querySelectorAll(".prompt-chip");
    const submitButton = chatForm?.querySelector("button[type='submit']");
    const STORAGE_KEY = "cinemate-chat-history";
    const FALLBACK_MESSAGE = "I'm having trouble connecting right now. Please try again.";

    if (!chatForm || !chatLog || !questionInput) {
        return;
    }

    function readHistory() {
        try {
            const value = window.sessionStorage.getItem(STORAGE_KEY);
            return value ? JSON.parse(value) : [];
        } catch (error) {
            console.warn("Chat history unavailable:", error);
            return [];
        }
    }

    function writeHistory(messages) {
        try {
            window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
        } catch (error) {
            console.warn("Could not save chat history:", error);
        }
    }

    let history = readHistory();

    function renderHistory() {
        chatLog.innerHTML = "";
        history.forEach(function (entry) {
            appendMessage(entry.text, entry.role, false);
        });
    }

    function appendMessage(text, role, persist) {
        const entry = document.createElement("div");
        entry.className = role === "user" ? "chat-bubble chat-bubble--user" : "chat-bubble chat-bubble--assistant";
        entry.textContent = text;
        chatLog.appendChild(entry);
        chatLog.scrollTop = chatLog.scrollHeight;

        if (persist !== false) {
            history.push({ role: role, text: text });
            writeHistory(history);
        }
    }

    function setBusy(isBusy) {
        questionInput.disabled = isBusy;
        if (submitButton) {
            submitButton.disabled = isBusy;
            submitButton.textContent = isBusy ? "Thinking…" : "Send";
        }
    }

    function askQuestion(question) {
        appendMessage(question, "user", true);
        setBusy(true);

        const thinking = document.createElement("div");
        thinking.className = "chat-bubble chat-bubble--assistant chat-bubble--typing";
        thinking.textContent = "CineMate is thinking…";
        chatLog.appendChild(thinking);
        chatLog.scrollTop = chatLog.scrollHeight;

        const controller = new AbortController();
        const timeoutHandle = window.setTimeout(function () {
            controller.abort();
        }, 20000);

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question }),
            signal: controller.signal,
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                window.clearTimeout(timeoutHandle);
                chatLog.removeChild(thinking);
                if (data.success) {
                    appendMessage(data.answer, "assistant", true);
                } else {
                    appendMessage(data.message || FALLBACK_MESSAGE, "assistant", true);
                }
            })
            .catch(function (error) {
                window.clearTimeout(timeoutHandle);
                chatLog.removeChild(thinking);
                const message = error.name === "AbortError"
                    ? FALLBACK_MESSAGE
                    : FALLBACK_MESSAGE;
                appendMessage(message, "assistant", true);
            })
            .finally(function () {
                setBusy(false);
            });
    }

    chatForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const question = questionInput.value.trim();
        if (!question) {
            return;
        }
        askQuestion(question);
        questionInput.value = "";
    });

    promptButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const prompt = button.getAttribute("data-prompt");
            if (prompt) {
                questionInput.value = prompt;
                questionInput.focus();
            }
        });
    });

    if (!history.length) {
        history = [{ role: "assistant", text: "Hello. Tell me your mood and I will help you find a film." }];
        writeHistory(history);
    }

    renderHistory();

    if (clearChatButton) {
        clearChatButton.addEventListener("click", function () {
            history = [];
            try {
                window.sessionStorage.removeItem(STORAGE_KEY);
            } catch (error) {
                writeHistory(history);
            }
            chatLog.innerHTML = "";
            questionInput.value = "";
            questionInput.focus();
        });
    }
}

function initNav() {
    const toggle = document.getElementById("nav-toggle");
    const nav = document.getElementById("site-nav");
    if (!toggle || !nav) {
        return;
    }
    toggle.addEventListener("click", function () {
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        nav.classList.toggle("is-open");
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setTimeOfDayTheme();
    initializeState();
    initNav();

    const page = document.body.getAttribute("data-page");
    if (page === "results") {
        initResultsPage();
    } else if (page === "watchlist") {
        initWatchlistPage();
    } else if (page === "history") {
        initHistoryPage();
    } else if (page === "collections") {
        initCollectionsPage();
    } else if (page === "ai-companion") {
        initAiCompanionPage();
    } else {
        initHomePage();
    }
});
