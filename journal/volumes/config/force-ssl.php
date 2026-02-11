<?php
// PROXY HTTPS FIX (PRODUCTION)
// Forces OJS to see the request as HTTPS if the proxy says so.
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && stripos($_SERVER['HTTP_X_FORWARDED_PROTO'], 'https') !== false) {
    $_SERVER['HTTPS'] = 'on';
    $_SERVER['REQUEST_SCHEME'] = 'https';
}
