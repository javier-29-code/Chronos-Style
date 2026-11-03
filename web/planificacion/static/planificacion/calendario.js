(() => {
    const dialogo = document.getElementById("calendar-detail");

    if (!dialogo) return;

    document.querySelectorAll("[data-calendar-event]").forEach(boton => {
        boton.addEventListener("click", () => {
            dialogo.querySelectorAll("[data-detalle]").forEach(elemento => {
                const clave = elemento.dataset.detalle;
                elemento.textContent = boton.dataset[clave] || "";
            });

            dialogo.showModal();
        });
    });
})();