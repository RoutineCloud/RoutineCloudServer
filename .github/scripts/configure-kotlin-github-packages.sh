#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:?usage: configure-kotlin-github-packages.sh <generated-kotlin-project>}"

if [[ -f "$PROJECT_DIR/build.gradle" ]]; then
  BUILD_FILE="$PROJECT_DIR/build.gradle"
  if grep -q "codex-github-packages-publish" "$BUILD_FILE"; then
    echo "GitHub Packages publishing already configured in $BUILD_FILE"
    exit 0
  fi

  cat >> "$BUILD_FILE" <<'EOF'

/*
 * codex-github-packages-publish
 * Adds an explicit Maven publication and GitHub Packages repository for CI.
 */
def sdkGithubRepository = System.getenv("GITHUB_REPOSITORY") ?: "RoutineCloud/RoutineCloudServer"
def sdkGroupId = (findProperty("sdk.groupId") ?: System.getenv("SDK_GROUP_ID") ?: project.group).toString()
def sdkArtifactId = (findProperty("sdk.artifactId") ?: System.getenv("SDK_ARTIFACT_ID") ?: project.name).toString()
def sdkVersion = (findProperty("sdk.version") ?: System.getenv("SDK_VERSION") ?: project.version).toString()

group = sdkGroupId
version = sdkVersion

apply plugin: 'maven-publish'

publishing {
    publications {
        create("github", MavenPublication) {
            from components.java
            groupId = sdkGroupId
            artifactId = sdkArtifactId
            version = sdkVersion
        }
    }
    repositories {
        maven {
            name = "GitHubPackages"
            url = uri("https://maven.pkg.github.com/${sdkGithubRepository}")
            credentials {
                username = (findProperty("gpr.user") ?: System.getenv("GITHUB_ACTOR"))?.toString()
                password = (findProperty("gpr.key") ?: System.getenv("GITHUB_TOKEN"))?.toString()
            }
        }
    }
}
EOF

  echo "Patched $BUILD_FILE for GitHub Packages publishing"
  exit 0
fi

if [[ -f "$PROJECT_DIR/build.gradle.kts" ]]; then
  BUILD_FILE="$PROJECT_DIR/build.gradle.kts"
  if grep -q "codex-github-packages-publish" "$BUILD_FILE"; then
    echo "GitHub Packages publishing already configured in $BUILD_FILE"
    exit 0
  fi

  cat >> "$BUILD_FILE" <<'EOF'

/*
 * codex-github-packages-publish
 * Adds an explicit Maven publication and GitHub Packages repository for CI.
 */
val sdkGithubRepository = System.getenv("GITHUB_REPOSITORY") ?: "RoutineCloud/RoutineCloudServer"
val sdkGroupId = (findProperty("sdk.groupId") as String?) ?: System.getenv("SDK_GROUP_ID") ?: project.group.toString()
val sdkArtifactId = (findProperty("sdk.artifactId") as String?) ?: System.getenv("SDK_ARTIFACT_ID") ?: project.name
val sdkVersion = (findProperty("sdk.version") as String?) ?: System.getenv("SDK_VERSION") ?: project.version.toString()

group = sdkGroupId
version = sdkVersion

apply(plugin = "maven-publish")

publishing {
    publications {
        create<org.gradle.api.publish.maven.MavenPublication>("github") {
            from(components["java"])
            groupId = sdkGroupId
            artifactId = sdkArtifactId
            version = sdkVersion
        }
    }
    repositories {
        maven {
            name = "GitHubPackages"
            url = uri("https://maven.pkg.github.com/$sdkGithubRepository")
            credentials {
                username = (findProperty("gpr.user") as String?) ?: System.getenv("GITHUB_ACTOR")
                password = (findProperty("gpr.key") as String?) ?: System.getenv("GITHUB_TOKEN")
            }
        }
    }
}
EOF

  echo "Patched $BUILD_FILE for GitHub Packages publishing"
  exit 0
fi

echo "No Gradle build file found under $PROJECT_DIR" >&2
exit 1
