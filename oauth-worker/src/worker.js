// GitHub OAuth proxy for Sveltia CMS.
// Two endpoints:
//   GET /oauth/authorize  -> redirects to GitHub's OAuth consent page
//   GET /oauth/callback   -> GitHub redirects back here; we exchange code for token
//                            and postMessage it back to the admin page opener.
//
// Secrets expected: GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET

const ALLOWED_ORIGINS = [
  'https://loveanddevi.pages.dev',
  'https://revamp-astro-cms.loveanddevi.pages.dev',
  'https://loveanddevi.com',
  'https://www.loveanddevi.com',
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/oauth/authorize') {
      const params = new URLSearchParams({
        client_id: env.GITHUB_CLIENT_ID,
        scope: 'repo,user',
        redirect_uri: `${url.origin}/oauth/callback`,
      });
      return Response.redirect(`https://github.com/login/oauth/authorize?${params}`, 302);
    }

    if (url.pathname === '/oauth/callback') {
      const code = url.searchParams.get('code');
      if (!code) return new Response('missing code', { status: 400 });

      const resp = await fetch('https://github.com/login/oauth/access_token', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: env.GITHUB_CLIENT_ID,
          client_secret: env.GITHUB_CLIENT_SECRET,
          code,
        }),
      });
      const data = await resp.json();
      const status = data.access_token ? 'success' : 'error';
      const content = data.access_token
        ? { token: data.access_token, provider: 'github' }
        : { error: data.error || 'no_token', error_description: data.error_description || '' };

      // Sveltia CMS listens for postMessage with this exact shape.
      const message = `authorization:github:${status}:${JSON.stringify(content)}`;
      const safeMessage = JSON.stringify(message);
      const allowed = JSON.stringify(ALLOWED_ORIGINS);

      const html = `<!doctype html><html><body><script>
(function(){
  var allowed = ${allowed};
  function send(e){
    if (allowed.indexOf(e.origin) === -1) return;
    e.source.postMessage(${safeMessage}, e.origin);
  }
  window.addEventListener('message', send, false);
  window.opener && window.opener.postMessage('authorizing:github', '*');
})();
</script><p>Signing you in — you can close this window.</p></body></html>`;

      return new Response(html, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      });
    }

    return new Response('OAuth proxy for loveanddevi CMS.', { status: 200 });
  },
};
