import {UserManager, WebStorageStateStore} from 'oidc-client-ts';
import {getEnv} from '@/env';

export const userManager = new UserManager({
  authority: getEnv('VITE_OIDC_ISSUER'),
  client_id: getEnv('VITE_OIDC_CLIENT_ID'),
  redirect_uri: `${window.location.origin}/callback`,
  post_logout_redirect_uri: `${window.location.origin}`,
  response_type: 'code',
  scope: 'openid profile email urn:iam:org:project:roles urn:zitadel:iam:org:projects:roles',
  userStore: new WebStorageStateStore({ store: window.localStorage }),
});

export default userManager;
