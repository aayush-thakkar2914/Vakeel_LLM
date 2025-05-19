async function submitQuery() {
  const input = document.getElementById("queryInput").value.trim();
  const responseContainer = document.getElementById("responseContainer");
  const responseText = document.getElementById("responseText");

  if (!input) {
    alert("Please enter your query.");
    return;
  }

  responseText.textContent = "Processing...";
  responseContainer.classList.remove("hidden");

  try {
    const res = await fetch("http://127.0.0.1:8000/api/vakeel", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ user_input: input })
    });

    const data = await res.json();

    if (res.ok) {
      responseText.textContent = `${data.intent.toUpperCase()}:\n\n${data.response}`;
    } else {
      responseText.textContent = `Error: ${data.detail}`;
    }
  } catch (error) {
    responseText.textContent = "Something went wrong. Please try again.";
    console.error(error);
  }
}
