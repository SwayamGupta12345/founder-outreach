const button =
  document.getElementById(
    "health"
  );

const status =
  document.getElementById(
    "status"
  );


button.addEventListener(
  "click",
  async () => {

    status.textContent =
      "Checking local backend...";


    try {

      const response =
        await fetch(
          "http://127.0.0.1:8000/health"
        );


      const data =
        await response.json();


      if (
        data.ollama
      ) {

        status.textContent =
          `✓ Local AI ready · ${data.model}`;

      } else {

        status.textContent =
          "Backend running, but Ollama is unavailable.";

      }


    } catch (error) {

      status.textContent =
        "Backend unavailable.";

    }

  }
);