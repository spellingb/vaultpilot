export type AuthState = "authenticated" | "missing_token";

export interface AuthStatus {
  state: AuthState;
  accountDisplayName?: string;
  lastAuthenticatedAt?: string;
}

export interface AuthStartResult {
  authorizeUrl: string;
  state: string;
  callbackUrl: string;
}

export interface AuthService {
  startAuth(): Promise<AuthStartResult>;
  getStatus(): Promise<AuthStatus>;
  logout(): Promise<AuthStatus>;
}

export class MockAuthService implements AuthService {
  private authenticated = false;

  async startAuth(): Promise<AuthStartResult> {
    const state = "mock-state-123";
    this.authenticated = true;
    return {
      authorizeUrl: "https://www.bungie.net/en/oauth/authorize?client_id=mock",
      state,
      callbackUrl: "http://127.0.0.1:8787/oauth/callback"
    };
  }

  async getStatus(): Promise<AuthStatus> {
    if (!this.authenticated) {
      return { state: "missing_token" };
    }

    return {
      state: "authenticated",
      accountDisplayName: "MockGuardian#1234",
      lastAuthenticatedAt: new Date().toISOString()
    };
  }

  async logout(): Promise<AuthStatus> {
    this.authenticated = false;
    return { state: "missing_token" };
  }
}
