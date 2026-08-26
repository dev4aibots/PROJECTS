/** Local dev server emulating Vercel routing: /api/<name> → api/<name>.js, static from public/. */
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3003;

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const m = url.pathname.match(/^\/api\/([a-z-]+)\/?$/);
  if (m) {
    const file = path.join(__dirname, 'api', `${m[1]}.js`);
    if (fs.existsSync(file)) {
      try {
        return await require(file)(req, res);
      } catch (e) {
        res.statusCode = 500;
        return res.end(JSON.stringify({ error: e.message }));
      }
    }
  }
  const index = path.join(__dirname, 'public', 'index.html');
  res.setHeader('content-type', 'text/html');
  res.end(fs.readFileSync(index));
});

server.listen(PORT, () => console.log(`durasupport dev server → http://localhost:${PORT}`));
