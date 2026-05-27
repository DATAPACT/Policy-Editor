(function () {
    function isOriginTrusted(origin) {
        return (window.TRUSTED_ORIGINS || []).some(function (entry) {
            if (entry.indexOf('*') === -1) {
                return origin === entry.replace(/\/$/, '');
            }
            // e.g. "https://*.dp.assistcloud.net"
            var parts = entry.split('*');
            return origin.startsWith(parts[0]) && origin.endsWith(parts[1]);
        });
    }

    var ssoInProgress = false;

    var parentOrigin = document.referrer ? new URL(document.referrer).origin : '*';

    function notifyParentError(message) {
        if (window.parent !== window) {
            window.parent.postMessage({ type: 'SSO_ERROR', message: message }, parentOrigin);
        }
    }

    function handleSsoToken(token) {
        if (ssoInProgress) return;
        ssoInProgress = true;

        fetch('/policy-editor/sso-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token }),
            credentials: 'same-origin',
        })
            .then(function (res) {
                return res.json().then(function (data) {
                    return { ok: res.ok, data: data };
                });
            })
            .then(function (result) {
                if (!result.ok) {
                    console.error('[SSO] Login failed:', result.data && result.data.error);
                    notifyParentError(result.data && result.data.error || 'Login failed');
                    ssoInProgress = false;
                    return;
                }
                if (result.data && result.data.redirect_url) {
                    var current = window.location.pathname;
                    var target = new URL(result.data.redirect_url, window.location.origin).pathname;
                    if (current !== target) {
                        window.location.href = result.data.redirect_url;
                    }
                }
            })
            .catch(function (err) {
                console.error('[SSO] Network error:', err);
                notifyParentError('Network error');
                ssoInProgress = false;
            });
    }

    window.addEventListener('message', function (event) {
        if (!isOriginTrusted(event.origin)) {
            return;
        }

        // INJECT_CSS: allows the trusted parent frame to apply custom styles
        // (e.g. theme overrides). Origin is validated above via isOriginTrusted —
        // only FRAME_ANCESTORS entries can send this message.
        // Note: injected CSS can visually overlay page content. Only origins listed
        // in FRAME_ANCESTORS (settings.py) are permitted to do this.
        if (event.data && event.data.type === 'INJECT_CSS' && typeof event.data.css === 'string') {
            var style = document.createElement('style');
            style.textContent = event.data.css;
            document.head.appendChild(style);
            return;
        }

        if (!event.data || event.data.type !== 'SSO_TOKEN' || !event.data.token) {
            return;
        }

        handleSsoToken(event.data.token);
    });

    // Signal to the parent frame that this page is ready to receive the SSO token.
    // This handles the timing issue where the parent sends SSO_TOKEN before sso.js loads
    // (e.g. after a @login_required redirect). The parent should respond with SSO_TOKEN
    // upon receiving SSO_READY.
    if (window.parent !== window) {
        window.parent.postMessage({ type: 'SSO_READY' }, parentOrigin);
    }
})();