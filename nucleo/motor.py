"""Motor: ejecuta turnos de un ensayo. Es lo único que junta memoria, formato y proveedor.

Lo usan el servidor (web/servidor.py, en streaming), los comandos (cli/) y las pruebas.
"""
import datetime, time

from . import ensayos, formatos, medidas, memoria, proveedores


def turno(e, al_texto=None, debe_parar=None, al_estado=None, guardar=True, base=None):
    """Genera el siguiente mensaje del ensayo, lo añade y (por defecto) guarda el ensayo.

    al_texto(texto)   se llama con el texto acumulado mientras llega
    debe_parar()      si devuelve True, se corta la generación (proveedores.Cancelado); no se guarda nada
    al_estado(texto)  avisos intermedios («Actualizando la memoria…»)
    Devuelve el mensaje nuevo.
    """
    c = e["config"]
    i = len(e["mensajes"]) % 2
    ia = c["ias"][i]

    def resumir(pedido):
        return proveedores.generar(ia["modelo"], pedido, memoria.TOKENS_RESUMEN, c["temperature"], debe_parar=debe_parar)

    rec = memoria.recuerdo(e, i, resumir, al_estado)
    msgs = formatos.obtener(c.get("formato", "chat")).mensajes(e, i, rec)
    t0 = time.time()
    res = proveedores.generar(ia["modelo"], msgs, c["num_predict"], c["temperature"], al_texto, debe_parar)
    mensaje = {
        "autor": i, "etiqueta": ia["etiqueta"], "modelo": ia["modelo"], "texto": res.texto.strip(),
        "hora": datetime.datetime.now().astimezone().isoformat(), "tokens": res.tokens,
        "segundos": round(time.time() - t0, 1), "cortado": res.cortado,
        "memoria": {**rec.registro(), "ctx": res.ctx},
    }
    if res.costo is not None:
        mensaje["costo"] = res.costo
    e["mensajes"].append(mensaje)
    if guardar:
        ensayos.guardar(e, base)
    return mensaje


def correr(e, hasta=None, parar_en_bucle=False, al_mensaje=None, reintentos=0, espera=10, base=None, **kw):
    """Ejecuta turnos hasta `hasta` (por defecto config.turnos). Devuelve el motivo del final."""
    hasta = hasta or e["config"]["turnos"]
    while len(e["mensajes"]) < hasta:
        for intento in range(reintentos + 1):
            try:
                m = turno(e, base=base, **kw)
                break
            except proveedores.Cancelado:
                raise
            except Exception as err:
                if intento == reintentos:
                    e["notas"] = (e.get("notas", "") + f" Se detuvo en el turno {len(e['mensajes']) + 1}: {err}").strip()
                    ensayos.guardar(e, base)
                    return f"error: {err}"
                time.sleep(espera * (intento + 1))
        al_mensaje and al_mensaje(m)
        if parar_en_bucle and medidas.copias_seguidas(e) >= 2:
            return "bucle"
    return "fin"
