var pe = Object.defineProperty;
var _e = (r, e, t) => e in r ? pe(r, e, { enumerable: !0, configurable: !0, writable: !0, value: t }) : r[e] = t;
var B = (r, e, t) => _e(r, typeof e != "symbol" ? e + "" : e, t);
/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const O = globalThis, J = O.ShadowRoot && (O.ShadyCSS === void 0 || O.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, se = Symbol(), G = /* @__PURE__ */ new WeakMap();
let ge = class {
  constructor(e, t, n) {
    if (this._$cssResult$ = !0, n !== se) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = t;
  }
  get styleSheet() {
    let e = this.o;
    const t = this.t;
    if (J && e === void 0) {
      const n = t !== void 0 && t.length === 1;
      n && (e = G.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), n && G.set(t, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const D = (r) => new ge(typeof r == "string" ? r : r + "", void 0, se), ve = (r, e) => {
  if (J) r.adoptedStyleSheets = e.map((t) => t instanceof CSSStyleSheet ? t : t.styleSheet);
  else for (const t of e) {
    const n = document.createElement("style"), a = O.litNonce;
    a !== void 0 && n.setAttribute("nonce", a), n.textContent = t.cssText, r.appendChild(n);
  }
}, Q = J ? (r) => r : (r) => r instanceof CSSStyleSheet ? ((e) => {
  let t = "";
  for (const n of e.cssRules) t += n.cssText;
  return D(t);
})(r) : r;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: we, defineProperty: $e, getOwnPropertyDescriptor: ye, getOwnPropertyNames: ke, getOwnPropertySymbols: xe, getPrototypeOf: Ae } = Object, p = globalThis, Z = p.trustedTypes, Se = Z ? Z.emptyScript : "", L = p.reactiveElementPolyfillSupport, A = (r, e) => r, V = { toAttribute(r, e) {
  switch (e) {
    case Boolean:
      r = r ? Se : null;
      break;
    case Object:
    case Array:
      r = r == null ? r : JSON.stringify(r);
  }
  return r;
}, fromAttribute(r, e) {
  let t = r;
  switch (e) {
    case Boolean:
      t = r !== null;
      break;
    case Number:
      t = r === null ? null : Number(r);
      break;
    case Object:
    case Array:
      try {
        t = JSON.parse(r);
      } catch {
        t = null;
      }
  }
  return t;
} }, le = (r, e) => !we(r, e), X = { attribute: !0, type: String, converter: V, reflect: !1, useDefault: !1, hasChanged: le };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), p.litPropertyMetadata ?? (p.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
let y = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ?? (this.l = [])).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, t = X) {
    if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
      const n = Symbol(), a = this.getPropertyDescriptor(e, n, t);
      a !== void 0 && $e(this.prototype, e, a);
    }
  }
  static getPropertyDescriptor(e, t, n) {
    const { get: a, set: o } = ye(this.prototype, e) ?? { get() {
      return this[t];
    }, set(i) {
      this[t] = i;
    } };
    return { get: a, set(i) {
      const l = a == null ? void 0 : a.call(this);
      o == null || o.call(this, i), this.requestUpdate(e, l, n);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? X;
  }
  static _$Ei() {
    if (this.hasOwnProperty(A("elementProperties"))) return;
    const e = Ae(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(A("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(A("properties"))) {
      const t = this.properties, n = [...ke(t), ...xe(t)];
      for (const a of n) this.createProperty(a, t[a]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const t = litPropertyMetadata.get(e);
      if (t !== void 0) for (const [n, a] of t) this.elementProperties.set(n, a);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t, n] of this.elementProperties) {
      const a = this._$Eu(t, n);
      a !== void 0 && this._$Eh.set(a, t);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const t = [];
    if (Array.isArray(e)) {
      const n = new Set(e.flat(1 / 0).reverse());
      for (const a of n) t.unshift(Q(a));
    } else e !== void 0 && t.push(Q(e));
    return t;
  }
  static _$Eu(e, t) {
    const n = t.attribute;
    return n === !1 ? void 0 : typeof n == "string" ? n : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    var e;
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), (e = this.constructor.l) == null || e.forEach((t) => t(this));
  }
  addController(e) {
    var t;
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(e), this.renderRoot !== void 0 && this.isConnected && ((t = e.hostConnected) == null || t.call(e));
  }
  removeController(e) {
    var t;
    (t = this._$EO) == null || t.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
    for (const n of t.keys()) this.hasOwnProperty(n) && (e.set(n, this[n]), delete this[n]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return ve(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    var e;
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(!0), (e = this._$EO) == null || e.forEach((t) => {
      var n;
      return (n = t.hostConnected) == null ? void 0 : n.call(t);
    });
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    var e;
    (e = this._$EO) == null || e.forEach((t) => {
      var n;
      return (n = t.hostDisconnected) == null ? void 0 : n.call(t);
    });
  }
  attributeChangedCallback(e, t, n) {
    this._$AK(e, n);
  }
  _$ET(e, t) {
    var o;
    const n = this.constructor.elementProperties.get(e), a = this.constructor._$Eu(e, n);
    if (a !== void 0 && n.reflect === !0) {
      const i = (((o = n.converter) == null ? void 0 : o.toAttribute) !== void 0 ? n.converter : V).toAttribute(t, n.type);
      this._$Em = e, i == null ? this.removeAttribute(a) : this.setAttribute(a, i), this._$Em = null;
    }
  }
  _$AK(e, t) {
    var o, i;
    const n = this.constructor, a = n._$Eh.get(e);
    if (a !== void 0 && this._$Em !== a) {
      const l = n.getPropertyOptions(a), s = typeof l.converter == "function" ? { fromAttribute: l.converter } : ((o = l.converter) == null ? void 0 : o.fromAttribute) !== void 0 ? l.converter : V;
      this._$Em = a, this[a] = s.fromAttribute(t, l.type) ?? ((i = this._$Ej) == null ? void 0 : i.get(a)) ?? null, this._$Em = null;
    }
  }
  requestUpdate(e, t, n) {
    var a;
    if (e !== void 0) {
      const o = this.constructor, i = this[e];
      if (n ?? (n = o.getPropertyOptions(e)), !((n.hasChanged ?? le)(i, t) || n.useDefault && n.reflect && i === ((a = this._$Ej) == null ? void 0 : a.get(e)) && !this.hasAttribute(o._$Eu(e, n)))) return;
      this.C(e, t, n);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, t, { useDefault: n, reflect: a, wrapped: o }, i) {
    n && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(e) && (this._$Ej.set(e, i ?? t ?? this[e]), o !== !0 || i !== void 0) || (this._$AL.has(e) || (this.hasUpdated || n || (t = void 0), this._$AL.set(e, t)), a === !0 && this._$Em !== e && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (t) {
      Promise.reject(t);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    var n;
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [o, i] of this._$Ep) this[o] = i;
        this._$Ep = void 0;
      }
      const a = this.constructor.elementProperties;
      if (a.size > 0) for (const [o, i] of a) {
        const { wrapped: l } = i, s = this[o];
        l !== !0 || this._$AL.has(o) || s === void 0 || this.C(o, void 0, i, s);
      }
    }
    let e = !1;
    const t = this._$AL;
    try {
      e = this.shouldUpdate(t), e ? (this.willUpdate(t), (n = this._$EO) == null || n.forEach((a) => {
        var o;
        return (o = a.hostUpdate) == null ? void 0 : o.call(a);
      }), this.update(t)) : this._$EM();
    } catch (a) {
      throw e = !1, this._$EM(), a;
    }
    e && this._$AE(t);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    var t;
    (t = this._$EO) == null || t.forEach((n) => {
      var a;
      return (a = n.hostUpdated) == null ? void 0 : a.call(n);
    }), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t) => this._$ET(t, this[t]))), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[A("elementProperties")] = /* @__PURE__ */ new Map(), y[A("finalized")] = /* @__PURE__ */ new Map(), L == null || L({ ReactiveElement: y }), (p.reactiveElementVersions ?? (p.reactiveElementVersions = [])).push("2.1.0");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const S = globalThis, R = S.trustedTypes, Y = R ? R.createPolicy("lit-html", { createHTML: (r) => r }) : void 0, ce = "$lit$", m = `lit$${Math.random().toFixed(9).slice(2)}$`, de = "?" + m, Ee = `<${de}>`, $ = document, T = () => $.createComment(""), M = (r) => r === null || typeof r != "object" && typeof r != "function", K = Array.isArray, Ce = (r) => K(r) || typeof (r == null ? void 0 : r[Symbol.iterator]) == "function", j = `[
\f\r]`, x = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ee = /-->/g, te = />/g, g = RegExp(`>|${j}(?:([^\\s"'>=/]+)(${j}*=${j}*(?:[^
\f\r"'\`<>=]|("|')|))|$)`, "g"), ne = /'/g, ae = /"/g, he = /^(?:script|style|textarea|title)$/i, Te = (r) => (e, ...t) => ({ _$litType$: r, strings: e, values: t }), H = Te(1), _ = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), re = /* @__PURE__ */ new WeakMap(), v = $.createTreeWalker($, 129);
function ue(r, e) {
  if (!K(r) || !r.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return Y !== void 0 ? Y.createHTML(e) : e;
}
const Me = (r, e) => {
  const t = r.length - 1, n = [];
  let a, o = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", i = x;
  for (let l = 0; l < t; l++) {
    const s = r[l];
    let h, u, c = -1, f = 0;
    for (; f < s.length && (i.lastIndex = f, u = i.exec(s), u !== null); ) f = i.lastIndex, i === x ? u[1] === "!--" ? i = ee : u[1] !== void 0 ? i = te : u[2] !== void 0 ? (he.test(u[2]) && (a = RegExp("</" + u[2], "g")), i = g) : u[3] !== void 0 && (i = g) : i === g ? u[0] === ">" ? (i = a ?? x, c = -1) : u[1] === void 0 ? c = -2 : (c = i.lastIndex - u[2].length, h = u[1], i = u[3] === void 0 ? g : u[3] === '"' ? ae : ne) : i === ae || i === ne ? i = g : i === ee || i === te ? i = x : (i = g, a = void 0);
    const b = i === g && r[l + 1].startsWith("/>") ? " " : "";
    o += i === x ? s + Ee : c >= 0 ? (n.push(h), s.slice(0, c) + ce + s.slice(c) + m + b) : s + m + (c === -2 ? l : b);
  }
  return [ue(r, o + (r[t] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), n];
};
class z {
  constructor({ strings: e, _$litType$: t }, n) {
    let a;
    this.parts = [];
    let o = 0, i = 0;
    const l = e.length - 1, s = this.parts, [h, u] = Me(e, t);
    if (this.el = z.createElement(h, n), v.currentNode = this.el.content, t === 2 || t === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (a = v.nextNode()) !== null && s.length < l; ) {
      if (a.nodeType === 1) {
        if (a.hasAttributes()) for (const c of a.getAttributeNames()) if (c.endsWith(ce)) {
          const f = u[i++], b = a.getAttribute(c).split(m), U = /([.?@])?(.*)/.exec(f);
          s.push({ type: 1, index: o, name: U[2], strings: b, ctor: U[1] === "." ? Pe : U[1] === "?" ? Ue : U[1] === "@" ? He : N }), a.removeAttribute(c);
        } else c.startsWith(m) && (s.push({ type: 6, index: o }), a.removeAttribute(c));
        if (he.test(a.tagName)) {
          const c = a.textContent.split(m), f = c.length - 1;
          if (f > 0) {
            a.textContent = R ? R.emptyScript : "";
            for (let b = 0; b < f; b++) a.append(c[b], T()), v.nextNode(), s.push({ type: 2, index: ++o });
            a.append(c[f], T());
          }
        }
      } else if (a.nodeType === 8) if (a.data === de) s.push({ type: 2, index: o });
      else {
        let c = -1;
        for (; (c = a.data.indexOf(m, c + 1)) !== -1; ) s.push({ type: 7, index: o }), c += m.length - 1;
      }
      o++;
    }
  }
  static createElement(e, t) {
    const n = $.createElement("template");
    return n.innerHTML = e, n;
  }
}
function k(r, e, t = r, n) {
  var i, l;
  if (e === _) return e;
  let a = n !== void 0 ? (i = t._$Co) == null ? void 0 : i[n] : t._$Cl;
  const o = M(e) ? void 0 : e._$litDirective$;
  return (a == null ? void 0 : a.constructor) !== o && ((l = a == null ? void 0 : a._$AO) == null || l.call(a, !1), o === void 0 ? a = void 0 : (a = new o(r), a._$AT(r, t, n)), n !== void 0 ? (t._$Co ?? (t._$Co = []))[n] = a : t._$Cl = a), a !== void 0 && (e = k(r, a._$AS(r, e.values), a, n)), e;
}
class ze {
  constructor(e, t) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: t }, parts: n } = this._$AD, a = ((e == null ? void 0 : e.creationScope) ?? $).importNode(t, !0);
    v.currentNode = a;
    let o = v.nextNode(), i = 0, l = 0, s = n[0];
    for (; s !== void 0; ) {
      if (i === s.index) {
        let h;
        s.type === 2 ? h = new P(o, o.nextSibling, this, e) : s.type === 1 ? h = new s.ctor(o, s.name, s.strings, this, e) : s.type === 6 && (h = new Oe(o, this, e)), this._$AV.push(h), s = n[++l];
      }
      i !== (s == null ? void 0 : s.index) && (o = v.nextNode(), i++);
    }
    return v.currentNode = $, a;
  }
  p(e) {
    let t = 0;
    for (const n of this._$AV) n !== void 0 && (n.strings !== void 0 ? (n._$AI(e, n, t), t += n.strings.length - 2) : n._$AI(e[t])), t++;
  }
}
class P {
  get _$AU() {
    var e;
    return ((e = this._$AM) == null ? void 0 : e._$AU) ?? this._$Cv;
  }
  constructor(e, t, n, a) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = a, this._$Cv = (a == null ? void 0 : a.isConnected) ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const t = this._$AM;
    return t !== void 0 && (e == null ? void 0 : e.nodeType) === 11 && (e = t.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, t = this) {
    e = k(this, e, t), M(e) ? e === d || e == null || e === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : e !== this._$AH && e !== _ && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : Ce(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== d && M(this._$AH) ? this._$AA.nextSibling.data = e : this.T($.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    var o;
    const { values: t, _$litType$: n } = e, a = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = z.createElement(ue(n.h, n.h[0]), this.options)), n);
    if (((o = this._$AH) == null ? void 0 : o._$AD) === a) this._$AH.p(t);
    else {
      const i = new ze(a, this), l = i.u(this.options);
      i.p(t), this.T(l), this._$AH = i;
    }
  }
  _$AC(e) {
    let t = re.get(e.strings);
    return t === void 0 && re.set(e.strings, t = new z(e)), t;
  }
  k(e) {
    K(this._$AH) || (this._$AH = [], this._$AR());
    const t = this._$AH;
    let n, a = 0;
    for (const o of e) a === t.length ? t.push(n = new P(this.O(T()), this.O(T()), this, this.options)) : n = t[a], n._$AI(o), a++;
    a < t.length && (this._$AR(n && n._$AB.nextSibling, a), t.length = a);
  }
  _$AR(e = this._$AA.nextSibling, t) {
    var n;
    for ((n = this._$AP) == null ? void 0 : n.call(this, !1, !0, t); e && e !== this._$AB; ) {
      const a = e.nextSibling;
      e.remove(), e = a;
    }
  }
  setConnected(e) {
    var t;
    this._$AM === void 0 && (this._$Cv = e, (t = this._$AP) == null || t.call(this, e));
  }
}
class N {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, t, n, a, o) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = e, this.name = t, this._$AM = a, this.options = o, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(new String()), this.strings = n) : this._$AH = d;
  }
  _$AI(e, t = this, n, a) {
    const o = this.strings;
    let i = !1;
    if (o === void 0) e = k(this, e, t, 0), i = !M(e) || e !== this._$AH && e !== _, i && (this._$AH = e);
    else {
      const l = e;
      let s, h;
      for (e = o[0], s = 0; s < o.length - 1; s++) h = k(this, l[n + s], t, s), h === _ && (h = this._$AH[s]), i || (i = !M(h) || h !== this._$AH[s]), h === d ? e = d : e !== d && (e += (h ?? "") + o[s + 1]), this._$AH[s] = h;
    }
    i && !a && this.j(e);
  }
  j(e) {
    e === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class Pe extends N {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === d ? void 0 : e;
  }
}
class Ue extends N {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== d);
  }
}
class He extends N {
  constructor(e, t, n, a, o) {
    super(e, t, n, a, o), this.type = 5;
  }
  _$AI(e, t = this) {
    if ((e = k(this, e, t, 0) ?? d) === _) return;
    const n = this._$AH, a = e === d && n !== d || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, o = e !== d && (n === d || a);
    a && this.element.removeEventListener(this.name, this, n), o && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    var t;
    typeof this._$AH == "function" ? this._$AH.call(((t = this.options) == null ? void 0 : t.host) ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Oe {
  constructor(e, t, n) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    k(this, e);
  }
}
const I = S.litHtmlPolyfillSupport;
I == null || I(z, P), (S.litHtmlVersions ?? (S.litHtmlVersions = [])).push("3.3.0");
const Re = (r, e, t) => {
  const n = (t == null ? void 0 : t.renderBefore) ?? e;
  let a = n._$litPart$;
  if (a === void 0) {
    const o = (t == null ? void 0 : t.renderBefore) ?? null;
    n._$litPart$ = a = new P(e.insertBefore(T(), o), o, void 0, t ?? {});
  }
  return a._$AI(r), a;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const w = globalThis;
let E = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var t;
    const e = super.createRenderRoot();
    return (t = this.renderOptions).renderBefore ?? (t.renderBefore = e.firstChild), e;
  }
  update(e) {
    const t = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Re(t, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    var e;
    super.connectedCallback(), (e = this._$Do) == null || e.setConnected(!0);
  }
  disconnectedCallback() {
    var e;
    super.disconnectedCallback(), (e = this._$Do) == null || e.setConnected(!1);
  }
  render() {
    return _;
  }
};
var ie;
E._$litElement$ = !0, E.finalized = !0, (ie = w.litElementHydrateSupport) == null || ie.call(w, { LitElement: E });
const W = w.litElementPolyfillSupport;
W == null || W({ LitElement: E });
(w.litElementVersions ?? (w.litElementVersions = [])).push("4.2.0");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const fe = { ATTRIBUTE: 1, CHILD: 2 }, be = (r) => (...e) => ({ _$litDirective$: r, values: e });
class me {
  constructor(e) {
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AT(e, t, n) {
    this._$Ct = e, this._$AM = t, this._$Ci = n;
  }
  _$AS(e, t) {
    return this.update(e, t);
  }
  update(e, t) {
    return this.render(...t);
  }
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
let q = class extends me {
  constructor(e) {
    if (super(e), this.it = d, e.type !== fe.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
  }
  render(e) {
    if (e === d || e == null) return this._t = void 0, this.it = e;
    if (e === _) return e;
    if (typeof e != "string") throw Error(this.constructor.directiveName + "() called with a non-string value");
    if (e === this.it) return this._t;
    this.it = e;
    const t = [e];
    return t.raw = t, this._t = { _$litType$: this.constructor.resultType, strings: t, values: [] };
  }
};
q.directiveName = "unsafeHTML", q.resultType = 1;
const oe = be(q);
/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ne = be(class extends me {
  constructor(r) {
    var e;
    if (super(r), r.type !== fe.ATTRIBUTE || r.name !== "class" || ((e = r.strings) == null ? void 0 : e.length) > 2) throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.");
  }
  render(r) {
    return " " + Object.keys(r).filter((e) => r[e]).join(" ") + " ";
  }
  update(r, [e]) {
    var n, a;
    if (this.st === void 0) {
      this.st = /* @__PURE__ */ new Set(), r.strings !== void 0 && (this.nt = new Set(r.strings.join(" ").split(/\s/).filter((o) => o !== "")));
      for (const o in e) e[o] && !((n = this.nt) != null && n.has(o)) && this.st.add(o);
      return this.render(e);
    }
    const t = r.element.classList;
    for (const o of this.st) o in e || (t.remove(o), this.st.delete(o));
    for (const o in e) {
      const i = !!e[o];
      i === this.st.has(o) || (a = this.nt) != null && a.has(o) || (i ? (t.add(o), this.st.add(o)) : (t.remove(o), this.st.delete(o)));
    }
    return _;
  }
}), Be = '@font-face{font-family:Roboto Mono Web;font-style:normal;font-weight:300;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-300.woff2) format("woff2")}@font-face{font-family:Roboto Mono Web;font-style:normal;font-weight:400;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-regular.woff2) format("woff2")}@font-face{font-family:Roboto Mono Web;font-style:normal;font-weight:700;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-700.woff2) format("woff2")}@font-face{font-family:Roboto Mono Web;font-style:italic;font-weight:300;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-300italic.woff2) format("woff2")}@font-face{font-family:Roboto Mono Web;font-style:italic;font-weight:400;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-italic.woff2) format("woff2")}@font-face{font-family:Roboto Mono Web;font-style:italic;font-weight:700;font-display:fallback;src:url(../fonts/roboto-mono/roboto-mono-v5-latin-700italic.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:normal;font-weight:300;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-light-webfont.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:normal;font-weight:400;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-regular-webfont.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:normal;font-weight:700;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-bold-webfont.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:italic;font-weight:300;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-lightitalic-webfont.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:italic;font-weight:400;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-italic-webfont.woff2) format("woff2")}@font-face{font-family:Source Sans Pro Web;font-style:italic;font-weight:700;font-display:fallback;src:url(../fonts/source-sans-pro/sourcesanspro-bolditalic-webfont.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:normal;font-weight:300;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-Light.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:normal;font-weight:400;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-Regular.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:normal;font-weight:700;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-Bold.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:italic;font-weight:300;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-LightItalic.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:italic;font-weight:400;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-Italic.woff2) format("woff2")}@font-face{font-family:Merriweather Web;font-style:italic;font-weight:700;font-display:fallback;src:url(../fonts/merriweather/Latin-Merriweather-BoldItalic.woff2) format("woff2")}.usa-media-block{align-items:flex-start;display:flex}.usa-media-block__img{flex-shrink:0;margin-right:.5rem}.usa-media-block__body{flex:1 1 0%}.usa-banner{font-family:Source Sans Pro Web,Helvetica Neue,Helvetica,Roboto,Arial,sans-serif;font-size:1.06rem;line-height:1.5;background-color:#f0f0f0}@media all and (min-width: 40em){.usa-banner{font-size:.87rem;padding-bottom:0rem}}.usa-banner .usa-accordion{font-family:Source Sans Pro Web,Helvetica Neue,Helvetica,Roboto,Arial,sans-serif;font-size:1.06rem;line-height:1.5}.usa-banner .grid-row{display:flex;flex-wrap:wrap}.usa-banner .grid-row.grid-gap-lg{margin-left:-.75rem;margin-right:-.75rem}.usa-banner .grid-row.grid-gap-lg>*{padding-left:.75rem;padding-right:.75rem}@media all and (min-width: 40em){.usa-banner .grid-row .tablet\\:grid-col-6{flex:0 1 auto;width:50%}}.usa-banner__header,.usa-banner__content{color:#1b1b1b}.usa-banner__content{margin-left:auto;margin-right:auto;max-width:64rem;padding-right:1rem;padding-left:1rem;background-color:transparent;font-size:1rem;overflow:hidden;padding:.25rem 1rem 1rem .5rem;width:100%}@media all and (min-width: 64em){.usa-banner__content{padding-left:2rem;padding-right:2rem}}@media all and (min-width: 40em){.usa-banner__content{padding-bottom:1.5rem;padding-top:1.5rem}}.usa-banner__content p:first-child{margin:0}.usa-banner__guidance{display:flex;align-items:flex-start;max-width:64ex;padding-top:1rem}@media all and (min-width: 40em){.usa-banner__guidance{padding-top:0rem}}.usa-banner__lock-image{height:1.5ex;width:1.21875ex}.usa-banner__lock-image path{fill:currentColor}@media (forced-colors: active){.usa-banner__lock-image path{fill:CanvasText}}.usa-banner__inner{margin-left:auto;margin-right:auto;max-width:64rem;padding-left:1rem;padding-right:1rem;display:flex;flex-wrap:wrap;align-items:flex-start;padding-right:0rem}@media all and (min-width: 64em){.usa-banner__inner{padding-left:2rem;padding-right:2rem}}@media all and (min-width: 40em){.usa-banner__inner{align-items:center}}.usa-banner__header{padding-bottom:.5rem;padding-top:.5rem;font-size:.8rem;font-weight:400;min-height:3rem;position:relative}@media all and (min-width: 40em){.usa-banner__header{padding-bottom:.25rem;padding-top:.25rem;min-height:0}}.usa-banner__header-text{margin-bottom:0;margin-top:0;font-size:.8rem;line-height:1.1}.usa-banner__header-action{color:#005ea2;line-height:1.1;margin-bottom:0rem;margin-top:2px;text-decoration:underline}.usa-banner__header-action:after{background-image:url(../img/usa-icons/expand_more.svg);background-repeat:no-repeat;background-position:center center;background-size:1rem 1rem;display:inline-block;height:1rem;width:1rem;content:"";vertical-align:middle;margin-left:auto}@supports (mask: url()){.usa-banner__header-action:after{background:none;background-color:#005ea2;-webkit-mask-image:url(../img/usa-icons/expand_more.svg),linear-gradient(transparent,transparent);mask-image:url(../img/usa-icons/expand_more.svg),linear-gradient(transparent,transparent);-webkit-mask-position:center center;mask-position:center center;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:1rem 1rem;mask-size:1rem 1rem}.usa-banner__header-action:after:hover{background-color:#1a4480}}.usa-banner__header-action:hover:after{content:"";background-color:#1a4480}.usa-banner__header-action:visited{color:#54278f}.usa-banner__header-action:hover,.usa-banner__header-action:active{color:#1a4480}@media all and (min-width: 40em){.usa-banner__header-action{display:none}}@media (forced-colors: active){.usa-banner__header-action{color:LinkText}.usa-banner__header-action:after{background-color:ButtonText}}.usa-banner__header-flag{float:left;margin-right:.5rem;width:1rem}@media all and (min-width: 40em){.usa-banner__header-flag{margin-right:.5rem;padding-top:0rem}}.usa-banner__header--expanded{padding-right:3.5rem}@media all and (min-width: 40em){.usa-banner__header--expanded{background-color:transparent;display:block;font-size:.8rem;font-weight:400;min-height:0rem;padding-right:0rem}}.usa-banner__header--expanded .usa-banner__inner{margin-left:0rem}@media all and (min-width: 40em){.usa-banner__header--expanded .usa-banner__inner{margin-left:auto}}.usa-banner__header--expanded .usa-banner__header-action{display:none}.usa-banner__button{background-color:transparent;border:0;border-radius:0;box-shadow:none;font-weight:400;justify-content:normal;text-align:left;margin:0;padding:0;left:0;position:absolute;bottom:0;top:0;text-decoration:underline;color:#005ea2;display:block;font-size:.8rem;height:auto;line-height:1.1;padding-top:0rem;padding-left:0rem;text-decoration:none;width:auto}.usa-banner__button:hover{color:#1a4480}.usa-banner__button:active{color:#162e51}.usa-banner__button:focus{outline:.25rem solid #2491ff;outline-offset:0rem}.usa-banner__button:hover,.usa-banner__button.usa-button--hover,.usa-banner__button:disabled:hover,.usa-banner__button[aria-disabled=true]:hover,.usa-banner__button:disabled.usa-button--hover,.usa-banner__button[aria-disabled=true].usa-button--hover,.usa-banner__button:active,.usa-banner__button.usa-button--active,.usa-banner__button:disabled:active,.usa-banner__button[aria-disabled=true]:active,.usa-banner__button:disabled.usa-button--active,.usa-banner__button[aria-disabled=true].usa-button--active,.usa-banner__button:disabled:focus,.usa-banner__button[aria-disabled=true]:focus,.usa-banner__button:disabled.usa-focus,.usa-banner__button[aria-disabled=true].usa-focus,.usa-banner__button:disabled,.usa-banner__button[aria-disabled=true],.usa-banner__button.usa-button--disabled{background-color:transparent;box-shadow:none;text-decoration:underline}.usa-banner__button.usa-button--hover{color:#1a4480}.usa-banner__button.usa-button--active{color:#162e51}.usa-banner__button:disabled,.usa-banner__button[aria-disabled=true],.usa-banner__button:disabled:hover,.usa-banner__button[aria-disabled=true]:hover,.usa-banner__button[aria-disabled=true]:focus{color:#757575}@media (forced-colors: active){.usa-banner__button:disabled,.usa-banner__button[aria-disabled=true],.usa-banner__button:disabled:hover,.usa-banner__button[aria-disabled=true]:hover,.usa-banner__button[aria-disabled=true]:focus{color:GrayText}}.usa-banner__button:visited{color:#54278f}.usa-banner__button:hover,.usa-banner__button:active{color:#1a4480}@media all and (max-width: 39.99em){.usa-banner__button{width:100%}.usa-banner__button:enabled:focus{outline-offset:-.25rem}}@media all and (min-width: 40em){.usa-banner__button{color:#005ea2;position:static;bottom:auto;left:auto;right:auto;top:auto;display:inline;margin-left:.5rem;position:relative}.usa-banner__button:after{background-image:url(../img/usa-icons/expand_more.svg);background-repeat:no-repeat;background-position:center center;background-size:1rem 1rem;display:inline-block;height:1rem;width:1rem;content:"";vertical-align:middle;margin-left:2px}@supports (mask: url()){.usa-banner__button:after{background:none;background-color:#005ea2;-webkit-mask-image:url(../img/usa-icons/expand_more.svg),linear-gradient(transparent,transparent);mask-image:url(../img/usa-icons/expand_more.svg),linear-gradient(transparent,transparent);-webkit-mask-position:center center;mask-position:center center;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:1rem 1rem;mask-size:1rem 1rem}.usa-banner__button:after:hover{background-color:#1a4480}}.usa-banner__button:hover:after{content:"";background-color:#1a4480}.usa-banner__button:visited{color:#54278f}.usa-banner__button:hover,.usa-banner__button:active{color:#1a4480}.usa-banner__button:after,.usa-banner__button:hover:after{position:absolute}}@media (min-width: 40em) and (forced-colors: active){.usa-banner__button:after,.usa-banner__button:hover:after{background-color:ButtonText}}@media all and (min-width: 40em){.usa-banner__button:hover{text-decoration:none}}.usa-banner__button[aria-expanded=false],.usa-banner__button[aria-expanded=false]:hover,.usa-banner__button[aria-expanded=true],.usa-banner__button[aria-expanded=true]:hover{background-image:none}@media (forced-colors: active){.usa-banner__button[aria-expanded=false]:before,.usa-banner__button[aria-expanded=false]:hover:before,.usa-banner__button[aria-expanded=true]:before,.usa-banner__button[aria-expanded=true]:hover:before{content:none}}@media all and (max-width: 39.99em){.usa-banner__button[aria-expanded=true]:after{background-image:url(../img/usa-icons/close.svg);background-repeat:no-repeat;background-position:center center;background-size:1.5rem 1.5rem;display:inline-block;height:3rem;width:3rem;content:"";vertical-align:middle;margin-left:0rem}@supports (mask: url()){.usa-banner__button[aria-expanded=true]:after{background:none;background-color:#005ea2;-webkit-mask-image:url(../img/usa-icons/close.svg),linear-gradient(transparent,transparent);mask-image:url(../img/usa-icons/close.svg),linear-gradient(transparent,transparent);-webkit-mask-position:center center;mask-position:center center;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:1.5rem 1.5rem;mask-size:1.5rem 1.5rem}}.usa-banner__button[aria-expanded=true]:before{bottom:0;top:0;position:absolute;right:0;background-color:#dfe1e2;content:"";display:block;height:3rem;width:3rem}.usa-banner__button[aria-expanded=true]:after{bottom:0;top:0;position:absolute;right:0}}@media all and (min-width: 40em){.usa-banner__button[aria-expanded=true]{height:auto;padding:0rem;position:relative}.usa-banner__button[aria-expanded=true]:after{background-image:url(../img/usa-icons/expand_less.svg);background-repeat:no-repeat;background-position:center center;background-size:1rem 1rem;display:inline-block;height:1rem;width:1rem;content:"";vertical-align:middle;margin-left:2px}@supports (mask: url()){.usa-banner__button[aria-expanded=true]:after{background:none;background-color:#005ea2;-webkit-mask-image:url(../img/usa-icons/expand_less.svg),linear-gradient(transparent,transparent);mask-image:url(../img/usa-icons/expand_less.svg),linear-gradient(transparent,transparent);-webkit-mask-position:center center;mask-position:center center;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:1rem 1rem;mask-size:1rem 1rem}.usa-banner__button[aria-expanded=true]:after:hover{background-color:#1a4480}}.usa-banner__button[aria-expanded=true]:hover:after{content:"";background-color:#1a4480}.usa-banner__button[aria-expanded=true]:after,.usa-banner__button[aria-expanded=true]:hover:after{position:absolute}}@media (min-width: 40em) and (forced-colors: active){.usa-banner__button[aria-expanded=true]:after,.usa-banner__button[aria-expanded=true]:hover:after{background-color:ButtonText}}.usa-banner__button-text{position:absolute;left:-999em;right:auto;text-decoration:underline}@media all and (min-width: 40em){.usa-banner__button-text{position:static;display:inline}}@media (forced-colors: active){.usa-banner__button-text{color:LinkText}}.usa-banner__icon{width:2.5rem}.usa-js-loading .usa-banner__content{position:absolute;left:-999em;right:auto}', Le = `:host{--icon-lock: url("data:image/svg+xml,%3c?xml%20version='1.0'%20encoding='UTF-8'?%3e%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='52'%20height='64'%20viewBox='0%200%2052%2064'%3e%3ctitle%3elock%3c/title%3e%3cpath%20fill='%231B1B1B'%20fill-rule='evenodd'%20d='M26%200c10.493%200%2019%208.507%2019%2019v9h3a4%204%200%200%201%204%204v28a4%204%200%200%201-4%204H4a4%204%200%200%201-4-4V32a4%204%200%200%201%204-4h3v-9C7%208.507%2015.507%200%2026%200zm0%208c-5.979%200-10.843%204.77-10.996%2010.712L15%2019v9h22v-9c0-6.075-4.925-11-11-11z'/%3e%3c/svg%3e");--icon-chevron-up: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20height='24'%20viewBox='0%200%2024%2024'%20width='24'%3e%3cpath%20d='M0%200h24v24H0z'%20fill='none'/%3e%3cpath%20fill='%23fff'%20d='m12%208-6%206%201.41%201.41L12%2010.83l4.59%204.58L18%2014z'/%3e%3c/svg%3e");--icon-chevron-down: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20height='24'%20viewBox='0%200%2024%2024'%20width='24'%3e%3cpath%20d='M0%200h24v24H0z'%20fill='none'/%3e%3cpath%20fill='%23fff'%20d='M16.59%208.59%2012%2013.17%207.41%208.59%206%2010l6%206%206-6z'/%3e%3c/svg%3e");--icon-close: url("data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20height='24'%20viewBox='0%200%2024%2024'%20width='24'%3e%3cpath%20d='M0%200h24v24H0z'%20fill='none'/%3e%3cpath%20fill='%23fff'%20d='M19%206.41%2017.59%205%2012%2010.59%206.41%205%205%206.41%2010.59%2012%205%2017.59%206.41%2019%2012%2013.41%2017.59%2019%2019%2017.59%2013.41%2012z'/%3e%3c/svg%3e");--theme-banner-background-color: var(--usa-base-lightest, #f0f0f0);--theme-banner-font-family: var(--usa-font-ui, system-ui, sans-serif);--theme-banner-text-color: var(--usa-text-base, #1b1b1b);--theme-banner-link-color: var(--theme-link-color, #005ea2);--theme-banner-link-color-hover: var(--theme-link-hover-color, #1a4480);--theme-banner-chevron-color: var(--theme-banner-link-color, #005ea2)}*{box-sizing:border-box}.usa-banner{background-color:var(--theme-banner-background-color);color:var(--theme-banner-text-color);font-family:var(--theme-banner-font-family)}.usa-banner__header,.usa-banner__content{color:var(--theme-banner-text-color)}.usa-banner__inner{flex-wrap:nowrap}.usa-banner .usa-accordion{font-family:inherit}.usa-banner__button{color:var(--theme-banner-link-color);cursor:pointer;font-family:inherit}.usa-banner__button:hover{color:var(--theme-banner-link-hover-color)}.usa-banner__button:after,.usa-banner__header-action:after{-webkit-mask-image:var(--icon-chevron-down);mask-image:var(--icon-chevron-down)}.usa-banner__button[aria-expanded=true]:after{-webkit-mask-image:var(--icon-close);mask-image:var(--icon-close)}.usa-banner__icon-lock{background-position:center;background-repeat:no-repeat;background-size:cover;display:inline-block;height:1.5ex;background-image:var(--icon-lock);-webkit-mask-image:var(--icon-lock);mask-image:var(--icon-lock);-webkit-mask-position:center;mask-position:center;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-size:cover;mask-size:cover;vertical-align:middle;width:1.21875ex}@media all and (min-width: 40em){:host{--chevron-width: 1rem}.usa-banner__button,.usa-banner__button[aria-expanded=true]{padding-inline-end:var(--chevron-width)}.usa-banner__button:after{background-color:var(--theme-banner-chevron-color);top:0;right:0}.usa-banner__button[aria-expanded=true]:after{-webkit-mask-image:var(--icon-chevron-up);mask-image:var(--icon-chevron-up)}}`, je = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAAAsBAMAAAAncaPMAAAAAXNSR0IArs4c6QAAABtQTFRF////4EAg2z8g2z8f2z4f2j4fHjSyHjOxHTOxQEYPwgAAAIdJREFUeNrNkUENxDAMBEOhFJaCKZiCKZhCKBj2ebV3rdR71+pIq+Qxj1GyqjJ3U8VlHkc07hFm0awBYe91juq6MSI0yhSAEgkzJ4TMKiXyzFw3pgR9lmIBJlqj2AmBedf+IycExmlKZVzvZEJ4A0oBrjBl/m6PCy95B3fFAN6YuQPxhbcB4QMkEj04wQXD5wAAAABJRU5ErkJggg==", Ie = "data:image/svg+xml,%3c?xml%20version='1.0'%20encoding='UTF-8'?%3e%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='64'%20height='64'%20viewBox='0%200%2064%2064'%3e%3ctitle%3eicon-dot-gov%3c/title%3e%3cpath%20fill='%232378C3'%20fill-rule='evenodd'%20d='m32%200c17.7%200%2032%2014.3%2032%2032s-14.3%2032-32%2032-32-14.3-32-32%2014.3-32%2032-32zm0%201.2c-17%200-30.8%2013.8-30.8%2030.8s13.8%2030.8%2030.8%2030.8%2030.8-13.8%2030.8-30.8-13.8-30.8-30.8-30.8zm11.4%2038.9c.5%200%20.9.4.9.8v1.6h-24.6v-1.6c0-.5.4-.8.9-.8zm-17.1-12.3v9.8h1.6v-9.8h3.3v9.8h1.6v-9.8h3.3v9.8h1.6v-9.8h3.3v9.8h.8c.5%200%20.9.4.9.8v.8h-21.4v-.8c0-.5.4-.8.9-.8h.8v-9.8zm5.7-8.2%2012.3%204.9v1.6h-1.6c0%20.5-.4.8-.9.8h-19.6c-.5%200-.9-.4-.9-.8h-1.6v-1.6s12.3-4.9%2012.3-4.9z'/%3e%3c/svg%3e", We = "data:image/svg+xml,%3c?xml%20version='1.0'%20encoding='UTF-8'?%3e%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='64'%20height='64'%20viewBox='0%200%2064%2064'%3e%3ctitle%3eicon-https%3c/title%3e%3cpath%20fill='%23719F2A'%20fill-rule='evenodd'%20d='M32%200c17.673%200%2032%2014.327%2032%2032%200%2017.673-14.327%2032-32%2032C14.327%2064%200%2049.673%200%2032%200%2014.327%2014.327%200%2032%200zm0%201.208C14.994%201.208%201.208%2014.994%201.208%2032S14.994%2062.792%2032%2062.792%2062.792%2049.006%2062.792%2032%2049.006%201.208%2032%201.208zm0%2018.886a7.245%207.245%200%200%201%207.245%207.245v3.103h.52c.86%200%201.557.698%201.557%201.558v9.322c0%20.86-.697%201.558-1.557%201.558h-15.53c-.86%200-1.557-.697-1.557-1.558V32c0-.86.697-1.558%201.557-1.558h.52V27.34A7.245%207.245%200%200%201%2032%2020.094zm0%203.103a4.142%204.142%200%200%200-4.142%204.142v3.103h8.284V27.34A4.142%204.142%200%200%200%2032%2023.197z'/%3e%3c/svg%3e", C = class C extends E {
  toggle() {
    this.isOpen = !this.isOpen, this.shadowRoot.querySelector(".usa-banner__content").toggleAttribute("hidden");
  }
  constructor() {
    super(), this.lang = "en", this.isOpen = !1, this.tld = "gov", this.data = {
      en: {
        banner: {
          label: "Official website of the United States government",
          text: "An official website of the United States government",
          action: "Here's how you know"
        },
        domain: {
          heading: "Official websites use",
          text1: "A",
          text2: "website belongs to an official government organization in the United States."
        },
        https: {
          heading1: "Secure",
          heading2: "websites use HTTPS",
          text1: "A <strong>lock</strong>",
          text2: "or <strong>https://</strong> means you’ve safely connected to the",
          text3: "website. Share sensitive information only on official, secure websites."
        }
      },
      es: {
        banner: {
          label: "Un sitio oficial del Gobierno de Estados Unidos",
          text: "Un sitio oficial del Gobierno de Estados Unidos",
          action: "Así es como usted puede verificarlo"
        },
        domain: {
          heading: "Los sitios web oficiales usan",
          text1: "Un sitio web",
          text2: "pertenece a una organización oficial del Gobierno de Estados Unidos."
        },
        https: {
          heading1: "Los sitios web seguros",
          heading2: "usan HTTPS",
          text1: "Un <strong>candado</strong>",
          text2: "o <strong>https://</strong> significa que usted se conectó de forma segura a un sitio web",
          text3: "Comparta información sensible sólo en sitios web oficiales y seguros."
        }
      }
    };
  }
  // Get English or Spanish strings. Default to English if an unknown `lang` is passed.
  // Ex: <usa-banner lang="zy"></usa-banner>
  get _bannerText() {
    return this.data[this.lang] || this.data.en;
  }
  // Get the action text and use for both mobile & desktop buttons.
  get _actionText() {
    const e = this.querySelector('[slot="banner-action"]');
    return e == null ? void 0 : e.textContent;
  }
  domainTemplate(e) {
    const { domain: t } = this._bannerText;
    return H`
      <img
        class="usa-banner__icon usa-media-block__img"
        src="${Ie}"
        role="img"
        alt=""
        aria-hidden="true"
      />
      <div class="usa-media-block__body">
        <p>
          <strong>
            <slot name="domain-heading"> ${t.heading} .${e} </slot>
          </strong>
          <br />
          <slot name="domain-text">
            ${t.text1} <strong>.${e}</strong> ${t.text2}
          </slot>
        </p>
      </div>
    `;
  }
  static lockIcon() {
    return H`
      <span
        class="usa-banner__icon-lock"
        role="img"
        aria-label="Locked padlock icon"
        part="lock-icon"
      ></span>
    `;
  }
  httpsTemplate(e) {
    const { https: t } = this._bannerText;
    return H`
      <img
        class="usa-banner__icon usa-media-block__img"
        src="${We}"
        role="img"
        alt=""
        aria-hidden="true"
      />
      <div class="usa-media-block__body">
        <p>
          <strong>
            <slot name="https-heading">
              ${t.heading1} .${e} ${t.heading2}
            </slot> </strong
          ><br />
          <slot name="https-text">
            ${oe(t.text1)} (${C.lockIcon()})
            ${oe(t.text2)} .${e} ${t.text3}
          </slot>
        </p>
      </div>
    `;
  }
  render() {
    const e = { "usa-banner__header--expanded": this.isOpen }, t = this.tld === "mil" ? "mil" : "gov", { banner: n } = this._bannerText;
    return H`
      <section class="usa-banner" aria-label=${this.label || n.label}>
        <div class="usa-accordion">
          <header class="usa-banner__header ${Ne(e)}">
            <div class="usa-banner__inner">
              <div class="grid-col-auto">
                <img
                  aria-hidden="true"
                  class="usa-banner__header-flag"
                  src=${je}
                  alt=""
                />
              </div>
              <div
                class="grid-col-fill tablet:grid-col-auto"
                aria-hidden="true"
              >
                <p class="usa-banner__header-text">
                  <slot name="banner-text">${n.text}</slot>
                </p>
                <p class="usa-banner__header-action">
                  <slot name="banner-action">${n.action}</slot>
                </p>
              </div>
              <button
                type="button"
                class="usa-accordion__button usa-banner__button"
                aria-expanded="${this.isOpen}"
                aria-controls="gov-banner-default"
                @click="${this.toggle}"
              >
                <span class="usa-banner__button-text">
                  ${this._actionText || n.action}
                </span>
              </button>
            </div>
          </header>
          <div class="usa-banner__content usa-accordion__content" hidden>
            <div class="grid-row grid-gap-lg">
              <div class="usa-banner__guidance tablet:grid-col-6">
                ${this.domainTemplate(t)}
              </div>
              <div class="usa-banner__guidance tablet:grid-col-6">
                ${this.httpsTemplate(t)}
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }
};
B(C, "properties", {
  lang: {
    type: String,
    reflect: !0
  },
  data: { attribute: !1 },
  isOpen: { type: Boolean },
  classes: {},
  label: { type: String },
  tld: {
    type: String,
    reflect: !0
  }
}), B(C, "styles", [D(Be), D(Le)]);
let F = C;
customElements.define("usa-banner", F);
export {
  F as default
};
