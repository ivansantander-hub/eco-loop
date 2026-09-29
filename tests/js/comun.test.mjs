// Pruebas de web/comun.js con Node (sin navegador). Las ejecuta tests/test_web.py.
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const require = createRequire(import.meta.url);
const { esc, norm, romano, mil, md } = require("../../web/comun.js");

assert.equal(esc('<a href="x">&</a>'), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;");
assert.equal(norm("¡Hola!"), "hola");
assert.equal(norm("**Estudios**"), "estudios");
assert.deepEqual([1, 4, 9, 14, 20, 49, 57, 99, 2026].map(romano), ["I", "IV", "IX", "XIV", "XX", "XLIX", "LVII", "XCIX", "MMXXVI"]);
assert.equal(mil(950), "950");
assert.equal(mil(3100), "3.1k");
assert.equal(mil(40960), "41k");

const html = md("¡Claro! Son **estudios**:\n\n---\n\n### 🧪 **Clínicos**\n\n- **Área:** Cardio\n  - Sub\n\n1. uno\n2. dos con *cursiva* y `code`");
assert.ok(html.includes("<strong>estudios</strong>"));
assert.ok(html.includes("<hr>"));
assert.ok(html.includes('<div class="md-h md-h3">🧪 <strong>Clínicos</strong></div>'));
assert.ok(html.includes('<li class="sub">Sub</li>'));
assert.ok(html.includes('<ol start="1">'));
assert.ok(html.includes("<em>cursiva</em>") && html.includes("<code>code</code>"));
assert.ok(!md("<script>alert(1)</script>").includes("<script>"), "escapa el HTML de los modelos");
console.log("comun.js: ok");
