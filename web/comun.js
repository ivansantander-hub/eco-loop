// Código de pantalla compartido por el informe y el banco de pruebas.
// No calcula medidas: el servidor (nucleo/medidas.py) manda la originalidad, las alertas y las palabras copiadas.

const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// Minúsculas y solo letras y números (igual que `norm` en nucleo/medidas.py).
const norm = w => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

const romano = n => n < 1 ? String(n) : [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"], [90, "XC"], [50, "L"],
  [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]].reduce((s, [v, r]) => { while (n >= v) { s += r; n -= v; } return s; }, "");

const mil = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n);

// Markdown mínimo (lo que usan los modelos y las bitácoras): títulos, negritas, cursivas, código, enlaces,
// listas, tablas, citas y separadores. Todo se interpreta sobre texto ya escapado.
function mdLinea(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(((?:https?:\/\/|\/|#)[^)\s]*)\)/g, (_, t, u) =>
      `<a href="${u}"${u.startsWith("http") ? ' target="_blank" rel="noopener"' : ""}>${t}</a>`)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*\w])\*(?!\s)([^*]+?)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(/(^|[^\w/])_(?!\s)([^_]+?)_(?![\w])/g, "$1<em>$2</em>");
}

const celdas = fila => fila.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());

function md(texto) {
  const out = [];
  let lista = null, parrafo = [], tabla = null, cita = [];
  const cerrarP = () => { if (parrafo.length) { out.push(`<p>${parrafo.join("<br>")}</p>`); parrafo = []; } };
  const cerrarL = () => { if (lista) { out.push(`</${lista}>`); lista = null; } };
  const cerrarT = () => {
    if (!tabla) return;
    const [cab, ...filas] = tabla;
    out.push(`<div class="md-tabla"><table><thead><tr>${cab.map(c => `<th>${mdLinea(c)}</th>`).join("")}</tr></thead><tbody>`
      + filas.map(f => `<tr>${f.map(c => `<td>${mdLinea(c)}</td>`).join("")}</tr>`).join("") + "</tbody></table></div>");
    tabla = null;
  };
  const cerrarC = () => { if (cita.length) { out.push(`<blockquote>${md(cita.join("\n"))}</blockquote>`); cita = []; } };
  const lineas = texto.split("\n");
  for (let i = 0; i < lineas.length; i++) {
    const linea = lineas[i], t = linea.trim();
    let m;
    if (t.startsWith(">")) { cerrarP(); cerrarL(); cerrarT(); cita.push(t.replace(/^>\s?/, "")); continue; }
    cerrarC();
    // Tabla: una fila con | seguida de la línea separadora |---|
    if (t.startsWith("|") && (tabla || /^\|?\s*:?-{2,}/.test((lineas[i + 1] || "").trim()))) {
      cerrarP(); cerrarL();
      if (/^\|?[\s:|-]+$/.test(t)) continue;
      (tabla = tabla || []).push(celdas(t));
      continue;
    }
    cerrarT();
    if (!t) { cerrarP(); cerrarL(); continue; }
    if (/^([-*_])(\s*\1){2,}$/.test(t)) { cerrarP(); cerrarL(); out.push("<hr>"); continue; }
    if ((m = t.match(/^(#{1,6})\s+(.*)$/))) { cerrarP(); cerrarL(); out.push(`<div class="md-h md-h${Math.min(m[1].length, 4)}">${mdLinea(m[2])}</div>`); continue; }
    if ((m = linea.match(/^(\s*)([-*+•]|\d+[.)])\s+(.*)$/))) {
      cerrarP();
      const tipo = /\d/.test(m[2]) ? "ol" : "ul";
      if (lista !== tipo) { cerrarL(); out.push(tipo === "ol" ? `<ol start="${parseInt(m[2])}">` : "<ul>"); lista = tipo; }
      out.push(`<li${m[1].length >= 2 ? ' class="sub"' : ""}>${mdLinea(m[3])}</li>`);
      continue;
    }
    cerrarL();
    parrafo.push(mdLinea(t));
  }
  cerrarP(); cerrarL(); cerrarT(); cerrarC();
  return out.join("");
}

// Pinta un mensaje con formato; las palabras de `copiadas` (normalizadas) llevan el color de la otra IA.
function pintarEn(el, texto, copiadas, autor) {
  el.innerHTML = md(texto);
  const set = copiadas instanceof Set ? copiadas : new Set(copiadas || []);
  if (!set.size) return;
  const cls = autor === 0 ? "w-b" : "w-a";
  const esCopiada = p => set.has(norm(p));
  const recorrido = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), textos = [];
  while (recorrido.nextNode()) textos.push(recorrido.currentNode);
  for (const nodo of textos) {
    const partes = nodo.nodeValue.split(/(\s+)/);
    if (!partes.some(esCopiada)) continue;
    const frag = document.createDocumentFragment();
    for (const p of partes) {
      if (!esCopiada(p)) { frag.append(p); continue; }
      const s = document.createElement("span");
      s.className = cls; s.textContent = p;
      frag.append(s);
    }
    nodo.replaceWith(frag);
  }
}

if (typeof module !== "undefined") module.exports = { esc, norm, romano, mil, md, mdLinea };
