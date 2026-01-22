import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    alias(libs.plugins.kotlin.jvm)
    application
    jacoco
    `maven-publish`
}

group = "com.mfdeveloper.fcm"
version = "0.1.1"

repositories {
    mavenCentral()
}

dependencies {
    // Firebase Admin SDK
    implementation(libs.firebase.admin)
    
    // JSON parsing
    implementation(libs.gson)
    
    // CLI argument parsing
    implementation(libs.clikt)
    
    // Kotlin standard library
    implementation(libs.kotlin.stdlib)
    
    // Testing (using bundle for all test dependencies)
    testImplementation(libs.bundles.testing)
}

application {
    mainClass.set("com.mfdeveloper.fcm.MainKt")
}

tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport)
    
    // Fork a new JVM for each test class to ensure clean mocking state
    forkEvery = 1
    
    // Increase heap size for tests
    maxHeapSize = "1g"
    
    // Disable default test logging - we'll use custom colored output
    testLogging {
        // Only show failures in default output
        events()
        
        showExceptions = true
        showCauses = true
        showStackTraces = true
        
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
    
    // Color individual test results
    afterTest(KotlinClosure2<TestDescriptor, TestResult, Unit>({ desc, result ->
        val testName = "${desc.className?.substringAfterLast('.') ?: ""} > ${desc.displayName}"
        val duration = "(${result.endTime - result.startTime}ms)"
        
        val output = when (result.resultType) {
            TestResult.ResultType.SUCCESS -> "\u001B[32m  ✓ PASSED\u001B[0m  $testName \u001B[90m$duration\u001B[0m"
            TestResult.ResultType.FAILURE -> "\u001B[31m  ✗ FAILED\u001B[0m  $testName \u001B[90m$duration\u001B[0m"
            TestResult.ResultType.SKIPPED -> "\u001B[33m  ⊘ SKIPPED\u001B[0m $testName"
            else -> "  ? ${result.resultType} $testName"
        }
        println(output)
    }))
    
    // Add colored summary for test results
    afterSuite(KotlinClosure2<TestDescriptor, TestResult, Unit>({ desc, result ->
        if (desc.parent == null) { // Root suite
            val duration = "%.2f".format((result.endTime - result.startTime) / 1000.0)
            val output = buildString {
                append("\n")
                append("\u001B[90m${"─".repeat(70)}\u001B[0m")
                append("\n")
                
                // Status header
                when (result.resultType) {
                    TestResult.ResultType.SUCCESS -> {
                        append("\u001B[42m\u001B[30m TEST RESULTS: SUCCESS \u001B[0m")
                    }
                    TestResult.ResultType.FAILURE -> {
                        append("\u001B[41m\u001B[37m TEST RESULTS: FAILURE \u001B[0m")
                    }
                    TestResult.ResultType.SKIPPED -> {
                        append("\u001B[43m\u001B[30m TEST RESULTS: SKIPPED \u001B[0m")
                    }
                    else -> append("TEST RESULTS: ${result.resultType}")
                }
                append(" \u001B[90m(${duration}s)\u001B[0m")
                append("\n")
                append("\u001B[90m${"─".repeat(70)}\u001B[0m")
                append("\n")
                
                // Stats
                append("  \u001B[1mTotal:\u001B[0m ${result.testCount} tests")
                append("\n")
                append("  \u001B[32m✓ Passed:\u001B[0m  ${result.successfulTestCount}")
                append("\n")
                if (result.failedTestCount > 0) {
                    append("  \u001B[31m✗ Failed:\u001B[0m  ${result.failedTestCount}")
                } else {
                    append("  \u001B[90m✗ Failed:\u001B[0m  ${result.failedTestCount}")
                }
                append("\n")
                if (result.skippedTestCount > 0) {
                    append("  \u001B[33m⊘ Skipped:\u001B[0m ${result.skippedTestCount}")
                } else {
                    append("  \u001B[90m⊘ Skipped:\u001B[0m ${result.skippedTestCount}")
                }
                append("\n")
                append("\u001B[90m${"─".repeat(70)}\u001B[0m")
            }
            println(output)
        }
    }))
}

tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
        csv.required.set(false)
    }
    
    doLast {
        val xmlFile = reports.xml.outputLocation.get().asFile
        if (xmlFile.exists()) {
            val factory = javax.xml.parsers.DocumentBuilderFactory.newInstance()
            factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false)
            factory.setFeature("http://xml.org/sax/features/external-general-entities", false)
            factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false)
            val xml = factory.newDocumentBuilder().parse(xmlFile)
            
            val counters = xml.getElementsByTagName("counter")
            var covered = 0L
            var missed = 0L
            
            // Sum up all INSTRUCTION counters at package level
            for (i in 0 until counters.length) {
                val counter = counters.item(i)
                val type = counter.attributes.getNamedItem("type").nodeValue
                if (type == "INSTRUCTION" && counter.parentNode.nodeName == "report") {
                    covered += counter.attributes.getNamedItem("covered").nodeValue.toLong()
                    missed += counter.attributes.getNamedItem("missed").nodeValue.toLong()
                }
            }
            
            val total = covered + missed
            if (total > 0) {
                val percentage = (covered * 100.0 / total)
                val formatted = "%.1f".format(percentage)
                
                val color = if (percentage >= 80) "\u001B[32m" else if (percentage >= 60) "\u001B[33m" else "\u001B[31m"
                val reset = "\u001B[0m"
                
                println()
                println("\u001B[90m${"─".repeat(70)}\u001B[0m")
                println("\u001B[44m\u001B[37m CODE COVERAGE \u001B[0m")
                println("\u001B[90m${"─".repeat(70)}\u001B[0m")
                println("  ${color}▓${reset} Instruction coverage: ${color}${formatted}%${reset} ($covered/$total)")
                println("  ${color}▓${reset} Threshold:            \u001B[90m80.0%\u001B[0m")
                println("\u001B[90m${"─".repeat(70)}\u001B[0m")
                println("  \u001B[90mReport: build/reports/jacoco/test/html/index.html\u001B[0m")
                println("\u001B[90m${"─".repeat(70)}\u001B[0m")
            }
        }
    }
}

tasks.jacocoTestCoverageVerification {
    dependsOn(tasks.jacocoTestReport)
    
    violationRules {
        rule {
            limit {
                // Instruction coverage threshold
                minimum = "0.80".toBigDecimal()
            }
        }
    }
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs = listOf("-Xjsr305=strict")
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

// Run the Kotlin script (.kts) using Gradle
tasks.register<Exec>("runScript") {
    description = "Run the fcm-send.main.kts script"
    
    // Depend on fatJar since the script imports the compiled JAR
    dependsOn("fatJar")
    group = "application"
    
    val scriptArgs = project.findProperty("scriptArgs")?.toString()?.split(" ") ?: listOf("--help")
    
    workingDir = projectDir
    
    // Try to find kotlin in common locations or use the bundled one
    val kotlinHome = System.getenv("KOTLIN_HOME")
    val kotlinCmd = when {
        kotlinHome != null -> "$kotlinHome/bin/kotlinc"
        file("/usr/local/bin/kotlinc").exists() -> "/usr/local/bin/kotlinc"
        file("/opt/homebrew/bin/kotlinc").exists() -> "/opt/homebrew/bin/kotlinc"
        else -> "kotlinc" // Fallback to PATH
    }
    
    commandLine = listOf(kotlinCmd, "-script", "fcm-send.main.kts", "--") + scriptArgs
}

// Create a fat JAR for distribution
tasks.register<Jar>("fatJar") {
    // Use a fixed name without version for easier script dependency
    archiveBaseName.set("fcm-send")
    archiveVersion.set("") // No version in filename
    archiveClassifier.set("all")
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    
    manifest {
        attributes["Main-Class"] = "com.mfdeveloper.fcm.MainKt"
    }
    
    from(sourceSets.main.get().output)
    
    dependsOn(configurations.runtimeClasspath)
    from({
        configurations.runtimeClasspath.get()
            .filter { it.name.endsWith("jar") }
            .map { zipTree(it) }
    }) {
        // Exclude signature files from signed JARs
        exclude("META-INF/*.SF")
        exclude("META-INF/*.DSA")
        exclude("META-INF/*.RSA")
    }
}

// =============================================================================
// JitPack / Maven Publishing Configuration
// =============================================================================

// Sources JAR for publishing
val sourcesJar by tasks.registering(Jar::class) {
    archiveClassifier.set("sources")
    from(sourceSets.main.get().allSource)
}

// Javadoc JAR (empty for Kotlin, but required by some repositories)
val javadocJar by tasks.registering(Jar::class) {
    archiveClassifier.set("javadoc")
    from(tasks.named("javadoc"))
}

publishing {
    publications {
        create<MavenPublication>("maven") {
            groupId = project.group.toString()
            artifactId = "fcm-send"
            version = project.version.toString()
            
            from(components["java"])
            
            artifact(sourcesJar)
            artifact(javadocJar)
            
            pom {
                name.set("FCM Send")
                description.set("Firebase Cloud Messaging CLI and library for sending push notifications")
                url.set("https://github.com/mfdeveloper/firebase_cloud_messaging_cli")
                
                licenses {
                    license {
                        name.set("MIT License")
                        url.set("https://opensource.org/licenses/MIT")
                    }
                }
                
                developers {
                    developer {
                        id.set("mfdeveloper")
                        name.set("MF Developer")
                    }
                }
                
                scm {
                    connection.set("scm:git:git://github.com/mfdeveloper/firebase_cloud_messaging_cli.git")
                    developerConnection.set("scm:git:ssh://github.com/mfdeveloper/firebase_cloud_messaging_cli.git")
                    url.set("https://github.com/mfdeveloper/firebase_cloud_messaging_cli")
                }
            }
        }
    }
}
