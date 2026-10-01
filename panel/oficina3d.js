// La oficina 3D de Isa: una oficina en miniatura (estilo maqueta) donde cada agente es un
// robot que trabaja sentado en su escritorio. Cuando Isa lo llama, se levanta, camina
// hasta la mesa de reuniones bajo el holograma de Isa, trabaja ahí y luego vuelve.
//
// Uso:  const oficina = crearOficina(contenedor, { alTocarAgente(id) {} });
//       oficina.setEquipo(agentes) · convocar(id) · actividad(id, texto) · liberar(id)
//       oficina.isa("reposo" | "pensando" | "hablando") · mostrarResultado(url)
import { THREE, CSS2DRenderer, CSS2DObject } from "./vendor/three-paquete.js";

const MOVIMIENTO = !matchMedia("(prefers-reduced-motion: reduce)").matches;
const MESA = new THREE.Vector3(0, 0, 0.6);

// Puestos de trabajo: dónde se sienta cada robot y hacia dónde mira (ángulo en radianes).
const PUESTOS = [
  { x: -5.0, z: -3.75, giro: 0.25 }, { x: 4.4, z: -3.75, giro: -0.2 }, { x: -6.2, z: 0.9, giro: 1.15 },
  { x: 6.0, z: 1.3, giro: -0.75 }, { x: -6.2, z: 4.1, giro: 1.15 }, { x: 5.9, z: 4.4, giro: -0.9 },
  { x: -1.8, z: -3.75, giro: 0.1 }, { x: 1.3, z: -3.75, giro: 0 },
];
// Lugares alrededor de la mesa de reuniones (primero los del fondo a los lados del holograma,
// para que la cámara les vea la cara y Isa no los tape).
const LUGARES = [150, 282, 112, 320, 186, 246, 72, 0].map((g) => {
  const a = (g * Math.PI) / 180;
  return new THREE.Vector3(MESA.x + Math.sin(a) * 2.35, 0, MESA.z + Math.cos(a) * 2.35);
});

/* ---------------- utilidades ---------------- */
function lienzo(w, h, dibujar) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  dibujar(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function malla(geo, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true; return m;
}
const suave = (a, b, k) => a + (b - a) * k;
// Caja con esquinas redondeadas (para pies y piezas suaves)
function RoundedBox(w, h, d, r) {
  const f = new THREE.Shape(), x = -w / 2, y = -d / 2;
  f.moveTo(x + r, y); f.lineTo(x + w - r, y); f.quadraticCurveTo(x + w, y, x + w, y + r); f.lineTo(x + w, y + d - r);
  f.quadraticCurveTo(x + w, y + d, x + w - r, y + d); f.lineTo(x + r, y + d); f.quadraticCurveTo(x, y + d, x, y + d - r);
  f.lineTo(x, y + r); f.quadraticCurveTo(x, y, x + r, y);
  const g = new THREE.ExtrudeGeometry(f, { depth: h - r, bevelEnabled: true, bevelThickness: r / 2, bevelSize: r / 2, bevelSegments: 3, curveSegments: 6 });
  g.rotateX(-Math.PI / 2); g.translate(0, -(h - r) / 2, 0); return g;
}
function anguloHacia(desde, hacia) { return Math.atan2(hacia.x - desde.x, hacia.z - desde.z); }
function girarHacia(actual, meta, k) {
  let d = meta - actual; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2;
  return actual + d * k;
}
function semillaAzar(n) { let s = n * 9301 + 49297; return () => ((s = (s * 9301 + 49297) % 233280) / 233280); }

/* ---------------- materiales compartidos ---------------- */
const MAT = {
  piso: null,
  pared: new THREE.MeshStandardMaterial({ color: 0xe9eff9, roughness: 0.9 }),
  zocalo: new THREE.MeshStandardMaterial({ color: 0x3d7bff, roughness: 0.5 }),
  base: new THREE.MeshStandardMaterial({ color: 0x1a3a86, roughness: 0.6 }),
  blanco: new THREE.MeshPhysicalMaterial({ color: 0xf7f9fd, roughness: 0.35, clearcoat: 0.6, clearcoatRoughness: 0.3 }),
  gris: new THREE.MeshStandardMaterial({ color: 0xc8d4ea, roughness: 0.5, metalness: 0.2 }),
  metal: new THREE.MeshStandardMaterial({ color: 0x8b9ab8, roughness: 0.3, metalness: 0.8 }),
  oscuro: new THREE.MeshStandardMaterial({ color: 0x1d2740, roughness: 0.5, metalness: 0.3 }),
  tela: new THREE.MeshStandardMaterial({ color: 0x2b4c9b, roughness: 0.85 }),
  maceta: new THREE.MeshStandardMaterial({ color: 0xf2f5fb, roughness: 0.6 }),
  hoja: new THREE.MeshStandardMaterial({ color: 0x36b98a, roughness: 0.6, side: THREE.DoubleSide }),
  hoja2: new THREE.MeshStandardMaterial({ color: 0x2a9a73, roughness: 0.6, side: THREE.DoubleSide }),
  madera: new THREE.MeshStandardMaterial({ color: 0xd9b991, roughness: 0.7 }),
  cian: new THREE.MeshBasicMaterial({ color: 0x6fdcff, toneMapped: false }),
};

/* ---------------- el robot ---------------- */
function rolDe(agente) {
  const t = (agente.id + " " + (agente.que_hace || "")).toLowerCase();
  if (/scraper|busca|investig|lector/.test(agente.id) || /investigador/.test(t)) return "lupa";
  if (/creador|contenido|video|anuncio/.test(agente.id)) return "camara";
  if (/estrateg|plan|calendario/.test(agente.id)) return "tableta";
  if (/cliente|crm|venta|pedido/.test(t)) return "telefono";
  return "taza";
}

function crearRobot(agente, variante) {
  const color = new THREE.Color(agente.color);
  const m = {
    casco: new THREE.MeshPhysicalMaterial({ color: 0xf5f8fd, roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.12 }),
    junta: new THREE.MeshStandardMaterial({ color: 0x27324d, roughness: 0.4, metalness: 0.55 }),
    acento: new THREE.MeshStandardMaterial({ color, roughness: 0.35, emissive: color, emissiveIntensity: 0.18 }),
    visor: new THREE.MeshPhysicalMaterial({ color: 0x08101f, roughness: 0.06, clearcoat: 1, metalness: 0.3 }),
    luz: new THREE.MeshBasicMaterial({ color: color.clone().multiplyScalar(1.4), toneMapped: false }),
  };
  const raiz = new THREE.Group(); raiz.userData.agente = agente.id;
  const cadera = new THREE.Group(); cadera.position.y = 0.8; raiz.add(cadera);
  const cuerpo = new THREE.Group(); cadera.add(cuerpo);

  // Torso
  cuerpo.add(malla(new THREE.BoxGeometry(0.44, 0.16, 0.3), m.junta, 0, 0.02, 0));
  const torso = malla(new THREE.CapsuleGeometry(0.3, 0.3, 8, 20), m.casco, 0, 0.44, 0); torso.scale.set(1, 1, 0.78); cuerpo.add(torso);
  const cinturon = malla(new THREE.CylinderGeometry(0.305, 0.3, 0.07, 24), m.acento, 0, 0.2, 0); cinturon.scale.z = 0.78; cuerpo.add(cinturon);
  const nucleo = malla(new THREE.CircleGeometry(0.075, 24), m.luz, 0, 0.52, 0.238); cuerpo.add(nucleo);
  const aro = malla(new THREE.TorusGeometry(0.1, 0.016, 8, 28), m.junta, 0, 0.52, 0.232); cuerpo.add(aro);
  if (variante % 2 === 0) { // mochila con propulsores
    const mochila = malla(new THREE.BoxGeometry(0.34, 0.36, 0.16), m.casco, 0, 0.5, -0.27); cuerpo.add(mochila);
    [-0.09, 0.09].forEach((x) => cuerpo.add(malla(new THREE.CylinderGeometry(0.05, 0.065, 0.12, 14), m.acento, x, 0.28, -0.3)));
  } else { // placa de hombros
    const placa = malla(new THREE.BoxGeometry(0.62, 0.06, 0.32), m.acento, 0, 0.7, 0); cuerpo.add(placa);
  }

  // Cuello y cabeza
  cuerpo.add(malla(new THREE.CylinderGeometry(0.075, 0.09, 0.14, 14), m.junta, 0, 0.84, 0));
  const cabeza = new THREE.Group(); cabeza.position.y = 1.05; cuerpo.add(cabeza);
  let frente = 0.27, ojoY = 0;
  if (variante % 4 === 0) {          // cabeza redonda
    const c = malla(new THREE.SphereGeometry(0.3, 32, 24), m.casco); c.scale.set(1.12, 0.95, 1); cabeza.add(c);
    frente = 0.27;
  } else if (variante % 4 === 1) {   // cabeza de pantalla
    cabeza.add(malla(new THREE.BoxGeometry(0.6, 0.44, 0.44), m.casco));
    [-0.3, 0.3].forEach((x) => cabeza.add(malla(new THREE.CylinderGeometry(0.22, 0.22, 0.04, 24), m.casco, x, 0, 0).rotateZ(Math.PI / 2)));
    frente = 0.225;
  } else if (variante % 4 === 2) {   // cápsula horizontal
    const c = malla(new THREE.CapsuleGeometry(0.25, 0.22, 8, 24), m.casco); c.rotation.z = Math.PI / 2; c.scale.set(1, 1, 0.95); cabeza.add(c);
    frente = 0.24;
  } else {                           // domo
    cabeza.add(malla(new THREE.CylinderGeometry(0.28, 0.3, 0.3, 28), m.casco, 0, -0.04, 0));
    const domo = malla(new THREE.SphereGeometry(0.28, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), m.casco, 0, 0.11, 0); cabeza.add(domo);
    frente = 0.29; ojoY = -0.02;
  }
  const visor = malla(new THREE.CapsuleGeometry(0.12, 0.26, 8, 20), m.visor, 0, ojoY, frente - 0.04);
  visor.rotation.z = Math.PI / 2; visor.scale.set(1, 1, 0.45); cabeza.add(visor);
  const ojos = [-0.085, 0.085].map((x) => {
    const o = malla(new THREE.CapsuleGeometry(0.03, 0.045, 6, 12), m.luz, x, ojoY + 0.01, frente + 0.02);
    o.castShadow = false; cabeza.add(o); return o;
  });
  const sonrisa = malla(new THREE.TorusGeometry(0.055, 0.011, 8, 20, Math.PI), m.luz, 0, ojoY - 0.06, frente + 0.02);
  sonrisa.rotation.z = Math.PI; sonrisa.visible = false; cabeza.add(sonrisa);
  // Orejas / audífonos y antena
  if (variante % 3 !== 2) [-1, 1].forEach((s) => {
    const oreja = malla(new THREE.CylinderGeometry(0.085, 0.085, 0.07, 20), m.acento, s * 0.33, 0, 0); oreja.rotation.z = Math.PI / 2; cabeza.add(oreja);
  });
  const antena = new THREE.Group(); antena.position.set(variante % 3 === 1 ? 0.14 : 0, 0.26, 0); cabeza.add(antena);
  antena.add(malla(new THREE.CylinderGeometry(0.012, 0.012, 0.22, 8), m.junta, 0, 0.1, 0));
  const foco = malla(new THREE.SphereGeometry(0.045, 16, 12), m.luz, 0, 0.23, 0); antena.add(foco);
  if (variante % 3 === 2) { // cresta
    const cresta = malla(new THREE.BoxGeometry(0.06, 0.08, 0.4), m.acento, 0, 0.27, 0); cabeza.add(cresta);
  }

  // Brazos
  const hombros = [], codos = [], manos = [];
  [-1, 1].forEach((s) => {
    const hombro = new THREE.Group(); hombro.position.set(s * 0.42, 0.66, 0); cuerpo.add(hombro);
    hombro.add(malla(new THREE.SphereGeometry(0.1, 16, 12), m.junta));
    hombro.add(malla(new THREE.CapsuleGeometry(0.092, 0.18, 6, 14), m.casco, 0, -0.19, 0));
    const codo = new THREE.Group(); codo.position.y = -0.36; hombro.add(codo);
    codo.add(malla(new THREE.SphereGeometry(0.07, 14, 10), m.junta));
    codo.add(malla(new THREE.CapsuleGeometry(0.088, 0.16, 6, 14), m.casco, 0, -0.16, 0));
    codo.add(malla(new THREE.CylinderGeometry(0.093, 0.093, 0.045, 16), m.acento, 0, -0.1, 0));
    const mano = new THREE.Group(); mano.position.y = -0.33; codo.add(mano);
    const palma = malla(new THREE.SphereGeometry(0.1, 16, 12), m.junta); palma.scale.set(1, 1.1, 0.8); mano.add(palma);
    hombros.push(hombro); codos.push(codo); manos.push(mano);
  });
  // Piernas
  const muslos = [], rodillas = [];
  [-1, 1].forEach((s) => {
    const muslo = new THREE.Group(); muslo.position.set(s * 0.15, 0, 0); cadera.add(muslo);
    muslo.add(malla(new THREE.CapsuleGeometry(0.11, 0.18, 6, 14), m.casco, 0, -0.18, 0));
    const rodilla = new THREE.Group(); rodilla.position.y = -0.38; muslo.add(rodilla);
    rodilla.add(malla(new THREE.SphereGeometry(0.085, 14, 10), m.junta));
    rodilla.add(malla(new THREE.CapsuleGeometry(0.1, 0.16, 6, 14), m.casco, 0, -0.17, 0));
    const pie = malla(new RoundedBox(0.21, 0.1, 0.33, 0.04), m.junta, 0, -0.36, 0.05); rodilla.add(pie);
    rodilla.add(malla(new THREE.BoxGeometry(0.2, 0.03, 0.13), m.acento, 0, -0.315, 0.13));
    muslos.push(muslo); rodillas.push(rodilla);
  });

  // Objeto en la mano según su trabajo
  const objeto = new THREE.Group(); manos[1].add(objeto); objeto.position.set(0, -0.08, 0.06);
  const rol = rolDe(agente);
  if (rol === "lupa") {
    objeto.add(malla(new THREE.CylinderGeometry(0.02, 0.025, 0.2, 10), m.junta, 0, -0.08, 0));
    const anillo = malla(new THREE.TorusGeometry(0.1, 0.018, 10, 28), m.acento, 0, -0.27, 0); objeto.add(anillo);
    const vidrio = malla(new THREE.CircleGeometry(0.09, 24), new THREE.MeshPhysicalMaterial({ color: 0xbfeaff, transparent: true, opacity: 0.45, roughness: 0, side: THREE.DoubleSide }), 0, -0.27, 0);
    objeto.add(vidrio); objeto.rotation.x = -1.2;
  } else if (rol === "camara") {
    objeto.add(malla(new THREE.BoxGeometry(0.2, 0.14, 0.12), m.junta, 0, -0.06, 0.06));
    const lente = malla(new THREE.CylinderGeometry(0.05, 0.06, 0.1, 18), m.acento, 0, -0.06, 0.16); lente.rotation.x = Math.PI / 2; objeto.add(lente);
    objeto.add(malla(new THREE.SphereGeometry(0.015, 8, 8), new THREE.MeshBasicMaterial({ color: 0xff4d5e, toneMapped: false }), 0.07, 0.02, 0.06));
  } else if (rol === "tableta") {
    objeto.add(malla(new THREE.BoxGeometry(0.26, 0.34, 0.02), m.junta, 0, -0.12, 0.05));
    const pantalla = malla(new THREE.PlaneGeometry(0.22, 0.3), new THREE.MeshBasicMaterial({ map: pantallaTableta(agente.color), toneMapped: false }), 0, -0.12, 0.062);
    objeto.add(pantalla); objeto.rotation.x = -0.9;
  } else if (rol === "telefono") {
    objeto.add(malla(new THREE.BoxGeometry(0.09, 0.17, 0.02), m.junta, 0, -0.06, 0.04));
  } else {
    objeto.add(malla(new THREE.CylinderGeometry(0.05, 0.045, 0.11, 16), m.acento, 0, -0.04, 0.06));
  }
  objeto.visible = false;

  raiz.scale.setScalar(0.9);
  raiz.traverse((o) => { if (o.isMesh) o.userData.agente = agente.id; });
  return { raiz, cadera, cuerpo, cabeza, hombros, codos, muslos, rodillas, ojos, foco, sonrisa, nucleo, objeto, rol };
}
function pantallaTableta(color) {
  return lienzo(128, 176, (x, w, h) => {
    x.fillStyle = "#0b1a38"; x.fillRect(0, 0, w, h);
    x.fillStyle = color; x.fillRect(10, 12, 60, 8);
    for (let i = 0; i < 5; i++) { x.fillStyle = i % 2 ? "#3d7bff" : color; x.globalAlpha = .8; x.fillRect(10 + i * 22, 140 - (30 + i * 17 % 60), 14, 30 + i * 17 % 60); }
    x.globalAlpha = 1;
  });
}

/* ---------------- muebles ---------------- */
function pantallaLaptop(color, n) {
  const azar = semillaAzar(n + 3);
  return lienzo(256, 160, (x, w, h) => {
    x.fillStyle = "#0a1428"; x.fillRect(0, 0, w, h);
    x.fillStyle = color; x.fillRect(0, 0, w, 14);
    for (let i = 0; i < 9; i++) {
      x.fillStyle = ["#7fb2ff", color, "#cfe6ff", "#5be3b0"][i % 4]; x.globalAlpha = .85;
      x.fillRect(14 + (i % 3) * 10, 26 + i * 14, 40 + azar() * 150, 6);
    }
    x.globalAlpha = 1;
  });
}
function crearEscritorio(agente, n) {
  const g = new THREE.Group();
  const color = new THREE.Color(agente.color);
  // Mesa (frente hacia el robot = -z local; el robot se sienta en z = 0 mirando a +z)
  g.add(malla(new THREE.BoxGeometry(1.9, 0.06, 0.9), MAT.blanco, 0, 0.74, 0.85));
  [-0.9, 0.9].forEach((x) => g.add(malla(new THREE.BoxGeometry(0.05, 0.72, 0.8), MAT.gris, x, 0.36, 0.85)));
  g.add(malla(new THREE.BoxGeometry(1.75, 0.34, 0.03), MAT.gris, 0, 0.5, 1.25));
  g.add(malla(new THREE.BoxGeometry(1.9, 0.025, 0.02), new THREE.MeshBasicMaterial({ color, toneMapped: false }), 0, 0.73, 1.305));
  // Laptop mirando al robot
  const laptop = new THREE.Group(); laptop.position.set(0, 0.775, 0.78); g.add(laptop);
  laptop.add(malla(new THREE.BoxGeometry(0.56, 0.02, 0.38), MAT.metal));
  const tapa = new THREE.Group(); tapa.position.set(0, 0.01, 0.19); tapa.rotation.x = 0.32; laptop.add(tapa);
  tapa.add(malla(new THREE.BoxGeometry(0.56, 0.36, 0.015), MAT.metal, 0, 0.18, 0));
  const pantalla = new THREE.Mesh(new THREE.PlaneGeometry(0.52, 0.32), new THREE.MeshBasicMaterial({ map: pantallaLaptop(agente.color, n), toneMapped: false }));
  pantalla.position.set(0, 0.18, -0.009); pantalla.rotation.y = Math.PI; tapa.add(pantalla);
  const logo = new THREE.Mesh(new THREE.CircleGeometry(0.045, 20), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }));
  logo.position.set(0, 0.18, 0.009); tapa.add(logo);
  // Taza, libreta y lámpara
  g.add(malla(new THREE.CylinderGeometry(0.05, 0.045, 0.11, 16), new THREE.MeshStandardMaterial({ color, roughness: .4 }), 0.62, 0.825, 0.65));
  g.add(malla(new THREE.BoxGeometry(0.24, 0.015, 0.32), MAT.oscuro, -0.55, 0.78, 0.8).rotateY(0.2));
  if (n % 2 === 0) { const p = crearPlanta(0.35); p.position.set(-0.75, 0.77, 1.05); g.add(p); }
  // Silla
  const silla = new THREE.Group(); g.add(silla);
  silla.add(malla(new THREE.BoxGeometry(0.54, 0.08, 0.5), MAT.tela, 0, 0.47, 0));
  silla.add(malla(new THREE.BoxGeometry(0.54, 0.6, 0.07), MAT.tela, 0, 0.82, -0.27).rotateX(-0.1));
  silla.add(malla(new THREE.CylinderGeometry(0.03, 0.03, 0.4, 10), MAT.metal, 0, 0.25, 0));
  for (let i = 0; i < 5; i++) {
    const pata = malla(new THREE.BoxGeometry(0.04, 0.03, 0.32), MAT.oscuro, 0, 0.05, 0);
    pata.rotation.y = (i / 5) * Math.PI * 2; pata.translateZ(0.15); silla.add(pata);
  }
  return g;
}
function crearPlanta(escala = 1) {
  const g = new THREE.Group();
  g.add(malla(new THREE.CylinderGeometry(0.28, 0.22, 0.5, 20), MAT.maceta, 0, 0.25, 0));
  g.add(malla(new THREE.CylinderGeometry(0.285, 0.285, 0.06, 20), MAT.zocalo, 0, 0.42, 0));
  const azar = semillaAzar(Math.round(escala * 100));
  for (let i = 0; i < 11; i++) {
    const hoja = malla(new THREE.SphereGeometry(0.5, 12, 8), i % 2 ? MAT.hoja : MAT.hoja2);
    hoja.scale.set(0.14, 0.62 + azar() * 0.35, 0.05);
    const a = (i / 11) * Math.PI * 2 + azar();
    hoja.position.set(Math.sin(a) * 0.12, 0.85 + azar() * 0.2, Math.cos(a) * 0.12);
    hoja.rotation.set(Math.cos(a) * 0.55, 0, -Math.sin(a) * 0.55); hoja.rotation.y = a;
    g.add(hoja);
  }
  g.scale.setScalar(escala); return g;
}

/* ---------------- la oficina ---------------- */
export function crearOficina(contenedor, opciones = {}) {
  const prueba = document.createElement("canvas");
  if (!(prueba.getContext("webgl2") || prueba.getContext("webgl"))) throw new Error("sin WebGL");

  const render = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  render.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  render.shadowMap.enabled = true; render.shadowMap.type = THREE.PCFSoftShadowMap;
  render.toneMapping = THREE.ACESFilmicToneMapping; render.toneMappingExposure = 1.05;
  render.outputColorSpace = THREE.SRGBColorSpace;
  contenedor.appendChild(render.domElement);
  const etiquetas = new CSS2DRenderer();
  etiquetas.domElement.className = "capa-etiquetas"; contenedor.appendChild(etiquetas.domElement);

  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(30, 1, 0.1, 200);
  // La cámara se encuadra sola según el tamaño de la ventana: toma de toda la oficina y toma
  // cercana de la mesa de reuniones (cuando Isa convoca al equipo).
  const DIRECCION = new THREE.Vector3(0.62, 0.66, 0.85).normalize(), DIRECCION_CERCA = new THREE.Vector3(0.5, 0.36, 0.88).normalize();
  const PUNTOS_LEJOS = [[-8.3, 0, -5.8], [8.3, 0, -5.8], [-8.3, 0, 4.2], [8.3, 0, 4.2], [-8.3, 4.7, -5.8], [8.3, 4.7, -5.8]];
  const PUNTOS_CERCA = [[-3.2, 0, -2.0], [3.2, 0, -2.0], [-3.2, 0, 2.8], [3.2, 0, 2.8], [0, 4.95, 0.6], [-3.2, 3.0, -2.0], [3.2, 3.0, 2.8]];
  const CAM_LEJOS = new THREE.Vector3(), MIRA_LEJOS = new THREE.Vector3(), CAM_CERCA = new THREE.Vector3(), MIRA_CERCA = new THREE.Vector3();
  function encuadrar(puntos, margen, cam, mira, DIRECCION, margenX = margen) {
    // Busca centro y distancia para que todos los puntos entren en pantalla con un margen.
    const c = new THREE.PerspectiveCamera(camara.fov, camara.aspect, 0.1, 200), v = new THREE.Vector3();
    const centro = new THREE.Vector3(); puntos.forEach((q) => centro.add(v.set(...q))); centro.divideScalar(puntos.length);
    let dist = 30;
    for (let k = 0; k < 6; k++) {
      c.position.copy(centro).addScaledVector(DIRECCION, dist); c.lookAt(centro); c.updateMatrixWorld();
      let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
      puntos.forEach((q) => { v.set(...q).project(c); x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y); });
      // mover el centro para que el encuadre quede centrado
      const derecha = new THREE.Vector3().setFromMatrixColumn(c.matrixWorld, 0), arriba = new THREE.Vector3().setFromMatrixColumn(c.matrixWorld, 1);
      const altoVista = 2 * dist * Math.tan((c.fov * Math.PI) / 360), anchoVista = altoVista * c.aspect;
      centro.addScaledVector(derecha, ((x0 + x1) / 2) * anchoVista / 2).addScaledVector(arriba, ((y0 + y1) / 2) * altoVista / 2);
      dist *= Math.max((x1 - x0) / 2 / margenX, (y1 - y0) / 2 / margen);
    }
    mira.copy(centro); cam.copy(centro).addScaledVector(DIRECCION, dist);
  }

  // Luces
  escena.add(new THREE.HemisphereLight(0xe4efff, 0x2b3d6b, 1.1));
  const sol = new THREE.DirectionalLight(0xffffff, 2.0); sol.position.set(9, 16, 10); sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048); Object.assign(sol.shadow.camera, { left: -12, right: 12, top: 10, bottom: -10, near: 1, far: 50 });
  sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.02; escena.add(sol);
  const relleno = new THREE.DirectionalLight(0x9cc3ff, 0.6); relleno.position.set(-10, 8, -4); escena.add(relleno);

  // Base, piso y paredes (maqueta)
  const texPiso = lienzo(512, 512, (x, w, h) => {
    x.fillStyle = "#eef3fb"; x.fillRect(0, 0, w, h);
    x.strokeStyle = "#d9e3f3"; x.lineWidth = 3;
    for (let i = 0; i <= 4; i++) { x.beginPath(); x.moveTo(i * 128, 0); x.lineTo(i * 128, h); x.stroke(); x.beginPath(); x.moveTo(0, i * 128); x.lineTo(w, i * 128); x.stroke(); }
  });
  texPiso.wrapS = texPiso.wrapT = THREE.RepeatWrapping; texPiso.repeat.set(4, 2.75);
  MAT.piso = new THREE.MeshStandardMaterial({ map: texPiso, roughness: 0.35, metalness: 0.05 });
  escena.add(malla(new THREE.BoxGeometry(16.6, 0.6, 11.6), MAT.base, 0, -0.5, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 0.4, 11), MAT.piso, 0, -0.2, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 4.6, 0.3), MAT.pared, 0, 2.3, -5.65));
  escena.add(malla(new THREE.BoxGeometry(0.3, 4.6, 11.3), MAT.pared, -8.15, 2.3, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 0.16, 0.06), MAT.zocalo, 0, 0.08, -5.48));
  escena.add(malla(new THREE.BoxGeometry(0.06, 0.16, 11), MAT.zocalo, -7.98, 0.08, 0));
  // franja azul en lo alto de las paredes
  escena.add(malla(new THREE.BoxGeometry(16, 0.1, 0.32), MAT.zocalo, 0, 4.6, -5.65));
  escena.add(malla(new THREE.BoxGeometry(0.32, 0.1, 11.3), MAT.zocalo, -8.15, 4.6, 0));
  // Alfombra de la sala de reuniones
  const alfombra = new THREE.Mesh(new THREE.CircleGeometry(3.15, 64), new THREE.MeshStandardMaterial({ color: 0xc7d9f8, roughness: 0.95 }));
  alfombra.rotation.x = -Math.PI / 2; alfombra.position.set(MESA.x, 0.005, MESA.z); alfombra.receiveShadow = true; escena.add(alfombra);
  const borde = new THREE.Mesh(new THREE.RingGeometry(3.02, 3.15, 64), new THREE.MeshStandardMaterial({ color: 0x3d7bff }));
  borde.rotation.x = -Math.PI / 2; borde.position.set(MESA.x, 0.008, MESA.z); escena.add(borde);

  // Ventanal con la ciudad al atardecer
  const ciudad = lienzo(1024, 400, (x, w, h) => {
    const cielo = x.createLinearGradient(0, 0, 0, h);
    cielo.addColorStop(0, "#0e2a6b"); cielo.addColorStop(0.55, "#3f7fe0"); cielo.addColorStop(0.85, "#9cc6ff"); cielo.addColorStop(1, "#ffd6b0");
    x.fillStyle = cielo; x.fillRect(0, 0, w, h);
    const azar = semillaAzar(11);
    for (let i = 0; i < 60; i++) { x.fillStyle = `rgba(255,255,255,${.3 + azar() * .5})`; x.fillRect(azar() * w, azar() * 120, 2, 2); }
    for (const [tono, alto, prob] of [["#2a4f9e", 170, .15], ["#173777", 250, .3]]) {
      let px = -20;
      while (px < w + 20) {
        const bw = 40 + azar() * 70, bh = alto * (0.5 + azar() * 0.7);
        x.fillStyle = tono; x.fillRect(px, h - bh, bw, bh);
        for (let wy = h - bh + 12; wy < h - 6; wy += 14) for (let wx = px + 8; wx < px + bw - 8; wx += 12)
          if (azar() < prob) { x.fillStyle = azar() < .75 ? "#ffd98a" : "#bfe8ff"; x.fillRect(wx, wy, 5, 7); }
        px += bw + 4;
      }
    }
  });
  const vista = new THREE.Mesh(new THREE.PlaneGeometry(6.6, 2.5), new THREE.MeshBasicMaterial({ map: ciudad, toneMapped: false }));
  vista.position.set(2.6, 2.55, -5.49); escena.add(vista);
  const marco = MAT.blanco;
  [[2.6, 3.84, 6.8, 0.1], [2.6, 1.26, 6.8, 0.1]].forEach(([x, y, w, h]) => escena.add(malla(new THREE.BoxGeometry(w, h, 0.14), marco, x, y, -5.45)));
  [-0.75, 1.5, 3.7, 5.95].forEach((x) => escena.add(malla(new THREE.BoxGeometry(0.08, 2.6, 0.14), marco, x, 2.55, -5.45)));
  escena.add(malla(new THREE.BoxGeometry(7.0, 0.07, 0.34), marco, 2.6, 1.22, -5.36));

  // Letrero FARMASI y pantalla en la pared izquierda
  const letrero = lienzo(1024, 300, (x, w, h) => {
    x.clearRect(0, 0, w, h); x.fillStyle = "#1f4fd1"; x.font = "800 150px Sora, 'Segoe UI', sans-serif"; x.textAlign = "center";
    x.fillText("FARMASI", w / 2, 170); x.fillStyle = "#4f6fa8"; x.font = "500 50px 'Segoe UI', sans-serif"; x.fillText("EQUIPO DE ISA", w / 2, 250);
  });
  const placaLetrero = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 1.23), new THREE.MeshBasicMaterial({ map: letrero, transparent: true }));
  placaLetrero.position.set(-4.4, 3.35, -5.48); placaLetrero.scale.setScalar(0.85); escena.add(placaLetrero);
  const tablero = lienzo(640, 360, (x, w, h) => {
    x.fillStyle = "#0b1a38"; x.fillRect(0, 0, w, h);
    x.fillStyle = "#cfe6ff"; x.font = "600 26px 'Segoe UI', sans-serif"; x.fillText("Resultados de la semana", 28, 46);
    const barras = [60, 90, 75, 120, 105, 150, 170];
    barras.forEach((b, i) => { const g = x.createLinearGradient(0, 300 - b, 0, 300); g.addColorStop(0, "#4cc9ff"); g.addColorStop(1, "#3d7bff");
      x.fillStyle = g; x.fillRect(40 + i * 62, 300 - b, 38, b); });
    x.strokeStyle = "#5be3b0"; x.lineWidth = 4; x.beginPath();
    barras.forEach((b, i) => { const px = 59 + i * 62, py = 280 - b * 0.9; i ? x.lineTo(px, py) : x.moveTo(px, py); }); x.stroke();
    x.fillStyle = "#6a82ab"; x.font = "500 18px 'Segoe UI'"; ["L", "M", "M", "J", "V", "S", "D"].forEach((d, i) => x.fillText(d, 52 + i * 62, 330));
  });
  const tv = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 1.58), new THREE.MeshBasicMaterial({ map: tablero, toneMapped: false }));
  tv.position.set(-7.94, 2.6, -1.9); tv.rotation.y = Math.PI / 2; escena.add(tv);
  escena.add(malla(new THREE.BoxGeometry(0.08, 1.72, 2.94), MAT.oscuro, -7.98, 2.6, -1.9));

  // Repisa con libros (pared izquierda) y cafetería (derecha)
  const repisa = new THREE.Group(); repisa.position.set(-7.8, 0.4, 2.5); escena.add(repisa);
  [1.6, 2.5].forEach((y) => repisa.add(malla(new THREE.BoxGeometry(0.4, 0.05, 2.4), MAT.blanco, 0.1, y, 0)));
  const colores = [0x3d7bff, 0x4cc9ff, 0xffc15e, 0x5be3b0, 0xa99bff, 0xff8a7a, 0xdfeaff];
  for (let i = 0; i < 14; i++) {
    const alto = 0.32 + ((i * 37) % 13) / 60;
    repisa.add(malla(new THREE.BoxGeometry(0.28, alto, 0.09), new THREE.MeshStandardMaterial({ color: colores[i % colores.length], roughness: .6 }),
      0.12, (i < 7 ? 1.625 : 2.525) + alto / 2, -1.0 + (i % 7) * 0.13));
  }
  const cafe = new THREE.Group(); cafe.position.set(7.15, 0, -3.9); escena.add(cafe);
  cafe.add(malla(new THREE.BoxGeometry(1.0, 0.95, 2.6), MAT.blanco, 0, 0.475, 0));
  cafe.add(malla(new THREE.BoxGeometry(1.06, 0.05, 2.66), MAT.madera, 0, 0.97, 0));
  cafe.add(malla(new THREE.BoxGeometry(0.45, 0.55, 0.4), MAT.oscuro, 0, 1.27, -0.6));
  cafe.add(malla(new THREE.BoxGeometry(0.3, 0.06, 0.06), new THREE.MeshBasicMaterial({ color: 0x4cc9ff, toneMapped: false }), -0.23, 1.38, -0.6));
  [0.2, 0.45, 0.7].forEach((z, i) => cafe.add(malla(new THREE.CylinderGeometry(0.06, 0.05, 0.12, 14), new THREE.MeshStandardMaterial({ color: colores[i] }), -0.15, 1.05, z)));

  // Plantas grandes
  [[-7.3, -4.85, 1.2], [-7.3, 5.0, 1.0], [7.4, 5.1, 0.95], [-0.1, -4.95, 0.75]].forEach(([x, z, e]) => { const p = crearPlanta(e); p.position.set(x, 0, z); escena.add(p); });

  // Mesa de reuniones y el holograma de Isa
  const mesa = new THREE.Group(); mesa.position.copy(MESA); escena.add(mesa);
  mesa.add(malla(new THREE.CylinderGeometry(1.65, 1.6, 0.08, 64), MAT.blanco, 0, 0.78, 0));
  mesa.add(malla(new THREE.TorusGeometry(1.64, 0.025, 8, 80), new THREE.MeshBasicMaterial({ color: 0x4cc9ff, toneMapped: false }), 0, 0.78, 0).rotateX(Math.PI / 2));
  mesa.add(malla(new THREE.CylinderGeometry(0.22, 0.32, 0.74, 24), MAT.gris, 0, 0.37, 0));
  mesa.add(malla(new THREE.CylinderGeometry(0.75, 0.8, 0.04, 40), MAT.gris, 0, 0.02, 0));
  const proyector = malla(new THREE.CylinderGeometry(0.34, 0.38, 0.06, 40), MAT.cian, 0, 0.84, 0); mesa.add(proyector);

  const holograma = new THREE.Group(); holograma.position.set(MESA.x, 2.75, MESA.z); escena.add(holograma);
  const texCono = lienzo(4, 128, (x, w, h) => { const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, "rgba(76,201,255,0)"); g.addColorStop(1, "rgba(76,201,255,.55)"); x.fillStyle = g; x.fillRect(0, 0, w, h); });
  const cono = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.32, 1.85, 40, 1, true),
    new THREE.MeshBasicMaterial({ map: texCono, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, toneMapped: false }));
  cono.position.set(MESA.x, 0.84 + 0.925, MESA.z); escena.add(cono);
  const resplandor = new THREE.Sprite(new THREE.SpriteMaterial({ map: lienzo(128, 128, (x) => {
    const g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, "rgba(160,230,255,1)"); g.addColorStop(.3, "rgba(76,201,255,.45)"); g.addColorStop(1, "rgba(76,201,255,0)");
    x.fillStyle = g; x.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  resplandor.scale.setScalar(2.3); holograma.add(resplandor);
  const nucleo = new THREE.Mesh(new THREE.SphereGeometry(0.36, 40, 30), new THREE.MeshPhysicalMaterial({
    color: 0x9fe6ff, emissive: 0x2a9dff, emissiveIntensity: 1.6, roughness: 0.15, clearcoat: 1, transparent: true, opacity: 0.92 }));
  holograma.add(nucleo);
  const malla20 = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(0.55, 1)),
    new THREE.LineBasicMaterial({ color: 0x9fe6ff, transparent: true, opacity: 0.55, toneMapped: false }));
  holograma.add(malla20);
  const anillos = [0.7, 0.86, 1.02].map((r, i) => {
    const a = new THREE.Mesh(new THREE.TorusGeometry(r, 0.012, 8, 120), new THREE.MeshBasicMaterial({ color: i === 1 ? 0x7fb2ff : 0x6fdcff, toneMapped: false, transparent: true, opacity: 0.8 }));
    a.rotation.set(Math.PI / 2 + (i - 1) * 0.5, i * 0.7, 0); holograma.add(a); return a;
  });
  const nPart = 260, posPart = new Float32Array(nPart * 3), azarP = semillaAzar(5);
  for (let i = 0; i < nPart; i++) {
    const r = 0.6 + azarP() * 0.7, t = azarP() * Math.PI * 2, f = Math.acos(2 * azarP() - 1);
    posPart.set([r * Math.sin(f) * Math.cos(t), r * Math.cos(f) * 0.6, r * Math.sin(f) * Math.sin(t)], i * 3);
  }
  const geoPart = new THREE.BufferGeometry(); geoPart.setAttribute("position", new THREE.BufferAttribute(posPart, 3));
  const particulas = new THREE.Points(geoPart, new THREE.PointsMaterial({ color: 0xbff0ff, size: 0.05, transparent: true, opacity: 0.85, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  holograma.add(particulas);
  const luzIsa = new THREE.PointLight(0x4cc9ff, 6, 9, 1.6); luzIsa.position.set(0, 0, 0); holograma.add(luzIsa);
  const etiquetaIsa = document.createElement("div"); etiquetaIsa.className = "etq-isa";
  etiquetaIsa.innerHTML = "<b>Isa</b><span>Lista para ayudarte</span>";
  const objIsa = new CSS2DObject(etiquetaIsa); objIsa.position.set(0, -1.35, 0); holograma.add(objIsa);


  /* ---------- robots y escritorios ---------- */
  const robots = new Map(); let grupoEquipo = new THREE.Group(); escena.add(grupoEquipo);
  const ocupados = new Set();

  function etiqueta(agente) {
    const d = document.createElement("div"); d.className = "etq-robot"; d.style.setProperty("--c", agente.color);
    d.innerHTML = `<div class="globo" hidden></div><b>${agente.nombre.replace(/[<>&]/g, "")}</b><span><i></i><em>En su escritorio</em></span>`;
    return d;
  }
  function setEquipo(agentes) {
    escena.remove(grupoEquipo);
    grupoEquipo.traverse((o) => { if (o.isCSS2DObject) o.element.remove(); });
    grupoEquipo = new THREE.Group(); escena.add(grupoEquipo); robots.clear(); ocupados.clear();
    agentes.forEach((a, i) => {
      const puesto = PUESTOS[i % PUESTOS.length];
      const casa = new THREE.Vector3(puesto.x, 0, puesto.z);
      const escritorio = crearEscritorio(a, i); escritorio.position.copy(casa); escritorio.rotation.y = puesto.giro; grupoEquipo.add(escritorio);
      const r = crearRobot(a, a.cara ?? i); r.raiz.position.copy(casa); r.raiz.rotation.y = puesto.giro; grupoEquipo.add(r.raiz);
      const el = etiqueta(a); const obj = new CSS2DObject(el); obj.position.set(0, 2.55, 0); r.raiz.add(obj);
      el.addEventListener("click", () => opciones.alTocarAgente?.(a.id));
      const adelante = new THREE.Vector3(Math.sin(puesto.giro), 0, Math.cos(puesto.giro));
      const derecha = new THREE.Vector3(Math.cos(puesto.giro), 0, -Math.sin(puesto.giro));
      const salida = casa.clone().addScaledVector(derecha, puesto.x > 0 ? -1.3 : 1.3).addScaledVector(adelante, -0.2);
      robots.set(a.id, { ...r, agente: a, el, casa, giroCasa: puesto.giro, salida, estado: "sentado", sentado: 1, metaSentado: 1,
        camino: [], giro: puesto.giro, metaGiro: puesto.giro, fase: Math.random() * 6, andar: 0, festejo: 0, hablar: 0,
        parpadeo: 2 + Math.random() * 3, lugar: -1, semilla: i * 1.7 });
    });
  }
  function estadoEtiqueta(r, texto, clase) {
    r.el.querySelector("em").textContent = texto; r.el.dataset.estado = clase || "";
  }
  function globo(r, texto, listo) {
    const g = r.el.querySelector(".globo"); g.hidden = !texto; g.textContent = texto || ""; g.classList.toggle("listo", !!listo);
  }
  // Camino alrededor de la mesa (para no atravesarla): puntos sobre un círculo entre dos lugares.
  function rodear(desde, hasta) {
    const R = 2.75, a0 = Math.atan2(desde.x - MESA.x, desde.z - MESA.z), a1 = Math.atan2(hasta.x - MESA.x, hasta.z - MESA.z);
    let d = a1 - a0; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2;
    const pasos = Math.max(1, Math.ceil(Math.abs(d) / 0.45)), puntos = [];
    for (let i = 0; i <= pasos; i++) { const a = a0 + (d * i) / pasos; puntos.push(new THREE.Vector3(MESA.x + Math.sin(a) * R, 0, MESA.z + Math.cos(a) * R)); }
    return puntos;
  }
  const esperar = (ms) => new Promise((ok) => setTimeout(ok, MOVIMIENTO ? ms : 0));
  const llegar = (r) => new Promise((ok) => { r.alLlegar = ok; if (!r.camino.length) ok(); });

  async function convocar(id) {
    const r = robots.get(id); if (!r) return;
    if (r.estado !== "sentado" && r.estado !== "volviendo") { globo(r, r.actividad || "Trabajando…"); return; }
    r.estado = "yendo"; globo(r, "¡Voy!"); estadoEtiqueta(r, "En reunión con Isa", "reunion");
    let libre = LUGARES.findIndex((_, i) => !ocupados.has(i)); if (libre < 0) libre = 0; ocupados.add(libre); r.lugar = libre;
    r.metaSentado = 0; await esperar(650);
    r.objeto.visible = true;
    r.camino = [r.salida.clone(), ...rodear(r.salida, LUGARES[libre]), LUGARES[libre].clone()]; await llegar(r);
    if (r.estado !== "yendo") return;
    r.estado = "reunion"; r.metaGiro = anguloHacia(LUGARES[libre], MESA); globo(r, r.actividad || "¡Manos a la obra!");
  }
  function actividad(id, texto) {
    const r = robots.get(id); if (!r) return; r.actividad = texto;
    if (r.estado === "reunion" || r.estado === "yendo") globo(r, texto);
  }
  async function liberar(id) {
    const r = robots.get(id); if (!r || r.estado === "sentado" || r.estado === "volviendo" || r.estado === "festejo") return;
    while (r.estado === "yendo") await esperar(200);
    r.estado = "festejo"; globo(r, "¡Listo! ✓", true); r.sonrisa.visible = true; estadoEtiqueta(r, "Tarea completada ✓", "listo");
    await esperar(1900);
    globo(r, ""); r.estado = "volviendo"; ocupados.delete(r.lugar); r.lugar = -1; r.actividad = "";
    r.camino = [...rodear(r.raiz.position, r.salida).slice(1), r.salida.clone(), r.casa.clone()]; await llegar(r);
    if (r.estado !== "volviendo") return;
    r.metaGiro = r.giroCasa; r.objeto.visible = false; r.metaSentado = 1; r.estado = "sentado"; r.sonrisa.visible = false;
    setTimeout(() => { if (r.estado === "sentado") estadoEtiqueta(r, "En su escritorio", ""); }, 7000);
  }

  /* ---------- Isa y resultados ---------- */
  let modo = "reposo", energia = 0, enfoque = 0, metaEnfoque = 0;
  function isa(nuevo, frase) {
    modo = nuevo || "reposo";
    etiquetaIsa.querySelector("span").textContent = frase || "Lista para ayudarte";
  }
  function reunion(si) { metaEnfoque = si ? 1 : 0; }
  const cargador = new THREE.TextureLoader();
  function mostrarResultado(url, esImagen) {
    const g = new THREE.Group(); g.position.set(MESA.x, 4.2, MESA.z); escena.add(g);
    const mat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, toneMapped: false, side: THREE.DoubleSide });
    const plano = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.5), mat); g.add(plano);
    const marcoR = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(1.57, 1.57)), new THREE.LineBasicMaterial({ color: 0x6fdcff, transparent: true, toneMapped: false }));
    g.add(marcoR);
    if (esImagen) cargador.load(url, (t) => { t.colorSpace = THREE.SRGBColorSpace; mat.map = t; mat.needsUpdate = true; });
    else { mat.map = lienzo(256, 256, (x) => { x.fillStyle = "#0b1a38"; x.fillRect(0, 0, 256, 256); x.fillStyle = "#4cc9ff"; x.font = "120px sans-serif"; x.textAlign = "center"; x.fillText(/\.mp4/i.test(url) ? "▶" : "▦", 128, 170); }); }
    const inicio = performance.now();
    resultados.push({ g, mat, marcoR, inicio });
  }
  const resultados = [];

  /* ---------- interacción ---------- */
  const rayo = new THREE.Raycaster(), puntero = new THREE.Vector2(), parallax = new THREE.Vector2();
  render.domElement.addEventListener("pointermove", (e) => {
    const b = render.domElement.getBoundingClientRect();
    parallax.set(((e.clientX - b.left) / b.width) * 2 - 1, ((e.clientY - b.top) / b.height) * 2 - 1);
  });
  render.domElement.addEventListener("click", (e) => {
    const b = render.domElement.getBoundingClientRect();
    puntero.set(((e.clientX - b.left) / b.width) * 2 - 1, -((e.clientY - b.top) / b.height) * 2 + 1);
    rayo.setFromCamera(puntero, camara);
    const tocado = rayo.intersectObjects(grupoEquipo.children, true).find((i) => i.object.userData.agente);
    if (tocado) { e.stopPropagation(); opciones.alTocarAgente?.(tocado.object.userData.agente); }
  });

  function ajustar() {
    const w = contenedor.clientWidth, h = contenedor.clientHeight; if (!w || !h) return;
    render.setSize(w, h); etiquetas.setSize(w, h); camara.aspect = w / h;
    camara.fov = w / h < 1.1 ? 34 : 28; camara.updateProjectionMatrix();
    // la toma general recorta un poco los lados para que el equipo se vea más grande
    encuadrar(PUNTOS_LEJOS, 0.97, CAM_LEJOS, MIRA_LEJOS, DIRECCION, w / h < 1 ? 1.22 : 1.08);
    encuadrar(PUNTOS_CERCA, 0.95, CAM_CERCA, MIRA_CERCA, DIRECCION_CERCA);
  }
  new ResizeObserver(ajustar).observe(contenedor); ajustar();

  /* ---------- animación ---------- */
  const reloj = new THREE.Clock(), tmp = new THREE.Vector3(), mira = new THREE.Vector3();
  function animarRobot(r, dt, t) {
    // Caminar por el camino
    r.andar = suave(r.andar, r.camino.length ? 1 : 0, Math.min(1, dt * 8));
    if (r.camino.length && r.sentado < 0.15) {
      const meta = r.camino[0], pos = r.raiz.position;
      tmp.subVectors(meta, pos); tmp.y = 0; const d = tmp.length();
      r.metaGiro = Math.atan2(tmp.x, tmp.z);
      const paso = 1.7 * dt;
      if (d <= paso) { pos.copy(meta); r.camino.shift(); if (!r.camino.length) r.alLlegar?.(); }
      else pos.addScaledVector(tmp.normalize(), paso);
      r.fase += dt * 9;
    }
    r.giro = girarHacia(r.giro, r.metaGiro, Math.min(1, dt * 7)); r.raiz.rotation.y = r.giro;
    r.sentado = suave(r.sentado, r.metaSentado, Math.min(1, dt * 5));
    r.festejo = suave(r.festejo, r.estado === "festejo" ? 1 : 0, Math.min(1, dt * 6));
    r.hablar = suave(r.hablar, r.estado === "reunion" ? 1 : 0, Math.min(1, dt * 4));
    const s = r.sentado, w = r.andar, f = r.fase, fe = r.festejo, ha = r.hablar;
    // Cadera: sentada más baja; al andar rebota; al festejar salta
    r.cadera.position.y = suave(0.8, 0.6, s) + Math.abs(Math.sin(f)) * 0.04 * w + Math.abs(Math.sin(t * 9)) * 0.18 * fe
      + Math.sin(t * 1.6 + r.semilla) * 0.008 * (1 - w);
    r.cadera.position.z = -0.12 * s;
    r.cuerpo.rotation.x = 0.06 * w + 0.05 * s;
    r.muslos.forEach((m, i) => {
      const ph = f + (i ? Math.PI : 0);
      m.rotation.x = -1.5 * s + Math.sin(ph) * 0.6 * w;
      r.rodillas[i].rotation.x = 1.5 * s + Math.max(0, Math.sin(ph + 1.2)) * 0.8 * w;
    });
    const teclear = s * (r.estado === "sentado" ? 1 : 0);
    r.hombros.forEach((h, i) => {
      const lado = i ? 1 : -1, ph = f + (i ? 0 : Math.PI);
      const caminar = Math.sin(ph) * 0.55 * w;
      const escribir = -0.95 + Math.sin(t * 16 + i * 2) * 0.06;
      const gesto = i ? -0.5 + Math.sin(t * 2.2 + r.semilla) * 0.35 : -0.15;
      h.rotation.x = caminar * (1 - teclear) + escribir * teclear + gesto * ha * (1 - teclear) - 0.25 * (w * (1 - teclear) * (i ? 1 : 0) * (r.objeto.visible ? 1 : 0));
      h.rotation.z = lado * (0.08 + 2.5 * fe);
      r.codos[i].rotation.x = -0.25 * w - 0.75 * teclear - (i ? 0.7 : 0.1) * ha;
    });
    // Cabeza: mira alrededor, asiente en reunión y mira a Isa
    r.cabeza.rotation.y = Math.sin(t * 0.5 + r.semilla) * 0.35 * (1 - w) * (1 - ha);
    r.cabeza.rotation.x = Math.sin(t * 3 + r.semilla) * 0.07 * ha - 0.18 * ha + 0.12 * teclear;
    // Parpadeo y luces
    r.parpadeo -= dt;
    const cerrado = r.parpadeo < 0.12 && r.parpadeo > 0;
    if (r.parpadeo <= 0) r.parpadeo = 2.5 + Math.random() * 3.5;
    r.ojos.forEach((o) => { o.scale.y = cerrado ? 0.15 : 1; });
    r.foco.scale.setScalar(1 + (r.estado === "reunion" ? Math.abs(Math.sin(t * 6)) * 0.6 : 0));
    r.nucleo.scale.setScalar(1 + Math.sin(t * 3 + r.semilla) * 0.08);
  }
  function cuadro() {
    const dt = Math.min(reloj.getDelta(), 0.1), t = reloj.elapsedTime;
    const meta = { reposo: 0, pensando: 1, hablando: 0.6 }[modo] ?? 0;
    energia = suave(energia, meta, Math.min(1, dt * 3));
    const vel = MOVIMIENTO ? 1 : 0.1;
    malla20.rotation.y += dt * (0.3 + energia * 1.5) * vel; malla20.rotation.x += dt * 0.15 * vel;
    anillos.forEach((a, i) => { a.rotation.z += dt * (0.4 + i * 0.25) * (1 + energia * 2) * (i % 2 ? -1 : 1) * vel; });
    particulas.rotation.y -= dt * (0.15 + energia * 0.8) * vel;
    const pulso = modo === "hablando" ? Math.abs(Math.sin(t * 8)) * 0.12 : Math.sin(t * 2) * 0.04;
    nucleo.scale.setScalar(1 + pulso + energia * 0.08);
    nucleo.material.emissiveIntensity = 1.4 + energia * 1.2;
    resplandor.material.opacity = 0.45 + energia * 0.35;
    holograma.position.y = 2.75 + Math.sin(t * 1.2) * 0.06;
    luzIsa.intensity = 5 + energia * 6 + pulso * 20;
    cono.material.opacity = 0.7 + energia * 0.3;

    robots.forEach((r) => animarRobot(r, dt, t));

    for (let i = resultados.length - 1; i >= 0; i--) {
      const res = resultados[i], e = (performance.now() - res.inicio) / 1000;
      const op = e < 0.6 ? e / 0.6 : e > 4 ? Math.max(0, 1 - (e - 4) / 0.8) : 1;
      res.mat.opacity = op; res.marcoR.material.opacity = op;
      res.g.scale.setScalar(0.4 + 0.6 * Math.min(1, e / 0.6)); res.g.position.y = 4.2 + Math.sin(e * 2) * 0.06;
      res.g.quaternion.copy(camara.quaternion);
      if (e > 4.8) { escena.remove(res.g); resultados.splice(i, 1); }
    }

    // Cámara: se acerca cuando hay reunión y se mueve un poco con el ratón
    enfoque = suave(enfoque, metaEnfoque, Math.min(1, dt * 1.2));
    camara.position.lerpVectors(CAM_LEJOS, CAM_CERCA, enfoque);
    camara.position.x += parallax.x * 0.5 + Math.sin(t * 0.15) * 0.25 * vel;
    camara.position.y -= parallax.y * 0.3;
    mira.lerpVectors(MIRA_LEJOS, MIRA_CERCA, enfoque); camara.lookAt(mira);

    render.render(escena, camara); etiquetas.render(escena, camara);
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(cuadro);

  const api = { setEquipo, convocar, actividad, liberar, isa, reunion, mostrarResultado };
  window.oficina3d = api;   // útil para probar desde la consola del navegador
  api.depurar = () => ({ cam: camara.position.toArray(), lejos: CAM_LEJOS.toArray(), cerca: CAM_CERCA.toArray(), mira: MIRA_CERCA.toArray(), enfoque, w: contenedor.clientWidth, h: contenedor.clientHeight });
  return api;
}
