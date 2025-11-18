# Environment Variables Setup

This project requires several environment variables for database access, authentication, and third-party integrations. Follow these steps to safely create your own `.env` file without committing secrets to Git.

## Database Credentials

Use any username/password you prefer. Example:

```env
USER_DB_USER=cplite
USER_DB_PASSWORD=cplitepassword
USER_DB_NAME=user_service_db
```

If you're using Docker Compose with PostgreSQL, the database URL becomes:

```
postgresql://<USER>:<PASSWORD>@postgres:5432/<DB_NAME>
```

Replace `<USER>`, `<PASSWORD>`, and `<DB_NAME>` accordingly.

## Generate a Secure JWT Secret

Run:

```bash
openssl rand -hex 32
```

Use the output for:

```env
JWT_SECRET_KEY=<your-secure-generated-secret>
```

## Google OAuth Credentials

To generate Google OAuth Client ID and Secret:

1. Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Go to **APIs & Services → Credentials**
3. Click **Create Credentials → OAuth Client ID**
4. Choose **Web Application**
5. Add authorized redirect URL:

```
http://localhost:8000/api/auth/google/callback
```

You will get:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Add them into your `.env`:

```env
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-client-secret>
```

## Redis Configuration

If using Docker, your Redis host is usually:

```
REDIS_HOST=redis
REDIS_PORT=6379
```

No password unless you set one.

## Codeforces API Keys

Generate from:
[https://codeforces.com/settings/api](https://codeforces.com/settings/api)

Add:

```env
CODEFORCES_API_KEY=<your-key>
CODEFORCES_API_SECRET=<your-secret>
```

## Gemini / Google AI API Key

Create from:
[https://aistudio.google.com/](https://aistudio.google.com/)

Add:

```env
GEMINI_API_KEY=<your-gemini-api-key>
```

## Recommendation & Internal Service Tokens

These can be any random strings unless you have custom logic.
Generate:

```bash
openssl rand -hex 24
```

Place them:

```env
RECOMMENDATION_SERVICE_TOKEN=<token>
RECOMMENDATION_SERVICE_SECRET=<secret>
```
