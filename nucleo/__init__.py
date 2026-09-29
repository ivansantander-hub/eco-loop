"""Núcleo de eco loop: el motor de las conversaciones.

No sabe nada de laboratorios concretos ni de interfaces. Lo usan por igual el servidor web
(web/), los comandos (cli/) y las pruebas (tests/).

    proveedores  Ollama, OpenRouter (y un proveedor de prueba) detrás de la misma interfaz
    formatos/    cómo se arman los mensajes de cada turno («chat», y en el futuro guion, moderado…)
    memoria      qué recuerda cada IA: completa, resumen + recientes o solo recientes
    medidas      originalidad, copias, bucles y señales de rol
    ensayos      crear, guardar, cargar y migrar ensayos
    laboratorios leer las definiciones de laboratorios/<id>/lab.json
    motor        ejecutar un turno: memoria + formato + proveedor, y guardarlo
    informe      armar el informe HTML de un laboratorio
"""
