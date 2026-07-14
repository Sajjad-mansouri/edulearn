/**
 *  authentication client with automatic JWT refresh.

 */
class Auth {
  /**
   * @param {Object} options
   * @param {string} options.baseURL       - The base URL of the API (e.g. "https://api.example.com")
   * @param {string} [options.loginPath]   - Path appended to baseURL for login (default "/token/")
   * @param {string} [options.refreshPath] - Path for token refresh (default "/token/refresh/")
   * @param {string} [options.logoutPath]  - Path for logout (default "/logout/")
   * @param {Object} [options.storage]     - An object implementing getItem/setItem/removeItem (default localStorage)
   * @param {Function} [options.onLogout]  - Callback invoked after local cleanup (e.g. redirect to login)
   * @param {Function} [options.fetch]     - Fetch implementation (default global fetch)
   */
  constructor({
    baseURL,
    loginPath = '/token/',
    refreshPath = '/token/refresh/',
    logoutPath = '/logout/',
    storage = localStorage,
    onLogout = () => {},
    fetch = window.fetch,
  } = {}) {
    if (!baseURL) {
      throw new Error('Auth: baseURL is required');
    }

    // Remove trailing slashes from baseURL for consistent concatenation
    this.baseURL = baseURL.replace(/\/+$/, '');
    this.loginURL = `${this.baseURL}${loginPath}`;
    this.refreshURL = `${this.baseURL}${refreshPath}`;
    this.logoutURL = `${this.baseURL}${logoutPath}`;

    this.storage = storage;
    this.onLogout = onLogout;
    this.fetch = fetch;

    // Tokens (access token remains in memory only, never persisted)
    this.accessToken = null;
    this.refreshToken = this.storage.getItem('refreshToken');

    // Refresh queue to serialise concurrent 401s
    this._isRefreshing = false;
    this._refreshPromise = null;
  }

  // -------------------------------------------------------------------------
  // Public API
  // -------------------------------------------------------------------------

  /**
   * Attempt login with credentials.
   * @returns {Promise<{success: boolean, data?: any, error?: string}>}
   */
  async login(username, password) {
    try {
      const response = await this._request('POST', this.loginURL, {
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return { success: false, error: errorData.detail || 'Login failed', data: errorData };
      }

      const data = await response.json();
      this._setTokens(data.access, data.refresh);
      return { success: true, data };
    } catch (err) {
      return { success: false, error: err.message || 'Network error' };
    }
  }

  /**
   * Log out locally and optionally notify the server.
   * Does NOT redirect – use `onLogout` callback for navigation.
   */
  async logout() {
    try {
      // Only attempt server logout if we have a refresh token
      if (this.refreshToken) {
        // Best effort – ignore failures; do not attach auth headers
        await this._request('POST', this.logoutURL, {
          body: JSON.stringify({ refresh: this.refreshToken }),
          skipAuthHeader: true,
        }).catch(() => {});
      }
    } finally {
      this._clearTokens();
      this.onLogout();
    }
  }

  /**
   * Perform an authenticated request. Automatically attaches the access token
   * and retries once with a new token if a 401 is received.
   *
   * @param {string} url     - Full URL or relative path (appended to baseURL if not absolute)
   * @param {Object} [options]
   * @param {string} [options.method='GET']
   * @param {*}      [options.body]          - Request body (string, FormData, etc.)
   * @param {Object} [options.headers={}]
   * @param {string} [options.contentType]   - Override Content-Type (e.g. 'multipart/form-data')
   * @returns {Promise<Response>} The raw Fetch Response (caller should handle status/body)
   */
  async authenticatedRequest(url, options = {}) {
    const {
      method = 'GET',
      body,
      headers: extraHeaders = {},
      contentType,
      ...rest
    } = options;

    // If a relative path is given, prepend baseURL
    const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;

    // Build initial headers with access token
    const headers = this._buildHeaders(extraHeaders, contentType);

    // First attempt
    let response = await this._request(method, fullURL, {
      body,
      headers,
      ...rest,
    });

    // If 401 and we have a refresh token, try to refresh and retry once
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this._refreshAccessToken();

      if (refreshed) {
        // Retry with the new access token (preserve original extra headers)
        const retryHeaders = this._buildHeaders(extraHeaders, contentType);
        response = await this._request(method, fullURL, {
          body,
          headers: retryHeaders,
          ...rest,
        });
      } else {
        // Refresh failed – user is now logged out (onLogout already called)
        throw new Error('Session expired');
      }
    }

    return response;
  }

  /**
   * Expose the current access token (if any). Useful for manual requests.
   */
  getAccessToken() {
    return this.accessToken;
  }

  // -------------------------------------------------------------------------
  // Private token management
  // -------------------------------------------------------------------------

  /** @private */
  _setTokens(accessToken, refreshToken) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    this.storage.setItem('refreshToken', refreshToken);
  }

  /** @private */
  _clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    this.storage.removeItem('refreshToken');
  }

  /**
   * Refresh the access token using the stored refresh token.
   * Uses a queue to ensure only one refresh is attempted at a time.
   * @private
   * @returns {Promise<boolean>} true if refresh succeeded, false otherwise
   */
  async _refreshAccessToken() {
    // If a refresh is already in progress, wait for it
    if (this._isRefreshing) {
      return this._refreshPromise;
    }

    this._isRefreshing = true;
    this._refreshPromise = this._performRefresh();

    const success = await this._refreshPromise;
    this._isRefreshing = false;
    this._refreshPromise = null;

    return success;
  }

  /** @private */
  async _performRefresh() {
    try {
      const response = await this._request('POST', this.refreshURL, {
        body: JSON.stringify({ refresh: this.refreshToken }),
        // Do not attach the (possibly expired) access token
        skipAuthHeader: true,
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      if (data.access) {
        this.accessToken = data.access;
        return true;
      }
      return false;
    } catch (err) {
      // Refresh failed – clear tokens and notify
      this._clearTokens();
      this.onLogout();
      return false;
    }
  }

  // -------------------------------------------------------------------------
  // Unified request builder
  // -------------------------------------------------------------------------

  /**
   * Core fetch wrapper. Adds default JSON handling, merges auth headers,
   * and respects special flags to bypass authentication.
   * @private
   */
  async _request(method, url, {
    body,
    headers = {},
    contentType,
    skipAuthHeader = false,
    ...fetchOptions
  } = {}) {
    const finalHeaders = new Headers(headers);

    // Set Content-Type for JSON bodies by default (unless FormData etc.)
    if (body && typeof body === 'string' && !finalHeaders.has('Content-Type')) {
      finalHeaders.set('Content-Type', contentType || 'application/json');
    }

    // Attach Authorization header if access token exists and not explicitly skipped
    if (!skipAuthHeader && this.accessToken) {
      finalHeaders.set('Authorization', `Bearer ${this.accessToken}`);
    }

    return this.fetch(url, {
      method,
      headers: finalHeaders,
      body,
      ...fetchOptions,
    });
  }

  /**
   * Build a headers object from user-supplied extra headers and optional contentType.
   * @private
   */
  _buildHeaders(extraHeaders = {}, contentType) {
    const headers = new Headers(extraHeaders);
    if (contentType) {
      headers.set('Content-Type', contentType);
    }
    return headers;
  }
}
