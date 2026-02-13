plugins {
    kotlin("jvm") version "1.9.22"
    application
}

group = "com.example"
version = "1.0.0"

repositories {
    mavenLocal()
    mavenCentral()
    // Uncomment to use JitPack instead of mavenLocal
    // maven { url = uri("https://jitpack.io") }
}

dependencies {
    // Using local Maven repository (after running: ./gradlew publishToMavenLocal)
    implementation("com.mfdeveloper.fcm:fcm-send:0.1.1")
    
    // Uncomment to use JitPack instead
    // implementation("com.github.mfdeveloper:firebase-cloud-messaging:0.1.1")
}

application {
    mainClass.set("com.example.MainKt")
}

kotlin {
    jvmToolchain(17)
}
