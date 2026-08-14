import { Workspace } from "@/components/workspace";

export default function Home() {
  return (
    <main>
      <nav><a className="brand" href="#top"><b>D</b> DocuMind</a><a href="#workspace">Workspace</a><a href="#principles">How it works</a></nav>
      <section className="hero" id="top">
        <p className="eyebrow">Evidence-first document intelligence</p>
        <h1>Answers you can<br/><em>actually verify.</em></h1>
        <p className="lede">Upload a PDF, ask a question, and inspect every source. DocuMind refuses when evidence is insufficient instead of inventing an answer.</p>
        <a className="primary" href="#workspace">Open the workspace →</a>
      </section>
      <section id="principles" className="principles">
        <article><span>01</span><h2>Page-scoped retrieval</h2><p>Every chunk maps to one PDF page so citations remain precise.</p></article>
        <article><span>02</span><h2>Deterministic validation</h2><p>Model citations are checked against retrieved evidence before display.</p></article>
        <article><span>03</span><h2>Honest refusal</h2><p>No sufficient evidence means no fabricated answer.</p></article>
      </section>
      <Workspace />
      <footer><span className="brand"><b>D</b> DocuMind</span><p>Built for inspectable AI, not confident guessing.</p></footer>
    </main>
  );
}
