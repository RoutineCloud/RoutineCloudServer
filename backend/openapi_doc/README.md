# Routine Cloud SDKs

This repository automatically generates and publishes SDKs for the Routine Cloud API across multiple languages and versions.

## API Versions
- **v1**: Current production API.

## Supported Languages
- **TypeScript**: Published to GitHub Packages as `@<owner>/routine-cloud-sdk-v1`.
- **Kotlin**: Published to GitHub Packages as `routine-cloud-v1-client`.

## CI/CD Workflow
The SDKs are generated using OpenAPI Generator and published via GitHub Actions.

### Triggering a Release
1. **Push to `main`**: Publishes a development version with a snapshot suffix (e.g., `0.0.0-snapshot.YYYYMMDDHHMMSS`).
   - TypeScript is published to GitHub Packages with the `dev` tag.
   - Kotlin is published to GitHub Packages.
2. **Push a Git Tag**: Publishes a stable version based on the tag name (e.g., `v1.0.0`).
   - Create and push a git tag following the `v*` scheme.
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   - This will build and publish stable SDKs for all supported languages.

### GitHub Secrets Required
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions for publishing to GitHub Packages.

## Consumption

### TypeScript (NPM via GitHub Packages)
Install:
```bash
npm install @<owner>/routine-cloud-sdk-v1
```
> Note: If the package is not yet public, you might need to add `@<owner>:registry=https://npm.pkg.github.com` and an `_authToken` to your `.npmrc`.

### Kotlin (Maven via GitHub Packages)
Add to your `build.gradle.kts`:
```kotlin
repositories {
    maven {
        url = uri("https://maven.pkg.github.com/<owner>/routine-cloud-server")
    }
}

dependencies {
    implementation("com.<owner>.routine-cloud:routine-cloud-v1-client:1.0.0")
}
```
> Note: If the package is not yet public, you might need to provide credentials in your `repositories` block.

