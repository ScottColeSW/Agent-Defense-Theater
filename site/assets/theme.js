/* Theme: dim (default), light or dark. Loaded in the head, after the stylesheet, so the page never flashes the wrong one.
   T holds the theme's colors for the charts, which are drawn in script, so charts and page always agree. */
(function () {
  try { var t = localStorage.getItem("adt-theme"); if (t === "light" || t === "dark" || t === "dim") document.documentElement.dataset.theme = t; } catch (e) { /* private window: stay on the default */ }
})();
const THEME = document.documentElement.dataset.theme || "dim";
const _css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const T = {text: _css("--text-primary"), muted: _css("--text-secondary"), grid: _css("--grid"), card: _css("--bg-card"), soft: _css("--soft"),
  blue: _css("--accent-blue"), green: _css("--accent-emerald"), red: _css("--accent-rose"), amber: _css("--accent-amber"), violet: _css("--accent-violet"),
  blueInk: _css("--blue-ink"), greenInk: _css("--green-ink"), redInk: _css("--red-ink"), amberInk: _css("--amber-ink"), violetInk: _css("--violet-ink")};
/* a translucent tint of a theme color, for fills: tint(T.red, .2) */
const tint = (color, a) => `color-mix(in srgb, ${color} ${Math.round(a * 100)}%, transparent)`;

function mountTheme() {
  const nav = document.querySelector(".site-nav");
  if (!nav || nav.querySelector(".theme-switch")) return;
  const box = document.createElement("span");
  box.className = "theme-switch"; box.setAttribute("role", "group"); box.setAttribute("aria-label", "Theme");
  box.innerHTML = [["dim", "Dim"], ["light", "Light"], ["dark", "Dark"]].map(([k, l]) => `<button type="button" data-t="${k}" aria-pressed="${k === THEME}">${l}</button>`).join("");
  box.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b || b.dataset.t === THEME) return;
    try { localStorage.setItem("adt-theme", b.dataset.t); } catch (err) { /* cannot remember it, still switch */ }
    document.documentElement.dataset.theme = b.dataset.t;
    location.reload();                              // redraw the charts in the new colors
  });
  nav.appendChild(box);
}
document.addEventListener("DOMContentLoaded", mountTheme);
