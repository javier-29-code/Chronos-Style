from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academico.models import Aula, PeriodoAcademico, Asignatura
from usuarios.models import PerfilDocente

from .models import PropuestaHorario


class CatalogosWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user(
            username="admin_catalogos",
            is_staff=True,
            is_superuser=True,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def datos_docente(self):
        return {
            "username": "nuevo_docente",
            "first_name": "Laura",
            "last_name": "García",
            "email": "laura@example.com",
            "titulo": "Ingeniera",
            "area": "Redes",
            "horas_semanales_max": 20,
        }

    def test_crea_docente_con_cuenta_sin_password_utilizable(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_docente"),
            self.datos_docente(),
        )

        self.assertEqual(respuesta.status_code, 302)

        usuario = get_user_model().objects.get(
            username="nuevo_docente",
        )
        self.assertFalse(usuario.has_usable_password())
        self.assertTrue(
            PerfilDocente.objects.filter(usuario=usuario).exists()
        )

    def test_docente_invalido_no_crea_cuenta(self):
        datos = self.datos_docente()
        datos["horas_semanales_max"] = 41

        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_docente"),
            datos,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username="nuevo_docente",
            ).exists()
        )

    def test_crea_aula_desde_web(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nueva_aula"),
            {
                "codigo": "A-PRUEBA",
                "nombre": "Aula de prueba",
                "tipo": Aula.Tipo.AULA,
                "capacidad": 30,
                "cantidad_computadoras": 0,
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(
            Aula.objects.filter(codigo="A-PRUEBA").exists()
        )

    def test_registros_exigen_permisos(self):
        usuario = get_user_model().objects.create_user(
            username="sin_permisos_catalogos",
        )
        self.client.force_login(usuario)

        for nombre in ("nueva_aula", "nuevo_docente"):
            with self.subTest(pantalla=nombre):
                respuesta = self.client.post(
                    reverse(f"planificacion_web:{nombre}"),
                    {},
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_historial_encuentra_propuesta_fuera_de_primera_pagina(self):
        periodo = PeriodoAcademico.objects.create(
            codigo="HISTORIAL",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )

        for numero in range(12):
            PropuestaHorario.objects.create(
                nombre=f"Propuesta archivo {numero:02d}",
                periodo=periodo,
                autor=self.admin,
            )

        url = reverse("planificacion_web:historial_propuestas")

        respuesta = self.client.get(url)
        self.assertEqual(
            len(respuesta.context["pagina"].object_list),
            10,
        )

        respuesta = self.client.get(
            url,
            {"q": "Propuesta archivo 00"},
        )
        self.assertContains(respuesta, "Propuesta archivo 00")
        self.assertEqual(
            respuesta.context["pagina"].paginator.count,
            1,
        )
        
        
    def test_catalogos_abren_desde_web(self):
        for nombre in ("lista_docentes", "lista_aulas"):
            with self.subTest(catalogo=nombre):
                respuesta = self.client.get(
                    reverse(f"planificacion_web:{nombre}")
                )
                self.assertEqual(respuesta.status_code, 200)

    def test_retirar_docente_conserva_cuenta_activa(self):
        self.client.post(
            reverse("planificacion_web:nuevo_docente"),
            self.datos_docente(),
        )

        usuario = get_user_model().objects.get(
            username="nuevo_docente",
        )
        docente = PerfilDocente.objects.get(usuario=usuario)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:estado_docente",
                args=[docente.pk],
            ),
            {"estado": "retirado"},
        )

        self.assertEqual(respuesta.status_code, 302)
        docente.refresh_from_db()
        usuario.refresh_from_db()

        self.assertFalse(docente.activo)
        self.assertTrue(usuario.is_active)

    def test_aula_se_retira_y_se_reactiva_sin_borrarse(self):
        aula = Aula.objects.create(
            codigo="A-ESTADO",
            nombre="Aula de prueba",
        )
        url = reverse(
            "planificacion_web:estado_aula",
            args=[aula.pk],
        )

        self.client.post(url, {"estado": "retirado"})
        aula.refresh_from_db()
        self.assertFalse(aula.activo)

        self.client.post(url, {"estado": "activo"})
        aula.refresh_from_db()
        self.assertTrue(aula.activo)

    def test_cambiar_estado_rechaza_get(self):
        for nombre in ("estado_docente", "estado_aula"):
            with self.subTest(accion=nombre):
                respuesta = self.client.get(
                    reverse(
                        f"planificacion_web:{nombre}",
                        args=[999],
                    )
                )
                self.assertEqual(respuesta.status_code, 405)
                
                
    def test_crea_asignatura_y_abre_catalogo(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nueva_asignatura"),
            {
                "codigo": "  prog-01 ",
                "nombre": "Programación",
                "activo": "on",
            },
            follow=True,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "PROG-01")
        self.assertTrue(
            Asignatura.objects.filter(codigo="PROG-01").exists()
        )

    def test_edita_asignatura_sin_crear_otra(self):
        asignatura = Asignatura.objects.create(
            codigo="BD-01",
            nombre="Nombre anterior",
        )

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_asignatura",
                args=[asignatura.pk],
            ),
            {
                "codigo": "BD-01",
                "nombre": "Bases de datos",
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        asignatura.refresh_from_db()
        self.assertEqual(asignatura.nombre, "Bases de datos")
        self.assertEqual(Asignatura.objects.count(), 1)

    def test_retira_y_reactiva_asignatura(self):
        asignatura = Asignatura.objects.create(
            codigo="BD-01",
            nombre="Bases de datos",
        )
        url = reverse(
            "planificacion_web:estado_asignatura",
            args=[asignatura.pk],
        )

        self.client.post(url, {"estado": "retirado"})
        asignatura.refresh_from_db()
        self.assertFalse(asignatura.activo)

        self.client.post(url, {"estado": "activo"})
        asignatura.refresh_from_db()
        self.assertTrue(asignatura.activo)

    def test_asignatura_rechaza_codigo_duplicado_desde_web(self):
        Asignatura.objects.create(
            codigo="BD-01",
            nombre="Bases de datos",
        )

        respuesta = self.client.post(
            reverse("planificacion_web:nueva_asignatura"),
            {
                "codigo": "bd-01",
                "nombre": "Otra materia",
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Asignatura.objects.count(), 1)

    def test_asignaturas_exigen_permisos(self):
        asignatura = Asignatura.objects.create(
            codigo="BD-01",
            nombre="Bases de datos",
        )
        usuario = get_user_model().objects.create_user(
            username="sin_permisos_asignaturas",
        )
        self.client.force_login(usuario)

        direcciones = (
            reverse("planificacion_web:lista_asignaturas"),
            reverse("planificacion_web:nueva_asignatura"),
            reverse(
                "planificacion_web:editar_asignatura",
                args=[asignatura.pk],
            ),
            reverse(
                "planificacion_web:estado_asignatura",
                args=[asignatura.pk],
            ),
        )

        for direccion in direcciones:
            with self.subTest(direccion=direccion):
                respuesta = self.client.post(direccion, {})
                self.assertEqual(respuesta.status_code, 403)
                
                
    def test_crea_periodo_desde_web(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_periodo"),
            {
                "codigo": "PERIODO-2027",
                "nombre": "Periodo académico 2027",
                "fecha_inicio": "2027-03-01",
                "fecha_fin": "2027-07-31",
            },
            follow=True,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "PERIODO-2027")
        self.assertTrue(
            PeriodoAcademico.objects.filter(
                codigo="PERIODO-2027",
            ).exists()
        )

    def test_periodo_con_fechas_invertidas_no_se_guarda(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_periodo"),
            {
                "codigo": "INVALIDO",
                "nombre": "Periodo inválido",
                "fecha_inicio": "2027-07-31",
                "fecha_fin": "2027-03-01",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            PeriodoAcademico.objects.filter(
                codigo="INVALIDO",
            ).exists()
        )

    def test_busca_periodo_por_codigo(self):
        PeriodoAcademico.objects.create(
            codigo="BUSCAR-2027",
            nombre="Periodo de búsqueda",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )

        respuesta = self.client.get(
            reverse("planificacion_web:lista_periodos"),
            {"q": "BUSCAR-2027"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.context["pagina"].paginator.count,
            1,
        )

    def test_periodos_exigen_permisos(self):
        usuario = get_user_model().objects.create_user(
            username="sin_permisos_periodos",
        )
        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("planificacion_web:lista_periodos")
        )
        self.assertEqual(respuesta.status_code, 403)

        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_periodo"),
            {},
        )
        self.assertEqual(respuesta.status_code, 403)
        
        
    def _datos_edicion_aula(self, **cambios):
        datos = {
            "codigo": "A-EDITAR",
            "nombre": "Aula actualizada",
            "tipo": Aula.Tipo.AULA,
            "ubicacion": "Edificio principal",
            "capacidad": 35,
            "cantidad_computadoras": 0,
            "equipamiento": "Pizarra",
            "tiene_proyector": "on",
            "activo": "on",
        }
        datos.update(cambios)
        return datos

    def test_edita_aula_conservando_identificador(self):
        aula = Aula.objects.create(
            codigo="A-EDITAR",
            nombre="Nombre anterior",
            capacidad=20,
        )
        identificador = aula.pk

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_aula",
                args=[aula.pk],
            ),
            self._datos_edicion_aula(),
        )

        self.assertEqual(respuesta.status_code, 302)
        aula.refresh_from_db()
        self.assertEqual(aula.pk, identificador)
        self.assertEqual(aula.nombre, "Aula actualizada")
        self.assertEqual(aula.capacidad, 35)
        self.assertTrue(aula.tiene_proyector)
        self.assertEqual(Aula.objects.count(), 1)

    def test_edicion_aula_invalida_conserva_datos(self):
        aula = Aula.objects.create(
            codigo="A-EDITAR",
            nombre="Nombre anterior",
            capacidad=20,
        )

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_aula",
                args=[aula.pk],
            ),
            self._datos_edicion_aula(capacidad=0),
        )

        self.assertEqual(respuesta.status_code, 200)
        aula.refresh_from_db()
        self.assertEqual(aula.nombre, "Nombre anterior")
        self.assertEqual(aula.capacidad, 20)

    def test_edicion_aula_rechaza_codigo_duplicado(self):
        Aula.objects.create(
            codigo="OCUPADO",
            nombre="Otra aula",
        )
        aula = Aula.objects.create(
            codigo="A-EDITAR",
            nombre="Nombre anterior",
        )

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_aula",
                args=[aula.pk],
            ),
            self._datos_edicion_aula(codigo="ocupado"),
        )

        self.assertEqual(respuesta.status_code, 200)
        aula.refresh_from_db()
        self.assertEqual(aula.codigo, "A-EDITAR")
        self.assertEqual(aula.nombre, "Nombre anterior")

    def test_edicion_aula_exige_permiso(self):
        aula = Aula.objects.create(
            codigo="A-EDITAR",
            nombre="Nombre anterior",
        )
        usuario = get_user_model().objects.create_user(
            username="sin_permiso_editar_aula",
        )
        self.client.force_login(usuario)

        url = reverse(
            "planificacion_web:editar_aula",
            args=[aula.pk],
        )

        self.assertEqual(self.client.get(url).status_code, 403)

        respuesta = self.client.post(
            url,
            self._datos_edicion_aula(),
        )

        self.assertEqual(respuesta.status_code, 403)
        aula.refresh_from_db()
        self.assertEqual(aula.nombre, "Nombre anterior")