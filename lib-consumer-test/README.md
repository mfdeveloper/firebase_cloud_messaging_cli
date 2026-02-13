# FCM Consumer Test

A standalone Kotlin/JVM project that demonstrates how to consume the `fcm-send` library as a dependency.

## Prerequisites

- JDK 17 or higher
- Gradle 8.5+

## Setup

### Option 1: Using Maven Local (Development)

First, publish the `fcm-send` library to your local Maven repository:

```bash
# From the main firebase-cloud-messaging project directory
cd ..
./gradlew publishToMavenLocal
```

Then build and run this consumer project:

```bash
./gradlew build run
```

### Option 2: Using JitPack (Production)

Edit `build.gradle.kts` to use JitPack instead of Maven Local:

```kotlin
repositories {
    mavenCentral()
    maven { url = uri("https://jitpack.io") }
}

dependencies {
    implementation("com.github.mfdeveloper:firebase-cloud-messaging:0.1.1")
}
```

## Running

```bash
# Build the project
./gradlew build

# Run the test application
./gradlew run
```

## Expected Output

```
Testing FCM library imports...

✓ FCMClient class instantiated: FCMClient
✓ AccessTokenType enum accessible: firebase_admin
✓ AccessTokenType FCM_OAUTH_HTTP_API accessible: fcm_http_api
✓ EnvironmentException class accessible: Test exception

═══════════════════════════════════════════════════
 ✓ All library imports verified successfully!
═══════════════════════════════════════════════════
```

## Opening in IntelliJ IDEA (or any other IDE/Editor)

1. Open IntelliJ IDEA
2. Select **File > Open**
3. Navigate to this `lib-consumer-test` directory
4. Click **Open**
5. Wait for Gradle sync to complete
    > PS: If it doesn't run automatically, force sync from your IDE/Editor (UI Button or using a CLI command) 
6. Run the `Main.kt` configuration, or compile/run [kotlin/com/example/Main.kt](./src/main/kotlin/com/example/Main.kt) file.

## Project Structure

```
lib-consumer-test/
├── build.gradle.kts          # Gradle build configuration
├── settings.gradle.kts       # Gradle settings
├── README.md                 # This file
└── src/
    └── main/
        └── kotlin/
            └── com/
                └── example/
                    └── Main.kt   # Test application
```
