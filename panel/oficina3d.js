// La oficina 3D de Isa: una oficina en miniatura (estilo maqueta) donde cada agente es un
// robot que trabaja sentado en su escritorio. Cuando Isa lo llama, se levanta, camina
// hasta la mesa de reuniones bajo el holograma de Isa, trabaja ahí y luego vuelve.
//
// Uso:  const oficina = crearOficina(contenedor, { alTocarAgente(id) {} });
//       oficina.setEquipo(agentes) · convocar(id) · actividad(id, texto) · liberar(id)
//       oficina.isa("reposo" | "pensando" | "hablando") · mostrarResultado(url)
//       oficina.reunirEquipo() · notasReunion({ id: { nota, antes } }) · despedirEquipo()
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
  pared: new THREE.MeshStandardMaterial({ color: 0xfaf1f1, roughness: 0.9 }),
  zocalo: new THREE.MeshStandardMaterial({ color: 0xe58aa8, roughness: 0.45 }),
  dorado: new THREE.MeshStandardMaterial({ color: 0xd8b46a, roughness: 0.25, metalness: 0.9 }),
  base: new THREE.MeshStandardMaterial({ color: 0x2c2350, roughness: 0.6 }),
  blanco: new THREE.MeshPhysicalMaterial({ color: 0xfffbfa, roughness: 0.35, clearcoat: 0.6, clearcoatRoughness: 0.3 }),
  gris: new THREE.MeshStandardMaterial({ color: 0xeadde0, roughness: 0.5, metalness: 0.2 }),
  metal: new THREE.MeshStandardMaterial({ color: 0xe3bfb0, roughness: 0.3, metalness: 0.8 }),   // oro rosa
  oscuro: new THREE.MeshStandardMaterial({ color: 0x1d2740, roughness: 0.5, metalness: 0.3 }),
  tela: new THREE.MeshPhysicalMaterial({ color: 0xf4b6c8, roughness: 0.8, sheen: 1, sheenColor: 0xffe1ea }),   // terciopelo rosado
  maceta: new THREE.MeshStandardMaterial({ color: 0xf2f5fb, roughness: 0.6 }),
  hoja: new THREE.MeshStandardMaterial({ color: 0x36b98a, roughness: 0.6, side: THREE.DoubleSide }),
  hoja2: new THREE.MeshStandardMaterial({ color: 0x2a9a73, roughness: 0.6, side: THREE.DoubleSide }),
  madera: new THREE.MeshStandardMaterial({ color: 0xd9b991, roughness: 0.7 }),
  cian: new THREE.MeshBasicMaterial({ color: 0xff9cc6, toneMapped: false }),
  flor: new THREE.MeshStandardMaterial({ color: 0xff8fb5, roughness: 0.5 }),
  flor2: new THREE.MeshStandardMaterial({ color: 0xffd1e0, roughness: 0.5 }),
  florero: new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.05, transmission: 0.6, transparent: true, opacity: 0.6 }),
};

/* ---------------- el robot ---------------- */
function rolDe(agente) {
  const t = (agente.id + " " + (agente.que_hace || "")).toLowerCase();
  if (/asesora|rutina/.test(agente.id)) return "frasco";
  if (/scraper|busca|investig|lector/.test(agente.id) || /investigador/.test(t)) return "lupa";
  if (/educa|profe|ensen|enseñ/.test(agente.id)) return "puntero";
  if (/guion/.test(agente.id)) return "claqueta";
  if (/analista|redes|metrica|estadistica/.test(agente.id)) return "grafico";
  if (/creador|contenido|video|anuncio/.test(agente.id)) return "camara";
  if (/estrateg|plan|calendario/.test(agente.id)) return "tableta";
  if (/cliente|crm|venta|pedido/.test(t)) return "telefono";
  return "taza";
}

// Colores del uniforme Farmasi: vestido rosa con cuello blanco, cinturón negro y detalles dorados.
const UNIFORME = { rosa: 0xe8457f, negro: 0x1c1a1f, dorado: 0xd8b46a };
// Tonos de pelo: cada robot tiene el suyo (fijo según su lugar en el equipo).
const PELOS = [0x4a2f27, 0xe6c07e, 0x231c22, 0xb0603c, 0xc9a2e0, 0x8a5440, 0xf3b4cc, 0xefe0c0];
function texturaGafete() {
  return lienzo(256, 96, (x, w, h) => {
    x.fillStyle = "#ffffff"; x.beginPath(); x.roundRect(0, 0, w, h, 18); x.fill();
    x.fillStyle = "#1c1a1f"; x.font = "800 58px Sora, 'Segoe UI', sans-serif"; x.textAlign = "center"; x.textBaseline = "middle";
    x.fillText("FARMASI", w / 2, h / 2 + 3);
  });
}
let GAFETE = null;

function crearRobot(agente, variante) {
  const color = new THREE.Color(agente.color);
  GAFETE ??= texturaGafete();
  const m = {
    casco: new THREE.MeshPhysicalMaterial({ color: 0xfdf8f7, roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.1, sheen: 0.4, sheenColor: 0xffd6e4 }),
    junta: new THREE.MeshStandardMaterial({ color: 0xe9dfe3, roughness: 0.35, metalness: 0.4 }),
    uniforme: new THREE.MeshPhysicalMaterial({ color: UNIFORME.rosa, roughness: 0.55, sheen: 1, sheenColor: 0xffc4da, sheenRoughness: 0.5 }),
    cuello: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6, side: THREE.DoubleSide }),
    negro: new THREE.MeshStandardMaterial({ color: UNIFORME.negro, roughness: 0.4 }),
    dorado: new THREE.MeshStandardMaterial({ color: UNIFORME.dorado, roughness: 0.25, metalness: 0.9 }),
    pelo: new THREE.MeshPhysicalMaterial({ color: PELOS[variante % PELOS.length], roughness: 0.45, clearcoat: 0.6, clearcoatRoughness: 0.35, side: THREE.DoubleSide }),
    acento: new THREE.MeshStandardMaterial({ color, roughness: 0.35, emissive: color, emissiveIntensity: 0.15 }),
    visor: new THREE.MeshPhysicalMaterial({ color: 0x1a1222, roughness: 0.08, clearcoat: 1, metalness: 0.2 }),
    luz: new THREE.MeshBasicMaterial({ color: 0x9ff0ff, toneMapped: false }),
    rubor: new THREE.MeshBasicMaterial({ color: 0xff7aa8, transparent: true, opacity: 0.75, toneMapped: false }),
    brillo: new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }),
  };
  // Cada robot con su color de ojos (el color del agente, aclarado para que brille)
  m.luz.color.copy(color).lerp(new THREE.Color(0xffffff), 0.35).multiplyScalar(1.3);
  const raiz = new THREE.Group(); raiz.userData.agente = agente.id;
  const cadera = new THREE.Group(); cadera.position.y = 0.8; raiz.add(cadera);
  const cuerpo = new THREE.Group(); cadera.add(cuerpo);

  // Vestido del uniforme: torso entallado con cintura fina
  const perfil = [[0, 0.06], [0.2, 0.06], [0.215, 0.12], [0.165, 0.26], [0.2, 0.42], [0.235, 0.56], [0.215, 0.68], [0.15, 0.76], [0.07, 0.8], [0, 0.81]]
    .map(([r, y]) => new THREE.Vector2(r, y));
  const torso = malla(new THREE.LatheGeometry(perfil, 32), m.uniforme); torso.scale.z = 0.8; cuerpo.add(torso);
  // Cuello blanco en V (solapas) y gafete FARMASI
  [-1, 1].forEach((s) => {
    const solapa = malla(new THREE.BoxGeometry(0.08, 0.2, 0.012), m.cuello, s * 0.06, 0.66, 0.165);
    solapa.rotation.set(-0.35, 0, s * 0.5); cuerpo.add(solapa);
  });
  const gafete = new THREE.Mesh(new THREE.PlaneGeometry(0.15, 0.056), new THREE.MeshBasicMaterial({ map: GAFETE, toneMapped: false }));
  gafete.position.set(0.1, 0.5, 0.188); gafete.rotation.set(-0.12, 0.28, 0); cuerpo.add(gafete);
  // Cinturón negro con hebilla dorada (el centro brilla con el color del agente)
  const cinturon = malla(new THREE.CylinderGeometry(0.172, 0.168, 0.05, 28), m.negro, 0, 0.26, 0); cinturon.scale.z = 0.8; cuerpo.add(cinturon);
  cuerpo.add(malla(new THREE.BoxGeometry(0.075, 0.055, 0.02), m.dorado, 0, 0.26, 0.138));
  const nucleo = malla(new THREE.CircleGeometry(0.016, 16), m.luz, 0, 0.26, 0.149); cuerpo.add(nucleo);
  // Botones dorados
  [0.38, 0.45].forEach((y) => cuerpo.add(malla(new THREE.SphereGeometry(0.014, 10, 8), m.dorado, 0, y, 0.172)));

  // Falda acampanada (se aplana al sentarse)
  const falda = malla(new THREE.LatheGeometry([[0.0, -0.23], [0.315, -0.23], [0.31, -0.2], [0.26, -0.06], [0.2, 0.08]].map(([r, y]) => new THREE.Vector2(r, y)), 32), m.uniforme);
  falda.scale.z = 0.85; cadera.add(falda);
  cadera.add(malla(new THREE.TorusGeometry(0.31, 0.012, 6, 40), m.cuello, 0, -0.22, 0).rotateX(Math.PI / 2)).scale.z = 0.85;

  // Cuello y cabeza (grande, estilo muñequita)
  cuerpo.add(malla(new THREE.CylinderGeometry(0.055, 0.07, 0.14, 14), m.casco, 0, 0.84, 0));
  cuerpo.add(malla(new THREE.TorusGeometry(0.065, 0.01, 6, 24), m.dorado, 0, 0.8, 0).rotateX(Math.PI / 2)); // collar
  const cabeza = new THREE.Group(); cabeza.position.y = 1.08; cabeza.scale.setScalar(1.15); cuerpo.add(cabeza);
  const craneo = malla(new THREE.SphereGeometry(0.29, 36, 28), m.casco); craneo.scale.set(1.04, 0.97, 1); cabeza.add(craneo);
  // Carita de porcelana: ojos grandes brillantes con pestañas, rubor y boquita
  const sobreCara = (x, y) => 0.29 * Math.sqrt(Math.max(0, 1 - (x / 0.3016) ** 2 - (y / 0.2813) ** 2)) + 0.003;
  const ojos = [-1, 1].map((s) => {
    const x = s * 0.092, y = 0.0;
    const o = new THREE.Group(); o.position.set(x, y, sobreCara(x, y)); o.rotation.y = s * 0.32; o.rotation.x = -0.02; cabeza.add(o);
    const blanco = new THREE.Mesh(new THREE.CircleGeometry(0.046, 24), m.visor); blanco.scale.y = 1.22; o.add(blanco);
    const iris = new THREE.Mesh(new THREE.CircleGeometry(0.03, 24), m.luz); iris.scale.y = 1.2; iris.position.set(0, -0.006, 0.001); o.add(iris);
    const chispa = new THREE.Mesh(new THREE.CircleGeometry(0.013, 12), m.brillo); chispa.position.set(-0.014, 0.02, 0.002); o.add(chispa);
    [0, 1, 2].forEach((k) => {            // pestañas
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.009, 0.034, 0.004), m.visor);
      const a = 0.35 + k * 0.38; p.position.set(s * Math.cos(a) * 0.05, Math.sin(a) * 0.058 + 0.004, 0.003); p.rotation.z = -s * (Math.PI / 2 - a) * 0.9;
      o.add(p);
    });
    return o;
  });
  [-1, 1].forEach((s) => {                  // rubor en las mejillas
    const x = s * 0.165, y = -0.07;
    const r = new THREE.Mesh(new THREE.CircleGeometry(0.03, 18), m.rubor); r.scale.y = 0.6;
    r.position.set(x, y, sobreCara(x, y)); r.rotation.y = s * 0.6; cabeza.add(r);
  });
  const boca = new THREE.Mesh(new THREE.TorusGeometry(0.022, 0.006, 6, 16, Math.PI), m.rubor);
  boca.position.set(0, -0.085, sobreCara(0, -0.085)); boca.rotation.z = Math.PI; cabeza.add(boca);
  const sonrisa = new THREE.Mesh(new THREE.CircleGeometry(0.04, 20, Math.PI, Math.PI), m.rubor);
  sonrisa.position.set(0, -0.075, sobreCara(0, -0.075) + 0.001); sonrisa.visible = false; cabeza.add(sonrisa);
  // Orejitas con aretes dorados
  [-1, 1].forEach((s) => {
    const oreja = malla(new THREE.CylinderGeometry(0.06, 0.06, 0.04, 18), m.casco, s * 0.295, -0.02, 0); oreja.rotation.z = Math.PI / 2; cabeza.add(oreja);
    cabeza.add(malla(new THREE.SphereGeometry(0.022, 10, 8), m.dorado, s * 0.31, -0.1, 0.01));
  });

  // Peinado (4 estilos): flequillo y casquete siempre; atrás cambia
  const R = 0.315, estilo = variante % 4;
  const casquete = malla(new THREE.SphereGeometry(R, 36, 20, 0, Math.PI * 2, 0, 1.1), m.pelo, 0, 0.02, 0); casquete.scale.set(1.05, 1, 1.02); cabeza.add(casquete);
  const largoAtras = [2.05, 1.7, 1.65, 2.35][estilo];
  const nuca = malla(new THREE.SphereGeometry(R, 36, 24, Math.PI / 2 + 0.85, Math.PI * 2 - 1.7, 0.4, largoAtras - 0.4), m.pelo, 0, 0.02, 0);
  nuca.scale.set(1.06, 1, 1.04); cabeza.add(nuca);
  let tope = 0.33;
  if (estilo === 1) {                       // cola de caballo
    const cola = new THREE.Group(); cola.position.set(0, 0.12, -0.3); cabeza.add(cola);
    const mecha = malla(new THREE.CapsuleGeometry(0.075, 0.28, 8, 16), m.pelo, 0, -0.17, -0.04); mecha.rotation.x = 0.35; cola.add(mecha);
    cola.add(malla(new THREE.TorusGeometry(0.06, 0.02, 8, 20), m.acento, 0, 0, 0).rotateX(Math.PI / 2 - 0.5));
  } else if (estilo === 2) {                // moño alto
    cabeza.add(malla(new THREE.SphereGeometry(0.13, 20, 16), m.pelo, 0, 0.3, -0.12));
    cabeza.add(malla(new THREE.TorusGeometry(0.1, 0.022, 8, 24), m.acento, 0, 0.25, -0.1).rotateX(Math.PI / 2 - 0.4));
    tope = 0.42;
  } else if (estilo === 3) {                // pelo largo
    const largo = malla(new THREE.CapsuleGeometry(0.2, 0.25, 8, 20), m.pelo, 0, -0.32, -0.16); largo.scale.set(1.35, 1, 0.55); cabeza.add(largo);
  }
  // Lazo en la cabeza del color del agente (el centro brilla cuando está en reunión)
  const lazo = new THREE.Group(); lazo.position.set(0.17, 0.24, 0.1); lazo.rotation.set(0.3, 0.4, -0.5); cabeza.add(lazo);
  [-1, 1].forEach((s) => {
    const ala = malla(new THREE.SphereGeometry(0.06, 16, 12), m.acento, s * 0.065, 0, 0); ala.scale.set(1.1, 0.75, 0.45); ala.rotation.z = s * 0.25; lazo.add(ala);
  });
  const foco = malla(new THREE.SphereGeometry(0.03, 14, 10), m.luz); lazo.add(foco);
  const antena = lazo;

  // Brazos finos con manguita abullonada del uniforme
  const hombros = [], codos = [], manos = [];
  [-1, 1].forEach((s) => {
    const hombro = new THREE.Group(); hombro.position.set(s * 0.27, 0.68, 0); cuerpo.add(hombro);
    const manga = malla(new THREE.SphereGeometry(0.085, 16, 12), m.uniforme, 0, -0.03, 0); manga.scale.set(1, 1.1, 1); hombro.add(manga);
    hombro.add(malla(new THREE.CapsuleGeometry(0.052, 0.2, 6, 14), m.casco, 0, -0.19, 0));
    const codo = new THREE.Group(); codo.position.y = -0.34; hombro.add(codo);
    codo.add(malla(new THREE.SphereGeometry(0.048, 12, 10), m.junta));
    codo.add(malla(new THREE.CapsuleGeometry(0.048, 0.17, 6, 14), m.casco, 0, -0.15, 0));
    codo.add(malla(new THREE.TorusGeometry(0.05, 0.01, 6, 20), m.dorado, 0, -0.24, 0).rotateX(Math.PI / 2)); // pulsera
    const mano = new THREE.Group(); mano.position.y = -0.31; codo.add(mano);
    const palma = malla(new THREE.SphereGeometry(0.06, 14, 10), m.casco); palma.scale.set(0.9, 1.15, 0.75); mano.add(palma);
    hombros.push(hombro); codos.push(codo); manos.push(mano);
  });
  // Piernas finas con zapatos rosados de tacón bajito
  const muslos = [], rodillas = [];
  [-1, 1].forEach((s) => {
    const muslo = new THREE.Group(); muslo.position.set(s * 0.1, 0, 0); cadera.add(muslo);
    muslo.add(malla(new THREE.CapsuleGeometry(0.07, 0.2, 6, 14), m.casco, 0, -0.18, 0));
    const rodilla = new THREE.Group(); rodilla.position.y = -0.38; muslo.add(rodilla);
    rodilla.add(malla(new THREE.SphereGeometry(0.058, 12, 10), m.junta));
    rodilla.add(malla(new THREE.CapsuleGeometry(0.06, 0.18, 6, 14), m.casco, 0, -0.17, 0));
    const zapato = malla(new RoundedBox(0.13, 0.08, 0.24, 0.035), m.uniforme, 0, -0.34, 0.04); rodilla.add(zapato);
    rodilla.add(malla(new THREE.BoxGeometry(0.04, 0.06, 0.04), m.uniforme, 0, -0.39, -0.05)); // tacón
    rodilla.add(malla(new THREE.SphereGeometry(0.016, 8, 6), m.dorado, 0, -0.31, 0.15));
    muslos.push(muslo); rodillas.push(rodilla);
  });

  // Objeto en la mano según su trabajo
  const objeto = new THREE.Group(); manos[1].add(objeto); objeto.position.set(0, -0.08, 0.06);
  const rol = rolDe(agente);
  if (rol === "lupa") {
    objeto.add(malla(new THREE.CylinderGeometry(0.02, 0.025, 0.2, 10), m.negro, 0, -0.08, 0));
    const anillo = malla(new THREE.TorusGeometry(0.1, 0.018, 10, 28), m.acento, 0, -0.27, 0); objeto.add(anillo);
    const vidrio = malla(new THREE.CircleGeometry(0.09, 24), new THREE.MeshPhysicalMaterial({ color: 0xbfeaff, transparent: true, opacity: 0.45, roughness: 0, side: THREE.DoubleSide }), 0, -0.27, 0);
    objeto.add(vidrio); objeto.rotation.x = -1.2;
  } else if (rol === "camara") {
    objeto.add(malla(new THREE.BoxGeometry(0.2, 0.14, 0.12), m.negro, 0, -0.06, 0.06));
    const lente = malla(new THREE.CylinderGeometry(0.05, 0.06, 0.1, 18), m.acento, 0, -0.06, 0.16); lente.rotation.x = Math.PI / 2; objeto.add(lente);
    objeto.add(malla(new THREE.SphereGeometry(0.015, 8, 8), new THREE.MeshBasicMaterial({ color: 0xff4d5e, toneMapped: false }), 0.07, 0.02, 0.06));
  } else if (rol === "tableta") {
    objeto.add(malla(new THREE.BoxGeometry(0.26, 0.34, 0.02), m.negro, 0, -0.12, 0.05));
    const pantalla = malla(new THREE.PlaneGeometry(0.22, 0.3), new THREE.MeshBasicMaterial({ map: pantallaTableta(agente.color), toneMapped: false }), 0, -0.12, 0.062);
    objeto.add(pantalla); objeto.rotation.x = -0.9;
  } else if (rol === "puntero") {   // el profe: puntero con punta que brilla
    const vara = malla(new THREE.CylinderGeometry(0.012, 0.02, 0.42, 10), m.negro, 0, -0.16, 0.02); objeto.add(vara);
    objeto.add(malla(new THREE.SphereGeometry(0.035, 12, 10), m.luz, 0, -0.38, 0.02));
    objeto.rotation.x = -1.0;
  } else if (rol === "claqueta") {   // el guionista: claqueta de cine con rayas
    objeto.add(malla(new THREE.BoxGeometry(0.26, 0.18, 0.02), m.negro, 0, -0.12, 0.05));
    const tapa = new THREE.Group(); tapa.position.set(-0.13, -0.025, 0.05); tapa.rotation.z = 0.35; objeto.add(tapa);
    for (let i = 0; i < 4; i++) {
      tapa.add(malla(new THREE.BoxGeometry(0.065, 0.045, 0.022), i % 2 ? m.casco : m.acento, 0.0325 + i * 0.065, 0.0225, 0));
    }
    objeto.rotation.x = -0.6;
  } else if (rol === "grafico") {   // la analista: tablero con barras que suben y una flecha
    objeto.add(malla(new THREE.BoxGeometry(0.28, 0.22, 0.02), m.negro, 0, -0.12, 0.05));
    [0.06, 0.1, 0.08, 0.15].forEach((h, i) => {
      objeto.add(malla(new THREE.BoxGeometry(0.04, h, 0.012), i === 3 ? m.luz : m.acento, -0.09 + i * 0.06, -0.21 + h / 2, 0.066));
    });
    const flecha = malla(new THREE.ConeGeometry(0.025, 0.05, 10), m.luz, 0.1, -0.03, 0.066); flecha.rotation.z = -0.5; objeto.add(flecha);
    objeto.rotation.x = -0.8;
  } else if (rol === "frasco") {   // la asesora: frasco de sérum con gotero
    objeto.add(malla(new THREE.CylinderGeometry(0.055, 0.06, 0.15, 18), m.acento, 0, -0.1, 0.06));
    objeto.add(malla(new THREE.CylinderGeometry(0.03, 0.03, 0.04, 14), m.negro, 0, -0.005, 0.06));
    objeto.add(malla(new THREE.SphereGeometry(0.035, 14, 10), m.negro, 0, 0.035, 0.06));
    objeto.add(malla(new THREE.SphereGeometry(0.012, 8, 8), m.luz, 0, -0.06, 0.12));
  } else if (rol === "telefono") {
    objeto.add(malla(new THREE.BoxGeometry(0.09, 0.17, 0.02), m.negro, 0, -0.06, 0.04));
  } else {
    objeto.add(malla(new THREE.CylinderGeometry(0.05, 0.045, 0.11, 16), m.acento, 0, -0.04, 0.06));
  }
  objeto.visible = false;
  if (rol === "puntero") {         // y su birrete de graduación, siempre puesto
    const birrete = new THREE.Group(); birrete.position.y = tope + 0.02; cabeza.add(birrete);
    birrete.add(malla(new THREE.CylinderGeometry(0.17, 0.19, 0.08, 20), m.negro, 0, 0.02, 0));
    const tabla = malla(new THREE.BoxGeometry(0.5, 0.03, 0.5), m.negro, 0, 0.075, 0); tabla.rotation.y = Math.PI / 4; birrete.add(tabla);
    birrete.add(malla(new THREE.SphereGeometry(0.025, 10, 8), m.acento, 0, 0.1, 0));
    const borla = malla(new THREE.CylinderGeometry(0.008, 0.008, 0.16, 6), m.acento, 0.3, 0.01, 0.06); birrete.add(borla);
    birrete.add(malla(new THREE.SphereGeometry(0.03, 10, 8), m.acento, 0.3, -0.08, 0.06));
    birrete.rotation.z = -0.08;
    antena.visible = false;          // la antena quedaría atravesando el birrete
  }

  raiz.scale.setScalar(0.95);
  raiz.traverse((o) => { if (o.isMesh) o.userData.agente = agente.id; });
  return { raiz, cadera, cuerpo, cabeza, hombros, codos, muslos, rodillas, ojos, foco, sonrisa, boca, falda, nucleo, objeto, rol };
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
  else { const f = crearFlores(0.8); f.position.set(-0.72, 0.77, 1.05); g.add(f); }
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

// Florero de vidrio con flores rosadas
function crearFlores(escala = 1) {
  const g = new THREE.Group();
  g.add(malla(new THREE.CylinderGeometry(0.09, 0.07, 0.26, 18), MAT.florero, 0, 0.13, 0));
  const azar = semillaAzar(Math.round(escala * 37));
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2 + azar(), r = i ? 0.08 + azar() * 0.05 : 0, y = 0.4 + azar() * 0.14;
    const tallo = malla(new THREE.CylinderGeometry(0.008, 0.008, y, 5), MAT.hoja2, Math.sin(a) * r / 2, y / 2 + 0.05, Math.cos(a) * r / 2);
    tallo.rotation.set(Math.cos(a) * r * 1.5, 0, -Math.sin(a) * r * 1.5); g.add(tallo);
    const flor = malla(new THREE.SphereGeometry(0.055, 12, 10), i % 3 ? MAT.flor : MAT.flor2, Math.sin(a) * r, y + 0.05, Math.cos(a) * r);
    flor.scale.y = 0.8; g.add(flor);
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
  const DIRECCION = new THREE.Vector3(0.5, 0.68, 0.9).normalize(), DIRECCION_CERCA = new THREE.Vector3(0.5, 0.36, 0.88).normalize();
  // Toma general: el fondo de la oficina más cada escritorio ocupado con su robot y su
  // etiqueta, para que ningún agente quede cortado (se recalcula al cambiar el equipo).
  const SALA = [[-8.3, 0, -5.8], [8.3, 0, -5.8], [-8.3, 4.7, -5.8], [8.3, 4.7, -5.8], [-3, 0, 3.4], [3, 0, 3.4]];
  let PUNTOS_LEJOS = SALA;
  function puntosDelEquipo(n) {
    const puntos = [...SALA];
    PUESTOS.slice(0, Math.max(1, Math.min(n, PUESTOS.length))).forEach(({ x, z }) => {
      for (const [dx, dz] of [[-1.3, -1.3], [1.3, -1.3], [-1.3, 1.3], [1.3, 1.3]]) puntos.push([x + dx, 0, z + dz]);
      puntos.push([x - 1.1, 3.1, z], [x + 1.1, 3.1, z]);   // cabeza del robot y su etiqueta
    });
    return puntos;
  }
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
  escena.add(new THREE.HemisphereLight(0xfff4f6, 0x6b4a6b, 1.15));
  const sol = new THREE.DirectionalLight(0xfff3e8, 2.0); sol.position.set(9, 16, 10); sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048); Object.assign(sol.shadow.camera, { left: -12, right: 12, top: 10, bottom: -10, near: 1, far: 50 });
  sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.02; escena.add(sol);
  const relleno = new THREE.DirectionalLight(0xffc6dc, 0.55); relleno.position.set(-10, 8, -4); escena.add(relleno);

  // Base, piso y paredes (maqueta)
  const texPiso = lienzo(512, 512, (x, w, h) => {   // piso de madera clara
    const azar = semillaAzar(7);
    for (let i = 0; i < 8; i++) {
      const y = i * 64;
      for (let px = -((i * 97) % 256); px < w; px += 256) {
        const tono = 222 + Math.floor(azar() * 14);
        x.fillStyle = `rgb(${tono + 14},${tono - 6},${tono - 28})`; x.fillRect(px, y, 256, 64);
        x.strokeStyle = "rgba(150,110,80,.10)"; x.lineWidth = 1;
        for (let k = 0; k < 5; k++) { x.beginPath(); x.moveTo(px, y + 8 + k * 11 + azar() * 4); x.bezierCurveTo(px + 80, y + 4 + k * 11, px + 170, y + 14 + k * 11, px + 256, y + 8 + k * 11); x.stroke(); }
        x.fillStyle = "rgba(140,100,70,.28)"; x.fillRect(px, y, 2, 64);
      }
      x.fillStyle = "rgba(140,100,70,.25)"; x.fillRect(0, y, w, 2);
    }
  });
  texPiso.wrapS = texPiso.wrapT = THREE.RepeatWrapping; texPiso.repeat.set(3, 2.1);
  MAT.piso = new THREE.MeshStandardMaterial({ map: texPiso, roughness: 0.45, metalness: 0.02 });
  escena.add(malla(new THREE.BoxGeometry(16.6, 0.6, 11.6), MAT.base, 0, -0.5, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 0.4, 11), MAT.piso, 0, -0.2, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 4.6, 0.3), MAT.pared, 0, 2.3, -5.65));
  escena.add(malla(new THREE.BoxGeometry(0.3, 4.6, 11.3), MAT.pared, -8.15, 2.3, 0));
  escena.add(malla(new THREE.BoxGeometry(16, 0.16, 0.06), MAT.zocalo, 0, 0.08, -5.48));
  escena.add(malla(new THREE.BoxGeometry(0.06, 0.16, 11), MAT.zocalo, -7.98, 0.08, 0));
  // franja rosada en lo alto de las paredes
  escena.add(malla(new THREE.BoxGeometry(16, 0.1, 0.32), MAT.zocalo, 0, 4.6, -5.65));
  escena.add(malla(new THREE.BoxGeometry(0.32, 0.1, 11.3), MAT.zocalo, -8.15, 4.6, 0));
  // Alfombra de la sala de reuniones
  const alfombra = new THREE.Mesh(new THREE.CircleGeometry(3.15, 64), new THREE.MeshStandardMaterial({ color: 0xf8dde6, roughness: 0.95 }));
  alfombra.rotation.x = -Math.PI / 2; alfombra.position.set(MESA.x, 0.005, MESA.z); alfombra.receiveShadow = true; escena.add(alfombra);
  const borde = new THREE.Mesh(new THREE.RingGeometry(3.02, 3.15, 64), new THREE.MeshStandardMaterial({ color: 0xe9b7c6, roughness: 0.6 }));
  borde.rotation.x = -Math.PI / 2; borde.position.set(MESA.x, 0.008, MESA.z); escena.add(borde);

  // Ventanal con la ciudad al atardecer
  const ciudad = lienzo(1024, 400, (x, w, h) => {
    const cielo = x.createLinearGradient(0, 0, 0, h);
    cielo.addColorStop(0, "#2b2a6e"); cielo.addColorStop(0.45, "#8b5fbf"); cielo.addColorStop(0.75, "#f59ab8"); cielo.addColorStop(1, "#ffd3a8");
    x.fillStyle = cielo; x.fillRect(0, 0, w, h);
    const azar = semillaAzar(11);
    for (let i = 0; i < 60; i++) { x.fillStyle = `rgba(255,255,255,${.3 + azar() * .5})`; x.fillRect(azar() * w, azar() * 120, 2, 2); }
    for (const [tono, alto, prob] of [["#6a4c93", 170, .15], ["#3b2d63", 250, .3]]) {
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
    x.clearRect(0, 0, w, h); x.fillStyle = "#1c1a1f"; x.font = "800 150px Sora, 'Segoe UI', sans-serif"; x.textAlign = "center";
    x.fillText("FARMASI", w / 2, 170); x.fillStyle = "#d4517f"; x.font = "500 50px 'Segoe UI', sans-serif"; x.fillText("EQUIPO DE ISA", w / 2, 250);
  });
  const placaLetrero = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 1.23), new THREE.MeshBasicMaterial({ map: letrero, transparent: true }));
  placaLetrero.position.set(-4.4, 3.35, -5.48); placaLetrero.scale.setScalar(0.85); escena.add(placaLetrero);
  const tablero = lienzo(640, 360, (x, w, h) => {
    x.fillStyle = "#fff4f8"; x.fillRect(0, 0, w, h);
    x.fillStyle = "#3a2440"; x.font = "600 26px 'Segoe UI', sans-serif"; x.fillText("Resultados de la semana", 28, 46);
    const barras = [60, 90, 75, 120, 105, 150, 170];
    barras.forEach((b, i) => { const g = x.createLinearGradient(0, 300 - b, 0, 300); g.addColorStop(0, "#ffb3cf"); g.addColorStop(1, "#e8457f");
      x.fillStyle = g; x.fillRect(40 + i * 62, 300 - b, 38, b); });
    x.strokeStyle = "#c99a4a"; x.lineWidth = 4; x.beginPath();
    barras.forEach((b, i) => { const px = 59 + i * 62, py = 280 - b * 0.9; i ? x.lineTo(px, py) : x.moveTo(px, py); }); x.stroke();
    x.fillStyle = "#a7889a"; x.font = "500 18px 'Segoe UI'"; ["L", "M", "M", "J", "V", "S", "D"].forEach((d, i) => x.fillText(d, 52 + i * 62, 330));
  });
  const tv = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 1.58), new THREE.MeshBasicMaterial({ map: tablero, toneMapped: false }));
  tv.position.set(-7.94, 2.6, -1.9); tv.rotation.y = Math.PI / 2; escena.add(tv);
  escena.add(malla(new THREE.BoxGeometry(0.08, 1.72, 2.94), MAT.oscuro, -7.98, 2.6, -1.9));

  // Repisa con libros (pared izquierda) y cafetería (derecha)
  const repisa = new THREE.Group(); repisa.position.set(-7.8, 0.4, 2.5); escena.add(repisa);
  [1.6, 2.5].forEach((y) => repisa.add(malla(new THREE.BoxGeometry(0.4, 0.05, 2.4), MAT.blanco, 0.1, y, 0)));
  const colores = [0xf4a6c0, 0xe8457f, 0xffd8a8, 0xc9b6ec, 0xffffff, 0xd8b46a, 0xf7d6df];
  for (let i = 0; i < 14; i++) {
    const alto = 0.32 + ((i * 37) % 13) / 60;
    repisa.add(malla(new THREE.BoxGeometry(0.28, alto, 0.09), new THREE.MeshStandardMaterial({ color: colores[i % colores.length], roughness: .6 }),
      0.12, (i < 7 ? 1.625 : 2.525) + alto / 2, -1.0 + (i % 7) * 0.13));
  }
  const cafe = new THREE.Group(); cafe.position.set(7.15, 0, -3.9); escena.add(cafe);
  cafe.add(malla(new THREE.BoxGeometry(1.0, 0.95, 2.6), MAT.blanco, 0, 0.475, 0));
  cafe.add(malla(new THREE.BoxGeometry(1.06, 0.05, 2.66), MAT.madera, 0, 0.97, 0));
  cafe.add(malla(new THREE.BoxGeometry(0.45, 0.55, 0.4), MAT.oscuro, 0, 1.27, -0.6));
  cafe.add(malla(new THREE.BoxGeometry(0.3, 0.06, 0.06), new THREE.MeshBasicMaterial({ color: 0xff9cc6, toneMapped: false }), -0.23, 1.38, -0.6));
  const floresCafe = crearFlores(1.3); floresCafe.position.set(0, 0.995, 0.95); cafe.add(floresCafe);
  [0.2, 0.45, 0.7].forEach((z, i) => cafe.add(malla(new THREE.CylinderGeometry(0.06, 0.05, 0.12, 14), new THREE.MeshStandardMaterial({ color: colores[i] }), -0.15, 1.05, z)));

  // Plantas grandes
  [[-7.3, -4.85, 1.2], [-7.3, 5.0, 1.0], [7.4, 5.1, 0.95], [-0.1, -4.95, 0.75]].forEach(([x, z, e]) => { const p = crearPlanta(e); p.position.set(x, 0, z); escena.add(p); });

  // Mesa de reuniones y el holograma de Isa
  const mesa = new THREE.Group(); mesa.position.copy(MESA); escena.add(mesa);
  mesa.add(malla(new THREE.CylinderGeometry(1.65, 1.6, 0.08, 64), MAT.blanco, 0, 0.78, 0));
  mesa.add(malla(new THREE.TorusGeometry(1.64, 0.03, 8, 80), new THREE.MeshStandardMaterial({ color: 0xe8c48a, roughness: 0.35, metalness: 0.3 }), 0, 0.78, 0).rotateX(Math.PI / 2));
  mesa.add(malla(new THREE.CylinderGeometry(0.22, 0.32, 0.74, 24), MAT.gris, 0, 0.37, 0));
  mesa.add(malla(new THREE.CylinderGeometry(0.75, 0.8, 0.04, 40), MAT.gris, 0, 0.02, 0));
  const proyector = malla(new THREE.CylinderGeometry(0.34, 0.38, 0.06, 40), MAT.cian, 0, 0.84, 0); mesa.add(proyector);

  const holograma = new THREE.Group(); holograma.position.set(MESA.x, 2.75, MESA.z); escena.add(holograma);
  const texCono = lienzo(4, 128, (x, w, h) => { const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, "rgba(255,140,190,0)"); g.addColorStop(1, "rgba(255,140,190,.5)"); x.fillStyle = g; x.fillRect(0, 0, w, h); });
  const cono = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.32, 1.85, 40, 1, true),
    new THREE.MeshBasicMaterial({ map: texCono, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, toneMapped: false }));
  cono.position.set(MESA.x, 0.84 + 0.925, MESA.z); escena.add(cono);
  const resplandor = new THREE.Sprite(new THREE.SpriteMaterial({ map: lienzo(128, 128, (x) => {
    const g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, "rgba(255,225,238,1)"); g.addColorStop(.3, "rgba(255,130,185,.45)"); g.addColorStop(1, "rgba(255,130,185,0)");
    x.fillStyle = g; x.fillRect(0, 0, 128, 128); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  resplandor.scale.setScalar(2.3); holograma.add(resplandor);
  const nucleo = new THREE.Mesh(new THREE.SphereGeometry(0.36, 40, 30), new THREE.MeshPhysicalMaterial({
    color: 0xffd0e2, emissive: 0xff4f9a, emissiveIntensity: 1.6, roughness: 0.15, clearcoat: 1, transparent: true, opacity: 0.92 }));
  holograma.add(nucleo);
  const malla20 = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(0.55, 1)),
    new THREE.LineBasicMaterial({ color: 0xffd0e2, transparent: true, opacity: 0.55, toneMapped: false }));
  holograma.add(malla20);
  const anillos = [0.7, 0.86, 1.02].map((r, i) => {
    const a = new THREE.Mesh(new THREE.TorusGeometry(r, 0.012, 8, 120), new THREE.MeshBasicMaterial({ color: i === 1 ? 0xffd27f : 0xffa6c9, toneMapped: false, transparent: true, opacity: 0.8 }));
    a.rotation.set(Math.PI / 2 + (i - 1) * 0.5, i * 0.7, 0); holograma.add(a); return a;
  });
  const nPart = 260, posPart = new Float32Array(nPart * 3), azarP = semillaAzar(5);
  for (let i = 0; i < nPart; i++) {
    const r = 0.6 + azarP() * 0.7, t = azarP() * Math.PI * 2, f = Math.acos(2 * azarP() - 1);
    posPart.set([r * Math.sin(f) * Math.cos(t), r * Math.cos(f) * 0.6, r * Math.sin(f) * Math.sin(t)], i * 3);
  }
  const geoPart = new THREE.BufferGeometry(); geoPart.setAttribute("position", new THREE.BufferAttribute(posPart, 3));
  const particulas = new THREE.Points(geoPart, new THREE.PointsMaterial({ color: 0xffe0ec, size: 0.05, transparent: true, opacity: 0.85, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  holograma.add(particulas);
  const luzIsa = new THREE.PointLight(0xff8fc0, 6, 9, 1.6); luzIsa.position.set(0, 0, 0); holograma.add(luzIsa);
  const etiquetaIsa = document.createElement("div"); etiquetaIsa.className = "etq-isa";
  etiquetaIsa.innerHTML = "<b>Isa</b><span>Lista para ayudarte</span>";
  const objIsa = new CSS2DObject(etiquetaIsa); objIsa.position.set(0, -1.35, 0); holograma.add(objIsa);


  /* ---------- robots y escritorios ---------- */
  const robots = new Map(); let grupoEquipo = new THREE.Group(); escena.add(grupoEquipo);
  const ocupados = new Set();

  // Solo el nombre: limpio. Lo que está haciendo cada una se ve en el panel "Misión en curso".
  function etiqueta(agente) {
    const d = document.createElement("div"); d.className = "etq-robot"; d.style.setProperty("--c", agente.color);
    d.innerHTML = `<b>${agente.nombre.replace(/[<>&]/g, "")}</b>`;
    return d;
  }
  function setEquipo(agentes) {
    escena.remove(grupoEquipo);
    grupoEquipo.traverse((o) => { if (o.isCSS2DObject) o.element.remove(); });
    grupoEquipo = new THREE.Group(); escena.add(grupoEquipo); robots.clear(); ocupados.clear();
    PUNTOS_LEJOS = puntosDelEquipo(agentes.length); ajustar();
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
  // El nombre se ilumina mientras trabaja y se pone verde un momento al terminar.
  function estadoEtiqueta(r, clase) { r.el.dataset.estado = clase || ""; }
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
    if (r.estado !== "sentado" && r.estado !== "volviendo") return;
    r.estado = "yendo"; estadoEtiqueta(r, "reunion");
    let libre = LUGARES.findIndex((_, i) => !ocupados.has(i)); if (libre < 0) libre = 0; ocupados.add(libre); r.lugar = libre;
    r.metaSentado = 0; await esperar(650);
    r.objeto.visible = true;
    r.camino = [r.salida.clone(), ...rodear(r.salida, LUGARES[libre]), LUGARES[libre].clone()]; await llegar(r);
    if (r.estado !== "yendo") return;
    r.estado = "reunion"; r.metaGiro = anguloHacia(LUGARES[libre], MESA);
  }
  function actividad(id, texto) {
    const r = robots.get(id); if (!r) return; r.actividad = texto;
  }
  async function liberar(id) {
    const r = robots.get(id); if (!r || r.estado === "sentado" || r.estado === "volviendo" || r.estado === "festejo") return;
    while (r.estado === "yendo") await esperar(200);
    r.estado = "festejo"; r.sonrisa.visible = true; estadoEtiqueta(r, "listo");
    await esperar(1900);
    r.estado = "volviendo"; ocupados.delete(r.lugar); r.lugar = -1; r.actividad = "";
    r.camino = [...rodear(r.raiz.position, r.salida).slice(1), r.salida.clone(), r.casa.clone()]; await llegar(r);
    if (r.estado !== "volviendo") return;
    r.metaGiro = r.giroCasa; r.objeto.visible = false; r.metaSentado = 1; r.estado = "sentado"; r.sonrisa.visible = false;
    setTimeout(() => { if (r.estado === "sentado") estadoEtiqueta(r, ""); }, 4000);
  }

  /* ---------- Reunión de equipo: todos se acercan a Isa ---------- */
  let enReunionEquipo = false;
  function reunirEquipo() {
    if (enReunionEquipo) return;
    enReunionEquipo = true; isa("pensando", "Reunión de equipo");
    // Cada robot sale con un poquito de diferencia, como gente levantándose para una reunión
    [...robots.keys()].forEach((id, i) => setTimeout(() => {
      if (enReunionEquipo) { convocar(id); actividad(id, "Escuchando a Isa"); }
    }, MOVIMIENTO ? i * 450 : 0));
    reunion(true);
  }
  function notasReunion(notas) {
    robots.forEach((r, id) => {
      const n = notas?.[id]; if (!n || n.nota == null) return;
      const d = n.antes == null ? "" : n.nota > n.antes ? " ▲" : n.nota < n.antes ? " ▼" : " =";
      r.actividad = `Nota ${Number(n.nota).toFixed(1)}${d}`;
      if (n.nota >= 9) r.sonrisa.visible = true;
    });
  }
  async function despedirEquipo() {
    if (!enReunionEquipo) return;
    enReunionEquipo = false;
    await Promise.all([...robots.keys()].map((id, i) => esperar(i * 300).then(() => liberar(id))));
    reunion(false); isa("reposo");
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
    const marcoR = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(1.57, 1.57)), new THREE.LineBasicMaterial({ color: 0xff9cc6, transparent: true, toneMapped: false }));
    g.add(marcoR);
    if (esImagen) cargador.load(url, (t) => { t.colorSpace = THREE.SRGBColorSpace; mat.map = t; mat.needsUpdate = true; });
    else { mat.map = lienzo(256, 256, (x) => { x.fillStyle = "#2a1f3d"; x.fillRect(0, 0, 256, 256); x.fillStyle = "#ff9cc6"; x.font = "120px sans-serif"; x.textAlign = "center"; x.fillText(/\.mp4/i.test(url) ? "▶" : "▦", 128, 170); }); }
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
    // Margen en píxeles: las etiquetas con el nombre miden lo mismo en cualquier pantalla
    // (~90 px a cada lado del robot), más el vaivén suave de la cámara y el mouse.
    encuadrar(PUNTOS_LEJOS, Math.max(0.65, 0.95 - 70 / h), CAM_LEJOS, MIRA_LEJOS, DIRECCION, Math.max(0.6, 0.96 - 120 / w));
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
    r.falda.scale.y = 1 - 0.55 * s; r.falda.position.z = 0.05 * s;   // al sentarse la falda se acomoda
    r.boca.visible = !r.sonrisa.visible;
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
    // En la reunión de equipo todos levantan la vista hacia el holograma de Isa
    const miraIsa = enReunionEquipo && r.estado === "reunion" ? 0.22 : 0;
    r.cabeza.rotation.x = Math.sin(t * 3 + r.semilla) * 0.07 * ha - 0.18 * ha - miraIsa * ha + 0.12 * teclear;
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

  const api = { setEquipo, convocar, actividad, liberar, isa, reunion, mostrarResultado, reunirEquipo, notasReunion, despedirEquipo };
  window.oficina3d = api;   // útil para probar desde la consola del navegador
  api.depurar = () => ({ cam: camara.position.toArray(), lejos: CAM_LEJOS.toArray(), cerca: CAM_CERCA.toArray(), mira: MIRA_CERCA.toArray(), enfoque, w: contenedor.clientWidth, h: contenedor.clientHeight });
  return api;
}
