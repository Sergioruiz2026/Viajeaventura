import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from excepciones import AutorizacionError, SesionExpiradaError, ValidacionError
from modelos.cliente import Cliente
from modelos.destino import Destino
from modelos.sesion import Sesion
from repositorios.base_datos import BaseDatos
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from servicios.paquete_servicio import PaqueteServicio


class GestionPaquetesTests(unittest.TestCase):
    def setUp(self):
        self.base_datos = BaseDatos(":memory:")
        self.addCleanup(self.base_datos.cerrar)
        self.destinos = DestinoRepositorio(self.base_datos)
        self.paquete_repo = PaqueteRepositorio(self.base_datos)
        self.servicio = PaqueteServicio(self.paquete_repo, self.destinos)
        self.admin = Sesion.administrador("admin")
        cliente = Cliente("Ana", "12.345.678-5", "ana@example.com", "+56912345678", "hash")
        self.cliente = Sesion(cliente)
        self.destinos.agregar(
            Destino("Norte", "Zona", "Desierto", 3, 120000)
        )
        self.destinos.agregar(
            Destino("Sur", "Zona", "Lagos", 4, 310000)
        )
        filas = self.base_datos.conexion.execute(
            "SELECT id FROM destinos ORDER BY id"
        ).fetchall()
        self.ids_destinos = [fila["id"] for fila in filas]

    def crear_paquete(self, nombre, fecha_salida=None, **kwargs):
        salida = fecha_salida or date.today() + timedelta(days=30)
        return self.servicio.crear_paquete(
            nombre,
            ids_destinos=self.ids_destinos,
            fecha_salida=salida,
            fecha_regreso=salida + timedelta(days=5),
            cupo_maximo=4,
            sesion=self.admin,
            **kwargs
        )

    def test_calcula_redondea_y_conserva_precio_publicado(self):
        paquete = self.crear_paquete(
            "Ruta", margen_operacion=Decimal("0.20")
        )
        self.assertEqual(paquete.precio_por_persona, Decimal("516000"))

        destino = self.destinos.buscar_por_nombre("Norte")
        destino.actualizar_costo(900000)
        self.destinos.actualizar("Norte", destino)

        guardado = self.paquete_repo.buscar_por_nombre("Ruta")
        self.assertEqual(guardado.precio_por_persona, Decimal("516000"))

    def test_roles_no_pueden_invocar_operaciones_de_paquetes_ajenas(self):
        salida = date.today() + timedelta(days=30)
        with self.assertRaises(AutorizacionError):
            self.servicio.crear_paquete(
                "Solo admin", self.ids_destinos, salida,
                salida + timedelta(days=5), 4, sesion=self.cliente
            )
        with self.assertRaises(AutorizacionError):
            self.servicio.listar_paquetes(sesion=self.cliente)
        with self.assertRaises(AutorizacionError):
            self.servicio.listar_vigentes(sesion=self.admin)
        sesion_expirada = Sesion(
            self.cliente.usuario,
            ahora=datetime.now() - timedelta(minutes=31)
        )
        with self.assertRaises(SesionExpiradaError):
            self.servicio.listar_vigentes(sesion=sesion_expirada)

    def test_rechaza_selecciones_invalidas_y_margen_negativo(self):
        salida = date.today() + timedelta(days=30)
        base = (salida, salida + timedelta(days=5), 4)
        for ids in ([], [self.ids_destinos[0]], self.ids_destinos * 3):
            with self.subTest(ids=ids), self.assertRaises(ValidacionError):
                self.servicio.crear_paquete(
                    "Inválido", ids, *base, sesion=self.admin
                )

        for ids, regreso, cupo, margen in (
            ([self.ids_destinos[0]] * 2, base[1], base[2], Decimal("0.2")),
            (self.ids_destinos, salida, base[2], Decimal("0.2")),
            (self.ids_destinos, base[1], 0, Decimal("0.2")),
            (self.ids_destinos, base[1], base[2], Decimal("-0.01")),
        ):
            with self.subTest(ids=ids, regreso=regreso, cupo=cupo, margen=margen):
                with self.assertRaises(ValidacionError):
                    self.servicio.crear_paquete(
                        "Inválido", ids, salida, regreso, cupo,
                        margen_operacion=margen, sesion=self.admin
                    )

        self.base_datos.conexion.execute(
            "UPDATE destinos SET disponible = 0 WHERE id = ?",
            (self.ids_destinos[0],)
        )
        with self.assertRaises(ValidacionError):
            self.servicio.crear_paquete(
                "Destino retirado", ids_destinos=self.ids_destinos,
                fecha_salida=salida, fecha_regreso=base[1], cupo_maximo=4,
                sesion=self.admin
            )

    def test_consultas_cliente_y_admin_exponen_cupo_y_estado(self):
        ayer = date.today() - timedelta(days=1)
        hoy = date.today()
        manana = date.today() + timedelta(days=1)
        self.crear_paquete("Vencido", ayer)
        self.crear_paquete("Hoy", hoy)
        self.crear_paquete("Vigente", manana)

        conexion = self.base_datos.conexion
        conexion.execute(
            """
            INSERT INTO usuarios (nombre, rut, correo, telefono, password_hash)
            VALUES ('Test', '1-9', 'test@example.com', '123', 'hash')
            """
        )
        paquete_id = conexion.execute(
            "SELECT id FROM paquetes WHERE nombre = 'Vigente'"
        ).fetchone()["id"]
        conexion.execute(
            """
            INSERT INTO reservas (usuario_id, paquete_id, cantidad_personas,
                                  fecha_emision, total)
            VALUES (1, ?, 2, ?, 100)
            """,
            (paquete_id, date.today().isoformat())
        )
        conexion.execute(
            """
            INSERT INTO reservas (usuario_id, paquete_id, cantidad_personas,
                                  fecha_emision, total, estado)
            VALUES (1, ?, 1, ?, 100, 'CANCELADA')
            """,
            (paquete_id, date.today().isoformat())
        )
        conexion.commit()

        vigentes = self.servicio.listar_vigentes(sesion=self.cliente)
        self.assertEqual([paquete.nombre for paquete in vigentes], ["Vigente"])
        self.assertEqual(vigentes[0].cupo_disponible, 2)
        self.assertEqual(vigentes[0].cupo_reservado_activo, 2)
        self.assertIn("Cupos disponibles: 2", str(vigentes[0]))

        todos = self.servicio.listar_paquetes(sesion=self.admin)
        self.assertEqual(len(todos), 3)
        self.assertEqual(
            {paquete.nombre: paquete.estado for paquete in todos},
            {"Vencido": "Vencido", "Hoy": "Vencido", "Vigente": "Vigente"}
        )
        self.assertIn("Vencido", str(todos[0]))


if __name__ == "__main__":
    unittest.main()