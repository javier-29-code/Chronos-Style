(() => {
    const dialogo = document.getElementById("calendar-detail");
    const calendario = document.querySelector(".calendar-layout");

    if (!dialogo || !calendario) return;

    const formulario = document.getElementById("calendar-move");
    const errorDialogo = document.getElementById("calendar-move-error");
    const estado = document.getElementById("calendar-move-status");
    let seleccionado;
    let arrastrado;
    let guardando = false;
    let distanciaAlInicio = 0;

    function mostrarError(elemento, texto = "") {
        elemento.textContent = texto;
        elemento.hidden = !texto;
    }

    async function guardarUbicacion(boton, datos, error) {
        if (guardando) return;

        mostrarError(error);
        guardando = true;
        const campos = formulario.querySelector("fieldset");
        campos.disabled = true;
        datos.set("csrfmiddlewaretoken", formulario.elements.csrfmiddlewaretoken.value);

        try {
            const respuesta = await fetch(boton.dataset.mover, {
                method: "POST",
                body: datos,
                headers: {Accept: "application/json"},
                mode: "same-origin",
            });
            const esJson = respuesta.headers.get("Content-Type")?.includes("application/json");
            const resultado = esJson ? await respuesta.json() : {};
            if (!respuesta.ok || !resultado.ok) {
                mostrarError(
                    error,
                    resultado.errores?.join(" ") || "No se pudo guardar la ubicación."
                );
                return;
            }

            history.replaceState(null, "", "#calendario-propuesta");
            window.location.reload();
        } catch {
            mostrarError(error, "No se pudo comunicar con el servidor. Inténtalo nuevamente.");
        } finally {
            campos.disabled = false;
            guardando = false;
        }
    }

    calendario.querySelectorAll("[data-calendar-event]").forEach(boton => {
        boton.addEventListener("click", () => {
            dialogo.querySelectorAll("[data-detalle]").forEach(elemento => {
                elemento.textContent = boton.dataset[elemento.dataset.detalle] || "";
            });

            if (formulario) {
                seleccionado = boton;
                formulario.elements.dia.value = boton.dataset.diaNumero;
                formulario.elements.hora_inicio.value = boton.dataset.horaInicio;
                formulario.elements.aula.value = boton.dataset.aulaId;
                mostrarError(errorDialogo);
            }

            dialogo.showModal();
        });

        if (!boton.dataset.mover) return;

        boton.addEventListener("dragstart", evento => {
            if (guardando) {
                evento.preventDefault();
                return;
            }

            arrastrado = boton;
            distanciaAlInicio = evento.clientY - boton.getBoundingClientRect().top;
            evento.dataTransfer.setData("text/plain", boton.dataset.diaNumero);
            evento.dataTransfer.effectAllowed = "move";
            boton.classList.add("is-dragging");
            mostrarError(estado);
        });

        boton.addEventListener("dragend", () => {
            arrastrado = null;
            boton.classList.remove("is-dragging");
            calendario.querySelectorAll(".is-drop-target").forEach(columna => {
                columna.classList.remove("is-drop-target");
            });
        });
    });

    if (!formulario) return;

    formulario.addEventListener("submit", evento => {
        evento.preventDefault();
        if (seleccionado?.dataset.mover) {
            guardarUbicacion(seleccionado, new FormData(formulario), errorDialogo);
        }
    });

    calendario.querySelectorAll("[data-dia-calendario]").forEach(columna => {
        columna.addEventListener("dragover", evento => {
            if (!arrastrado) return;
            evento.preventDefault();
            evento.dataTransfer.dropEffect = "move";
            columna.classList.add("is-drop-target");
        });

        columna.addEventListener("dragleave", evento => {
            if (!columna.contains(evento.relatedTarget)) {
                columna.classList.remove("is-drop-target");
            }
        });

        columna.addEventListener("drop", evento => {
            if (!arrastrado) return;
            evento.preventDefault();
            columna.classList.remove("is-drop-target");

            const destino = columna.getBoundingClientRect();
            const inicio = Number(calendario.dataset.inicio);
            const fin = Number(calendario.dataset.fin);
            const posicion = evento.clientY - destino.top - distanciaAlInicio;
            const minutos = inicio + posicion * (fin - inicio) / destino.height;
            const paso = 15;
            const hora = Math.min(fin - paso, Math.max(inicio, Math.round(minutos / paso) * paso));
            const horaTexto = String(Math.floor(hora / 60)).padStart(2, "0");
            const minutoTexto = String(hora % 60).padStart(2, "0");

            const datos = new FormData();
            datos.set("dia", columna.dataset.diaCalendario);
            datos.set("hora_inicio", horaTexto + ":" + minutoTexto);
            guardarUbicacion(arrastrado, datos, estado);
        });
    });
})();
