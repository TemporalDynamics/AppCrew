const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accentColor": "#1D7C5A",
  "paperTone": "#F4F1DC",
  "codeDensity": 1,
  "gridOpacity": 0.38
}/*EDITMODE-END*/;

const screens = [
  {
    step: 1,
    label: 'Ciudad viva',
    eyebrow: 'Mintly / operador',
    title: 'Habla con tu dinero como si fuera una mini ciudad.',
    body: 'Describe lo que quieres en lenguaje natural. Mintly convierte la frase en reglas simples para hogares, comercios y rutas de gasto.',
    primary: 'Crear mi distrito',
    secondary: 'Entrar con una ciudad existente',
    accent: 'city',
  },
  {
    step: 2,
    label: 'Permisos',
    eyebrow: 'Agentes locales',
    title: 'Elige qué habitantes pueden tocar tu atención.',
    body: 'Los permisos son como servicios municipales: solo activamos avisos que ayudan a dirigir tu flujo semanal sin invadirte.',
    primary: 'Autorizar agentes útiles',
    secondary: 'Configurar después',
    accent: 'terminal',
  },
  {
    step: 3,
    label: 'Primera orden',
    eyebrow: 'Comando natural',
    title: 'Escribe una orden y mira cómo se traduce.',
    body: 'No tienes que llenar formularios. Una frase basta para crear una rutina, priorizar personas y dejar una pista verificable.',
    primary: 'Ejecutar orden segura',
    secondary: 'Ver otras órdenes',
    accent: 'signal',
  },
];

const permissions = [
  { title: 'Agente de facturas', detail: 'Avisa 48 h antes de cortes críticos', state: 'On' },
  { title: 'Pulso de barrio', detail: 'Resumen semanal de hábitos', state: 'On' },
  { title: 'Promos de mercado', detail: 'Ofertas y novedades comerciales', state: 'Off' },
];

const goals = [
  { name: '“Baja ocio si renta sube”', meta: 'if rent.delta > 0 → suggest dining cap', selected: true },
  { name: '“Cuida a Ana hasta el viernes”', meta: 'protect emergency buffer + transit pass', selected: false },
  { name: '“Muéstrame fugas pequeñas”', meta: 'scan subscriptions under $12', selected: false },
];

function PhoneFrame({ children }) {
  return (
    <div className="device" aria-label="iPhone onboarding preview">
      <div className="island" aria-hidden="true" />
      <div className="screen">{children}</div>
    </div>
  );
}

function StatusBar() {
  return (
    <div className="status" aria-hidden="true">
      <span>9:41</span>
      <span className="statusDots"><i /><i /><b /></span>
    </div>
  );
}

function Progress({ active }) {
  return (
    <nav className="progress" aria-label={`Onboarding progress, step ${active} of 3`}>
      {screens.map((screen) => (
        <span key={screen.step} className={screen.step <= active ? 'dot active' : 'dot'} aria-label={`${screen.label}${screen.step === active ? ', current step' : ''}`} />
      ))}
    </nav>
  );
}

function AppGlyph({ type }) {
  return (
    <div className={`glyph ${type}`} aria-hidden="true">
      {type === 'city' && <><span /><span /><em /></>}
      {type === 'terminal' && <><span /><b /></>}
      {type === 'signal' && <><span /><b /></>}
    </div>
  );
}

function WelcomePanel() {
  return (
    <section className="simPanel" aria-label="Natural language city command preview">
      <p className="cardKicker">lenguaje natural</p>
      <div className="promptBubble">“Haz que mi barrio llegue tranquilo al viernes.”</div>
      <div className="citizenGrid" aria-hidden="true">
        {['Ana', 'Luis', 'Mora', 'Kai', 'Nora', 'Ivo'].map((name, index) => <span key={name} style={{ '--delay': index }}><b />{name}</span>)}
      </div>
      <code>rule weekly_buffer: protect 18% cashflow</code>
    </section>
  );
}

function PermissionPanel() {
  return (
    <section className="permissionCard" aria-label="Notification permission settings">
      <div className="permissionHeader">
        <span className="terminalTile" aria-hidden="true">&gt;_</span>
        <div>
          <h3>Permisos de agentes</h3>
          <p>Servicios municipales de atención</p>
        </div>
      </div>
      <div className="permissionList">
        {permissions.map((item) => (
          <div className="permissionRow" key={item.title}>
            <div>
              <strong>{item.title}</strong>
              <span>{item.detail}</span>
            </div>
            <span className={item.state === 'On' ? 'switch on' : 'switch'} role="switch" aria-checked={item.state === 'On'} tabIndex="0"><i /></span>
          </div>
        ))}
      </div>
    </section>
  );
}

function GoalPanel() {
  return (
    <section className="goalList" aria-label="Suggested natural language commands">
      {goals.map((goal) => (
        <button className={goal.selected ? 'goal selected' : 'goal'} key={goal.name} type="button" aria-pressed={goal.selected}>
          <span className="radio" aria-hidden="true" />
          <span><strong>{goal.name}</strong><em>{goal.meta}</em></span>
        </button>
      ))}
      <div className="successHint" role="status">
        <span aria-hidden="true">✓</span>
        <p><strong>Pista de éxito:</strong> la orden queda como tarjeta editable: texto humano arriba, regla tipo código abajo.</p>
      </div>
    </section>
  );
}

function ScreenContent({ screen }) {
  return (
    <article className="appScreen" aria-labelledby={`screen-title-${screen.step}`}>
      <StatusBar />
      <header className="topbar">
        <button type="button" className="ghostButton" aria-label={screen.step === 1 ? 'Close onboarding' : 'Go back'}>{screen.step === 1 ? 'Skip' : 'Back'}</button>
        <Progress active={screen.step} />
      </header>
      <main className="content">
        <div className="heroMark"><AppGlyph type={screen.accent} /></div>
        <p className="eyebrow">{screen.eyebrow}</p>
        <h2 id={`screen-title-${screen.step}`}>{screen.title}</h2>
        <p className="bodyCopy">{screen.body}</p>
        {screen.step === 1 && <WelcomePanel />}
        {screen.step === 2 && <PermissionPanel />}
        {screen.step === 3 && <GoalPanel />}
      </main>
      <footer className="actions">
        <button type="button" className="primary">{screen.primary}</button>
        <button type="button" className="secondary">{screen.secondary}</button>
      </footer>
    </article>
  );
}

function App() {
  return (
    <div className="stage">
      <style>{css}</style>
      <header className="pageHeader">
        <p>Onboarding estilo Paperclip / SimCity</p>
        <h1>Mintly como simulador de personas y reglas naturales</h1>
      </header>
      <section className="phoneGrid" aria-label="Onboarding screens">
        {screens.map((screen) => <PhoneFrame key={screen.step}><ScreenContent screen={screen} /></PhoneFrame>)}
      </section>
    </div>
  );
}

const css = `
  :root {
    --accent: var(--ocd-tweak-accent-color, ${TWEAK_DEFAULTS.accentColor});
    --paper: var(--ocd-tweak-paper-tone, ${TWEAK_DEFAULTS.paperTone});
    --density: var(--ocd-tweak-code-density, ${TWEAK_DEFAULTS.codeDensity});
    --grid-opacity: var(--ocd-tweak-grid-opacity, ${TWEAK_DEFAULTS.gridOpacity});
    --ink: #253326;
    --muted: #647160;
    --line: #A9C4A7;
    --mint: #DDF4D4;
    --screen: #F8F5DF;
    --shadow: rgba(35, 62, 44, .18);
    font-family: ui-rounded, "Avenir Next", system-ui, sans-serif;
    color: var(--ink);
    background: var(--paper);
  }
  * { box-sizing: border-box; }
  body { margin: 0; min-width: 320px; }
  .stage { min-height: 100vh; padding: clamp(14px, 2.5vw, 28px); background:
      linear-gradient(rgba(29,124,90,var(--grid-opacity)) 1px, transparent 1px),
      linear-gradient(90deg, rgba(29,124,90,var(--grid-opacity)) 1px, transparent 1px),
      radial-gradient(circle at 18% 14%, #D7F2C2 0 14%, transparent 34%),
      var(--paper); background-size: 22px 22px, 22px 22px, auto, auto; }
  .pageHeader { max-width: 930px; margin: 0 auto 14px; display: flex; justify-content: space-between; gap: 24px; align-items: end; }
  .pageHeader p { margin: 0; font: 800 12px/1.1 ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; letter-spacing: .14em; color: #556551; }
  .pageHeader h1 { margin: 0; max-width: 620px; font-size: clamp(24px, 3.8vw, 38px); line-height: .92; letter-spacing: -.055em; text-align: right; }
  .phoneGrid { max-width: 1090px; margin: 0 auto; display: grid; grid-template-columns: repeat(3, minmax(285px, 1fr)); gap: clamp(18px, 2.5vw, 30px); align-items: start; }
  .device { width: min(100%, 286px); min-height: 562px; margin: 0 auto; padding: 9px; border-radius: 38px; background: #283427; box-shadow: 0 25px 60px rgba(41, 62, 42, .26), inset 0 0 0 2px #111b14; position: relative; }
  .island { position: absolute; z-index: 3; width: 88px; height: 27px; border-radius: 999px; background: #121914; left: 50%; top: 20px; transform: translateX(-50%); }
  .screen { min-height: 544px; overflow: hidden; border-radius: 29px; background:
      linear-gradient(rgba(37,51,38,.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(37,51,38,.07) 1px, transparent 1px),
      var(--screen); background-size: 18px 18px; border: 2px solid #5D704E; }
  .appScreen { min-height: 672px; display: flex; flex-direction: column; transform: scale(.805); transform-origin: top center; width: 124.23%; margin-left: -12.12%; }
  .status { height: 42px; padding: 15px 24px 0; display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 900; }
  .statusDots { display: inline-flex; gap: 3px; align-items: center; } .statusDots i, .statusDots b { display:block; background: var(--ink); } .statusDots i { width: 4px; height: 9px; border-radius: 2px; } .statusDots b { width: 16px; height: 8px; border-radius: 3px; }
  .topbar { padding: 4px 22px 0; display: flex; justify-content: space-between; align-items: center; }
  .ghostButton { min-height: 36px; padding: 0 12px; border: 1px solid #B9C9A9; border-radius: 10px; background: rgba(255,255,245,.58); color: var(--ink); font-weight: 900; font-size: 12px; }
  .progress { display: flex; gap: 7px; align-items: center; } .dot { width: 10px; height: 10px; border-radius: 50%; border: 1px solid #7A936E; background: #F5F2DD; } .dot.active { width: 28px; border-radius: 999px; background: var(--accent); border-color: var(--accent); }
  .content { flex: 1; padding: 16px 24px 10px; display: flex; flex-direction: column; }
  .heroMark { width: 76px; height: 76px; border: 2px solid #263428; border-radius: 12px; background: #C8E7BA; box-shadow: 6px 6px 0 #263428; display: grid; place-items: center; margin-bottom: 18px; }
  .glyph { width: 54px; height: 54px; position: relative; }
  .glyph.city span:first-child { position:absolute; left:5px; bottom:5px; width:14px; height:29px; background: var(--accent); box-shadow: 18px -9px 0 #77B55F, 36px -2px 0 #405C3D; }
  .glyph.city span:nth-child(2) { position:absolute; left:10px; top:11px; width:5px; height:5px; background:#F7F2D6; box-shadow: 18px 0 #F7F2D6, 36px 7px #F7F2D6, 0 11px #F7F2D6, 18px 16px #F7F2D6; }
  .glyph.city em { position:absolute; left:6px; bottom:0; width:44px; height:5px; background:#263428; }
  .glyph.terminal { border:2px solid #263428; border-radius:8px; background:#263428; color:#DCF7CB; } .glyph.terminal::before { content:'> ask'; position:absolute; left:8px; top:10px; font:800 11px ui-monospace, monospace; } .glyph.terminal span { position:absolute; left:8px; top:29px; width:30px; height:4px; background:#DCF7CB; }
  .glyph.signal span { position:absolute; inset:9px; border:4px solid var(--accent); border-radius:50%; } .glyph.signal b { position:absolute; left:24px; top:24px; width:7px; height:7px; border-radius:50%; background:#263428; box-shadow: 0 0 0 8px #DDF4D4; }
  .eyebrow { margin: 0 0 8px; color: #54634B; font: 900 12px/1.1 ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; letter-spacing: .11em; }
  h2 { margin: 0; max-width: 285px; font-size: 30px; line-height: .98; letter-spacing: -.045em; }
  .bodyCopy { margin: 12px 0 14px; color: var(--muted); font-size: 14px; line-height: 1.42; font-weight: 650; }
  .simPanel, .permissionCard, .goalList { margin-top: auto; }
  .simPanel, .permissionCard { border: 2px solid #263428; border-radius: 14px; padding: calc(var(--density) * 12px); background: rgba(255,255,245,.72); box-shadow: 5px 5px 0 #263428; }
  .cardKicker { margin: 0 0 8px; color: #556551; font: 900 11px ui-monospace, monospace; text-transform: uppercase; letter-spacing: .12em; }
  .promptBubble { border:1px dashed #7A936E; border-radius: 12px; background:#FAF7E4; padding: 10px; font-weight: 900; line-height:1.18; }
  .citizenGrid { display:grid; grid-template-columns: repeat(3,1fr); gap:7px; margin: 10px 0; } .citizenGrid span { min-height:42px; border:1px solid #A9C4A7; border-radius:10px; display:grid; place-items:center; font-size:10px; font-weight:900; background:#E4F3D8; } .citizenGrid b { width:13px; height:13px; border-radius:50% 50% 40% 40%; background:var(--accent); box-shadow: 0 10px 0 #6A8C58; }
  code { display:block; padding:9px; border-radius:9px; background:#263428; color:#DDF4D4; font: 800 11px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: normal; }
  .permissionHeader { display: flex; gap: 12px; align-items: center; padding-bottom: 12px; border-bottom: 1px solid #B9C9A9; } .terminalTile { width:42px; height:42px; border-radius:10px; display:grid; place-items:center; background:#263428; color:#DDF4D4; font:900 15px ui-monospace, monospace; }
  .permissionHeader h3 { margin: 0; font-size: 17px; } .permissionHeader p { margin: 3px 0 0; font-size: 12px; color: var(--muted); }
  .permissionRow { min-height: 50px; display: flex; align-items: center; justify-content: space-between; gap: 10px; border-bottom: 1px solid #D4DABF; } .permissionRow:last-child { border-bottom: 0; } .permissionRow strong, .goal strong { display: block; font-size: 13px; } .permissionRow span:not(.switch) { display: block; color: var(--muted); font-size: 11.5px; margin-top: 2px; }
  .switch { width: 48px; height: 30px; border-radius: 9px; background: #D4DABF; padding: 3px; display: inline-flex; align-items: center; flex: 0 0 auto; border: 2px solid #263428; } .switch i { width: 20px; height: 20px; background: #fffbe8; border: 2px solid #263428; border-radius: 6px; } .switch.on { background: var(--accent); justify-content: flex-end; }
  .goalList { display: grid; gap: 8px; }
  .goal { min-height: 55px; width: 100%; border: 2px solid #263428; border-radius: 12px; background: rgba(255,255,245,.72); text-align: left; padding: 8px 9px; display: grid; grid-template-columns: 24px 1fr; gap: 8px; align-items: center; color: var(--ink); box-shadow: 3px 3px 0 #263428; } .goal.selected { background: #DFF4D3; outline: 3px solid rgba(29,124,90,.22); }
  .radio { width: 20px; height: 20px; border-radius: 6px; border: 2px solid #263428; display: block; position: relative; background:#FFFBE8; } .selected .radio::after { content: ''; position: absolute; inset: 4px; border-radius: 3px; background: var(--accent); } .goal em { display: block; font-style: normal; color: #52624C; font: 800 10.5px/1.25 ui-monospace, SFMono-Regular, Menlo, monospace; margin-top: 3px; }
  .successHint { border: 2px solid #263428; border-radius: 12px; padding: 8px; display: flex; gap: 8px; background: #CFEFC4; color: #243226; font-size: 11.5px; line-height: 1.28; box-shadow: 3px 3px 0 #263428; } .successHint span { width: 23px; height: 23px; border-radius: 7px; background: var(--accent); color: white; display: grid; place-items: center; font-weight: 900; flex: 0 0 auto; border: 2px solid #263428; } .successHint p { margin: 0; }
  .actions { padding: 8px 22px 20px; display: grid; gap: 7px; } .primary, .secondary { min-height: 47px; border-radius: 12px; font-weight: 950; letter-spacing: -.01em; border: 2px solid #263428; } .primary { background: var(--accent); color: #fff; box-shadow: 4px 4px 0 #263428; } .secondary { background: #FFFBE8; color: #243226; }
  button:focus-visible, .switch:focus-visible { outline: 3px solid #102317; outline-offset: 3px; box-shadow: 0 0 0 6px rgba(221,244,212,.9); } button:active { transform: translateY(1px) scale(.99); }
  @media (max-width: 1000px) { .phoneGrid { grid-template-columns: 1fr; } .pageHeader { display:block; max-width: 342px; } .pageHeader h1 { text-align:left; margin-top:10px; } }
  @media (max-width: 420px) { .stage { padding: 18px 12px; } .device { width: 100%; } }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; } }
`;

ReactDOM.createRoot(document.getElementById('root')).render(<App />);