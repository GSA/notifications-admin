# Integrating with login.gov

How to integrate with the login.gov sandbox:  https://dashboard.int.identitysandbox.gov

1. Create a team and a user over in the login.gov sandbox.
2. Create a test app:
   - you will need to create a unique client id that looks like: urn:gov:gsa:openidconnect.profiles:sp:sso:gsa:test_notify_gov
   - Select OpenIdConnect and private key JWT
   - select authentication only
   - select MFA required + remember device 30 days only (AAL1)
   - set redirect urls like:  http://localhost:6012/sign-in
3. generate a cert: openssl req -nodes -x509 -days 365 -newkey rsa:2048 -keyout private.pem -out public.crt
4. Upload the public.crt to your app in the sandbox
5. put the private.pem contents and public.crt contents in github secrets (?)


## Open Issues

1. The logout functionality is not working.  The URL in sign_out.py does work by itself, but for some reason a 
   requests.post(url) fails.



