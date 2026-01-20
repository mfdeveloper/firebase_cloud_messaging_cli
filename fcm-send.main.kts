#!/usr/bin/env kotlin

// ============================================================================
// FCM Send - Kotlin Script (Reuses compiled classes from the project)
// ============================================================================
// 
// PREREQUISITES: Build the fat JAR first:
//   ./gradlew fatJar
//
// USAGE:
//   kotlinc -script fcm-send.main.kts -- --help
//   kotlinc -script fcm-send.main.kts -- --info
//   kotlinc -script fcm-send.main.kts -- --token TOKEN --title "Hello" --body "World"
//
// Or make executable:
//   chmod +x fcm-send.main.kts
//   ./fcm-send.main.kts --help
//
// ============================================================================

// Version-less JAR name - no need to update when version changes
@file:DependsOn("build/libs/fcm-send-all.jar")

import com.mfdeveloper.fcm.CLIHandler

// Delegate to the existing CLI handler - no code duplication!
CLIHandler().main(args)
