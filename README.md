# Firebase Cloud Messaging (FCM) Notification Sender - Kotlin

![fcm-icon](./images/firebase-fcm-icon.png)

A Kotlin CLI tool for sending [Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android) notifications using the **[Firebase Admin SDK for Java](https://firebase.google.com/docs/admin/setup#add-sdk).**

[![Kotlin 1.9+](https://img.shields.io/badge/kotlin-1.9+-blue.svg)](https://kotlinlang.org/)
[![Java 17+](https://img.shields.io/badge/java-17+-orange.svg)](https://www.oracle.com/java/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![JitPack](https://jitpack.io/v/mfdeveloper/firebase-cloud-messaging.svg)](https://jitpack.io/#mfdeveloper/firebase-cloud-messaging)

## Requirements

- **Java 17+** (JDK required for building)
- **Gradle 8.5+** (included via wrapper)
- [**Kotlin CLI compiler**](https://kotlinlang.org/docs/command-line.html#install-the-compiler) (for Kotlin script usage)

## Quick Start

### 1. Build the Project

```bash
# Using Gradle wrapper (recommended)
./gradlew build

# Run tests
./gradlew clean test

# Run tests with coverage report
./gradlew test jacocoTestReport
```

### 2. Run the CLI

```bash
# Run directly with Gradle
./gradlew run --args="--help"

# Or build and run the JAR
./gradlew fatJar
java -jar build/libs/fcm-send-0.1.1-all.jar --help
```

## Features

- **Send push notifications** with title, body, and optional custom data
- **Send data-only messages** (silent notifications for background processing)
- **Display service account info** and retrieve the access token
- **Dry-run mode** to validate messages without sending
- **Image support** for rich notifications

## Prerequisites

### Firebase Service Account

To authenticate a service account and authorize it to access Firebase services, you must generate a
`service-account.json` private key file in **JSON** format.

**To generate a private key file for your service account:**

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Open **Project Settings** > [Service Accounts](https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk)
4. Click **Generate New Private Key**, then confirm by clicking **Generate Key**
5. Securely store the `.json` file containing the key

### Environment Setup

Set the credentials environment variable pointing to your service account JSON file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
```

> **Tip:** Add this to your `~/.zshrc` or `~/.bashrc` for persistence.

## Usage

### Show Service Account Info & Access Token

```bash
./gradlew run --args="--info"
# Or
./gradlew run --args="--access-token"
```

### Pass Google Credentials File

```bash
./gradlew run --args="--credentials-key-file /path/to/service-account.json --info"
```

### Send a Simple Notification

```bash
./gradlew run --args="--token YOUR_FCM_TOKEN --title 'Hello' --body 'World'"
```

### Send Notification with Custom Data

```bash
./gradlew run --args="--token YOUR_FCM_TOKEN --title 'Order Update' --body 'Your order shipped!' --data '{\"order_id\": \"12345\"}'"
```

### Send Data-Only Message (Silent/Background)

```bash
./gradlew run --args="--token YOUR_FCM_TOKEN --data-only '{\"action\": \"sync\", \"id\": \"123\"}'"
```

### Validate Message Without Sending (Dry Run)

```bash
./gradlew run --args="--token YOUR_FCM_TOKEN --title 'Test' --body 'Test message' --dry-run"
```

## CLI Options Reference

| Option                   | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| `--credentials-key-file` | Path to Firebase service account `.json` file (takes precedence over env variable)          |
| `--info`                 | Display service account info and access token                                               |
| `--info-http`            | Display service account info and Google OAuth2 access token for FCM HTTP API                |
| `--access-token`         | Alias for `--info`                                                                          |
| `--access-token-http`    | Alias for `--info-http`                                                                     |
| `--token <FCM_TOKEN>`    | FCM registration token of the target device                                                 |
| `--title TEXT`           | Notification title                                                                          |
| `--body TEXT`            | Notification body                                                                           |
| `--data <JSON>`          | Custom data payload as JSON string                                                          |
| `--data-only <JSON>`     | Send data-only message (no visible notification)                                            |
| `--image URL`            | Image URL for rich notifications                                                            |
| `--dry-run`              | Validate message without sending                                                            |
| `--version`              | Show version information                                                                    |
| `--help`                 | Show help message                                                                           |

## Using as a Library

You can also use `fcm-send` as a library in your Kotlin/Java code:

```kotlin
import com.fcm.FCMClient

// Initialize client with credentials file
val client = FCMClient("/path/to/service-account.json")

// Send a notification
val response = client.sendNotification(
    fcmToken = "device_fcm_token",
    title = "Hello",
    body = "World",
    data = mapOf("key" to "value")  // optional
)
println("Message ID: $response")

// Send a data-only message
val dataResponse = client.sendDataMessage(
    fcmToken = "device_fcm_token",
    data = mapOf("action" to "sync", "id" to "123")
)
```

## Development

### Project Structure

```shell
firebase-cloud-messaging/
├── src/
│   ├── main/kotlin/com/fcm/
│   │   ├── AccessTokenType.kt   # Enum for token types
│   │   ├── FCMClient.kt         # Firebase client class
│   │   ├── CLIHandler.kt        # CLI command handler
│   │   └── Main.kt              # Entry point
│   └── test/kotlin/com/fcm/
│       ├── FCMClientTest.kt     # Client unit tests
│       ├── CLIHandlerTest.kt    # CLI unit tests
│       └── MainTest.kt          # Main entry tests
├── build.gradle.kts             # Gradle build configuration
├── settings.gradle.kts          # Gradle settings
├── gradlew                      # Gradle wrapper (Unix)
├── gradlew.bat                  # Gradle wrapper (Windows)
└── gradle/wrapper/
    └── gradle-wrapper.properties
```

### Running Tests

```bash
# Run all tests
./gradlew test

# Run tests with verbose output
./gradlew test --info

# Run a specific test class
./gradlew test --tests "com.fcm.FCMClientTest"
```

#### Colorized Test Output

Tests display with colored output in the terminal for easy visibility:

| Status     | Color     | Symbol |
|------------|-----------|--------|
| **Passed** | 🟢 Green  | ✓      |
| **Failed** | 🔴 Red    | ✗      |
| **Skipped**| 🟡 Yellow | ⊘      |

**Sample Output:**

```shell
> Task :test
  ✓ PASSED  CLIHandlerTest > notification success message() (2597ms)
  ✓ PASSED  CLIHandlerTest > parser shows help when no args() (134ms)
  ✓ PASSED  FCMClientTest > send notification builds correct message() (1221ms)
  ...

──────────────────────────────────────────────────────────────────────
 TEST RESULTS: SUCCESS  (10.49s)
──────────────────────────────────────────────────────────────────────
  Total: 23 tests
  ✓ Passed:  23
  ✗ Failed:  0
  ⊘ Skipped: 0
──────────────────────────────────────────────────────────────────────
```

### Code Coverage

This project uses **JaCoCo** for code coverage reporting. The coverage percentage is displayed in the terminal when the report is generated.

```bash
# Generate coverage report (displays coverage in terminal)
./gradlew test jacocoTestReport

# View HTML report
open build/reports/jacoco/test/html/index.html

# Verify coverage thresholds (80% minimum)
./gradlew jacocoTestCoverageVerification
```

#### Terminal Coverage Output

When running `jacocoTestReport`, the terminal displays a colorized coverage summary:

```shell
──────────────────────────────────────────────────────────────────────
 CODE COVERAGE 
──────────────────────────────────────────────────────────────────────
  ▓ Instruction coverage: 86.5% (1427/1649)
  ▓ Threshold:            80.0%
──────────────────────────────────────────────────────────────────────
  Report: build/reports/jacoco/test/html/index.html
──────────────────────────────────────────────────────────────────────
```

| Coverage | Color     | Description                     |
|----------|-----------|---------------------------------|
| ≥ 80%    | 🟢 Green  | Meets threshold                 |
| 60-79%   | 🟡 Yellow | Below threshold, needs work     |
| < 60%    | 🔴 Red    | Critical, significant gaps      |

#### Coverage Reports

Reports are generated in:

- **HTML**: `build/reports/jacoco/test/html/index.html`
- **XML**: `build/reports/jacoco/test/jacocoTestReport.xml`

### Building a Fat JAR

Create a self-contained JAR with all dependencies:

```bash
./gradlew fatJar

# Run the fat JAR (version-less name for easier scripting)
java -jar build/libs/fcm-send-all.jar --help
```

### Kotlin Script (`.kts`)

A lightweight [Kotlin script](https://kotlinlang.org/docs/command-line.html#run-scripts) is available that reuses the compiled classes (no code duplication).

1. Install the [Kotlin CLI compiler](https://kotlinlang.org/docs/command-line.html#install-the-compiler)

2. Perform the commands below:

```bash
# PREREQUISITE: Build the fat JAR first
./gradlew fatJar

# Run with kotlinc-script CLI (requires Kotlin CLI installed)
kotlinc -script fcm-send.main.kts -- --help

# Alternatively, run the script straight-forward
./fcm-send.main.kts --version

# Or make it executable
chmod +x fcm-send.main.kts
./fcm-send.main.kts --help

# Run via Gradle (alternative if Kotlin CLI not installed)
./gradlew runScript -PscriptArgs="--help"
./gradlew runScript -PscriptArgs="--info"
```

The script uses `@file:DependsOn` to import the compiled fat JAR, reusing `FCMClient` and `CLIHandler` classes directly.

#### IntelliJ Run Configurations

Pre-configured IntelliJ run configurations are available in `.idea/runConfigurations/`:

| Configuration              | Description                              |
|----------------------------|------------------------------------------|
| `fcm-send.kts --help`      | Show help message                        |
| `fcm-send.kts --info`      | Display service account info             |
| `fcm-send.kts --version`   | Show version                             |

To use: Open the project in IntelliJ IDEA → Run → Select configuration from dropdown.

## Use as a Library (JitPack)

[![](https://jitpack.io/v/mfdeveloper/firebase-cloud-messaging.svg)](https://jitpack.io/#mfdeveloper/firebase-cloud-messaging)

You can use this project as a Gradle/Maven dependency via [JitPack](https://jitpack.io/).

### Gradle (Kotlin DSL)

```kotlin
// settings.gradle.kts or build.gradle.kts
repositories {
    mavenCentral()
    maven { url = uri("https://jitpack.io") }
}

// build.gradle.kts
dependencies {
    implementation("com.github.mfdeveloper:firebase_cloud_messaging_cli:kotlin-0.1.1")
}
```

### Gradle (Groovy)

```groovy
// settings.gradle or build.gradle
repositories {
    mavenCentral()
    maven { url 'https://jitpack.io' }
}

// build.gradle
dependencies {
    implementation 'com.github.mfdeveloper/firebase_cloud_messaging_cli:kotlin-0.1.1'
    // Optionally, use the SNAPSHOT branch
    implementation 'com.github.mfdeveloper/firebase_cloud_messaging_cli:kotlin-cli-SNAPSHOT'
}
```

### Maven

```xml
<repositories>
    <repository>
        <id>jitpack.io</id>
        <url>https://jitpack.io</url>
    </repository>
</repositories>

<dependency>
    <groupId>com.github.mfdeveloper</groupId>
    <artifactId>firebase-cloud-messaging</artifactId>
    <version>0.1.1</version>
</dependency>
```

### Library Usage Example

```kotlin
import com.mfdeveloper.fcm.FCMClient
import com.mfdeveloper.fcm.AccessTokenType

// Create client with credentials file
val client = FCMClient("/path/to/service-account.json")

// Send a notification
val messageId = client.sendNotification(
    fcmToken = "device_fcm_token",
    title = "Hello",
    body = "World",
    data = mapOf("key" to "value")
)
println("Message sent: $messageId")

// Send a data-only message
val dataMessageId = client.sendDataMessage(
    fcmToken = "device_fcm_token",
    data = mapOf("action" to "sync", "id" to "123")
)

// Get access token
val accessToken = client.getAccessToken()

// Show service account info
client.showInfo(AccessTokenType.FIREBASE_ADMIN)
```

## Dependencies

| Dependency              | Version | Purpose                           |
|-------------------------|---------|-----------------------------------|
| `firebase-admin`        | 9.2.0   | Firebase Admin SDK for Java       |
| `gson`                  | 2.10.1  | JSON parsing                      |
| `clikt`                 | 4.2.2   | Command-line argument parsing     |
| `kotlin-stdlib`         | 1.9.22  | Kotlin standard library           |
| `junit-jupiter`         | 5.10.1  | Unit testing framework            |
| `mockk`                 | 1.13.9  | Kotlin mocking library            |
| `assertj-core`          | 3.25.1  | Fluent assertions                 |

## Gradle Commands Reference

| Command                                  | Description                              |
|------------------------------------------|------------------------------------------|
| `./gradlew build`                        | Compile and build the project            |
| `./gradlew test`                         | Run all tests                            |
| `./gradlew jacocoTestReport`             | Generate code coverage report            |
| `./gradlew jacocoTestCoverageVerification` | Verify coverage meets 80% threshold    |
| `./gradlew run --args="..."`             | Run the application with arguments       |
| `./gradlew fatJar`                       | Create fat JAR with all dependencies     |
| `./gradlew runScript -PscriptArgs="..."` | Run the Kotlin script (.kts)             |
| `./gradlew publishToMavenLocal`          | Publish to local Maven repository        |
| `./gradlew clean`                        | Clean build directory                    |
| `./gradlew dependencies`                 | Show project dependencies                |

### Publishing to Local Maven Repository

To use this library in other local projects before publishing to JitPack:

```bash
# Publish to ~/.m2/repository
./gradlew publishToMavenLocal
```

Then in your other project, add the `mavenLocal()` repository:

```kotlin
// build.gradle.kts
repositories {
    mavenLocal()
    mavenCentral()
}

dependencies {
    implementation("com.mfdeveloper.fcm:fcm-send:0.1.1")
    // Optionally, use the branch-SNAPSHOT as version
    implementation("com.mfdeveloper.fcm:fcm-send:kotlin-cli-SNAPSHOT")
}
```

## CI/CD

GitHub Actions workflows are available for automated testing and building:

| Workflow | File | Description |
|----------|------|-------------|
| **Kotlin > Tests** | `.github/workflows/tests.yml` | Runs tests with coverage on push/PR |
| **Kotlin > Build** | `.github/workflows/build.yml` | Builds the project and fat JAR |
| **Kotlin > Integration Test** | `.github/workflows/kotlin-integration.yml` | Tests the library as a dependency |

### Test Workflow

Triggered on push/PR to `main`/`master` when Kotlin files change:

- Runs tests on **Java 17** and **Java 21**
- Generates JaCoCo coverage reports
- Verifies **80% coverage threshold**
- Uploads test results and coverage as artifacts

### Build Workflow

Can be triggered manually or called by other workflows:

- Builds the project with Gradle
- Creates the fat JAR distribution
- Uploads JARs as artifacts

### Integration Test Workflow

Verifies the library can be consumed as a dependency:

- **Test as Library Dependency**: Creates a temporary consumer project that imports and uses the library classes (`FCMClient`, `AccessTokenType`, `EnvironmentException`)
- **Simulate JitPack Build**: Publishes to Maven Local and verifies all required artifacts are generated (JAR, POM, sources)

## References

- [Firebase Admin SDK for Java](https://firebase.google.com/docs/admin/setup#add-sdk)
- [FCM: Retrieve the current registration token](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android#retrieve-the-current-registration-token)
- [Kotlin Documentation](https://kotlinlang.org/docs/home.html)
- [Clikt - Command Line Interface for Kotlin](https://ajalt.github.io/clikt/)
- [JaCoCo - Java Code Coverage](https://www.jacoco.org/jacoco/)
