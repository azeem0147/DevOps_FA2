const API_BASE_URL = "/api-proxy";

let events = [];

const getElement = (selector) => {
    return document.querySelector(selector);
};

const getElements = (selector) => {
    return Array.from(
        document.querySelectorAll(selector)
    );
};


function escapeHtml(value = "") {
    return String(value).replace(
        /[&<>"']/g,
        (character) => {
            const values = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                "\"": "&quot;",
                "'": "&#39;"
            };

            return values[character];
        }
    );
}


function showToast(message, type = "success") {
    const toast = getElement("#toast");

    toast.textContent = message;
    toast.className = `toast show ${type}`;

    clearTimeout(showToast.timer);

    showToast.timer = setTimeout(() => {
        toast.className = "toast";
    }, 3500);
}


async function apiRequest(path, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${path}`,
        {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        }
    );

    if (response.status === 204) {
        return null;
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error || "Request failed."
        );
    }

    return data;
}


function formatDate(dateValue) {
    return new Intl.DateTimeFormat(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    ).format(
        new Date(`${dateValue}T00:00:00`)
    );
}


function switchPage(pageName) {
    getElements(".page").forEach((page) => {
        page.classList.toggle(
            "active",
            page.id === `${pageName}-page`
        );
    });

    getElements(".nav-button").forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.page === pageName
        );
    });
}


async function loadSystemInformation() {
    try {
        const information = await apiRequest(
            "/api/info"
        );

        const health = await apiRequest(
            "/health"
        );

        getElement(
            "#environmentBadge"
        ).textContent = (
            `${information.environment} Environment`
        );

        getElement(
            "#healthBadge"
        ).textContent = "Backend Healthy";

        const systemValues = [
            [
                "Application",
                information.application
            ],
            [
                "Environment",
                information.environment
            ],
            [
                "Version",
                information.version
            ],
            [
                "Log Level",
                information.log_level
            ],
            [
                "Deployment",
                information.deployment
            ],
            [
                "Backend",
                health.status
            ],
            [
                "Database",
                health.database
            ],
            [
                "Service",
                health.service
            ]
        ];

        getElement(
            "#systemInformation"
        ).innerHTML = systemValues.map(
            ([label, value]) => {
                return `
                    <div class="system-card">
                        <span>
                            ${escapeHtml(label)}
                        </span>

                        <strong>
                            ${escapeHtml(value)}
                        </strong>
                    </div>
                `;
            }
        ).join("");

    } catch (error) {
        getElement(
            "#healthBadge"
        ).textContent = "Backend Unavailable";

        showToast(
            error.message,
            "error"
        );
    }
}


async function loadEvents() {
    const parameters = new URLSearchParams();

    const search = getElement(
        "#searchInput"
    ).value.trim();

    const category = getElement(
        "#categoryFilter"
    ).value;

    const status = getElement(
        "#statusFilter"
    ).value;

    if (search) {
        parameters.set(
            "search",
            search
        );
    }

    if (category) {
        parameters.set(
            "category",
            category
        );
    }

    if (status) {
        parameters.set(
            "status",
            status
        );
    }

    try {
        events = await apiRequest(
            `/api/events?${parameters.toString()}`
        );

        renderEvents();
        renderAdminEvents();

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


function renderEvents() {
    const eventGrid = getElement(
        "#eventGrid"
    );

    const emptyMessage = getElement(
        "#emptyEvents"
    );

    getElement(
        "#eventSummary"
    ).textContent = (
        `${events.length} event`
        + `${events.length === 1 ? "" : "s"} available`
    );

    emptyMessage.classList.toggle(
        "hidden",
        events.length > 0
    );

    eventGrid.innerHTML = events.map((event) => {
        const availablePercentage = Math.max(
            0,
            Math.min(
                100,
                (
                    event.available_seats
                    / event.capacity
                ) * 100
            )
        );

        const registrationDisabled = (
            event.status !== "active"
            || event.available_seats === 0
        );

        let buttonText = "Register Now";

        if (event.available_seats === 0) {
            buttonText = "Event Full";
        } else if (event.status !== "active") {
            buttonText = "Registration Closed";
        }

        return `
            <article class="event-card">
                <div class="event-header">
                    <span class="category">
                        ${escapeHtml(event.category)}
                    </span>

                    <span
                        class="status ${escapeHtml(event.status)}"
                    >
                        ${escapeHtml(event.status)}
                    </span>
                </div>

                <h3>
                    ${escapeHtml(event.title)}
                </h3>

                <p class="event-description">
                    ${escapeHtml(event.description)}
                </p>

                <div class="event-meta">
                    <span>
                        Date: ${formatDate(event.event_date)}
                    </span>

                    <span>
                        Venue: ${escapeHtml(event.venue)}
                    </span>
                </div>

                <div class="capacity-section">
                    <strong>
                        ${event.available_seats}
                    </strong>

                    seats available out of
                    ${event.capacity}

                    <div class="progress-bar">
                        <div
                            class="progress-value"
                            style="width: ${availablePercentage}%"
                        ></div>
                    </div>
                </div>

                <button
                    class="primary-button register-button"
                    data-event-id="${event.id}"
                    ${registrationDisabled ? "disabled" : ""}
                >
                    ${buttonText}
                </button>
            </article>
        `;
    }).join("");

    getElements(
        ".register-button"
    ).forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                openRegistrationDialog(
                    Number(button.dataset.eventId)
                );
            }
        );
    });
}


function renderAdminEvents() {
    const adminEventList = getElement(
        "#adminEventList"
    );

    if (events.length === 0) {
        adminEventList.innerHTML = (
            "<p>No events available.</p>"
        );

        return;
    }

    adminEventList.innerHTML = events.map((event) => {
        return `
            <div class="admin-event">
                <div>
                    <strong>
                        ${escapeHtml(event.title)}
                    </strong>

                    <span>
                        ${formatDate(event.event_date)}
                        |
                        ${escapeHtml(event.status)}
                        |
                        ${event.registered_count}
                        /
                        ${event.capacity}
                        registered
                    </span>
                </div>

                <div>
                    <button
                        class="text-button edit-event-button"
                        data-event-id="${event.id}"
                    >
                        Edit
                    </button>

                    <button
                        class="
                            text-button
                            delete-button
                            delete-event-button
                        "
                        data-event-id="${event.id}"
                    >
                        Delete
                    </button>
                </div>
            </div>
        `;
    }).join("");

    getElements(
        ".edit-event-button"
    ).forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                editEvent(
                    Number(button.dataset.eventId)
                );
            }
        );
    });

    getElements(
        ".delete-event-button"
    ).forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                deleteEvent(
                    Number(button.dataset.eventId)
                );
            }
        );
    });
}


function openRegistrationDialog(eventId) {
    const selectedEvent = events.find(
        (event) => event.id === eventId
    );

    getElement(
        "#registrationEventId"
    ).value = eventId;

    getElement(
        "#registrationEventTitle"
    ).textContent = selectedEvent.title;

    getElement(
        "#registrationDialog"
    ).showModal();
}


async function submitRegistration(
    submitEvent
) {
    submitEvent.preventDefault();

    const eventId = getElement(
        "#registrationEventId"
    ).value;

    const registrationData = {
        student_name: getElement(
            "#studentName"
        ).value,

        roll_number: getElement(
            "#rollNumber"
        ).value,

        email: getElement(
            "#studentEmail"
        ).value
    };

    try {
        const result = await apiRequest(
            `/api/events/${eventId}/register`,
            {
                method: "POST",
                body: JSON.stringify(
                    registrationData
                )
            }
        );

        getElement(
            "#registrationDialog"
        ).close();

        getElement(
            "#registrationForm"
        ).reset();

        showToast(
            "Registration successful. "
            + `Registration ID: `
            + `${result.registration_code}`
        );

        await loadEvents();

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


async function searchRegistrations(
    submitEvent
) {
    submitEvent.preventDefault();

    const rollNumber = getElement(
        "#registrationRollSearch"
    ).value.trim();

    try {
        const registrations = await apiRequest(
            "/api/registrations"
            + `?roll_number=${encodeURIComponent(rollNumber)}`
        );

        const registrationList = getElement(
            "#registrationList"
        );

        if (registrations.length === 0) {
            registrationList.innerHTML = `
                <div class="empty-message">
                    <h3>No registrations found</h3>

                    <p>
                        No registration was found for
                        ${escapeHtml(rollNumber)}.
                    </p>
                </div>
            `;

            return;
        }

        registrationList.innerHTML = registrations.map(
            (registration) => {
                return `
                    <article class="registration-card">
                        <div>
                            <span class="category">
                                ${
                                    escapeHtml(
                                        registration.registration_code
                                    )
                                }
                            </span>

                            <h3>
                                ${
                                    escapeHtml(
                                        registration.event_title
                                    )
                                }
                            </h3>

                            <p>
                                ${
                                    formatDate(
                                        registration.event_date
                                    )
                                }
                                |
                                ${escapeHtml(registration.venue)}
                            </p>

                            <p>
                                Student:
                                ${
                                    escapeHtml(
                                        registration.student_name
                                    )
                                }
                                (
                                ${
                                    escapeHtml(
                                        registration.roll_number
                                    )
                                }
                                )
                            </p>
                        </div>

                        <div>
                            <span
                                class="
                                    status
                                    ${
                                        escapeHtml(
                                            registration.status
                                        )
                                    }
                                "
                            >
                                ${
                                    escapeHtml(
                                        registration.status
                                    )
                                }
                            </span>

                            ${
                                registration.status === "active"
                                ? `
                                    <button
                                        class="
                                            secondary-button
                                            cancel-registration-button
                                        "
                                        data-registration-code="${
                                            escapeHtml(
                                                registration.registration_code
                                            )
                                        }"
                                    >
                                        Cancel Registration
                                    </button>
                                `
                                : ""
                            }
                        </div>
                    </article>
                `;
            }
        ).join("");

        getElements(
            ".cancel-registration-button"
        ).forEach((button) => {
            button.addEventListener(
                "click",
                () => {
                    cancelRegistration(
                        button.dataset.registrationCode
                    );
                }
            );
        });

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


async function cancelRegistration(
    registrationCode
) {
    const confirmation = confirm(
        `Cancel registration ${registrationCode}?`
    );

    if (!confirmation) {
        return;
    }

    try {
        await apiRequest(
            `/api/registrations/${registrationCode}`,
            {
                method: "DELETE"
            }
        );

        showToast(
            "Registration cancelled successfully."
        );

        getElement(
            "#registrationSearchForm"
        ).requestSubmit();

        loadEvents();

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


async function saveEvent(submitEvent) {
    submitEvent.preventDefault();

    const eventId = getElement(
        "#eventId"
    ).value;

    const eventData = {
        title: getElement(
            "#eventTitle"
        ).value,

        description: getElement(
            "#eventDescription"
        ).value,

        category: getElement(
            "#eventCategory"
        ).value,

        event_date: getElement(
            "#eventDate"
        ).value,

        venue: getElement(
            "#eventVenue"
        ).value,

        capacity: Number(
            getElement(
                "#eventCapacity"
            ).value
        ),

        status: getElement(
            "#eventStatus"
        ).value
    };

    try {
        const path = eventId
            ? `/api/events/${eventId}`
            : "/api/events";

        const method = eventId
            ? "PUT"
            : "POST";

        await apiRequest(
            path,
            {
                method: method,
                body: JSON.stringify(eventData)
            }
        );

        showToast(
            eventId
                ? "Event updated successfully."
                : "Event created successfully."
        );

        resetEventForm();
        await loadEvents();

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


function editEvent(eventId) {
    const selectedEvent = events.find(
        (event) => event.id === eventId
    );

    getElement(
        "#eventId"
    ).value = selectedEvent.id;

    getElement(
        "#eventTitle"
    ).value = selectedEvent.title;

    getElement(
        "#eventDescription"
    ).value = selectedEvent.description;

    getElement(
        "#eventCategory"
    ).value = selectedEvent.category;

    getElement(
        "#eventDate"
    ).value = selectedEvent.event_date;

    getElement(
        "#eventVenue"
    ).value = selectedEvent.venue;

    getElement(
        "#eventCapacity"
    ).value = selectedEvent.capacity;

    getElement(
        "#eventStatus"
    ).value = selectedEvent.status;

    getElement(
        "#eventFormHeading"
    ).textContent = "Edit Event";

    getElement(
        "#saveEventButton"
    ).textContent = "Save Changes";

    getElement(
        "#cancelEdit"
    ).classList.remove("hidden");
}


function resetEventForm() {
    getElement(
        "#eventForm"
    ).reset();

    getElement(
        "#eventId"
    ).value = "";

    getElement(
        "#eventFormHeading"
    ).textContent = "Create New Event";

    getElement(
        "#saveEventButton"
    ).textContent = "Create Event";

    getElement(
        "#cancelEdit"
    ).classList.add("hidden");
}


async function deleteEvent(eventId) {
    const selectedEvent = events.find(
        (event) => event.id === eventId
    );

    const confirmation = confirm(
        `Delete ${selectedEvent.title}?`
    );

    if (!confirmation) {
        return;
    }

    try {
        await apiRequest(
            `/api/events/${eventId}`,
            {
                method: "DELETE"
            }
        );

        showToast(
            "Event deleted successfully."
        );

        await loadEvents();

    } catch (error) {
        showToast(
            error.message,
            "error"
        );
    }
}


function initializeApplication() {
    loadSystemInformation();
    loadEvents();

    getElements(
        ".nav-button"
    ).forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                switchPage(
                    button.dataset.page
                );
            }
        );
    });

    let searchTimer;

    getElement(
        "#searchInput"
    ).addEventListener(
        "input",
        () => {
            clearTimeout(searchTimer);

            searchTimer = setTimeout(
                loadEvents,
                300
            );
        }
    );

    getElement(
        "#categoryFilter"
    ).addEventListener(
        "change",
        loadEvents
    );

    getElement(
        "#statusFilter"
    ).addEventListener(
        "change",
        loadEvents
    );

    getElement(
        "#refreshEvents"
    ).addEventListener(
        "click",
        loadEvents
    );

    getElement(
        "#refreshAdminEvents"
    ).addEventListener(
        "click",
        loadEvents
    );

    getElement(
        "#registrationForm"
    ).addEventListener(
        "submit",
        submitRegistration
    );

    getElement(
        "#registrationSearchForm"
    ).addEventListener(
        "submit",
        searchRegistrations
    );

    getElement(
        "#eventForm"
    ).addEventListener(
        "submit",
        saveEvent
    );

    getElement(
        "#cancelEdit"
    ).addEventListener(
        "click",
        resetEventForm
    );

    getElement(
        "#closeDialog"
    ).addEventListener(
        "click",
        () => {
            getElement(
                "#registrationDialog"
            ).close();
        }
    );

    getElement(
        "#cancelRegistrationDialog"
    ).addEventListener(
        "click",
        () => {
            getElement(
                "#registrationDialog"
            ).close();
        }
    );
}


document.addEventListener(
    "DOMContentLoaded",
    initializeApplication
);