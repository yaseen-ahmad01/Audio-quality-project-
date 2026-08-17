const form = document.getElementById("submissionForm");
const button = document.getElementById("submitBtn");
const statusBox = document.getElementById("status");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = document.getElementById("audio").files[0];

    if (!file) {
        statusBox.textContent = "Please select an audio file.";
        return;
    }

    if (file.size > 25 * 1024 * 1024) {
        statusBox.textContent = "File must be smaller than 25 MB.";
        return;
    }

    const formData = new FormData(form);

    button.disabled = true;
    button.textContent = "Uploading...";
    statusBox.textContent = "";

    try {
        const response = await fetch("/api/submissions", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Submission failed.");
        }

        statusBox.textContent =
            `Success! Submission #${data.submission_id} was received.`;

        form.reset();
    } catch (error) {
        statusBox.textContent = error.message;
    } finally {
        button.disabled = false;
        button.textContent = "Submit recording";
    }
});
