import React from "react";
import {AbsoluteFill, Img, staticFile, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from "remotion";
import data from "./data.json";

const C = {bg: "#0B0F17", card: "#131B2E", border: "#23304C", text: "#F8FAFC", muted: "#94A3B8",
  kept: "#10B981", broken: "#EF4444", in_progress: "#F59E0B", undecided: "#8B5CF6", stalled: "#64748B", accent: "#38BDF8"};
const vc = (v: string) => (C as Record<string, string>)[v] ?? C.accent;
const page: React.CSSProperties = {backgroundColor: C.bg, padding: 80, color: C.text, fontFamily: "Inter, sans-serif"};

const Badge: React.FC<{label: string; color: string}> = ({label, color}) => (
  <span style={{backgroundColor: `${color}22`, border: `2px solid ${color}`, color, padding: "6px 16px",
    borderRadius: 999, fontSize: 22, fontWeight: 700, letterSpacing: 1}}>{label}</span>
);

const CAPTIONS: [number, number, string][] = [
  [0, 120, "Built at the Archil AI Hackathon, Nov 10"],
  [120, 270, "Using Archil for persistent storage and Keenable for web search and fetch"],
  [270, 660, "Real quotes, real sources. Each promise gets a verdict and a reason."],
  [660, 800, "1 Fetch: save the source and lock it with a SHA-256 hash"],
  [800, 920, "2–3 Extract the exact quote, then gate it: real, measurable, SF"],
  [920, 1020, "4–5 Two isolated advocates argue; Arbitrator code decides"],
  [1020, 1130, "Watchdog test: one word in the quote is altered"],
  [1130, 1260, "The deterministic check catches it"],
  [1260, 1380, "A changed quote never reaches the public table"],
  [1380, 1800, "Models draft. Deterministic code decides."],
];

const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const c = CAPTIONS.find(([a, b]) => f >= a && f < b);
  if (!c) return null;
  return (
    <div style={{position: "absolute", left: 80, right: 80, bottom: 40, textAlign: "center", fontSize: 38, fontWeight: 600,
      color: "#fff", background: "#000d", padding: "14px 28px", borderRadius: 12, fontFamily: "Inter, sans-serif",
      opacity: interpolate(f, [c[0], c[0] + 8, c[1] - 8, c[1]], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})}}>
      {c[2]}
    </div>
  );
};

const Intro: React.FC = () => {
  const f = useCurrentFrame();
  const up = (s: number) => interpolate(f, [s, s + 12], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return (
    <AbsoluteFill style={{...page, justifyContent: "center"}}>
      <div style={{color: C.accent, fontSize: 28, fontWeight: 700, letterSpacing: 3, opacity: up(0)}}>ARCHIL AI HACKATHON · THE RECORD OF OUR CITY · SAN FRANCISCO</div>
      <h1 style={{fontSize: 150, margin: "10px 0", opacity: up(10)}}>SF Promises</h1>
      <p style={{fontSize: 36, color: C.muted, maxWidth: 1500, lineHeight: 1.4, opacity: up(30)}}>
        From mayoral pledges at City Hall to the Valkyries at Chase Center, Dead &amp; Company in Golden Gate Park, Waymo on our streets and affordable homes at Mission Rock — we check who kept their word.
      </p>
      <div style={{display: "flex", gap: 24, marginTop: 30, opacity: up(120)}}>
        {[["ARCHIL", "persistent disk for the SQLite DB + saved sources"], ["KEENABLE", "web search and page fetch for every source"]].map(([n, d]) => (
          <div key={n} style={{background: C.card, border: `2px solid ${C.accent}`, borderRadius: 16, padding: "20px 28px", fontSize: 28}}>
            <b style={{color: C.accent}}>{n}</b> · {d}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Cards: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const c = data.counts;
  const list = ["P82", "P11", "P05", "P10", "P21"].map((id) => data.cards.find((x) => x.id === id)!);
  const why: Record<string, string> = {
    P82: "WNBA title won inside the five-year window",
    P11: "Sphere residencies + Golden Gate Park shows followed",
    P05: "Numeric shelter target not met",
    P10: "Partial completion, full scope unresolved",
    P21: "JFK Promenade made permanent",
  };
  return (
    <AbsoluteFill style={page}>
      <div style={{color: C.accent, fontSize: 24, fontWeight: 700, letterSpacing: 2}}>PROMISE · EVIDENCE · VERDICT</div>
      <div style={{display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 20, marginTop: 24}}>
        {list.map((p, i) => {
          const pop = spring({frame: f - i * 12, fps, config: {damping: 14}});
          return (
            <div key={p.id} style={{transform: `scale(${pop})`, opacity: pop, backgroundColor: C.card, border: `2px solid ${vc(p.verdict)}`,
              borderRadius: 20, padding: 24, height: 640, display: "flex", flexDirection: "column", justifyContent: "space-between"}}>
              <div>
                <div style={{fontSize: 18, color: C.accent, fontWeight: 700}}>{p.id} · promised {p.made}</div>
                <div style={{fontSize: 30, fontWeight: 700, margin: "10px 0"}}>{p.entity}</div>
                <div style={{fontSize: 22, color: C.muted, lineHeight: 1.4, fontStyle: "italic"}}>“{p.quote}”</div>
              </div>
              <div>
                <div style={{fontSize: 20, marginBottom: 8}}>{why[p.id]}</div>
                <div style={{fontSize: 17, color: C.muted, marginBottom: 12}}>source: {p.domain}</div>
                <Badge label={p.verdict.replace("_", " ").toUpperCase()} color={vc(p.verdict)} />
              </div>
            </div>
          );
        })}
      </div>
      <div style={{position: "absolute", left: 80, right: 80, bottom: 130, padding: "18px 32px", backgroundColor: "#1E293B", borderRadius: 16,
        display: "flex", justifyContent: "space-between", fontSize: 28, fontWeight: 600}}>
        <span>{data.total} tracked</span>
        <span style={{color: C.kept}}>{c.kept} kept</span>
        <span style={{color: C.in_progress}}>{c.in_progress} in progress</span>
        <span style={{color: C.broken}}>{c.broken} broken</span>
        <span style={{color: C.undecided}}>{c.undecided} undecided</span>
      </div>
    </AbsoluteFill>
  );
};

const FRAMES = 210; // recorded at 15 fps from the real demo page

const Clip: React.FC<{name: "p02" | "n01"; label: string; color: string}> = ({name, label, color}) => {
  const f = useCurrentFrame();
  const idx = Math.min(FRAMES - 1, Math.floor(f * 0.6)); // ~1.2x playback
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <Img src={staticFile(`rec/${name}/${String(idx).padStart(4, "0")}.jpg`)} style={{width: 1920, height: 1080}} />
      <div style={{position: "absolute", top: 24, right: 40}}><Badge label={label} color={color} /></div>
    </AbsoluteFill>
  );
};

const Close: React.FC = () => {
  const c = data.counts;
  return (
    <AbsoluteFill style={{...page, justifyContent: "center"}}>
      <div style={{color: C.accent, fontSize: 26, fontWeight: 700, letterSpacing: 2}}>MODELS DRAFT. DETERMINISTIC CODE DECIDES.</div>
      <h1 style={{fontSize: 110, margin: "12px 0"}}>SF Promises</h1>
      <div style={{fontSize: 40, color: C.muted}}>
        {data.total} promises · {c.kept} kept · {c.broken} broken · {c.in_progress} in progress · {c.undecided} undecided
      </div>
      <div style={{fontSize: 32, marginTop: 30, lineHeight: 1.6}}>
        <div><b style={{color: C.accent}}>Keenable</b> found and fetched the sources</div>
        <div><b style={{color: C.accent}}>Archil</b> kept the database and saved files on one persistent disk</div>
        <div>Arbitrator: seven deterministic checks, no model calls</div>
      </div>
      <div style={{fontSize: 30, color: C.accent, marginTop: 36}}>github.com/arii/sf-promises · Built by Ariel Anders</div>
    </AbsoluteFill>
  );
};

export const PromisesVideo: React.FC = () => (
  <AbsoluteFill>
    <Sequence from={0} durationInFrames={270}><Intro /></Sequence>
    <Sequence from={270} durationInFrames={390}><Cards /></Sequence>
    <Sequence from={660} durationInFrames={360}>
      <Clip name="p02" label="KEPT PATH · SAVED REPLAY" color={C.kept} />
    </Sequence>
    <Sequence from={1020} durationInFrames={360}>
      <Clip name="n01" label="WATCHDOG TEST · SAVED REPLAY" color={C.broken} />
    </Sequence>
    <Sequence from={1380} durationInFrames={420}><Close /></Sequence>
    <Captions />
  </AbsoluteFill>
);
