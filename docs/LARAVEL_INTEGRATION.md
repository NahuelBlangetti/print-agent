  # Integración con Laravel

  Esta guía es para el equipo de Laravel: qué impresoras soporta el agente y
  cómo comunicarse con él desde la app (cloud) hacia la PC del cliente.

  ## 1. Qué impresoras puede usar este proyecto

  El agente **no imprime documentos genéricos** (PDF, Word, imágenes). Solo
  reenvía dos tipos de contenido crudo, tal cual se lo mande Laravel, a la
  impresora indicada:

  | Endpoint | Protocolo | Tipo de impresora | Driver |
  |---|---|---|---|
  | `POST /print/label` | ZPL | Etiquetadoras Zebra (o cualquier impresora compatible con ZPL) | `ZebraDriver` |
  | `POST /print/ticket` | ESC/POS | Impresoras de tickets/recibos: Epson, XPrinter y compatibles | `EscPosDriver` |

  Requisitos para que una impresora funcione con el agente:
  - Debe estar **instalada en el sistema operativo** de la PC del cliente
    (spooler de Windows, o CUPS en Ubuntu 22.04) — el agente no descubre
    impresoras por su cuenta, solo lista las que el SO ya reconoce
    (`GET /printers`).
  - Idealmente configurada como **cola RAW**, para que el SO no intente
    reinterpretar el ZPL/ESC-POS como texto normal.
  - Conectada por USB o red (LAN) — es indistinto para el agente, ya que
    habla con la impresora a través del spooler del SO, no directamente
    por USB/red.

  Todavía no soporta otro tipo de dispositivos (básculas, cajones
  monederos, terminales de pago) — eso está en el roadmap del
  [README.md](../README.md).

  ## 2. Cómo se comunica Laravel con el agente

  **Punto clave: Laravel corre en la nube, el agente corre en `127.0.0.1` de
  la PC del cliente.** El backend de Laravel (el servidor) *no puede* llamar
  directamente al agente — no hay ninguna ruta de red desde la nube hacia el
  `localhost` de la computadora del cliente.

  Quien sí puede llegar al agente es **el navegador del cliente**, porque
  corre físicamente en la misma máquina donde está instalado el agente. Por
  eso la integración es siempre client-side (JavaScript), nunca
  server-to-server:

  ```
  1. Usuario hace clic en "Imprimir" en la webapp
  2. Navegador  --AJAX-->  Laravel (Cloud)
                            Laravel genera el ZPL/ESC-POS (logica de negocio)
                            y lo devuelve como JSON
  3. Navegador  --fetch directo-->  Print Agent (http://127.0.0.1:58432)
                                    usando el contenido recibido en el paso 2
  4. Print Agent responde 202 + job_id, encola e imprime en background
  5. (Opcional) Navegador hace polling a
    GET http://127.0.0.1:58432/print/job/{job_id}
  ```

  ### Ejemplo

  **Laravel — genera el contenido y lo devuelve (no imprime nada):**

  ```php
  // routes/api.php
  Route::post('/labels/{order}/zpl', [LabelController::class, 'zpl']);
  ```

  ```php
  // app/Http/Controllers/LabelController.php
  public function zpl(Order $order)
  {
      $zpl = $this->zplBuilder->build($order); // logica de negocio, vive en Laravel

      return response()->json([
          'printer' => $order->store->default_label_printer, // nombre exacto instalado en el SO
          'content' => $zpl,
      ]);
  }
  ```

  **Frontend — pide el ZPL a Laravel y lo manda directo al agente local:**

  ```js
  async function printLabel(orderId) {
    const { printer, content } = await fetch(`/api/labels/${orderId}/zpl`)
      .then(r => r.json());

    const res = await fetch('http://127.0.0.1:58432/print/label', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ printer, content }),
    });

    const { job_id } = await res.json(); // 202 Accepted
    return job_id;
  }
  ```

  `host`/`port` son configurables (ver `config/.env.example`); por defecto
  `127.0.0.1:58432`.

  ## 3. CORS

  Como la página la sirve el dominio de Laravel (ej.
  `https://app.tuempresa.com`) y el fetch va a `http://127.0.0.1:58432`, eso
  es un origen distinto — el navegador bloquea la respuesta salvo que el
  agente responda con los headers `Access-Control-Allow-Origin`
  correspondientes.

  (La llamada en sí de una página HTTPS a `http://127.0.0.1` no es
  bloqueada como "mixed content" en navegadores modernos gracias a la
  excepción para loopback, pero **igual hace falta CORS** porque es
  cross-origin.)

  El agente ya tiene `CORSMiddleware` configurado en `app/main.py`, pero
  **no permite ningún origen por defecto** (`cors_origins: list[str] = []`
  en `Settings`, ver [app/core/config.py](../app/core/config.py)). Para
  habilitar la conexión desde el navegador, hay que declarar el dominio
  de Laravel en `config/.env`:

  ```bash
  CORS_ORIGINS=["https://app.tuempresa.com"]
  ```

  Se puede listar más de un origen (ej. dev/staging/producción) separados
  por coma dentro del mismo array JSON. Sin esta variable configurada,
  las llamadas desde el navegador van a fallar con un error de CORS en la
  consola aunque el agente esté corriendo correctamente.

  ## 4. Seguridad

  Hoy no hay autenticación entre Laravel y el agente — cualquier proceso
  que pueda alcanzar `127.0.0.1:58432` en esa PC puede mandar trabajos de
  impresión. `Settings.api_key` ya existe en la configuración pero todavía
  no se aplica en ningún endpoint (ver roadmap en
  [README.md](../README.md)).

  ## 5. Referencia de endpoints

  Ver la sección "Endpoints" del [README.md](../README.md) para el detalle
  completo de request/response de `/status`, `/printers`, `/print/label`,
  `/print/ticket` y `/print/job/{job_id}`.
