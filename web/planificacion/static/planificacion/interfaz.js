(() => {
    const sidebar = document.getElementById("sidebar");
    const abrir = document.getElementById("menu-open");
    const overlay = document.querySelector(".sidebar-overlay");
    const movil = window.matchMedia("(max-width: 800px)");

    if (!sidebar || !abrir || !overlay) return;

    function cambiarMenu(abierto) {
        const mostrar = movil.matches && abierto;

        document.body.classList.toggle("menu-open", mostrar);
        abrir.setAttribute("aria-expanded", String(mostrar));
        overlay.hidden = !mostrar;
        sidebar.inert = movil.matches && !mostrar;
    }

    abrir.addEventListener("click", () => {
        cambiarMenu(true);
        sidebar.querySelector("a")?.focus();
    });

    document.querySelectorAll("[data-menu-close]").forEach(boton => {
        boton.addEventListener("click", () => {
            cambiarMenu(false);
            abrir.focus();
        });
    });

    document.addEventListener("keydown", evento => {
        if (
            evento.key === "Escape" &&
            document.body.classList.contains("menu-open")
        ) {
            cambiarMenu(false);
            abrir.focus();
        }
    });

    movil.addEventListener("change", () => cambiarMenu(false));

    cambiarMenu(false);
})();