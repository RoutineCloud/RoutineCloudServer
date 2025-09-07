// src/api/auth.ts
import { http } from "./http"

export interface LoginResponse {
  access_token: string
  token_type: "bearer"
}

export async function loginReq(username: string, password: string) {
  const form = new URLSearchParams()
  form.append("username", username)
  form.append("password", password)
  const { data } = await http.post<LoginResponse>("/auth/token", form)
  return data
}

export async function meReq() {
  const { data } = await http.get<LoginResponse["user"]>("/auth/me")
  return data
}

export async function generateAuthToken(clientId,
                                        redirectUri,
                                        scope,
                                        state,
                                        challenge,
                                        code_challenge_method) {
    const form = new URLSearchParams({
        response_type: "code",
        client_id: clientId,
        redirect_uri: redirectUri,
        scope,
        state,
        code_challenge: challenge,
        code_challenge_method: code_challenge_method,
      });
    const {data} = await http.get(`/oauth/auth-json?${form.toString()}`)
    return data
}