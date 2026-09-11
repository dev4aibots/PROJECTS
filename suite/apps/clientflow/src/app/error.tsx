'use client';
export default function ErrorPage({reset}: {reset:()=>void}) {return <main id="main-content" className="standalone empty-state"><h1>The workspace could not load.</h1><p>Try again. Reloading this demo restores its sample projects.</p><button className="button primary" onClick={reset}>Try again</button></main>;}
